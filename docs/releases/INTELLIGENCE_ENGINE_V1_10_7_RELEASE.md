# SANKET V1.10.7 — Case-memory design system and frontend information architecture

Date: 20 September 2026

## Scope

This milestone applies the audited case-memory frontend design system supplied by the team. It is a presentation-layer refactor only: routes, API contracts, state stores, graph/map/workflow engines, evidence logic and backend business rules remain unchanged.

## Design system

- Dark graphite surfaces with a single desaturated-teal brand accent.
- Status colours are reserved for success, warning, danger and informational states.
- Borders and spacing replace glows, gradients and HUD decoration as the primary hierarchy tools.
- Inter is used for UI copy. JetBrains Mono remains reserved for identifiers, hashes and technical values.
- Minimum interface text target is 12px.
- Sentence-case buttons and navigation labels replace pervasive all-caps microcopy.
- WCAG-oriented focus states and reduced-motion support are included in the frontend layer.

## Information architecture

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

The app should feel like one case memory with different views over the same evidence, not a collection of independent dashboards.

## Shared shell

- 56px header.
- 232px sidebar on desktop, collapsible to a 64px rail at narrower widths.
- A compact source-scope bar is rendered only on document-scoped pages: Ledger, Documents and Evidence Review.
- A single H1 page header is provided by the app shell; redundant child page introductions are suppressed.
- Ingestion remains the primary global action.
- Navigation badges now distinguish informational counts from review attention counts.

## Evidence thread pattern

The frontend uses compact source chips and confidence indicators so that source linkage becomes a visual signature instead of a large repeated panel.

## Page treatments

### Overview

- Four compact KPIs: source documents, remembered entities, timeline events and open conflicts.
- Cross-document conflicts are counted separately from document-level quality flags.
- Case summary, attention queue, identifiers, remembered entities, chronology and seized assets remain available as source-linked cards.
- Metadata-only cryptographic dates/hashes are excluded from the investigative timeline presentation; they remain available in evidence views.

### Entity network

- Network remains a full-bleed investigation surface inside the workspace.
- Existing graph engine and V1.10.6 evidence-linked composition are preserved.
- Search, layout, auto-arrange, show-isolates, zoom and fit controls remain available.
- Node/source inspection remains in the existing inspector drawer.

### Locations

- Existing OpenStreetMap-backed MapLibre implementation is retained.
- Location list remains docked beside the map rather than overlaying it.

### Workflow

- Existing workflow engine remains unchanged in this milestone.
- Legacy HUD styling is visually normalized through the global design layer; workflow optimization is deferred to the next milestone.

### Ledger

- Field names display as readable labels with raw keys secondary.
- Empty values are shown as “Not found” rather than pretending an empty field is a successful extraction.
- Confidence uses a thin indicator with warning/danger states instead of identical green pills.
- Sources are compact evidence-thread chips and row actions appear on hover/focus.
- CSV export and source inspection remain functional.

### Documents

- Existing two-pane Document Inspector is normalized into a source-first workspace.
- Processed/original image switching, bounding boxes, hash copying, Graph Contract export, validation flags, rule checks, field filtering and audit trail remain functional.

### Evidence review

- Contradictions use a neutral surface with a 3px danger edge.
- Provenance details remain master-detail and source-linked.
- Technical identifiers stay secondary/collapsible in visual hierarchy.

### Quality & analytics

- Extraction coverage now uses confidence as the main visual measure with an 85% threshold marker.
- Documents are sorted by confidence, with field and flag counts as supporting context.
- Role mix uses compact rows/grid treatment instead of an oversized categorical visualization.

## Tooltip / discoverability layer

Existing `title` and `data-tooltip` help text is normalized and expanded across navigation, ingestion, network controls, evidence inspection, location controls, workflow controls, export actions and review interactions.

## Functional preservation

The following remain intact:

- multi-document ingestion;
- sample dataset loading;
- asynchronous factual ingestion progress;
- Clarity Graph Contract integration;
- Entity Resolution;
- Evidence Graph;
- Temporal Engine;
- Graph Analytics;
- Anomaly Engine;
- Investigation Workflow Engine;
- Evidence Provenance;
- Contradiction Engine;
- Cytoscape network;
- MapLibre locations;
- document inspection and bounding boxes;
- CSV and Graph Contract exports.

## Known data-quality findings intentionally surfaced, not silently corrected

- A source observation may carry conflicting roles.
- Source identifiers may disagree across documents.
- VLM confidence can be over-uniform.
- Different UI/API counts must be reconciled as a later data-contract task.

These are evidence-quality concerns, not reasons to invent cleaner values in the UI.

## Next milestone

**V1.10.8 — Investigation Workflow Optimization**

Focus: turn the workflow workspace into the clearest, most usable investigative procedure builder while preserving the existing deterministic execution engine and evidence traceability.
