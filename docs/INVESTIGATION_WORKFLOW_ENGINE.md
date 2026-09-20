# Investigation Workflow Engine — V1.7

V1.7 adds the deterministic workflow orchestration layer for the PS #13 investigation canvas.

## Purpose

The workflow engine is the executable backend model for the planned n8n-style investigation canvas. It is not the UI itself. It allows the frontend to represent analytical steps as nodes connected by typed workflow edges, validate the graph, execute it in deterministic topological order, and preserve each node's intermediate output.

## Separation of concerns

```text
Evidence Graph = what the case data says
Investigation Workflow = what the investigator asks the system to do
```

The same evidence graph can therefore be analyzed by multiple workflows without mutating the evidence source of truth.

## Supported V1.7 nodes

- `TIME_FILTER` — creates a temporal scope/snapshot.
- `EXPAND_NETWORK` — expands an entity neighborhood to a configured hop depth.
- `GRAPH_ANALYTICS` — runs the existing graph analytics report.
- `KEY_INDIVIDUALS` — returns the top analytical network-influence leads.
- `COMMUNITY_DETECTION` — returns deterministic graph communities.
- `BRIDGE_ANALYSIS` — returns structural bridge/intermediary candidates.
- `ANOMALY_DETECTION` — executes the existing explainable suspicious-pattern engine.
- `SHORTEST_PATH` — finds a path between two eligible entities.
- `EVIDENCE_REVIEW` — collects graph nodes/edges and upstream findings for inspection.
- `REPORT` — packages selected upstream outputs into a deterministic investigation report structure.

## Safety boundary

The engine has an allow-list of supported node types and configuration keys. It never executes arbitrary Python, shell, SQL, browser code, or LLM-generated code. A future AI agent must generate a `InvestigationWorkflow`/structured workflow JSON, which must pass the same validation before execution.

## Validation

The engine rejects:

- duplicate node IDs;
- duplicate edge IDs;
- missing source/target nodes;
- self-loops;
- duplicate incoming connections to the same input port;
- unknown node configuration keys;
- invalid time windows;
- invalid node-specific parameters;
- workflow cycles.

## Determinism

Node execution follows a stable topological order. The execution ID is derived from the workflow definition and graph structure, making repeated execution of the same workflow against the same graph reproducible at the orchestration level.

## Example workflow

```json
{
  "workflow_id": "WF-BRIDGE-001",
  "version": "1.0.0",
  "name": "Find Cross-Community Intermediaries",
  "nodes": [
    {
      "id": "time_30d",
      "type": "TIME_FILTER",
      "config": {
        "start": "2026-08-01T00:00:00+05:30",
        "end": "2026-08-31T23:59:59+05:30"
      }
    },
    {
      "id": "bridge",
      "type": "BRIDGE_ANALYSIS",
      "config": {
        "minimum_cross_community_ratio": 0.5
      }
    },
    {
      "id": "review",
      "type": "EVIDENCE_REVIEW"
    },
    {
      "id": "report",
      "type": "REPORT",
      "config": {
        "title": "Bridge Analysis Report"
      }
    }
  ],
  "edges": [
    {"id": "e1", "source_node_id": "time_30d", "target_node_id": "bridge"},
    {"id": "e2", "source_node_id": "bridge", "target_node_id": "review"},
    {"id": "e3", "source_node_id": "review", "target_node_id": "report"}
  ]
}
```

The V1.7 engine does not yet implement full semantic scoping of every analytics operation by every upstream node. For example, `TIME_FILTER` records a valid temporal scope, while graph analytics currently operate on the evidence graph unless their own service receives a scoped graph. This is intentional: scope propagation into all analytical services is a later milestone, and V1.7 establishes the workflow contract and safe execution model first.
