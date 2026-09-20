"""Deterministic investigation reporting from validated workflow executions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from clarity.intelligence.workflow_engine import InvestigationWorkflow, WorkflowExecutionResult


class InvestigationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    case_id: str
    generated_at: str
    title: str
    question: str | None = None
    workflow_id: str
    workflow_version: str
    execution_id: str
    status: str
    summary: dict[str, Any] = Field(default_factory=dict)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    evidence_review: dict[str, Any] = Field(default_factory=dict)
    uncertainty: list[str] = Field(default_factory=list)
    provenance_count: int = 0
    contradiction_count: int = 0
    notes: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"**Case:** {self.case_id}",
            f"**Execution:** {self.execution_id}",
            f"**Workflow:** {self.workflow_id} v{self.workflow_version}",
            f"**Status:** {self.status}",
            f"**Generated:** {self.generated_at}",
            "",
        ]
        if self.question:
            lines.extend(["## Investigation question", self.question, ""])
        lines.extend(["## Run summary", ""])
        for key, value in self.summary.items():
            lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        lines.append("")
        lines.append("## Findings")
        if not self.findings:
            lines.append("No analytical findings were produced by the selected workflow.")
        else:
            for index, finding in enumerate(self.findings, start=1):
                label = finding.get("label") or finding.get("candidate") or finding.get("finding_id") or f"Finding {index}"
                lines.append(f"### {index}. {label}")
                for key in ("status", "score", "bridge_score", "confidence", "reason", "explanation"):
                    if key in finding and finding[key] not in (None, ""):
                        lines.append(f"- **{key.replace('_', ' ').title()}:** {finding[key]}")
                refs = finding.get("supporting_relationship_ids") or finding.get("supporting_event_ids") or []
                if refs:
                    lines.append(f"- **Supporting object IDs:** {', '.join(map(str, refs))}")
                lines.append("")
        lines.append("## Uncertainty and review")
        if not self.uncertainty:
            lines.append("No additional workflow-level uncertainty notes were generated.")
        else:
            lines.extend(f"- {item}" for item in self.uncertainty)
        lines.append("")
        lines.append("## Evidence review")
        lines.append(f"- Provenance items: {self.provenance_count}")
        lines.append(f"- Contradictions: {self.contradiction_count}")
        lines.append("")
        lines.append("> Analytical results are investigative leads derived from the selected evidence graph and workflow. They are not legal guilt determinations.")
        if self.notes:
            lines.extend(["", "## Notes", *[f"- {item}" for item in self.notes]])
        return "\n".join(lines)


def build_investigation_report(
    *,
    case_id: str,
    workflow: InvestigationWorkflow,
    execution: WorkflowExecutionResult,
    graph_summary: Mapping[str, Any],
    evidence_review: Mapping[str, Any],
    question: str | None = None,
) -> InvestigationReport:
    findings: list[dict[str, Any]] = []
    uncertainty: list[str] = []
    for result in execution.node_results:
        output = result.output or {}
        for key in ("findings", "bridge_candidates", "key_individuals"):
            values = output.get(key, [])
            if isinstance(values, list):
                findings.extend(item for item in values if isinstance(item, dict))
        for issue in result.issues:
            uncertainty.append(f"{result.node_id}: {issue.message}")

    contradictions = evidence_review.get("contradictions") or {}
    provenance = evidence_review.get("provenance") or {}
    contradiction_count = int(contradictions.get("contradiction_count", len(contradictions.get("items", []))))
    provenance_count = int((provenance.get("summary") or {}).get("total_items", len(provenance.get("items", []))))

    report_id = f"RPT-{execution.execution_id.replace('EXEC-', '', 1)}"
    return InvestigationReport(
        report_id=report_id,
        case_id=case_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        title=workflow.name or "Investigation Report",
        question=question,
        workflow_id=workflow.workflow_id,
        workflow_version=workflow.version,
        execution_id=execution.execution_id,
        status=execution.status,
        summary={
            "documents": graph_summary.get("total_documents", 0),
            "entities": graph_summary.get("entity_count", 0),
            "events": graph_summary.get("event_count", 0),
            "relationships": graph_summary.get("edge_count", 0),
            "workflow_nodes": len(workflow.nodes),
            "workflow_results": len(execution.node_results),
            "finding_count": len(findings),
        },
        findings=findings,
        evidence_review=dict(evidence_review),
        uncertainty=sorted(set(uncertainty)),
        provenance_count=provenance_count,
        contradiction_count=contradiction_count,
        notes=[
            "This report is generated from a validated deterministic workflow.",
            "Evidence conflicts remain visible and are not silently reconciled.",
        ],
    )
