# Verify V1.7

From the project root:

```powershell
python -m pytest -q tests\test_graph_contract_adapter.py tests\test_entity_resolution.py tests\test_evidence_graph.py tests\test_temporal_engine.py tests\test_graph_analytics.py tests\test_anomaly_engine.py tests\test_workflow_engine.py; python -c "from clarity.intelligence import InvestigationWorkflowEngine; print('Workflow Engine import: OK')"
```

Expected V1.7 result:

- 85 tests passed (70 previous intelligence tests + 15 workflow tests)
- `Workflow Engine import: OK`

If the 15 workflow tests fail, do not modify the project manually; report the complete traceback/output and use the next replacement ZIP.
