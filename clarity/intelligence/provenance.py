"""Evidence provenance and workflow lineage utilities.

V1.10 makes provenance a first-class analytical object rather than a UI-only
convenience. Every source field and graph object can be traced back to the
original document and, when available, the exact bounding box/text span.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field

from clarity.intelligence.evidence_graph import EvidenceGraph
from clarity.intelligence.models import EvidenceReference, InvestigationStatus


class ProvenanceItem(BaseModel):
    """One traceable evidence lineage record."""

    model_config = ConfigDict(extra="forbid")

    provenance_id: str
    object_type: str
    object_id: str
    label: str
    status: str = InvestigationStatus.OBSERVED.value
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_references: list[EvidenceReference] = Field(default_factory=list)
    derived_from: list[str] = Field(default_factory=list)
    explanation: str = ""


class ProvenanceSummary(BaseModel):
    """Compact provenance inventory for an investigation case."""

    model_config = ConfigDict(extra="forbid")

    total_items: int = Field(ge=0)
    entity_items: int = Field(ge=0)
    event_items: int = Field(ge=0)
    relationship_items: int = Field(ge=0)
    field_items: int = Field(ge=0)
    finding_items: int = Field(ge=0)


class ProvenanceReport(BaseModel):
    """Deterministic, JSON-ready provenance report."""

    model_config = ConfigDict(extra="forbid")

    case_id: str | None = None
    summary: ProvenanceSummary
    items: list[ProvenanceItem] = Field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def _safe_float(value: Any, default: float = 1.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _field_source(document: Mapping[str, Any], field: Mapping[str, Any]) -> EvidenceReference:
    bbox = field.get("bounding_box")
    normalized_bbox = None
    if isinstance(bbox, Mapping):
        normalized_bbox = {}
        for key in ("x", "y", "w", "h"):
            if key in bbox:
                try:
                    normalized_bbox[key] = float(bbox[key])
                except (TypeError, ValueError):
                    pass
    return EvidenceReference(
        document_id=str(document.get("document_id", "")),
        filename=str(document.get("original_filename", "")),
        file_hash_sha256=str(document.get("file_hash_sha256", "")),
        page=1,
        bounding_box=normalized_bbox,
        text_span=str(field.get("field_value") or "") or None,
    )


def build_field_provenance(documents: Iterable[Mapping[str, Any]]) -> list[ProvenanceItem]:
    """Create one provenance item per non-empty extracted field."""
    items: list[ProvenanceItem] = []
    for document in documents:
        document_id = str(document.get("document_id", "unknown-document"))
        filename = str(document.get("original_filename", "unknown-document"))
        for index, field in enumerate(document.get("field_items") or []):
            value = str(field.get("field_value") or "").strip()
            if not value:
                continue
            field_name = str(field.get("field_name") or "field")
            field_id = f"FIELD-{document_id[:8]}-{index:04d}"
            items.append(
                ProvenanceItem(
                    provenance_id=field_id,
                    object_type="FIELD",
                    object_id=f"{document_id}:{field_name}:{index}",
                    label=field_name,
                    status=InvestigationStatus.OBSERVED.value,
                    confidence=_safe_float(field.get("confidence"), 1.0),
                    source_references=[_field_source(document, field)],
                    explanation=f"Observed in extracted field '{field_name}' from {filename}.",
                )
            )
    return items


def build_graph_provenance(graph: EvidenceGraph) -> list[ProvenanceItem]:
    """Create provenance items for canonical graph nodes and relationships."""
    items: list[ProvenanceItem] = []
    for node in sorted(graph.nodes.values(), key=lambda item: item.id):
        refs = list(node.source_refs)
        status = str(node.metadata.get("status", InvestigationStatus.OBSERVED.value))
        items.append(
            ProvenanceItem(
                provenance_id=f"GRAPH-{node.id}",
                object_type=node.kind.value,
                object_id=node.id,
                label=node.label,
                status=status,
                confidence=_safe_float(node.confidence),
                source_references=refs,
                explanation=f"{node.kind.value.title()} '{node.label}' is backed by {len(refs)} source reference(s).",
            )
        )
    for edge in sorted(graph.edges.values(), key=lambda item: item.id):
        items.append(
            ProvenanceItem(
                provenance_id=f"GRAPH-EDGE-{edge.id}",
                object_type="RELATIONSHIP",
                object_id=edge.id,
                label=edge.relationship_type,
                status=edge.status.value,
                confidence=_safe_float(edge.confidence),
                source_references=list(edge.source_refs),
                explanation=(
                    f"Relationship {edge.source_id} → {edge.target_id} "
                    f"is represented by the evidence graph with {len(edge.source_refs)} direct source reference(s)."
                ),
            )
        )
    return items


def build_finding_provenance(
    findings: Iterable[Mapping[str, Any]],
    graph: EvidenceGraph,
) -> list[ProvenanceItem]:
    """Attach graph evidence references to analytical findings."""
    items: list[ProvenanceItem] = []
    for index, finding in enumerate(findings):
        finding_id = str(finding.get("finding_id") or finding.get("node_id") or f"finding-{index + 1}")
        related_ids: list[str] = []
        for key in ("supporting_relationship_ids", "supporting_event_ids", "entity_ids", "supporting_entity_ids"):
            values = finding.get(key)
            if isinstance(values, list):
                related_ids.extend(str(value) for value in values)
        related_ids = sorted(set(related_ids))
        refs: list[EvidenceReference] = []
        for object_id in related_ids:
            node = graph.nodes.get(object_id)
            if node:
                refs.extend(node.source_refs)
                continue
            edge = graph.edges.get(object_id)
            if edge:
                refs.extend(edge.source_refs)
        deduped: list[EvidenceReference] = []
        seen: set[tuple[str, str, int, str | None]] = set()
        for ref in refs:
            key = (ref.document_id, ref.file_hash_sha256, ref.page, ref.text_span)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(ref)
        items.append(
            ProvenanceItem(
                provenance_id=f"FINDING-{finding_id}",
                object_type="FINDING",
                object_id=finding_id,
                label=str(finding.get("label") or finding.get("candidate") or finding_id),
                status=str(finding.get("status") or "INVESTIGATIVE_LEAD"),
                confidence=_safe_float(finding.get("bridge_score", finding.get("score", finding.get("confidence", 1.0)))),
                source_references=deduped,
                derived_from=related_ids,
                explanation="Analytical finding linked to the graph objects listed in derived_from; it is not a standalone source fact.",
            )
        )
    return items


def build_provenance_report(
    *,
    case_id: str | None,
    documents: Iterable[Mapping[str, Any]],
    graph: EvidenceGraph | None = None,
    findings: Iterable[Mapping[str, Any]] = (),
) -> ProvenanceReport:
    """Build a case-wide provenance report from extraction and graph layers."""
    field_items = build_field_provenance(documents)
    graph_items = build_graph_provenance(graph) if graph is not None else []
    finding_items = build_finding_provenance(findings, graph) if graph is not None else []
    items = [*field_items, *graph_items, *finding_items]
    summary = ProvenanceSummary(
        total_items=len(items),
        entity_items=sum(item.object_type == "ENTITY" for item in graph_items),
        event_items=sum(item.object_type == "EVENT" for item in graph_items),
        relationship_items=sum(item.object_type == "RELATIONSHIP" for item in graph_items),
        field_items=len(field_items),
        finding_items=len(finding_items),
    )
    return ProvenanceReport(case_id=case_id, summary=summary, items=items)
