# Verify V1.10.7

## Scope
Presentation-layer frontend redesign based on the audited case-memory brief. Backend/API, graph, map and workflow engines are preserved.

## Local acceptance
Run from the project root:

```powershell
python -m pytest -q

cd frontend
npm install
npm run build
npm run dev
```

## Manual QA

- Overview: case memory summary, attention, entities and timeline.
- Entity network: semantic nodes, evidence anchors, search/layout/fit/inspect.
- Locations: OpenStreetMap, docked location panel and marker selection.
- Workflow: existing node editing/execution preserved; visual normalization applied.
- Ledger: readable fields, confidence indicator, source thread and CSV export.
- Documents: source image, fields, bounding boxes, integrity metadata and Graph Contract export.
- Evidence review: contradictions, provenance and source inspection.
- Quality & analytics: coverage threshold, role mix and review queue.

## Environment note
The isolated build environment used for packaging did not contain the full Python/frontend dependency tree, so the complete test suite and Next.js production build remain a user-machine acceptance gate. TypeScript/TSX source syntax was parsed successfully during packaging.
