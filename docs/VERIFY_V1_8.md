# Verify V1.8 — Investigation Canvas UI

## Goal
Verify that the new interactive investigation canvas renders and its core interactions work.

## Frontend checks
From `frontend/`:

```powershell
npm ci
npm run build
```

Then run:

```powershell
npm run dev
```

Open the local Next.js URL shown by the terminal.

## Manual acceptance checklist

1. `Investigation Canvas` appears in the navigation bar.
2. The canvas opens without a runtime error.
3. The seeded workflow contains the seven default nodes and their connections.
4. Nodes can be dragged.
5. Clicking an output pin puts the canvas into connection mode.
6. Clicking another node's input pin creates a new edge.
7. The selected node configuration panel updates when different nodes are selected.
8. Analysis nodes can be added from the palette.
9. A selected node can be deleted.
10. `RESET` restores the default workflow.
11. `RUN PREVIEW` animates the deterministic seven-step UI trace.
12. No live execution claim is made; V1.8 is a frontend workflow-editor milestone.
