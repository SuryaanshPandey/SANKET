from clarity.intelligence import (
    EvidenceGraph,
    GraphEdge,
    GraphNode,
    InvestigationStatus,
    InvestigationWorkflow,
    InvestigationWorkflowEngine,
    NodeKind,
    WorkflowEdge,
    WorkflowFailurePolicy,
    WorkflowNode,
    WorkflowNodeType,
)


def _node(node_id: str, label: str, entity_type: str = "PERSON") -> GraphNode:
    return GraphNode(
        id=node_id,
        kind=NodeKind.ENTITY,
        type=entity_type,
        label=label,
        confidence=1.0,
        source_refs=[],
        attributes={},
        metadata={},
    )


def _event(event_id: str, source: str, target: str, timestamp: str) -> GraphNode:
    return GraphNode(
        id=event_id,
        kind=NodeKind.EVENT,
        type="CALL",
        label=event_id,
        confidence=1.0,
        source_refs=[],
        attributes={},
        metadata={"source_entity_id": source, "target_entity_id": target, "timestamp": timestamp},
    )


def _graph() -> EvidenceGraph:
    nodes = {
        "A": _node("A", "Alice"),
        "B": _node("B", "Bob"),
        "C": _node("C", "Charlie"),
        "E1": _event("E1", "A", "B", "2026-09-01T10:00:00+05:30"),
        "E2": _event("E2", "B", "C", "2026-09-01T11:00:00+05:30"),
        "E3": _event("E3", "A", "C", "2026-09-02T12:00:00+05:30"),
    }
    edges = {
        "R1": GraphEdge(id="R1", source_id="A", target_id="B", relationship_type="CALLED", confidence=0.9, status=InvestigationStatus.OBSERVED),
        "R2": GraphEdge(id="R2", source_id="B", target_id="C", relationship_type="CALLED", confidence=0.9, status=InvestigationStatus.OBSERVED),
        "R3": GraphEdge(id="R3", source_id="A", target_id="C", relationship_type="CALLED", confidence=0.8, status=InvestigationStatus.OBSERVED),
    }
    adjacency = {"A": ["B", "C"], "B": ["C"], "C": []}
    reverse = {"A": [], "B": ["A"], "C": ["A", "B"]}
    return EvidenceGraph(contract_version="1.0", nodes=nodes, edges=edges, adjacency=adjacency, reverse_adjacency=reverse)


def _workflow(nodes, edges=None, policy=WorkflowFailurePolicy.STOP):
    return InvestigationWorkflow(
        workflow_id="WF-001",
        version="1.0.0",
        name="Test Investigation",
        nodes=nodes,
        edges=edges or [],
        failure_policy=policy,
    )


def test_time_filter_node_executes():
    workflow = _workflow([
        WorkflowNode(id="time", type=WorkflowNodeType.TIME_FILTER, config={"start": "2026-09-01T00:00:00+05:30", "end": "2026-09-03T00:00:00+05:30"})
    ])
    result = InvestigationWorkflowEngine().execute(_graph(), workflow)
    assert result.status == "COMPLETED"
    assert result.node_results[0].output["event_ids"] == ["E1", "E2", "E3"]


def test_expand_network_uses_explicit_seed_and_depth():
    workflow = _workflow([
        WorkflowNode(id="expand", type=WorkflowNodeType.EXPAND_NETWORK, config={"seed_entity_ids": ["A"], "depth": 1})
    ])
    result = InvestigationWorkflowEngine().execute(_graph(), workflow)
    assert result.status == "COMPLETED"
    assert result.final_output["entity_ids"] == ["A", "B", "C"]


def test_workflow_passes_upstream_ids_to_expand_network():
    nodes = [
        WorkflowNode(id="time", type=WorkflowNodeType.TIME_FILTER, config={"start": "2026-09-01T00:00:00+05:30", "end": "2026-09-03T00:00:00+05:30"}),
        WorkflowNode(id="expand", type=WorkflowNodeType.EXPAND_NETWORK, config={"depth": 1}),
    ]
    edges = [WorkflowEdge(id="e1", source_node_id="time", target_node_id="expand")]
    result = InvestigationWorkflowEngine().execute(_graph(), _workflow(nodes, edges))
    assert result.status == "COMPLETED"
    assert result.node_results[1].output["seed_entity_ids"] == ["A", "B", "C"]


def test_graph_analytics_node_executes():
    workflow = _workflow([
        WorkflowNode(id="analytics", type=WorkflowNodeType.GRAPH_ANALYTICS, config={"target_entity_types": ["PERSON"]})
    ])
    result = InvestigationWorkflowEngine().execute(_graph(), workflow)
    assert result.status == "COMPLETED"
    assert "metrics" in result.final_output
    assert len(result.final_output["metrics"]) == 3


def test_key_individuals_node_respects_top_k():
    workflow = _workflow([
        WorkflowNode(id="keys", type=WorkflowNodeType.KEY_INDIVIDUALS, config={"top_k": 2})
    ])
    result = InvestigationWorkflowEngine().execute(_graph(), workflow)
    assert result.status == "COMPLETED"
    assert len(result.final_output["key_individuals"]) == 2


def test_community_and_bridge_nodes_execute():
    nodes = [
        WorkflowNode(id="communities", type=WorkflowNodeType.COMMUNITY_DETECTION, config={}),
        WorkflowNode(id="bridges", type=WorkflowNodeType.BRIDGE_ANALYSIS, config={"minimum_cross_community_ratio": 0.0}),
    ]
    edges = [WorkflowEdge(id="e1", source_node_id="communities", target_node_id="bridges")]
    result = InvestigationWorkflowEngine().execute(_graph(), _workflow(nodes, edges))
    assert result.status == "COMPLETED"
    assert "communities" in result.node_results[0].output
    assert "bridge_candidates" in result.node_results[1].output


