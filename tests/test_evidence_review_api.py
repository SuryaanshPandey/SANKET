import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from clarity.api.app import app
from clarity.db.session import init_db
from clarity.vlm.parser import StructuredExtraction, PartyItem, IdentifierItem

client = TestClient(app)

def _image():
    img = Image.new("RGB", (120, 80), color=(250, 250, 250))
    buf = io.BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()

def test_case_evidence_review_endpoint():
    init_db()
    extraction = StructuredExtraction(
        document_type="fir_report",
        parties=[PartyItem(name="Ramesh Kumar", role="accused", confidence=0.95)],
        dates=[], amounts=[],
        identifiers=[IdentifierItem(type="FIR Number", value="29/17", confidence=0.9)],
        raw_text="FIR 29/17", overall_confidence=0.9,
    )
    with patch("clarity.pipeline.runner.VLMClient") as MockVLM, patch("clarity.pipeline.batch.VLMClient", new=MockVLM):
        instance = MockVLM.return_value
        instance.classify_document.return_value = {"document_type": "fir_report", "confidence": 0.9, "model_used": "mock"}
        instance.extract_structured.return_value = (extraction, {"model_used": "mock", "prompt_version": "v1", "parsed": extraction.model_dump()})
        response = client.post("/api/v1/documents/batch-process", files=[("files", ("fir.png", _image(), "image/png"))], data={"case_id": "CASE-EVIDENCE-REVIEW", "run_dual_validation": "false", "auto_escalate": "false"})
        assert response.status_code == 200

    review = client.get("/api/v1/cases/CASE-EVIDENCE-REVIEW/evidence-review")
    assert review.status_code == 200
    body = review.json()
    assert body["case_id"] == "CASE-EVIDENCE-REVIEW"
    assert body["provenance"]["summary"]["field_items"] >= 1
    assert "contradictions" in body
