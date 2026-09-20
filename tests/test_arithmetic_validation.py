"""Test arithmetic cross-check logic for financial documents."""

import pytest
from clarity.validation.arithmetic import verify_invoice_arithmetic
from clarity.vlm.parser import AmountItem


def test_matching_subtotal_and_tax():
    amounts = [
        AmountItem(label="Subtotal", value=100.00, currency="USD"),
        AmountItem(label="Sales Tax", value=8.25, currency="USD"),
        AmountItem(label="Total Amount", value=108.25, currency="USD"),
    ]
    is_valid, detail = verify_invoice_arithmetic(amounts)
    assert is_valid is True
    assert detail is not None
    assert detail["matched"] is True


def test_mismatch_subtotal_and_tax():
    amounts = [
        AmountItem(label="Subtotal", value=100.00, currency="USD"),
        AmountItem(label="Tax", value=10.00, currency="USD"),
        AmountItem(label="Grand Total", value=125.00, currency="USD"),  # 100+10 != 125
    ]
    is_valid, detail = verify_invoice_arithmetic(amounts)
    assert is_valid is False
    assert detail is not None
    assert detail["difference"] == 15.00
    assert "does not match" in detail["message"]


def test_line_items_sum():
    amounts = [
        AmountItem(label="Consulting Service A", value=250.00, currency="USD"),
        AmountItem(label="Software License B", value=750.00, currency="USD"),
        AmountItem(label="Total", value=1000.00, currency="USD"),
    ]
    is_valid, detail = verify_invoice_arithmetic(amounts)
    assert is_valid is True
    assert detail["matched"] is True


def test_line_items_mismatch():
    amounts = [
        AmountItem(label="Consulting Service A", value=250.00, currency="USD"),
        AmountItem(label="Software License B", value=700.00, currency="USD"),
        AmountItem(label="Total", value=1000.00, currency="USD"),  # 950 != 1000
    ]
    is_valid, detail = verify_invoice_arithmetic(amounts)
    assert is_valid is False
    assert detail["difference"] == 50.00