def test_anomaly_node_executes():
    workflow = _workflow([
        WorkflowNode(id="anomaly", type=WorkflowNodeType.ANOMALY_DETECTION, config={
            "target_start": "2026-09-01T00:00:00+05:30",
            "target_end": "2026-09-03T00:00:00+05:30",
            "max_findings": 5,
        })
    ])
    result = InvestigationWorkflowEngine().execute(_graph(), workflow)
    assert result.status == "COMPLETED"
    assert "findings" in result.final_output


def test_shortest_path_node_executes():
    workflow = _workflow([
        WorkflowNode(id="path", type=WorkflowNodeType.SHORTEST_PATH, config={"source_id": "A", "target_id": "C"})
    ])
    result = InvestigationWorkflowEngine().execute(_graph(), workflow)
    assert result.status == "COMPLETED"
    assert result.final_output["path"] == ["A", "C"]


def test_evidence_review_collects_upstream_outputs():
    nodes = [
        WorkflowNode(id="expand", type=WorkflowNodeType.EXPAND_NETWORK, config={"seed_entity_ids": ["A"], "depth": 1}),
        WorkflowNode(id="review", type=WorkflowNodeType.EVIDENCE_REVIEW, config={}),
    ]
    edges = [WorkflowEdge(id="e1", source_node_id="expand", target_node_id="review")]
    result = InvestigationWorkflowEngine().execute(_graph(), _workflow(nodes, edges))
    assert result.status == "COMPLETED"
    assert {node["id"] for node in result.final_output["nodes"]} == {"A", "B", "C"}
    assert "evidence_references" in result.final_output


def test_report_aggregates_selected_inputs():
    nodes = [
        WorkflowNode(id="keys", type=WorkflowNodeType.KEY_INDIVIDUALS, config={"top_k": 2}),
        WorkflowNode(id="report", type=WorkflowNodeType.REPORT, config={"title": "Case Report", "include_node_outputs": ["keys"], "notes": "test"}),
    ]
    edges = [WorkflowEdge(id="e1", source_node_id="keys", target_node_id="report")]
    result = InvestigationWorkflowEngine().execute(_graph(), _workflow(nodes, edges))
    assert result.status == "COMPLETED"
    assert result.final_output["title"] == "Case Report"
    assert "keys" in result.final_output["sections"]


def test_validation_rejects_cycle():
    nodes = [
        WorkflowNode(id="a", type=WorkflowNodeType.KEY_INDIVIDUALS),
        WorkflowNode(id="b", type=WorkflowNodeType.COMMUNITY_DETECTION),
    ]
    edges = [
        WorkflowEdge(id="e1", source_node_id="a", target_node_id="b"),
        WorkflowEdge(id="e2", source_node_id="b", target_node_id="a"),
    ]
    result = InvestigationWorkflowEngine().execute(_graph(), _workflow(nodes, edges))
    assert result.status == "VALIDATION_FAILED"
    assert any(issue.code == "WORKFLOW_CYCLE" for issue in result.issues)


def test_validation_rejects_unknown_config():
    workflow = _workflow([
        WorkflowNode(id="keys", type=WorkflowNodeType.KEY_INDIVIDUALS, config={"not_allowed": True})
    ])
    result = InvestigationWorkflowEngine().execute(_graph(), workflow)
    assert result.status == "VALIDATION_FAILED"
    assert any(issue.code == "UNKNOWN_NODE_CONFIG" for issue in result.issues)


def test_multiple_incoming_edges_to_report_input_are_supported():
    nodes = [
        WorkflowNode(id="a", type=WorkflowNodeType.COMMUNITY_DETECTION),
        WorkflowNode(id="b", type=WorkflowNodeType.KEY_INDIVIDUALS),
        WorkflowNode(id="report", type=WorkflowNodeType.REPORT),
    ]
    edges = [
        WorkflowEdge(id="e1", source_node_id="a", target_node_id="report"),
        WorkflowEdge(id="e2", source_node_id="b", target_node_id="report"),
    ]
    result = InvestigationWorkflowEngine().execute(_graph(), _workflow(nodes, edges))
    assert result.status == "COMPLETED"
    assert set(result.final_output["sections"]) == {"a", "b"}


def test_failure_policy_continue_allows_independent_nodes_to_run():
    nodes = [
        WorkflowNode(id="bad", type=WorkflowNodeType.EXPAND_NETWORK, config={"depth": 1}),
        WorkflowNode(id="good", type=WorkflowNodeType.KEY_INDIVIDUALS),
    ]
    result = InvestigationWorkflowEngine().execute(_graph(), _workflow(nodes, policy=WorkflowFailurePolicy.CONTINUE))
    assert result.status == "FAILED"
    assert result.node_results[0].status == "FAILED"
    assert result.node_results[1].status == "COMPLETED"


def test_execution_id_is_stable_for_same_workflow_and_graph():
    workflow = _workflow([
        WorkflowNode(id="keys", type=WorkflowNodeType.KEY_INDIVIDUALS)
    ])
    engine = InvestigationWorkflowEngine()
    first = engine.execute(_graph(), workflow)
    second = engine.execute(_graph(), workflow)
    assert first.execution_id == second.execution_id
