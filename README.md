## V1.10.5 — Map, Graph Layout & Contextual Help

The current frontend release keeps the case-memory architecture while improving visualization and discoverability. The entity network is connection-aware and auto-arranged; isolated nodes reveal full names on hover/search to avoid collisions; relationship labels appear on hover; and the Locations workspace uses OpenStreetMap standard tiles with visible attribution. Interactive controls throughout the application include plain-language hover descriptions.

# SANKET — Case Memory & Investigation Workspace

## Current completion milestone — V1.10.6 + C4

The frozen V1.10.6 interface and approved light-theme variant remain the visual baseline. C4 completes the investigator-facing workflow experience and moves the product toward final validation and delivery hardening:

- **AI investigation planner:** natural-language questions are converted into an allow-listed `InvestigationWorkflow`; the AI plan is validated and is never executed directly.
- **Deterministic reporting:** completed workflow runs now return a structured investigation report plus Markdown export, with findings, provenance counts, contradictions and uncertainty notes.
- **Human field review:** extracted fields can be explicitly verified/corrected without overwriting the original extraction value; the action is added to the audit trail.
- **Workflow persistence:** the investigation canvas can save/load the current workflow per case in browser storage.
- **API hardening:** local CORS origins are explicit/configurable and upload size is bounded per file.
- **Runtime resilience:** the OpenAI SDK is loaded only for non-Ollama transport, so native local Ollama usage does not require the SDK import path.

Backend regression suite: **149 tests passing** in the available environment. A deterministic final-acceptance harness also validates the full post-extraction investigation loop without a live VLM, including workflow execution and result traceability. Frontend production build still needs to be executed on a machine with npm dependencies installed; the current environment cannot reach the npm registry.

Run the deterministic final acceptance from the repository root:

```powershell
python scripts/final_acceptance.py
```

See `docs/FINALIZATION_AND_DEMO.md` for the manual end-to-end gate, demo script and submission checklist.

**KAYA Software Hackathon — Problem Statement #13**

SANKET is the investigation-facing intelligence layer built around the Clarity document extraction pipeline. Its purpose is not to become another document dashboard. It turns fragmented case information into a connected, traceable, time-aware **case memory** that an investigator can explore, investigate and verify.

> **Core idea:** collect scattered information, keep the relationships and chronology together, and make every important conclusion traceable back to its source evidence.

## KAYA Software Hackathon alignment

This project targets **Problem Statement #13 — AI-Powered Criminal Network Analysis System** in KAYA Software Hackathon. The official Software Hackathon brief asks teams to build secure, agent-powered software and describes PS #13 around collecting/processing multiple sources, extracting people/locations/vehicles/phones/organizations, mapping relationships, identifying key individuals, detecting suspicious patterns, and assisting investigators with visual and analytical insights.

For the online submission, KAYA currently requires a **public GitHub repository** containing the source code and README, plus a **demo video of up to 5 minutes**. A presentation deck is optional but recommended, and a hosted demo URL is optional. The current submission deadline shown by KAYA is **24 September 2026**.

Source: https://kaya.azmth.in/events/hackathon/

## What SANKET solves

Investigative information is often distributed across FIRs, reports, seizure memos, arrest records, medical records, forensic reports, communications, transactions, locations and other evidence. SANKET consolidates the extracted information into one case model:

```text
Scattered evidence
      ↓
Clarity extraction / Graph Contract
      ↓
Entity resolution
      ↓
Evidence Graph
      ↓
Case Memory
 ┌────┼─────────┬──────────┐
 ↓    ↓         ↓          ↓
People  Events  Locations  Documents
      ↓
Explore / Investigate / Verify
      ↓
Evidence-backed findings
```

The system is designed as investigator decision support. It does not make legal guilt determinations or automate enforcement decisions.

## Official PS #13 coverage

The project remains aligned with the required capabilities of KAYA PS #13:

| Requirement | SANKET capability |
|---|---|
| Multiple data sources | Documents, structured records, scenario data and supported evidence sources |
| Structured + unstructured analysis | Clarity Graph Contract plus structured case records |
| Entity extraction | People, locations, vehicles, phones, organizations and extensible entity types |
| Relationship mapping | Evidence Graph and Cytoscape network exploration |
| Key individuals | Graph analytics and workflow nodes for structural importance |
| Suspicious / unusual activity | Deterministic anomaly and bridge analysis |
| Investigator-facing insight | Case memory, timeline, workflow canvas, evidence review and source-linked findings |

## Product model

SANKET is best understood as **one case memory with different views**, not as a collection of unrelated tools.

### Case memory

The persistent logical model contains:

- documents and hashes;
- extracted fields;
- people, locations, vehicles, phones, accounts and organizations;
- events and dates;
- relationships;
- evidence references;
- contradictions;
- confidence and review state;
- workflow executions and analytical findings.

### Explore

Investigators can inspect the same memory as:

