# SANKET — KAYA Submission Manifest

## Project

**Title:** SANKET — Case Memory & Investigation Workspace  
**Problem Statement:** KAYA Software Hackathon PS #13 — AI-Powered Criminal Network Analysis System  
**Release:** V1.10.6 + C3 Workflow Builder / Planner Reliability

## Links to fill before submission

| Item | Value |
|---|---|
| Public GitHub repository | `TBD` |
| Demo video (≤ 5 min) | `TBD` |
| Presentation PDF (≤ 10 slides) | `TBD` |
| Hosted demo | `TBD / N/A` |

## Submission description

SANKET is an AI-assisted investigation workspace that turns fragmented case evidence into a connected, traceable and time-aware case memory. It combines document extraction output, entity resolution, an evidence graph, temporal intelligence, graph analytics, anomaly/pattern detection and an investigator-controlled workflow canvas. A constrained AI planner converts natural-language investigation questions into validated workflows; the deterministic engine executes those workflows and returns evidence-backed analytical leads. Provenance, contradictions, uncertainty and human verification remain visible throughout the investigation.

## Security position

SANKET is an investigative decision-support prototype. It does not make automated guilt determinations or enforcement decisions. AI-generated workflow plans are schema-validated and allow-listed before execution. Evidence conflicts are preserved rather than silently reconciled.

## Data position

Demo and benchmark scenarios are synthetic or controlled public-data validations. They must not be described as access to confidential law-enforcement datasets.

## Final acceptance evidence

- Backend regression suite: run locally before submission.
- Target-machine preflight: `python scripts/target_machine_preflight.py`
- Deterministic acceptance: `python scripts/final_acceptance.py`
- Frontend production build: `npm ci` then `npm run build`
- Manual end-to-end case test: complete before recording.

## KAYA online submission note

KAYA's current Software Hackathon page states that the online submission requires a public GitHub repository and a demo video of at most five minutes. The page also lists a 24 September 2026 submission deadline and describes innovation, technical depth/execution, security and real-world impact as judging dimensions.

Reference: https://kaya.azmth.in/events/hackathon/


## C3 delivery note

The final workflow demo should visibly include direct output-pin → input-pin connection, connection selection/deletion, AI planner → review → Apply to Canvas, workflow validation, deterministic execution and evidence-backed report export.
