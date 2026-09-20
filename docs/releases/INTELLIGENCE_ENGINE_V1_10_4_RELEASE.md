# SANKET V1.10.5 Release Notes

## Release title

**Map, Graph Layout & Contextual Help**

## Product intent

The case-memory frontend should make relationships and locations immediately understandable without turning the interface into a dense technical dashboard. This release improves the two spatial surfaces most visible in investigation work: the entity network and the location map.

## Changes

- Entity network auto-arrangement is tuned for current graph connections and separated components.
- Isolated entity labels are hidden by default to reduce overlap; full labels are shown on hover, selection, and search.
- Relationship labels remain quiet until a relationship is hovered, keeping dense graphs readable.
- An explicit **Auto Arrange** control is available next to layout selection.
- Hovering a node or relationship shows a concise explanation, confidence, connection count/source context, and a click-to-inspect hint.
- Locations now use the official OpenStreetMap standard raster tile endpoint and visible OSM attribution.
- Case-location markers and the location list both expose clear hover descriptions.
- Navigation, evidence, inspection, review, analytics and workflow controls expose descriptive hover help.

## OSM usage note

The frontend uses `https://tile.openstreetmap.org/{z}/{x}/{y}.png` for interactive viewing and keeps visible attribution as required by the OpenStreetMap Foundation tile usage policy. No tile prefetch/download feature is implemented.

## Non-goals

- No backend intelligence changes.
- No VLM changes.
- No change to case-memory data contracts.
- No removal of any existing workspace feature.


# SANKET V1.10.4 Release Notes

## Release title

**Case Memory Frontend Redesign**

## Product decision

SANKET is now explicitly designed as a **case-memory and investigation workspace** rather than a tactical dashboard collection.

The product's job is to collect scattered information, keep the important relationships and chronology together, and make every observation/finding traceable back to source evidence.

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

## What was removed or demoted

- repeated "sovereign / tactical / radar" branding;
- duplicated case/document status messaging;
- decorative KPI-only panels;
- statutory/rule visualizations as the primary analytics experience;
- raw JSON as the default representation of workflow node outputs;
- hash/checksum values as timeline events;
- dataset selector occupying permanent primary-header space in the product model;
- controls whose only purpose was visual signalling.

The underlying data and analytical checks remain available through the relevant evidence/review workspaces.

## What was made more functional

- entity search in the network workspace;
- source-document navigation from entity inspection;
- direct ledger-row navigation into the document inspector;
- compact but persistent ingestion access;
- location fit-to-case control;
- evidence-review source navigation;
- selected-node workflow output inspection.

## Evidence handling position

Observed data is kept distinct from inference. Contradictions are surfaced instead of silently corrected. Source observations remain inspectable.

## Non-goals

- no backend intelligence rewrite;
- no cloud VLM migration;
- no automatic guilt or criminality decision;
- no removal of provenance or review functionality.

## Additional functional corrections in the final V1.10.4 package

- The workspace restores the active case dossier after a frontend/backend restart when persisted case data exists.
- The Entity Network prefers real case-level Graph Contract entities, events, and relationship edges instead of connecting every entity only to a synthetic case hub.
- The Entity Network falls back to the reconciled case memory when the Graph Contract is incomplete, and it clearly states that limitation in the UI.
- Timeline-oriented document integrity values remain evidence metadata rather than case events.

