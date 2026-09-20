"""Test suite for Indian Police Investigation document verification.

Covers:
- Statutory quality gates under CrPC/BNSS, IPC/BNS, and IEA/BSA
- Document classification taxonomy for Indian Police documents
- Structured schema extraction and compliance verification
"""

import pytest
from clarity.validation.police_rules import (
    verify_arrest_memo_compliance,
    verify_charge_sheet_compliance,
    verify_fir_compliance,
    verify_forensic_report_compliance,
    verify_medical_legal_compliance,
    verify_seizure_memo_compliance,
)
from clarity.validation.rules import evaluate_extraction_quality
from clarity.vlm.parser import (
    AmountItem,
    DateItem,
    IdentifierItem,
    PartyItem,
    StructuredExtraction,
)


def test_fir_compliance_valid():
    """Test clean FIR with all mandatory CrPC 154 provisions."""
    extraction = StructuredExtraction(
        document_type="fir_report",
        parties=[
            PartyItem(name="Smt. Meera Bai", role="complainant", confidence=0.9),
            PartyItem(name="Rajesh alias Kallu", role="accused", confidence=0.9),
        ],
        dates=[
            DateItem(label="Date of Occurrence", value="10/05/2026", confidence=0.9),
            DateItem(label="Date of Registration", value="11/05/2026", confidence=0.9),
        ],
        identifiers=[
            IdentifierItem(type="FIR Number", value="FIR No. 104/2026", confidence=0.95),
            IdentifierItem(type="Police Station", value="PS Hauz Khas", confidence=0.95),
            IdentifierItem(type="Acts & Sections", value="Sec 379 IPC / Sec 303 BNS", confidence=0.9),
        ],
        overall_confidence=0.92,
    )
    flags = verify_fir_compliance(extraction)
    assert len(flags) == 0


def test_fir_compliance_chronology_violation():
    """Test detection of impossible chronology (occurrence after registration)."""
    extraction = StructuredExtraction(
        document_type="fir_report",
        dates=[
            DateItem(label="Date of Occurrence", value="15/05/2026", confidence=0.9),
            DateItem(label="Date of Registration", value="10/05/2026", confidence=0.9),
        ],
        identifiers=[
            IdentifierItem(type="FIR Number", value="104/2026", confidence=0.9),
            IdentifierItem(type="Police Station", value="PS Kotwali", confidence=0.9),
            IdentifierItem(type="Acts & Sections", value="302 IPC", confidence=0.9),
        ],
    )
    flags = verify_fir_compliance(extraction)
    chronology_flag = next((f for f in flags if f["type"] == "chronology_violation"), None)
    assert chronology_flag is not None
    assert chronology_flag["severity"] == "critical"


def test_seizure_memo_two_panchas_requirement():
    """Test enforcement of Section 100(4) CrPC (minimum 2 independent Panch witnesses)."""
    # Case with only 1 Panch witness -> must flag
    extraction_one_panch = StructuredExtraction(
        document_type="seizure_memo",
        parties=[
            PartyItem(name="Inspector V. Sharma", role="investigating_officer", confidence=0.9),
            PartyItem(name="Mahesh Kumar", role="panch_witness", confidence=0.9),
        ],
        identifiers=[
            IdentifierItem(type="Seal Status", value="Sealed with SHO seal", confidence=0.9),
        ],
    )
    flags = verify_seizure_memo_compliance(extraction_one_panch)
    panch_flag = next((f for f in flags if f["type"] == "insufficient_panch_witnesses"), None)
    assert panch_flag is not None
    assert "at least 2 independent Panch witnesses" in panch_flag["message"]

    # Case with 2 Panch witnesses -> passes
    extraction_two_panchas = StructuredExtraction(
        document_type="seizure_memo",
        parties=[
            PartyItem(name="Inspector V. Sharma", role="investigating_officer", confidence=0.9),
            PartyItem(name="Mahesh Kumar", role="panch_witness", confidence=0.9),
            PartyItem(name="Ramesh Singh", role="panch_witness", confidence=0.9),
        ],
        identifiers=[
            IdentifierItem(type="Seal Status", value="Sealed with SHO seal", confidence=0.9),
        ],
    )
    flags2 = verify_seizure_memo_compliance(extraction_two_panchas)
    panch_flag2 = next((f for f in flags2 if f["type"] == "insufficient_panch_witnesses"), None)
    assert panch_flag2 is None


