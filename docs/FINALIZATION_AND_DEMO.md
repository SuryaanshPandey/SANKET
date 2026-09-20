# SANKET — Finalization & Demo Readiness

## Milestone

**V1.10.6 + C4 — workflow experience completion and submission hardening**

The frozen V1.10.6 interaction model and the approved light-theme visual variant remain unchanged. This milestone is deliberately focused on proving the existing product works end-to-end and making the result easy to demonstrate and submit.

## What is being finalized

SANKET's intended investigation loop is:

```text
Evidence
  ↓
Clarity extraction / Graph Contract
  ↓
Entity resolution
  ↓
Evidence Graph / Case Memory
  ↓
Temporal + Graph Analytics
  ↓
Pattern / Anomaly Analysis
  ↓
Investigation Workflow
  ↓
Evidence Review
  ↓
Evidence-backed Report
```

The AI planner sits beside this loop as a constrained orchestration layer:

```text
Investigator question
  ↓
AI planner
  ↓
Workflow schema validation
  ↓
Allow-list validation
  ↓
Deterministic execution
  ↓
Evidence-backed outputs
```

The model must not directly execute arbitrary SQL, shell commands, filesystem operations or other tools.

## Target-machine preflight

Before the final manual run, execute:

```powershell
python scripts/target_machine_preflight.py
```

`PASS` means the local Python/backend prerequisites and frontend lockfile are available. A local SQLite runtime database is reported as a warning because it is expected during development and must simply be excluded from the final submission. A missing local Ollama process is also a warning unless the live AI planner is being demonstrated.

## Deterministic final acceptance

Run from the repository root:

```powershell
python scripts/final_acceptance.py
```

The harness creates a controlled synthetic graph with:

- a primary structural bridge candidate;
- a target-window activity spike;
- a novel relationship;
- an interaction burst;
- temporal scoping;
- a multi-step investigation workflow;
- evidence-linked report generation;
- deterministic execution-ID reproducibility.

The benchmark is a **controlled software-behaviour test**, not a real-world policing accuracy measurement.

The result is written to:

```text
artifacts/final_acceptance.json
```

## Manual end-to-end acceptance on the target machine

### 1. Backend

Start the FastAPI service using the repository's normal local command and confirm:

```text
GET /api/v1/health → healthy
```

### 2. Frontend

Start the Next.js application with the repository's normal local command and confirm the light-theme workstation opens without console errors.

### 3. Fresh case

Use the prepared police investigation case or a fresh document set.

Verify that ingestion shows:

```text
queued → current document/stage → confirmed completion
```

No percentage should be simulated from elapsed wall-clock time.

### 4. Case memory

From Overview, confirm the case exposes the same underlying information through:

- Overview;
- Entity Network;
- Locations;
- Investigation Workflow;
- Evidence Ledger;
- Document Inspector;
- Evidence Review;
- Quality & Analytics.

### 5. Network

Verify:

- semantic investigation objects are readable;
- source documents are visible as evidence anchors when applicable;
- relationships are distinct from provenance links;
- automatic arrangement keeps connected components readable;
- isolated observations are not allowed to dominate the graph.

### 6. Investigation workflow

Run the default deterministic workflow first.

Then test the AI planner:

1. ask an investigator-style question;
2. inspect the generated plan;
3. confirm the plan is visibly reviewable;
4. apply it to the canvas;
5. validate;
6. execute;
7. inspect node outputs and evidence references;
8. export the report.

The planner is optional at execution time; a human can still edit and run the deterministic workflow directly.

### 7. Evidence review

Confirm that contradictions remain visible and are not silently reconciled.

Confirm that a human field correction preserves:

```text
original extracted value
corrected value
reviewer
review timestamp
```

The original extraction should remain intact for auditability.

### 8. Report

Confirm that a completed workflow produces a structured report containing:

- case identifier;
- workflow/execution identifier;
- summary counts;
- analytical findings;
- evidence review counts;
- uncertainty notes;
- explicit investigative-lead language.

