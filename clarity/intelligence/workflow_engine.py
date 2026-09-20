"""Deterministic investigation workflow engine.

The workflow engine is the orchestration layer between the analytical services
and the future investigation-canvas UI. It deliberately executes only an
allow-listed set of deterministic investigation operations; it never executes
arbitrary Python, SQL, shell commands, or LLM-generated code.

Design goals:
- model an n8n-style node-and-edge investigation workflow;
- validate IDs, ports, duplicate nodes, duplicate edges, and cycles before run;
- execute nodes deterministically in stable topological order;
- pass prior node outputs explicitly through workflow connections;
- keep analytical findings evidence-aware and separate observed evidence from
  inference/lead semantics;
- make workflow definitions JSON-serializable and reproducible;
- provide a clean boundary for a later AI layer to generate validated
  StructuredWorkflow objects rather than directly executing database/system
  commands.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from clarity.intelligence.anomaly_engine import AnomalyEngine
from clarity.intelligence.evidence_graph import EvidenceGraph
from clarity.intelligence.graph_analytics import GraphAnalyticsEngine
from clarity.intelligence.temporal_engine import TemporalEngine, TimeWindow


class WorkflowEngineError(ValueError):
    """Raised when a workflow cannot be validated or executed safely."""


class WorkflowFailurePolicy(str, Enum):
    STOP = "STOP"
    CONTINUE = "CONTINUE"


class WorkflowNodeType(str, Enum):
    """Allow-listed analytical nodes supported by V1.7."""

    TIME_FILTER = "TIME_FILTER"
    EXPAND_NETWORK = "EXPAND_NETWORK"
    GRAPH_ANALYTICS = "GRAPH_ANALYTICS"
    KEY_INDIVIDUALS = "KEY_INDIVIDUALS"
    COMMUNITY_DETECTION = "COMMUNITY_DETECTION"
    BRIDGE_ANALYSIS = "BRIDGE_ANALYSIS"
    ANOMALY_DETECTION = "ANOMALY_DETECTION"
    SHORTEST_PATH = "SHORTEST_PATH"
    EVIDENCE_REVIEW = "EVIDENCE_REVIEW"
    REPORT = "REPORT"


class WorkflowPort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    required: bool = False


class WorkflowNode(BaseModel):
    """UI + execution definition of one investigation node."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    type: WorkflowNodeType
    label: str = Field(default="", max_length=256)
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    input_ports: list[WorkflowPort] = Field(default_factory=list)
    output_ports: list[WorkflowPort] = Field(default_factory=list)


class WorkflowEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    source_node_id: str = Field(min_length=1, max_length=128)
    target_node_id: str = Field(min_length=1, max_length=128)
    source_port: str = "output"
    target_port: str = "input"
    enabled: bool = True


