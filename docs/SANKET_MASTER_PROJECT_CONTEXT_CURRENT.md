# AI-Powered Criminal Network Analysis System — MASTER PROJECT CONTEXT

> KAYA Software Hackathon — Problem Statement #13  
> **This document is the project's source-of-truth context for Team 2.**
>
> Last updated: **19 September 2026**

## 0. Purpose of This File

This file exists so that every future design, implementation, architecture, dataset, UI, AI/ML, testing, demo and documentation decision remains aligned with the actual KAYA PS #13.

It is intentionally more strict than a normal README.

### Non-negotiable rule

Before implementing any major feature, the team must check this document.

If a major product/architecture/data decision changes, this file must be updated first or at the same time, with the decision recorded in the Change Log at the end.

### Never drift into a different project

The project must remain an:

> **AI-powered system that analyzes structured and unstructured crime-related data to uncover criminal networks, identify key influencers, detect suspicious patterns and provide actionable intelligence for investigators.**

The n8n-style canvas is a product/UI mechanism. It is not a replacement for the official problem statement.

### Important distinction

This project is separate from the user's other KAYA project:

- Team 1: iTantra — PS #11
- Team 2: Criminal Network Analysis — PS #13

Do not mix their requirements, architecture, datasets or implementation plans.

---

# 1. OFFICIAL KAYA PS #13 — SOURCE OF TRUTH

The following is the exact problem statement supplied by the team from the official KAYA page. It must remain the mandatory scope.

## 13

### AI-Powered Criminal Network Analysis System

### Hackathon Software

#### Background

Modern criminal activities are increasingly organized and interconnected. Criminals operate through networks involving associates, intermediaries, financial channels, communication links, locations and events. Law enforcement agencies collect large volumes of data from sources such as FIRs and police reports, Call Detail Records (CDRs), financial transaction records, surveillance reports, social media intelligence, criminal history databases and intelligence agency reports. Investigators frequently face challenges identifying hidden relationships among suspects because data is fragmented, unstructured and distributed across multiple systems, and manual analysis is slow, labor-intensive and prone to missing critical connections. Advances in AI, ML, NLP and Graph Analytics make it possible to automatically discover relationships, detect patterns, and generate insights to understand criminal networks more effectively.

#### Description

Develop an AI-powered system that analyzes large volumes of criminal and intelligence-related data to uncover hidden networks and relationships among individuals, organizations, locations and events.

#### The system should

1. Collect and process data from multiple sources.
2. Extract important entities — people, locations, vehicles, phone numbers, organizations.
3. Build relationship maps showing how different entities are connected.
4. Identify key individuals playing influential roles in criminal networks.
5. Detect suspicious patterns and unusual activities.
6. Assist investigators with visual and analytical insights.

#### Expected Solution

Develop an AI-powered system that automatically analyzes structured and unstructured crime-related data to uncover criminal networks, identify key influencers, detect suspicious patterns, and provide actionable intelligence for investigators.

---

# 2. Mandatory Coverage Matrix

Every release/demo must be traceable to every official requirement.

| Official PS requirement | Our implementation target | Must be demonstrated? |
|---|---|---|
| Multi-source data collection | Case reports/FIR-like documents, CDR-like records, financial records, location/event data, scenario data and other supported sources | Yes |
| Structured + unstructured processing | Structured records + document/text extraction output | Yes |
| Entity extraction | Person, location, vehicle, phone, organization; extensible to account/device/IP/case | Yes |
| Relationship mapping | Evidence-backed temporal graph | Yes |
| Key individual identification | Centrality + community role + bridge/intermediary analysis + transparent scoring | Yes |
| Suspicious pattern detection | Temporal + structural + behavioral + cross-source anomaly/pattern detection | Yes |
| Investigator visual insights | Interactive evidence graph + timeline + investigation canvas + entity/evidence inspector | Yes |
| Investigator analytical assistance | Search, filtering, tracing, evidence review, AI-assisted workflow generation and reporting | Yes |
| Actionable intelligence | Evidence-backed leads/hypotheses with provenance and uncertainty | Yes |

A feature is not complete merely because it exists in code. It is complete when the relevant PS requirement can be demonstrated and explained.

---

# 3. CURRENT TEAM OWNERSHIP / MODULE BOUNDARY

## Vaibhav — Document Extraction Layer

Vaibhav is responsible for the portion before the intelligence engine:

```text
Uploaded document
    ↓
Document parsing/OCR/text extraction
    ↓
Entity/event/relationship extraction
    ↓
Structured extraction output
```

The exact extraction technology is still an implementation decision.

### Vaibhav's output should preferably contain

### Entities

- stable or temporary extraction ID
- entity type
- raw value/name
- normalized value where available
- aliases where available
- attributes
- document ID
- page/line/text-span or other source locator
- extraction confidence

### Events

- event ID
- event type
- source entity
- target entity where applicable
- timestamp/date/time range
- event attributes
- source document and location
- extraction confidence

### Relationships

Where confidently extractable:

- source entity
- target entity
- relationship type
- confidence
- evidence/source references

### Critical integration rule

The extraction layer must preserve provenance.

Do not return only:

```json
{
  "name": "Rahul Kumar"
}
```

Prefer:

```json
{
  "id": "raw_person_01",
  "type": "PERSON",
  "name": "Rahul Kumar",
  "source": {
    "document_id": "FIR_001",
    "page": 2,
    "text_span": "Rahul Kumar..."
  },
  "confidence": 0.96
}
```

The exact schema can evolve, but the contract must be explicit before integration.

---

# 4. MY / POST-EXTRACTION MODULE

The user's current responsibility starts after Vaibhav's extraction output.

Primary ownership:

```text
Structured extraction output
        ↓
Entity normalization
        ↓
Entity resolution
        ↓
Relationship/event normalization
        ↓
Evidence graph
        ↓
Temporal analysis
        ↓
Graph analytics
        ↓
Pattern/anomaly detection
        ↓
Evidence scoring / provenance
        ↓
Investigation workflow engine
        ↓
AI investigation orchestration
        ↓
Investigator-facing UI
```

This boundary is intentionally explicit so the two team members can work independently.

---

# 5. PRODUCT CONCEPT — INVESTIGATIVE GRAPH WORKFLOW CANVAS

The product should be treated as:

> **n8n-style investigation workflow + evidence graph + temporal intelligence + AI assistance + provenance/uncertainty**

The core design principle is to separate:

### Evidence Graph

Answers:

> Who/what is connected to whom/what, when, and based on which evidence?

### Investigation Canvas

Answers:

> What analytical operations is the investigator performing, in what order, and with what parameters?

These are synchronized but should not be treated as the same data structure.

---

# 6. FRONTEND DIRECTION

The visual reference discussed by the team is a dark, professional operations/investigation dashboard:

- dark background
- central large canvas
- thin connection lines
- compact node cards
- left-side navigation/tool rail
- top control bar
- bottom analytical cards
- timeline controls
- restrained green/amber/red status semantics
- dense but organized information hierarchy
- smooth zoom/pan/selection
- minimal decorative clutter

Do not copy a reference image 1:1.

Adapt the visual language to investigative intelligence.

## Recommended screen composition

```text
┌───────────────────────────────────────────────────────────────┐
│ CASE • TIME RANGE • SEARCH • FILTERS • RUN • EXPORT          │
├──────┬────────────────────────────────────────────────────────┤
│      │                                                        │
│ NAV  │               INVESTIGATION CANVAS                     │
│      │                                                        │
│      │     [Workflow Nodes + Evidence/Graph View]             │
│      │                                                        │
│      │                                                        │
├──────┴────────────────────────────────────────────────────────┤
│ Network Stats │ Findings │ Alerts │ Selected Entity/Evidence │
├───────────────────────────────────────────────────────────────┤
│                    TEMPORAL TIMELINE                           │
└───────────────────────────────────────────────────────────────┘
```

---

# 7. THREE CATEGORIES OF CANVAS NODES

## 7.1 Entity nodes

Examples:

- Person
- Phone
- Account
- Vehicle
- Device
- Location
- Organization
- IP/digital identifier
- Case

## 7.2 Evidence nodes

Examples:

- Call record
- Transaction
- CCTV observation
- Report
- Chat/message
- Location event
- Device artifact
- Case document

## 7.3 Analysis/workflow nodes

Examples:

- Filter
- Expand
- Trace
- Correlate
- Compare
- Cluster
- Detect anomaly
- Find bridges
- Rank
- Verify
- Report

The canvas must not visually imply that an analytical operation is an entity in the evidence graph.

---

# 8. EDGE / THREAD SEMANTICS

The “thread and pins” concept should be functional, not decorative.

Every relationship should carry metadata.

Example:

```text
PERSON A ───────── PERSON B

Type: Communication
Strength: 0.82
Confidence: 0.87

Supporting evidence:
• 17 calls
• 3.4 hours total duration
• 4 overlapping dates
• 6 common tower regions

First observed: 03 Aug
Last observed: 12 Sep

Status: Evidence-backed
```

## Relationship states

At minimum:

```text
OBSERVED
CORRELATED
INFERRED
HYPOTHESIS
CONTRADICTED / CONFLICTED
UNRESOLVED
```

The UI should distinguish these states clearly.

### Never do this

```text
AI score = 0.91
↓
Person is criminal
```

### Do this

```text
Investigative lead
Score = 0.91
Evidence + supporting signals shown
Contradictions shown
Status = inferred/hypothesis
```

---

# 9. KEY DIFFERENTIATOR

The team has already identified that ordinary criminal-network visualization is crowded.

Established platforms such as i2 Analyst's Notebook and DataWalk already provide mature link-analysis, entity/relationship exploration, temporal analysis and visual investigation capabilities.

Therefore:

> **Do not claim the invention is “a graph for criminal networks.”**

Our product differentiation is the combination of:

1. Investigation workflow composition
2. Evidence-aware relationships
3. Temporal reasoning
4. Explicit uncertainty
5. AI-generated analytical workflows
6. Reproducible investigation state
7. Evidence provenance
8. Controlled anomaly/bridge discovery

The competitive thesis is:

> **An AI-native investigation workspace that turns fragmented, uncertain and time-dependent evidence into an auditable, reproducible network-analysis workflow.**

---

# 10. CORE END-TO-END FLOW

```text
CASE / SOURCE DATA
        ↓
DATA INGESTION
        ↓
DOCUMENT / STRUCTURED PROCESSING
        ↓
ENTITY EXTRACTION
        ↓
ENTITY NORMALIZATION
        ↓
ENTITY RESOLUTION
        ↓
EVENT / RELATIONSHIP NORMALIZATION
        ↓
EVIDENCE GRAPH
        ↓
┌───────────────────────┬────────────────────────┐
│                       │                        │
▼                       ▼                        ▼
TEMPORAL ENGINE     GRAPH ANALYTICS        PATTERN ENGINE
│                       │                        │
└───────────────────────┴────────────────────────┘
                        ↓
                INVESTIGATION ENGINE
                        ↓
            ┌───────────┴───────────┐
            ▼                       ▼
       AI WORKFLOW AGENT       HUMAN ANALYST
            │                       │
            └───────────┬───────────┘
                        ↓
                ANALYTICAL EXECUTION
                        ↓
               FINDINGS / LEADS
                        ↓
                  EVIDENCE REVIEW
                        ↓
              INVESTIGATION REPORT
```

---

# 11. AI ARCHITECTURE

AI should not be allowed to directly invent evidence or run arbitrary database/system operations.

Preferred flow:

```text
Natural-language investigator request
        ↓
Investigation Agent
        ↓
Structured Workflow JSON
        ↓
Schema validation
        ↓
Allowed-operation validation
        ↓
Execution engine
        ↓
Graph / Evidence services
        ↓
Evidence-backed result
        ↓
AI explanation constrained by retrieved evidence
```

## Example

Investigator:

> “Find possible intermediaries connecting Group A and Group B during the last 30 days.”

AI creates:

```json
{
  "workflow": [
    {
      "node": "time_filter",
      "parameters": {
        "days": 30
      }
    },
    {
      "node": "community_select",
      "parameters": {
        "groups": ["A", "B"]
      }
    },
    {
      "node": "bridge_analysis"
    },
    {
      "node": "rank_candidates"
    },
    {
      "node": "attach_evidence"
    }
  ]
}
```

The engine—not the LLM—executes the analysis.

---

# 12. DATA STRATEGY — LOCKED PRINCIPLE

## Do not claim access to real sensitive investigation data unless it actually exists and is lawfully available.

Never write or say:

> “We trained on millions of real Indian FIR/CDR/banking records”

unless this can be documented.

Real case-level law-enforcement, CDR and financial investigation data is sensitive.

## Recommended data strategy

```text
Public research datasets
        +
Domain-specific simulators
        +
Controlled synthetic investigation scenarios
        ↓
Subsystem validation + end-to-end evaluation
```

The README must always distinguish:

- real/public dataset
- synthetic simulator output
- internally generated scenario
- transformed/preprocessed derivative data

---

# 13. PUBLIC / RESEARCH DATASET STRATEGY

## 13.1 Enron Email Network

Stanford SNAP publishes the Enron email communication network.

Current SNAP summary includes approximately:

- 36,692 nodes
- 183,831 edges

The dataset is suitable for validating communication-network analytics, community detection, temporal/network methods and visualization.

### Critical limitation

It is not a criminal-network dataset.

Use it for:

```text
communication graph validation
community analysis
network statistics
temporal interaction analysis
bridge/intermediary algorithms
```

Source:

https://snap.stanford.edu/data/email-Enron.html

---

## 13.2 IBM AMLSim

IBM AMLSim is a simulator intended to generate synthetic banking transaction data with known money-laundering patterns for testing ML models and graph algorithms.

It is useful for:

- transaction graphs
- suspicious transaction patterns
- graph analytics
- financial network analysis
- ground-truth evaluation

### Critical limitation

AMLSim is synthetic.

Do not describe it as real police/banking investigation data.

Source:

https://github.com/IBM/AMLSim

---

## 13.3 IBM AML Data

IBM also provides synthetic anti-money-laundering transaction data. The repository documentation states that transactions include legitimate and laundering-tagged activity and that the data is generated by a multi-agent virtual world rather than derived by anonymizing real people.

Use only after checking exact license/terms and the precise version/data package being used.

Source:

https://github.com/IBM/AML-Data

---

## 13.4 Elliptic Bitcoin Dataset

The Elliptic ecosystem includes labeled cryptocurrency transaction research data used for illicit-transaction analysis.

Use it for:

- financial graph experiments
- illicit/licit transaction classification
- graph anomaly experiments
- risk scoring experiments

### Critical limitation

It is cryptocurrency transaction data, not a complete criminal intelligence network and not a substitute for Indian police intelligence data.

Source:

https://www.elliptic.co/insights/elliptic-dataset-cryptocurrency-financial-crime/

Before bundling the dataset into the project, verify the current access/license/terms.

---

## 13.5 UNODC Data Portal

UNODC provides official international crime and justice statistics across multiple categories.

Use it for:

- domain context
- aggregate statistics
- crime-category context
- explanatory charts

Do not use it as though it were an individual-level relationship graph.

Source:

https://data.unodc.org/

---

# 14. SYNTHETIC DATA — HOW WE AVOID THE “FAKE DATA” PROBLEM

The team identified a real risk: random fake CSV rows are easy for judges to spot and difficult to defend.

Therefore, we should not use:

```text
Person1
Person2
random calls
random transactions
random locations
```

Instead use a documented, seed-controlled scenario generator.

Example:

```text
Scenario ID: CRIME-SIM-0042
Seed: 847213

Entities:
50 persons
30 phones
20 accounts
12 locations
8 vehicles
4 organizations

Events:
2,000 calls
800 transactions
200 location events
50 reports
```

Then intentionally insert:

- duplicate identities
- aliases
- missing information
- contradictory locations
- temporal coordination
- shared communication hubs
- suspicious transaction chains
- hidden intermediaries
- cross-community bridges
- incomplete evidence

Most importantly:

> The generator knows the hidden ground truth.

The analytical engine does not receive the hidden labels.

---

# 15. GROUND-TRUTH EVALUATION

This is our answer to:

> “How do you know your synthetic data is producing valid conclusions?”

Process:

```text
Scenario generator
        ↓
Create ground-truth structure
        ↓
Hide planted labels
        ↓
Run investigation system
        ↓
Produce predictions/rankings
        ↓
Compare against hidden ground truth
        ↓
Precision / Recall / Ranking metrics
```

