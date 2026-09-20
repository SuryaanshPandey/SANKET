# Clarity Investigation Engine — V1 Verification

This is the first complete development snapshot combining the Clarity extraction repository with the post-extraction Graph Contract Adapter.

## What this milestone contains

```text
Clarity extraction/evidence pipeline
        ↓
Graph Contract
        ↓
GraphContractAdapter
        ↓
Canonical InvestigationGraph
```

The current milestone does not yet implement entity-resolution intelligence, Neo4j persistence, temporal analytics, anomaly detection, bridge detection, AI investigation, or the investigation canvas.

## Setup

From the project root:

```powershell
python -m pip install -e ".[dev]"
```

This installs the dependencies declared by `pyproject.toml`, including the development test dependencies.

## Adapter test

Run:

```powershell
python -m pytest -q tests/test_graph_contract_adapter.py
```

Expected result:

```text
11 passed
```

## Import checks

```powershell
python -c "from clarity.intelligence.graph_contract_adapter import GraphContractAdapter; print('Adapter import: OK')"
```

```powershell
python -c "from clarity.intelligence.models import InvestigationGraph; print('Models import: OK')"
```

## Integration gate

The unit tests use controlled contract payloads. Before starting the next development layer, obtain one real response from Clarity's running API:

```text
GET /api/v1/cases/{case_id}/graph-contract
```

or:

```text
GET /api/v1/documents/{document_id}/graph-contract
```

That real payload should be tested through `GraphContractAdapter` before the intelligence/graph layer is implemented.
