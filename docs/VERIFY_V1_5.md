# V1.5 Verification

From the project root:

```powershell
python -m pytest -q tests\test_graph_contract_adapter.py
python -m pytest -q tests\test_entity_resolution.py
python -m pytest -q tests\test_evidence_graph.py
python -m pytest -q tests\test_temporal_engine.py
python -m pytest -q tests\test_graph_analytics.py
python -c "from clarity.intelligence import GraphAnalyticsEngine; print('Graph Analytics import: OK')"
```

Expected dedicated analytics result:

```text
10 passed
Graph Analytics import: OK
```

The full cumulative suite should also be run before accepting V1.5 as the next `perfect` backup.
