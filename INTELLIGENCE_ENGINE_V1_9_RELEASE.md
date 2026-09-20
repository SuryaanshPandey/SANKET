# Intelligence Engine V1.9.0 Release

## Purpose
V1.9 converts the V1.8 investigation canvas from a visual preview into a real backend-executed workflow against a case EvidenceGraph.

## Included
- GET case investigation graph endpoint
- workflow validation endpoint
- workflow execution endpoint
- deterministic execution IDs
- case-scoped Entity Resolution + Evidence Graph assembly
- downstream scope propagation from TIME_FILTER and EXPAND_NETWORK
- frontend RUN WORKFLOW integration
- node-level execution output inspection
- backend execution status/error display
- V1.9 integration tests

## Non-goals
No cloud VLM provider is introduced. Local Ollama remains the development inference path. AI workflow generation remains a later milestone.
