# SANKET — V1.10.6 + C2 Finalization / Delivery Hardening

## Scope

C2 is the final engineering hardening milestone before hackathon delivery. The frozen V1.10.6 interaction model and approved light-theme presentation remain unchanged.

## Included

### Acceptance harness

`scripts/final_acceptance.py` validates, without external network access or a live VLM:

- temporal scoping;
- key-individual analysis;
- structural bridge analysis;
- explainable anomaly detection;
- workflow schema validation;
- workflow execution;
- evidence-backed report generation;
- deterministic execution-ID reproducibility.

Result of the release workspace run: **8/8 checks passed**.

### Delivery documentation

- `docs/FINALIZATION_AND_DEMO.md`
- `submission/SUBMISSION_MANIFEST.md`
- `artifacts/final_acceptance.json`
- `artifacts/final_acceptance.md`
- `artifacts/backend_regression.txt`
- `artifacts/frontend_parser_check.txt`

## Regression state

- Backend regression suite: **148 passed**.
- TypeScript/TSX parser check: **PASS**.
- Global CSS brace balance: **PASS**.

The target machine must still run the real frontend production build because this release workspace does not contain `frontend/node_modules` and the environment cannot be relied on for npm package installation.

## Completion gate

The product is submission-ready only after the target machine confirms:

1. `python -m pytest -q`
2. `python scripts/final_acceptance.py`
3. `cd frontend; npm ci; npm run build`
4. fresh-case ingestion;
5. case-memory restoration;
6. AI planner → review → apply → validate → execute;
7. evidence traceability and contradiction review;
8. report export;
9. final demo recording and public-link testing.

## Non-negotiable evidence language

Analytical scores are investigative leads, not probabilities of guilt. Source conflicts remain visible. Rule-based document checks are not blanket legal certification. Controlled synthetic benchmark results are not real-world accuracy claims.
