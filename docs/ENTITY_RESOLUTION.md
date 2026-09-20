# Entity Resolution Core

This module is the first intelligence layer after the Clarity Graph Contract Adapter.

## Input

`CanonicalEntity[]` from `clarity.intelligence.GraphContractAdapter`.

## Output

- `EntityMatchCandidate[]` for explainable pairwise decisions.
- `ResolvedEntityCluster[]` for high-confidence automatic merges.
- `entity_to_cluster` mapping.
- unresolved IDs for entities that have no confirmed cluster.

## Safety rules

- Only compatible entity types are compared.
- Strong identifier contradictions block automatic confirmation.
- Only high-confidence matches are automatically clustered.
- Probable/possible matches remain reviewable candidates.
- Every candidate exposes its signals and reasons.
- Original IDs and source document IDs are preserved in confirmed clusters.
- The resolver makes no claims about guilt or criminality.
- The same input/configuration produces deterministic output.

## Current signal model

The initial score combines only available signals:

- normalized-name similarity
- strong identifier overlap
- overlapping attributes
- role compatibility
- contradiction penalty for conflicting strong identifiers

The values are configurable implementation parameters. They are not validated scientific probabilities and must be benchmarked against ground-truth scenarios later.

## Why this is separate from graph analytics

Entity resolution decides whether multiple extracted records may refer to the same real-world entity. It must happen before network analysis so that duplicate records do not distort degree, betweenness, community structure or bridge detection.

## Next integration gate

A real Clarity `/graph-contract` response must still be run through the adapter and resolver before the downstream schema is considered production-integrated.
