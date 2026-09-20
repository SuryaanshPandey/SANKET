# SANKET V1.10.6 — Evidence-linked Network Composition

## Purpose

Fix the Entity Network so it visualizes the actual case memory instead of displaying dozens of unrelated extracted field objects.

## Changes

- Added source-document nodes to the network.
- Added explicit `OBSERVED_IN` evidence connections from semantic entities/events to their source documents.
- Kept direct Graph Contract relationships as semantic edges.
- Filtered field-like/metadata-heavy objects out of the default investigation network.
- Preserved all such fields in Evidence Ledger and Document Inspector.
- Default layout now operates on a connected evidence spine and then places truly unconnected observations separately when requested.
- Added document-node styling and a legend entry.
- Network summary now reports evidence connections rather than implying every extracted field is a relationship.
- Updated master project context and release documentation.

## Acceptance

- Network must show a readable connected evidence structure when source documents exist.
- Direct relationships and source-evidence links must be visually distinguishable.
- Search, hover, selection, zoom, fit, layout, source inspection and isolate toggle remain functional.
- Evidence Ledger remains the complete field-level record.
