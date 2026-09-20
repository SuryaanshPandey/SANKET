"""Deterministic final-acceptance harness for SANKET.

This script validates the post-extraction investigation layer without a live VLM,
network service, or external dataset. It is intentionally small enough to run on
the hackathon machine and produces a machine-readable JSON artifact.

Checks:
1. temporal scoping over an evidence graph;
2. key-individual and structural bridge analysis;
3. explainable temporal/interaction anomaly detection;
4. validated workflow composition + deterministic execution;
5. evidence review/report generation and provenance/contradiction counters;
6. stable execution IDs for reproducibility.

The benchmark scenario is synthetic and its metrics must not be presented as
real-world law-enforcement accuracy.
"""

from __future__ import annotations

import argparse
import sys
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from clarity.intelligence.anomaly_engine import AnomalyEngine
from clarity.intelligence.evidence_graph import EvidenceGraph, GraphEdge, GraphNode
from clarity.intelligence.graph_analytics import GraphAnalyticsEngine
from clarity.intelligence.reporting import build_investigation_report
from clarity.intelligence.temporal_engine import TemporalEngine, TimeWindow
from clarity.intelligence.models import InvestigationStatus, NodeKind
from clarity.intelligence.workflow_engine import (
    InvestigationWorkflow,
    InvestigationWorkflowEngine,
    WorkflowEdge,
    WorkflowNode,
    WorkflowNodeType,
)

UTC = timezone.utc


def person(node_id: str, label: str) -> GraphNode:
    return GraphNode(
        id=node_id,
        kind=NodeKind.ENTITY,
        type="PERSON",
        label=label,
        confidence=1.0,
        source_refs=[
            {
                "document_id": "DOC-SYN-01",
                "filename": "synthetic_investigation_bundle.json",
                "file_hash_sha256": "synthetic-not-a-real-document-hash",
                "page": 1,
                "text_span": label,
            }
        ],
    )


def relationship(edge_id: str, left: str, right: str) -> GraphEdge:
    return GraphEdge(
        id=edge_id,
        source_id=left,
        target_id=right,
        relationship_type="ASSOCIATED_WITH",
        confidence=1.0,
        status=InvestigationStatus.OBSERVED,
        source_refs=[
            {
                "document_id": "DOC-SYN-01",
                "filename": "synthetic_investigation_bundle.json",
                "file_hash_sha256": "synthetic-not-a-real-document-hash",
                "page": 1,
                "text_span": f"relationship {left} -> {right}",
            }
        ],
    )


def event(
    event_id: str,
    timestamp: datetime,
    source: str,
    target: str | None = None,
    event_type: str = "CALL",
) -> GraphNode:
    metadata: dict[str, Any] = {
        "timestamp": timestamp.isoformat(),
        "source_entity_id": source,
    }
    if target is not None:
        metadata["target_entity_id"] = target
    return GraphNode(
        id=event_id,
        kind=NodeKind.EVENT,
        type=event_type,
        label=event_type,
        confidence=1.0,
        metadata=metadata,
        source_refs=[
            {
                "document_id": "DOC-SYN-01",
                "filename": "synthetic_investigation_bundle.json",
                "file_hash_sha256": "synthetic-not-a-real-document-hash",
                "page": 1,
                "text_span": event_id,
            }
        ],
    )


def build_synthetic_graph() -> EvidenceGraph:
    # Two dense-ish communities connected through X. A2/B1 are local
    # articulation-style candidates, while X is the intended primary bridge.
    nodes = [
        person("A1", "Arun"),
        person("A2", "Asha"),
        person("A3", "Amit"),
        person("X", "Xavier"),
        person("B1", "Bina"),
        person("B2", "Bhavesh"),
        person("C1", "Chetan"),
        person("C2", "Chitra"),
    ]
    edges = [
        relationship("R1", "A1", "A2"),
        relationship("R2", "A2", "A3"),
        relationship("R3", "A2", "X"),
        relationship("R4", "X", "B1"),
        relationship("R5", "B1", "B2"),
        relationship("R6", "C1", "C2"),
    ]

    baseline = datetime(2026, 8, 1, tzinfo=UTC)
    target = datetime(2026, 8, 8, tzinfo=UTC)
    event_nodes: list[GraphNode] = []

    # Baseline activity for X: one event per day.
    for index in range(6):
        event_nodes.append(
            event(
                f"BX{index + 1}",
                baseline + timedelta(days=index, hours=10),
                "X",
                "A2",
            )
        )

    # Target activity spike for X: five events in the same 30-minute bucket.
    for index in range(5):
        event_nodes.append(
            event(
                f"TX{index + 1}",
                target + timedelta(hours=10, minutes=index),
                "X",
                "A2",
            )
        )

    # A novel cross-cluster pair and a target interaction burst.
    event_nodes.append(event("NX1", target + timedelta(hours=13), "X", "C1"))
    for index in range(4):
        event_nodes.append(
            event(
                f"TB{index + 1}",
                target + timedelta(hours=14, minutes=index),
                "A1",
                "B2",
            )
        )

    all_nodes = nodes + event_nodes
    adjacency: dict[str, set[str]] = {item.id: set() for item in all_nodes}
    reverse: dict[str, set[str]] = {item.id: set() for item in all_nodes}
    for item in edges:
        adjacency[item.source_id].add(item.target_id)
        reverse[item.target_id].add(item.source_id)

    return EvidenceGraph(
        contract_version="1.0.0",
        case_id="CASE-SYNTHETIC-FINAL",
        total_documents=1,
        nodes={item.id: item for item in all_nodes},
        edges={item.id: item for item in edges},
        adjacency={key: sorted(value) for key, value in sorted(adjacency.items())},
        reverse_adjacency={key: sorted(value) for key, value in sorted(reverse.items())},
    )


