from clarity.intelligence.contradiction_engine import ContradictionEngine


def _doc(doc_id, filename, fields):
    return {
        "document_id": doc_id,
        "original_filename": filename,
        "file_hash_sha256": "a" * 64,
        "field_items": fields,
    }


def _field(name, value, confidence=0.9, bbox=None):
    return {"field_name": name, "field_value": value, "confidence": confidence, "bounding_box": bbox}


def test_detects_conflicting_case_references():
    report = ContradictionEngine().analyze([
        _doc("d1", "fir.png", [_field("id:FIR Number", "29/17")]),
        _doc("d2", "seizure.png", [_field("id:Case / FIR No", "184/2026")]),
        _doc("d3", "forensic.png", [_field("id:FSL/crime reference number.", "RC-218/2026/EOW")]),
    ], case_id="CASE-1")
    assert report.contradiction_count == 1
    assert report.items[0].type == "IDENTIFIER_MISMATCH"
    assert report.items[0].severity == "high"
    assert {o.value for o in report.items[0].observations} == {"29/17", "184/2026", "RC-218/2026/EOW"}


def test_ignores_identical_values():
    report = ContradictionEngine().analyze([
        _doc("d1", "a.png", [_field("id:Police Station / Thana", "PS: Airport")]),
        _doc("d2", "b.png", [_field("id:Police Station / Thana", "PS: Airport")]),
    ])
    assert report.contradiction_count == 0


def test_preserves_bounding_boxes_and_confidence():
    report = ContradictionEngine().analyze([
        _doc("d1", "a.png", [_field("id:FIR Number", "29/17", 0.8, {"x": 1, "y": 2, "w": 3, "h": 4})]),
        _doc("d2", "b.png", [_field("id:FIR Number", "184/2026", 0.7)]),
    ])
    obs = report.items[0].observations[0]
    assert obs.confidence in {0.7, 0.8}
    assert obs.bounding_box is None or obs.bounding_box["w"] == 3.0


def test_does_not_flag_empty_values():
    report = ContradictionEngine().analyze([
        _doc("d1", "a.png", [_field("id:FIR Number", "")]),
        _doc("d2", "b.png", [_field("id:FIR Number", "184/2026")]),
    ])
    assert report.contradiction_count == 0
