"""Arithmetic cross-check logic for financial documents (invoices, receipts, bills)."""

import re
from typing import Any, Dict, List, Optional, Tuple
from clarity.vlm.parser import AmountItem


def normalize_label(label: str) -> str:
    return re.sub(r"[^a-z0-9]", "", label.lower())


def verify_invoice_arithmetic(
    amounts: List[AmountItem],
    tolerance: float = 0.02,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Verify that invoice line items, subtotals, and taxes sum to the stated total.

    Returns:
        (is_valid, detail_dict)
    """
    if not amounts or len(amounts) < 2:
        # Not enough amount fields to cross-check arithmetic
        return True, None

    # Classify amounts by label
    totals: List[AmountItem] = []
    subtotals: List[AmountItem] = []
    taxes: List[AmountItem] = []
    line_items: List[AmountItem] = []

    for item in amounts:
        norm = normalize_label(item.label)
        if any(term in norm for term in ["subtotal", "subtot", "netamount"]):
            subtotals.append(item)
        elif any(term in norm for term in ["tax", "vat", "gst", "salestax"]):
            taxes.append(item)
        elif any(term in norm for term in ["grandtotal", "totalamount", "total", "balance", "amountdue"]):
            totals.append(item)
        else:
            line_items.append(item)

    if not totals:
        # No explicit total identified
        return True, None

    # Take the most prominent stated total
    stated_total_item = max(totals, key=lambda x: x.value)
    stated_total = stated_total_item.value

    # Case A: We have subtotal (+ optional taxes)
    if subtotals:
        calc_sum = subtotals[0].value + sum(t.value for t in taxes)
        diff = abs(calc_sum - stated_total)
        if diff > tolerance:
            return False, {
                "check_type": "subtotal_plus_tax_vs_total",
                "stated_total": stated_total,
                "subtotal": subtotals[0].value,
                "taxes_sum": sum(t.value for t in taxes),
                "calculated_sum": round(calc_sum, 2),
                "difference": round(diff, 2),
                "message": f"Stated total ({stated_total:.2f}) does not match subtotal + tax ({calc_sum:.2f}), diff: {diff:.2f}",
            }
        return True, {
            "check_type": "subtotal_plus_tax_vs_total",
            "stated_total": stated_total,
            "calculated_sum": round(calc_sum, 2),
            "difference": round(diff, 2),
            "matched": True,
        }

    # Case B: We have multiple line items and a total
    if len(line_items) >= 2:
        calc_sum = sum(item.value for item in line_items)
        diff = abs(calc_sum - stated_total)
        if diff > tolerance:
            return False, {
                "check_type": "line_items_sum_vs_total",
                "stated_total": stated_total,
                "line_items_count": len(line_items),
                "calculated_sum": round(calc_sum, 2),
                "difference": round(diff, 2),
                "message": f"Stated total ({stated_total:.2f}) does not match sum of {len(line_items)} line items ({calc_sum:.2f}), diff: {diff:.2f}",
            }
        return True, {
            "check_type": "line_items_sum_vs_total",
            "stated_total": stated_total,
            "calculated_sum": round(calc_sum, 2),
            "difference": round(diff, 2),
            "matched": True,
        }

    return True, None