def test_arrest_memo_dk_basu_compliance():
    """Test D.K. Basu guidelines verification (grounds of arrest, family intimation)."""
    # Missing grounds and family intimation
    extraction_non_compliant = StructuredExtraction(
        document_type="arrest_memo",
        parties=[
            PartyItem(name="Suraj Verma", role="arrestee", confidence=0.9),
            PartyItem(name="SI Amit Kumar", role="arresting_officer", confidence=0.9),
        ],
        identifiers=[],
    )
    flags = verify_arrest_memo_compliance(extraction_non_compliant)
    flag_types = [f["type"] for f in flags]
    assert "missing_grounds_of_arrest" in flag_types
    assert "missing_family_intimation" in flag_types

    # Compliant arrest memo
    extraction_compliant = StructuredExtraction(
        document_type="arrest_memo",
        parties=[
            PartyItem(name="Suraj Verma", role="arrestee", confidence=0.9),
            PartyItem(name="SI Amit Kumar", role="arresting_officer", confidence=0.9),
            PartyItem(name="Radha Verma (Wife)", role="intimated_person", confidence=0.9),
        ],
        identifiers=[
            IdentifierItem(type="Grounds of Arrest", value="Arrested in bank fraud", confidence=0.9),
            IdentifierItem(type="Physical Condition", value="No visible external injuries", confidence=0.9),
        ],
    )
    flags_ok = verify_arrest_memo_compliance(extraction_compliant)
    assert len(flags_ok) == 0


def test_charge_sheet_compliance():
    """Test Charge Sheet under Sec 173 CrPC requirements."""
    extraction = StructuredExtraction(
        document_type="charge_sheet",
        parties=[
            PartyItem(name="Karthik Sundaram", role="accused_chargesheeted", confidence=0.9),
            PartyItem(name="Sanjay Nambiar", role="prosecution_witness", confidence=0.9),
        ],
        identifiers=[
            IdentifierItem(type="Court Name", value="Chief Metropolitan Magistrate", confidence=0.9),
            IdentifierItem(type="Acts & Sections", value="Sec 420, 120B IPC", confidence=0.9),
        ],
    )
    flags = verify_charge_sheet_compliance(extraction)
    assert len(flags) == 0


def test_medical_legal_compliance():
    """Test Medico-Legal / Injury Report requirements."""
    extraction = StructuredExtraction(
        document_type="medical_legal",
        parties=[
            PartyItem(name="Dr. Sneha Kulkarni", role="examining_doctor", confidence=0.9),
            PartyItem(name="Arvind Sharma", role="victim", confidence=0.9),
        ],
        identifiers=[
            IdentifierItem(type="Injury Classification", value="Grievous injury over forearm", confidence=0.9),
        ],
        raw_text="The injury is grievous in nature caused by sharp cutting weapon.",
    )
    flags = verify_medical_legal_compliance(extraction)
    assert len(flags) == 0


def test_forensic_report_digital_hash_verification():
    """Test Section 65B electronic evidence digital hash requirement."""
    # Missing digital hash -> flags
    ext_no_hash = StructuredExtraction(
        document_type="forensic_report",
        parties=[PartyItem(name="Dr. A. Mathur", role="forensic_analyst", confidence=0.9)],
        raw_text="Extracted data from seized mobile phone.",
    )
    flags = verify_forensic_report_compliance(ext_no_hash)
    assert any(f["type"] == "missing_digital_hash" for f in flags)

    # Valid SHA-256 hash -> passes
    ext_with_hash = StructuredExtraction(
        document_type="forensic_report",
        parties=[PartyItem(name="Dr. A. Mathur", role="forensic_analyst", confidence=0.9)],
        identifiers=[
            IdentifierItem(
                type="SHA-256 Hash",
                value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                confidence=0.95,
            )
        ],
    )
    flags_ok = verify_forensic_report_compliance(ext_with_hash)
    assert len(flags_ok) == 0


def test_evaluate_extraction_quality_dispatches_police_rules():
    """Test that evaluate_extraction_quality automatically triggers police validation rules."""
    extraction = StructuredExtraction(
        document_type="seizure_memo",
        parties=[PartyItem(name="Mahesh", role="panch_witness", confidence=0.9)],  # Only 1 witness
        identifiers=[],
        overall_confidence=0.9,
    )
    report = evaluate_extraction_quality(extraction, doc_type="seizure_memo")
    assert not report.is_valid
    assert any(f["type"] == "insufficient_panch_witnesses" for f in report.flags)
    assert report.needs_escalation is True
