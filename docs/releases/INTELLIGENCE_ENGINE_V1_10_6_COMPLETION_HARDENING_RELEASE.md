# SANKET — V1.10.6 + C1 Completion Hardening

## Scope

This milestone moves the frozen V1.10.6 product into finalization without replacing its architecture or investigation-first UI direction.

## Implemented

### AI investigation planner
- Natural-language question endpoint.
- Local Ollama and OpenAI-compatible text transport.
- JSON-only planner contract.
- Pydantic workflow validation.
- Existing deterministic workflow-engine validation.
- Explicit rejection of graph/entity IDs that were not selected by the investigator.
- No arbitrary SQL, shell, filesystem, or tool execution is exposed to the model.

### Reporting
- Structured report model.
- Findings collected from bridge/key/anomaly workflow outputs.
- Provenance/contradiction counts.
- Explicit uncertainty notes.
- Markdown export.

### Human review
- Field verification/correction endpoint.
- Original extracted value remains unchanged.
- Corrected value and reviewer are stored separately.
- Audit log entry is written for each review action.

### Workflow UX
- Save/load workflow locally per active case.
- AI plan preview and apply-to-canvas flow.
- Report export after a successful workflow execution.

### API/runtime hardening
- CORS allow-list is configurable through `CORS_ALLOWED_ORIGINS`.
- File upload size is configurable through `MAX_UPLOAD_SIZE_MB`.
- OpenAI dependency is only imported when a non-Ollama transport is actually used.

## Validation

- Python regression suite: **147 passed**.
- TypeScript parser pass was completed with the global compiler; unresolved module/type diagnostics remain because frontend npm dependencies are not installed in the build environment.
- Full `npm run build` must be run on the target development machine after `npm ci`.

## Release rule

Keep the frozen V1.10.6 visual structure intact. The next work should be end-to-end validation, benchmark capture, demo recording, deployment packaging and submission documentation.
