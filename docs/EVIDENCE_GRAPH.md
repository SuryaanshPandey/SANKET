# Evidence Graph — V1.3

## Purpose

This milestone creates the database-agnostic evidence graph that sits after Clarity extraction and entity resolution and before temporal/network analytics.

```text
Clarity Graph Contract
        ↓
Graph Contract Adapter
        ↓
Entity Resolution
        ↓
Evidence Graph  ← this milestone
        ↓
Temporal Engine / Graph Analytics / Pattern Detection
```

## Core rules

1. Entities and events are first-class graph nodes.
2. Relationships remain evidence-aware; they retain confidence, epistemic status, evidence text and provenance references.
3. Confirmed entity-resolution clusters collapse multiple raw IDs to the cluster's canonical node while retaining member IDs and aliases.
4. Entity attributes are aggregated. Conflicting values are retained as arrays and recorded under `attribute_conflicts` rather than silently overwritten.
5. Events preserve timestamps and participant IDs for the future temporal engine.
6. Isolated entities are preserved. Lack of an edge is not proof that no relationship exists.
7. Dangling relationships and incompatible node/edge IDs are surfaced as structural issues and are fatal in strict mode.
8. If entity resolution collapses two endpoints into one node, the relationship is retained and explicitly marked as a `COLLAPSED_SELF_RELATIONSHIP` warning rather than silently discarded.
9. The graph is currently in-memory and database-agnostic. Neo4j persistence is deliberately deferred.
10. The graph represents evidence and analytical relationships; it does not determine criminality.

## Module

`clarity/intelligence/evidence_graph.py`

Main API:

- `EvidenceGraphBuilder`
- `GraphBuildConfig`
- `EvidenceGraph`
- `GraphNode`
- `GraphEdge`
- `GraphBuildIssue`
- `build_evidence_graph(...)`

## Deterministic query primitives

- `get_node()`
- `get_edge()`
- `neighbors()`
- `incident_edges()`
- `relationship_between()`
- `shortest_path()`
- `to_records()`

## Deliberately deferred

- Neo4j persistence
- centrality/community detection
- bridge/middleman scoring
- anomaly detection
- temporal window engine
- AI-generated workflows
- frontend canvas
