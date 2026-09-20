# SANKET — V1.10.6 + C4 Workflow Experience Completion

## Scope

C4 completes the investigator-facing workflow experience over the existing deterministic workflow engine. The approved V1.10.6 light-theme visual system and C3 interactive workflow builder remain intact.

## Results workspace

After a successful or failed workflow execution, the workspace can open a dedicated **Workflow Results** surface with four views:

- **Insights** — analytical leads from bridge candidates, key individuals and anomaly findings, with scores/severity where supplied by the engine.
- **Evidence** — provenance/evidence counts, contradiction summaries and source references returned through Evidence Review.
- **Run** — execution ID, per-node execution status, validation issues and recent browser-local execution history.
- **Report** — deterministic report preview and Markdown export.

The existing node inspector remains available beside the result surface. A selected finding can jump back to its originating workflow node. When a finding's canonical entity label matches a reconciled case entity, the investigator can open Entity Network from that finding.

## Responsive behavior

- Wide desktop: palette + canvas + results/inspector.
- Medium desktop: palette becomes an overlay to protect canvas width.
- Smaller widths: results and node inspector stack vertically while the canvas remains the primary workspace.
- Explicit zoom and fit controls are retained; node controls are not shrunk below a practical size.

## Manual workflow composition

The existing C3 interaction model remains:

- drag a palette operation into the canvas or click to add it;
- create a custom executable node from an allow-listed operation;
- drag output pin → input pin to connect nodes;
- click an edge to select it;
- Delete/Backspace removes the selected node/edge when focus is not inside a form control;
- Escape cancels connection mode;
- self-loops, duplicates and cycles are rejected before backend execution.

## Safety boundary

Custom labels and descriptions do not introduce new executable code. The workflow layer executes only the allow-listed `WorkflowNodeType` operations already implemented and tested by the backend. AI planning remains a workflow-generation helper and cannot directly execute arbitrary Python, SQL, shell commands or database instructions.

## Validation

Release workspace checks:

- Python regression suite: **149 passed**.
- TypeScript/TSX transpile validation: **17/17 source files parsed successfully**.
- Global CSS brace validation: **balanced**.
- Full Next.js production build: **target-machine gate**; npm dependency installation was not available to complete the build in this environment.

## Acceptance sequence

1. Ask the AI planner for an investigation.
2. Apply the AI workflow.
3. Add a manual node or custom node.
4. Connect nodes by dragging output to input.
5. Validate and run.
6. Use Workflow Results to inspect what was discovered, what supports it and what remains unresolved.
7. Open a finding back on the graph/evidence context.
8. Export the deterministic report.
