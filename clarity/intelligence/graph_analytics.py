"""Deterministic graph analytics over the canonical EvidenceGraph.

This module implements the first analytical layer required by PS #13:
key-individual identification, community discovery, path analysis, and
bridge/intermediary detection.

Important safety/design constraints:
- The analytics layer ranks network roles, not criminality or guilt.
- EvidenceGraph remains the source of truth; this module never mutates it.
- All outputs are deterministic for a fixed graph/configuration.
- Entity-only analysis is used for person/organization network metrics.
  Event nodes can optionally contribute interaction edges through their
  explicit source_entity_id/target_entity_id metadata.
- No relationship is invented from document ordering or missing data.
- Scores are analytical priority/influence scores, not probabilities of guilt.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from math import isfinite
from typing import Any, Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field

from clarity.intelligence.evidence_graph import EvidenceGraph, GraphEdge, GraphNode
from clarity.intelligence.models import InvestigationStatus, NodeKind


class GraphAnalyticsError(ValueError):
    """Raised when a graph analytical operation cannot be completed safely."""


class GraphAnalyticsConfig(BaseModel):
    """Configuration for deterministic graph analytics."""

    model_config = ConfigDict(extra="forbid")

    target_entity_types: list[str] = Field(default_factory=lambda: ["PERSON"])
    include_entity_types: list[str] = Field(default_factory=list)
    include_event_interactions: bool = True
    max_pagerank_iterations: int = Field(default=100, ge=1, le=10_000)
    pagerank_tolerance: float = Field(default=1e-9, gt=0.0, lt=1.0)
    community_max_iterations: int = Field(default=50, ge=1, le=1_000)


class GraphAnalyticsIssue(BaseModel):
    """Non-silent quality issue encountered during analytics."""

    model_config = ConfigDict(extra="forbid")

    severity: str
    code: str
    message: str
    object_id: str | None = None


class NodeMetrics(BaseModel):
    """Network metrics for one eligible entity."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    label: str
    entity_type: str
    degree: int = Field(ge=0)
    weighted_degree: float = Field(ge=0.0)
    degree_centrality: float = Field(ge=0.0, le=1.0)
    betweenness_centrality: float = Field(ge=0.0, le=1.0)
    closeness_centrality: float = Field(ge=0.0, le=1.0)
    pagerank: float = Field(ge=0.0)
    community_id: str | None = None


class KeyIndividual(BaseModel):
    """Ranked network-influence lead; never a criminality judgment."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    label: str
    entity_type: str
    influence_score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)
    reasons: list[str] = Field(default_factory=list)
    metrics: NodeMetrics


class Community(BaseModel):
    """A deterministic graph community produced by label propagation."""

    model_config = ConfigDict(extra="forbid")

    community_id: str
    member_ids: list[str] = Field(default_factory=list)
    member_count: int = Field(ge=0)


class BridgeCandidate(BaseModel):
    """Entity that connects otherwise different communities."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    label: str
    entity_type: str
    bridge_score: float = Field(ge=0.0, le=1.0)
    betweenness_centrality: float = Field(ge=0.0, le=1.0)
    cross_community_ratio: float = Field(ge=0.0, le=1.0)
    neighbor_community_ids: list[str] = Field(default_factory=list)
    supporting_relationship_ids: list[str] = Field(default_factory=list)
    supporting_event_ids: list[str] = Field(default_factory=list)
    status: str = "INVESTIGATIVE_LEAD"