Example:

```text
Ground-truth intermediary: P17

System ranking:
1. P17 → 0.91
2. P04 → 0.67
3. P33 → 0.52

Ground truth appeared at Rank #1
```

Do not present this as an achieved result until it has actually been measured.

---

# 16. DATASET PROVENANCE

Every dataset should have a metadata record.

Example:

```json
{
  "dataset_id": "CRIME-SIM-0042",
  "source_type": "synthetic_scenario",
  "generator": "internal_scenario_generator",
  "generator_version": "0.1.0",
  "seed": 847213,
  "created_at": "2026-09-19T00:00:00Z",
  "scenario": "cross_network_intermediary",
  "ground_truth_available": true,
  "ground_truth_visible_to_model": false
}
```

For public data also store:

- name
- publisher
- source URL
- access date
- license/terms
- version where known
- preprocessing steps
- transformed-file hash where useful

This makes dataset questions answerable instead of hand-waved.

---

# 17. TRAINING STRATEGY

A custom giant criminal LLM is not required.

The initial system should prefer:

```text
Pretrained NLP model
+
Domain rules
+
Entity normalization
+
Entity-resolution scoring
+
Graph algorithms
+
Lightweight anomaly models
+
Controlled AI workflow generation
```

## NLP

Use a suitable pretrained NER-capable model plus domain rules.

## Entity resolution

Use explicit signals:

- name similarity
- identifier overlap
- phone overlap
- address similarity
- temporal consistency
- shared neighbors
- shared locations

Store the resulting score and reasons.

## Graph analytics

Use established methods:

- degree centrality
- betweenness centrality
- closeness
- eigenvector/PageRank-type influence
- shortest paths
- connected components
- community detection
- temporal activity statistics

## Anomaly detection

Possible lightweight methods:

- Isolation Forest
- Local Outlier Factor
- statistical baselines
- graph-structure deviation analysis

## Advanced ML

GNNs/learned edge-risk models are optional.

Rule:

> Never add a model to the MVP merely for buzzwords if the team cannot explain its data, training, evaluation and failure modes.

---

# 18. ENTITY RESOLUTION — CORE TECHNICAL MODULE

Example input:

```text
Ravi Kumar
R. Kumar
Ravi K.
9876543210
```

Possible result:

```text
Canonical entity: PERSON_017

Aliases:
- Ravi Kumar
- R. Kumar
- Ravi K.

Linked identifier:
- phone identifier

Resolution confidence: 0.91

Evidence:
✓ name similarity
✓ phone overlap
✓ address consistency
✓ temporal consistency
```

## Never silently merge entities.

Possible states:

```text
CONFIRMED MATCH
PROBABLE MATCH
POSSIBLE MATCH
UNRESOLVED
CONFLICTED
```

Low-confidence matches should remain reviewable.

---

# 19. EVIDENCE GRAPH DATA MODEL

## Entity types

```text
Person
Phone
Account
Vehicle
Device
Location
Organization
DigitalIdentifier
Case
```

## Evidence/event types

```text
Call
Transaction
Meeting
LocationEvent
Document
CCTVObservation
Message
DeviceArtifact
```

## Example relations

```text
PERSON ──OWNS──> PHONE
PERSON ──USES──> ACCOUNT
PERSON ──DRIVES──> VEHICLE
PERSON ──LOCATED_AT──> LOCATION
PERSON ──CALLED──> PERSON
PERSON ──TRANSFERRED_TO──> ACCOUNT
PERSON ──ASSOCIATED_WITH──> PERSON
CASE ──CONTAINS──> EVIDENCE
EVIDENCE ──SUPPORTS──> RELATIONSHIP
```

## Edge metadata

Every relationship should be able to store:

```text
type
confidence
strength
first_seen
last_seen
source_ids
status
inference_method
supporting_signals
contradicting_signals
```

---

# 20. TEMPORAL INTELLIGENCE

Time is a first-class property.

Support:

- exact timestamps where available
- date ranges
- first seen
- last seen
- active period
- before/after event queries
- rolling windows
- last 7/30/90 days
- event-relative windows

The user should be able to inspect how the network changes over time.

Example:

```text
JAN ─ FEB ─ MAR ─ APR ─ MAY ─ JUN ─ JUL
                  ▲
              selected window
```

Useful questions:

- What relationships existed during the selected period?
- Which entities became active after a key event?
- Which links disappeared?
- Which entity started connecting separate communities?
- Which activity intensified immediately before an event?

---

# 21. KEY-INDIVIDUAL ANALYSIS

The PS explicitly requires identification of influential roles.

Do not rely on one metric.

Possible signals:

```text
Degree
Betweenness
Closeness
PageRank/eigenvector influence
Cross-community connectivity
Communication frequency
Transaction connectivity
Temporal coordination
Repeated co-occurrence
```

Example:

```text
PERSON_017

Degree: 0.74
Betweenness: 0.91
Cross-community bridge score: 0.88
Communication signal: 0.84
Temporal signal: 0.79

Investigative priority: 0.86
```

This is a lead/priority score, not a probability of guilt.

---

# 22. HIDDEN-LINK / BRIDGE ANALYSIS

Recommended showcase capability:

```text
GROUP A                        GROUP B

A1 ─ A2 ─ A3                B1 ─ B2 ─ B3
          \                  /
           \                /
                X
```

Potential candidate X can be surfaced from:

- bridge/betweenness structure
- communications with both groups
- transaction links
- location overlap
- temporal overlap
- repeated co-occurrence

Output:

```text
Candidate: X
Score: 0.84

Supporting evidence:
✓ 11 communications
✓ 3 shared locations
✓ 2 transaction paths
✓ 4 temporal overlaps

Status: Investigative lead
```

Never state that X is a criminal solely because X scores highly.

---

# 23. SUSPICIOUS-PATTERN ENGINE

The official PS requires suspicious patterns and unusual activity.

The initial engine should detect interpretable patterns such as:

### Structural

- bridge node
- sudden hub formation
- unusually dense subgroup
- cross-community connector
- unexpected multi-hop linkage

### Temporal

- burst activity
- unusual simultaneous interactions
- sudden change in activity
- repeated coordination windows

### Financial

- rapid money flow through multiple accounts
- unusual transaction paths
- repeated round-trip structures
- cross-community money movement

### Communication

- sudden contact burst
- new high-frequency contact
- coordinated communication windows
- unusual cross-group communication

### Location

- repeated co-location
- improbable movement sequence
- unusual location overlap

These are analytical patterns, not criminal determinations.

---

# 24. MULTI-SOURCE CORRELATION

The system should benefit from multiple sources rather than relying on one.

Example:

```text
CALL RECORD
    +
TRANSACTION
    +
LOCATION EVENT
    +
CASE REPORT
        ↓
Cross-source correlation
        ↓
Stronger or weaker lead
```

This is one of the strongest reasons to preserve source-level provenance.

---

# 25. CONTRADICTION HANDLING

Real investigation data can disagree.

Example:

```text
Source A:
P17 → Location: Lucknow

Source B:
P17 → Location: Kanpur
```

Do not overwrite one with the other.

Represent:

```text
Status: CONFLICT

Reason:
Conflicting observations in overlapping time window
```

Possible future extensions:

- source reliability metadata
- temporal disambiguation
- conflict resolution suggestions
- human review queue

---

# 26. UNKNOWN / MISSING DATA HANDLING

The system must distinguish:

```text
KNOWN
UNKNOWN
MISSING
NOT APPLICABLE
CONTRADICTORY
LOW CONFIDENCE
```

Never interpret missing data as evidence of absence.

Example:

```text
No transaction record found
```

must not automatically become:

```text
No transaction occurred
```

This distinction should appear in the data model and in investigator explanations.

---

# 27. ORPHAN / PARTIAL RECORD HANDLING

Possible input cases:

- event references an entity not yet resolved
- phone exists but person mapping is unknown
- transaction has one side missing
- timestamp is incomplete
- document extraction misses an identifier
- relationship type is unknown
- duplicate event records exist

The system should not crash.

Preferred behavior:

```text
PARTIAL EVIDENCE
UNRESOLVED ENTITY
UNKNOWN RELATIONSHIP
INCOMPLETE EVENT
```

Allow later resolution when new data arrives.

---

# 28. DATA NORMALIZATION

Normalize common fields before graph creation:

- phone formats
- account identifiers
- vehicle identifiers
- location spellings
- names/aliases
- date/time formats
- organization names

But retain the raw original value.

Recommended structure:

```text
raw_value
normalized_value
normalization_method
normalization_confidence
```

Never destroy source text during normalization.

---

# 29. INVESTIGATION CANVAS BEHAVIOR

## Node operations

- Add node
- Remove node
- Connect
- Configure
- Duplicate
- Expand neighbors
- Run
- Disable
- View input/output
- Pin/lock
- Focus neighborhood

## Workflow operations

- Run selected node
- Run entire workflow
- Pause
- Inspect intermediate result
- Re-run from a node
- Save
- Load
- Version
- Compare versions

## Graph operations

- Search
- Filter by type
- Filter by time
- Filter by confidence
- Filter by evidence status
- Expand 1/2/3 hops
- Focus neighborhood
- Compare communities
- Hide/show relationship classes

---

# 30. REPRODUCIBILITY

A finding should be reproducible.

Store:

- case ID
- dataset ID/version
- workflow definition
- workflow version
- node parameters
- model/rule version
- execution timestamp
- evidence references
- result identifiers

A saved workflow should be rerunnable against the same case version.

---

# 31. EVIDENCE PROVENANCE

Every finding should answer:

> Why does the system believe this?

Example:

```text
Finding #17
Potential bridge entity: P17

Derived from:
├── 11 communication records
├── 3 location events
├── 2 transaction paths
└── 4 temporal overlaps

Rule/model version:
bridge-score-v0.1

Status:
Investigative lead
```

The investigator should be able to click the evidence references.

---

# 32. EXPLAINABILITY RULE

Every score must have:

```text
score
input signals
weights/model version
supporting evidence
contradictory evidence
status
```

Do not expose unexplained numbers such as:

```text
Risk = 0.83
```

without showing what contributes to it.

---

# 33. PROPOSED TRANSPARENT SCORING BASELINE

Initial design example:

```text
Candidate Score =
    35% bridge/connectivity signal
  + 25% communication signal
  + 20% transaction signal
  + 10% location signal
  + 10% temporal signal
```

These percentages are design defaults only.

They are not validated probabilities.

They must be experimentally tuned or justified before being presented as model performance.

---

# 34. HLD — HIGH-LEVEL DESIGN

```text
┌─────────────────────────────────────────────────────────────┐
│                    INVESTIGATION UI                        │
│ Canvas | Graph | Timeline | Evidence | Investigator Chat   │
└──────────────────────────────┬──────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                INVESTIGATION ORCHESTRATOR                   │
│ validation • execution • state • workflow versioning        │
└───────────────┬─────────────────────────────┬───────────────┘
                ↓                             ↓
┌─────────────────────────┐       ┌───────────────────────────┐
│ AI INVESTIGATION AGENT  │       │ GRAPH / PATTERN ENGINE    │
│ NL → workflow           │       │ centrality               │
│ explanation             │       │ communities              │
│ hypothesis assistance   │       │ temporal analysis        │
└──────────────┬──────────┘       │ bridges / anomalies      │
               │                  └────────────┬──────────────┘
               └──────────────┬───────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     EVIDENCE GRAPH                          │
│ entities • events • relations • sources • confidence • time│
└──────────────────────────────┬──────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│            ENTITY / RELATIONSHIP LAYER                     │
│ normalization • resolution • linking • evidence metadata  │
└──────────────────────────────┬──────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                     DATA INGESTION                          │
│ extracted structured output • public data • scenario data  │
└─────────────────────────────────────────────────────────────┘
```

---

# 35. LLD — LOW-LEVEL DIRECTION

Use a modular monolith first.

Recommended structure:

```text
criminal-network-analysis/
│
├── frontend/
│   ├── canvas/
│   ├── graph-view/
│   ├── timeline/
│   ├── evidence-panel/
│   ├── investigator-chat/
│   └── components/
│
├── backend/
│   ├── api/
│   ├── orchestration/
│   ├── workflow/
│   ├── ai/
│   ├── graph/
│   ├── evidence/
│   ├── entity_resolution/
│   ├── nlp/
│   ├── analytics/
│   ├── scoring/
│   ├── provenance/
│   └── reporting/
│
├── data/
│   ├── public/
│   ├── synthetic/
│   └── schemas/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
│
└── docs/
```

Do not prematurely split into many microservices.

---

# 36. SUGGESTED TECHNOLOGY STACK

## Frontend

- React
- TypeScript
- React Flow or equivalent workflow-canvas library
- Cytoscape.js or equivalent network visualization library
- Timeline/chart library only where needed

## Backend

- Python
- FastAPI

## Graph

- Neo4j
- NetworkX for local/algorithmic operations where appropriate

## NLP/ML

- Transformers / spaCy or another suitable open model
- RapidFuzz or equivalent similarity library
- scikit-learn
- optional PyTorch

## AI

- LLM/agent layer for structured workflow generation
- function/tool calling or strict JSON schema
- deterministic validated backend execution

Avoid unnecessary infrastructure.

---

# 37. DATABASE / GRAPH DESIGN PRINCIPLE

Neo4j should store the graph and relationship/evidence context required for graph traversal.

Do not put every UI state directly into the graph.

Recommended conceptual separation:

```text
CASE/EVIDENCE DATA
        ↓
DOMAIN GRAPH
        ↓
ANALYSIS RESULTS
        ↓
WORKFLOW STATE
```

Workflow definitions can be persisted separately or as structured documents associated with a case.

---

# 38. EVALUATION PLAN

## Entity resolution

Measure:

- precision
- recall
- F1

## Hidden-link / bridge detection

Measure:

- Precision@K
- Recall@K
- ranking quality such as NDCG where appropriate

## Anomaly detection

Measure:

- precision
- recall
- false-positive rate

## Workflow

Measure:

- execution time
- graph-query latency
- analytical-node latency
- failure rate

## Provenance/explainability

Verify:

- every finding has evidence references
- every score has contributing signals
- contradictions are surfaced
- workflow version is stored

These are evaluation plans, not results until measured.

---

# 39. EDGE-CASE / FAILURE MATRIX

This section exists specifically so that implementation does not forget important possibilities.

| Situation | Required behavior |
|---|---|
| Duplicate entity names | Do not assume same entity; resolve with evidence |
| Same phone linked to multiple people | Preserve ambiguity; flag shared identifier |
| Missing phone | Continue using remaining evidence |
| Missing timestamp | Mark time as incomplete; don't invent a date |
| Conflicting timestamps | Preserve both; mark conflict |
| Conflicting locations | Preserve both; surface contradiction |
| Duplicate event | Detect/deduplicate carefully without losing provenance |
| Unknown entity type | Keep as `UNKNOWN` until resolvable |
| Unknown relationship | Store as unresolved relationship candidate |
| One-sided transaction | Store partial event |
| Event references unknown entity | Create temporary/unresolved entity |
| Very low confidence extraction | Keep reviewable; don't hard merge |
| No evidence supports an inference | Do not create the inference |
| Contradictory evidence | Lower confidence/surface conflict; don't hide it |
| No graph connections | Show isolated entity state |
| Very large graph | Lazy expansion, filtering, focused subgraph |
| Multiple communities | Allow community comparison |
| Dense graph | Filter by relationship/time/confidence |
| Time window empty | Clearly show “no qualifying evidence” |
| Model unavailable | Fall back to deterministic baseline where possible |
| AI output malformed | Reject and request/retry structured output |
| AI suggests unsupported operation | Validator blocks it |
| AI invents evidence | Evidence-grounded response layer rejects unsupported claim |
| Graph query fails | Graceful error + preserve workflow state |
| Dataset version changes | Store dataset version and invalidate/recompute affected findings |
| Scenario seed changes | Treat as a new evaluation run |
| User changes workflow | Version the workflow |
| Same entity has aliases | Preserve canonical + raw aliases |
| Same entity may actually be different people | Maintain uncertainty rather than forced merge |
| Missing source provenance | Mark evidence as provenance-incomplete |
| Real-person data accidentally enters demo | Remove/quarantine before public demo |
| Model score is uncalibrated | Call it a score, not a probability |
| Rank is high but evidence is weak | Surface high uncertainty |
| Strong single source but contradicted elsewhere | Show source conflict |
| No anomaly found | Say no anomaly detected under current criteria, not “safe” |

