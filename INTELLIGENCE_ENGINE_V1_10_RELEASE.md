# V1.10 RELEASE NOTES — Evidence Provenance & Contradiction Review

Status: **Implementation complete; local user acceptance required**

## Goal

Turn evidence traceability and cross-document conflict detection into first-class deterministic capabilities rather than UI-only annotations.

## Added

- `clarity/intelligence/provenance.py`
  - field-level provenance
  - graph-node and relationship provenance
  - analytical finding lineage
  - compact provenance summaries
- `clarity/intelligence/contradiction_engine.py`
  - conservative semantic field grouping
  - identifier mismatch detection
  - field-value conflict detection
  - source observation preservation
- `GET /api/v1/cases/{case_id}/evidence-review`
- workflow execution response now includes evidence-review data
- Evidence Review node now returns explicit source evidence references
- Evidence Review frontend workspace
- navigation entry for provenance/conflict inspection
- deterministic unit/API tests for the new layer

## Safety / semantics

Contradictions are review items, not corrections. The system does not rewrite source observations, declare guilt, or make legal determinations. Analytical findings remain distinct from observed source facts.

## Acceptance gate

Run the full Python test suite and frontend production build on the development machine. No V1.10 release is considered accepted until the user's environment confirms the results.
