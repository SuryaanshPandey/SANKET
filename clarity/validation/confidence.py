"""Confidence quality gate and threshold checking."""

from typing import Any, Dict, List
from clarity.config import settings
from clarity.vlm.parser import PartyItem, StructuredExtraction


def check_confidence_thresholds(
    extraction: StructuredExtraction,
    threshold: float = settings.confidence_threshold,
) -> List[Dict[str, Any]]:
    """Flag fields falling below confidence threshold for human review."""
    flags: List[Dict[str, Any]] = []

    # Check overall confidence
    if extraction.overall_confidence < threshold:
        flags.append({
            "type": "low_overall_confidence",
            "field": "overall",
            "confidence": extraction.overall_confidence,
            "threshold": threshold,
            "message": f"Overall extraction confidence ({extraction.overall_confidence:.2f}) is below threshold ({threshold:.2f})",
        })

    # Parties
    for i, p in enumerate(extraction.parties):
        if isinstance(p, PartyItem) and p.confidence < threshold:
            flags.append({
                "type": "low_confidence_field",
                "field": f"parties[{i}]: {p.name}",
                "confidence": p.confidence,
                "threshold": threshold,
                "message": f"Party '{p.name}' confidence ({p.confidence:.2f}) below threshold",
            })

    # Dates
    for d in extraction.dates:
        if d.confidence < threshold:
            flags.append({
                "type": "low_confidence_field",
                "field": f"date:{d.label}",
                "value": d.value,
                "confidence": d.confidence,
                "threshold": threshold,
                "message": f"Date '{d.label}' ({d.value}) confidence ({d.confidence:.2f}) below threshold",
            })

    # Amounts
    for a in extraction.amounts:
        if a.confidence < threshold:
            flags.append({
                "type": "low_confidence_field",
                "field": f"amount:{a.label}",
                "value": f"{a.value:.2f}",
                "confidence": a.confidence,
                "threshold": threshold,
                "message": f"Amount '{a.label}' ({a.value:.2f}) confidence ({a.confidence:.2f}) below threshold",
            })

    # Identifiers
    for ident in extraction.identifiers:
        if ident.confidence < threshold:
            flags.append({
                "type": "low_confidence_field",
                "field": f"identifier:{ident.type}",
                "value": ident.value,
                "confidence": ident.confidence,
                "threshold": threshold,
                "message": f"Identifier '{ident.type}' ({ident.value}) confidence ({ident.confidence:.2f}) below threshold",
            })

    return flags
