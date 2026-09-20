# SANKET — V1.10.6 + C3 Workflow Builder / Planner Reliability

## Scope

C3 addresses the investigator-facing workflow canvas interaction gap discovered during target-machine review. The approved V1.10.6 light-theme visual system remains the presentation baseline; this release adds workflow-editor interactions and hardens the AI planner without changing the Evidence Graph, document extraction contract, or deterministic analytical engine.

## Workflow canvas changes

- Drag directly from an output port to an input port to create a connection.
- A live dashed wire follows the pointer while a connection is being created.
- Invalid connections are rejected when they would self-loop, duplicate an existing edge, or introduce a workflow cycle.
- Existing connections can be clicked and selected.
- Selected connections can be deleted from the toolbar, inspector, or keyboard Delete/Backspace.
- Escape cancels an active connection.
- Nodes remain draggable without accidentally starting a node drag when a control/port is clicked.
- Selected nodes can be duplicated without copying their existing connections.
- The selected connection inspector identifies source, target and edge ID.
- Workflow direction is visually reinforced with arrow markers.
- Save/Load/Reset and backend execution continue to operate on the same `InvestigationWorkflow` model.

## AI planner reliability changes

Local instruction-tuned models can occasionally serialize edge endpoints using ordinal placeholders such as `node-2` even when the real workflow node IDs differ. The planner now:

1. requires exact node-ID references in its system prompt;
2. deterministically maps common `node-N`, `step-N` and `n-N` placeholders to the Nth emitted workflow node;
3. surfaces every repair as a planner warning;
4. still rejects arbitrary unknown node references, self-loops and cycles.

This preserves the safety boundary: the LLM still cannot execute arbitrary commands or invent selected entity identifiers.

## Frontend response handling

The planner dialog now safely handles non-JSON backend responses and reports the HTTP status instead of exposing a generic JSON parse failure.

## Validation

Release workspace result after C3 changes:

- Python regression suite: **149 passed**.
- AI planner tests: **3 passed**.
- Workflow API tests: **4 passed**.
- Final acceptance test: **1 passed**.
- Investigation Canvas TSX transpile/syntax validation: **PASS**.
- Python compilation: **PASS**.

A full Next.js production build still requires the target machine to run `npm ci` and `npm run build` because the release workspace does not contain `node_modules`.

## Known target-machine browser note

If the browser reports `Failed to load module script: The server responded with a non-JavaScript MIME type of "text/html"`, remove the frontend `.next` cache and restart the Next.js server. This is consistent with a stale/missing chunk being requested as HTML after replacing the release folder; it is not an application API response.
