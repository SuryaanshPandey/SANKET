"""Canonical evidence graph builder and query layer.

This module converts the canonical Clarity post-extraction models, together
with confirmed entity-resolution clusters, into a deterministic in-memory
evidence graph. It deliberately remains database-agnostic so Neo4j persistence
can be added later without changing the analytical contract.

Design goals:
- preserve evidence/provenance instead of flattening relationships to bare edges;
- remap confirmed entity-resolution aliases to one canonical node;
- retain event nodes as first-class nodes;
- keep observed/inferred/hypothesis status explicit;
- detect structural integrity problems instead of silently dropping data;
- provide deterministic adjacency/query operations for later analytics.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field

from clarity.intelligence.entity_resolution import (
    EntityResolutionResult,
    ResolvedEntityCluster,
)
from clarity.intelligence.models import (
    CanonicalEntity,
    CanonicalEvent,
    CanonicalRelationship,
    EvidenceReference,
    InvestigationGraph,
    InvestigationStatus,
    NodeKind,
)


class EvidenceGraphError(ValueError):
    """Raised when an evidence graph cannot be built safely."""


class GraphBuildConfig(BaseModel):
    """Controls how the in-memory evidence graph is built."""

    model_config = ConfigDict(extra="forbid")

    merge_confirmed_entities: bool = True
    include_events: bool = True
    reject_dangling_relationships: bool = True


class GraphNode(BaseModel):
    """A graph node retaining its original evidence semantics."""

    model_config = ConfigDict(extra="forbid")

    id: str
    kind: NodeKind
    type: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_refs: list[EvidenceReference] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """An evidence-aware directed graph edge."""

    model_config = ConfigDict(extra="forbid")

    id: str
    source_id: str
    target_id: str
    relationship_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    status: InvestigationStatus = InvestigationStatus.OBSERVED
    evidence_text: Optional[str] = None
    source_refs: list[EvidenceReference] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphBuildIssue(BaseModel):
    """Non-silent issue captured during graph construction."""

    model_config = ConfigDict(extra="forbid")

    severity: str
    code: str
    message: str
    node_id: Optional[str] = None
    relationship_id: Optional[str] = None


class EvidenceGraph(BaseModel):
    """Deterministic, database-agnostic in-memory evidence graph."""

    model_config = ConfigDict(extra="forbid")

    contract_version: str
    case_id: Optional[str] = None
    batch_id: Optional[str] = None
    total_documents: int = Field(default=0, ge=0)
    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    edges: Dict[str, GraphEdge] = Field(default_factory=dict)
    adjacency: Dict[str, list[str]] = Field(default_factory=dict)
    reverse_adjacency: Dict[str, list[str]] = Field(default_factory=dict)
    entity_clusters: Dict[str, list[str]] = Field(default_factory=dict)
    issues: list[GraphBuildIssue] = Field(default_factory=list)
    audit_chain: Dict[str, Any] = Field(default_factory=dict)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def entity_count(self) -> int:
        return sum(node.kind == NodeKind.ENTITY for node in self.nodes.values())

    @property
    def event_count(self) -> int:
        return sum(node.kind == NodeKind.EVENT for node in self.nodes.values())

    def get_node(self, node_id: str) -> GraphNode:
        try:
            return self.nodes[node_id]
        except KeyError as exc:
            raise EvidenceGraphError(f"Unknown graph node '{node_id}'.") from exc

    def get_edge(self, edge_id: str) -> GraphEdge:
        try:
            return self.edges[edge_id]
        except KeyError as exc:
            raise EvidenceGraphError(f"Unknown graph edge '{edge_id}'.") from exc

    def neighbors(self, node_id: str, *, direction: str = "both") -> list[str]:
        """Return deterministic neighboring node IDs.

        direction: "out", "in", or "both".
        """
        if node_id not in self.nodes:
            raise EvidenceGraphError(f"Unknown graph node '{node_id}'.")
        if direction not in {"out", "in", "both"}:
            raise ValueError("direction must be 'out', 'in', or 'both'")
        values: set[str] = set()
        if direction in {"out", "both"}:
            values.update(self.adjacency.get(node_id, []))
        if direction in {"in", "both"}:
            values.update(self.reverse_adjacency.get(node_id, []))
        return sorted(values)

    def incident_edges(self, node_id: str) -> list[GraphEdge]:
        """Return deterministic incoming/outgoing edges for a node."""
        if node_id not in self.nodes:
            raise EvidenceGraphError(f"Unknown graph node '{node_id}'.")
        return sorted(
            [
                edge
                for edge in self.edges.values()
                if edge.source_id == node_id or edge.target_id == node_id
            ],
            key=lambda edge: edge.id,
        )

    def relationship_between(self, source_id: str, target_id: str) -> list[GraphEdge]:
        """Return all directed edges from source to target."""
        if source_id not in self.nodes or target_id not in self.nodes:
            raise EvidenceGraphError("Both source and target nodes must exist.")
        return sorted(
            [
                edge
                for edge in self.edges.values()
                if edge.source_id == source_id and edge.target_id == target_id
            ],
            key=lambda edge: edge.id,
        )

    def shortest_path(self, source_id: str, target_id: str) -> Optional[list[str]]:
        """Return a shortest undirected evidence path, if one exists."""
        if source_id not in self.nodes or target_id not in self.nodes:
            raise EvidenceGraphError("Both source and target nodes must exist.")
        if source_id == target_id:
            return [source_id]

        queue: deque[str] = deque([source_id])
        parent: dict[str, Optional[str]] = {source_id: None}
        while queue:
            current = queue.popleft()
            for neighbor in self.neighbors(current, direction="both"):
                if neighbor in parent:
                    continue
                parent[neighbor] = current
                if neighbor == target_id:
                    path = [target_id]
                    while path[-1] != source_id:
                        previous = parent[path[-1]]
                        if previous is None:
                            break
                        path.append(previous)
                    path.reverse()
                    return path
                queue.append(neighbor)
        return None

    def scoped(self, *, node_ids: set[str] | list[str] | tuple[str, ...] | None = None,
               edge_ids: set[str] | list[str] | tuple[str, ...] | None = None) -> "EvidenceGraph":
        """Return a deterministic, read-only-style scoped copy of this graph.

        The scope is explicit: nodes are limited to ``node_ids`` and edges are
        limited to ``edge_ids`` whose endpoints both remain present. Existing
        provenance, clusters and graph issues are preserved. This is used by
        the workflow engine so a TIME_FILTER / EXPAND node actually constrains
        downstream analytics instead of merely displaying a preview snapshot.
        """
        selected_nodes = set(node_ids or self.nodes.keys()) & set(self.nodes.keys())
        selected_edges = set(edge_ids or self.edges.keys()) & set(self.edges.keys())
        edges = {
            edge_id: edge for edge_id, edge in self.edges.items()
            if edge_id in selected_edges
            and edge.source_id in selected_nodes
            and edge.target_id in selected_nodes
        }
        nodes = {node_id: self.nodes[node_id] for node_id in sorted(selected_nodes)}
        adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes}
        reverse_adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes}
        for edge in sorted(edges.values(), key=lambda item: item.id):
            adjacency.setdefault(edge.source_id, []).append(edge.target_id)
            reverse_adjacency.setdefault(edge.target_id, []).append(edge.source_id)
        for mapping in (adjacency, reverse_adjacency):
            for key in mapping:
                mapping[key] = sorted(set(mapping[key]))
        clusters = {
            cluster_id: members
            for cluster_id, members in self.entity_clusters.items()
            if cluster_id in nodes
        }
        return self.model_copy(update={
            "nodes": nodes,
            "edges": dict(sorted(edges.items())),
            "adjacency": dict(sorted(adjacency.items())),
            "reverse_adjacency": dict(sorted(reverse_adjacency.items())),
            "entity_clusters": dict(sorted(clusters.items())),
        })

    def to_records(self) -> dict[str, Any]:
        """Return JSON-ready records for API/Neo4j adapters later."""
        return {
            "nodes": [node.model_dump(mode="json") for node in self.nodes.values()],
            "edges": [edge.model_dump(mode="json") for edge in self.edges.values()],
            "entity_clusters": self.entity_clusters,
            "issues": [issue.model_dump(mode="json") for issue in self.issues],
        }


@dataclass(frozen=True)
class _ClusterIndex:
    member_to_canonical: Mapping[str, str]
    canonical_to_cluster: Mapping[str, ResolvedEntityCluster]


class EvidenceGraphBuilder:
    """Build an evidence graph from Clarity's canonical graph plus resolution."""

    def __init__(self, config: GraphBuildConfig | None = None) -> None:
        self.config = config or GraphBuildConfig()

    def build(
        self,
        investigation_graph: InvestigationGraph,
        resolution: EntityResolutionResult | None = None,
    ) -> EvidenceGraph:
        cluster_index = self._build_cluster_index(resolution)
        issues: list[GraphBuildIssue] = []
        nodes: dict[str, GraphNode] = {}

        # Build entity nodes once per canonical ID. When a confirmed cluster
        # contains several raw entity mentions, aggregate their provenance and
        # compatible attributes instead of treating them as ID collisions.
        grouped: dict[str, list[CanonicalEntity]] = {}
        for entity in investigation_graph.entities:
            canonical_id = self._canonical_id(entity.id, cluster_index)
            grouped.setdefault(canonical_id, []).append(entity)

        for canonical_id in sorted(grouped):
            members = sorted(grouped[canonical_id], key=lambda item: item.id)
            node = self._merge_entity_members(canonical_id, members, cluster_index)
            self._insert_node(nodes, node, issues)

        if self.config.include_events:
            for event in investigation_graph.events:
                event_node = self._event_to_node(event, cluster_index)
                self._insert_node(nodes, event_node, issues)

        edges: dict[str, GraphEdge] = {}
        for relationship in investigation_graph.relationships:
            edge = self._relationship_to_edge(relationship, cluster_index)
            if edge.source_id not in nodes or edge.target_id not in nodes:
                issues.append(
                    GraphBuildIssue(
                        severity="error" if self.config.reject_dangling_relationships else "warning",
                        code="DANGLING_RELATIONSHIP",
                        message=(
                            f"Relationship '{edge.id}' references missing endpoint(s): "
                            f"{edge.source_id} -> {edge.target_id}."
                        ),
                        relationship_id=edge.id,
                    )
                )
                # A dangling edge is never inserted because doing so would
                # make the graph internally inconsistent. In non-strict mode
                # we retain the issue so callers can inspect what was dropped.
                continue

            if edge.source_id == edge.target_id and relationship.source_id != relationship.target_id:
                issues.append(
                    GraphBuildIssue(
                        severity="warning",
                        code="COLLAPSED_SELF_RELATIONSHIP",
                        message=(
                            f"Relationship '{edge.id}' collapsed to a self-relationship after entity "
                            f"resolution ({edge.source_id})."
                        ),
                        relationship_id=edge.id,
                    )
                )
                edge.metadata["collapsed_self_relationship"] = True

            self._insert_edge(edges, edge, issues)

        adjacency, reverse_adjacency = self._build_adjacency(nodes, edges)
        entity_clusters = self._cluster_payload(resolution)

        graph = EvidenceGraph(
            contract_version=investigation_graph.contract_version,
            case_id=investigation_graph.case_id,
            batch_id=investigation_graph.batch_id,
            total_documents=investigation_graph.total_documents,
            nodes=dict(sorted(nodes.items())),
            edges=dict(sorted(edges.items())),
            adjacency={key: adjacency[key] for key in sorted(adjacency)},
            reverse_adjacency={key: reverse_adjacency[key] for key in sorted(reverse_adjacency)},
            entity_clusters=dict(sorted(entity_clusters.items())),
            issues=issues,
            audit_chain=dict(investigation_graph.audit_chain),
        )
        self._raise_if_strict_failure(graph)
        return graph

    def _build_cluster_index(self, resolution: EntityResolutionResult | None) -> _ClusterIndex:
        if resolution is None or not self.config.merge_confirmed_entities:
            return _ClusterIndex(member_to_canonical={}, canonical_to_cluster={})
        member_to_canonical: dict[str, str] = {}
        canonical_to_cluster: dict[str, ResolvedEntityCluster] = {}
        for cluster in resolution.confirmed_clusters:
            canonical_to_cluster[cluster.canonical_entity_id] = cluster
            for member_id in cluster.member_ids:
                member_to_canonical[member_id] = cluster.canonical_entity_id
        return _ClusterIndex(member_to_canonical, canonical_to_cluster)

    @staticmethod
    def _canonical_id(entity_id: str, cluster_index: _ClusterIndex) -> str:
        return cluster_index.member_to_canonical.get(entity_id, entity_id)

    def _merge_entity_members(
        self,
        canonical_id: str,
        members: list[CanonicalEntity],
        cluster_index: _ClusterIndex,
    ) -> GraphNode:
        canonical = next((item for item in members if item.id == canonical_id), members[0])
        source_refs = _unique_source_refs([item.source for item in members])
        attributes, conflicts = _merge_attributes(members)
        aliases = sorted({item.name for item in members if item.name != canonical.name})
        metadata: dict[str, Any] = {
            "original_entity_id": canonical.id,
            "member_entity_ids": [item.id for item in members],
            "contract_types": sorted({item.contract_type for item in members if item.contract_type}),
            "roles": sorted({item.role for item in members if item.role}),
        }
        cluster = cluster_index.canonical_to_cluster.get(canonical_id)
        if cluster:
            metadata.update(
                {
                    "resolution_cluster_id": cluster.cluster_id,
                    "resolution_status": "CONFIRMED",
                    "aliases": sorted(set(cluster.aliases) | set(aliases)),
                    "source_document_ids": sorted(set(cluster.source_document_ids)),
                }
            )
        if conflicts:
            metadata["attribute_conflicts"] = conflicts

        confidence = min(item.confidence for item in members)
        return GraphNode(
            id=canonical_id,
            kind=NodeKind.ENTITY,
            type=canonical.type,
            label=canonical.normalized_name or canonical.name,
            confidence=confidence,
            source_refs=source_refs,
            attributes=attributes,
            metadata=metadata,
        )

    def _event_to_node(
        self,
        event: CanonicalEvent,
        cluster_index: _ClusterIndex,
    ) -> GraphNode:
        metadata = {
            "contract_type": event.contract_type,
            "timestamp": event.timestamp,
            "timestamp_start": event.timestamp_start,
            "timestamp_end": event.timestamp_end,
            "source_entity_id": (
                self._canonical_id(event.source_entity_id, cluster_index)
                if event.source_entity_id
                else None
            ),
            "target_entity_id": (
                self._canonical_id(event.target_entity_id, cluster_index)
                if event.target_entity_id
                else None
            ),
        }
        return GraphNode(
            id=event.id,
            kind=NodeKind.EVENT,
            type=event.type,
            label=event.title,
            confidence=1.0,
            source_refs=[event.source],
            attributes=dict(event.attributes),
            metadata=metadata,
        )

    def _relationship_to_edge(
        self,
        relationship: CanonicalRelationship,
        cluster_index: _ClusterIndex,
    ) -> GraphEdge:
        source_id = self._canonical_id(relationship.source_id, cluster_index)
        target_id = self._canonical_id(relationship.target_id, cluster_index)
        metadata = dict(relationship.metadata)
        metadata["original_source_id"] = relationship.source_id
        metadata["original_target_id"] = relationship.target_id
        return GraphEdge(
            id=relationship.id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship.relationship_type,
            confidence=relationship.confidence,
            status=relationship.status,
            evidence_text=relationship.evidence_text,
            source_refs=list(relationship.source_refs),
            metadata=metadata,
        )

    @staticmethod
    def _insert_node(nodes: dict[str, GraphNode], node: GraphNode, issues: list[GraphBuildIssue]) -> None:
        existing = nodes.get(node.id)
        if existing is None:
            nodes[node.id] = node
            return
        if existing.model_dump(mode="json") == node.model_dump(mode="json"):
            return
        issues.append(
            GraphBuildIssue(
                severity="error",
                code="NODE_COLLISION",
                message=f"Node ID '{node.id}' maps to incompatible node definitions.",
                node_id=node.id,
            )
        )

    @staticmethod
    def _insert_edge(edges: dict[str, GraphEdge], edge: GraphEdge, issues: list[GraphBuildIssue]) -> None:
        existing = edges.get(edge.id)
        if existing is None:
            edges[edge.id] = edge
            return
        if existing.model_dump(mode="json") == edge.model_dump(mode="json"):
            return
        issues.append(
            GraphBuildIssue(
                severity="error",
                code="EDGE_COLLISION",
                message=f"Relationship ID '{edge.id}' maps to incompatible edge definitions.",
                relationship_id=edge.id,
            )
        )

    @staticmethod
    def _build_adjacency(
        nodes: Mapping[str, GraphNode],
        edges: Mapping[str, GraphEdge],
    ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        adjacency: dict[str, set[str]] = {node_id: set() for node_id in nodes}
        reverse: dict[str, set[str]] = {node_id: set() for node_id in nodes}
        for edge in edges.values():
            if edge.source_id not in adjacency or edge.target_id not in adjacency:
                continue
            adjacency[edge.source_id].add(edge.target_id)
            reverse[edge.target_id].add(edge.source_id)
        return (
            {key: sorted(value) for key, value in adjacency.items()},
            {key: sorted(value) for key, value in reverse.items()},
        )

    @staticmethod
    def _cluster_payload(resolution: EntityResolutionResult | None) -> dict[str, list[str]]:
        if resolution is None:
            return {}
        return {
            cluster.canonical_entity_id: sorted(cluster.member_ids)
            for cluster in resolution.confirmed_clusters
        }

    @staticmethod
    def _raise_if_strict_failure(graph: EvidenceGraph) -> None:
        fatal_codes = {
            "DANGLING_RELATIONSHIP",
            "NODE_COLLISION",
            "EDGE_COLLISION",
        }
        fatal = [issue for issue in graph.issues if issue.code in fatal_codes and issue.severity == "error"]
        if fatal:
            summary = "; ".join(issue.message for issue in fatal[:5])
            raise EvidenceGraphError(summary)


def _unique_source_refs(refs: list[EvidenceReference]) -> list[EvidenceReference]:
    seen: set[tuple[Any, ...]] = set()
    result: list[EvidenceReference] = []
    for ref in refs:
        key = (
            ref.document_id,
            ref.filename,
            ref.file_hash_sha256,
            ref.page,
            tuple(sorted((ref.bounding_box or {}).items())),
            ref.text_span,
        )
        if key not in seen:
            seen.add(key)
            result.append(ref)
    return sorted(result, key=lambda ref: (ref.document_id, ref.page, ref.filename, ref.text_span or ""))


def _merge_attributes(members: list[CanonicalEntity]) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    values_by_key: dict[str, list[Any]] = {}
    for member in members:
        for key, value in member.attributes.items():
            values_by_key.setdefault(key, []).append(value)

    merged: dict[str, Any] = {}
    conflicts: dict[str, list[Any]] = {}
    for key, values in sorted(values_by_key.items()):
        unique = _unique_jsonish(values)
        if len(unique) == 1:
            merged[key] = unique[0]
        else:
            merged[key] = unique
            conflicts[key] = unique
    return merged, conflicts


def _unique_jsonish(values: list[Any]) -> list[Any]:
    unique: list[Any] = []
    seen: set[str] = set()
    for value in values:
        marker = repr(value)
        if marker not in seen:
            seen.add(marker)
            unique.append(value)
    unique.sort(key=lambda item: repr(item))
    return unique


def build_evidence_graph(
    investigation_graph: InvestigationGraph,
    resolution: EntityResolutionResult | None = None,
    config: GraphBuildConfig | None = None,
) -> EvidenceGraph:
    """Convenience function for the common graph-build operation."""
    return EvidenceGraphBuilder(config).build(investigation_graph, resolution)
