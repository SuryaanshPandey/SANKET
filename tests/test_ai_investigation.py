from __future__ import annotations

import json

from clarity.intelligence.ai_investigation import (
    InvestigationPlanRequest,
    InvestigationPlanner,
    InvestigationPlannerError,
)
from clarity.intelligence.workflow_engine import InvestigationWorkflowEngine
from clarity.intelligence import ai_investigation as ai_module


def _planner_payload() -> dict:
    return {
        "workflow": {
            "workflow_id": "ai-plan",
            "version": "1.0.0",
            "name": "Bridge lead review",
            "description": "Find bridge candidates and inspect their evidence.",
            "failure_policy": "STOP",
            "nodes": [
                {"id": "communities", "type": "COMMUNITY_DETECTION", "label": "FIND COMMUNITIES", "config": {}, "enabled": True, "position": {"x": 0, "y": 0}},
                {"id": "bridges", "type": "BRIDGE_ANALYSIS", "label": "FIND BRIDGE LEADS", "config": {"minimum_cross_community_ratio": 0.2}, "enabled": True, "position": {"x": 300, "y": 0}},
                {"id": "evidence", "type": "EVIDENCE_REVIEW", "label": "REVIEW EVIDENCE", "config": {}, "enabled": True, "position": {"x": 600, "y": 0}},
                {"id": "report", "type": "REPORT", "label": "REPORT", "config": {"include_node_outputs": True}, "enabled": True, "position": {"x": 900, "y": 0}},
            ],
            "edges": [
                {"id": "e1", "source_node_id": "communities", "target_node_id": "bridges", "source_port": "output", "target_port": "input", "enabled": True},
                {"id": "e2", "source_node_id": "bridges", "target_node_id": "evidence", "source_port": "output", "target_port": "input", "enabled": True},
                {"id": "e3", "source_node_id": "evidence", "target_node_id": "report", "source_port": "output", "target_port": "input", "enabled": True},
            ],
            "metadata": {"purpose": "bridge-analysis"},
        },
        "explanation": "A transparent community → bridge → evidence → report workflow.",
        "warnings": [],
    }


def test_ai_planner_validates_llm_workflow(monkeypatch):
    payload = _planner_payload()

    monkeypatch.setattr(
        ai_module,
        "_chat_local_ollama",
        lambda **_: (json.dumps(payload), "ollama-native:test-model"),
    )

    planner = InvestigationPlanner(model="test-model", timeout=2)
    result = planner.plan(
        InvestigationPlanRequest(question="Find possible intermediaries between network communities."),
        case_context={"graph_summary": {"entities": 4, "relationships": 5}},
        graph_node_ids={"P1", "P2", "P3"},
    )

    assert result.workflow.name == "Bridge lead review"
    assert len(result.workflow.nodes) == 4
    assert result.planner_transport == "ollama-native:test-model"
    assert not InvestigationWorkflowEngine().validate(result.workflow)


def test_ai_planner_rejects_unknown_entity_reference(monkeypatch):
    payload = _planner_payload()
    payload["workflow"]["nodes"][0]["type"] = "EXPAND_NETWORK"
    payload["workflow"]["nodes"][0]["config"] = {"seed_entity_ids": ["P999"], "depth": 2}

    monkeypatch.setattr(ai_module, "_chat_local_ollama", lambda **_: (json.dumps(payload), "ollama-native:test-model"))

    planner = InvestigationPlanner(model="test-model", timeout=2)
    try:
        planner.plan(
            InvestigationPlanRequest(question="Expand around the selected person."),
            case_context={"graph_summary": {}},
            allowed_entity_ids=set(),
            graph_node_ids={"P1", "P2"},
        )
    except InvestigationPlannerError as exc:
        assert "not explicitly selected" in str(exc)
    else:
        raise AssertionError("Expected the planner to reject an unselected entity reference")


def test_ai_planner_repairs_ordinal_node_edge_aliases(monkeypatch):
    payload = _planner_payload()
    payload["workflow"]["edges"][0]["source_node_id"] = "node-1"
    payload["workflow"]["edges"][0]["target_node_id"] = "node-2"
    payload["workflow"]["edges"][1]["source_node_id"] = "step-2"
    payload["workflow"]["edges"][1]["target_node_id"] = "step-3"

    monkeypatch.setattr(
        ai_module,
        "_chat_local_ollama",
        lambda **_: (json.dumps(payload), "ollama-native:test-model"),
    )

    planner = InvestigationPlanner(model="test-model", timeout=2)
    result = planner.plan(
        InvestigationPlanRequest(question="Find bridge leads and review their evidence."),
        case_context={"graph_summary": {"entities": 4, "relationships": 5}},
        graph_node_ids={"P1", "P2", "P3"},
    )

    assert [(edge.source_node_id, edge.target_node_id) for edge in result.workflow.edges[:2]] == [
        ("communities", "bridges"),
        ("bridges", "evidence"),
    ]
    assert any("Repaired AI edge" in warning for warning in result.warnings)
    assert not InvestigationWorkflowEngine().validate(result.workflow)
