"""Test FastAPI API routes."""

import io
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from clarity.api.app import app
from clarity.vlm.parser import AmountItem, DateItem, IdentifierItem, PartyItem, StructuredExtraction

from clarity.db.session import init_db

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "vlm_model" in data


def test_process_document_api():
    # Create sample image
    img = Image.new("RGB", (400, 300), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    mock_extraction = StructuredExtraction(
        document_type="invoice",
        parties=[PartyItem(name="Omega Corp", role="seller", confidence=0.97)],
        dates=[DateItem(label="Due Date", value="2026-08-01", confidence=0.96)],
        amounts=[AmountItem(label="Total", value=750.00, currency="USD", confidence=0.99)],
        identifiers=[IdentifierItem(type="PO Number", value="PO-4451", confidence=0.94)],
        raw_text="Omega Corp PO-4451 Due Date: 2026-08-01 Total: $750.00",
        notes_on_legibility="Clean",
        overall_confidence=0.97,
    )

    with patch("clarity.pipeline.runner.VLMClient") as MockVLM:
        instance = MockVLM.return_value
        instance.classify_document.return_value = {
            "document_type": "invoice",
            "confidence": 0.98,
            "model_used": "qwen3-vl:8b",
        }
        instance.extract_structured.return_value = (
            mock_extraction,
            {"model_used": "qwen3-vl:8b", "prompt_version": "2026.09.v1", "parsed": mock_extraction.model_dump()},
        )

        files = {"file": ("test_po.png", img_bytes, "image/png")}
        data = {
            "case_id": "CASE-2026-09",
            "actor_id": "auditor_1",
            "run_dual_validation": "false",
            "auto_escalate": "false",
        }

        response = client.post("/api/v1/documents/process", files=files, data=data)
        assert response.status_code == 200
        res_json = response.json()

        assert res_json["document_id"] is not None
        assert res_json["doc_type"] == "invoice"
        assert res_json["file_hash_sha256"] is not None
        assert len(res_json["field_items"]) >= 4
        assert len(res_json["audit_trail"]) >= 4

        # Test document retrieval endpoint
        doc_id = res_json["document_id"]
        doc_resp = client.get(f"/api/v1/documents/{doc_id}")
        assert doc_resp.status_code == 200
        doc_data = doc_resp.json()
        assert doc_data["id"] == doc_id
        assert doc_data["doc_type"] == "invoice"


def test_batch_process_api():
    img = Image.new("RGB", (300, 200), color=(250, 250, 250))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    mock_fir = StructuredExtraction(
        document_type="fir_report",
        parties=[PartyItem(name="Ramesh Kumar", role="accused", confidence=0.95)],
        dates=[DateItem(label="FIR Date", value="12-05-2026", confidence=0.95)],
        amounts=[],
        identifiers=[IdentifierItem(type="FIR Number", value="184/2026", confidence=0.95)],
        raw_text="FIR 184/2026",
        overall_confidence=0.95,
    )

    with patch("clarity.pipeline.runner.VLMClient") as MockVLM, patch("clarity.pipeline.batch.VLMClient", new=MockVLM):
        instance = MockVLM.return_value
        instance.classify_document.return_value = {
            "document_type": "fir_report",
            "confidence": 0.95,
            "model_used": "mock",
        }
        instance.extract_structured.return_value = (
            mock_fir,
            {"model_used": "mock", "prompt_version": "v1", "parsed": mock_fir.model_dump()},
        )

        files = [
            ("files", ("fir_1.png", img_bytes, "image/png")),
            ("files", ("fir_2.png", img_bytes, "image/png")),
        ]
        data = {
            "case_id": "CASE-API-BATCH",
            "actor_id": "auditor_batch",
            "run_dual_validation": "false",
            "auto_escalate": "false",
        }

        response = client.post("/api/v1/documents/batch-process", files=files, data=data)
        assert response.status_code == 200
        res_json = response.json()

        assert res_json["batch_id"] is not None
        assert res_json["total_documents"] == 2
        assert res_json["successful_count"] == 2
        assert "cross_document_intelligence" in res_json

        # Test batch get endpoint
        batch_id = res_json["batch_id"]
        batch_resp = client.get(f"/api/v1/batches/{batch_id}")
        assert batch_resp.status_code == 200
        b_data = batch_resp.json()
        assert b_data["batch_id"] == batch_id
        assert b_data["total_documents"] == 2


def test_sample_catalog():
    response = client.get("/api/v1/samples/catalog")
    assert response.status_code == 200
    catalog = response.json()
    assert isinstance(catalog, list)
    assert len(catalog) >= 5
    keys = [item["key"] for item in catalog]
    assert "police_case" in keys
    assert "receipts" in keys
    assert "invoices" in keys
    assert "financial" in keys
    assert "contracts" in keys


