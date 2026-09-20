"""End-to-end pipeline test with mock/real VLM."""

import io
from unittest.mock import MagicMock
import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from clarity.db.models import Base
from clarity.pipeline.runner import DocumentExtractionPipeline
from clarity.storage.local import LocalStorageBackend
from clarity.vlm.client import VLMClient
from clarity.vlm.parser import AmountItem, DateItem, IdentifierItem, PartyItem, StructuredExtraction


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_clarity.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()


def test_pipeline_e2e_with_mock_vlm(tmp_path, test_db):
    # 1. Setup mock VLM
    mock_vlm = MagicMock(spec=VLMClient)
    mock_vlm.classify_document.return_value = {
        "document_type": "invoice",
        "confidence": 0.96,
        "model_used": "qwen3-vl:8b",
    }

    mock_extraction = StructuredExtraction(
        document_type="invoice",
        parties=[PartyItem(name="Global Tech Logistics", role="vendor", confidence=0.98)],
        dates=[DateItem(label="Invoice Date", value="2026-06-15", confidence=0.95)],
        amounts=[
            AmountItem(label="Line Item 1", value=400.0, currency="USD", confidence=0.95),
            AmountItem(label="Line Item 2", value=600.0, currency="USD", confidence=0.95),
            AmountItem(label="Total Amount", value=1000.0, currency="USD", confidence=0.99),
        ],
        identifiers=[IdentifierItem(type="Invoice Number", value="INV-88992", confidence=0.97)],
        raw_text="Invoice #INV-88992 Global Tech Logistics Total: $1000.00",
        notes_on_legibility="Legible scan",
        overall_confidence=0.96,
    )

    mock_vlm.extract_structured.return_value = (
        mock_extraction,
        {
            "model_used": "qwen3-vl:8b",
            "prompt_version": "2026.09.v1",
            "parsed": mock_extraction.model_dump(),
        },
    )

    # 2. Setup storage
    storage = LocalStorageBackend(base_dir=tmp_path / "storage")

    # 3. Create test document
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    test_image_bytes = buf.getvalue()

    # 4. Run pipeline
    pipeline = DocumentExtractionPipeline(vlm_client=mock_vlm, storage=storage)
    result = pipeline.process_file(
        file_path_or_bytes=test_image_bytes,
        filename="test_invoice.png",
        session=test_db,
        actor_id="test_agent",
        run_dual_validation=False,
    )

    # 5. Assertions
    assert result.document_id is not None
    assert result.doc_type == "invoice"
    assert result.overall_confidence == 0.96
    assert result.validation_report.is_valid is True
    assert len(result.validation_report.flags) == 0

    # Verify audit trail contains all lifecycle events
    actions = [a["action"] for a in result.audit_trail]
    assert "ingestion" in actions
    assert "preprocessing" in actions
    assert "classification" in actions
    assert "validation_performed" in actions
    assert "extraction_completed" in actions

    # Verify storage contains files
    assert storage.exists(result.storage_path)
    assert storage.exists(result.preprocessed_storage_path)