- an entity network;
- a timeline;
- a geographic view;
- a document/evidence index.

### Investigate

The Investigation Canvas lets an investigator compose and execute deterministic analysis nodes such as:

- time filtering;
- network expansion;
- graph analytics;
- key-individual analysis;
- community detection;
- bridge analysis;
- anomaly detection;
- shortest path;
- evidence review;
- reporting.

Natural-language AI is intended to generate a validated workflow rather than directly execute arbitrary system/database operations.

### Verify

Every important observation or finding should be inspectable through:

- source document;
- page / bounding box where available;
- extracted value;
- confidence;
- SHA-256 hash;
- provenance chain;
- contradictory observations.

## Current architecture

```text
                     ┌────────────────────────┐
                     │      Clarity            │
                     │ extraction / validation │
                     └───────────┬────────────┘
                                 │ Graph Contract
                                 ▼
                    ┌─────────────────────────┐
                    │ Graph Contract Adapter   │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ Entity Resolution       │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ Evidence Graph          │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ Temporal Intelligence   │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ Graph Analytics         │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ Anomaly / Pattern       │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ Investigation Workflow  │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ Evidence / Provenance  │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ AI Investigation Agent  │
                    │ (next milestone)        │
                    └─────────────────────────┘
```

## Data and evidence principles

### Observed facts are not hypotheses

SANKET distinguishes:

```text
OBSERVED
CORRELATED
INFERRED
HYPOTHESIS
CONFLICT / REVIEW_REQUIRED
```

An inferred association must never be presented as an established fact.

### Contradictions are preserved

Conflicting source observations are not silently overwritten. For example, if separate documents contain different case references or locations, SANKET records the observations, exposes the conflict and asks the investigator to review the underlying evidence.

### Synthetic and public data

The integrated demo should use transparent, controlled data. Public datasets can validate components, while seed-controlled synthetic investigation scenarios provide hidden ground truth for objective evaluation.

Examples:

- **IBM AMLSim** — synthetic banking / AML transaction scenarios;
- **Elliptic Bitcoin Dataset** — labeled Bitcoin transaction data for illicit-transaction detection;
- **Stanford SNAP Enron Network** — email communication-network dataset;
- **UNODC Data Portal** — crime and criminal-justice statistics.

These datasets serve different validation roles and should not be described as a single real criminal-network corpus.

## Technology stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite / PostgreSQL-compatible persistence
- NetworkX / deterministic graph analytics
- Clarity Graph Contract integration

### VLM / extraction

- Qwen2.5-VL 3B (`qwen2.5vl:3b`)
- Ollama for local/offline development
- OpenCV + Pillow preprocessing
- Schema-constrained structured extraction

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- Cytoscape.js
- MapLibre GL
- TanStack Table / Virtual
- ECharts where charting is useful
- Zustand
- Lucide icons

## Frontend design direction

The SANKET interface is intentionally **professional, minimal and investigation-first**.

The application is organized into five mental areas:

```text
CASE
  Overview

EXPLORE
  Entity network
  Locations

INVESTIGATE
  Workflow

EVIDENCE
  Ledger
  Documents

REVIEW
  Evidence review
  Quality & analytics
```

All existing functionality remains available, but technical subsystems should appear inside the workspace where they are useful instead of competing for equal visual priority.

### Design rules

- The case and its evidence are the primary context.
- Ingestion is always discoverable.
- Documents are a compact source strip, not a permanent dashboard wall.
- The network and workflow are the main investigative surfaces.
- Evidence and provenance remain one click away.
- Raw JSON is secondary to human-readable summaries.
- Technical details are revealed progressively.
- Decorative HUD elements, glowing cards and unsupported certification language are avoided.

## Main workspaces

### Overview — case memory

Answers:

> What is in this case, what do we know, and what needs attention?

Contains:

- case summary;
- source-document count;
- remembered entities;
- timeline events;
- review queue;
- important identifiers;
- seized property summary.

### Entity network — relationships

Answers:

> What is connected to what?

Includes:

- Cytoscape graph;
- layout controls;
- entity search;
- node inspection;
- source-document navigation;
- property relationships.

### Investigation — analytical workflow

Answers:

> What analysis should I run, and how was the result produced?

The workflow canvas supports editing, connecting, configuring and executing allow-listed analysis nodes against the case Evidence Graph.

### Locations — geographic memory

Answers:

> Where did the relevant evidence/events occur?

Provides an interactive MapLibre view, source-linked location details and case-fit navigation.

### Evidence — source record

Answers:

> Where did this information come from?

Includes:

- searchable field ledger;
- document inspector;
- bounding-box overlays;
- source metadata;
- Graph Contract export.

### Review — uncertainty and quality

Answers:

> What should I verify before trusting the analytical result?

Includes:

- contradiction review;
- provenance inventory;
- confidence and quality signals;
- source lineage.

