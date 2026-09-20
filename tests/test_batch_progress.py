import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from clarity.api.app import app
from clarity.db.crud import create_batch, update_batch_progress
from clarity.db.session import get_db_session, init_db

client = TestClient(app)


def _img_bytes():
    img = Image.new("RGB", (80, 60), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_batch_status_reports_persisted_real_progress():
    init_db()
    with get_db_session() as session:
        batch = create_batch(
            session=session,
            case_id="CASE-PROGRESS",
            title="Progress Test",
            created_by="test",
            total_documents=3,
        )
        session.commit()
        update_batch_progress(
            session=session,
            batch_id=batch.id,
            processed_count=1,
            progress_state={
                "progress_percentage": 41,
                "current_document_index": 2,
                "current_document_filename": "second.png",
                "current_stage": "extraction",
                "stage_detail": "Running multimodal VLM extraction.",
                "elapsed_seconds": 12,
                "status": "processing",
                "completed": False,
                "total_documents": 3,
                "processed_documents": 1,
            },
        )
        session.commit()
        batch_id = batch.id

    response = client.get(f"/api/v1/batches/{batch_id}/status")
    assert response.status_code == 200
    body = response.json()
    assert body["progress_percentage"] == 41
    assert body["processed_count"] == 1
    assert body["current_document_filename"] == "second.png"
    assert body["current_stage"] == "extraction"
    assert body["completed"] is False


def test_async_batch_start_returns_before_background_work(monkeypatch):
    init_db()
    with patch("clarity.api.routes._run_batch_background") as background:
        response = client.post(
            "/api/v1/documents/batch-process/start",
            files=[("files", ("sample.png", _img_bytes(), "image/png"))],
            data={"case_id": "CASE-ASYNC-START", "actor_id": "test", "run_dual_validation": "false", "auto_escalate": "false"},
        )
        assert response.status_code == 202
        body = response.json()
        assert body["batch_id"]
        assert body["status"] == "processing"
        background.assert_called_once()