def build_workflow() -> InvestigationWorkflow:
    nodes = [
        WorkflowNode(
            id="time",
            type=WorkflowNodeType.TIME_FILTER,
            label="Scope target window",
            config={"start": "2026-08-08T00:00:00+00:00", "end": "2026-08-08T23:59:59+00:00"},
            position={"x": 0, "y": 0},
        ),
        WorkflowNode(
            id="expand",
            type=WorkflowNodeType.EXPAND_NETWORK,
            label="Expand network",
            config={"depth": 2},
            position={"x": 260, "y": 0},
        ),
        WorkflowNode(
            id="analytics",
            type=WorkflowNodeType.GRAPH_ANALYTICS,
            label="Analyze network",
            config={"target_entity_types": ["PERSON"]},
            position={"x": 520, "y": 0},
        ),
        WorkflowNode(
            id="bridge",
            type=WorkflowNodeType.BRIDGE_ANALYSIS,
            label="Find bridge leads",
            config={"minimum_cross_community_ratio": 0.5},
            position={"x": 780, "y": 0},
        ),
        WorkflowNode(
            id="anomaly",
            type=WorkflowNodeType.ANOMALY_DETECTION,
            label="Detect unusual activity",
            config={
                "target_start": "2026-08-08T00:00:00+00:00",
                "target_end": "2026-08-08T23:59:59+00:00",
                "baseline_start": "2026-08-01T00:00:00+00:00",
                "baseline_end": "2026-08-07T23:59:59+00:00",
                "max_findings": 20,
            },
            position={"x": 1040, "y": 0},
        ),
        WorkflowNode(
            id="review",
            type=WorkflowNodeType.EVIDENCE_REVIEW,
            label="Review evidence",
            config={},
            position={"x": 1300, "y": 0},
        ),
        WorkflowNode(
            id="report",
            type=WorkflowNodeType.REPORT,
            label="Investigation report",
            config={"include_node_outputs": True},
            position={"x": 1560, "y": 0},
        ),
    ]
    edges = [
        WorkflowEdge(id="E1", source_node_id="time", target_node_id="expand"),
        WorkflowEdge(id="E2", source_node_id="expand", target_node_id="analytics"),
        WorkflowEdge(id="E3", source_node_id="analytics", target_node_id="bridge"),
        WorkflowEdge(id="E4", source_node_id="bridge", target_node_id="review"),
        WorkflowEdge(id="E5", source_node_id="anomaly", target_node_id="review"),
        WorkflowEdge(id="E6", source_node_id="review", target_node_id="report"),
        WorkflowEdge(id="E7", source_node_id="expand", target_node_id="anomaly"),
    ]
    return InvestigationWorkflow(
        workflow_id="wf-final-acceptance",
        version="1.0.0",
        name="Final acceptance investigation",
        description="Deterministic end-to-end validation workflow.",
        nodes=nodes,
        edges=edges,
        metadata={"investigation_question": "Find bridge leads and unusual activity in the target window."},
    )


