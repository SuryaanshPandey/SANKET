"""Adapter from Clarity Graph Contract -> canonical investigation model.

This module deliberately performs normalization and structural validation only.
Entity merging/fuzzy resolution, graph analytics, anomaly detection, AI
orchestration, and persistence belong to later layers.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Union

from pydantic import ValidationError

from clarity.contract.schemas import GraphContractResponse
from clarity.intelligence.models import (
    AdapterIssue,
    CanonicalEntity,
    CanonicalEvent,
    CanonicalRelationship,
    EvidenceReference,
    InvestigationGraph,
    InvestigationStatus,
    NodeKind,
)


class GraphContractAdapterError(ValueError):
    """Raised when the upstream graph contract cannot be safely adapted."""


GraphContractInput = Union[GraphContractResponse, Mapping[str, Any], str, bytes, bytearray]


class GraphContractAdapter:
    """Convert a Clarity graph contract into stable investigation models.

    Parameters
    ----------
    strict:
        When True (default), structural errors raise immediately. When False,
        the returned graph contains issues and processing continues wherever
        possible. Warnings are never treated as fatal.
    """

    def __init__(self, strict: bool = True) -> None:
        self.strict = strict

    def adapt(self, source: GraphContractInput) -> InvestigationGraph:
        contract = self._parse_contract(source)
        issues: list[AdapterIssue] = []

        entities = [self._adapt_entity(item) for item in contract.entities]
        events = [self._adapt_event(item) for item in contract.events]

        node_kind_by_id = self._build_node_index(entities, events, issues)
        self._validate_event_endpoints(events, node_kind_by_id, issues)
        relationships: list[CanonicalRelationship] = []
        seen_relationship_ids: set[str] = set()
        for index, relationship in enumerate(contract.relationships):
            if relationship.id in seen_relationship_ids:
                issues.append(
                    AdapterIssue(
                        severity="error",
                        code="DUPLICATE_RELATIONSHIP_ID",
                        message=f"Duplicate relationship ID '{relationship.id}' found.",
                        path=f"relationships[{index}].id",
                    )
                )
            seen_relationship_ids.add(relationship.id)
            relationships.append(
                self._adapt_relationship(
                    relationship,
                    index=index,
                    node_kind_by_id=node_kind_by_id,
                    events_by_id={item.id: item for item in events},
                    issues=issues,
                )
            )

        graph = InvestigationGraph(
            contract_version=contract.contract_version,
            case_id=contract.case_id,
            batch_id=contract.batch_id,
            total_documents=contract.total_documents,
            entities=entities,
            events=events,
            relationships=relationships,
            audit_chain=dict(contract.audit_chain),
            issues=issues,
        )

        self._raise_if_strict_errors(issues)
        return graph

    def adapt_json(self, payload: str | bytes | bytearray) -> InvestigationGraph:
        return self.adapt(payload)

    def _parse_contract(self, source: GraphContractInput) -> GraphContractResponse:
        if isinstance(source, GraphContractResponse):
            # Re-validate through Pydantic to avoid accidentally mutating a model
            # created through unsafe construction.
            return GraphContractResponse.model_validate(source.model_dump(mode="python"))

        if isinstance(source, (bytes, bytearray)):
            try:
                source = json.loads(source.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise GraphContractAdapterError(f"Invalid Graph Contract JSON bytes: {exc}") from exc

        if isinstance(source, str):
            try:
                source = json.loads(source)
            except json.JSONDecodeError as exc:
                raise GraphContractAdapterError(f"Invalid Graph Contract JSON: {exc}") from exc

        if isinstance(source, Mapping):
            try:
                return GraphContractResponse.model_validate(source)
            except ValidationError as exc:
                raise GraphContractAdapterError(
                    f"Graph Contract schema validation failed: {exc}"
                ) from exc

        raise GraphContractAdapterError(
            f"Unsupported Graph Contract input type: {type(source).__name__}"
        )

    @staticmethod
    def _adapt_evidence(source: Any) -> EvidenceReference:
        return EvidenceReference(
            document_id=source.document_id,
            filename=source.filename,
            file_hash_sha256=source.file_hash_sha256,
            page=source.page,
            bounding_box=(source.bounding_box.model_dump(mode="json") if source.bounding_box else None),
            text_span=source.text_span,
        )

    def _adapt_entity(self, source: Any) -> CanonicalEntity:
        return CanonicalEntity(
            id=source.id,
            type=source.type.value if hasattr(source.type, "value") else str(source.type),
            name=source.name,
            normalized_name=source.normalized_name,
            role=source.role,
            attributes=dict(source.attributes),
            confidence=source.confidence,
            source=self._adapt_evidence(source.source),
            contract_type=source.type.value if hasattr(source.type, "value") else str(source.type),
        )

    def _adapt_event(self, source: Any) -> CanonicalEvent:
        event_type = source.type.value if hasattr(source.type, "value") else str(source.type)
        return CanonicalEvent(
            id=source.id,
            type=event_type,
            title=source.title,
            source_entity_id=source.source_entity,
            target_entity_id=source.target_entity,
            timestamp=source.timestamp,
            timestamp_start=source.timestamp_start,
            timestamp_end=source.timestamp_end,
            attributes=dict(source.attributes),
            source=self._adapt_evidence(source.source),
            contract_type=event_type,
        )

    @staticmethod
    def _validate_event_endpoints(
        events: list[CanonicalEvent],
        node_kind_by_id: dict[str, NodeKind],
        issues: list[AdapterIssue],
    ) -> None:
        for index, event in enumerate(events):
            if event.source_entity_id:
                kind = node_kind_by_id.get(event.source_entity_id)
                if kind is None:
                    issues.append(
                        AdapterIssue(
                            severity="error",
                            code="DANGLING_EVENT_SOURCE",
                            message=(
                                f"Event '{event.id}' references missing source entity "
                                f"'{event.source_entity_id}'."
                            ),
                            path=f"events[{index}].source_entity",
                        )
                    )
                elif kind != NodeKind.ENTITY:
                    issues.append(
                        AdapterIssue(
                            severity="error",
                            code="INVALID_EVENT_SOURCE_KIND",
                            message=(
                                f"Event '{event.id}' source '{event.source_entity_id}' "
                                "must reference an entity node."
                            ),
                            path=f"events[{index}].source_entity",
                        )
                    )

            if event.target_entity_id:
                kind = node_kind_by_id.get(event.target_entity_id)
                if kind is None:
                    issues.append(
                        AdapterIssue(
                            severity="error",
                            code="DANGLING_EVENT_TARGET",
                            message=(
                                f"Event '{event.id}' references missing target entity "
                                f"'{event.target_entity_id}'."
                            ),
                            path=f"events[{index}].target_entity",
                        )
                    )
                elif kind != NodeKind.ENTITY:
                    issues.append(
                        AdapterIssue(
                            severity="error",
                            code="INVALID_EVENT_TARGET_KIND",
                            message=(
                                f"Event '{event.id}' target '{event.target_entity_id}' "
                                "must reference an entity node."
                            ),
                            path=f"events[{index}].target_entity",
                        )
                    )

    @staticmethod
    def _build_node_index(
        entities: list[CanonicalEntity],
        events: list[CanonicalEvent],
        issues: list[AdapterIssue],
    ) -> dict[str, NodeKind]:
        node_kind_by_id: dict[str, NodeKind] = {}
        for entity in entities:
            if entity.id in node_kind_by_id:
                issues.append(
                    AdapterIssue(
                        severity="error",
                        code="DUPLICATE_NODE_ID",
                        message=f"Duplicate graph node ID '{entity.id}' found.",
                        path="entities",
                    )
                )
                continue
            node_kind_by_id[entity.id] = NodeKind.ENTITY

        for event in events:
            if event.id in node_kind_by_id:
                issues.append(
                    AdapterIssue(
                        severity="error",
                        code="NODE_ID_COLLISION",
                        message=f"Event ID '{event.id}' collides with an existing entity ID.",
                        path="events",
                    )
                )
                continue
            node_kind_by_id[event.id] = NodeKind.EVENT
        return node_kind_by_id

    def _adapt_relationship(
        self,
        source: Any,
        *,
        index: int,
        node_kind_by_id: dict[str, NodeKind],
        events_by_id: dict[str, CanonicalEvent],
        issues: list[AdapterIssue],
    ) -> CanonicalRelationship:
        source_kind = node_kind_by_id.get(source.source_entity)
        target_kind = node_kind_by_id.get(source.target_entity)

        if source_kind is None:
            issues.append(
                AdapterIssue(
                    severity="error",
                    code="DANGLING_SOURCE_ENDPOINT",
                    message=(
                        f"Relationship '{source.id}' references missing source node "
                        f"'{source.source_entity}'."
                    ),
                    path=f"relationships[{index}].source_entity",
                )
            )
            source_kind = NodeKind.ENTITY

        if target_kind is None:
            issues.append(
                AdapterIssue(
                    severity="error",
                    code="DANGLING_TARGET_ENDPOINT",
                    message=(
                        f"Relationship '{source.id}' references missing target node "
                        f"'{source.target_entity}'."
                    ),
                    path=f"relationships[{index}].target_entity",
                )
            )
            target_kind = NodeKind.ENTITY

        source_refs: list[EvidenceReference] = []
        # A relationship can point at an event, and the event's source is a
        # defensible provenance reference for the relationship's occurrence.
        if source_kind == NodeKind.EVENT and source.source_entity in events_by_id:
            source_refs.append(events_by_id[source.source_entity].source)
        if target_kind == NodeKind.EVENT and source.target_entity in events_by_id:
            target_ref = events_by_id[source.target_entity].source
            if not any(
                ref.document_id == target_ref.document_id
                and ref.file_hash_sha256 == target_ref.file_hash_sha256
                and ref.page == target_ref.page
                and ref.text_span == target_ref.text_span
                for ref in source_refs
            ):
                source_refs.append(target_ref)

        return CanonicalRelationship(
            id=source.id,
            source_id=source.source_entity,
            target_id=source.target_entity,
            source_kind=source_kind,
            target_kind=target_kind,
            relationship_type=source.relationship_type,
            confidence=source.confidence,
            status=InvestigationStatus.OBSERVED,
            evidence_text=source.evidence,
            source_refs=source_refs,
            metadata={
                "adapter": "clarity_graph_contract",
                "relationship_contract_index": index,
            },
        )

    def _raise_if_strict_errors(self, issues: list[AdapterIssue]) -> None:
        if not self.strict:
            return
        errors = [issue for issue in issues if issue.severity.lower() == "error"]
        if not errors:
            return
        summary = "; ".join(f"{item.code}: {item.message}" for item in errors)
        raise GraphContractAdapterError(summary)


def adapt_graph_contract(source: GraphContractInput, *, strict: bool = True) -> InvestigationGraph:
    """Functional wrapper for simple integration points."""
    return GraphContractAdapter(strict=strict).adapt(source)