class InvestigationWorkflow(BaseModel):
    """Versioned, serializable workflow definition."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(min_length=1, max_length=128)
    version: str = Field(default="1.0.0", min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=256)
    description: str = Field(default="", max_length=2000)
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    failure_policy: WorkflowFailurePolicy = WorkflowFailurePolicy.STOP

    @model_validator(mode="after")
    def _validate_nonempty(self) -> "InvestigationWorkflow":
        if not self.nodes:
            raise ValueError("workflow must contain at least one node")
        return self


class WorkflowIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str
    code: str
    message: str
    node_id: str | None = None
    edge_id: str | None = None


class NodeExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    node_type: WorkflowNodeType
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    input_node_ids: list[str] = Field(default_factory=list)
    issues: list[WorkflowIssue] = Field(default_factory=list)


class WorkflowExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_id: str
    workflow_id: str
    workflow_version: str
    status: str
    ordered_node_ids: list[str] = Field(default_factory=list)
    node_results: list[NodeExecutionResult] = Field(default_factory=list)
    final_output: dict[str, Any] = Field(default_factory=dict)
    issues: list[WorkflowIssue] = Field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


_ALLOWED_CONFIG_KEYS: dict[WorkflowNodeType, set[str]] = {
    WorkflowNodeType.TIME_FILTER: {"start", "end"},
    WorkflowNodeType.EXPAND_NETWORK: {"seed_entity_ids", "depth"},
    WorkflowNodeType.GRAPH_ANALYTICS: {"target_entity_types", "include_event_interactions"},
    WorkflowNodeType.KEY_INDIVIDUALS: {"top_k", "target_entity_types", "include_event_interactions"},
    WorkflowNodeType.COMMUNITY_DETECTION: {"target_entity_types", "include_event_interactions"},
    WorkflowNodeType.BRIDGE_ANALYSIS: {"minimum_cross_community_ratio", "target_entity_types", "include_event_interactions"},
    WorkflowNodeType.ANOMALY_DETECTION: {
        "target_start", "target_end", "baseline_start", "baseline_end", "target_entity_types", "max_findings"
    },
    WorkflowNodeType.SHORTEST_PATH: {"source_id", "target_id"},
    WorkflowNodeType.EVIDENCE_REVIEW: {"entity_ids", "event_ids", "relationship_ids", "finding_ids"},
    WorkflowNodeType.REPORT: {"title", "include_node_outputs", "notes"},
}


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _execution_id(workflow: InvestigationWorkflow, graph: EvidenceGraph) -> str:
    payload = {
        "workflow": workflow.model_dump(mode="json"),
        "graph": {
            "case_id": graph.case_id,
            "contract_version": graph.contract_version,
            "node_ids": sorted(graph.nodes),
            "edge_ids": sorted(graph.edges),
        },
    }
    digest = hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()[:16]
    return f"EXEC-{digest}"


def _iso_window(config: Mapping[str, Any], prefix: str = "") -> TimeWindow:
    start_key = f"{prefix}start" if prefix else "start"
    end_key = f"{prefix}end" if prefix else "end"
    if start_key not in config or end_key not in config:
        raise WorkflowEngineError(
            f"TIME_FILTER/ANOMALY_DETECTION requires '{start_key}' and '{end_key}'."
        )
    return TimeWindow(start=config[start_key], end=config[end_key])


class InvestigationWorkflowEngine:
    """Validate and execute allow-listed investigation workflows."""

    def __init__(
        self,
        *,
        temporal_engine: TemporalEngine | None = None,
        graph_analytics_engine: GraphAnalyticsEngine | None = None,
        anomaly_engine: AnomalyEngine | None = None,
    ) -> None:
        self.temporal_engine = temporal_engine or TemporalEngine()
        self.graph_analytics_engine = graph_analytics_engine or GraphAnalyticsEngine()
        self.anomaly_engine = anomaly_engine or AnomalyEngine(
            temporal_engine=self.temporal_engine,
            graph_analytics_engine=self.graph_analytics_engine,
        )

    def validate(self, workflow: InvestigationWorkflow) -> list[WorkflowIssue]:
        issues: list[WorkflowIssue] = []
        node_map: dict[str, WorkflowNode] = {}
        for node in workflow.nodes:
            if node.id in node_map:
                issues.append(
                    WorkflowIssue(severity="error", code="DUPLICATE_NODE_ID", message=f"Duplicate node id '{node.id}'.", node_id=node.id)
                )
            else:
                node_map[node.id] = node
            allowed = _ALLOWED_CONFIG_KEYS[node.type]
            unknown = sorted(set(node.config) - allowed)
            if unknown:
                issues.append(
                    WorkflowIssue(
                        severity="error",
                        code="UNKNOWN_NODE_CONFIG",
                        message=f"Node '{node.id}' has unsupported config keys: {unknown}.",
                        node_id=node.id,
                    )
                )
            config_issues = self._validate_node_config(node)
            issues.extend(config_issues)

        edge_ids: set[str] = set()
        incoming_ports: set[tuple[str, str]] = set()
        adjacency: dict[str, list[str]] = defaultdict(list)
        indegree: dict[str, int] = {node.id: 0 for node in workflow.nodes}
        for edge in workflow.edges:
            if edge.id in edge_ids:
                issues.append(
                    WorkflowIssue(severity="error", code="DUPLICATE_EDGE_ID", message=f"Duplicate edge id '{edge.id}'.", edge_id=edge.id)
                )
            edge_ids.add(edge.id)
            if edge.source_node_id not in node_map:
                issues.append(
                    WorkflowIssue(severity="error", code="MISSING_SOURCE_NODE", message=f"Edge '{edge.id}' references missing source node '{edge.source_node_id}'.", edge_id=edge.id)
                )
                continue
            if edge.target_node_id not in node_map:
                issues.append(
                    WorkflowIssue(severity="error", code="MISSING_TARGET_NODE", message=f"Edge '{edge.id}' references missing target node '{edge.target_node_id}'.", edge_id=edge.id)
                )
                continue
            if edge.source_node_id == edge.target_node_id:
                issues.append(
                    WorkflowIssue(severity="error", code="SELF_LOOP", message=f"Edge '{edge.id}' connects node '{edge.source_node_id}' to itself.", edge_id=edge.id)
                )
            incoming_ports.add((edge.target_node_id, edge.target_port))
            if edge.enabled:
                adjacency[edge.source_node_id].append(edge.target_node_id)
                indegree[edge.target_node_id] += 1

        # Validate declared ports when present.
        for node in workflow.nodes:
            declared_inputs = {port.name for port in node.input_ports}
            declared_outputs = {port.name for port in node.output_ports}
            for edge in workflow.edges:
                if not edge.enabled:
                    continue
                if edge.target_node_id == node.id and declared_inputs and edge.target_port not in declared_inputs:
                    issues.append(
                        WorkflowIssue(severity="error", code="UNKNOWN_TARGET_PORT", message=f"Node '{node.id}' has no input port '{edge.target_port}'.", node_id=node.id)
                    )
                if edge.source_node_id == node.id and declared_outputs and edge.source_port not in declared_outputs:
                    issues.append(
                        WorkflowIssue(severity="error", code="UNKNOWN_SOURCE_PORT", message=f"Node '{node.id}' has no output port '{edge.source_port}'.", node_id=node.id)
                    )

        # Cycle detection.
        q = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
        visited = 0
        working_indegree = dict(indegree)
        while q:
            current = q.popleft()
            visited += 1
            for neighbor in sorted(adjacency.get(current, [])):
                working_indegree[neighbor] -= 1
                if working_indegree[neighbor] == 0:
                    q.append(neighbor)
        if visited != len(node_map):
            issues.append(
                WorkflowIssue(severity="error", code="WORKFLOW_CYCLE", message="Workflow contains a cycle; DAG execution is required.")
            )

        return issues

    def _validate_node_config(self, node: WorkflowNode) -> list[WorkflowIssue]:
        c = node.config
        issues: list[WorkflowIssue] = []
        required: dict[WorkflowNodeType, tuple[str, ...]] = {
            WorkflowNodeType.TIME_FILTER: ("start", "end"),
            WorkflowNodeType.EXPAND_NETWORK: ("depth",),
            WorkflowNodeType.SHORTEST_PATH: ("source_id", "target_id"),
            WorkflowNodeType.ANOMALY_DETECTION: ("target_start", "target_end"),
        }
        for key in required.get(node.type, ()):
            if key not in c:
                issues.append(
                    WorkflowIssue(severity="error", code="MISSING_NODE_CONFIG", message=f"Node '{node.id}' requires config field '{key}'.", node_id=node.id)
                )
        if "depth" in c:
            if not isinstance(c["depth"], int) or not 1 <= c["depth"] <= 10:
                issues.append(WorkflowIssue(severity="error", code="INVALID_DEPTH", message=f"Node '{node.id}' depth must be an integer from 1 to 10.", node_id=node.id))
        if "top_k" in c:
            if not isinstance(c["top_k"], int) or c["top_k"] < 1:
                issues.append(WorkflowIssue(severity="error", code="INVALID_TOP_K", message=f"Node '{node.id}' top_k must be >= 1.", node_id=node.id))
        if "maximum_findings" in c:
            issues.append(WorkflowIssue(severity="error", code="UNKNOWN_NODE_CONFIG", message=f"Node '{node.id}' must use 'max_findings'.", node_id=node.id))
        if node.type == WorkflowNodeType.ANOMALY_DETECTION:
            if any(k in c for k in ("baseline_start", "baseline_end")) and not all(k in c for k in ("baseline_start", "baseline_end")):
                issues.append(WorkflowIssue(severity="error", code="PARTIAL_BASELINE_WINDOW", message=f"Node '{node.id}' must provide both baseline_start and baseline_end.", node_id=node.id))
        try:
            if node.type == WorkflowNodeType.TIME_FILTER and "start" in c and "end" in c:
                _iso_window(c)
            if node.type == WorkflowNodeType.ANOMALY_DETECTION and "target_start" in c and "target_end" in c:
                _iso_window(c, "target_")
            if node.type == WorkflowNodeType.ANOMALY_DETECTION and all(k in c for k in ("baseline_start", "baseline_end")):
                _iso_window(c, "baseline_")
        except Exception as exc:
            issues.append(WorkflowIssue(severity="error", code="INVALID_TIME_WINDOW", message=f"Node '{node.id}' has invalid temporal configuration: {exc}", node_id=node.id))
        return issues

    def _topological_order(self, workflow: InvestigationWorkflow) -> list[str]:
        node_ids = {node.id for node in workflow.nodes}
        adjacency: dict[str, list[str]] = defaultdict(list)
        indegree: dict[str, int] = {node_id: 0 for node_id in node_ids}
        for edge in workflow.edges:
            if not edge.enabled:
                continue
            if edge.source_node_id in node_ids and edge.target_node_id in node_ids:
                adjacency[edge.source_node_id].append(edge.target_node_id)
                indegree[edge.target_node_id] += 1
        q = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
        order: list[str] = []
        while q:
            current = q.popleft()
            order.append(current)
            for neighbor in sorted(adjacency.get(current, [])):
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    q.append(neighbor)
        if len(order) != len(node_ids):
            raise WorkflowEngineError("Workflow contains a cycle or unresolved dependency.")
        return order

    @staticmethod
    def _inputs_for_node(
        node_id: str,
        workflow: InvestigationWorkflow,
        results: Mapping[str, NodeExecutionResult],
    ) -> dict[str, list[NodeExecutionResult]]:
        """Return all upstream results grouped by target input port."""
        inputs: dict[str, list[NodeExecutionResult]] = defaultdict(list)
        for edge in workflow.edges:
            if not edge.enabled or edge.target_node_id != node_id:
                continue
            if edge.source_node_id in results:
                inputs[edge.target_port].append(results[edge.source_node_id])
        for port in inputs:
            inputs[port] = sorted(inputs[port], key=lambda result: result.node_id)
        return dict(inputs)

    @staticmethod
    def _flatten_inputs(inputs: Mapping[str, list[NodeExecutionResult]]) -> list[NodeExecutionResult]:
        values: dict[str, NodeExecutionResult] = {}
        for results in inputs.values():
            for result in results:
                values[result.node_id] = result
        return [values[key] for key in sorted(values)]

    @staticmethod
    def _collect_ids_from_inputs(inputs: Mapping[str, list[NodeExecutionResult]], keys: Iterable[str]) -> list[str]:
        collected: set[str] = set()
        wanted = set(keys)
        for result in InvestigationWorkflowEngine._flatten_inputs(inputs):
            for key in wanted:
                values = result.output.get(key)
                if isinstance(values, list):
                    collected.update(str(value) for value in values)
                elif isinstance(values, str):
                    collected.add(values)
        return sorted(collected)

    @staticmethod
    def _scoped_graph_from_inputs(
        graph: EvidenceGraph,
        inputs: Mapping[str, NodeExecutionResult],
    ) -> EvidenceGraph:
        """Resolve the most recent explicit workflow scope from upstream nodes."""
        scoped_nodes: set[str] | None = None
        scoped_edges: set[str] | None = None
        for result in InvestigationWorkflowEngine._flatten_inputs(inputs):
            output = result.output
            candidate_nodes: set[str] | None = None
            candidate_edges: set[str] | None = None
            snapshot = output.get("snapshot")
            if isinstance(snapshot, dict):
                raw_nodes = snapshot.get("node_ids")
                raw_edges = snapshot.get("edge_ids")
                if isinstance(raw_nodes, list):
                    candidate_nodes = {str(value) for value in raw_nodes}
                if isinstance(raw_edges, list):
                    candidate_edges = {str(value) for value in raw_edges}
            raw_nodes = output.get("scoped_node_ids", output.get("node_ids"))
            raw_edges = output.get("scoped_edge_ids", output.get("edge_ids"))
            if isinstance(raw_nodes, list):
                candidate_nodes = {str(value) for value in raw_nodes}
            if isinstance(raw_edges, list):
                candidate_edges = {str(value) for value in raw_edges}
            if candidate_nodes is not None:
                scoped_nodes = candidate_nodes
            if candidate_edges is not None:
                scoped_edges = candidate_edges
        if scoped_nodes is None and scoped_edges is None:
            return graph
        return graph.scoped(node_ids=scoped_nodes, edge_ids=scoped_edges)

    def execute(
        self,
        graph: EvidenceGraph,
        workflow: InvestigationWorkflow,
        *,
        execution_id: str | None = None,
    ) -> WorkflowExecutionResult:
        validation_issues = self.validate(workflow)
        errors = [issue for issue in validation_issues if issue.severity == "error"]
        if errors:
            return WorkflowExecutionResult(
                execution_id=execution_id or _execution_id(workflow, graph),
                workflow_id=workflow.workflow_id,
                workflow_version=workflow.version,
                status="VALIDATION_FAILED",
                ordered_node_ids=[],
                node_results=[],
                final_output={},
                issues=validation_issues,
            )

        order = self._topological_order(workflow)
        node_map = {node.id: node for node in workflow.nodes}
        results: dict[str, NodeExecutionResult] = {}
        execution_issues = list(validation_issues)
        halted = False

        for node_id in order:
            node = node_map[node_id]
            incoming = self._inputs_for_node(node_id, workflow, results)
            input_node_ids = sorted(result.node_id for result in self._flatten_inputs(incoming))
            if halted:
                results[node_id] = NodeExecutionResult(
                    node_id=node.id,
                    node_type=node.type,
                    status="SKIPPED_AFTER_FAILURE",
                    input_node_ids=input_node_ids,
                )
                continue
            if not node.enabled:
                results[node_id] = NodeExecutionResult(
                    node_id=node.id,
                    node_type=node.type,
                    status="SKIPPED_DISABLED",
                    input_node_ids=input_node_ids,
                )
                continue
            try:
                output = self._execute_node(node, graph, incoming)
                results[node_id] = NodeExecutionResult(
                    node_id=node.id,
                    node_type=node.type,
                    status="COMPLETED",
                    output=output,
                    input_node_ids=input_node_ids,
                )
            except WorkflowEngineError as exc:
                issue = WorkflowIssue(severity="error", code="NODE_EXECUTION_FAILED", message=str(exc), node_id=node.id)
                execution_issues.append(issue)
                results[node_id] = NodeExecutionResult(
                    node_id=node.id,
                    node_type=node.type,
                    status="FAILED",
                    input_node_ids=input_node_ids,
                    issues=[issue],
                )
                if workflow.failure_policy == WorkflowFailurePolicy.STOP:
                    halted = True
            except Exception as exc:  # pragma: no cover - defensive boundary
                issue = WorkflowIssue(severity="error", code="UNEXPECTED_NODE_FAILURE", message=f"Unexpected failure in node '{node.id}': {type(exc).__name__}: {exc}", node_id=node.id)
                execution_issues.append(issue)
                results[node_id] = NodeExecutionResult(
                    node_id=node.id,
                    node_type=node.type,
                    status="FAILED",
                    input_node_ids=input_node_ids,
                    issues=[issue],
                )
                if workflow.failure_policy == WorkflowFailurePolicy.STOP:
                    halted = True

        completed = all(result.status in {"COMPLETED", "SKIPPED_DISABLED", "SKIPPED_AFTER_FAILURE"} for result in results.values())
        failed = any(result.status == "FAILED" for result in results.values())
        status = "FAILED" if failed else ("COMPLETED" if completed else "UNKNOWN")
        final_output = results[order[-1]].output if order else {}
        return WorkflowExecutionResult(
            execution_id=execution_id or _execution_id(workflow, graph),
            workflow_id=workflow.workflow_id,
            workflow_version=workflow.version,
            status=status,
            ordered_node_ids=order,
            node_results=[results[node_id] for node_id in order],
            final_output=final_output,
            issues=execution_issues,
        )

    def _execute_node(
        self,
        node: WorkflowNode,
        graph: EvidenceGraph,
        incoming: Mapping[str, NodeExecutionResult],
    ) -> dict[str, Any]:
        c = node.config
        if node.type == WorkflowNodeType.TIME_FILTER:
            window = _iso_window(c)
            snapshot, issues = self.temporal_engine.snapshot(graph, window)
            return {
                "window": window.model_dump(mode="json"),
                "snapshot": snapshot.model_dump(mode="json"),
                "active_entity_ids": snapshot.entity_ids,
                "event_ids": snapshot.event_ids,
                "edge_ids": snapshot.edge_ids,
                "scoped_node_ids": snapshot.node_ids,
                "scoped_edge_ids": snapshot.edge_ids,
                "issues": [issue.model_dump(mode="json") for issue in issues],
            }

        if node.type == WorkflowNodeType.EXPAND_NETWORK:
            seeds = [str(value) for value in c.get("seed_entity_ids", [])]
            if not seeds:
                seeds = self._collect_ids_from_inputs(incoming, ("active_entity_ids", "entity_ids", "selected_entity_ids"))
            if not seeds:
                raise WorkflowEngineError("EXPAND_NETWORK requires seed_entity_ids or an upstream node that outputs entity IDs.")
            depth = int(c["depth"])
            discovered = set(seeds)
            frontier = set(seeds)
            for _ in range(depth):
                next_frontier: set[str] = set()
                for node_id in sorted(frontier):
                    if node_id not in graph.nodes:
                        continue
                    next_frontier.update(graph.neighbors(node_id, direction="both"))
                next_frontier -= discovered
                discovered.update(next_frontier)
                frontier = next_frontier
                if not frontier:
                    break
            edges = sorted(
                edge.id
                for edge in graph.edges.values()
                if edge.source_id in discovered and edge.target_id in discovered
            )
            entity_ids = sorted(node_id for node_id in discovered if node_id in graph.nodes and graph.nodes[node_id].kind.value == "ENTITY")
            return {"seed_entity_ids": sorted(set(seeds)), "entity_ids": entity_ids, "node_ids": sorted(discovered), "edge_ids": edges, "scoped_node_ids": sorted(discovered), "scoped_edge_ids": edges, "depth": depth}

        if node.type in {WorkflowNodeType.GRAPH_ANALYTICS, WorkflowNodeType.KEY_INDIVIDUALS, WorkflowNodeType.COMMUNITY_DETECTION, WorkflowNodeType.BRIDGE_ANALYSIS}:
            # Translate only supported workflow config into a fresh analytics
            # engine; the shared service object is never mutated by a workflow.
            from clarity.intelligence.graph_analytics import GraphAnalyticsConfig, GraphAnalyticsEngine
            engine = GraphAnalyticsEngine(
                GraphAnalyticsConfig(
                    target_entity_types=c.get("target_entity_types", self.graph_analytics_engine.config.target_entity_types),
                    include_event_interactions=c.get("include_event_interactions", self.graph_analytics_engine.config.include_event_interactions),
                    max_pagerank_iterations=self.graph_analytics_engine.config.max_pagerank_iterations,
                    pagerank_tolerance=self.graph_analytics_engine.config.pagerank_tolerance,
                    community_max_iterations=self.graph_analytics_engine.config.community_max_iterations,
                )
            )
            analysis_graph = self._scoped_graph_from_inputs(graph, incoming)
            report = engine.analyze(analysis_graph)
            scope = {
                "scoped_node_ids": sorted(analysis_graph.nodes),
                "scoped_edge_ids": sorted(analysis_graph.edges),
            }
            if node.type == WorkflowNodeType.GRAPH_ANALYTICS:
                payload = report.model_dump(mode="json")
                payload.update(scope)
                return payload
            if node.type == WorkflowNodeType.KEY_INDIVIDUALS:
                top_k = int(c.get("top_k", 10))
                payload = {"key_individuals": [item.model_dump(mode="json") for item in report.key_individuals[:top_k]], "rank_count": min(top_k, len(report.key_individuals))}
                payload.update(scope)
                return payload
            if node.type == WorkflowNodeType.COMMUNITY_DETECTION:
                payload = {"communities": [item.model_dump(mode="json") for item in report.communities]}
                payload.update(scope)
                return payload
            min_ratio = float(c.get("minimum_cross_community_ratio", 0.5))
            candidates = engine.find_bridge_candidates(analysis_graph, minimum_cross_community_ratio=min_ratio)
            payload = {"bridge_candidates": [item.model_dump(mode="json") for item in candidates]}
            payload.update(scope)
            return payload

        if node.type == WorkflowNodeType.ANOMALY_DETECTION:
            target = _iso_window(c, "target_")
            baseline = _iso_window(c, "baseline_") if "baseline_start" in c and "baseline_end" in c else None
            from clarity.intelligence.anomaly_engine import AnomalyEngine
            anomaly_engine = AnomalyEngine(
                temporal_engine=self.temporal_engine,
                graph_analytics_engine=self.graph_analytics_engine,
            )
            report = anomaly_engine.analyze(graph, target, baseline_window=baseline)
            if "max_findings" in c:
                max_findings = int(c["max_findings"])
                report = report.model_copy(update={"findings": report.findings[:max_findings], "finding_count": min(max_findings, report.finding_count)})
            return report.model_dump(mode="json")

        if node.type == WorkflowNodeType.SHORTEST_PATH:
            source_id = str(c["source_id"])
            target_id = str(c["target_id"])
            result = self.graph_analytics_engine.shortest_path(graph, source_id, target_id)
            return result.model_dump(mode="json")

        if node.type == WorkflowNodeType.EVIDENCE_REVIEW:
            entity_ids = set(str(value) for value in c.get("entity_ids", []))
            event_ids = set(str(value) for value in c.get("event_ids", []))
            relationship_ids = set(str(value) for value in c.get("relationship_ids", []))
            finding_ids = set(str(value) for value in c.get("finding_ids", []))
            # Pull IDs from common upstream outputs when explicit IDs are absent.
            if not entity_ids:
                entity_ids.update(self._collect_ids_from_inputs(incoming, ("entity_ids", "active_entity_ids", "selected_entity_ids")))
            if not event_ids:
                event_ids.update(self._collect_ids_from_inputs(incoming, ("event_ids", "supporting_event_ids")))
            if not relationship_ids:
                relationship_ids.update(self._collect_ids_from_inputs(incoming, ("edge_ids", "supporting_relationship_ids")))
            reviewed_nodes = []
            for node_id in sorted(entity_ids | event_ids):
                if node_id in graph.nodes:
                    reviewed_nodes.append(graph.nodes[node_id].model_dump(mode="json"))
            reviewed_edges = [graph.edges[edge_id].model_dump(mode="json") for edge_id in sorted(relationship_ids) if edge_id in graph.edges]
            finding_refs = []
            for result in self._flatten_inputs(incoming):
                findings = result.output.get("findings", [])
                if isinstance(findings, list):
                    for finding in findings:
                        if isinstance(finding, dict):
                            if not finding_ids or finding.get("finding_id") in finding_ids:
                                finding_refs.append(finding)

            evidence_references = []
            seen_refs = set()
            for reviewed_node in reviewed_nodes:
                for ref in reviewed_node.get("source_refs", []):
                    key = (ref.get("document_id"), ref.get("file_hash_sha256"), ref.get("page"), ref.get("text_span"))
                    if key not in seen_refs:
                        seen_refs.add(key)
                        evidence_references.append({"object_id": reviewed_node["id"], "object_type": reviewed_node["kind"], "reference": ref})
            for reviewed_edge in reviewed_edges:
                for ref in reviewed_edge.get("source_refs", []):
                    key = (ref.get("document_id"), ref.get("file_hash_sha256"), ref.get("page"), ref.get("text_span"))
                    if key not in seen_refs:
                        seen_refs.add(key)
                        evidence_references.append({"object_id": reviewed_edge["id"], "object_type": "RELATIONSHIP", "reference": ref})
            return {
                "nodes": reviewed_nodes,
                "edges": reviewed_edges,
                "findings": finding_refs,
                "evidence_references": evidence_references,
            }

        if node.type == WorkflowNodeType.REPORT:
            include_ids = c.get("include_node_outputs")
            upstream = {result.node_id: result for result in self._flatten_inputs(incoming)}
            selected_ids = list(include_ids) if isinstance(include_ids, list) else sorted(upstream)
            sections: dict[str, Any] = {}
            for node_id in selected_ids:
                if node_id in upstream:
                    sections[node_id] = upstream[node_id].output
            report = {
                "title": c.get("title", node.label or "Investigation Report"),
                "workflow_context": {"node_ids": selected_ids},
                "sections": sections,
                "notes": c.get("notes", ""),
                "generated_as": "DETERMINISTIC_WORKFLOW_REPORT",
            }
            return report

        raise WorkflowEngineError(f"Unsupported workflow node type '{node.type}'.")


def build_workflow(**data: Any) -> InvestigationWorkflow:
    """Convenience constructor for API/tests/UI integration."""
    return InvestigationWorkflow(**data)
