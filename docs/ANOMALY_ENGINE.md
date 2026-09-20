# V1.6 — Suspicious Pattern / Anomaly Engine

The anomaly layer sits above the V1.5 Evidence Graph, Temporal Engine and Graph Analytics Engine.

```text
Evidence Graph
     +
Temporal Intelligence
     +
Graph Analytics
        |
        v
Suspicious Pattern / Anomaly Engine
        |
        +--> Activity spikes
        +--> Novel relationships
        +--> Interaction bursts
        +--> New cross-community activity
        +--> Structural + activity convergence
```

## Design principles

1. Findings describe unusual patterns or investigative leads, not criminality or guilt.
2. Every time-sensitive finding uses explicit timestamps/intervals. Undated events are not placed into a window.
3. The default baseline is the equal-duration period immediately preceding the target window.
4. Findings preserve supporting event IDs and relationship IDs wherever available.
5. Scores are analytical anomaly/priority scores, not probabilities of guilt.
6. The engine is deterministic for a fixed graph, configuration and windows.
7. The graph itself is not mutated by analysis.

## Detectable patterns

### ACTIVITY_SPIKE
Compares an entity's busiest target-window activity bucket with the baseline bucket distribution.

### NOVEL_RELATIONSHIP
Finds an interaction pair with time-stamped evidence in the target window and no time-stamped interaction evidence in the baseline window.

### INTERACTION_BURST
Detects an unusually dense burst between an entity pair in one target bucket relative to baseline.

### CROSS_COMMUNITY_ACTIVITY
Detects a new target-window interaction connecting separate baseline connected components. The components are derived only from baseline activity, so a new connection cannot erase the distinction that made it notable.

### STRUCTURAL_ACTIVITY_CONVERGENCE
Combines a strong betweenness role from graph analytics with a target-window activity deviation. This is an investigative lead, not a criminality score.

## Why deterministic baselines first

The initial MVP intentionally does not train a black-box anomaly model. A transparent baseline makes each finding auditable and gives us a reference for any future learned model.

A later ML model may be added only if it improves validated metrics and its output can remain evidence-traceable.

## Evaluation plan

The scenario generator will eventually plant known patterns and hide their labels from the engine. We can then measure:

- precision / recall for planted anomalies;
- Precision@K for ranked investigative leads;
- false-positive rate;
- detection latency;
- evidence-traceability completeness.

These are evaluation targets, not achieved results until experiments are run.