## Case-memory restoration

The frontend attempts to restore the active case from the backend when the workspace opens. This prevents a restart of the FastAPI process or browser workspace from being treated as a brand-new empty investigation when the case data is already persisted in the local database.

## Evidence graph source

The Network workspace prefers the case-level Graph Contract endpoint when a rich graph is available. It renders entity/event nodes and semantic relationship edges from that contract, while retaining a reconciled-entity fallback so the workspace remains usable when a contract is temporarily incomplete.

## Ingestion behaviour

Document ingestion is asynchronous.

The frontend receives a batch ID and polls confirmed backend status. Numeric progress is never simulated from elapsed time. A long-running VLM call can remain on the current confirmed stage while the interface shows activity. The progress reaches 100% only after the backend reports completed ingestion and cross-document reconciliation.

## Evidence provenance

Each traceable object may retain:

```text
object type
object id
status
confidence
source document
page
bounding box
text/value span
SHA-256
relationship / finding lineage
```

## Security and responsible-use position

SANKET is an investigative decision-support prototype.

It explicitly does not:

- declare a person criminal;
- make automated arrest or enforcement decisions;
- silently resolve contradictory evidence;
- allow an LLM to run arbitrary system/database commands;
- claim access to confidential law-enforcement datasets that the team does not possess.

## Development workflow

During development, the project is validated through complete replacement ZIP releases. A release is accepted only after the local automated test suite and frontend production build pass.

The final competition repository can then be published as the team's submission source.

## Current release

**V1.10.6 + C3 — Workflow Builder / Planner Reliability**

This release reorganizes the UI around the case-memory concept while preserving the backend intelligence, evidence and workflow capabilities already implemented in V1.10.3.

See:

- `docs/MASTER_PROJECT_CONTEXT.md`
- `INTELLIGENCE_ENGINE_VERSION.md`
- `INTELLIGENCE_ENGINE_V1_10_4_RELEASE.md`

for the detailed source-of-truth context and release notes.


## V1.10.6 — Network visualization correction

The Entity Network is now a case-memory view rather than a dump of extracted field objects. Semantic entities/events are shown as investigation objects, while source documents are rendered as evidence anchors connected by explicit `OBSERVED_IN` provenance links. Direct semantic relationships remain distinct from these contextual evidence links. Field-level observations such as identifiers, dates, checksums and quality notes remain fully available in the Evidence Ledger and Document Inspector.


### V1.10.6 network behavior

The Entity Network prioritizes semantic case objects and source-document evidence anchors. It hides field-like observations from the default relationship view, uses actual Graph Contract relationships when available, and adds explicit `OBSERVED_IN` provenance links to source documents. Unconnected observations can still be revealed without removing them from case memory.


## V1.10.6 Light Theme Visual Variant

The approved V1.10.6 frontend is also provided as a light-theme visual variant for workstation readability. This variant changes presentation only; the intelligence engine, evidence model, workflow engine, ingestion behaviour and case-memory structure remain unchanged.

See `INTELLIGENCE_ENGINE_V1_10_6_LIGHT_THEME_RELEASE.md` for the visual scope and acceptance notes.


## V1.10.6 + C3 — Workflow builder interactions

The Investigation workspace now behaves as an investigator-controlled workflow editor rather than a static diagram. Output pins can be dragged directly to input pins to create edges, a live wire previews the connection, and invalid self-loops/duplicates/cycles are rejected before they reach the backend. Connections can be selected and deleted, nodes can be duplicated, and Escape/Delete keyboard actions provide direct editing controls.

The AI Investigation Planner also hardens a common local-model failure mode: ordinal edge placeholders such as `node-2` are deterministically mapped to the exact node emitted in that workflow and surfaced as a warning. Arbitrary unknown references remain rejected.

See `INTELLIGENCE_ENGINE_V1_10_6_C3_WORKFLOW_BUILDER_RELEASE.md` for the complete release notes.


## V1.10.6 + C4 — Workflow experience completion

C4 makes the Investigation Canvas communicate the value of execution instead of leaving the investigator with only a low-level execution trace. After a run, a dedicated results workspace exposes analytical leads, evidence/provenance counts, contradictions, execution details and the deterministic report. Findings can be opened back on their originating workflow node and, when a reconciled entity match is available, in Entity Network.

The workflow workspace also adapts to narrower viewports: the node palette becomes an overlay, result/inspector content stacks, and the canvas keeps explicit fit/zoom controls instead of shrinking nodes below usable size.

Manual custom nodes remain safe: the investigator selects an existing allow-listed execution operation, gives it an investigator-facing label/description and configuration, then connects it through output/input ports. The builder never executes arbitrary code.

See `INTELLIGENCE_ENGINE_V1_10_6_C4_WORKFLOW_EXPERIENCE_RELEASE.md` for release notes and the updated `docs/MASTER_PROJECT_CONTEXT.md` for the product context.
