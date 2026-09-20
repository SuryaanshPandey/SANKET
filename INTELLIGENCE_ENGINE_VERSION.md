# Intelligence Engine Version

Current milestone: **V1.10.6 + C4 — Workflow Experience Completion**

Stable technical baseline: **V1.10.5 — Map, Graph Layout & Contextual Help**

## V1.10.4 scope

This milestone redesigns the complete frontend information architecture and visual system around the product's actual purpose: collecting fragmented evidence into one persistent case memory and helping an investigator explore, investigate and verify it. It also restores persisted case state on workspace load and prefers the case-level Graph Contract for relationship visualization.

The backend intelligence, Graph Contract, Evidence Graph, Temporal Engine, Graph Analytics, Anomaly Engine, Investigation Workflow Engine, Provenance and Contradiction APIs remain unchanged.

### New information architecture

```text
CASE
  Overview

EXPLORE
  Entity network
  Locations

INVESTIGATE
  Workflow

EVIDENCE
  Ledger
  Documents

REVIEW
  Evidence review
  Quality & analytics
```

### Frontend changes

- Case-memory overview replaces tactical KPI-heavy dashboard presentation.
- Entity network gains a clean investigation toolbar, entity search and source navigation.
- Locations gains a clean map/list relationship and a case-fit control.
- Evidence ledger gains direct source-document inspection from every row.
- Document Inspector is reorganized into source image, provenance metadata and field review.
- Evidence Review is reorganized around contradictions and traceable objects.
- Analytics is reframed around useful quality and analytical signals instead of decorative radar/rose charts.
- Investigation Canvas output is kept in the selected-node inspector rather than rendered inside every workflow node.
- Global interface removes redundant tactical/certification language and decorative glow effects.
- Document strip remains visible but compact, with an explicit source-inspector action.
- Ingestion remains a persistent primary action.

### Preserved functionality

- multi-document ingestion;
- sample dataset loading;
- asynchronous factual progress;
- Cytoscape graph;
- network layouts and controls;
- node inspection;
- MapLibre locations;
- evidence ledger sorting/filtering/export;
- document image switching and bounding boxes;
- Graph Contract export;
- evidence provenance;
- contradiction review;
- investigation canvas editing;
- deterministic workflow execution;
- backend execution trace.

## Acceptance

Acceptance requires:

1. Python test suite remains green.
2. Next.js production build passes on the user's machine.
3. Every visible primary action has a functional effect.
4. No core feature is hidden behind decorative UI.
5. No unsupported legal certification claim is presented as an application-wide guarantee.

## V1.10.5 scope

This milestone improves the case-memory frontend without changing the backend intelligence architecture. The Entity Network now uses a connection-aware force layout with stronger component spacing, hides labels for isolated observations until hover/search to prevent visual collisions, exposes an explicit Auto Arrange action, and shows a contextual hover card for nodes and relationships. The Locations workspace now uses OpenStreetMap standard raster tiles with visible attribution and interactive case markers. Interactive controls across the workspace also expose plain-language hover help/tooltips so a new investigator can understand what each control does.

### V1.10.5 acceptance

- OpenStreetMap tiles render behind the location evidence panel.
- OSM attribution remains visible on the map.
- Connected graph components are automatically separated and arranged from current relationships.
- Dense network labels no longer dominate the graph; full labels remain available on hover and search.
- Auto Arrange, zoom, fit, layout selection and source inspection remain functional.
- Workflow node library, connection pins, navigation, evidence, review and inspection controls expose descriptive hover help.
- Backend intelligence and stored evidence contracts remain unchanged.


## V1.10.6 scope — Evidence-linked network composition

This milestone corrects the sparse/field-level network presentation observed after V1.10.5. The default Entity Network now renders investigator-facing semantic entities and event nodes while excluding field-like `OTHER`/identifier/date/hash observations from the main graph. Case documents are represented as evidence objects and connected to observed entities/events through explicitly dashed `OBSERVED_IN` links. Direct semantic relationships remain visually distinct.

### V1.10.6 behavior

- The network is arranged from actual semantic relationships plus source-evidence links.
- Unconnected field observations do not overwhelm the relationship view.
- Source documents act as evidence anchors, making the scattered-to-connected case-memory concept visible in one graph.
- `Show unconnected observations` remains available for objects with no graph connection.
- Hover and selection expose object type, confidence, connections, and source context.
- Document/source edges are contextual evidence links, not inferred interpersonal relationships.
- All extracted fields remain available in the Evidence Ledger and Document Inspector.


## V1.10.6 + C2 — finalization

This milestone does not introduce a new product surface. It packages the existing intelligence, evidence, workflow and light-theme interface for final validation and demo readiness.

### Added delivery tooling

- `scripts/final_acceptance.py` — deterministic VLM-free synthetic acceptance harness.
- `artifacts/final_acceptance.json` — machine-readable acceptance result.
- `artifacts/final_acceptance.md` — human-readable acceptance summary.
- `docs/FINALIZATION_AND_DEMO.md` — manual end-to-end gate and five-minute demo plan.
- `submission/SUBMISSION_MANIFEST.md` — submission fields, disclosure/security notes and final checklist.

### Verified in the release workspace

- Python regression suite: **148 passed**.
- Deterministic final acceptance: **8/8 checks passed**.
- Frontend TypeScript/TSX parser validation: **PASS**.
- Global CSS brace/syntax balance check: **PASS**.

### Remaining target-machine gate

- Run `npm ci` and `npm run build` on the target Windows machine.
- Complete fresh-case manual acceptance.
- Verify local Ollama planner behaviour in the target environment.
- Record and test the final demo video.
- Complete submission links and publish the final source repository.

The deterministic benchmark is synthetic and validates software behaviour; it must not be presented as real-world criminal-network accuracy.


## V1.10.6 + C4 scope — Workflow Experience Completion

- Dedicated workflow results workspace with Insights, Evidence, Run and Report views.
- Automatic results opening after completed/failed execution.
- Finding cards for bridge, key-individual and anomaly outputs with source object counts and score/severity where available.
- Evidence and contradiction summaries expose what supports a finding and what still requires review.
- Execution history is retained locally per case for inspection of compact run snapshots.
- Finding-to-workflow-node and finding-to-Entity-Network navigation is supported where the canonical entity match is available.
- Workflow canvas layout is responsive across wide, medium and small viewports, with palette overlay and stacked results/inspector layouts at narrower widths.
- Existing C3 output/input connection editing, safe custom nodes, AI planning, deterministic execution and light-theme visual system are preserved.

### C4 validation
- Python regression suite: 149 passed in the release workspace.
- TypeScript/TSX transpile validation: 17/17 source files parsed successfully.
- Global CSS brace validation: balanced.
- Full Next.js production build remains a target-machine gate because dependency installation was not available in the release environment.
