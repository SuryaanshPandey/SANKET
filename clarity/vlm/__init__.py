"""VLM package for multimodal inference, prompting, and parsing."""

from clarity.vlm.client import VLMClient
from clarity.vlm.parser import StructuredExtraction, flatten_extracted_fields, parse_and_validate_extraction
from clarity.vlm.prompts import PROMPT_VERSION

__all__ = [
    "VLMClient",
    "StructuredExtraction",
    "parse_and_validate_extraction",
    "flatten_extracted_fields",
    "PROMPT_VERSION",
]
