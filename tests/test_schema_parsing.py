"""Test defensive JSON schema parsing and recovery."""

import pytest
from clarity.vlm.parser import (
    extract_json_substring,
    flatten_extracted_fields,
    parse_and_validate_extraction,
    repair_common_json_issues,
)


def test_markdown_fence_stripping():
    wrapped_json = """Here is the extracted document data:
```json
{
  "document_type": "invoice",
  "parties": [{"name": "Acme Corp", "role": "vendor", "confidence": 0.95}],
  "dates": [{"label": "invoice_date", "value": "2026-04-10", "confidence": 0.98, "bounding_box": {"x": 100, "y": 200, "w": 300, "h": 50}}],
  "amounts": [{"label": "total", "value": 1540.50, "currency": "USD", "confidence": 0.99}],
  "identifiers": [{"type": "invoice_number", "value": "INV-2026-001", "confidence": 0.97}],
  "raw_text": "Invoice from Acme Corp",
  "notes_on_legibility": "Clear scan",
  "overall_confidence": 0.96
}
```
Let me know if you need more analysis."""

    extracted = parse_and_validate_extraction(wrapped_json)
    assert extracted.document_type == "invoice"
    assert len(extracted.parties) == 1
    assert extracted.parties[0].name == "Acme Corp"
    assert len(extracted.amounts) == 1
    assert extracted.amounts[0].value == 1540.50
    assert extracted.amounts[0].currency == "USD"
    assert extracted.overall_confidence == 0.96


def test_trailing_commas_repair():
    malformed_json = """{
      "document_type": "receipt",
      "parties": ["Store 123",],
      "dates": [],
      "amounts": [
        {"label": "total", "value": "$45.99", "currency": "USD", "confidence": 0.9,},
      ],
      "identifiers": [],
      "raw_text": "Total 45.99",
      "notes_on_legibility": "Slight crumple",
      "overall_confidence": 0.88,
    }"""

    extracted = parse_and_validate_extraction(malformed_json)
    assert extracted.document_type == "receipt"
    assert extracted.amounts[0].value == 45.99


def test_flattening_fields():
    json_str = """{
      "document_type": "contract",
      "parties": [{"name": "Alice Inc", "role": "buyer", "confidence": 0.92}],
      "dates": [{"label": "effective_date", "value": "2026-01-01", "confidence": 0.88}],
      "amounts": [{"label": "deposit", "value": 5000, "currency": "EUR", "confidence": 0.95}],
      "identifiers": [{"type": "contract_id", "value": "CTR-999", "confidence": 0.90}],
      "raw_text": "Contract text",
      "notes_on_legibility": "Good",
      "overall_confidence": 0.91
    }"""

    extracted = parse_and_validate_extraction(json_str)
    flat = flatten_extracted_fields(extracted)

    field_names = [f["field_name"] for f in flat]
    assert any("buyer" in name for name in field_names)
    assert any("effective_date" in name for name in field_names)
    assert any("deposit" in name for name in field_names)
    assert any("contract_id" in name for name in field_names)
