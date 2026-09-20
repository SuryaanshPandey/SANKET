# Graph Contract Adapter — Team 2 Investigation Engine

This milestone defines the handoff from Vaibhav's Clarity extraction/evidence pipeline to the post-extraction criminal-network intelligence engine.

## Boundary

```text
Clarity document extraction
        ↓
GraphContractResponse / JSON
        ↓
GraphContractAdapter
        ↓
Canonical InvestigationGraph
        ↓
Entity Resolution → Evidence Graph → Temporal/Graph Analytics → Patterns → Investigation Workflow → AI/UI
```

## Added files

```text
clarity/intelligence/
├── __init__.py
├── models.py
└── graph_contract_adapter.py

tests/test_graph_contract_adapter.py
```

## Usage

```python
from clarity.intelligence import GraphContractAdapter

adapter = GraphContractAdapter(strict=True)
graph = adapter.adapt(contract_payload)
```

Accepted input types:
- existing `GraphContractResponse`
- Python mapping/dict
- JSON string
- UTF-8 JSON bytes

## Strict vs non-strict

`strict=True` is the integration default. Structural problems raise `GraphContractAdapterError` so invalid graph data cannot silently flow into analytics.

`strict=False` returns the canonical graph and records quality problems in `graph.issues` for inspection.

## Important design constraints

The adapter does not perform fuzzy entity resolution, graph analytics, anomaly detection, LLM calls, Neo4j persistence or UI work.

It preserves:
- entity/event IDs
- Clarity source traceability
- timestamps
- relationship evidence text
- audit-chain metadata

A relationship receives a provenance reference only when that reference can be objectively derived from a linked event endpoint. The adapter never fabricates relationship provenance.
