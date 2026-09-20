# V1.5 Release Candidate — Graph Analytics Engine

This release adds the deterministic graph analytics layer on top of the verified V1.4 stack.

## Included

- Graph Contract Adapter
- Entity Resolution
- Evidence Graph
- Temporal Intelligence
- Graph Analytics
- Tests and design/verification documentation

## Graph analytics capabilities

- degree and weighted degree
- degree centrality
- betweenness centrality
- closeness centrality
- deterministic PageRank
- deterministic label-propagation communities
- key-individual/network-influence ranking
- shortest paths
- articulation-style bridge/intermediary detection
- supporting relationship/event provenance IDs

## Validation

The new dedicated test suite contains 10 tests.

In the development environment used to prepare this ZIP, the five intelligence suites were exercised together and 56 tests passed. The environment did not have the repository's `openai` runtime dependency installed, so the validation run used a temporary local import stub for the existing VLM client; no project file was changed for that stub. On the target laptop, install the project's normal dependencies and run the verification commands in `docs/VERIFY_V1_5.md`.

Do not treat V1.5 as the next `perfect` backup until the user has successfully run the verification suite locally.
