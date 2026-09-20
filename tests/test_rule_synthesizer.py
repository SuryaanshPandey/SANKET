"""Tests for rule-derived field and entity synthesis."""

from clarity.validation.rule_synthesizer import synthesize_rule_fields_and_entities
from clarity.validation.rules import ValidationReport
from clarity.vlm.parser import AmountItem, DateItem, IdentifierItem, PartyItem, StructuredExtraction


def test_fir_rule_synthesis():
    extraction = StructuredExtraction(
        document_type="fir_report",
        parties=[PartyItem(name="Ramesh Kumar", role="accused", confidence=0.95)],
        dates=[
            DateItem(label="Occurrence Date", value="12-05-2026", confidence=0.95),
            DateItem(label="Registration Date", value="13-05-2026", confidence=0.95),
        ],
        amounts=[],
        identifiers=[
            IdentifierItem(type="FIR Number", value="184/2026", confidence=0.95),
            IdentifierItem(type="Police Station", value="Vasant Vihar", confidence=0.95),
            IdentifierItem(type="Sections", value="379, 411 IPC", confidence=0.95),
        ],
        raw_text="FIR 184/2026 registered at Vasant Vihar PS u/s 379, 411 IPC",
        overall_confidence=0.95,
    )
    val_report = ValidationReport(is_valid=True, needs_escalation=False, escalation_reason=None, flags=[])

    fields, new_parties = synthesize_rule_fields_and_entities("fir_report", extraction, val_report)
    field_names = [f["field_name"] for f in fields]

    assert "rule:fir_statutory_basis" in field_names
    assert "rule:temporal_integrity_status" in field_names
    assert "rule:penal_sections_detected" in field_names
    assert "rule:quality_gate_status" in field_names


def test_seizure_memo_rule_synthesis():
    extraction = StructuredExtraction(
        document_type="seizure_memo",
        parties=[
            PartyItem(name="Anil Sharma", role="panch_witness", confidence=0.90),
            PartyItem(name="Sunil Gupta", role="panch_witness", confidence=0.90),
            PartyItem(name="Ramesh Kumar", role="person from whom recovered", confidence=0.95),
        ],
        dates=[DateItem(label="Date", value="14-05-2026", confidence=0.95)],
        amounts=[AmountItem(label="iPhone 15", value=135000.0, currency="INR", confidence=0.95)],
        identifiers=[
            IdentifierItem(type="Seal Status", value="Intact sample seal impression affixed", confidence=0.95),
        ],
        raw_text="Seized articles in presence of two independent panch witnesses Anil Sharma and Sunil Gupta",
        overall_confidence=0.94,
    )
    val_report = ValidationReport(is_valid=True, needs_escalation=False, escalation_reason=None, flags=[])

    fields, new_parties = synthesize_rule_fields_and_entities("seizure_memo", extraction, val_report)
    field_map = {f["field_name"]: f["field_value"] for f in fields}

    assert "rule:panchnama_statutory_validity" in field_map
    assert "COMPLIANT" in field_map["rule:panchnama_statutory_validity"]
    assert field_map["rule:independent_witness_count"] == "2"
    assert "rule:sample_seal_condition" in field_map


def test_arrest_memo_dk_basu_synthesis():
    extraction = StructuredExtraction(
        document_type="arrest_memo",
        parties=[
            PartyItem(name="Ramesh Kumar", role="arrestee", confidence=0.95)],
        dates=[DateItem(label="Date of Arrest", value="14-05-2026", confidence=0.95)],
        amounts=[],
        identifiers=[
            IdentifierItem(type="Grounds of Arrest", value="Possession of stolen iPhone under Section 411 IPC", confidence=0.95),
        ],
        raw_text="Arrested Ramesh Kumar. Grounds explained. Next-of-kin informed.",
        overall_confidence=0.95,
    )
    val_report = ValidationReport(is_valid=True, needs_escalation=False, escalation_reason=None, flags=[])

    fields, new_parties = synthesize_rule_fields_and_entities("arrest_memo", extraction, val_report)
    field_map = {f["field_name"]: f["field_value"] for f in fields}

    assert "rule:dk_basu_compliance_status" in field_map
    assert "rule:grounds_of_arrest_disclosed" in field_map
    assert "rule:custodial_medical_exam_deadline" in field_map
