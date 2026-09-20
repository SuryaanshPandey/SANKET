# Graph Analytics Engine — V1.5

## Purpose

V1.5 is the first analytical layer for PS #13. It consumes the existing `EvidenceGraph` and produces deterministic network-intelligence outputs for:

- key-individual / network-influence analysis;
- community discovery;
- shortest-path investigation;
- bridge/intermediary candidate detection.

The layer does not decide criminality, guilt, threat, or legal responsibility.

## Analytical graph projection

The source `EvidenceGraph` contains entity nodes, event nodes, and evidence-aware relationships. Human network metrics are computed on an entity-only undirected projection.

Two entities become adjacent when:

1. an evidence relationship directly connects them; or
2. an event node explicitly names both entities through `source_entity_id` and `target_entity_id`, and event interaction projection is enabled.

No link is created from document order, missing information, or free-form speculation.

## Metrics

For each eligible entity:

- degree;
- weighted degree using relationship/event confidence;
- degree centrality;
- betweenness centrality using Brandes' shortest-path algorithm;
- closeness centrality on the reachable graph;
- PageRank using deterministic fixed-point iteration.

## Key-individual ranking

The default composite network-influence score is:

```text
25% degree centrality
35% betweenness centrality
15% closeness centrality
25% PageRank
```

These weights are initial engineering defaults, not validated scientific weights. They must be benchmarked before being presented as a final model.

The output language is intentionally role-oriented:

- key network role;
- high connectivity;
- bridge/intermediary lead;
- investigative lead.

It must never describe a person as a criminal based only on this score.

## Communities

V1.5 uses deterministic label propagation with stable tie-breaking. Communities are analytical clusters, not legal or behavioral classifications.

## Bridge/intermediary detection

A bridge candidate is an eligible entity whose removal separates its eligible neighbors into at least two local connected components. This articulation-style test avoids depending on a single global community detector. The bridge score combines:

```text
65% betweenness centrality
35% cross-community ratio (the candidate's eligible neighbors are structurally separated after the candidate is removed)
```

The output retains supporting relationship/event IDs so the UI can trace the lead back to evidence.

## Paths

Shortest paths are computed as unweighted undirected paths over the analytical entity projection. The result returns the entity path plus supporting relationship/event IDs.

## Determinism and safety

- Stable sorting is used for nodes, neighbors, communities and rankings.
- The evidence graph is never mutated.
- Isolated entities remain visible.
- An empty/unreachable path is represented explicitly rather than inferred.
- Scores are analytical scores, not probabilities of guilt.

## Next layer

V1.5 outputs are the input to the future suspicious-pattern/anomaly engine and investigation workflow engine.
