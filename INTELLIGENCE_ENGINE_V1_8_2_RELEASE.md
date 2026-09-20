# Intelligence Engine V1.8.2 — Batch Pipeline Compatibility Fix

## Problem fixed

The V1.8.1 filename-based document-type fallback called
`infer_document_type_from_filename()` through `self.vlm_client`.

In production this works for a real `VLMClient`, but it breaks isolated pipeline tests that inject a mocked VLM client because the mock creates a `MagicMock` for the unconfigured method. SQLAlchemy then receives that `MagicMock` as `doc_type`, causing:

```text
sqlite3.ProgrammingError: Error binding parameter 1: type 'MagicMock' is not supported
```

## Fix

The fallback now calls the deterministic class method directly:

```python
VLMClient.infer_document_type_from_filename(original_filename)
```

This keeps filename inference independent of the injected transport/mock and preserves the intended behavior: filename inference is only used when VLM classification is `other` or below the confidence threshold.

## Scope

- No change to Ollama transport.
- No change to extraction schema.
- No change to graph-contract behavior.
- No change to investigation/analytics logic.
- Fixes batch-pipeline compatibility with mocked VLM clients.
