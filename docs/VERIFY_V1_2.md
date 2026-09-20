# Verify V1.2 — Entity Resolution Core

## Purpose

Validate the Entity Resolution Core in isolation before moving to the Evidence Graph milestone.

## Project location

Run commands from the project root, the directory containing `pyproject.toml`.

## Required checks

### 1. Compile check

```powershell
python -m compileall -q clarity\intelligence tests\test_entity_resolution.py
```

Expected: no output and exit code 0.

### 2. Existing adapter regression tests

```powershell
python -m pytest -q tests\test_graph_contract_adapter.py
```

Expected:

```text
11 passed
```

### 3. Entity-resolution tests

```powershell
python -m pytest -q tests\test_entity_resolution.py
```

Expected:

```text
10 passed
```

### 4. Import check

```powershell
python -c "from clarity.intelligence import EntityResolver, EntityResolutionConfig; print('Entity Resolver import: OK')"
```

Expected:

```text
Entity Resolver import: OK
```

## Current scope

This milestone does not require Neo4j, the frontend canvas, an LLM, live Clarity API access or graph analytics.

## Integration gate

Before the next milestone is accepted, run one real Clarity `graph-contract` response through the adapter and then the resolver. Do not hand-edit the real payload to make tests pass; record schema differences and fix the integration boundary deliberately.