---

# 40. SECURITY AND PRIVACY

This is an authorized investigative decision-support system.

Principles:

- human in the loop
- least privilege
- role-based access where needed
- audit logging
- evidence provenance
- synthetic/demo data isolated from any real sensitive data
- no automatic arrest/guilt decisions
- no silent identity merging
- no unsupported relationship creation

The AI can:

- generate investigation workflows
- summarize retrieved evidence
- explain analytical results
- suggest hypotheses

The AI must not autonomously:

- determine guilt
- initiate enforcement
- fabricate evidence
- silently merge identities
- create unsupported graph facts

---

# 41. IMPORTANT ETHICAL / PRODUCT LANGUAGE

Use:

- “investigative lead”
- “potential association”
- “inferred relationship”
- “evidence-backed signal”
- “analytical priority”
- “model confidence”
- “hypothesis”

Avoid:

- “criminal” as an automatic model verdict
- “guilty”
- “mastermind”
- “confirmed offender”
- “certain relationship” unless directly established by evidence

Suggested product statement:

> **The system provides evidence-backed investigative leads and analytical insights. It does not determine guilt or replace human judgment.**

---

# 42. WHAT WE ARE NOT BUILDING

Do not allow scope to silently expand into:

- replacement for i2 Analyst's Notebook
- replacement for DataWalk
- complete law-enforcement case-management platform
- full digital-forensics suite
- universal NER system
- perfect criminal prediction
- autonomous enforcement
- unrestricted surveillance system
- giant proprietary LLM
- full real-world deployment stack for every agency

The MVP is a focused intelligence-analysis platform.

---

# 43. MVP DEFINITION

The MVP is complete only when one end-to-end investigation works:

```text
1. Load case data
2. Process structured/unstructured source outputs
3. Extract required entities
4. Resolve noisy/duplicate entities
5. Build evidence graph
6. Filter by time
7. Run graph analytics
8. Detect at least one meaningful suspicious/hidden pattern
9. Identify a key/bridge candidate
10. Show supporting evidence
11. Show uncertainty/contradictions
12. Allow investigation workflow composition
13. Allow AI to generate a validated workflow
14. Execute the workflow
15. Inspect intermediate results
16. Generate an evidence-backed report
17. Reproduce the result from saved case/workflow state
```

---

# 44. DEMO SCENARIO

Use one controlled but realistic case.

Recommended scale:

- 50–200 entities in the demo scenario
- hundreds/thousands of underlying events
- focused subgraph shown initially
- hidden ground truth behind the planted patterns

## Demo sequence

### Step 1

Load the case.

### Step 2

Show entity extraction and resolution.

### Step 3

Show the evidence graph.

### Step 4

Ask:

> “Find possible intermediaries connecting Group A and Group B during the last 30 days.”

### Step 5

AI constructs workflow nodes.

### Step 6

Execute.

### Step 7

Show candidate(s).

### Step 8

Click the candidate.

Display:

- score
- supporting evidence
- contradictions
- timeline
- source records
- inference status

### Step 9

Show the actual evidence behind the conclusion.

### Step 10

Generate report.

The demo should tell a complete story instead of showing disconnected features.

---

# 45. PERFORMANCE / UX PRINCIPLES

Do not render every entity and every relationship by default.

Preferred:

```text
Case
 ↓
Overview
 ↓
Relevant community
 ↓
Selected entity
 ↓
Neighbor expansion
 ↓
Evidence
```

Use:

- lazy expansion
- focused neighborhoods
- relationship filters
- time filtering
- confidence filtering
- community clustering
- search
- stable layouts

Keep the primary demo deterministic.

---

# 46. EXISTING-SYSTEM AWARENESS

## i2 Analyst's Notebook

Important because it already supports traditional link analysis and visual investigative analysis.

Implication:

> We should not market basic node-edge visualization as our main invention.

Source:

https://i2group.com/solutions/i2-analysts-notebook

Additional documentation:

https://www.ibm.com/docs/

## DataWalk

Important because it already combines investigation workflows around graph/data integration, entity resolution, visual link analysis and temporal/geospatial capabilities.

Implication:

> Our product must explain exactly where its workflow/AI/evidence/reproducibility emphasis differs.

Source:

https://datawalk.com/solutions/investigation/

---

# 47. WHAT OUR NOVELTY CLAIM SHOULD AND SHOULD NOT BE

## Do claim

> An AI-native investigation workspace that combines an evidence-aware temporal graph with a visual, reproducible investigation workflow and explicit uncertainty/provenance.

## Do not claim

> We invented graph-based criminal network analysis.

## Do not claim

> We built the first criminal-network graph system.

## Do not claim

> Our AI can identify criminals with high accuracy.

Unless independently measured and legally/contextually supported, do not make stronger claims.

---

# 48. JUDGE Q&A BASELINE

## “Isn't this just Neo4j?”

Neo4j is the graph storage/query component. The application adds entity resolution, evidence provenance, temporal analysis, workflow composition, pattern detection and AI-assisted investigative orchestration.

## “Isn't this just i2 Analyst's Notebook?”

i2 is an established link-analysis platform. Our focus is an AI-native investigation workflow model where investigative intent can become a transparent, executable and reproducible analytical workflow with explicit evidence and uncertainty.

## “Where is your data from?”

Public research datasets and documented synthetic/simulated scenarios, with provenance stored for each dataset. We do not claim access to sensitive real-world police/CDR/banking investigation data.

## “Why synthetic data?”

Because authentic case-level law-enforcement and financial investigation data is sensitive. Synthetic scenarios are openly disclosed and are generated with hidden ground truth so the system can be objectively evaluated.

## “How do you know the synthetic scenario isn't arbitrary?”

The scenario generator is seed-controlled, documented, and produces hidden ground truth. The model/analysis engine does not receive the ground-truth labels.

## “How do you prevent hallucinations?”

The AI creates structured workflow definitions. The workflow is schema-validated and executed by deterministic analytical services. Final findings must be tied to evidence references.

## “What does 87% confidence mean?”

It is an analytical score/confidence indicator, not a probability of guilt.

## “Are you predicting criminals?”

No. The system provides analytical leads and patterns for human investigation.

## “Why not use a GNN?”

A graph neural network can be added later, but the baseline prioritizes explainability, reproducibility and measurable performance.

## “How do you identify influential individuals?”

Use multiple graph and behavioral signals such as betweenness, degree, cross-community linkage, communications, transactions and temporal behavior.

## “What happens when sources disagree?”

Conflicts remain visible. The system does not silently overwrite contradictory evidence.

## “What happens when data is missing?”

Missing data is explicitly represented as missing/unknown; absence of a record is not automatically interpreted as evidence of absence.

---

# 49. DEVELOPMENT PRIORITY

When time is limited, priority is:

```text
P0 — Mandatory / core

Data contract
Entity resolution
Evidence graph
Graph queries
Time filtering
Key-person analysis
Bridge/pattern detection
Evidence provenance
Investigation canvas
One working AI workflow
Demo scenario

P1 — Strong value

Community comparison
Contradiction handling UI
Advanced anomaly signals
Report export
Workflow versioning

P2 — Optional

Advanced ML/GNN
Complex geospatial views
Additional data connectors
More workflow nodes
Large-scale performance work
```

Never sacrifice the P0 end-to-end flow to build P2 features.

---

# 50. IMPLEMENTATION ORDER

1. Freeze data schema
2. Integrate Vaibhav extraction sample
3. Normalize entities/events
4. Build entity resolution
5. Build evidence graph
6. Build graph search/traversal
7. Build temporal filtering
8. Build key-individual analytics
9. Build bridge/pattern engine
10. Build evidence/provenance
11. Build investigation workflow schema
12. Build workflow execution
13. Build canvas
14. Add AI workflow generation
15. Integrate all components
16. Build synthetic evaluation generator
17. Benchmark
18. Build final demo
19. Documentation
20. Pitch/video/Q&A

The AI layer should not be allowed to become the first dependency.

---

# 51. CURRENT INTEGRATION CONTRACT WITH VAIBHAV

Before integration is considered stable, obtain from Vaibhav:

1. Current extraction JSON/schema
2. Example output on one document
3. Document IDs
4. Page/line/text-span provenance
5. Entity types
6. Event types
7. Relationship types, if any
8. Extraction confidence
9. Supported file types
10. Handling of OCR failures
11. Handling of missing values
12. Handling of dates/timestamps
13. Whether raw and normalized values are both preserved

Once these are known, update this file and freeze the interface version.

Example:

```text
EXTRACTION_CONTRACT_VERSION = v0.1
```

Any breaking change must increment the version.

---

# 52. FILE / API CONTRACT PRINCIPLE

The intelligence module should be able to run without depending directly on Vaibhav's internal implementation.

Bad:

```text
Your module calls Vaibhav's internal NER class directly.
```

Better:

```text
Vaibhav implementation
        ↓
Stable extraction contract
        ↓
Your intelligence engine
```

This allows both teams to develop independently.

---

# 53. FINAL PRODUCT ARCHITECTURE

```text
                         ┌───────────────────────┐
                         │     INVESTIGATOR      │
                         └───────────┬───────────┘
                                     │
                    Natural Language / Manual Workflow
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                     ▼
        ┌───────────────────┐                ┌──────────────────┐
        │  AI WORKFLOW      │                │ WORKFLOW CANVAS  │
        │  AGENT            │                │ React Flow-like  │
        └─────────┬─────────┘                └────────┬─────────┘
                  │                                   │
                  └────────────────┬──────────────────┘
                                   ▼
                       ┌────────────────────────┐
                       │ INVESTIGATION ENGINE   │
                       └────────────┬───────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    ▼               ▼                ▼
              GRAPH SERVICE   TIME SERVICE     PATTERN ENGINE
                    │               │                │
                    └───────────────┼────────────────┘
                                    ▼
                         ┌──────────────────────┐
                         │    EVIDENCE GRAPH    │
                         └──────────┬───────────┘
                                    │
                         ENTITY RESOLUTION
                                    │
                                    ▼
                         NORMALIZED DATA MODEL
                                    │
                              EXTRACTION
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
             STRUCTURED DATA                 DOCUMENT OUTPUT
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
                                 VAIBHAV
```

---

# 54. SUCCESS CRITERIA

The project should be considered successful when the team can demonstrate:

### Functional

- multiple source types
- required entity extraction support
- relationship mapping
- key-individual analysis
- suspicious-pattern detection
- investigator visual analytics

### Analytical

- measurable entity-resolution quality
- measurable ranking/pattern detection quality
- evidence traceability
- temporal analysis
- reproducibility

### AI

- natural-language investigation request
- structured workflow generation
- validation
- execution
- evidence-grounded explanation

### UX

- clean canvas
- readable graph
- timeline
- evidence inspection
- clear status/uncertainty

### Demo

- one deterministic case
- one end-to-end investigation
- one memorable analytical discovery
- underlying evidence shown
- no unsupported claims

---

# 55. CHANGE CONTROL — MANDATORY FROM THIS POINT ON

Whenever we make a major project decision, update this document before moving to implementation.

Major decisions include:

- changing the core product idea
- changing HLD
- changing LLD
- adding/removing a mandatory module
- changing the extraction contract
- changing the graph schema
- selecting a different primary dataset
- changing the AI architecture
- changing the frontend architecture
- changing the principal demo scenario
- adding a major feature
- removing a required PS capability

## Required record

```text
DATE:
DECISION:
WHY:
IMPACT:
AFFECTED SECTIONS:
STATUS:
```

---

# 56. DECISION LOG

## 2026-09-19 — Team 2 project scope

Decision:
Proceed with KAYA PS #13.

Why:
Team selected Criminal Network Analysis as the second KAYA project.

Impact:
All future work uses the official PS #13 requirements as mandatory.

Status:
LOCKED

## 2026-09-19 — Post-extraction responsibility split

Decision:
Vaibhav owns document extraction. The user's module starts from structured extraction output.

Why:
Parallel development and clear ownership.

Impact:
Stable extraction schema is now an integration dependency.

Status:
LOCKED PENDING CONTRACT v0.1

## 2026-09-19 — Product interaction model

Decision:
Use an n8n-style investigation workflow canvas synchronized with an evidence graph.

Why:
The team wants a visual “nodes + pins + threads” investigation experience.

Impact:
Frontend architecture must support workflow nodes separately from graph entities.

Status:
DESIGN BASELINE

## 2026-09-19 — Data strategy

Decision:
Use public/research datasets and documented synthetic scenarios rather than claiming access to sensitive real criminal-investigation data.

Why:
Data availability, legality, reproducibility and evaluation.

Impact:
Every demo dataset must have provenance; synthetic cases must have hidden ground truth.

Status:
LOCKED PRINCIPLE

## 2026-09-19 — Differentiation strategy

Decision:
Do not position the product as “another criminal network graph.”

Focus:
Investigation workflow + evidence provenance + temporal reasoning + uncertainty + AI workflow generation + measurable evaluation.

Status:
LOCKED

## 2026-09-19 — AI safety architecture

Decision:
AI generates structured analytical workflows; deterministic/validated services execute them.

Why:
Reduce hallucinations, improve explainability and reproducibility.

Status:
LOCKED PRINCIPLE

---

# 57. FINAL “DO NOT FORGET” CHECKLIST

Before implementation:

- [ ] Exact official PS is still the source of truth
- [ ] All six required capabilities are represented
- [ ] Vaibhav's extraction contract is known
- [ ] Provenance is preserved
- [ ] Entity resolution is included
- [ ] Evidence graph is included
- [ ] Temporal analysis is included
- [ ] Key-individual analysis is included
- [ ] Suspicious-pattern detection is included
- [ ] Investigator visual analytics is included
- [ ] AI is constrained to validated workflows
- [ ] Uncertainty is explicit
- [ ] Contradictions are preserved
- [ ] Missing data is represented correctly
- [ ] Synthetic data has documented generation and hidden ground truth
- [ ] Public datasets are not misrepresented as criminal datasets
- [ ] Existing products such as i2/DataWalk are acknowledged
- [ ] The product is not pretending to replace them
- [ ] The n8n-style canvas remains separate from the evidence graph
- [ ] The demo has one deterministic investigation scenario
- [ ] Metrics are measured before being claimed
- [ ] The README is updated before major implementation changes

---

# 58. STATUS

Current state:

> **Research complete → architecture/product definition → integration-contract phase → implementation preparation**

Immediate next artifacts to freeze:

1. Vaibhav extraction schema
2. Exact evidence/entity/event schema
3. Neo4j data model
4. Entity-resolution rules
5. Initial analytics API
6. Investigation workflow-node schema
7. Synthetic scenario generator specification
8. Benchmark protocol
9. Frontend information architecture
10. Demo case
11. Final product name



---

# 61. ORIGINAL RESEARCH BASELINE (PRESERVED IN FULL)

# AI-Powered Criminal Network Analysis System

> **KAYA Software Hackathon — Problem Statement #13**
>
> Internal research, architecture, feasibility, data and differentiation document for Team 2.
>
> **Research status:** 18 September 2026
>
> **Important:** This document is a design/research baseline. It does not claim that the proposed system is a novel invention in every individual component. The competitive goal is to combine established graph, NLP, evidence and AI capabilities into a differentiated, auditable investigation workflow.

---

## 1. Project Context

We are participating in the **KAYA Software Hackathon** under **PS #13 — AI-Powered Criminal Network Analysis System**.

KAYA's Software Hackathon currently describes the event around **Cyber Security, Agentic Workflow and Prompt Engineering**. The published submission requirements emphasize a working solution, problem/approach/architecture, a live demo, security considerations and impact. The online submission requires a public GitHub repository and a demo video of up to five minutes; a PDF presentation of up to 10 slides is recommended. Team size is 2–4. The currently published online submission deadline is **20 September 2026**, followed by an online-round result on **30 September 2026** and an offline round on **10–11 October 2026**.  
> Source: https://kaya.azmth.in/events/hackathon/

