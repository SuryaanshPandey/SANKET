"""Tests for Cross-Document Intelligence, Entity Reconciliation, and Timeline Synthesis."""

import pytest
from clarity.pipeline.cross_document import CrossDocumentAggregator, normalize_name, parse_date_to_sortable


def test_normalize_name():
    assert normalize_name("Ramesh Kumar s/o Late Mohan Lal") == "Ramesh Kumar"
    assert normalize_name("SI Rajesh Sharma, age 42") == "Rajesh Sharma"
    assert normalize_name("Shri Vikramaditya Singh") == "Vikramaditya Singh"
    assert normalize_name("Dr. P.K. Verma") == "P.K. Verma"


def test_parse_date_to_sortable():
    dt1 = parse_date_to_sortable("14-05-2026")
    assert dt1 is not None
    assert dt1.year == 2026 and dt1.month == 5 and dt1.day == 14

    dt2 = parse_date_to_sortable("2026-05-12")
    assert dt2 is not None
    assert dt2.year == 2026 and dt2.month == 5 and dt2.day == 12


def test_cross_document_aggregator_reconciliation():
    aggregator = CrossDocumentAggregator()

    mock_docs = [
        {
            "document_id": "doc-1",
            "original_filename": "01_fir_report.png",
            "doc_type": "fir_report",
            "overall_confidence": 0.95,
            "extracted_data": {
                "parties": [
                    {"name": "Ramesh Kumar s/o Mohan Lal", "role": "accused", "confidence": 0.95},
                    {"name": "SI Rajesh Sharma", "role": "investigating_officer", "confidence": 0.92},
                ],
                "dates": [{"label": "Date of FIR", "value": "12-05-2026"}],
                "identifiers": [
                    {"type": "FIR Number", "value": "184/2026"},
                    {"type": "Police Station", "value": "Vasant Vihar"},
                ],
                "amounts": [],
            },
        },
        {
            "document_id": "doc-2",
            "original_filename": "02_seizure_memo.png",
            "doc_type": "seizure_memo",
            "overall_confidence": 0.93,
            "extracted_data": {
                "parties": [
                    {"name": "Ramesh Kumar", "role": "person from whom recovered", "confidence": 0.94},
                    {"name": "Vikramaditya Singh", "role": "panch_witness", "confidence": 0.90},
                    {"name": "Harish Chand", "role": "panch_witness", "confidence": 0.88},
                ],
                "dates": [{"label": "Date of Seizure", "value": "14-05-2026"}],
                "identifiers": [
                    {"type": "FIR Number", "value": "184/2026"},
                    {"type": "IMEI No", "value": "356891094821034"},
                ],
                "amounts": [
                    {"label": "iPhone 15 Pro", "value": 135000.0, "currency": "INR"},
                    {"label": "Dell Laptop", "value": 85000.0, "currency": "INR"},
                ],
            },
        },
        {
            "document_id": "doc-3",
            "original_filename": "03_arrest_memo.png",
            "doc_type": "arrest_memo",
            "overall_confidence": 0.94,
            "extracted_data": {
                "parties": [
                    {"name": "Ramesh Kumar", "role": "arrestee", "confidence": 0.96},
                    {"name": "SI Rajesh Sharma", "role": "arresting_officer", "confidence": 0.95},
                ],
                "dates": [{"label": "Date of Arrest", "value": "14-05-2026"}],
                "identifiers": [
                    {"type": "FIR Number", "value": "184/2026"},
                ],
                "amounts": [],
            },
        },
    ]

    analysis = aggregator.analyze(mock_docs)

    assert analysis.total_documents == 3
    assert analysis.doc_types["fir_report"] == 1
    assert analysis.doc_types["seizure_memo"] == 1
    assert analysis.doc_types["arrest_memo"] == 1

    # Check Entity Reconciliation: Ramesh Kumar should appear in 3 documents
    ramesh = next((e for e in analysis.reconciled_entities if "Ramesh" in e["canonical_name"]), None)
    assert ramesh is not None
    assert ramesh["document_count"] == 3
    assert "accused" in ramesh["roles"]
    assert "arrestee" in ramesh["roles"]

    # SI Rajesh Sharma should appear in 2 documents
    rajesh = next((e for e in analysis.reconciled_entities if "Rajesh" in e["canonical_name"]), None)
    assert rajesh is not None
    assert rajesh["document_count"] == 2

    # Check Master Chronological Timeline
    timeline = analysis.master_timeline
    assert len(timeline) == 3
    # Earliest date should be FIR (12-05-2026)
    assert "12" in timeline[0]["raw_date"]

    # Check Financial Ledger
    ledger = analysis.financial_ledger
    assert ledger["total_amount"] == 220000.0
    assert ledger["currency"] == "INR"
    assert len(ledger["items"]) == 2

    # Check Identifiers
    fir_ref = next((r for r in analysis.cross_references if "FIR" in r["identifier_type"]), None)
    assert fir_ref is not None
    assert fir_ref["value"] == "184/2026"
    assert fir_ref["document_count"] == 3


def test_timeline_contradiction_detection():
    aggregator = CrossDocumentAggregator()

    # Create contradiction: Seizure on May 10, but FIR on May 12!
    bad_docs = [
        {
            "document_id": "doc-1",
            "original_filename": "fir.png",
            "doc_type": "fir_report",
            "extracted_data": {
                "parties": [{"name": "Ramesh Kumar", "role": "accused"}],
                "dates": [{"label": "Date of FIR", "value": "12-05-2026"}],
                "identifiers": [{"type": "FIR Number", "value": "184/2026"}],
            },
        },
        {
            "document_id": "doc-2",
            "original_filename": "seizure.png",
            "doc_type": "seizure_memo",
            "extracted_data": {
                "parties": [{"name": "Ramesh Kumar", "role": "accused"}],
                "dates": [{"label": "Date of Seizure", "value": "10-05-2026"}],
                "identifiers": [{"type": "FIR Number", "value": "184/2026"}],
            },
        },
    ]

    analysis = aggregator.analyze(bad_docs)
    assert len(analysis.discrepancies) > 0
    flag = next((d for d in analysis.discrepancies if d["flag_type"] == "TEMPORAL_CONTRADICTION"), None)
    assert flag is not None
    assert "predates FIR registration date" in flag["message"]
