"""Dual-run differential verification between deterministic and non-zero temperature runs."""

import re
from typing import Any, Dict, List
from clarity.vlm.parser import StructuredExtraction


def _clean_str(s: str) -> str:
    return re.sub(r"[\s\-_.,/]", "", s.lower())


def diff_extractions(
    primary: StructuredExtraction,
    secondary: StructuredExtraction,
    amount_tolerance: float = 0.05,
) -> List[Dict[str, Any]]:
    """Compare primary extraction (T=0) with secondary validation run (T>0).

    Returns list of discrepancies and divergences.
    """
    disagreements: List[Dict[str, Any]] = []

    # 1. Document type check
    if _clean_str(primary.document_type) != _clean_str(secondary.document_type):
        disagreements.append({
            "type": "dual_run_doc_type_disagreement",
            "field": "document_type",
            "primary": primary.document_type,
            "secondary": secondary.document_type,
            "message": f"Document type differs between runs ('{primary.document_type}' vs '{secondary.document_type}')",
        })

    # 2. Amounts check
    # Match amounts by label or position
    prim_amounts = {i: a for i, a in enumerate(primary.amounts)}
    sec_amounts = {i: a for i, a in enumerate(secondary.amounts)}

    # Compare values
    for i, a1 in prim_amounts.items():
        if i in sec_amounts:
            a2 = sec_amounts[i]
            diff = abs(a1.value - a2.value)
            if diff > amount_tolerance:
                disagreements.append({
                    "type": "dual_run_amount_disagreement",
                    "field": f"amount[{i}]: {a1.label}",
                    "primary": a1.value,
                    "secondary": a2.value,
                    "difference": round(diff, 2),
                    "message": f"Amount divergence on '{a1.label}': primary={a1.value:.2f}, secondary={a2.value:.2f}",
                })

    # 3. Dates check
    prim_dates = {i: d for i, d in enumerate(primary.dates)}
    sec_dates = {i: d for i, d in enumerate(secondary.dates)}
    for i, d1 in prim_dates.items():
        if i in sec_dates:
            d2 = sec_dates[i]
            if _clean_str(d1.value) != _clean_str(d2.value):
                disagreements.append({
                    "type": "dual_run_date_disagreement",
                    "field": f"date[{i}]: {d1.label}",
                    "primary": d1.value,
                    "secondary": d2.value,
                    "message": f"Date divergence on '{d1.label}': primary='{d1.value}', secondary='{d2.value}'",
                })

    # 4. Identifiers check
    prim_ids = {i: ident for i, ident in enumerate(primary.identifiers)}
    sec_ids = {i: ident for i, ident in enumerate(secondary.identifiers)}
    for i, id1 in prim_ids.items():
        if i in sec_ids:
            id2 = sec_ids[i]
            if _clean_str(id1.value) != _clean_str(id2.value):
                disagreements.append({
                    "type": "dual_run_identifier_disagreement",
                    "field": f"identifier[{i}]: {id1.type}",
                    "primary": id1.value,
                    "secondary": id2.value,
                    "message": f"Identifier divergence on '{id1.type}': primary='{id1.value}', secondary='{id2.value}'",
                })

    return disagreements
