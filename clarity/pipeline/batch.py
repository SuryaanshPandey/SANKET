"""Multi-Document Batch Processing Pipeline with Cross-Document Synthesis."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session

from clarity.db.crud import (
    create_batch,
    get_batch_by_id,
    save_batch_analysis,
    update_batch_progress,
)
from clarity.pipeline.cross_document import CrossDocumentAggregator, CrossDocumentAnalysisResult
from clarity.pipeline.runner import DocumentExtractionPipeline, PipelineResult
from clarity.storage import get_storage
from clarity.vlm.client import VLMClient
import time


_STAGE_WEIGHTS = {
    "queued": 0.0,
    "ingestion": 0.10,
    "preprocessing": 0.20,
    "classification": 0.32,
    "extraction": 0.68,
    "validation": 0.84,
    "persisting": 0.96,
    "completed": 1.0,
}


def _build_progress_state(
    *,
    total_documents: int,
    processed_documents: int,
    current_index: int,
    current_filename: str,
    stage: str,
    detail: str,
    started_at: float,
    status: str = "processing",
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    total = max(1, total_documents)
    doc_fraction = min(1.0, max(0.0, processed_documents / total))
    current_share = 1.0 / total
    stage_fraction = _STAGE_WEIGHTS.get(stage, 0.0)
    if stage == "completed" or status == "completed":
        percentage = 100
    elif stage == "reconciliation" and processed_documents >= total_documents:
        # All documents are done, but the batch is not complete until reconciliation finishes.
        percentage = 99
    else:
        percentage = int(round((doc_fraction + current_share * stage_fraction) * 100))
        percentage = max(1 if status == "processing" else 0, min(98, percentage))
    return {
        "progress_percentage": percentage,
        "current_document_index": current_index if current_filename else None,
        "current_document_filename": current_filename or None,
        "current_stage": stage,
        "stage_detail": detail,
        "elapsed_seconds": max(0, int(time.time() - started_at)),
        "started_at_epoch": started_at,
        "status": status,
        "completed": status == "completed",
        "error_message": error_message,
        "total_documents": total_documents,
        "processed_documents": processed_documents,
    }



@dataclass
class BatchPipelineResult:
    batch_id: str
    case_id: Optional[str]
    title: Optional[str]
    total_documents: int
    successful_count: int
    failed_count: int
    documents: List[Dict[str, Any]]
    failed_documents: List[Dict[str, Any]]
    cross_document_intelligence: Dict[str, Any]


class BatchExtractionPipeline:
    """Orchestrates multi-document ingestion, parallel/sequential extraction, and cross-doc synthesis."""

    def __init__(
        self,
        vlm_client: Optional[VLMClient] = None,
        doc_pipeline: Optional[DocumentExtractionPipeline] = None,
        aggregator: Optional[CrossDocumentAggregator] = None,
    ):
        self.vlm_client = vlm_client or VLMClient()
        self.doc_pipeline = doc_pipeline or DocumentExtractionPipeline(vlm_client=self.vlm_client)
        self.aggregator = aggregator or CrossDocumentAggregator()

    def process_batch(
        self,
        files: List[Tuple[str, Union[str, Path, bytes]]],  # (filename, path_or_bytes)
        case_id: Optional[str] = None,
        batch_title: Optional[str] = None,
        actor_id: str = "investigator",
        run_dual_validation: bool = True,
        auto_escalate: bool = True,
        session: Optional[Session] = None,
        existing_batch_id: Optional[str] = None,
    ) -> BatchPipelineResult:
        """Process a collection of documents together as an evidentiary case batch."""
        if not files:
            raise ValueError("No files provided for batch processing")

        # Database session scope
        if session is None:
            from clarity.db.session import get_db_session

            with get_db_session() as auto_session:
                return self._execute_batch(
                    files=files,
                    case_id=case_id,
                    batch_title=batch_title,
                    actor_id=actor_id,
                    run_dual_validation=run_dual_validation,
                    auto_escalate=auto_escalate,
                    session=auto_session,
                    existing_batch_id=existing_batch_id,
                )
        else:
            return self._execute_batch(
                files=files,
                case_id=case_id,
                batch_title=batch_title,
                actor_id=actor_id,
                run_dual_validation=run_dual_validation,
                auto_escalate=auto_escalate,
                session=session,
                existing_batch_id=existing_batch_id,
            )

    def _execute_batch(
        self,
        files: List[Tuple[str, Union[str, Path, bytes]]],
        case_id: Optional[str],
        batch_title: Optional[str],
        actor_id: str,
        run_dual_validation: bool,
        auto_escalate: bool,
        session: Session,
        existing_batch_id: Optional[str] = None,
    ) -> BatchPipelineResult:
        # 1. Initialize Batch record
        total = len(files)
        title = batch_title or (f"Case Batch: {case_id}" if case_id else f"Evidence Batch ({total} docs)")
        if existing_batch_id:
            batch = get_batch_by_id(session, existing_batch_id)
            if not batch:
                raise ValueError(f"Batch {existing_batch_id} not found")
            batch_id = batch.id
        else:
            batch = create_batch(
                session=session,
                case_id=case_id,
                title=title,
                created_by=actor_id,
                total_documents=total,
            )
            batch_id = batch.id
        session.commit()

        started_at = time.time()
        def report(stage: str, detail: str, current_index: int, current_filename: str, processed_count: int) -> None:
            state = _build_progress_state(
                total_documents=total,
                processed_documents=processed_count,
                current_index=current_index,
                current_filename=current_filename,
                stage=stage,
                detail=detail,
                started_at=started_at,
            )
            update_batch_progress(session=session, batch_id=batch_id, progress_state=state)
            session.commit()

        update_batch_progress(
            session=session,
            batch_id=batch_id,
            progress_state=_build_progress_state(
                total_documents=total, processed_documents=0, current_index=1, current_filename=files[0][0] if files else "",
                stage="queued", detail="Batch accepted. Waiting for the first document to begin.", started_at=started_at
            ),
        )
        session.commit()

        successful_docs: List[Dict[str, Any]] = []
        failed_docs: List[Dict[str, Any]] = []

        # 2. Process each document sequentially with fault isolation
        for idx, (filename, file_input) in enumerate(files):
            report("ingestion", f"Preparing document {idx + 1} of {total}.", idx + 1, filename, idx)
            try:
                doc_res = self.doc_pipeline.process_file(
                    file_path_or_bytes=file_input,
                    filename=filename,
                    session=session,
                    case_id=case_id,
                    batch_id=batch_id,
                    actor_id=actor_id,
                    run_dual_validation=run_dual_validation,
                    auto_escalate=auto_escalate,
                    progress_callback=lambda stage, detail, i=idx + 1, fn=filename, processed=idx: report(stage, detail, i, fn, processed),
                )
                doc_dict = {
                    "document_id": doc_res.document_id,
                    "original_filename": doc_res.original_filename,
                    "file_hash_sha256": doc_res.file_hash_sha256,
                    "storage_path": doc_res.storage_path,
                    "preprocessed_storage_path": doc_res.preprocessed_storage_path,
                    "doc_type": doc_res.doc_type,
                    "overall_confidence": doc_res.overall_confidence,
                    "is_escalated": doc_res.is_escalated,
                    "extracted_data": doc_res.extracted_data,
                    "field_items": doc_res.field_items,
                    "validation_flags": doc_res.validation_report.flags,
                    "audit_trail": doc_res.audit_trail,
                }
                successful_docs.append(doc_dict)
            except Exception as e:
                failed_docs.append({
                    "filename": filename,
                    "error": str(e),
                })

            # Document is fully ingested; only now advance processed_count.
            update_batch_progress(
                session=session,
                batch_id=batch_id,
                processed_count=idx + 1,
                progress_state=_build_progress_state(
                    total_documents=total, processed_documents=idx + 1, current_index=idx + 1, current_filename=filename,
                    stage="persisting", detail=f"Document {idx + 1} of {total} is stored and committed.", started_at=started_at
                ),
            )
            session.commit()

        # 3. Cross-Document Synthesis & Intelligence
        update_batch_progress(
            session=session, batch_id=batch_id,
            progress_state=_build_progress_state(
                total_documents=total, processed_documents=total, current_index=total, current_filename=files[-1][0] if files else "",
                stage="reconciliation", detail="All documents are ingested. Synthesizing cross-document intelligence.", started_at=started_at
            )
        )
        session.commit()
        cross_doc_analysis: CrossDocumentAnalysisResult = self.aggregator.analyze(successful_docs)
        analysis_dict = cross_doc_analysis.to_dict()

        # 4. Save analysis to batch
        save_batch_analysis(
            session=session,
            batch_id=batch_id,
            analysis=analysis_dict,
        )
        final_state = _build_progress_state(
            total_documents=total,
            processed_documents=total,
            current_index=total,
            current_filename=files[-1][0] if files else "",
            stage="completed",
            detail="Ingestion and cross-document reconciliation completed successfully.",
            started_at=started_at,
            status="completed",
        )
        update_batch_progress(
            session=session,
            batch_id=batch_id,
            processed_count=total,
            status="completed",
            progress_state=final_state,
        )
        # Preserve the final analytical result while keeping progress metadata in a compact sidecar.
        batch_record = get_batch_by_id(session, batch_id)
        if batch_record:
            batch_record.cross_document_analysis = dict(analysis_dict)
            batch_record.cross_document_analysis["_progress"] = final_state
        session.commit()

        return BatchPipelineResult(
            batch_id=batch_id,
            case_id=case_id,
            title=title,
            total_documents=total,
            successful_count=len(successful_docs),
            failed_count=len(failed_docs),
            documents=successful_docs,
            failed_documents=failed_docs,
            cross_document_intelligence=analysis_dict,
        )