## Five-minute demo script

The KAYA Software Hackathon currently specifies a maximum **5-minute** demo video and asks the video to cover the problem/motivation, approach/architecture, a live working demo, security and impact. urlKAYA Software Hackathon requirementshttps://kaya.azmth.in/events/hackathon/

### 0:00–0:30 — Problem

> Investigative data is scattered across documents and systems. The problem is not simply extracting text; it is remembering what belongs together, what happened when, what connects, and which conclusions still need verification.

Show the SANKET case memory concept.

### 0:30–1:05 — Architecture

Show one simple pipeline:

```text
Documents → Graph Contract → Evidence Graph → Analytics → Workflow → Evidence-backed report
```

State that AI plans the investigation but the deterministic engine executes it.

### 1:05–1:50 — Ingestion / Case Memory

Open the prepared case.

Show the source documents and the Overview.

Point out that the same information persists across the workspace.

### 1:50–2:35 — Entity Network + Locations

Open Entity Network.

Show the connected case structure, document evidence anchors and readable layout.

Jump to Locations and show a source-linked location.

### 2:35–3:40 — Investigation Workflow

Open Investigation.

Use a question such as:

> “Find possible bridge leads between network communities and check whether unusual activity appears in the same target period.”

Show the AI-generated plan, review it, apply it, validate it and execute it.

### 3:40–4:25 — Evidence Review

Open the workflow result and Evidence Review.

Show one finding and trace it back to its supporting evidence.

Then show a contradiction and explain that SANKET preserves the conflict instead of selecting a convenient answer.

### 4:25–4:50 — Report + Human Review

Export the investigation report.

Show the human verification flow briefly.

### 4:50–5:00 — Security / impact

Close with:

> SANKET does not decide guilt. It connects evidence, exposes analytical leads, preserves uncertainty, and lets investigators verify every important conclusion against its source.

## Demo discipline

Do not spend video time clicking through every feature. The strongest story is one continuous investigation:

```text
scattered evidence
      ↓
connected case memory
      ↓
network / time understanding
      ↓
AI-assisted workflow
      ↓
evidence-backed lead
      ↓
human verification
```

Avoid presenting any confidence score as a probability of guilt.

Avoid describing document rule checks as blanket legal certification.

Avoid showing synthetic benchmark numbers without explicitly identifying the data as synthetic.

## Submission checklist

### Required

- Public source repository with README and code.
- Demo video ≤ 5 minutes.

### Recommended

- PDF presentation deck ≤ 10 slides.
- Hosted demo URL, if a stable deployment is available.

### Before submitting

- Open every public/unlisted link in an incognito browser.
- Keep links live until judging is complete.
- Confirm the final repository contains no runtime database, cache, secret or local environment file.
- Confirm the repository history satisfies the event's stated work-window requirements.
- Record the final release identifier in the submission notes.

## C4 workflow experience demonstration

For the workflow portion of the final demonstration:

1. Open **Investigate → Workflow** and press **AI PLAN**.
2. Ask: `Find possible bridge intermediaries and check unusual activity during August.`
3. Apply the validated plan to the canvas.
4. Add one additional operation by dragging a node from the left library to the canvas, or use **CUSTOM NODE** to give an allow-listed operation an investigator-facing label.
5. Drag the new node's output pin onto another node's input pin. The live wire confirms the connection before release.
6. Press **VALIDATE** to check the workflow without execution, then **RUN WORKFLOW** to execute it.
7. Show the **Workflow Results** panel immediately after execution. Start on **Insights** to demonstrate leads, evidence links, contradictions and graph scope.
8. Switch to **Evidence** to show provenance/contradiction context; **Run** to show node execution and reproducible execution ID; **Report** to show the deterministic report.
9. Use **OPEN NODE** from a finding, then **OPEN GRAPH** when a canonical entity match is available.

The story to narrate is: `AI proposes the investigation, the investigator controls the workflow, deterministic nodes execute it, and the results remain tied to evidence and review state.`
