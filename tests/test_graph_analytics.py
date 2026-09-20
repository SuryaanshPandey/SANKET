from clarity.intelligence.evidence_graph import EvidenceGraph, GraphEdge, GraphNode
from clarity.intelligence.graph_analytics import (
    GraphAnalyticsConfig,
    GraphAnalyticsEngine,
)
from clarity.intelligence.models import InvestigationStatus, NodeKind


def make_node(node_id: str, label: str, entity_type: str = "PERSON") -> GraphNode:
    return GraphNode(
        id=node_id,
        kind=NodeKind.ENTITY,
        type=entity_type,
        label=label,
        confidence=1.0,
    )


def make_edge(edge_id: str, left: str, right: str, confidence: float = 1.0) -> GraphEdge:
    return GraphEdge(
        id=edge_id,
        source_id=left,
        target_id=right,
        relationship_type="ASSOCIATED_WITH",
        confidence=confidence,
        status=InvestigationStatus.OBSERVED,
    )


def make_graph(nodes: list[GraphNode], edges: list[GraphEdge]) -> EvidenceGraph:
    adjacency = {node.id: set() for node in nodes}
    reverse = {node.id: set() for node in nodes}
    for edge in edges:
        adjacency[edge.source_id].add(edge.target_id)
        reverse[edge.target_id].add(edge.source_id)
    return EvidenceGraph(
        contract_version="1.0",
        nodes={node.id: node for node in nodes},
        edges={edge.id: edge for edge in edges},
        adjacency={key: sorted(value) for key, value in sorted(adjacency.items())},
        reverse_adjacency={key: sorted(value) for key, value in sorted(reverse.items())},
    )


def test_metrics_on_star_graph_identifies_center():
    nodes = [make_node("P1", "Center"), make_node("P2", "A"), make_node("P3", "B"), make_node("P4", "C")]
    edges = [make_edge("R1", "P1", "P2"), make_edge("R2", "P1", "P3"), make_edge("R3", "P1", "P4")]
    graph = make_graph(nodes, edges)
    engine = GraphAnalyticsEngine()

    report = engine.analyze(graph)
    metrics = {item.node_id: item for item in report.metrics}

    assert metrics["P1"].degree == 3
    assert metrics["P1"].betweenness_centrality == 1.0
    assert metrics["P1"].degree_centrality == 1.0
    assert report.key_individuals[0].node_id == "P1"


def test_community_detection_separates_disconnected_components():
    nodes = [make_node("A", "A"), make_node("B", "B"), make_node("C", "C"), make_node("D", "D")]
    edges = [make_edge("R1", "A", "B"), make_edge("R2", "C", "D")]
    graph = make_graph(nodes, edges)
    communities = GraphAnalyticsEngine().detect_communities(graph)

    assert len(communities) == 2
    assert {tuple(c.member_ids) for c in communities} == {("A", "B"), ("C", "D")}


def test_bridge_candidate_is_detected_across_communities():
    nodes = [
        make_node("A1", "A1"),
        make_node("A2", "A2"),
        make_node("B1", "B1"),
        make_node("B2", "B2"),
        make_node("X", "Bridge"),
    ]
    edges = [
        make_edge("R1", "A1", "A2"),
        make_edge("R2", "B1", "B2"),
        make_edge("R3", "A2", "X"),
        make_edge("R4", "X", "B1"),
    ]
    graph = make_graph(nodes, edges)
    candidates = GraphAnalyticsEngine().find_bridge_candidates(graph)

    assert candidates
    assert candidates[0].node_id == "X"
    assert len(candidates[0].neighbor_community_ids) == 2
    assert candidates[0].cross_community_ratio == 1.0
    assert candidates[0].status == "INVESTIGATIVE_LEAD"


def test_shortest_path_returns_supporting_relationships():
    nodes = [make_node("A", "A"), make_node("B", "B"), make_node("C", "C")]
    edges = [make_edge("R1", "A", "B"), make_edge("R2", "B", "C")]
    graph = make_graph(nodes, edges)
    result = GraphAnalyticsEngine().shortest_path(graph, "A", "C")

    assert result.path == ["A", "B", "C"]
    assert result.hop_count == 2
    assert result.relationship_ids == ["R1", "R2"]


def test_event_interaction_is_projected_without_mutating_graph():
    nodes = [
        make_node("A", "A"),
        make_node("B", "B"),
        GraphNode(
            id="EV1",
            kind=NodeKind.EVENT,
            type="CALL",
            label="Call",
            confidence=1.0,
            metadata={"source_entity_id": "A", "target_entity_id": "B"},
        ),
    ]
    graph = make_graph(nodes, [])
    report = GraphAnalyticsEngine().analyze(graph)

    assert report.eligible_entity_count == 2
    assert report.projected_relationship_count == 1
    assert report.metrics[0].degree == 1
    assert graph.edge_count == 0


def test_config_can_include_multiple_entity_types():
    nodes = [make_node("P1", "Person", "PERSON"), make_node("O1", "Org", "ORGANIZATION")]
    edges = [make_edge("R1", "P1", "O1")]
    graph = make_graph(nodes, edges)
    engine = GraphAnalyticsEngine(GraphAnalyticsConfig(include_entity_types=["PERSON", "ORGANIZATION"]))

    report = engine.analyze(graph)
    assert report.eligible_entity_count == 2
    assert {metric.entity_type for metric in report.metrics} == {"PERSON", "ORGANIZATION"}


def test_isolated_person_is_preserved_with_zero_centralities():
    graph = make_graph([make_node("P1", "Solo")], [])
    report = GraphAnalyticsEngine().analyze(graph)

    assert len(report.metrics) == 1
    metric = report.metrics[0]
    assert metric.degree == 0
    assert metric.degree_centrality == 0.0
    assert metric.betweenness_centrality == 0.0
    assert metric.closeness_centrality == 0.0


def test_unreachable_shortest_path_returns_empty_result():
    nodes = [make_node("A", "A"), make_node("B", "B")]
    graph = make_graph(nodes, [])
    result = GraphAnalyticsEngine().shortest_path(graph, "A", "B")

    assert result.path == []
    assert result.hop_count == 0
    assert result.relationship_ids == []


def test_top_k_is_deterministic():
    nodes = [make_node("P1", "1"), make_node("P2", "2"), make_node("P3", "3")]
    edges = [make_edge("R1", "P1", "P2"), make_edge("R2", "P2", "P3")]
    graph = make_graph(nodes, edges)
    engine = GraphAnalyticsEngine()
    metrics = engine.compute_metrics(graph)

    first = engine.rank_key_individuals(metrics, top_k=2)
    second = engine.rank_key_individuals(metrics, top_k=2)
    assert [x.node_id for x in first] == [x.node_id for x in second]


def test_analysis_report_preserves_network_role_language():
    nodes = [make_node("P1", "Lead"), make_node("P2", "Other")]
    graph = make_graph(nodes, [make_edge("R1", "P1", "P2")])
    report = GraphAnalyticsEngine().analyze(graph)

    assert report.key_individuals[0].influence_score >= 0.0
    assert report.bridge_candidates == []
    assert report.key_individuals[0].reasons
