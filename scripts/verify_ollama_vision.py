"""Fast local diagnostic for Clarity's Ollama multimodal extraction path.

Usage from the project root:
    python scripts/verify_ollama_vision.py samples/sample_fir_report.png

This intentionally tests ONE image so a transport/model issue can be diagnosed
without re-running the complete five-document dossier.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from clarity.config import settings
from clarity.vlm.client import VLMClient
from clarity.vlm.parser import parse_and_validate_extraction


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    args = parser.parse_args()

    image = args.image.read_bytes()
    client = VLMClient()
    doc_type = client.infer_document_type_from_filename(args.image.name)
    print(f"Endpoint: {settings.openai_api_base}")
    print(f"Model: {settings.vlm_default_model}")
    print(f"Transport: {'ollama-native' if client.use_native_ollama else 'openai-compatible'}")
    print(f"Filename type hint: {doc_type}")

    extraction, meta = client.extract_structured(
        image,
        document_type=doc_type,
    )
    print("--- extraction summary ---")
    print(json.dumps(extraction.model_dump(), indent=2, ensure_ascii=False))
    print("--- diagnostics ---")
    print(json.dumps({k: v for k, v in meta.items() if k != "raw_text"}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
