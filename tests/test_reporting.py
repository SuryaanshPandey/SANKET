from clarity.intelligence.reporting import build_investigation_report
from clarity.intelligence.workflow_engine import InvestigationWorkflowEngine, InvestigationWorkflow
from clarity.intelligence.evidence_graph import EvidenceGraph


def test_investigation_report_is_deterministic_in_structure():
    workflow = InvestigationWorkflow.model_validate({
        "workflow_id": "wf-report",
        "name": "Lead review",
        "description": "Report test",
        "nodes": [{"id": "report", "type": "REPORT", "config": {}}],
        "edges": [],
    })
    graph = EvidenceGraph(
        contract_version="1.0.0",
        case_id="CASE-REPORT",
        total_documents=2,
        nodes={},
        edges={},
        adjacency={},
        reverse_adjacency={},
    )
    execution = InvestigationWorkflowEngine().execute(graph, workflow)
    report = build_investigation_report(
        case_id="CASE-REPORT",
        workflow=workflow,
        execution=execution,
        graph_summary={"total_documents": 2, "entity_count": 0, "event_count": 0, "edge_count": 0},
        evidence_review={"contradictions": {"contradiction_count": 1}, "provenance": {"summary": {"total_items": 3}}},
        question="Produce a review report",
    )
    assert report.case_id == "CASE-REPORT"
    assert report.contradiction_count == 1
    assert report.provenance_count == 3
    assert "Analytical results are investigative leads" in report.to_markdown()