def run_acceptance() -> dict[str, Any]:
    started = perf_counter()
    graph = build_synthetic_graph()
    temporal = TemporalEngine()
    analytics = GraphAnalyticsEngine()
    anomalies = AnomalyEngine(temporal_engine=temporal, graph_analytics_engine=analytics)

    target_window = TimeWindow(
        start=datetime(2026, 8, 8, tzinfo=UTC),
        end=datetime(2026, 8, 8, 23, 59, 59, tzinfo=UTC),
    )
    baseline_window = TimeWindow(
        start=datetime(2026, 8, 1, tzinfo=UTC),
        end=datetime(2026, 8, 7, 23, 59, 59, tzinfo=UTC),
    )

    snapshot, snapshot_issues = temporal.snapshot(graph, target_window)
    analytics_report = analytics.analyze(graph)
    anomaly_report = anomalies.analyze(graph, target_window, baseline_window=baseline_window)

    primary_bridge = analytics_report.bridge_candidates[0] if analytics_report.bridge_candidates else None
    anomaly_types = sorted({finding.anomaly_type for finding in anomaly_report.findings})

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check(
        "temporal_scope",
        bool(snapshot.event_ids) and not any(issue.severity == "error" for issue in snapshot_issues),
        f"target_events={len(snapshot.event_ids)}, temporal_issues={len(snapshot_issues)}",
    )
    check(
        "key_individual_analysis",
        bool(analytics_report.key_individuals),
        f"ranked_entities={len(analytics_report.key_individuals)}",
    )
    check(
        "primary_bridge_lead",
        primary_bridge is not None and primary_bridge.node_id == "X",
        f"top_bridge={primary_bridge.node_id if primary_bridge else None}",
    )
    expected_anomalies = {"ACTIVITY_SPIKE", "NOVEL_RELATIONSHIP", "INTERACTION_BURST"}
    check(
        "anomaly_coverage",
        expected_anomalies.issubset(set(anomaly_types)),
        f"expected={sorted(expected_anomalies)}, observed={anomaly_types}",
    )

    workflow = build_workflow()
    workflow_engine = InvestigationWorkflowEngine(
        temporal_engine=temporal,
        graph_analytics_engine=analytics,
        anomaly_engine=anomalies,
    )
    validation_issues = workflow_engine.validate(workflow)
    validation_errors = [item for item in validation_issues if item.severity == "error"]
    check(
        "workflow_validation",
        not validation_errors,
        f"errors={len(validation_errors)}, warnings={len(validation_issues) - len(validation_errors)}",
    )

    execution = workflow_engine.execute(graph, workflow)
    check(
        "workflow_execution",
        execution.status == "COMPLETED",
        f"status={execution.status}, nodes={len(execution.node_results)}, execution_id={execution.execution_id}",
    )

    review_payload = {
        "contradictions": {"contradiction_count": 0, "items": []},
        "provenance": {"summary": {"total_items": sum(len(node.source_refs) for node in graph.nodes.values()) + sum(len(edge.source_refs) for edge in graph.edges.values())}},
    }
    report = build_investigation_report(
        case_id=graph.case_id or "CASE-SYNTHETIC-FINAL",
        workflow=workflow,
        execution=execution,
        graph_summary={
            "total_documents": graph.total_documents,
            "entity_count": graph.entity_count,
            "event_count": graph.event_count,
            "edge_count": graph.edge_count,
        },
        evidence_review=review_payload,
        question=workflow.metadata.get("investigation_question"),
    )
    markdown = report.to_markdown()
    check(
        "evidence_backed_report",
        report.execution_id == execution.execution_id and "Analytical results are investigative leads" in markdown,
        f"findings={report.summary.get('finding_count', 0)}, provenance={report.provenance_count}",
    )

    # Reproducibility check: same workflow + same graph => same execution ID.
    execution_repeat = workflow_engine.execute(graph, workflow)
    check(
        "reproducible_execution_id",
        execution_repeat.execution_id == execution.execution_id,
        f"first={execution.execution_id}, repeat={execution_repeat.execution_id}",
    )

    passed = all(item["passed"] for item in checks)
    elapsed = perf_counter() - started

    return {
        "suite": "SANKET final acceptance",
        "version": "V1.10.6 + C4",
        "generated_at": datetime.now(UTC).isoformat(),
        "scenario": {
            "name": "synthetic_bridge_and_temporal_anomaly",
            "case_id": graph.case_id,
            "documents": graph.total_documents,
            "entities": graph.entity_count,
            "events": graph.event_count,
            "relationships": graph.edge_count,
            "ground_truth_primary_bridge": "X",
        },
        "results": {
            "passed": passed,
            "checks_passed": sum(item["passed"] for item in checks),
            "checks_total": len(checks),
            "duration_seconds": round(elapsed, 4),
            "primary_bridge": primary_bridge.model_dump(mode="json") if primary_bridge else None,
            "anomaly_types": anomaly_types,
            "workflow_status": execution.status,
            "workflow_execution_id": execution.execution_id,
            "provenance_count": report.provenance_count,
            "contradiction_count": report.contradiction_count,
        },
        "checks": checks,
        "limitations": [
            "Synthetic benchmark only; not a law-enforcement accuracy estimate.",
            "VLM extraction quality is outside this deterministic acceptance harness.",
            "Legal/document quality rules are rule checks and not blanket legal certification.",
            "The benchmark validates expected behaviour on a controlled scenario, not population-level recall or precision.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=Path("artifacts/final_acceptance.json"))
    args = parser.parse_args()

    result = run_acceptance()
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 78)
    print("SANKET FINAL ACCEPTANCE")
    print("=" * 78)
    print(f"Version : {result['version']}")
    print(f"Scenario: {result['scenario']['name']}")
    print(f"Checks  : {result['results']['checks_passed']}/{result['results']['checks_total']} passed")
    print(f"Status  : {'PASS' if result['results']['passed'] else 'FAIL'}")
    print(f"Output  : {args.json_out}")
    print("\nCheck details:")
    for item in result["checks"]:
        marker = "PASS" if item["passed"] else "FAIL"
        print(f"  [{marker}] {item['name']}: {item['detail']}")
    return 0 if result["results"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
