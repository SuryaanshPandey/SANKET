# V1.6 Verification

From the project root:

```powershell
python -m pytest -q tests\test_graph_contract_adapter.py
python -m pytest -q tests\test_entity_resolution.py
python -m pytest -q tests\test_evidence_graph.py
python -m pytest -q tests\test_temporal_engine.py
python -m pytest -q tests\test_graph_analytics.py
python -m pytest -q tests\test_anomaly_engine.py
python -c "from clarity.intelligence import AnomalyEngine; print('Anomaly Engine import: OK')"
```

Expected dedicated anomaly suite:

```text
14 passed
Anomaly Engine import: OK
```

Also run the complete intelligence suite before creating the V1.6 `perfect` backup.
