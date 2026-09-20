# SANKET — AI-Native Investigation Workspace

> **Connect fragmented evidence into an auditable, time-aware case memory.**

SANKET is an investigator-facing intelligence workspace for **KAYA Software Hackathon — Problem Statement #13: AI-Powered Criminal Network Analysis System**.

It turns fragmented documents and structured evidence into a connected case model that investigators can **explore, analyze, verify, and report** without losing source provenance or uncertainty.

**Current release:** `V1.10.7`
**Validated intelligence baseline:** `V1.10.6 + C4`

---

## The Problem

Investigative information is rarely contained in one place.

Relevant facts may be distributed across reports, statements, seizure records, communications, locations, identifiers, transactions, and other evidence.

The difficult problem is therefore not only:

> **“What information is inside this document?”**

It is also:

> **“What belongs together, what happened when, what is connected, what is unusual, and which conclusions can actually be traced back to evidence?”**

SANKET is designed around that second problem.

---

## What SANKET Does

```text
Documents / Evidence
        │
        ▼
Clarity Extraction
        │
        ▼
Graph Contract
        │
        ▼
Entity Resolution
        │
        ▼
Evidence Graph
        │
        ├──────────────► Timeline / Temporal Analysis
        │
        ├──────────────► Graph Analytics
        │
        └──────────────► Anomaly / Pattern Analysis
                              │
                              ▼
                    Investigation Workflow
                              │
                              ▼
                       Evidence Review
                              │
                              ▼
                    Evidence-backed Report
```

The result is a persistent **case memory** rather than a collection of disconnected dashboards.

---

## Core Capabilities

### 1. Case Memory

SANKET maintains a unified logical model of:

* source documents
* extracted fields
* people
* locations
* vehicles
* phones
* accounts
* organizations
* events
* dates
* relationships
* evidence references
* contradictions
* confidence and review state
* workflow executions
* analytical findings

The same underlying case memory can be explored through different investigator-facing views.

### 2. Entity Network

The Entity Network helps investigators understand:

* who is connected to whom;
* which entities act as structural bridges;
* how relationships are distributed;
* which source documents support those relationships;
* how the case structure changes when evidence is filtered.

The graph distinguishes semantic relationships from evidence provenance links.

### 3. Temporal Intelligence

The timeline and temporal analysis layer help answer:

* what happened during a target period;
* which entities were active;
* whether activity clusters in time;
* whether relationships or interactions are newly appearing;
* how events relate to the broader case chronology.

### 4. Anomaly and Pattern Analysis

The deterministic intelligence layer can identify analytical signals such as:

* activity spikes;
* interaction bursts;
* novel relationships;
* cross-community activity;
* structural activity convergence;
* bridge candidates.

These are presented as **investigative leads**, not conclusions of guilt.

### 5. Investigation Workflow

Investigators can compose and execute an explicit analytical workflow containing allow-listed operations such as:

* temporal filtering;
* network expansion;
* graph analytics;
* key-individual analysis;
* community detection;
* bridge analysis;
* anomaly detection;
* shortest path analysis;
* evidence review;
* reporting.

The workflow is inspectable and reproducible.

### 6. AI Investigation Planner

Natural-language investigation questions can be converted into a structured workflow plan.

```text
Investigator Question
        │
        ▼
AI Planner
        │
        ▼
Workflow Schema Validation
        │
        ▼
Allow-list Validation
        │
        ▼
Deterministic Execution
        │
        ▼
Evidence-backed Results
```

The model does **not** receive unrestricted execution access.

The planner cannot directly execute arbitrary:

* SQL;
* shell commands;
* filesystem operations;
* arbitrary code;
* database mutations.

AI is used as a constrained orchestration layer; the deterministic investigation engine remains responsible for execution.

---

## Evidence Provenance

SANKET is designed so that important findings remain traceable to their supporting evidence.

A provenance chain may include:

```text
Finding
  ↓
Analytical result
  ↓
Entity / event / relationship
  ↓
Extracted observation
  ↓
Source document
  ↓
Page / bounding box / text span
  ↓
SHA-256 document hash
```

Where available, investigators can inspect:

* source document;
* page;
* bounding box;
* extracted value;
* confidence;
* document hash;
* provenance links;
* contradictory observations.

This makes the analytical output auditable rather than opaque.

---

