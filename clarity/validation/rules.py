"""Validation orchestrator and quality gate rules."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from clarity.config import settings
from clarity.validation.arithmetic import verify_invoice_arithmetic
from clarity.validation.confidence import check_confidence_thresholds
from clarity.validation.dual_run import diff_extractions
from clarity.validation.police_rules import (
    verify_arrest_memo_compliance,
    verify_charge_sheet_compliance,
    verify_fir_compliance,
    verify_forensic_report_compliance,
    verify_medical_legal_compliance,
    verify_seizure_memo_compliance,
)
from clarity.vlm.parser import StructuredExtraction


@dataclass
class ValidationReport:
    is_valid: bool
    needs_escalation: bool
    escalation_reason: Optional[str]
    flags: List[Dict[str, Any]] = field(default_factory=list)
    arithmetic_result: Optional[Dict[str, Any]] = None
    dual_run_disagreements: List[Dict[str, Any]] = field(default_factory=list)


def evaluate_extraction_quality(
    primary_extraction: StructuredExtraction,
    doc_type: str,
    secondary_extraction: Optional[StructuredExtraction] = None,
    max_flags: int = settings.max_flagged_fields_before_escalation,
    confidence_threshold: float = settings.confidence_threshold,
    tolerance: float = settings.arithmetic_tolerance,
) -> ValidationReport:
    """Run all quality gates: statutory police compliance, arithmetic checks, and confidence checks."""
    all_flags: List[Dict[str, Any]] = []
    needs_escalation = False
    escalation_reasons: List[str] = []

    # 1. Statutory Indian Police Legal Quality Gates
    police_flags: List[Dict[str, Any]] = []
    if doc_type == "fir_report":
        police_flags = verify_fir_compliance(primary_extraction)
    elif doc_type == "seizure_memo":
        police_flags = verify_seizure_memo_compliance(primary_extraction)
    elif doc_type == "arrest_memo":
        police_flags = verify_arrest_memo_compliance(primary_extraction)
    elif doc_type == "charge_sheet":
        police_flags = verify_charge_sheet_compliance(primary_extraction)
    elif doc_type == "medical_legal":
        police_flags = verify_medical_legal_compliance(primary_extraction)
    elif doc_type == "forensic_report":
        police_flags = verify_forensic_report_compliance(primary_extraction)

    all_flags.extend(police_flags)
    critical_police_flags = [f for f in police_flags if f.get("severity") == "critical"]
    if critical_police_flags:
        needs_escalation = True
        escalation_reasons.append(f"Critical statutory compliance violations: {critical_police_flags[0]['message']}")

    # 2. Arithmetic verification for financial documents
    arithmetic_valid = True
    arithmetic_detail = None
    if doc_type in ["invoice", "receipt", "bank_statement"]:
        arithmetic_valid, arithmetic_detail = verify_invoice_arithmetic(
            primary_extraction.amounts, tolerance=tolerance
        )
        if not arithmetic_valid and arithmetic_detail:
            flag = {
                "type": "arithmetic_mismatch",
                "field": "amounts_sum",
                "detail": arithmetic_detail,
                "message": arithmetic_detail.get("message", "Arithmetic mismatch detected"),
            }
            all_flags.append(flag)
            needs_escalation = True
            escalation_reasons.append("Invoice line-item arithmetic mismatch")

    # 3. Confidence threshold inspection
    confidence_flags = check_confidence_thresholds(primary_extraction, threshold=confidence_threshold)
    all_flags.extend(confidence_flags)

    # 3. Dual-run diff comparison if secondary run exists
    dual_run_flags: List[Dict[str, Any]] = []
    if secondary_extraction is not None:
        dual_run_flags = diff_extractions(primary_extraction, secondary_extraction)
        all_flags.extend(dual_run_flags)

    # 4. Check escalation thresholds
    if len(all_flags) > max_flags:
        needs_escalation = True
        escalation_reasons.append(f"Flagged fields count ({len(all_flags)}) exceeded limit ({max_flags})")

    if primary_extraction.overall_confidence < (confidence_threshold - 0.10):
        needs_escalation = True
        escalation_reasons.append(
            f"Overall confidence ({primary_extraction.overall_confidence:.2f}) critically low"
        )

    escalation_reason_str = "; ".join(escalation_reasons) if escalation_reasons else None

    return ValidationReport(
        is_valid=(len(all_flags) == 0),
        needs_escalation=needs_escalation,
        escalation_reason=escalation_reason_str,
        flags=all_flags,
        arithmetic_result=arithmetic_detail,
        dual_run_disagreements=dual_run_flags,
    )
