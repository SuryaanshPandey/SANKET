"""Tests for live investigation workflow API integration."""

import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from clarity.api.app import app
from clarity.db.session import init_db
from clarity.vlm.parser import StructuredExtraction, PartyItem, DateItem

client = TestClient(app)


def _img_bytes():
    img = Image.new("RGB", (200, 120), color=(245, 245, 245))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _seed_case():
    init_db()
    extraction = StructuredExtraction(
        document_type="fir_report",
        parties=[PartyItem(name="Ramesh Kumar", role="accused", confidence=0.95)],
        dates=[DateItem(label="Date of Occurrence", value="2026-06-10", confidence=0.95)], amounts=[], identifiers=[],
        raw_text="FIR 184/2026 Ramesh Kumar", overall_confidence=0.95,
    )
    with patch("clarity.pipeline.runner.VLMClient") as MockVLM, patch("clarity.pipeline.batch.VLMClient", new=MockVLM):
        instance = MockVLM.return_value
        instance.classify_document.return_value = {"document_type": "fir_report", "confidence": 0.95, "model_used": "mock"}
        instance.extract_structured.return_value = (extraction, {"model_used": "mock", "prompt_version": "v1", "parsed": extraction.model_dump()})
        files = [("files", ("fir.png", _img_bytes(), "image/png"))]
        data = {"case_id": "CASE-WORKFLOW-API", "actor_id": "test", "run_dual_validation": "false", "auto_escalate": "false"}
        response = client.post("/api/v1/documents/batch-process", files=files, data=data)
        assert response.status_code == 200
        return response.json()["case_id"]


def _workflow():
    return {
        "workflow_id": "wf-api-test",
        "version": "1.0.0",
        "name": "API Test Workflow",
        "nodes": [
            {"id": "time", "type": "TIME_FILTER", "config": {"start": "2026-01-01T00:00:00+00:00", "end": "2026-12-31T23:59:59+00:00"}},
            {"id": "expand", "type": "EXPAND_NETWORK", "config": {"depth": 1}},
            {"id": "report", "type": "REPORT", "config": {"include_node_outputs": True}},
        ],
        "edges": [
            {"id": "e1", "source_node_id": "time", "target_node_id": "expand"},
            {"id": "e2", "source_node_id": "expand", "target_node_id": "report"},
        ],
    }


def test_validate_and_execute_workflow_api():
    case_id = _seed_case()
    workflow = _workflow()
    validation = client.post(f"/api/v1/cases/{case_id}/workflows/validate", json=workflow)
    assert validation.status_code == 200
    assert validation.json()["valid"] is True

    execution = client.post(f"/api/v1/cases/{case_id}/workflows/execute", json=workflow)
    assert execution.status_code == 200
    body = execution.json()
    assert body["execution"]["status"] == "COMPLETED"
    assert body["execution"]["execution_id"].startswith("EXEC-")
    assert body["graph_summary"]["node_count"] >= 1
    assert "resolution" in body


def test_invalid_workflow_returns_validation_errors():
    case_id = _seed_case()
    workflow = _workflow()
    workflow["nodes"][1]["config"]["depth"] = 99
    response = client.post(f"/api/v1/cases/{case_id}/workflows/validate", json=workflow)
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert any(issue["code"] == "INVALID_DEPTH" for issue in payload["errors"])


def test_execute_workflow_returns_exportable_report():
    case_id = _seed_case()
    workflow = _workflow()
    response = client.post(f"/api/v1/cases/{case_id}/workflows/execute", json=workflow)
    assert response.status_code == 200
    body = response.json()
    assert body["report"]["execution_id"].startswith("EXEC-")
    assert "Analytical results are investigative leads" in body["report"]["markdown"]


def test_human_field_review_preserves_original_value():
    case_id = _seed_case()
    dossier = client.get(f"/api/v1/cases/{case_id}/dossier")
    assert dossier.status_code == 200
    field = dossier.json()["documents"][0]["field_items"][0]
    assert field["id"]
    original = field["field_value"]

    reviewed = client.patch(
        f"/api/v1/extracted-fields/{field['id']}/review?actor_id=test_reviewer",
        json={"human_verified": True, "corrected_value": original + " (reviewed)"},
    )
    assert reviewed.status_code == 200
    data = reviewed.json()
    assert data["original_value"] == original
    assert data["corrected_value"] == original + " (reviewed)"
    assert data["human_verified"] is True

    dossier_after = client.get(f"/api/v1/cases/{case_id}/dossier")
    refreshed = dossier_after.json()["documents"][0]["field_items"][0]
    assert refreshed["field_value"] == original
    assert refreshed["corrected_value"] == original + " (reviewed)"
    assert refreshed["human_verified"] is True
