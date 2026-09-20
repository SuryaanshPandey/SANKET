# V1.4 Verification Guide

Run these from the project root.

```powershell
python -m pytest -q tests\test_graph_contract_adapter.py
python -m pytest -q tests\test_entity_resolution.py
python -m pytest -q tests\test_evidence_graph.py
python -m pytest -q tests\test_temporal_engine.py
python -c "from clarity.intelligence import TemporalEngine, TimeWindow; print('Temporal Engine import: OK')"
```

Expected test results for this milestone:

- Graph Contract Adapter: 11 passed
- Entity Resolution: 10 passed
- Evidence Graph: 14 passed
- Temporal Engine: 11 passed
- Combined: 46 passed

The exact total should only change if the test suites themselves are intentionally extended.

V1.4 is ready to become a `perfect` backup only after the local machine reproduces the expected results.
