# SANKET — KAYA Submission Manifest

## Project

**Title:** SANKET — AI-Native Investigation Workspace
**Problem Statement:** KAYA Software Hackathon PS #13 — AI-Powered Criminal Network Analysis System
**Release:** V1.10.7
**Validated Intelligence Baseline:** V1.10.6 + C4

## Submission Links

| Item                     | Value                                     |
| ------------------------ | ----------------------------------------- |
| Public GitHub repository | https://github.com/SuryaanshPandey/SANKET |
| Demo video (≤ 5 min)     | `TBD`                                     |
| Presentation PDF         | `TBD`                                     |
| Hosted demo              | `N/A`                                     |

## Submission Description

SANKET is an investigator-facing intelligence workspace that turns fragmented case evidence into a connected, traceable and time-aware case memory.

It combines document extraction, Graph Contract normalization, entity resolution, an evidence graph, temporal intelligence, graph analytics, anomaly and pattern analysis, evidence review, and an investigator-controlled workflow engine.

A constrained AI investigation planner converts natural-language questions into validated, allow-listed workflows. The deterministic workflow engine executes those workflows and produces evidence-backed analytical leads, provenance information, uncertainty notes and structured reports.

The system is designed around one principle:

> Important analytical conclusions should remain traceable to the evidence from which they were derived.

## PS #13 Capability Coverage

SANKET provides:

* multi-source evidence ingestion;
* structured and unstructured information processing;
* entity extraction and resolution;
* relationship and network analysis;
* temporal analysis;
* key-individual and bridge analysis;
* anomaly and unusual-activity detection;
* investigator-facing network, timeline, location and evidence views;
* configurable investigation workflows;
* AI-assisted workflow planning;
* evidence provenance;
* contradiction and uncertainty handling;
* human verification;
* evidence-backed reporting.

## Security Position

SANKET is an **investigative decision-support prototype**.

It does not:

* determine legal guilt;
* make autonomous arrest or enforcement decisions;
* silently resolve conflicting evidence;
* treat AI-generated hypotheses as established facts;
* permit unrestricted AI execution of arbitrary code, SQL or system commands.

AI-generated workflow plans are schema-validated and allow-listed before deterministic execution.

## Data Position

Demonstration and benchmark scenarios use controlled synthetic and/or public data.

The repository does not claim access to confidential law-enforcement datasets.

Police-style demonstration documents and other sample investigation material should be interpreted as project demonstration assets unless explicitly identified otherwise.

Sample-data licensing and attribution are documented in:

```text
samples/LICENSES.md
```

## Validation Evidence

The repository has been validated using the following gates:

### Backend regression

```powershell
pytest -q
```

Validated baseline:

```text
149 tests passed
```

### Deterministic final acceptance

```powershell
python scripts/final_acceptance.py
```

Validated result:

```text
8 / 8 checks passed
```

The acceptance scenario validates temporal analysis, key-individual analysis, bridge analysis, anomaly coverage, workflow validation, workflow execution, evidence-backed reporting and reproducibility.

### Frontend production build

```powershell
cd frontend
npm ci
npm run build
```

### Manual end-to-end validation

Before final submission, the complete investigator workflow should be exercised from ingestion through reporting.

## Recommended Demo Flow

The demonstration should communicate one continuous investigation:

```text
Fragmented Evidence
        ↓
Connected Case Memory
        ↓
Entity Network + Timeline
        ↓
AI-Assisted Workflow
        ↓
Deterministic Execution
        ↓
Evidence Review
        ↓
Evidence-backed Report
```

The key capabilities to demonstrate are:

1. Case ingestion and memory formation
2. Entity Network exploration
3. Temporal / location analysis
4. Investigation Workflow
5. AI plan review and application
6. Evidence and provenance inspection
7. Contradiction / human-review flow
8. Evidence-backed report generation

## Submission Checklist

Before submitting:

* [ ] Public GitHub repository is accessible
* [ ] README accurately describes V1.10.7
* [ ] Demo video is no longer than the required submission limit
* [ ] Demo video shows a complete working investigation flow
* [ ] Presentation is consistent with the repository
* [ ] No secrets or runtime databases are committed
* [ ] Sample-data licensing is documented
* [ ] Backend tests pass
* [ ] Deterministic final acceptance passes
* [ ] Frontend production build passes
* [ ] Manual end-to-end demo has been completed
* [ ] Submission links have been filled
* [ ] KAYA participant dashboard requirements have been rechecked immediately before submission

## Repository Documentation

Key technical documentation is available under:

```text
docs/
```

including:

```text
docs/INVESTIGATION_WORKFLOW_ENGINE.md
docs/EVIDENCE_GRAPH.md
docs/ENTITY_RESOLUTION.md
docs/TEMPORAL_ENGINE.md
docs/GRAPH_ANALYTICS.md
docs/FINALIZATION_AND_DEMO.md
```

Historical release notes are preserved under:

```text
docs/releases/
```
