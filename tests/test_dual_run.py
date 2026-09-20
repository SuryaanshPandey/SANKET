"""Test dual-run differential comparison."""

import pytest
from clarity.validation.dual_run import diff_extractions
from clarity.vlm.parser import AmountItem, DateItem, IdentifierItem, StructuredExtraction


def test_dual_run_identical():
    run1 = StructuredExtraction(
        document_type="invoice",
        dates=[DateItem(label="inv_date", value="2026-05-01")],
        amounts=[AmountItem(label="total", value=500.0)],
        identifiers=[IdentifierItem(type="inv_no", value="101")],
    )
    run2 = StructuredExtraction(
        document_type="invoice",
        dates=[DateItem(label="inv_date", value="2026-05-01")],
        amounts=[AmountItem(label="total", value=500.0)],
        identifiers=[IdentifierItem(type="inv_no", value="101")],
    )

    diffs = diff_extractions(run1, run2)
    assert len(diffs) == 0


def test_dual_run_amount_divergence():
    run1 = StructuredExtraction(
        document_type="invoice",
        amounts=[AmountItem(label="total", value=500.0)],
    )
    run2 = StructuredExtraction(
        document_type="invoice",
        amounts=[AmountItem(label="total", value=550.0)],
    )

    diffs = diff_extractions(run1, run2)
    assert len(diffs) == 1
    assert diffs[0]["type"] == "dual_run_amount_disagreement"
    assert diffs[0]["difference"] == 50.0
