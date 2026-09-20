"""Tests for BatchExtractionPipeline and multi-document ingestion."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from PIL import Image
import io

from clarity.db.models import Base
from clarity.db.session import engine, get_db_session
from clarity.pipeline.batch import BatchExtractionPipeline
from clarity.pipeline.runner import DocumentExtractionPipeline
from clarity.vlm.parser import AmountItem, DateItem, IdentifierItem, PartyItem, StructuredExtraction


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def create_dummy_image_bytes(color=(255, 255, 255)):
    img = Image.new("RGB", (200, 200), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_batch_extraction_pipeline_with_mock():
    mock_vlm = MagicMock()
    mock_vlm.classify_document.side_effect = [
        {"document_type": "fir_report", "model_used": "mock"},
        {"document_type": "seizure_memo", "model_used": "mock"},
    ]

    extraction_fir = StructuredExtraction(
        document_type="fir_report",
        parties=[PartyItem(name="Ramesh Kumar", role="accused", confidence=0.95)],
        dates=[DateItem(label="FIR Date", value="12-05-2026", confidence=0.95)],
        amounts=[],
        identifiers=[IdentifierItem(type="FIR Number", value="184/2026", confidence=0.95)],
        raw_text="FIR 184/2026 registered against Ramesh Kumar",
        overall_confidence=0.95,
    )

    extraction_seizure = StructuredExtraction(
        document_type="seizure_memo",
        parties=[
            PartyItem(name="Ramesh Kumar", role="person from whom recovered", confidence=0.95),
            PartyItem(name="Vikramaditya Singh", role="panch_witness", confidence=0.90),
        ],
        dates=[DateItem(label="Seizure Date", value="14-05-2026", confidence=0.95)],
        amounts=[AmountItem(label="iPhone 15", value=135000.0, currency="INR", confidence=0.95)],
        identifiers=[IdentifierItem(type="FIR Number", value="184/2026", confidence=0.95)],
        raw_text="Seized iPhone 15 from Ramesh Kumar in presence of Vikramaditya Singh",
        overall_confidence=0.94,
    )

    mock_vlm.extract_structured.side_effect = [
        (extraction_fir, {"model_used": "mock", "prompt_version": "v1", "parsed": extraction_fir.model_dump()}),
        (extraction_seizure, {"model_used": "mock", "prompt_version": "v1", "parsed": extraction_seizure.model_dump()}),
    ]

    doc_pipeline = DocumentExtractionPipeline(vlm_client=mock_vlm)
    batch_pipeline = BatchExtractionPipeline(vlm_client=mock_vlm, doc_pipeline=doc_pipeline)

    img1 = create_dummy_image_bytes(color=(255, 255, 255))
    img2 = create_dummy_image_bytes(color=(200, 150, 100))

    files = [
        ("fir.png", img1),
        ("seizure.png", img2),
    ]

    with get_db_session() as session:
        batch_res = batch_pipeline.process_batch(
            files=files,
            case_id="CASE-TEST-BATCH",
            batch_title="Test Batch",
            session=session,
            run_dual_validation=False,
            auto_escalate=False,
        )

        assert batch_res.batch_id is not None
        assert batch_res.total_documents == 2
        assert batch_res.successful_count == 2
        assert batch_res.failed_count == 0

        # Check cross document intelligence
        intel = batch_res.cross_document_intelligence
        assert intel["total_documents"] == 2
        assert len(intel["reconciled_entities"]) >= 1

        ramesh = next((e for e in intel["reconciled_entities"] if "Ramesh" in e["canonical_name"]), None)
        assert ramesh is not None
        assert ramesh["document_count"] == 2
