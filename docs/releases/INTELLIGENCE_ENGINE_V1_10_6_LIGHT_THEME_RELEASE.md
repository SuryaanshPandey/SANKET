# Intelligence Engine V1.10.6 Light Theme Visual Variant

Date: 20 September 2026

## Scope

This is a visual-only variant of the frozen SANKET V1.10.6 baseline. The interface is converted from the approved dark workstation theme to a light workstation theme without changing application behaviour.

## Changed visually

- Global page, shell, navigation, toolbars, evidence strip, cards and footers use light surfaces.
- Text, borders and controls are recalibrated for light-background contrast.
- Teal is retained as the primary interaction accent.
- Warning, error and success states retain semantic meaning with light-surface treatments.
- Entity Network Cytoscape nodes, graph labels and graph canvas are recalibrated for light backgrounds.
- Locations markers, map overlays and MapLibre controls use light surfaces while the OpenStreetMap source and attribution remain unchanged.
- Investigation Canvas panels, workflow cards, execution trace and controls use light surfaces while workflow behaviour remains unchanged.
- SANKET emblem presentation uses light fills instead of dark-only fills.

## Explicitly unchanged

- Backend APIs and data contracts
- ingestion and reconciliation behaviour
- Evidence Graph and Graph Contract logic
- provenance and contradiction handling
- network composition rules
- workflow execution and validation
- navigation structure and page information architecture
- source documents and extracted case data

## Acceptance

- Python regression tests pass.
- Next.js production build passes.
- No application behaviour is intentionally modified by this release.
- The visual result remains a replacement for the frozen V1.10.6 baseline.