This project is being developed as a **separate project/team from iTantra (PS #11)**.

---

# 2. Problem Statement Understanding

The broad PS asks for an AI-powered system capable of analyzing criminal networks from fragmented information.

A realistic interpretation is:

```text
FIR / Case Reports / CDR-like Records / Transactions / Locations / Vehicles / Devices / Other Evidence
                                      ↓
                              Entity Extraction
                                      ↓
                              Entity Resolution
                                      ↓
                             Relationship Extraction
                                      ↓
                              Evidence / Knowledge Graph
                                      ↓
                     Network + Temporal + Pattern Analysis
                                      ↓
                          Investigator-facing Intelligence
```

The system is intended as **decision support for investigators**, not as an autonomous system for declaring someone a criminal or making arrest decisions.

---

# 3. The Main Strategic Problem: Crowding

The simplest implementation of PS #13 is very easy to describe:

```text
Upload data
   ↓
Extract people / phone / account / location
   ↓
Put everything in Neo4j
   ↓
Draw graph
   ↓
Run centrality
   ↓
Highlight suspicious nodes
```

This is **not enough** to stand out.

Existing systems already provide substantial capabilities for visual link analysis, temporal analysis, key-individual identification and relationship exploration.

### i2 Analyst's Notebook

i2 explicitly supports modeling and visualizing **entities, links, events and timelines** and includes link-analysis capabilities for identifying key individuals/relationships and temporal patterns. Its documentation also covers common network measures including degree, closeness, betweenness and eigenvector centrality.

Sources:
- https://i2group.com/solutions/i2-analysts-notebook
- https://www.ibm.com/docs/en/SSJSV9_9.2.4/pdf/SSJSV9_pdf.pdf

### DataWalk

DataWalk markets an investigation platform combining graph, AI, data integration, visual queries, link charts, temporal/geospatial analysis, entity resolution and investigative reporting. It describes capabilities for connecting financial, communications, device, public-record and other sources, and for identifying hidden relationships.

Source:
- https://datawalk.com/solutions/investigation/

### Research / open implementations

Criminal-network research is already exploring combinations of NLP, entity extraction, knowledge graphs, graph analysis and LLM-based reasoning. Examples include research on criminal-network knowledge graph construction, multimodal criminal intelligence platforms, and LLM-assisted knowledge-graph construction for human-smuggling/legal text.

Sources:
- https://cina.gmu.edu/projects/using-deep-learning-to-extract-and-analyze-dynamic-knowledge-graphs-of-criminal-networks-from-publicly-available-text/
- https://arxiv.org/abs/2509.26487
- https://arxiv.org/abs/2506.21607
- https://arxiv.org/abs/2510.26486
- https://graphaware.com/blog/combine-knowledge-graphs-and-llms-to-speed-up-criminal-network-analysis-lessons-learned/

### Competitive conclusion

**Do not pitch:**

> "We created a criminal network graph with AI."

**Pitch instead:**

> "We are building an AI-native investigation workspace where analysts can compose, execute and audit multi-step investigations over an evidence-aware temporal graph, with AI turning natural-language investigative questions into transparent analysis workflows."

The individual components are not claimed to be unprecedented; the product experience, evidence model, workflow composition and evaluation methodology are the differentiating focus.

---

# 4. Product Concept

## Working concept

### **Investigative Graph Workflow Canvas**

Think of the product as:

> **n8n-style investigation workflow + evidence graph + AI reasoning + temporal analysis + provenance**

The core idea is to separate two concepts that are often confused:

1. **Evidence Graph** — represents the entities, events and relationships in the case.
2. **Investigation Canvas** — represents what the investigator is doing to analyze that graph.

The canvas is therefore not just a visual network. It is a **programmable investigation workspace**.

---

# 5. Why the n8n / “Thread and Pins” UI Idea Matters

The proposed interface should visually resemble a node-based workflow editor.

Example:

```text
[CASE DATA]
     ↓
[ENTITY EXTRACTION]
     ↓
[ENTITY RESOLUTION]
     ↓
[BUILD GRAPH]
     ↓
[TIME FILTER]
     ↓
[EXPAND NETWORK]
     ↓
[FIND BRIDGES]
     ↓
[ANOMALY ANALYSIS]
     ↓
[RANK CANDIDATES]
     ↓
[EVIDENCE REVIEW]
     ↓
[REPORT]
```

However, the **network graph itself remains a separate synchronized view**.

This gives us:

- a clean workflow editor
- an actual network graph
- a connection between analysis steps and evidence
- reproducibility of how a result was produced
- a visual way for AI to generate an investigation procedure rather than simply returning a paragraph

---

# 6. Core Product Philosophy

## 6.1 Facts must be different from hypotheses

Every relationship/finding should carry a status such as:

```text
OBSERVED
CORRELATED
INFERRED
HYPOTHESIS
```

Example:

```text
Person A ===== Person B

Status: OBSERVED
Evidence: 17 calls
```

versus:

```text
Person A - - - - Person B

Status: INFERRED
Confidence: 0.84
Reasons:
- communication overlap
- location overlap
- shared transaction path
```

The system must never present an inferred association as an established fact.

---

# 7. Evidence-Aware Relationships

The relationship/edge should itself be a rich object rather than a line with a color.

Example:

```text
PERSON A ───────── PERSON B

Relationship type: Communication
Strength: 0.82
Confidence: 0.87

Supporting evidence:
• 17 calls
• 3.4 hours total duration
• 4 overlapping dates
• 6 common tower regions

First observed: 03 Aug 2026
Last observed: 12 Sep 2026

Status: Evidence-backed
```

For inferred links:

```text
PERSON A - - - - PERSON B

Relationship: Potential association
Confidence: 0.71

Supporting signals:
• shared location
• temporal overlap
• common intermediary

Contradictory signals:
• inconsistent address history

Status: Model inference / investigation lead
```

---

# 8. Three Classes of Canvas Nodes

The investigation canvas should support three broad node classes.

## 8.1 Entity Nodes

Examples:

- Person
- Phone
- Account
- Vehicle
- Device
- Location
- Organization
- IP address / digital identifier

## 8.2 Evidence Nodes

Examples:

- Call record
- Transaction
- CCTV observation
- Report
- Chat/message
- Location event
- Device artifact
- Case document

## 8.3 Analysis Nodes

Examples:

- Filter
- Expand
- Correlate
- Compare
- Cluster
- Trace
- Rank
- Detect anomaly
- Verify
- Report

The separation between **evidence/entity nodes** and **analysis/workflow nodes** is important for keeping the product architecture clean.

---

# 9. Core End-to-End Workflow

```text
                         CASE / DATA
                              │
                              ▼
                     DATA INGESTION
                              │
                              ▼
                    ENTITY EXTRACTION
                              │
                              ▼
                    ENTITY RESOLUTION
                              │
                              ▼
                   RELATIONSHIP EXTRACTION
                              │
                              ▼
                      EVIDENCE GRAPH
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
          TIME ENGINE                 GRAPH ENGINE
                │                           │
                └─────────────┬─────────────┘
                              ▼
                 INVESTIGATION CANVAS
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
      AI WORKFLOW AGENT                  HUMAN ANALYST
             │                                 │
             └────────────────┬────────────────┘
                              ▼
                    ANALYTICAL EXECUTION
                              │
                              ▼
                   FINDINGS / HYPOTHESES
                              │
                              ▼
                      EVIDENCE REVIEW
                              │
                              ▼
                    INVESTIGATION REPORT
```

---

# 10. AI Agent Design

The AI should **not** be the forensic engine.

Its job is to help the investigator express and execute analytical intent.

Example user request:

> "Find possible intermediaries connecting Network A and Network B during the last 30 days."

The system should convert this into a workflow:

```text
[30-Day Filter]
       ↓
[Network Expansion]
       ↓
[Community Detection]
       ↓
[Bridge Analysis]
       ↓
[Candidate Ranking]
       ↓
[Evidence Review]
```

The AI can generate the workflow and parameters, but the actual analysis should run through deterministic/validated services.

### Preferred flow

```text
Natural Language
      ↓
Investigation Agent
      ↓
Structured Workflow JSON
      ↓
Schema Validation
      ↓
Allowed-Operation Check
      ↓
Execution Engine
      ↓
Graph / Evidence Services
      ↓
Evidence-backed Result
```

Do not allow the LLM to directly execute arbitrary database/system commands.

---

# 11. The Central Differentiator: Evidence + Workflow + Uncertainty

Our strongest product proposition should be a combination of:

### A. Investigation workflow composition

The investigator can visually build a multi-step analysis.

### B. Evidence-aware graph

Every relationship and conclusion is traceable to underlying records.

### C. Temporal intelligence

Relationships and patterns are evaluated within explicit time windows.

### D. Uncertainty representation

The system distinguishes observed facts from inferred associations.

### E. AI-generated analytical workflows

AI converts investigative intent into an executable, inspectable workflow.

### F. Reproducibility

A result should be reproducible by storing:

- input dataset/version
- workflow definition
- analysis-node parameters
- model/version where applicable
- timestamps
- resulting evidence references

---

# 12. The “Middleman / Bridge” Use Case

A strong demo can focus on detecting a potential intermediary between two groups.

Example:

```text
GROUP A                          GROUP B
A1 ─ A2 ─ A3                  B1 ─ B2 ─ B3
          \                    /
           \                  /
             X
```

Candidate X could be surfaced because of a combination of signals:

- connections to both communities
- communication pattern
- transaction linkage
- location overlap
- temporal overlap
- graph bridge/betweenness characteristics

The system should show:

```text
Candidate: X
Score: 0.84

Supporting evidence
✓ 11 communications
✓ 3 shared locations
✓ 2 linked transaction paths
✓ 4 temporal overlaps

Status: INVESTIGATIVE LEAD
```

Never label the person "criminal" solely because the model ranks them highly.

---

# 13. Temporal Analysis as a First-Class Feature

A criminal/investigative network is not static.

The graph should be queryable by time.

Example:

```text
JAN ─ FEB ─ MAR ─ APR ─ MAY ─ JUN ─ JUL
                 ▲
               selected period
```

The investigator can ask:

- What relationships existed during a specific period?
- Which entities became active only after an event?
- Which connections disappeared?
- Which actor suddenly connected previously separate groups?

Temporal analysis already exists in established tools, so this is **not claimed as our invention**. It is included because it materially improves the investigation workflow and is required for meaningful evidence reasoning.

---

# 14. Data Strategy — The Critical Risk

## 14.1 What we should NOT claim

We should not claim:

> "We trained our model on millions of real Indian FIR/CDR records."

unless we actually have lawful access to such data and can document it.

Real law-enforcement, CDR and financial-investigation datasets are sensitive and generally unavailable to a student hackathon team.

## 14.2 What we SHOULD do

Use a **multi-source evaluation strategy**:

```text
Public research datasets
        +
Domain-specific simulators
        +
Our controlled synthetic investigation scenarios
        ↓
Algorithm validation + end-to-end demo
```

The key is to clearly disclose what each dataset is used for.

---

# 15. Public / Research Datasets We Can Use

## 15.1 Enron Email Network

Stanford SNAP publishes the Enron email communication network. The network covers roughly half a million emails and the summarized network contains:

- **36,692 nodes**
- **183,831 edges**
- Largest weakly connected component: 33,696 nodes

The dataset was originally made public by the Federal Energy Regulatory Commission during its investigation into Enron.

### What we can use it for

- communication graph algorithms
- temporal/interaction analysis
- community detection
- bridge/intermediary analysis
- network visualization

### Important limitation

It is **not a criminal-network dataset**. It validates network-analysis machinery only.

Source:
- https://snap.stanford.edu/data/email-Enron.html

---

## 15.2 IBM AMLSim

IBM AMLSim is specifically designed as a simulator that generates **synthetic banking transaction data together with known money-laundering patterns** for testing machine-learning models and graph algorithms.

This is significantly stronger than manually inventing random financial rows because:

- the generator is documented
- the simulator has configurable scenarios
- known alert patterns can be generated
- the generated output is intended for algorithm research/validation
- the underlying project is public

The project includes transaction/account/party outputs and known alert-related structures.

### What we can use it for

- financial relationship graphs
- money-flow analysis
- suspicious-pattern detection
- graph ML experiments
- anomaly detection
- ground-truth evaluation

### Important limitation

AMLSim data is **synthetic**, not actual law-enforcement banking data.

Source:
- https://github.com/IBM/AMLSim

---

## 15.3 Elliptic Bitcoin Dataset

Elliptic publicly released a labeled dataset containing approximately **200,000 Bitcoin transactions** with a total value described as **$6 billion**. Where known, transactions were labeled licit or illicit. The dataset was released specifically to enable research into illicit cryptocurrency transaction detection.

### What we can use it for

- transaction graphs
- illicit/licit transaction classification experiments
- graph anomaly detection
- financial-network analysis
- benchmarking risk scoring

### Important limitation

This is **cryptocurrency transaction data**, not a complete real-world criminal network and not a substitute for police intelligence data.

Source:
- https://www.elliptic.co/insights/elliptic-dataset-cryptocurrency-financial-crime/

---

## 15.4 UNODC Data Portal

The UNODC Data Portal provides official international crime and justice statistics, including categories such as:

- drug trafficking/cultivation
- intentional homicide
- violent and sexual crime
- corruption and other crime
- prisons/prisoners
- justice systems
- firearms trafficking
- trafficking in persons
- wildlife trafficking

These are useful for **domain context and aggregate statistics**, not for building individual-level relationship graphs.

Source:
- https://data.unodc.org/

---

# 16. The Right Way to Use Synthetic Data

Synthetic data is not automatically weak.

**Undocumented fake data is weak.**

The correct strategy is a **scenario generator with known hidden ground truth**.

Example:

```text
Scenario ID: CRIME-SIM-0042
Seed: 847213

Entities:
50 persons
30 phones
20 accounts
12 locations
8 vehicles
4 organizations

Events:
2,000 calls
800 transactions
200 location events
50 case/report records
```

Then intentionally inject known patterns:

- hidden intermediary
- duplicate identity
- suspicious transaction chain
- shared communication hub
- cross-community bridge
- temporal coordination
- contradictory records
- missing evidence

The ground-truth generator keeps the answer hidden from the analytics engine.

Then:

```text
Ground Truth
      ↓
Hide labels from model
      ↓
Run investigation
      ↓
Predictions / candidates
      ↓
Compare against ground truth
```

This allows us to report objective metrics rather than demonstrating a hand-made story with a predetermined answer.

---

# 17. Dataset Provenance Record

Every dataset/scenario used in the system should have a metadata record such as:

```json
{
  "dataset_id": "CRIME-SIM-0042",
  "source_type": "synthetic_scenario",
  "generator": "internal_scenario_generator",
  "generator_version": "0.1.0",
  "seed": 847213,
  "created_at": "2026-09-18T00:00:00Z",
  "scenario": "cross_network_intermediary",
  "ground_truth_available": true,
  "ground_truth_visible_to_model": false
}
```

For public datasets, store:

- dataset name
- publisher
- URL
- access date
- license/terms as applicable
- exact preprocessing steps
- local transformed version/hash where possible

This is how we answer judges when asked:

> "Where did your data come from?"

without hand-waving.

---

# 18. “Training Data” Strategy

## We do not need to train a giant model from scratch.

The system can combine:

```text
Pretrained NLP model
        +
Rules / deterministic extraction
        +
Entity resolution model / scoring
        +
Graph algorithms
        +
Anomaly detection
        +
LLM for workflow generation
```

### NLP / entity extraction

Use a pretrained NER-capable model plus domain rules.

Example:

```text
"Ravi Kumar contacted 9876543210 from Kanpur on 12 August."

PERSON    → Ravi Kumar
PHONE     → 9876543210
LOCATION  → Kanpur
DATE      → 12 August
```

### Entity resolution

Combine signals such as:

- name similarity
- phone overlap
- address similarity
- identifier overlap
- temporal consistency
- shared contacts
- shared locations

Possible first implementation:

```text
Entity Match Score =
  weighted(name similarity)
+ weighted(phone/identifier evidence)
+ weighted(location similarity)
+ weighted(temporal consistency)
+ weighted(shared-neighbor evidence)
```

The weights should be configurable and explainable.

### Graph analytics

Most core analytics do **not require model training**:

- degree centrality
- betweenness centrality
- closeness
- eigenvector centrality
- shortest paths
- connected components
- community detection
- temporal activity statistics

These are established network-analysis methods and are documented in tools such as i2 Analyst's Notebook.

### Anomaly detection

Potential lightweight approaches:

- Isolation Forest
- Local Outlier Factor
- statistical baselines
- graph-structure deviations

### Optional advanced ML

A GNN or learned edge-risk model can be explored **only after the non-ML baseline is working**.

Do not make a GNN the foundation of the MVP if the team cannot explain it in Q&A.

---

# 19. Proposed Analytical Signals

For a potential relationship or investigative lead, the system can aggregate:

```text
Communication evidence
Location overlap
Transaction connectivity
Temporal overlap
Graph topology
Cross-community connectivity
Shared infrastructure
Repeated co-occurrence
Identity-resolution confidence
Contradictory evidence
```

Example transparent scoring model:

```text
Candidate Score =
    35% bridge/connectivity signal
  + 25% communication signal
  + 20% transaction signal
  + 10% location signal
  + 10% temporal signal
```

These percentages are **initial design values only**, not validated results. They should be tuned experimentally and reported honestly.

---

# 20. HLD — High-Level Design

```text
┌─────────────────────────────────────────────────────┐
│                 INVESTIGATION UI                    │
│                                                     │
│ Workflow Canvas | Evidence Graph | Timeline | Chat  │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│              INVESTIGATION ORCHESTRATOR             │
│  Workflow validation • execution • state tracking   │
└───────────────┬──────────────────────┬──────────────┘
                │                      │
                ▼                      ▼
┌─────────────────────┐       ┌──────────────────────┐
│ AI INVESTIGATION     │       │ GRAPH ANALYTICS      │
│ AGENT                │       │                      │
│ NL → Workflow        │       │ centrality           │
│ explanation          │       │ communities          │
│ hypothesis assist    │       │ temporal analysis    │
└──────────┬──────────┘       │ bridge analysis      │
           │                  │ anomaly detection    │
           │                  └──────────┬───────────┘
           │                             │
           └──────────────┬──────────────┘
                          ▼
┌─────────────────────────────────────────────────────┐
│                   EVIDENCE GRAPH                     │
│ entities • events • relationships • sources • time │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│             ENTITY / RELATIONSHIP LAYER             │
│ extraction • normalization • resolution • linking   │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  DATA INGESTION                      │
│ CSV • JSON • reports • generated scenarios          │
└─────────────────────────────────────────────────────┘
```

---

# 21. LLD — Low-Level Design Direction

The MVP can be structured as a **modular monolith**, not microservices.

```text
criminal-network-analysis/
│
├── frontend/
│   ├── canvas/
│   ├── graph-view/
│   ├── timeline/
│   ├── evidence-panel/
│   └── investigator-chat/
│
├── backend/
│   ├── api/
│   ├── orchestration/
│   ├── workflow/
│   ├── ai/
│   ├── graph/
│   ├── evidence/
│   ├── entity-resolution/
│   ├── nlp/
│   ├── analytics/
│   ├── provenance/
│   └── reporting/
│
├── data/
│   ├── public/
│   ├── synthetic/
│   └── schemas/
│
└── tests/
```

### Example internal object flow

```text
WorkflowDefinition
        ↓
WorkflowValidator
        ↓
WorkflowExecutor
        ↓
AnalysisNode
        ↓
GraphService / EvidenceService
        ↓
Finding
        ↓
EvidenceReference[]
        ↓
InvestigationReport
```

The detailed class diagram should only be created after the core MVP workflow is frozen.

---

# 22. Suggested Technology Stack

## Frontend

- **React + TypeScript**
- **React Flow** (or equivalent) for the n8n-style investigation workflow canvas
- **Cytoscape.js** (or equivalent) for the evidence/network graph
- Lightweight chart/timeline library where necessary

## Backend

- **Python + FastAPI**

## Graph

- **Neo4j** for graph storage and traversal
- **NetworkX** / graph algorithms for local analytical operations where appropriate

## NLP / ML

- Python
- Transformers / spaCy or another suitable open model for extraction
- RapidFuzz / similarity methods for entity resolution
- scikit-learn for lightweight anomaly models
- Optional PyTorch for more advanced ML only after baseline completion

## AI

- LLM/agent layer for converting natural-language investigator requests into a structured workflow
- Prefer controlled tool/function calling or structured JSON output
- Keep graph/evidence operations deterministic and validated

## Storage

- Neo4j for network/evidence relationships
- A relational store can be added only if needed for user/case metadata; avoid unnecessary infrastructure in the MVP

---

# 23. Proposed Data Model

## Entity types

```text
Person
Phone
Account
Vehicle
Device
Location
Organization
DigitalIdentifier
Case
```

## Event/evidence types

```text
Call
Transaction
Meeting
LocationEvent
Document
CCTVObservation
Message
DeviceArtifact
```

## Relationship examples

```text
PERSON ──OWNS──> PHONE
PERSON ──USES──> ACCOUNT
PERSON ──DRIVES──> VEHICLE
PERSON ──LOCATED_AT──> LOCATION
PERSON ──CALLED──> PERSON
PERSON ──TRANSFERRED_TO──> ACCOUNT
PERSON ──ASSOCIATED_WITH──> PERSON
CASE ──CONTAINS──> EVIDENCE
EVIDENCE ──SUPPORTS──> RELATIONSHIP
```

## Relationship metadata

Every edge should support fields such as:

```text
type
confidence
strength
first_seen
last_seen
source_ids
status
inference_method
supporting_signals
contradicting_signals
```

---

# 24. Evidence Provenance

This is a high-priority feature.

Every finding should be able to answer:

> **Why does the system believe this?**

Example:

```text
Finding #17
──────────────────────────────
Potential bridge entity: P17

Derived from:
├── 11 communication records
├── 3 location events
├── 2 transaction paths
└── 4 temporal overlaps

Model / rule version:
bridge-score-v0.1

Status:
Investigative lead
```

The user should be able to click evidence references and inspect the underlying record.

---

# 25. Contradiction Handling

We should intentionally model conflicting evidence because real-world investigation data is noisy.

Example:

```text
Source A:
P17 → Location: Lucknow

Source B:
P17 → Location: Kanpur

Status:
CONFLICT

Reason:
Conflicting observations in overlapping time window
```

Instead of hiding the conflict, the system should surface it.

This makes the project feel much closer to a genuine investigative environment than a clean classroom graph.

---

# 26. Entity Resolution Example

Input:

```text
Ravi Kumar
R. Kumar
Ravi K.
+91-98XXXXXX10
```

The system should produce:

```text
Canonical Entity: PERSON_017

Aliases:
- Ravi Kumar
- R. Kumar
- Ravi K.

Linked identifiers:
- phone hash / identifier

Resolution confidence: 0.91

Evidence:
✓ phone overlap
✓ name similarity
✓ address consistency
✓ temporal overlap
```

Do not silently merge records. Store the evidence for the merge decision.

---

# 27. Investigation Canvas Behaviour

### Node operations

- Add node
- Remove node
- Connect node
- Configure node
- Duplicate node
- Expand neighbors
- Run node
- Disable node
- View input/output

### Workflow operations

- Run selected node
- Run entire workflow
- Pause
- Inspect intermediate result
- Re-run from node
- Save workflow
- Version workflow

### Graph operations

- Search entity
- Filter by type
- Filter by time
- Filter by confidence
- Filter by evidence status
- Expand 1/2/3 hops
- Focus neighborhood
- Compare communities

---

# 28. AI Workflow Example

### Investigator request

> "Show me people who connect the two groups, only use evidence from the last 30 days, and include their strongest supporting evidence."

### AI output (conceptual)

```json
{
  "workflow": [
    {"node": "time_filter", "days": 30},
    {"node": "community_select", "groups": ["A", "B"]},
    {"node": "bridge_analysis"},
    {"node": "rank_candidates"},
    {"node": "attach_evidence"}
  ]
}
```

The workflow is validated before execution.

---

# 29. Demo Scenario

A strong demo should use **one controlled case**, not a giant dataset.

Recommended scale for the primary demo:

- roughly 50–200 entities visible in the scenario
- hundreds/thousands of events underneath
- only relevant subgraphs shown initially

### Demo flow

#### Step 1 — Load case

Load a synthetic investigation case with:

- people
- phones
- accounts
- locations
- transactions
- calls
- case reports

#### Step 2 — Extract / resolve

Show duplicate or noisy identities being resolved.

#### Step 3 — Build evidence graph

Show the network emerging.

#### Step 4 — Investigator question

> "Find possible intermediaries connecting Group A and Group B during the last 30 days."

#### Step 5 — AI generates workflow

The canvas automatically populates with analysis nodes.

#### Step 6 — Execute

The graph changes and candidate entities are highlighted.

#### Step 7 — Inspect evidence

Click the strongest candidate.

Show:

```text
Confidence
Evidence
Contradictions
Timeline
Supporting records
```

#### Step 8 — Evidence review

The investigator can inspect the actual underlying records.

#### Step 9 — Report

Generate an evidence-backed report that clearly labels inferred conclusions as leads/hypotheses.

---

# 30. Evaluation Strategy

We should not rely only on visual demonstrations.

## Entity resolution

Measure:

- precision
- recall
- F1

## Hidden-relationship / bridge detection

Measure:

- Precision@K
- Recall@K
- ranking quality (e.g., NDCG)

## Anomaly detection

Measure:

- precision
- recall
- false-positive rate

## Workflow execution

Measure:

- workflow completion time
- graph-query latency
- analytical node latency

## Explainability

Measure/verify that:

- every inference has evidence references
- every score has traceable contributing signals
- contradictions are exposed rather than silently ignored

These metrics are **evaluation plans**, not achieved results until we actually run experiments.

---

# 31. Ground-Truth Evaluation Design

This is the cleanest answer to the "synthetic data isn't credible" concern.

```text
Scenario Generator
      ↓
Creates true relationships and planted patterns
      ↓
Hide planted labels
      ↓
Run system
      ↓
Rank / predict candidates
      ↓
Compare against hidden truth
      ↓
Report objective metrics
```

Example:

```text
Ground-truth intermediary: P17

System ranking:
1. P17  → 0.91
2. P04  → 0.67
3. P33  → 0.52

Result:
Ground truth appears at Rank #1
```

This can be repeated with multiple random seeds and scenarios.

---

# 32. Public Dataset + Synthetic Scenario Split

The strongest evaluation story is likely:

### Public datasets
Used to validate specific components:

```text
Enron
→ communication-network algorithms

AMLSim
→ transaction / AML graph analysis

Elliptic
→ illicit transaction / financial graph analysis
```

### Controlled synthetic cases
Used to validate the integrated criminal-investigation workflow:

```text
Scenario generator
→ entity noise
→ temporal behavior
→ planted hidden links
→ contradictions
→ missing records
→ ground truth
```

This is much more defensible than claiming that one public dataset represents the entire criminal-investigation problem.

---

# 33. Security & Privacy Principles

The product should be designed as an **authorized investigative decision-support system**.

Principles:

- Human-in-the-loop
- Evidence traceability
- Least-privilege data access
- Role-based case access where needed
- Audit logging
- No automatic arrest or guilt determination
- Clear separation of observed evidence and model inference
- Synthetic/demo data separated from real data
- Do not expose sensitive real-person data in the demo

### AI safety principle

The AI may:

- generate analytical workflows
- summarize evidence
- explain graph findings
- suggest hypotheses

The AI should not autonomously:

- declare guilt
- initiate enforcement actions
- silently merge uncertain identities
- create unsupported relationships

---

# 34. Main Risks and Mitigations

## Risk 1 — Crowding

**Problem:** Many teams can produce graph visualizations.

**Mitigation:** Make the investigation workflow + evidence provenance + uncertainty model the core product story.

---

## Risk 2 — Data availability

**Problem:** No authentic student-accessible FIR/CDR/banking investigation corpus.

**Mitigation:** Use public research datasets for subsystem validation and a controlled synthetic scenario generator with documented generation rules and hidden ground truth.

---

## Risk 3 — Synthetic data looks fake

**Problem:** Clean/random rows are easy for judges to identify as artificial.

**Mitigation:** Introduce realistic structure and noise:

- aliases
- duplicate identifiers
- missing data
- conflicting locations
- time patterns
- multi-hop relationships
- seeded hidden communities

Document exactly how scenarios are generated.

---

## Risk 4 — NLP quality

**Problem:** General NER may make obvious mistakes.

**Mitigation:** Hybrid extraction:

```text
pretrained NER
+
regex / domain rules
+
normalization
+
entity-resolution scoring
```

Keep demo text constrained and verifiable.

---

## Risk 5 — Scope creep

**Problem:** The PS covers extraction, graphs, key-player detection, anomaly detection and visualization.

**Mitigation:** Build one excellent end-to-end path first.

MVP path:

```text
Data
→ Entity extraction
→ Entity resolution
→ Graph
→ Temporal filter
→ Bridge / anomaly analysis
→ Evidence review
→ Report
```

Everything else is secondary.

---

## Risk 6 — Explainability

**Problem:** A black-box model can be hard to defend.

**Mitigation:** Make the first version transparent. Use graph measures + explicit signal aggregation. Add deeper ML only if the team fully understands it.

---

## Risk 7 — Demo instability

**Problem:** Large graphs become unreadable; layout can fail.

**Mitigation:**

- show focused subgraphs
- lazy-expand neighbors
- filter aggressively
- keep the main demo deterministic
- precompute heavy processing where appropriate
- always have a known-good demo case

---

## Risk 8 — Ethical/sensitivity concerns

**Problem:** A model can appear to accuse real people.

**Mitigation:** Use fictional entities and state clearly:

> "The system provides evidence-backed investigative leads. It does not determine guilt or replace human judgment."

---

# 35. What We Are NOT Building

To control scope, the MVP does not attempt to be:

- a replacement for i2 Analyst's Notebook
- a replacement for DataWalk
- a complete law-enforcement case-management system
- a complete digital-forensics suite
- a universal NER model
- a perfect criminal-prediction engine
- an autonomous arrest / enforcement system
- a surveillance platform for unrestricted real-world deployment
- a giant proprietary LLM trained from scratch

---

# 36. MVP Definition

The MVP is successful when all of the following work together:

```text
1. Load case data
2. Extract entities
3. Resolve duplicate/noisy entities
4. Build evidence graph
5. Apply time filtering
6. Run graph analysis
7. Detect at least one meaningful planted pattern
8. Show supporting evidence
9. Allow investigator to inspect the reasoning path
10. Generate/save an investigation workflow
11. Produce an evidence-backed report
```

---

# 37. “Winning” Product Story

The project should not be sold as:

> **"A graph that finds criminals."**

A stronger and more defensible statement is:

> **"An AI-native investigative workspace for turning fragmented evidence into auditable, time-aware network intelligence."**

Possible one-line value proposition:

> **Connect the evidence. Build the investigation. Challenge the inference. Trace every conclusion.**

---

# 38. Suggested Product Modules

## Module 1 — Case Manager

- create case
- upload data
- dataset metadata
- scenario information

## Module 2 — Ingestion

- CSV
- JSON
- text/report data
- generated scenario data

## Module 3 — NLP / Extraction

- entities
- dates
- identifiers
- relationships

## Module 4 — Entity Resolution

- aliases
- duplicates
- merge suggestions
- confidence

## Module 5 — Evidence Graph

- graph storage
- relationship metadata
- sources
- timestamps

## Module 6 — Investigation Canvas

- analysis nodes
- pins/connections
- workflow save/load
- execution

## Module 7 — Graph Analytics

- centrality
- communities
- bridge analysis
- shortest path
- temporal patterns
- anomaly scoring

## Module 8 — AI Investigation Agent

- natural-language investigation requests
- workflow generation
- explanation
- hypothesis suggestions

## Module 9 — Evidence Inspector

- source records
- relationship support
- contradictions
- provenance

## Module 10 — Reporting

- case summary
- findings
- evidence references
- uncertainty statements
- workflow version

---

# 39. Team Development Priorities

If the team has 4 members, a practical split is:

### Member A — Frontend / Canvas

- React
- workflow canvas
- graph visualization
- timeline
- evidence panel

### Member B — Backend / Graph

- FastAPI
- Neo4j schema
- graph queries
- workflow executor

### Member C — AI / NLP / Analytics

- extraction
- entity resolution
- anomaly/bridge scoring
- AI workflow generation

### Member D — Data / Evaluation / Integration

- public datasets
- scenario generator
- ground truth
- testing
- benchmark metrics
- integration and demo

For 3 people, combine Data/Evaluation with Backend or AI depending on team strengths.

---

# 40. Suggested Implementation Order

## Phase 1 — Core data model

Freeze:

- node types
- relationship types
- evidence schema
- timestamps

## Phase 2 — Graph foundation

- ingest sample data
- create graph
- search/expand/filter

## Phase 3 — Entity resolution

- aliases
- duplicate detection
- confidence

## Phase 4 — Analytics

- centrality
- communities
- bridge candidates
- temporal analysis

## Phase 5 — Investigation canvas

- analysis nodes
- workflow execution

## Phase 6 — Evidence/provenance

- supporting records
- inference status
- contradictions

## Phase 7 — AI

- NL → workflow
- explanation

## Phase 8 — Demo + benchmark

- seeded scenario
- hidden ground truth
- evaluation results

The order is intentional: **the AI layer comes after the deterministic analytical core exists.**

---

# 41. Judge Questions We Should Be Ready For

## Q1. “Isn't this just Neo4j?”

**Answer:**

No. Neo4j is a graph storage/query component. Our application builds an investigator-facing workflow layer around an evidence graph, with temporal analysis, provenance, uncertainty handling and AI-generated analytical workflows.

## Q2. “How is this different from i2 Analyst's Notebook?”

**Answer:**

i2 already provides mature link-analysis and temporal-analysis capabilities. We are not claiming to replace it. Our focus is an AI-native workflow model where a natural-language investigative question can become a transparent, executable analysis workflow whose findings remain linked to evidence and uncertainty.

## Q3. “Where is your data from?”

**Answer:**

We use public research datasets such as Enron for communication-network validation, IBM AMLSim for synthetic financial-crime pattern generation, and the Elliptic dataset for illicit-transaction graph experiments. For our integrated demo we use a documented, seed-controlled synthetic investigation generator with hidden ground truth so that we can objectively evaluate discovery performance.

## Q4. “Why synthetic data?”

**Answer:**

Because authentic case-level police/CDR/financial investigation data is sensitive and is not appropriate to fabricate or claim to possess. We make this explicit and use public datasets for component validation. Our synthetic cases are generated with known hidden ground truth so we can measure whether the system actually recovers planted structures.

## Q5. “How do you prevent AI hallucinations?”

**Answer:**

The AI does not directly invent graph facts or execute arbitrary commands. It generates a structured investigation workflow that is validated and then executed against the evidence graph. Findings must reference underlying evidence.

## Q6. “Why should we trust an 87% confidence score?”

**Answer:**

It is not a probability of guilt. It is an analytical confidence/lead score based on explicit signals and supporting/contradictory evidence. The UI shows how the score was formed and labels the result as an investigative lead.

## Q7. “Are you predicting criminals?”

**Answer:**

No. The system identifies patterns, relationships and investigative leads. It does not make legal determinations or automate enforcement decisions.

## Q8. “Why not just use a GNN?”

**Answer:**

A graph neural network can be added later, but our first version prioritizes explainability and reproducibility. Established graph analytics give us strong baselines that judges and investigators can understand.

## Q9. “What is the real innovation?”

**Answer:**

The innovation focus is the combination of an evidence-aware temporal graph with an AI-generated investigation workflow and explicit distinction between observed evidence, correlation, inference and hypothesis, with reproducible provenance.

## Q10. “How do you know your detector works?”

**Answer:**

Our controlled scenarios have hidden ground truth. The system's predictions are evaluated using precision/recall/ranking metrics instead of being judged only by a visual demo.

---

# 42. What Would Make the Project Weak

Avoid these failure modes:

```text
❌ Static graph only
❌ Generic LLM chatbot
❌ Random synthetic CSVs with no provenance
❌ Black-box “risk score” with no explanation
❌ Claims about real criminal data that we do not possess
❌ GNN added only for buzzwords
❌ Thousands of nodes rendered at once
❌ Uncontrolled AI database access
❌ Automatic labeling of people as criminals
```

---

# 43. What Would Make It Strong

Aim for:

```text
✅ Interactive investigation canvas
✅ Evidence graph underneath it
✅ Time-aware analysis
✅ Entity resolution with evidence
✅ Hidden-link / bridge analysis
✅ Controlled anomaly detection
✅ Natural language → analytical workflow
✅ Every finding linked to evidence
✅ Explicit uncertainty / contradiction handling
✅ Seeded scenario generator
✅ Hidden ground-truth evaluation
✅ Reproducible workflows
✅ Professional, focused demo
```

---

# 44. Recommended Final Product Flow

```text
                         INVESTIGATOR
                              │
                     Natural-language request
                              │
                              ▼
                     ┌─────────────────┐
                     │    AI AGENT     │
                     └────────┬────────┘
                              │
                      Workflow definition
                              │
                              ▼
                     ┌─────────────────┐
                     │ VALIDATOR       │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ INVESTIGATION   │
                     │    CANVAS       │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ EXECUTION       │
                     │ ENGINE          │
                     └────────┬────────┘
                              │
               ┌──────────────┼───────────────┐
               ▼              ▼               ▼
          Graph Query     Temporal       Anomaly /
          / Traversal     Analysis       Bridge Analysis
               │              │               │
               └──────────────┼───────────────┘
                              ▼
                     ┌─────────────────┐
                     │ FINDINGS        │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ EVIDENCE        │
                     │ REVIEW          │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ REPORT          │
                     └─────────────────┘
```

---

# 45. Current Research Conclusions

### Conclusion 1

**PS #13 is feasible**, but a basic graph dashboard is not strategically strong enough.

### Conclusion 2

**i2 Analyst's Notebook and DataWalk confirm that traditional link-analysis, temporal analysis, entity/relationship modeling and investigative graph visualization are already mature capabilities.**

### Conclusion 3

The project's differentiator should therefore be **workflow-centric, AI-assisted investigation over an evidence-aware graph**, not graph visualization alone.

### Conclusion 4

**Synthetic data is acceptable when it is transparent, documented, reproducible and evaluated against known hidden ground truth.** IBM AMLSim is an important reference because it explicitly exists to generate synthetic banking data with known money-laundering patterns for research. 

### Conclusion 5

**We do not need a custom giant criminal LLM.** The first system can be built from pretrained extraction models, deterministic/entity-resolution logic, graph algorithms, lightweight anomaly detection and a controlled AI workflow layer.

### Conclusion 6

**Entity resolution is a core technical challenge.** A large amount of practical value comes from correctly deciding when different records likely refer to the same real-world entity and showing the evidence behind that decision.

### Conclusion 7

**Explainability must be built into the data model**, not bolted onto the UI after the analytical result has already been produced.

### Conclusion 8

**The UI concept should separate the evidence graph from the investigation workflow canvas.** This preserves the n8n-like interaction idea without pretending that entity graphs and workflow nodes are the same thing.

---

# 46. Final Product Definition

## Working title

**[To be finalized]**

## Product category

AI-powered investigative intelligence / graph analytics / evidence reasoning

## Core statement

> **An AI-native investigation workspace that turns fragmented, uncertain and time-dependent evidence into an auditable criminal-network analysis workflow.**

## Primary differentiators

1. **Investigation Canvas** — n8n-style visual composition of analytical steps.
2. **Evidence-aware Graph** — relationships retain provenance, timestamps, support and confidence.
3. **Uncertainty Model** — observed facts are clearly separated from correlations, inferences and hypotheses.
4. **AI Workflow Generation** — natural-language investigative requests become structured, inspectable analytical workflows.
5. **Ground-Truth Evaluation** — seed-controlled synthetic scenarios allow objective measurement instead of purely visual claims.

---

# 47. Source Register

## KAYA

- KAYA Software Hackathon: https://kaya.azmth.in/events/hackathon/

## i2 Analyst's Notebook

- i2 product overview: https://i2group.com/solutions/i2-analysts-notebook
- IBM i2 documentation: https://www.ibm.com/docs/en/SSJSV9_9.2.4/pdf/SSJSV9_pdf.pdf

## DataWalk

- Investigation platform: https://datawalk.com/solutions/investigation/

## Stanford SNAP

- Enron email network: https://snap.stanford.edu/data/email-Enron.html
- SNAP dataset index: https://snap.stanford.edu/data/

## IBM AMLSim

- Repository and methodology: https://github.com/IBM/AMLSim

## Elliptic

- Elliptic dataset article: https://www.elliptic.co/insights/elliptic-dataset-cryptocurrency-financial-crime/
- Elliptic dataset / AML research context: https://www.elliptic.co/newsroom/ibm-mit-and-elliptic-release/

## UNODC

- UNODC Data Portal: https://data.unodc.org/

## Research / prior art

- GMU criminal-network project: https://cina.gmu.edu/projects/using-deep-learning-to-extract-and-analyze-dynamic-knowledge-graphs-of-criminal-networks-from-publicly-available-text/
- Criminal investigation KG + NLP: https://arxiv.org/abs/2509.26487
- CORE-KG: https://arxiv.org/abs/2506.21607
- LINK-KG: https://arxiv.org/abs/2510.26486
- GraphAware criminal network + KG/LLM series: https://graphaware.com/blog/combine-knowledge-graphs-and-llms-to-speed-up-criminal-network-analysis-lessons-learned/
- GraphAware technical implementation: https://graphaware.com/blog/combine-knowledge-graphs-and-llms-to-speed-up-criminal-network-analysis-technical-implementation-details/

---

# 48. Team Rule Going Forward

Before implementing a major feature, ask:

> **Does this improve the core investigation workflow, evidence quality, analytical validity, or judge-visible technical depth?**

If not, it should probably wait.

The project should optimize for a **credible, measurable, end-to-end investigation experience**, not for the number of buzzwords or screens.

---

# 49. Verified Integration Baseline — Clarity Handoff

This section was added before implementing the post-extraction intelligence layer.

## 49.1 Verified Clarity repository boundary

Vaibhav's `Clarity` repository already contains:

- `Clarity/contract/schemas.py` — Pydantic graph-contract models
- `Clarity/contract/transformer.py` — document/case graph-contract builders
- `Clarity/api/routes.py` — graph-contract API endpoints
- `tests/test_graph_contract.py` — contract/API tests
- an existing Next.js frontend with `NetworkGraphView`, `ForensicAnalyticsView`, and `GeospatialMapView`

The currently exposed graph-contract endpoints are:

```text
GET /api/v1/documents/{document_id}/graph-contract
GET /api/v1/cases/{case_id}/graph-contract
```

Clarity also exposes a headless extraction endpoint:

```text
POST /api/v1/engine/extract
```

The downstream intelligence layer must consume the graph contract rather than coupling itself to Clarity's internal OCR/VLM/database implementation.

## 49.2 Verified Graph Contract fields

The current contract contains:

```text
GraphContractResponse
├── contract_version
├── case_id
├── batch_id
├── total_documents
├── entities[]
├── events[]
├── relationships[]
└── audit_chain{}
```

Entities currently carry:

```text
id
 type
 name
 normalized_name
 role
 attributes{}
 confidence
 source{}
```

Current entity types include:

```text
PERSON
PHONE
ACCOUNT
LOCATION
ORGANIZATION
VEHICLE
WEAPON
IDENTIFIER
OTHER
```

Events currently carry:

```text
id
type
title
source_entity
target_entity
timestamp
timestamp_start
timestamp_end
attributes{}
source{}
```

Relationships currently carry:

```text
id
source_entity
target_entity
relationship_type
confidence
evidence
```

Source traceability currently contains:

```text
document_id
filename
file_hash_sha256
page
bounding_box?
text_span?
```

The current Clarity relationship contract does not itself contain a structured source-document reference. The intelligence layer must not fabricate relationship provenance. It may preserve the relationship's textual `evidence` and use actual entity/event source references only where the linkage is objectively derivable.

## 49.3 Verified Clarity limitations relevant to our module

The current case transformer performs cross-document entity reconciliation primarily by:

```text
type + normalized_name
```

The current relationship synthesis is deterministic and includes relationship types such as:

```text
ACCOUNT_HOLDER
COMPLAINANT_OF
VICTIM_OF
ACCUSED_IN
DEBITED_IN
```

Therefore our intelligence layer must add—not duplicate—richer investigative capabilities such as:

- stronger entity-resolution evidence and unresolved states
- relationship/event enrichment
- temporal network construction
- graph analytics
- bridge/intermediary analysis
- anomaly/pattern analysis
- evidence-aware findings
- investigator workflow execution

## 49.4 First implementation decision: GraphContractAdapter

Before Neo4j, ML, or the investigation canvas, the first implementation layer is a `GraphContractAdapter`.

Purpose:

```text
Clarity GraphContractResponse / JSON
        ↓
GraphContractAdapter
        ↓
Canonical Investigation Model
```

The adapter is responsible for:

1. validating the incoming contract;
2. preserving raw IDs and provenance;
3. normalizing the contract into stable internal models;
4. supporting relationships that point to either entities or events;
5. detecting dangling relationship endpoints rather than silently dropping them;
6. preserving audit-chain metadata;
7. remaining independent of Neo4j/UI/AI implementation details.

The adapter must not:

- perform fuzzy entity merging;
- invent relationship evidence;
- infer criminality;
- execute graph analytics;
- call an LLM;
- write directly to the UI.

Those concerns belong to later layers.

## 49.5 Canonical model rules

The internal model will distinguish:

```text
Entity
Event
Relationship
EvidenceReference
InvestigationGraph
```

Each source-backed object retains enough provenance to trace it back to Clarity's evidence contract.

Relationship status starts as `OBSERVED` for a contract-provided relationship. Later inference stages may create `CORRELATED`, `INFERRED`, or `HYPOTHESIS` relationships/findings. This status must never be used to imply legal guilt.

## 49.6 Integration acceptance criteria

The first adapter milestone is complete only when:

- a valid Clarity contract object can be converted deterministically;
- the same conversion works from JSON/dict payloads;
- entity/event/relationship IDs are preserved;
- event endpoints in relationships are supported;
- source traceability survives conversion;
- audit-chain metadata survives conversion;
- dangling relationship endpoints are reported explicitly;
- no evidence is silently invented or discarded;
- unit tests cover valid, invalid, event-linked, and provenance cases.

## 49.7 Change-control rule

Any change to the Clarity handoff schema, canonical internal model, or ownership boundary must be recorded here before/with implementation.

## Status

**Research phase → Architecture definition → MVP implementation**

Next design artifacts to freeze:

1. Exact feature list
2. Exact HLD
3. Exact LLD
4. Neo4j data model
5. Investigation workflow node schema
6. Synthetic scenario schema + generator rules
7. Benchmark protocol
8. Demo case
9. Final product name
10. Team work split



---

# MASTER CONTEXT ADDENDUM — SOURCE/RESEARCH INTEGRITY

This project context intentionally preserves a critical distinction:

- official KAYA requirements are mandatory scope;
- existing commercial/research capabilities are prior art;
- proposed features are design choices;
- example scores are illustrative until benchmarked;
- synthetic data is acceptable only when transparently documented;
- model output is an analytical lead, not a legal conclusion.

## Current KAYA event source

Official KAYA Software Hackathon page:

https://kaya.azmth.in/events/hackathon/

Current published page lists the Software Hackathon as a 2–4 person event and currently shows the online submission deadline as 20 September 2026, with the offline round scheduled for 10–11 October 2026. These event details can change; verify the official page before any submission-critical decision.

Official problem-statements page:

https://kaya.azmth.in/problem-statements/

## Source register retained from the research baseline

### KAYA
- https://kaya.azmth.in/events/hackathon/
- https://kaya.azmth.in/problem-statements/

### i2 Analyst's Notebook
- https://i2group.com/solutions/i2-analysts-notebook
- https://www.ibm.com/docs/

### DataWalk
- https://datawalk.com/solutions/investigation/

### Stanford SNAP
- https://snap.stanford.edu/data/email-Enron.html
- https://snap.stanford.edu/data/

### IBM AMLSim
- https://github.com/IBM/AMLSim

### IBM AML Data
- https://github.com/IBM/AML-Data

### Elliptic
- https://www.elliptic.co/insights/elliptic-dataset-cryptocurrency-financial-crime/

### UNODC
- https://data.unodc.org/

### Research / prior-art references retained from the earlier baseline
- https://cina.gmu.edu/projects/using-deep-learning-to-extract-and-analyze-dynamic-knowledge-graphs-of-criminal-networks-from-publicly-available-text/
- https://arxiv.org/abs/2509.26487
- https://arxiv.org/abs/2506.21607
- https://arxiv.org/abs/2510.26486
- https://graphaware.com/blog/combine-knowledge-graphs-and-llms-to-speed-up-criminal-network-analysis-lessons-learned/
- https://graphaware.com/blog/combine-knowledge-graphs-and-llms-to-speed-up-criminal-network-analysis-technical-implementation-details/

## Source-validation rule

Before using a source to make a strong external claim in the final pitch, README or judge answer:

1. Open the source.
2. Verify the exact claim.
3. Record the source URL and relevant version/date.
4. Avoid stronger language than the source supports.

---

# 59. IMPLEMENTATION GATE

Do not start major implementation work until the following are frozen:

```text
[ ] PS scope
[ ] Team boundaries
[ ] Extraction contract
[ ] Core schema
[ ] HLD
[ ] Initial LLD
[ ] Graph model
[ ] Workflow-node model
[ ] Evaluation strategy
[ ] Demo scenario
```

Small experimental spikes are allowed before full freezing, but any experiment that becomes part of the product must be incorporated into this context file.

---

# 60. MASTER PRINCIPLE

The project should optimize for:

> **Credible, measurable, evidence-backed investigative intelligence.**

Not for:

- the number of AI models
- the number of screens
- the number of graph nodes
- buzzwords
- unsupported accuracy claims

The final product should allow an investigator to go from:

```text
Fragmented evidence
        ↓
Connected entities
        ↓
Temporal network
        ↓
Analytical workflow
        ↓
Pattern / key-person discovery
        ↓
Evidence review
        ↓
Reproducible investigative lead
```

Every major implementation decision should preserve this chain.

---

# 61. TEAM INTEGRATION: VAIBHAV'S CLARITY EXTRACTION PLATFORM

## 61.1 Ownership Boundary

Vaibhav owns the document-intelligence / extraction layer through the public repository:

- Repository: https://github.com/Vkkthebest2004/Clarity
- Current repository description: Evidence-Grade Document Extraction Platform & Portable Engine for Forensic Auditing & Knowledge Graphs.

Clarity is responsible for taking rough document inputs and turning them into structured, evidence-grade outputs. Our downstream intelligence system begins after the Clarity graph contract is produced.

### Vaibhav / Clarity responsibility

```text
Raw Document / Image / Scan
        ↓
Ingestion + Hashing
        ↓
Preprocessing
        ↓
Document Classification
        ↓
VLM Structured Extraction
        ↓
Validation / Confidence / Dual-Run / Escalation
        ↓
Persistence + Audit Dossier
        ↓
GRAPH CONTRACT
        ↓
OUR SYSTEM
```

## 61.2 Verified Clarity capabilities

The repository currently documents the following technology and pipeline:

- VLM: Qwen3-VL-8B (`qwen3-vl:8b`)
- Escalation model: Qwen3-VL Thinking (`qwen3-vl:8b-thinking`)
- Local inference interface: Ollama / vLLM through an OpenAI-compatible endpoint
- Image preprocessing: OpenCV + Pillow
- Database: PostgreSQL / SQLite using SQLAlchemy 2.0 + Alembic
- Storage: content-addressable S3 / MinIO / local storage keyed by SHA-256
- API/CLI: FastAPI + Rich CLI

The documented extraction lifecycle includes SHA-256 hashing, EXIF orientation, perspective correction, deskewing, contrast enhancement, document classification, schema-constrained JSON extraction, confidence checks, dual-run diffing, escalation and audit persistence.

Source: https://github.com/Vkkthebest2004/Clarity

## 61.3 Critical integration APIs

The Clarity README documents these downstream-facing endpoints:

- `GET /api/v1/documents/{document_id}/graph-contract`
  - exports structured entities, events and relationships for downstream graph/analytics engines.
- `GET /api/v1/cases/{case_id}/graph-contract`
  - aggregates multi-document case entities and resolved relationships.
- `POST /api/v1/engine/extract`
  - headless document extraction for external application integration.

The portable `ClarityEngine` also exposes a graph-contract result and supports exporting it to a file.

The documented graph-contract version is `v1.0.0` and the README describes fixed downstream keys:

```text
entities
 events
 relationships
 audit_chain
```

IMPORTANT: Before implementing against any assumed field-level schema, fetch/inspect an actual graph-contract response from Clarity. The public README confirms the contract concept and top-level structure, but this master document must not invent undocumented nested fields.

## 61.4 What OUR module receives

Our module should consume Clarity's graph contract rather than re-implement document OCR/VLM extraction.

Conceptually:

```text
Clarity Graph Contract
        ↓
Input Adapter / Contract Validator
        ↓
Normalization
        ↓
Entity Resolution (where not already reliably resolved)
        ↓
Evidence Graph
        ↓
Temporal + Graph Analytics
        ↓
Pattern / Bridge / Key-Individual Analysis
        ↓
Investigation Workflow
        ↓
AI Investigation Layer
        ↓
Investigator Canvas / Graph / Report
```

## 61.5 Evidence provenance must survive the boundary

Clarity already emphasizes evidence-grade extraction, SHA-256 chain-of-custody, audit logging and source-level bounding boxes. Our downstream graph must preserve references back to those source records wherever technically available.

For each entity/event/relationship we should preserve, at minimum when supplied by Clarity:

- source document identifier
- source record/extraction identifier
- page / location information when available
- original extracted value
- confidence
- audit/provenance reference
- bounding-box information when available

We should not discard provenance during normalization, entity resolution or graph construction.

## 61.6 Do not duplicate Clarity unnecessarily

Do NOT rebuild:

- OCR
- document preprocessing
- VLM document extraction
- document classification
- extraction confidence logic
- extraction audit persistence
- cryptographic hashing / chain-of-custody

unless integration testing proves a missing capability is required by PS #13.

Our innovation and engineering effort is downstream:

```text
EXTRACTED EVIDENCE
        ↓
CONNECT
        ↓
RESOLVE
        ↓
ANALYZE
        ↓
INVESTIGATE
        ↓
EXPLAIN
```

## 61.7 Responsibility split for PS #13

### Vaibhav / Clarity

1. Multi-format document ingestion supported by his implementation
2. Document preprocessing
3. Entity/event/relationship extraction
4. Confidence / validation / escalation
5. Extraction audit trail
6. Graph-contract generation

### Our downstream intelligence system

1. Contract validation / adapter
2. Normalization
3. Cross-source entity resolution as required
4. Evidence-graph construction
5. Relationship enrichment
6. Temporal modeling
7. Key-individual analysis
8. Community detection
9. Bridge/intermediary detection
10. Suspicious / unusual pattern detection
11. Evidence-aware scoring
12. Investigation workflow execution
13. Natural-language → workflow AI
14. Interactive investigation canvas
15. Evidence inspection
16. Investigative reporting

This split is the current project boundary unless explicitly changed in the decision log.

## 61.8 Important repository observations

Clarity already includes a frontend with a network-graph/forensic-analytics view and an audit dossier. Therefore our final product should not simply duplicate the existing Clarity dashboard.

Our frontend should focus on the downstream investigation experience:

- interactive investigation workflow canvas
- synchronized evidence graph
- timeline
- analytical nodes
- evidence-backed findings
- uncertainty / contradiction views
- investigator queries
- reproducible investigation workflows

Clarity's extraction/document-inspection capabilities remain upstream infrastructure.

## 61.9 Integration acceptance test

Before declaring our integration complete, verify this concrete path:

```text
1. Upload a supported case document to Clarity
2. Clarity processes and validates it
3. Retrieve the graph contract
4. Validate contract against the expected version/schema
5. Convert entities/events/relationships into our internal model
6. Preserve provenance references
7. Build the evidence graph
8. Run one analytical workflow
9. Produce a finding with traceable evidence
10. Show the finding in the investigation canvas
```

The integration is not considered complete if step 9 or 10 loses the source/evidence chain.

## 61.10 Current caution

The Clarity README documents a `v1.0.0` graph contract and a case-level endpoint described as aggregating resolved relationships, while cross-document entity resolution is also listed as a later roadmap milestone. Treat this as an integration point that must be verified against actual runtime behavior rather than assumed. We should inspect a real `case graph-contract` response before deciding whether our system or Clarity owns final cross-document entity resolution.

---

# 62. CURRENT ARCHITECTURAL ENTRY POINT

For future implementation discussions, the canonical handoff is:

```text
                VAIBHAV / CLARITY
                        │
                        ▼
              Evidence Graph Contract
                        │
                        ▼
             ┌──────────────────────┐
             │ OUR INTELLIGENCE     │
             │       LAYER          │
             ├──────────────────────┤
             │ Contract Adapter     │
             │ Entity Resolution    │
             │ Graph Builder        │
             │ Temporal Engine      │
             │ Graph Analytics      │
             │ Pattern Detection    │
             │ Key-Person Analysis  │
             │ Investigation Engine │
             │ AI Workflow Agent    │
             │ Evidence/Provenance  │
             └──────────┬───────────┘
                        ▼
              Investigation Canvas
                        │
                ┌───────┴───────┐
                ▼               ▼
          Evidence Graph     Report
```

Any future architecture or implementation proposal should attach itself to this boundary unless the project decision log explicitly changes it.


---

# 49. Verified Integration Baseline — Clarity Repository Inspection

> Verified against the team-provided Clarity repository archive on 19 September 2026. This section records what is actually implemented in the current codebase, rather than relying only on the repository's high-level README.

## 49.1 Current Repository Structure Relevant to Team 2

The current Clarity repository contains:

```text
clarity/
├── api/
├── contract/
├── db/
├── pipeline/
├── preprocessing/
├── storage/
├── validation/
├── vlm/
└── web/

frontend/
├── src/app/
├── src/components/
│   ├── brand/
│   ├── layout/
│   └── views/
└── src/store/
```

The repository already contains a frontend network visualization component:

```text
frontend/src/components/views/NetworkGraphView.tsx
```

and also existing views for:

```text
ForensicAnalyticsView.tsx
GeospatialMapView.tsx
EvidenceDataTableView.tsx
DocumentInspectorView.tsx
ExecutiveDossierView.tsx
```

Therefore, the final Team 2 product should extend the existing application rather than create a completely separate frontend application unless a later architecture decision explicitly requires it.

## 49.2 Current Graph Contract Schema

The current contract implementation is in:

```text
clarity/contract/schemas.py
```

It defines:

### EntityType

```text
PERSON
PHONE
ACCOUNT
LOCATION
ORGANIZATION
VEHICLE
WEAPON
IDENTIFIER
OTHER
```

### EventType

```text
CALL
TRANSACTION
FINANCIAL_FRAUD
FIR_REGISTRATION
SEIZURE
ARREST
MEDICAL_EXAM
FORENSIC_REPORT
INCIDENT
```

### SourceTraceability

Each entity/event source currently includes:

```text
document_id
filename
file_hash_sha256
page
bounding_box (optional)
text_span (optional)
```

### EntityContractItem

Currently contains:

```text
id
type
name
normalized_name
role
attributes
confidence
source
```

### EventContractItem

Currently contains:

```text
id
type
title
source_entity
target_entity
timestamp
timestamp_start
timestamp_end
attributes
source
```

### RelationshipContractItem

Currently contains:

```text
id
source_entity
target_entity
relationship_type
confidence
evidence
```

### GraphContractResponse

Currently contains:

```text
contract_version
case_id
batch_id
total_documents
entities[]
events[]
relationships[]
audit_chain{}
```

The contract version currently defaults to:

```text
1.0.0
```

## 49.3 Existing Graph-Contract API

The current API exposes:

```text
GET /api/v1/documents/{document_id}/graph-contract
GET /api/v1/cases/{case_id}/graph-contract
POST /api/v1/engine/extract
```

The first endpoint returns a single-document `GraphContractResponse`.

The second synthesizes a case-level contract across documents.

The third is a headless extraction endpoint that accepts uploaded files and directly returns a `GraphContractResponse`.

## 49.4 Current Case-Level Merge Behavior

The current `build_graph_contract_for_case()` implementation in:

```text
clarity/contract/transformer.py
```

merges entities across documents using:

```text
(type, normalized_name.lower())
```

as its canonical key.

That means Clarity already performs a basic deterministic cross-document reconciliation, but this should NOT be treated as the final intelligence-grade entity-resolution system.

Our Team 2 intelligence layer should be capable of stronger resolution using multiple signals such as:

```text
name similarity
phone/identifier overlap
address/location similarity
temporal consistency
shared-neighbor evidence
other corroborating attributes
```

and should retain the basis for every merge suggestion.

## 49.5 Current Transformer Behavior — Important Scope Constraint

The current transformer constructs a useful graph contract from extracted fields, dates, amounts and a limited set of deterministic relationships.

Examples already present include:

```text
ACCOUNT_HOLDER
COMPLAINANT_OF
VICTIM_OF
ACCUSED_IN
DEBITED_IN
```

However, the current transformer does NOT yet represent the full breadth of relationship types required for the final PS #13 intelligence experience.

For example, a full investigative graph may eventually need richer representations for:

```text
CALLED
TRANSFERRED_TO
LOCATED_AT
OWNED
USED
MET
OBSERVED_WITH
REGISTERED_TO
COMMUNICATED_WITH
CONNECTED_TO
```

Therefore, the architecture MUST distinguish:

```text
Clarity extraction/contract capabilities
        from
Team 2 analytical enrichment
```

and must not assume that every required investigative relationship already exists in the incoming contract.

## 49.6 Current Event Construction — Important Limitation

The current document-level transformer creates events primarily from extracted date fields and document semantics.

It already supports event types such as:

```text
INCIDENT
FINANCIAL_FRAUD
FIR_REGISTRATION
SEIZURE
ARREST
```

but it should not be assumed that arbitrary CDRs, transaction ledgers, surveillance observations or social-media records will automatically become rich event objects in the present implementation.

For PS #13, our integration layer should therefore support both:

```text
Clarity-generated events
+
structured external/demo evidence feeds
```

where required.

## 49.7 Current Provenance Capability

Clarity already attaches provenance to extracted entities/events through:

```text
document_id
filename
file_hash_sha256
page
bounding_box
text_span
```

This is a major architectural advantage.

The Team 2 intelligence layer should preserve this provenance through every transformation:

```text
Source evidence
      ↓
Entity resolution
      ↓
Graph relationship
      ↓
Analytical signal
      ↓
Finding
      ↓
Investigation report
```

No analytical result should lose the references that explain where it came from.

## 49.8 Current Audit Capability

The graph contract already includes:

```text
audit_chain
```

and the document contract records quality/audit metadata.

The Team 2 system should preserve this information and add its own analytical audit trail for:

```text
workflow version
analysis-node configuration
algorithm/model version
execution timestamp
dataset/scenario version
input graph snapshot/reference
output finding IDs
```

## 49.9 Integration Boundary

The authoritative Team 2 integration boundary is now:

```text
                 CLARITY
        Documents → Extraction
                    ↓
              Validation
                    ↓
             Graph Contract
                    ↓
        ┌────────────────────────┐
        │ GRAPH CONTRACT ADAPTER │
        └────────────┬───────────┘
                     ↓
          CANONICAL INVESTIGATION MODEL
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
      Entity       Event        Evidence
    Resolution    Timeline      Model
        └────────────┼────────────┘
                     ↓
               Evidence Graph
                     ↓
              Intelligence Engine
                     ↓
              Investigation Engine
                     ↓
          AI Workflow / Canvas
                     ↓
                 Frontend
```

The `Graph Contract Adapter` is intentionally a separate layer.

This prevents changes inside Clarity from forcing a rewrite of the analytical engine.

## 49.10 Existing Frontend Capability

The current `NetworkGraphView.tsx` already uses Cytoscape for graph visualization.

The current frontend store also already maintains:

```text
crossDocIntelligence
selectedEntity
documents
timeline-related data
available datasets
```

The Team 2 product should therefore evolve the existing visual system into:

```text
Evidence Graph
+
Investigation Workflow Canvas
+
Timeline
+
Evidence Inspector
+
Analytics panels
```

rather than throwing away the existing UI.

## 49.11 Architecture Decision — Two Different Graph Concepts

The final product MUST keep these conceptually separate:

### Evidence Graph

Answers:

> What entities, events and relationships exist in the available evidence?

### Investigation Workflow Canvas

Answers:

> What analytical operations is the investigator performing on that evidence?

Example workflow:

```text
[CASE]
   ↓
[FILTER TIME]
   ↓
[EXPAND NETWORK]
   ↓
[COMMUNITY DETECTION]
   ↓
[FIND BRIDGE]
   ↓
[RANK]
   ↓
[ATTACH EVIDENCE]
   ↓
[REPORT]
```

The evidence graph is the data being analyzed.

The workflow canvas is the procedure used to analyze it.

## 49.12 Current Integration Acceptance Test

Before Team 2 implements advanced analytics, the following basic integration test should pass:

```text
1. Clarity processes a sample case.
2. Case graph-contract endpoint returns valid JSON.
3. Adapter validates GraphContractResponse.
4. All source identifiers are preserved.
5. Entity IDs referenced by events/relationships resolve correctly.
6. Canonical internal objects are created.
7. Evidence provenance is retained.
8. A simple graph visualization can be generated.
9. A deterministic analytics function can query the internal model.
```

Only after this passes should we begin implementing advanced bridge/anomaly/investigation workflow features.

---

# 50. Implementation Rule — Master Context Must Be Updated Before Major Architectural Changes

This document is the Team 2 master context.

Before implementing a major new architectural capability, update this document first with:

```text
Decision
Reason
Affected components
Input/output contract
Risks
Fallback
Status
```

This prevents architecture drift and inconsistent assumptions between team members.

---

# 51. Current Status After Clarity Inspection

```text
KAYA PS #13                    ✅ Locked
Clarity upstream system        ✅ Existing
Graph Contract                 ✅ Existing
Case-level contract            ✅ Existing
Basic cross-document merge     ✅ Existing
Provenance                     ✅ Existing
Audit metadata                 ✅ Existing
Existing network frontend      ✅ Existing
Investigation canvas           ⏳ To build
Intelligence engine            ⏳ To build
Advanced entity resolution     ⏳ To build/enrich
Evidence graph persistence     ⏳ To design
Temporal analytics             ⏳ To build
Key-individual analytics       ⏳ To build
Bridge/hidden-link detection   ⏳ To build
Suspicious-pattern engine      ⏳ To build
AI workflow agent              ⏳ To build
Ground-truth evaluation        ⏳ To build
```

## Immediate next technical task

DO NOT start with advanced ML.

First implement:

```text
Clarity Graph Contract
        ↓
Graph Contract Adapter
        ↓
Canonical Investigation Model
        ↓
Validation tests
        ↓
Minimal graph rendering
```

After that is stable, freeze the Neo4j/evidence-graph schema and begin the analytical engine.

# 52. Implemented Milestone — Graph Contract Adapter (19 September 2026)

The first post-extraction implementation milestone has now been designed and implemented in the development copy of Clarity.

## 52.1 Files added

```text
Clarity/intelligence/
├── __init__.py
├── models.py
└── graph_contract_adapter.py

tests/
└── test_graph_contract_adapter.py
```

## 52.2 Responsibility

The adapter is the formal boundary between Vaibhav's Clarity extraction/evidence pipeline and Suryaansh's downstream investigation intelligence layer.

```text
Clarity GraphContractResponse / JSON
                ↓
       GraphContractAdapter
                ↓
     Canonical Investigation Model
                ↓
     future graph / analytics layers
```

## 52.3 Canonical models introduced

```text
EvidenceReference
CanonicalEntity
CanonicalEvent
CanonicalRelationship
AdapterIssue
InvestigationGraph
InvestigationStatus
NodeKind
```

`InvestigationStatus` currently supports:

```text
OBSERVED
CORRELATED
INFERRED
HYPOTHESIS
```

The adapter maps upstream contract relationships to `OBSERVED` because they are already supplied by the Clarity contract. Later analytical/inference layers may create stronger epistemic distinctions.

## 52.4 Adapter guarantees

The adapter currently:

- accepts a `GraphContractResponse`, mapping/dict payload, JSON string, or JSON bytes;
- re-validates incoming data with the existing Pydantic Graph Contract schema;
- preserves entity/event IDs;
- preserves source document, filename, SHA-256, page, bounding box and text-span provenance;
- preserves event timestamps and event attributes;
- supports relationship endpoints that target either entities or events;
- retains relationship textual evidence;
- derives relationship source references only when objectively supported by a linked event endpoint;
- preserves `audit_chain` metadata;
- detects duplicate node IDs;
- detects duplicate relationship IDs;
- detects dangling event endpoints;
- detects dangling relationship endpoints;
- detects invalid event endpoint node kinds;
- supports strict mode for fail-fast integration and non-strict mode for collecting quality issues.

## 52.5 Explicit non-responsibilities

The adapter does not:

- perform fuzzy entity resolution;
- invent relationships;
- infer criminality;
- run graph analytics;
- calculate anomaly scores;
- call an LLM;
- persist to Neo4j;
- control the frontend.

Those responsibilities remain downstream layers.

## 52.6 Test status

The adapter's dedicated test suite currently passes:

```text
11 passed
```

The test coverage includes:

- Pydantic contract adaptation
- JSON adaptation
- provenance preservation
- event endpoint preservation
- event-linked relationship provenance
- missing relationship endpoint handling
- non-strict issue reporting
- duplicate node collision handling
- duplicate relationship ID handling
- invalid JSON handling
- JSON-ready canonical serialization
- invalid event endpoint handling

## 52.7 Important environment note

The uploaded Clarity repository uses a package directory named `Clarity` while Python imports use the lowercase module name `clarity`. This works naturally on the team's Windows development environment because Windows filesystem lookup is case-insensitive, but a Linux test environment may require the project to be packaged/installed correctly or otherwise expose the expected lowercase import path. This is an environment/package-layout issue, not a design change to the adapter.

# 53. Next Implementation Gate

Do not jump directly into the final graph/canvas implementation until the team obtains one real graph-contract response from the running Clarity application.

Required artifact:

```text
A real JSON response from:
GET /api/v1/cases/{case_id}/graph-contract
```

or the document equivalent:

```text
GET /api/v1/documents/{document_id}/graph-contract
```

The real payload must be compared against the adapter tests. Any schema differences must be recorded in this document before the adapter contract is changed.

After this gate passes, the next planned milestone is:

```text
Canonical Investigation Model
        ↓
Entity-resolution engine
        ↓
Evidence-graph persistence/model
        ↓
Temporal query layer
        ↓
Key-person + bridge + suspicious-pattern analytics
```

# 60. Approved Implementation Decision — Entity Resolution Core (19 September 2026)

The next implementation milestone is the deterministic, explainable Entity Resolution Core built against the already-validated canonical investigation model produced by `GraphContractAdapter`.

This does **not** bypass the live Clarity contract validation gate. The resolver is schema-independent at its input boundary because it consumes `CanonicalEntity` objects. A real Clarity `graph-contract` payload is still required before we declare the upstream integration complete.

## 60.1 Scope of this milestone

Build only:

```text
CanonicalEntity[]
      ↓
Normalization / candidate generation
      ↓
Pairwise entity matching
      ↓
Explainable match score
      ↓
Match status
      ↓
Confirmed clusters + unresolved/probable candidates
```

Do not yet implement:

- Neo4j persistence
- graph analytics
- anomaly detection
- AI/LLM reasoning
- investigation canvas
- temporal analytics

## 60.2 Entity-resolution safety rules

1. Entity candidates are compared only within compatible entity types.
2. Strong identifiers are never silently overwritten.
3. Contradictory strong identifiers reduce confidence and can block automatic confirmation.
4. Automatic clustering is allowed only for high-confidence matches; probable/possible matches remain reviewable suggestions.
5. Every match decision must expose its contributing signals.
6. Every resolved canonical cluster must retain all original entity IDs and source provenance.
7. The resolver must never infer criminality or investigative guilt.
8. Results must be deterministic for the same input and configuration.

## 60.3 Initial signal model

The initial implementation may use configurable, explainable signals such as:

- normalized-name equality / similarity
- strong identifier overlap
- attribute overlap (e.g. phone/account/location where available)
- role compatibility
- contradictory identifier detection

The initial weights are implementation parameters, not validated scientific claims. They must be configurable and later evaluated against ground-truth scenarios.

## 60.4 Match statuses

```text
CONFIRMED
PROBABLE
POSSIBLE
UNRESOLVED
CONTRADICTED
```

These describe identity-resolution confidence, not criminality.

## 60.5 Required milestone tests

The resolver test suite must include:

- exact duplicate identity across documents;
- exact strong-identifier match;
- fuzzy-name match with supporting attributes;
- incompatible entity types not matching;
- contradictory strong identifiers blocking confirmation;
- unresolved weak candidates;
- deterministic output ordering;
- provenance and alias preservation;
- confirmed-cluster construction;
- probable/possible candidates remaining separate from automatic clusters.

## 60.6 Integration gate retained

After this isolated core is implemented and tested, obtain a real Clarity response from:

```text
GET /api/v1/cases/{case_id}/graph-contract
```

or:

```text
GET /api/v1/documents/{document_id}/graph-contract
```

Run the real payload through the adapter and resolver. Any mismatch or new field requirement must be recorded here before changing either contract.

# 61. Implemented Milestone — Entity Resolution Core (19 September 2026)

The Entity Resolution Core has been implemented on top of the canonical model and tested in an isolated environment.

## 61.1 Implemented module

```text
clarity/intelligence/entity_resolution.py
```

It provides:

- `EntityResolver`
- `EntityResolutionConfig`
- `EntityResolutionResult`
- `EntityResolutionStatus`
- `EntityMatchCandidate`
- `ResolvedEntityCluster`
- `MatchSignal`

## 61.2 Behavior

The resolver:

- compares only compatible entity types;
- normalizes names for comparison;
- computes deterministic string/token similarity;
- recognizes strong identifier attributes such as phone/account/vehicle/device/IP/email identifiers;
- canonicalizes common Indian phone formats such as `+91-XXXXXXXXXX` vs `XXXXXXXXXX`;
- uses attribute overlap and role compatibility as supporting signals;
- detects contradictory strong identifiers;
- exposes an explainable weighted score and signal breakdown;
- classifies candidates as `CONFIRMED`, `PROBABLE`, `POSSIBLE`, `UNRESOLVED`, or `CONTRADICTED`;
- automatically clusters only candidates meeting the configured auto-cluster threshold;
- preserves original member IDs, aliases and source document IDs in confirmed clusters;
- keeps lower-confidence matches reviewable rather than silently merging them;
- returns deterministic ordering for equivalent inputs regardless of input ordering.

## 61.3 Deliberate limitation

The resolver does not yet rewrite the `InvestigationGraph` entity/event/relationship IDs into cluster IDs. That transformation belongs at the next graph-construction boundary after the resolver has been validated against a real Clarity contract and the graph storage model is frozen.

## 61.4 Tests

The dedicated isolated resolver suite currently passes:

```text
10 passed
```

Covered cases include:

- exact duplicate person records;
- strong phone identifier support;
- fuzzy-name + supporting-attribute matching;
- incompatible entity types;
- contradictory phone identifiers;
- weak/unresolved entities;
- alias and source preservation;
- deterministic output ordering;
- configurable auto-cluster threshold;
- exact phone entity normalization.

## 61.5 Important interpretation rule

Resolver scores and statuses represent identity-resolution evidence only. They are not probabilities of criminality, guilt, threat or wrongdoing.

## 61.6 Next implementation gate

The next milestone remains the Evidence Graph foundation. Before that is implemented, a real Clarity `graph-contract` response should be run through:

```text
Clarity API
    ↓
GraphContractAdapter
    ↓
EntityResolver
```

Any real payload mismatch must be recorded before modifying the adapter or canonical models.

The next implementation layer after this gate is planned as:

```text
Resolved entities + raw events + relationships
        ↓
Evidence Graph Model
        ↓
Temporal metadata / traversal foundation
```

# 53. V1.4 TEMPORAL INTELLIGENCE MILESTONE — 19 SEPTEMBER 2026

V1.4 adds a deterministic, database-agnostic Temporal Intelligence Engine above the V1.3 Evidence Graph.

## Scope implemented

- ISO-8601 point/interval parsing
- configurable default timezone (Asia/Kolkata)
- explicit inclusive time-window semantics
- event-in-window queries
- active-entity discovery from dated event participants
- deterministic activity buckets
- time-filtered graph snapshots
- snapshot-to-snapshot comparison
- explicit malformed timestamp diagnostics
- explicit handling of undated events/relationships

## Temporal correctness rules

1. Never invent a date or time from document order, filenames, visual position, or narrative assumptions.
2. A point timestamp is an instant; an explicit start/end pair is an interval.
3. Naive timestamps require the configured timezone assumption; offset-aware timestamps are normalized to UTC for comparison.
4. Undated events are reported as `UNDATED_EVENT` and are excluded from temporal windows.
5. Undated direct entity/entity relationships are not assigned to a time window.
6. Explicitly dated relationships can participate in temporal snapshots.
7. Entity↔event structural edges are included in a snapshot when the associated dated event is selected, because they document participation in that event.
8. Invalid temporal values generate a non-silent error issue; they are not auto-corrected.

## Current validated development chain

```text
Clarity extraction
    ↓
Graph Contract Adapter
    ↓
Entity Resolution
    ↓
Evidence Graph
    ↓
Temporal Intelligence Engine  ← V1.4
```

## Next milestone

The next layer should be the deterministic Graph Analytics Engine, beginning with centrality, connected components, shortest-path analysis, community detection and bridge/intermediary candidates. Temporal signals from V1.4 must remain available to that layer.

## User workflow requirement

Per team process, V1.4 is considered a candidate known-good snapshot only after local user validation. After successful validation it is copied into the user's `perfect` backup directory. No Git workflow is required during development.

## V1.10.6 + C4 — Workflow Experience Completion

C4 completes the investigator-facing workflow experience without introducing a new analytical engine. The existing V1.10.6 light-theme visual baseline and C3 interactive workflow builder remain intact.

### Investigator workflow model
- The Investigation Canvas is an executable visual program for a case investigation, not a decorative flowchart.
- AI can generate a workflow; the investigator can then inspect, edit, add, remove, duplicate and connect nodes manually.
- Manual node creation uses the same allow-listed deterministic operations as AI-generated nodes.
- Custom node label/description are presentation metadata; the execution operation and configuration remain the real executable contract.
- Output-to-input wiring is the only supported workflow connection mechanism.
- Cycles, self-loops, duplicate edges and unknown node references remain invalid.

### C4 results model
A workflow run must expose the analytical value of execution in the workflow workspace rather than leaving results buried in raw execution traces.

The results experience surfaces:
- finding/lead cards from bridge candidates, key individuals and anomaly findings;
- case graph summary metrics returned by execution;
- evidence/provenance counts and contradictions;
- per-node outputs and execution status;
- generated report availability and export;
- execution ID for reproducibility and audit;
- recent local execution history for the active case.

Every result remains framed as an investigative lead, not a guilt determination. Findings should retain source/relationship/event references where the engine provides them.

### C4 responsive workflow behavior
The workflow workspace must adapt to available viewport width instead of relying on simultaneous permanent side panels:
- wide desktop: node palette + canvas + result/inspector regions;
- medium desktop: collapsible/overlay palette and responsive results inspector;
- small viewport: canvas-first workspace with overlay drawers for palette, node inspector and results;
- workflow canvas retains explicit zoom/fit controls and scrollable world coordinates rather than shrinking nodes below usable size.

### C4 navigation semantics
- Clicking a workflow finding selects its originating workflow node.
- When an analytical finding exposes a canonical entity ID, the investigator can jump to Entity Network, preserving case context.
- Evidence-backed counts and report actions remain in the same results surface.
- Execution history can be selected for inspection; history is browser-local and does not alter the canonical case database.

### C4 acceptance intent
Acceptance is based on investigator task completion:
1. Ask AI for a workflow and apply it.
2. Add one manual node from the palette.
3. Drag an output port to another node's input port.
4. Edit/duplicate/remove nodes and connections.
5. Run the workflow.
6. Immediately see what the workflow discovered, what evidence supports it, what contradictions remain, and which report can be exported.
7. Navigate from a finding back to the graph/evidence context.

This milestone intentionally does not add arbitrary AI code execution, automated guilt decisions, or new backend analytical primitives.