class PathResult(BaseModel):
    """Shortest undirected path over the analytical entity projection."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    target_id: str
    path: list[str] = Field(default_factory=list)
    hop_count: int = Field(default=0, ge=0)
    relationship_ids: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)


class GraphAnalyticsReport(BaseModel):
    """Complete deterministic analytics report for one evidence graph."""

    model_config = ConfigDict(extra="forbid")

    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    eligible_entity_count: int = Field(ge=0)
    projected_relationship_count: int = Field(ge=0)
    metrics: list[NodeMetrics] = Field(default_factory=list)
    communities: list[Community] = Field(default_factory=list)
    key_individuals: list[KeyIndividual] = Field(default_factory=list)
    bridge_candidates: list[BridgeCandidate] = Field(default_factory=list)
    issues: list[GraphAnalyticsIssue] = Field(default_factory=list)


@dataclass(frozen=True)
class _Projection:
    adjacency: Mapping[str, tuple[str, ...]]
    pair_relationship_ids: Mapping[tuple[str, str], tuple[str, ...]]
    pair_event_ids: Mapping[tuple[str, str], tuple[str, ...]]
    pair_weight: Mapping[tuple[str, str], float]


def _undirected_pair(left: str, right: str) -> tuple[str, str] | None:
    if left == right:
        return None
    return (left, right) if left < right else (right, left)


def _normalize_weights(values: Mapping[str, float]) -> dict[str, float]:
    finite = {key: float(value) for key, value in values.items() if isfinite(float(value))}
    if not finite:
        return {key: 0.0 for key in values}
    maximum = max(finite.values())
    if maximum <= 0:
        return {key: 0.0 for key in values}
    return {key: max(0.0, min(1.0, float(value) / maximum)) for key, value in values.items()}


class GraphAnalyticsEngine:
    """Deterministic graph analytics over EvidenceGraph."""

    def __init__(self, config: GraphAnalyticsConfig | None = None) -> None:
        self.config = config or GraphAnalyticsConfig()

    def analyze(self, graph: EvidenceGraph) -> GraphAnalyticsReport:
        projection, issues = self._build_projection(graph)
        eligible_ids = sorted(projection.adjacency)
        communities = self.detect_communities(graph)
        community_lookup = {
            member_id: community.community_id
            for community in communities
            for member_id in community.member_ids
        }
        metrics = self.compute_metrics(graph, projection=projection, community_lookup=community_lookup)
        key_individuals = self.rank_key_individuals(metrics)
        bridge_candidates = self.find_bridge_candidates(
            graph,
            projection=projection,
            metrics=metrics,
            community_lookup=community_lookup,
        )
        projected_pairs = set(projection.pair_relationship_ids) | set(projection.pair_event_ids)
        projected_relationship_count = len(projected_pairs)
        return GraphAnalyticsReport(
            node_count=graph.node_count,
            edge_count=graph.edge_count,
            eligible_entity_count=len(eligible_ids),
            projected_relationship_count=projected_relationship_count,
            metrics=metrics,
            communities=communities,
            key_individuals=key_individuals,
            bridge_candidates=bridge_candidates,
            issues=issues,
        )

    def _eligible(self, node: GraphNode) -> bool:
        if node.kind != NodeKind.ENTITY:
            return False
        if self.config.include_entity_types:
            return node.type in self.config.include_entity_types
        return node.type in self.config.target_entity_types

    def _build_projection(self, graph: EvidenceGraph) -> tuple[_Projection, list[GraphAnalyticsIssue]]:
        eligible = {node.id for node in graph.nodes.values() if self._eligible(node)}
        adjacency: dict[str, set[str]] = {node_id: set() for node_id in eligible}
        pair_relationship_ids: dict[tuple[str, str], list[str]] = {}
        pair_event_ids: dict[tuple[str, str], list[str]] = {}
        pair_weight: dict[tuple[str, str], float] = {}
        issues: list[GraphAnalyticsIssue] = []

        def add_pair(
            left: str,
            right: str,
            *,
            weight: float,
            relationship_id: str | None = None,
            event_id: str | None = None,
        ) -> None:
            pair = _undirected_pair(left, right)
            if pair is None or pair[0] not in eligible or pair[1] not in eligible:
                return
            adjacency[pair[0]].add(pair[1])
            adjacency[pair[1]].add(pair[0])
            pair_weight[pair] = pair_weight.get(pair, 0.0) + max(0.0, weight)
            if relationship_id is not None:
                pair_relationship_ids.setdefault(pair, []).append(relationship_id)
            if event_id is not None:
                pair_event_ids.setdefault(pair, []).append(event_id)

        for edge in graph.edges.values():
            if edge.source_id in eligible and edge.target_id in eligible:
                add_pair(
                    edge.source_id,
                    edge.target_id,
                    weight=max(0.05, edge.confidence),
                    relationship_id=edge.id,
                )

        if self.config.include_event_interactions:
            for node in graph.nodes.values():
                if node.kind != NodeKind.EVENT:
                    continue
                source_id = node.metadata.get("source_entity_id")
                target_id = node.metadata.get("target_entity_id")
                if not source_id or not target_id:
                    continue
                if source_id not in eligible or target_id not in eligible:
                    continue
                event_weight = float(node.confidence) if node.confidence else 1.0
                add_pair(source_id, target_id, weight=max(0.05, event_weight), event_id=node.id)

        for mapping in (pair_relationship_ids, pair_event_ids):
            for pair in mapping:
                mapping[pair] = sorted(set(mapping[pair]))

        return (
            _Projection(
                adjacency={key: tuple(sorted(value)) for key, value in sorted(adjacency.items())},
                pair_relationship_ids={key: tuple(value) for key, value in sorted(pair_relationship_ids.items())},
                pair_event_ids={key: tuple(value) for key, value in sorted(pair_event_ids.items())},
                pair_weight={key: value for key, value in sorted(pair_weight.items())},
            ),
            issues,
        )

    def compute_metrics(
        self,
        graph: EvidenceGraph,
        *,
        projection: _Projection | None = None,
        community_lookup: Mapping[str, str] | None = None,
    ) -> list[NodeMetrics]:
        projection = projection or self._build_projection(graph)[0]
        betweenness = self._betweenness(projection.adjacency)
        closeness = self._closeness(projection.adjacency)
        pagerank = self._pagerank(projection.adjacency)
        degree_centrality: dict[str, float] = {}
        weighted_degree: dict[str, float] = {node_id: 0.0 for node_id in projection.adjacency}
        pair_weights = projection.pair_weight
        for node_id, neighbors in projection.adjacency.items():
            degree_centrality[node_id] = len(neighbors) / max(1, len(projection.adjacency) - 1)
        for pair, weight in pair_weights.items():
            left, right = pair
            if left in weighted_degree:
                weighted_degree[left] += weight
            if right in weighted_degree:
                weighted_degree[right] += weight

        result: list[NodeMetrics] = []
        for node_id in sorted(projection.adjacency):
            node = graph.nodes[node_id]
            result.append(
                NodeMetrics(
                    node_id=node_id,
                    label=node.label,
                    entity_type=node.type,
                    degree=len(projection.adjacency[node_id]),
                    weighted_degree=round(weighted_degree[node_id], 12),
                    degree_centrality=round(degree_centrality[node_id], 12),
                    betweenness_centrality=round(betweenness.get(node_id, 0.0), 12),
                    closeness_centrality=round(closeness.get(node_id, 0.0), 12),
                    pagerank=round(pagerank.get(node_id, 0.0), 12),
                    community_id=(community_lookup or {}).get(node_id),
                )
            )
        return result

    def detect_communities(self, graph: EvidenceGraph) -> list[Community]:
        projection, _ = self._build_projection(graph)
        labels: dict[str, str] = {node_id: node_id for node_id in projection.adjacency}
        if not labels:
            return []

        for _ in range(self.config.community_max_iterations):
            changed = False
            for node_id in sorted(labels):
                neighbors = projection.adjacency[node_id]
                if not neighbors:
                    continue
                counts = Counter(labels[neighbor] for neighbor in neighbors)
                best_count = max(counts.values())
                best_labels = sorted(label for label, count in counts.items() if count == best_count)
                new_label = best_labels[0]
                if new_label != labels[node_id]:
                    labels[node_id] = new_label
                    changed = True
            if not changed:
                break

        groups: dict[str, list[str]] = {}
        for node_id, label in labels.items():
            groups.setdefault(label, []).append(node_id)

        ordered_groups = sorted(groups.values(), key=lambda members: (members[0], len(members)))
        communities: list[Community] = []
        for index, members in enumerate(ordered_groups, start=1):
            member_ids = sorted(members)
            communities.append(
                Community(
                    community_id=f"COMM_{index:03d}",
                    member_ids=member_ids,
                    member_count=len(member_ids),
                )
            )
        return communities

    def rank_key_individuals(
        self,
        metrics: Iterable[NodeMetrics],
        *,
        top_k: int | None = None,
    ) -> list[KeyIndividual]:
        metrics_list = list(metrics)
        if not metrics_list:
            return []
        influence = {
            item.node_id: (
                0.25 * item.degree_centrality
                + 0.35 * item.betweenness_centrality
                + 0.15 * item.closeness_centrality
                + 0.25 * item.pagerank
            )
            for item in metrics_list
        }
        influence = _normalize_weights(influence)
        by_id = {item.node_id: item for item in metrics_list}
        ordered = sorted(
            metrics_list,
            key=lambda item: (-influence[item.node_id], -item.betweenness_centrality, item.node_id),
        )
        if top_k is not None:
            if top_k < 1:
                raise ValueError("top_k must be >= 1 when provided")
            ordered = ordered[:top_k]

        results: list[KeyIndividual] = []
        for rank, item in enumerate(ordered, start=1):
            reasons: list[str] = []
            if item.betweenness_centrality >= 0.5:
                reasons.append("high_betweenness")
            if item.degree_centrality >= 0.5:
                reasons.append("high_connectivity")
            if item.closeness_centrality >= 0.5:
                reasons.append("short_network_distance")
            average_pagerank = (
                sum(metric.pagerank for metric in metrics_list) / len(metrics_list)
                if metrics_list
                else 0.0
            )
            if item.pagerank >= average_pagerank:
                reasons.append("high_recursive_network_influence")
            if not reasons:
                reasons.append("combined_network_metrics")
            results.append(
                KeyIndividual(
                    node_id=item.node_id,
                    label=item.label,
                    entity_type=item.entity_type,
                    influence_score=round(influence[item.node_id], 12),
                    rank=rank,
                    reasons=reasons,
                    metrics=by_id[item.node_id],
                )
            )
        return results

    def find_bridge_candidates(
        self,
        graph: EvidenceGraph,
        *,
        projection: _Projection | None = None,
        metrics: Iterable[NodeMetrics] | None = None,
        community_lookup: Mapping[str, str] | None = None,
        minimum_cross_community_ratio: float = 0.5,
    ) -> list[BridgeCandidate]:
        """Find structural intermediary candidates.

        A candidate is considered a bridge when removing the candidate splits
        its eligible neighbors across at least two local components. This is
        stronger than relying only on a global community detector and works
        for articulation-style bridge roles even when community propagation
        merges the whole graph into one global community.
        """
        if not 0.0 <= minimum_cross_community_ratio <= 1.0:
            raise ValueError("minimum_cross_community_ratio must be between 0 and 1")
        projection = projection or self._build_projection(graph)[0]
        metrics_list = list(metrics) if metrics is not None else self.compute_metrics(graph, projection=projection)
        metric_by_id = {item.node_id: item for item in metrics_list}
        candidates: list[BridgeCandidate] = []

        for node_id in sorted(projection.adjacency):
            neighbors = projection.adjacency[node_id]
            if len(neighbors) < 2:
                continue

            remaining = {
                item_id: tuple(
                    neighbor
                    for neighbor in projection.adjacency[item_id]
                    if neighbor != node_id
                )
                for item_id in projection.adjacency
                if item_id != node_id
            }
            local_components = self._connected_components(remaining)
            local_community_by_node: dict[str, str] = {}
            for index, component in enumerate(local_components, start=1):
                local_id = f"LOCAL_{node_id}_{index:03d}"
                for member in component:
                    local_community_by_node[member] = local_id

            neighbor_groups = sorted(
                {
                    local_community_by_node[neighbor]
                    for neighbor in neighbors
                    if neighbor in local_community_by_node
                }
            )
            if len(neighbor_groups) < 2:
                continue

            cross_ratio = len(neighbors) / max(1, len(neighbors))
            if cross_ratio < minimum_cross_community_ratio:
                continue
            metric = metric_by_id[node_id]
            bridge_score = min(1.0, 0.65 * metric.betweenness_centrality + 0.35 * cross_ratio)
            support_relationships: set[str] = set()
            support_events: set[str] = set()
            for neighbor in neighbors:
                pair = _undirected_pair(node_id, neighbor)
                if pair is None:
                    continue
                support_relationships.update(projection.pair_relationship_ids.get(pair, ()))
                support_events.update(projection.pair_event_ids.get(pair, ()))
            node = graph.nodes[node_id]
            # Use caller-supplied global community labels when they exist,
            # otherwise expose deterministic local structural groups.
            displayed_groups = sorted(
                {
                    community_lookup.get(neighbor)
                    for neighbor in neighbors
                    if community_lookup and community_lookup.get(neighbor) is not None
                }
            )
            if len(displayed_groups) < 2:
                displayed_groups = neighbor_groups
            candidates.append(
                BridgeCandidate(
                    node_id=node_id,
                    label=node.label,
                    entity_type=node.type,
                    bridge_score=round(bridge_score, 12),
                    betweenness_centrality=round(metric.betweenness_centrality, 12),
                    cross_community_ratio=round(cross_ratio, 12),
                    neighbor_community_ids=displayed_groups,
                    supporting_relationship_ids=sorted(support_relationships),
                    supporting_event_ids=sorted(support_events),
                )
            )
        return sorted(
            candidates,
            key=lambda item: (-item.bridge_score, -item.betweenness_centrality, item.node_id),
        )

    @staticmethod
    def _connected_components(adjacency: Mapping[str, tuple[str, ...]]) -> list[tuple[str, ...]]:
        """Return deterministic connected components for a simple graph."""
        unseen = set(adjacency)
        components: list[tuple[str, ...]] = []
        while unseen:
            start = min(unseen)
            queue: deque[str] = deque([start])
            seen = {start}
            unseen.remove(start)
            while queue:
                current = queue.popleft()
                for neighbor in adjacency.get(current, ()):
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        seen.add(neighbor)
                        queue.append(neighbor)
            components.append(tuple(sorted(seen)))
        return sorted(components, key=lambda component: (component[0], len(component)))

    def shortest_path(self, graph: EvidenceGraph, source_id: str, target_id: str) -> PathResult:
        projection, _ = self._build_projection(graph)
        if source_id not in projection.adjacency or target_id not in projection.adjacency:
            raise GraphAnalyticsError("Both path endpoints must be eligible entity nodes.")
        path = self._projection_shortest_path(projection.adjacency, source_id, target_id)
        if path is None:
            return PathResult(source_id=source_id, target_id=target_id)
        relationship_ids: set[str] = set()
        event_ids: set[str] = set()
        for left, right in zip(path, path[1:]):
            pair = _undirected_pair(left, right)
            if pair is None:
                continue
            relationship_ids.update(projection.pair_relationship_ids.get(pair, ()))
            event_ids.update(projection.pair_event_ids.get(pair, ()))
        return PathResult(
            source_id=source_id,
            target_id=target_id,
            path=path,
            hop_count=max(0, len(path) - 1),
            relationship_ids=sorted(relationship_ids),
            event_ids=sorted(event_ids),
        )

    @staticmethod
    def _projection_shortest_path(
        adjacency: Mapping[str, tuple[str, ...]], source_id: str, target_id: str
    ) -> list[str] | None:
        if source_id == target_id:
            return [source_id]
        queue: deque[str] = deque([source_id])
        parents: dict[str, str | None] = {source_id: None}
        while queue:
            current = queue.popleft()
            for neighbor in adjacency.get(current, ()):  # already sorted
                if neighbor in parents:
                    continue
                parents[neighbor] = current
                if neighbor == target_id:
                    path = [target_id]
                    while path[-1] != source_id:
                        parent = parents[path[-1]]
                        if parent is None:
                            break
                        path.append(parent)
                    path.reverse()
                    return path
                queue.append(neighbor)
        return None

    @staticmethod
    def _betweenness(adjacency: Mapping[str, tuple[str, ...]]) -> dict[str, float]:
        nodes = sorted(adjacency)
        centrality = dict.fromkeys(nodes, 0.0)
        for source in nodes:
            stack: list[str] = []
            predecessors: dict[str, list[str]] = {node: [] for node in nodes}
            sigma: dict[str, float] = dict.fromkeys(nodes, 0.0)
            sigma[source] = 1.0
            distance: dict[str, int] = {source: 0}
            queue: deque[str] = deque([source])
            while queue:
                current = queue.popleft()
                stack.append(current)
                for neighbor in adjacency[current]:
                    if neighbor not in distance:
                        distance[neighbor] = distance[current] + 1
                        queue.append(neighbor)
                    if distance[neighbor] == distance[current] + 1:
                        sigma[neighbor] += sigma[current]
                        predecessors[neighbor].append(current)
            dependency: dict[str, float] = dict.fromkeys(nodes, 0.0)
            while stack:
                node = stack.pop()
                for predecessor in predecessors[node]:
                    if sigma[node] > 0:
                        dependency[predecessor] += (
                            sigma[predecessor] / sigma[node]
                        ) * (1.0 + dependency[node])
                if node != source:
                    centrality[node] += dependency[node]
        for node in centrality:
            centrality[node] /= 2.0
        n = len(nodes)
        if n > 2:
            scale = 2.0 / ((n - 1) * (n - 2))
            centrality = {node: value * scale for node, value in centrality.items()}
        return centrality

    @staticmethod
    def _closeness(adjacency: Mapping[str, tuple[str, ...]]) -> dict[str, float]:
        result: dict[str, float] = {}
        n = len(adjacency)
        for source in sorted(adjacency):
            distance: dict[str, int] = {source: 0}
            queue: deque[str] = deque([source])
            while queue:
                current = queue.popleft()
                for neighbor in adjacency[current]:
                    if neighbor in distance:
                        continue
                    distance[neighbor] = distance[current] + 1
                    queue.append(neighbor)
            reachable = len(distance)
            if reachable <= 1:
                result[source] = 0.0
                continue
            total_distance = sum(distance.values())
            base = (reachable - 1) / total_distance if total_distance else 0.0
            result[source] = base * ((reachable - 1) / max(1, n - 1))
        return result

    def _pagerank(self, adjacency: Mapping[str, tuple[str, ...]]) -> dict[str, float]:
        nodes = sorted(adjacency)
        n = len(nodes)
        if n == 0:
            return {}
        damping = 0.85
        rank = {node: 1.0 / n for node in nodes}
        for _ in range(self.config.max_pagerank_iterations):
            base = (1.0 - damping) / n
            next_rank = {node: base for node in nodes}
            dangling_mass = sum(rank[node] for node in nodes if not adjacency[node])
            dangling_share = damping * dangling_mass / n
            for node in nodes:
                next_rank[node] += dangling_share
                neighbors = adjacency[node]
                if not neighbors:
                    continue
                contribution = damping * rank[node] / len(neighbors)
                for neighbor in neighbors:
                    next_rank[neighbor] += contribution
            diff = sum(abs(next_rank[node] - rank[node]) for node in nodes)
            rank = next_rank
            if diff < self.config.pagerank_tolerance:
                break
        return rank


__all__ = [
    "BridgeCandidate",
    "Community",
    "GraphAnalyticsConfig",
    "GraphAnalyticsEngine",
    "GraphAnalyticsError",
    "GraphAnalyticsIssue",
    "GraphAnalyticsReport",
    "KeyIndividual",
    "NodeMetrics",
    "PathResult",
]
