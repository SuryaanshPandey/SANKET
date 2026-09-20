# Verify V1.3 — Evidence Graph

Run from the project root.

## Milestone tests

```powershell
python -m pytest -q tests\test_graph_contract_adapter.py
python -m pytest -q tests\test_entity_resolution.py
python -m pytest -q tests\test_evidence_graph.py
```

Expected:

- Graph Contract Adapter: 11 passed
- Entity Resolution: 10 passed
- Evidence Graph: 13 passed

## Import check

```powershell
python -c "from clarity.intelligence import EvidenceGraphBuilder; print('Evidence Graph import: OK')"
```

## Full suite

```powershell
python -m pytest -q
```

Existing Clarity tests may require the environment/model dependencies described by the root project README. The three commands above isolate the investigation-engine milestone and are the primary V1.3 gate.
