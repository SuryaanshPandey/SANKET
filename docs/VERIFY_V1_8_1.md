# Verify V1.8.1 — Clarity VLM Integration Fix

## Purpose
Confirm that local Ollama multimodal requests actually send image bytes to the model and produce structured extraction before a full dossier run.

## 1. Verify one image first
From the project root:

```powershell
python scripts/verify_ollama_vision.py samples\sample_fir_report.png
```

Expected high-level outcome:
- Transport reports `ollama-native` for the default local endpoint.
- The result is not the fallback-only message `Extracted via forensic heuristic recovery engine`.
- At least one useful party/identifier/date/summary is extracted from a readable benchmark image, subject to the model's actual ability to read that image.
- Diagnostics no longer silently hide a transport error.

## 2. Run the existing intelligence tests

```powershell
python -m pytest -q tests\test_graph_contract_adapter.py tests\test_entity_resolution.py tests\test_evidence_graph.py tests\test_temporal_engine.py tests\test_graph_analytics.py tests\test_anomaly_engine.py tests\test_workflow_engine.py
```

The V1.8 intelligence baseline should remain green.

## 3. Only after step 1 succeeds, rerun the five-document police dossier

Use the existing UI's `Forensic Police Dossier (5 docs)` ingest flow.

Acceptance criteria:
- Documents are no longer all classified as `OTHER` when filename/type cues are explicit.
- Documents have non-empty extraction fields where the image contains readable evidence.
- The Graph Contract contains real entities/events/relationships rather than the heuristic legibility note as an `OTHER` entity.
- Entity Network is not empty when the source case contains extracted entities.

## 4. If step 1 fails
Do not rerun the five-document dossier. Capture the full terminal output from the one-image diagnostic and replace this build only after the transport/model issue is fixed.