## Epistemic Separation

SANKET explicitly separates different kinds of statements:

```text
OBSERVED
CORRELATED
INFERRED
HYPOTHESIS
CONFLICT / REVIEW_REQUIRED
```

An inferred relationship is not silently promoted into an observed fact.

Contradictory source observations are preserved for review rather than automatically overwritten.

---

## KAYA PS #13 Coverage

SANKET is designed around the capabilities specified by the KAYA PS #13 problem statement.

| PS #13 Capability                  | SANKET Implementation                                                          |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| Multiple information sources       | Document ingestion, structured records, scenario data and evidence objects     |
| Structured + unstructured analysis | Clarity extraction + Graph Contract + structured case model                    |
| Entity extraction                  | People, locations, vehicles, phones, organizations and extensible entity types |
| Relationship mapping               | Evidence Graph + interactive network exploration                               |
| Key individual analysis            | Graph analytics and structural importance analysis                             |
| Suspicious / unusual activity      | Deterministic anomaly and pattern analysis                                     |
| Investigator-facing visualization  | Network, timeline, locations, evidence and workflow surfaces                   |
| Analytical workflows               | Allow-listed Investigation Workflow Engine                                     |
| Traceable outputs                  | Evidence and provenance chain                                                  |
| Human review                       | Contradiction review and field verification                                    |
| Reporting                          | Evidence-backed deterministic investigation report                             |

---

## System Architecture

```text
┌───────────────────────────────┐
│      Clarity Extraction       │
│  Document understanding/VLM   │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│     Graph Contract Adapter    │
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│       Entity Resolution       │
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│        Evidence Graph         │
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│       Temporal Engine         │
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│       Graph Analytics         │
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│   Anomaly / Pattern Engine    │
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│ Investigation Workflow Engine │
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│ Evidence Review / Reporting   │
└───────────────────────────────┘
```

The frontend presents these capabilities as one investigation workspace rather than exposing every subsystem as a separate engineering tool.

---

## Workspace Model

The interface follows a simple investigation flow:

```text
CASE
  Overview

EXPLORE
  Entity Network
  Locations

INVESTIGATE
  Workflow

EVIDENCE
  Ledger
  Documents

REVIEW
  Evidence Review
  Quality & Analytics
```

Each view operates on the same underlying case memory.

---

## Ingestion Behaviour

Document ingestion is asynchronous.

The frontend receives a batch identifier and polls confirmed backend status.

Progress is based on **backend-confirmed stages**, not simulated elapsed time.

The system therefore avoids presenting artificial percentage completion while a long-running extraction operation is still executing.

---

## Human Verification

Extracted information can be reviewed and corrected without destroying the original extraction.

A correction preserves the distinction between:

```text
Original extracted value
        ↓
Human correction
        ↓
Reviewer
        ↓
Review timestamp
```

The original observation remains available for auditability.

---

## Deterministic Investigation Engine

SANKET separates planning from execution.

A workflow is validated before execution and is composed from explicit analysis nodes.

The execution layer provides:

* typed nodes;
* workflow validation;
* DAG execution;
* dependency validation;
* explicit failure policies;
* deterministic workflow definitions;
* reproducible execution identifiers;
* structured analytical results;
* provenance-aware report generation.

---

## Validation

The current frozen backend baseline has been validated with:

```text
149 tests passing
```

The deterministic final-acceptance scenario validates:

```text
8 / 8 checks passed
```

The acceptance scenario covers:

* temporal scoping;
* key-individual analysis;
* primary bridge analysis;
* anomaly coverage;
* workflow validation;
* workflow execution;
* evidence-backed reporting;
* reproducible execution identifiers.

The frontend production build also completes successfully in the validated environment.

Run the deterministic acceptance harness from the repository root:

```powershell
python scripts/final_acceptance.py
```

See:

* `docs/FINALIZATION_AND_DEMO.md`
* `docs/VERIFY_V1_10_7.md`
* `INTELLIGENCE_ENGINE_VERSION.md`

for validation and release context.

---

## Technology Stack

### Backend

* Python 3.11+
* FastAPI
* SQLAlchemy
* Alembic
* SQLite / PostgreSQL-compatible persistence
* NetworkX
* Pydantic
* Clarity extraction pipeline

### Document / VLM Layer

