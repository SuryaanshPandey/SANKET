"""End-to-end evidence-grade document extraction pipeline orchestrator."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from sqlalchemy.orm import Session

from clarity.config import settings
from clarity.db.crud import (
    create_document,
    create_extraction_record,
    get_document_by_hash,
    get_document_by_id,
    log_audit_event,
    update_document_classification,
    update_document_preprocessing,
)
from clarity.db.models import Document, Extraction
from clarity.preprocessing.pipeline import run_preprocessing_pipeline
from clarity.storage import compute_sha256, get_hashed_storage_path, get_storage
from clarity.validation.rules import ValidationReport, evaluate_extraction_quality
from clarity.validation.rule_synthesizer import synthesize_rule_fields_and_entities
from clarity.vlm.client import VLMClient
from clarity.vlm.parser import flatten_extracted_fields


@dataclass
class PipelineResult:
    document_id: str
    original_filename: str
    file_hash_sha256: str
    storage_path: str
    preprocessed_storage_path: str
    doc_type: str
    overall_confidence: float
    extracted_data: Dict[str, Any]
    field_items: List[Dict[str, Any]]
    validation_report: ValidationReport
    is_escalated: bool
    audit_trail: List[Dict[str, Any]]


class DocumentExtractionPipeline:
    """Orchestrator for processing single documents with complete chain-of-custody."""

    def __init__(
        self,
        vlm_client: Optional[VLMClient] = None,
        storage=None,
    ):
        self.vlm_client = vlm_client or VLMClient()
        self.storage = storage or get_storage()

    def process_file(
        self,
        file_path_or_bytes: Union[str, Path, bytes],
        filename: Optional[str] = None,
        session: Optional[Session] = None,
        case_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        actor_id: str = "investigator",
        run_dual_validation: bool = False,
        auto_escalate: bool = False,
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> PipelineResult:
        """Execute the full 6-stage evidence extraction pipeline for a single document."""
        # 1. Read untouched raw bytes
        if isinstance(file_path_or_bytes, (str, Path)):
            path = Path(file_path_or_bytes)
            if not path.exists():
                raise FileNotFoundError(f"Input file not found: {path}")
            raw_bytes = path.read_bytes()
            original_filename = filename or path.name
        else:
            raw_bytes = file_path_or_bytes
            original_filename = filename or "uploaded_document.bin"

        # Determine extension
        ext = Path(original_filename).suffix or ".bin"

        # -------------------------------------------------------------
        # STAGE 1: Ingestion & Hashing
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("ingestion", "Reading bytes and computing SHA-256 provenance.")
        file_hash = compute_sha256(raw_bytes)
        raw_storage_key = get_hashed_storage_path(file_hash, prefix="raw", extension=ext)

        # Store pristine original in content-addressable storage
        self.storage.put_bytes(raw_storage_key, raw_bytes)

        # DB operations
        if session is None:
            from clarity.db.session import get_db_session

            with get_db_session() as auto_session:
                return self._execute_pipeline(
                    raw_bytes=raw_bytes,
                    file_hash=file_hash,
                    original_filename=original_filename,
                    raw_storage_key=raw_storage_key,
                    session=auto_session,
                    case_id=case_id,
                    batch_id=batch_id,
                    actor_id=actor_id,
                    run_dual_validation=run_dual_validation,
                    auto_escalate=auto_escalate,
                    progress_callback=progress_callback,
                )
        else:
            return self._execute_pipeline(
                raw_bytes=raw_bytes,
                file_hash=file_hash,
                original_filename=original_filename,
                raw_storage_key=raw_storage_key,
                session=session,
                case_id=case_id,
                batch_id=batch_id,
                actor_id=actor_id,
                run_dual_validation=run_dual_validation,
                auto_escalate=auto_escalate,
                progress_callback=progress_callback,
            )

    def _execute_pipeline(
        self,
        raw_bytes: bytes,
        file_hash: str,
        original_filename: str,
        raw_storage_key: str,
        session: Session,
        case_id: Optional[str],
        batch_id: Optional[str],
        actor_id: str,
        run_dual_validation: bool,
        auto_escalate: bool,
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> PipelineResult:
        # Check if already ingested (prevent duplicate mutation, keep chain of custody)
        existing_doc = get_document_by_hash(session, file_hash)
        if existing_doc:
            doc = existing_doc
            if batch_id:
                doc.batch_id = batch_id
            if case_id:
                doc.case_id = case_id
            log_audit_event(
                session=session,
                document_id=doc.id,
                action="reprocess_requested",
                actor_id=actor_id,
                detail={"message": "Document with identical hash reprocessed", "batch_id": batch_id},
            )
        else:
            doc = create_document(
                session=session,
                original_filename=original_filename,
                file_hash_sha256=file_hash,
                storage_path=raw_storage_key,
                ingested_by=actor_id,
                case_id=case_id,
                batch_id=batch_id,
            )

        # -------------------------------------------------------------
        # STAGE 2: Preprocessing
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("preprocessing", "Applying image orientation, contrast enhancement, and deskewing.")
        prep_result = run_preprocessing_pipeline(raw_bytes)
        prep_storage_key = get_hashed_storage_path(file_hash, prefix="preprocessed", extension="png")
        self.storage.put_bytes(prep_storage_key, prep_result.preprocessed_bytes, content_type="image/png")

        doc = update_document_preprocessing(
            session=session,
            document_id=doc.id,
            preprocessed_storage_path=prep_storage_key,
            metrics=prep_result.metrics,
            actor_id=actor_id,
        )

        # -------------------------------------------------------------
        # STAGE 3: Document Classification
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("classification", "Identifying the document type before structured extraction.")
        classification = self.vlm_client.classify_document(prep_result.preprocessed_bytes)
        doc_type = classification.get("document_type", "other")

        # Local benchmark/sample files carry reliable type cues in their names.
        # Use filename inference only when the VLM cannot classify the image.
        if doc_type == "other" or float(classification.get("confidence", 0.0)) < 0.60:
            filename_type = VLMClient.infer_document_type_from_filename(original_filename)
            if filename_type != "other":
                doc_type = filename_type

        doc = update_document_classification(
            session=session,
            document_id=doc.id,
            doc_type=doc_type,
            actor_id=actor_id,
            model_used=classification.get("model_used"),
        )

        # -------------------------------------------------------------
        # STAGE 4: Structured Extraction (Primary Run, Temp=0)
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("extraction", "Running multimodal VLM extraction. This step can take time; progress remains factual.")
        primary_structured, primary_meta = self.vlm_client.extract_structured(
            image_bytes=prep_result.preprocessed_bytes,
            temperature=0.0,
            document_type=doc_type,
        )

        if primary_meta.get("transport_failed"):
            log_audit_event(
                session=session,
                document_id=doc.id,
                action="vlm_transport_failure",
                actor_id=actor_id,
                detail={
                    "model_used": primary_meta.get("model_used"),
                    "transport": primary_meta.get("transport"),
                    "primary_error": primary_meta.get("primary_error"),
                    "retry_error": primary_meta.get("retry_error"),
                },
            )

        # -------------------------------------------------------------
        # STAGE 5: Validation Layer & Quality Gates
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("validation", "Evaluating extraction quality and deterministic evidence rules.")
        secondary_structured = None
        if run_dual_validation:
            try:
                secondary_structured, _ = self.vlm_client.extract_structured(
                    image_bytes=prep_result.preprocessed_bytes,
                    temperature=settings.dual_run_temperature,
                    document_type=doc_type,
                )
            except Exception as e:
                # If secondary run fails, we still proceed with primary
                pass

        val_report = evaluate_extraction_quality(
            primary_extraction=primary_structured,
            doc_type=doc_type,
            secondary_extraction=secondary_structured,
            max_flags=settings.max_flagged_fields_before_escalation,
            confidence_threshold=settings.confidence_threshold,
            tolerance=settings.arithmetic_tolerance,
        )

        # Log validation check
        log_audit_event(
            session=session,
            document_id=doc.id,
            action="validation_performed",
            actor_id=actor_id,
            detail={
                "is_valid": val_report.is_valid,
                "flag_count": len(val_report.flags),
                "needs_escalation": val_report.needs_escalation,
                "escalation_reason": val_report.escalation_reason,
            },
        )

        # -------------------------------------------------------------
        # Escalation Run (if triggered and enabled)
        # -------------------------------------------------------------
        is_escalated = False
        final_structured = primary_structured
        final_meta = primary_meta

        if auto_escalate and val_report.needs_escalation:
            log_audit_event(
                session=session,
                document_id=doc.id,
                action="escalation_triggered",
                actor_id=actor_id,
                detail={"reason": val_report.escalation_reason, "target_model": settings.vlm_thinking_model},
            )
            try:
                esc_structured, esc_meta = self.vlm_client.extract_structured(
                    image_bytes=prep_result.preprocessed_bytes,
                    model=settings.vlm_thinking_model,
                    temperature=0.0,
                    document_type=doc_type,
                )
                is_heuristic = "heuristic" in (esc_structured.notes_on_legibility or "").lower()
                primary_entity_count = len(primary_structured.parties) + len(primary_structured.identifiers)
                esc_entity_count = len(esc_structured.parties) + len(esc_structured.identifiers)
                
                # Only accept escalated result if it cleanly parsed structured entities without falling back to heuristic recovery
                if not is_heuristic and esc_entity_count >= primary_entity_count:
                    final_structured = esc_structured
                    final_meta = esc_meta
                    is_escalated = True
                else:
                    log_audit_event(
                        session=session,
                        document_id=doc.id,
                        action="escalation_retained_primary",
                        actor_id=actor_id,
                        detail={"message": "Escalated model did not produce superior structured schema; primary output retained."},
                    )
            except Exception as esc_err:
                # If thinking model not loaded or error, keep primary with flags
                log_audit_event(
                    session=session,
                    document_id=doc.id,
                    action="escalation_failed",
                    actor_id=actor_id,
                    detail={"error": str(esc_err)},
                )

        # Transform to granular items
        flat_fields = flatten_extracted_fields(final_structured)

        # Synthesize domain-rule-derived fields & statutory entities
        rule_fields, new_entities = synthesize_rule_fields_and_entities(
            doc_type=doc_type,
            extraction=final_structured,
            val_report=val_report,
        )
        flat_fields.extend(rule_fields)
        if new_entities:
            final_structured.parties.extend(new_entities)

        if rule_fields:
            log_audit_event(
                session=session,
                document_id=doc.id,
                action="rule_synthesis",
                actor_id=actor_id,
                detail={
                    "rule_field_count": len(rule_fields),
                    "new_entities_count": len(new_entities),
                    "fields_synthesized": [f["field_name"] for f in rule_fields],
                },
            )

        if progress_callback:
            progress_callback("persisting", "Saving structured evidence, provenance, and validation results.")

        # Persist extraction record
        extraction = create_extraction_record(
            session=session,
            document_id=doc.id,
            model_used=final_meta["model_used"],
            prompt_version=final_meta["prompt_version"],
            raw_output=final_meta["parsed"],
            extracted_fields_json=final_structured.model_dump(),
            overall_confidence=final_structured.overall_confidence,
            validation_flags=val_report.flags,
            is_escalated=is_escalated,
            field_items=flat_fields,
            actor_id=actor_id,
        )

        session.commit()

        # Build complete audit trail
        reloaded = get_document_by_id(session, doc.id)
        audit_trail = [
            {
                "id": entry.id,
                "action": entry.action,
                "actor_id": entry.actor_id,
                "timestamp": entry.timestamp.isoformat(),
                "detail": entry.detail,
            }
            for entry in reloaded.audit_logs
        ]

        return PipelineResult(
            document_id=doc.id,
            original_filename=doc.original_filename,
            file_hash_sha256=doc.file_hash_sha256,
            storage_path=doc.storage_path,
            preprocessed_storage_path=doc.preprocessed_storage_path or "",
            doc_type=doc.doc_type or "other",
            overall_confidence=final_structured.overall_confidence,
            extracted_data=final_structured.model_dump(),
            field_items=flat_fields,
            validation_report=val_report,
            is_escalated=is_escalated,
            audit_trail=audit_trail,
        )
