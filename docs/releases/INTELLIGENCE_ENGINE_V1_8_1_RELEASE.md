# Intelligence Engine V1.8.1 — VLM Integration Reliability Patch

This release is an integration fix built on V1.8. It does not add a new intelligence feature.

## Changes
- Use native Ollama `/api/chat` for local multimodal image requests.
- Send image bytes as base64 in the native `images` array.
- Request JSON output through Ollama `format: "json"`.
- Preserve OpenAI-compatible multimodal transport for non-local endpoints.
- Preserve `content`, `reasoning`, and `reasoning_content` response handling.
- Surface transport failures in extraction metadata/audit events.
- Add filename type hints for local benchmark sample files when VLM classification is unavailable/low-confidence.
- Pass inferred document type into extraction prompts.
- Add `scripts/verify_ollama_vision.py` for a single-image diagnostic.

## Why
A real Clarity run on 19 September 2026 produced empty entity/event/relationship output and only the heuristic legibility note. The client was using an unsupported/undocumented `image_url` path for local Ollama multimodal requests. This release fixes that transport boundary before downstream intelligence proceeds.
