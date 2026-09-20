from datetime import datetime, timedelta, timezone

from clarity.intelligence.anomaly_engine import AnomalyEngine, AnomalyEngineConfig
from clarity.intelligence.evidence_graph import EvidenceGraph, GraphEdge, GraphNode
from clarity.intelligence.models import InvestigationStatus, NodeKind
from clarity.intelligence.temporal_engine import TimeWindow


UTC = timezone.utc


def person(node_id: str, label: str) -> GraphNode:
    return GraphNode(id=node_id, kind=NodeKind.ENTITY, type="PERSON", label=label, confidence=1.0)


def event(event_id: str, ts: datetime, source: str, target: str | None = None, event_type: str = "CALL") -> GraphNode:
    metadata = {"timestamp": ts.isoformat(), "source_entity_id": source}
    if target is not None:
        metadata["target_entity_id"] = target
    return GraphNode(
        id=event_id,
        kind=NodeKind.EVENT,
        type=event_type,
        label=event_type,
        confidence=1.0,
        metadata=metadata,
    )


def edge(edge_id: str, source: str, target: str) -> GraphEdge:
    return GraphEdge(
        id=edge_id,
        source_id=source,
        target_id=target,
        relationship_type="ASSOCIATED_WITH",
        confidence=1.0,
        status=InvestigationStatus.OBSERVED,
    )


def graph(nodes, edges=()) -> EvidenceGraph:
    adjacency = {node.id: set() for node in nodes}
    reverse = {node.id: set() for node in nodes}
    for item in edges:
        adjacency[item.source_id].add(item.target_id)
        reverse[item.target_id].add(item.source_id)
    return EvidenceGraph(
        contract_version="1.0",
        nodes={node.id: node for node in nodes},
        edges={item.id: item for item in edges},
        adjacency={key: sorted(value) for key, value in sorted(adjacency.items())},
        reverse_adjacency={key: sorted(value) for key, value in sorted(reverse.items())},
    )


def window() -> tuple[TimeWindow, TimeWindow]:
    baseline = TimeWindow(
        start=datetime(2026, 8, 1, tzinfo=UTC),
        end=datetime(2026, 8, 7, 23, 59, 59, tzinfo=UTC),
    )
    target = TimeWindow(
        start=datetime(2026, 8, 8, tzinfo=UTC),
        end=datetime(2026, 8, 14, 23, 59, 59, tzinfo=UTC),
    )
    return target, baseline


def test_no_activity_produces_no_findings():
    target, baseline = window()
    g = graph([person("P1", "A")])
    report = AnomalyEngine().analyze(g, target, baseline_window=baseline)
    assert report.findings == []
    assert report.evaluated_entity_count == 1


def test_activity_spike_is_detected_and_has_event_evidence():
    target, baseline = window()
    nodes = [person("P1", "Alice")]
    for index, day in enumerate(range(1, 7), start=1):
        nodes.append(event(f"B{index}", datetime(2026, 8, day, 10, 0, tzinfo=UTC), "P1"))
    for index in range(1, 6):
        nodes.append(event(f"T{index}", datetime(2026, 8, 8, 10, index, tzinfo=UTC), "P1"))
    report = AnomalyEngine().analyze(graph(nodes), target, baseline_window=baseline)
    finding = next(item for item in report.findings if item.anomaly_type == "ACTIVITY_SPIKE")
    assert finding.entity_id == "P1"
    assert finding.score > 0
    assert finding.supporting_event_ids == [f"T{i}" for i in range(1, 6)]


def test_novel_relationship_is_detected():
    target, baseline = window()
    nodes = [person("A", "A"), person("B", "B")]
    nodes += [event("B1", datetime(2026, 8, 2, 10, tzinfo=UTC), "A", "A")]
    nodes += [event("T1", datetime(2026, 8, 8, 12, tzinfo=UTC), "A", "B")]
    report = AnomalyEngine().analyze(graph(nodes), target, baseline_window=baseline)
    finding = next(item for item in report.findings if item.anomaly_type == "NOVEL_RELATIONSHIP")
    assert (finding.source_entity_id, finding.target_entity_id) == ("A", "B")
    assert finding.supporting_event_ids == ["T1"]


def test_interaction_burst_requires_minimum_events():
    target, baseline = window()
    nodes = [person("A", "A"), person("B", "B")]
    nodes += [event("T1", datetime(2026, 8, 8, 12, 1, tzinfo=UTC), "A", "B")]
    nodes += [event("T2", datetime(2026, 8, 8, 12, 2, tzinfo=UTC), "A", "B")]
    report = AnomalyEngine().analyze(graph(nodes), target, baseline_window=baseline)
    assert not any(item.anomaly_type == "INTERACTION_BURST" for item in report.findings)


def test_interaction_burst_is_detected():
    target, baseline = window()
    nodes = [person("A", "A"), person("B", "B")]
    for index in range(1, 5):
        nodes.append(event(f"T{index}", datetime(2026, 8, 8, 12, index, tzinfo=UTC), "A", "B"))
    report = AnomalyEngine().analyze(graph(nodes), target, baseline_window=baseline)
    assert any(item.anomaly_type == "INTERACTION_BURST" for item in report.findings)


