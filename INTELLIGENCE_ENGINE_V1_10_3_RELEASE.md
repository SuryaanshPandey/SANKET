# SANKET Intelligence Engine — V1.10.3

## Factual Ingestion Progress & Completion Semantics

### Problem

The previous frontend used a time-based progress simulation that intentionally capped at 95% while the VLM continued processing in the backend. This created a misleading “stuck at 95%” experience.

### V1.10.3 solution

- Background batch ingestion endpoint returns a batch ID immediately.
- Backend status endpoint exposes actual persisted progress.
- Pipeline reports real stage boundaries before and after long operations.
- Current document and current stage are visible.
- The frontend polls backend status rather than estimating completion from elapsed time.
- 100% is shown only after the batch status becomes `completed`.
- Failed jobs terminate in `failed` rather than appearing to continue.
- A short indeterminate shimmer communicates activity during long VLM inference without falsifying percent complete.
- Existing synchronous endpoints remain intact for compatibility.

### Completion contract

```text
START REQUEST
    ↓
202 Accepted + batch_id
    ↓
POLL /batches/{batch_id}/status
    ↓
confirmed backend stage updates
    ↓
status = completed
    ↓
FETCH completed batch result
    ↓
100%
```

### Explicit non-goals

- no VLM model change;
- no inference-speed claim;
- no removal of synchronous API compatibility;
- no fake ETA;
- no completion state before backend reconciliation finishes.