* Qwen2.5-VL 3B
* Ollama
* OpenCV
* Pillow
* Schema-constrained extraction

### Frontend

* Next.js 16
* React 19
* TypeScript
* Tailwind CSS
* Cytoscape.js
* MapLibre GL
* TanStack Table
* TanStack Virtual
* ECharts
* Zustand
* Lucide

---

## Local Setup

### Backend

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project and development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Configure the environment using:

```text
.env.example
```

The repository's backend and finalization documentation contain the project-specific service startup and environment details.

### Frontend

```powershell
cd frontend
npm install
```

The frontend uses the local backend through the configured `/api` rewrite.

---

## Deterministic Acceptance

From the repository root:

```powershell
python scripts/final_acceptance.py
```

The acceptance harness uses a controlled synthetic scenario for repeatable software-behaviour validation.

It is **not** a real-world law-enforcement accuracy benchmark.

---

## Responsible Use

SANKET is an **investigative decision-support prototype**.

It does not:

* determine legal guilt;
* make automated arrest decisions;
* make autonomous enforcement decisions;
* silently resolve conflicting evidence;
* treat hypotheses as established facts;
* provide an unrestricted AI execution environment;
* claim access to confidential law-enforcement datasets that the project does not possess.

Analytical outputs should be reviewed against their underlying evidence by qualified human users.

---

## Data Position

The repository uses controlled project data and synthetic/public material for demonstration and software validation.

Synthetic scenarios are used where controlled ground truth is required for deterministic testing.

Sample and source-data information is documented in:

```text
samples/LICENSES.md
```

No real confidential law-enforcement dataset should be inferred from the presence of police-style demonstration material.

---

## Repository Structure

```text
SANKET/
│
├── clarity/                         # Backend / intelligence engine
├── frontend/                        # Next.js investigation workspace
├── migrations/                      # Database migrations
├── scripts/                         # Validation and operational scripts
├── tests/                           # Automated test suite
├── examples/                        # Example configurations / workflows
├── samples/                         # Demonstration data and sample licensing
│
├── docs/
│   ├── releases/                   # Historical release notes
│   ├── ANOMALY_ENGINE.md
│   ├── ENTITY_RESOLUTION.md
│   ├── EVIDENCE_GRAPH.md
│   ├── FINALIZATION_AND_DEMO.md
│   ├── GRAPH_ANALYTICS.md
│   ├── GRAPH_CONTRACT_ADAPTER.md
│   ├── INVESTIGATION_WORKFLOW_ENGINE.md
│   └── TEMPORAL_ENGINE.md
│
├── submission/
│   └── SUBMISSION_MANIFEST.md
│
├── .env.example
├── INTELLIGENCE_ENGINE_VERSION.md
├── Modelfile
├── alembic.ini
├── pyproject.toml
└── README.md
```

---

## Documentation

### Architecture

See the technical documentation in `docs/` for the system's major intelligence layers.

### Workflow Engine

See:

```text
docs/INVESTIGATION_WORKFLOW_ENGINE.md
```

### Evidence Graph

See:

```text
docs/EVIDENCE_GRAPH.md
```

### Entity Resolution

See:

```text
docs/ENTITY_RESOLUTION.md
```

### Temporal Intelligence

See:

```text
docs/TEMPORAL_ENGINE.md
```

### Graph Analytics

See:

```text
docs/GRAPH_ANALYTICS.md
```

### Finalization and Demo

See:

```text
docs/FINALIZATION_AND_DEMO.md
```

Historical engineering releases are preserved under:

```text
docs/releases/
```

---

## Five-Minute Demo Story

The recommended demo follows one continuous investigation:

```text
Scattered Evidence
       ↓
Connected Case Memory
       ↓
Entity Network + Timeline
       ↓
AI-Assisted Investigation Workflow
       ↓
Evidence Review
       ↓
Evidence-backed Report
```

The strongest product story is not the number of screens.

It is the transition from:

> **fragmented evidence**

to:

> **connected, traceable investigative understanding.**

---

## Project Status

**Release:** `V1.10.7`

V1.10.7 is the current case-memory presentation and frontend information-architecture release, while the validated intelligence baseline remains `V1.10.6 + C4`.

The repository is maintained as a competition submission and demonstration codebase. Historical release notes remain available under `docs/releases/` for engineering traceability.

---
---

## License

No open-source license has been declared for this repository.