def test_cross_community_activity_uses_baseline_components():
    target, baseline = window()
    nodes = [person("A", "A"), person("B", "B"), person("C", "C"), person("D", "D")]
    edges = [edge("R1", "A", "B"), edge("R2", "C", "D")]
    nodes += [event("B1", datetime(2026, 8, 2, 9, tzinfo=UTC), "A", "B")]
    nodes += [event("B2", datetime(2026, 8, 2, 10, tzinfo=UTC), "C", "D")]
    nodes += [event("T1", datetime(2026, 8, 8, 15, tzinfo=UTC), "B", "C")]
    report = AnomalyEngine().analyze(graph(nodes, edges), target, baseline_window=baseline)
    assert any(item.anomaly_type == "CROSS_COMMUNITY_ACTIVITY" for item in report.findings)


def test_structural_activity_convergence_is_detected():
    target, baseline = window()
    nodes = [person("X", "Bridge"), person("A", "A"), person("B", "B"), person("C", "C"), person("D", "D")]
    edges = [edge("R1", "A", "X"), edge("R2", "X", "B"), edge("R3", "C", "X"), edge("R4", "X", "D")]
    for index, name in enumerate(["B1", "B2", "B3", "B4"]):
        nodes.append(event(name, datetime(2026, 8, 2, 9 + index, tzinfo=UTC), "X", "A"))
    for index in range(4):
        nodes.append(event(f"T{index}", datetime(2026, 8, 8, 12, index, tzinfo=UTC), "X", "B"))
    report = AnomalyEngine().analyze(graph(nodes, edges), target, baseline_window=baseline)
    assert any(item.anomaly_type == "STRUCTURAL_ACTIVITY_CONVERGENCE" for item in report.findings)


def test_undated_event_does_not_create_target_finding_and_is_reported():
    target, baseline = window()
    nodes = [person("P1", "A"), GraphNode(
        id="EV_UNDATED", kind=NodeKind.EVENT, type="CALL", label="CALL", confidence=1.0,
        metadata={"source_entity_id": "P1"},
    )]
    report = AnomalyEngine().analyze(graph(nodes), target, baseline_window=baseline)
    assert any(issue.code == "UNDATED_EVENT" for issue in report.issues)
    assert report.findings == []


def test_invalid_timestamp_is_reported_without_inventing_a_date():
    target, baseline = window()
    nodes = [person("P1", "A"), GraphNode(
        id="EV_BAD", kind=NodeKind.EVENT, type="CALL", label="CALL", confidence=1.0,
        metadata={"timestamp": "not-a-date", "source_entity_id": "P1"},
    )]
    report = AnomalyEngine().analyze(graph(nodes), target, baseline_window=baseline)
    assert any(issue.code == "INVALID_EVENT_TIME" for issue in report.issues)


def test_custom_entity_types_can_include_organization():
    target, baseline = window()
    org = GraphNode(id="O1", kind=NodeKind.ENTITY, type="ORGANIZATION", label="Org", confidence=1.0)
    nodes = [org, event("T1", datetime(2026, 8, 8, 12, tzinfo=UTC), "O1")]
    config = AnomalyEngineConfig(target_entity_types=["ORGANIZATION"])
    report = AnomalyEngine(config).analyze(graph(nodes), target, baseline_window=baseline)
    assert report.evaluated_entity_count == 1
    assert any(item.entity_id == "O1" for item in report.findings)


def test_findings_have_stable_order_and_ids():
    target, baseline = window()
    nodes = [person("A", "A"), person("B", "B")]
    nodes += [event("T1", datetime(2026, 8, 8, 10, 1, tzinfo=UTC), "A", "B")]
    nodes += [event("T2", datetime(2026, 8, 8, 10, 2, tzinfo=UTC), "A", "B")]
    engine = AnomalyEngine()
    first = engine.analyze(graph(nodes), target, baseline_window=baseline)
    second = engine.analyze(graph(nodes), target, baseline_window=baseline)
    assert [f.model_dump() for f in first.findings] == [f.model_dump() for f in second.findings]
    assert [f.finding_id for f in first.findings] == sorted([f.finding_id for f in first.findings])


def test_max_findings_is_respected():
    target, baseline = window()
    nodes = [person("A", "A")]
    for index in range(20):
        nodes.append(event(f"T{index:02d}", datetime(2026, 8, 8, 10, index, tzinfo=UTC), "A"))
    engine = AnomalyEngine(AnomalyEngineConfig(max_findings=1))
    report = engine.analyze(graph(nodes), target, baseline_window=baseline)
    assert report.finding_count <= 1


def test_default_baseline_is_immediately_preceding_equal_duration():
    target = TimeWindow(
        start=datetime(2026, 8, 8, tzinfo=UTC),
        end=datetime(2026, 8, 14, 23, 59, 59, tzinfo=UTC),
    )
    nodes = [person("P1", "A"), event("T1", datetime(2026, 8, 8, 10, tzinfo=UTC), "P1")]
    report = AnomalyEngine().analyze(graph(nodes), target)
    assert report.findings
    finding = report.findings[0]
    assert finding.baseline_window.end < target.start


def test_relationship_provenance_is_preserved_for_temporal_pattern():
    target, baseline = window()
    nodes = [person("A", "A"), person("B", "B"), event("T1", datetime(2026, 8, 8, 10, tzinfo=UTC), "A", "B")]
    edges = [edge("R1", "A", "B")]
    report = AnomalyEngine().analyze(graph(nodes, edges), target, baseline_window=baseline)
    finding = next(item for item in report.findings if item.anomaly_type == "NOVEL_RELATIONSHIP")
    assert finding.supporting_relationship_ids == ["R1"]
