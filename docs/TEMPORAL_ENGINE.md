# Temporal Intelligence Engine

## Purpose

The temporal engine is the first time-aware layer above the Evidence Graph. It provides deterministic queries and snapshots without assigning dates to evidence that does not explicitly contain temporal metadata.

## Supported temporal representations

- `timestamp` / `datetime` / `occurred_at`: point-in-time event
- `timestamp_start` + `timestamp_end`: interval event
- `start_time` / `end_time`: explicit interval metadata

ISO-8601 values are supported. Naive datetimes use the configured timezone (`Asia/Kolkata` by default). Offset-aware datetimes are normalized to UTC for comparisons.

## Query semantics

All windows are inclusive at both ends. Intervals overlap when:

`event.start <= window.end AND event.end >= window.start`

An undated event is not assigned to a time window. The engine emits a `UNDATED_EVENT` warning instead.

## Snapshot semantics

A snapshot contains:

- dated events overlapping the window;
- entities participating in those events;
- explicit temporal relationships overlapping the window;
- entity↔event contextual edges for selected events.

Direct entity↔entity edges with no temporal metadata are not assigned to a time window. They remain available in the base Evidence Graph.

## Why this design

The PS needs temporal and pattern analysis, but the system must not invent chronology. A temporal engine should prefer a visible `unknown` state over a false date.

## Current API

- `events_in_window(...)`
- `active_entity_ids(...)`
- `activity_buckets(...)`
- `snapshot(...)`
- `network_at(...)`
- `compare_snapshots(...)`
- `interval_for_node(...)`
- `interval_for_edge(...)`

These APIs are deterministic and suitable for later Neo4j persistence, anomaly detection, bridge detection and investigation-workflow nodes.
