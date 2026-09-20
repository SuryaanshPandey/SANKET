"""Strictly audited and append-friendly CRUD operations for Clarity."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from clarity.db.models import AuditLog, Document, DocumentBatch, ExtractedField, Extraction


def log_audit_event(
    session: Session,
    document_id: str,
    action: str,
    actor_id: str = "system",
    detail: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Record an immutable cryptographic audit event."""
    log_entry = AuditLog(
        document_id=document_id,
        action=action,
        actor_id=actor_id,
        detail=detail or {},
        timestamp=datetime.now(timezone.utc),
    )
    session.add(log_entry)
    session.flush()
    return log_entry


def create_document(
    session: Session,
    original_filename: str,
    file_hash_sha256: str,
    storage_path: str,
    ingested_by: str = "system",
    case_id: Optional[str] = None,
    batch_id: Optional[str] = None,
    page_count: int = 1,
) -> Document:
    """Ingest a new document record. Never overwrites existing files."""
    doc = Document(
        original_filename=original_filename,
        file_hash_sha256=file_hash_sha256,
        storage_path=storage_path,
        ingested_by=ingested_by,
        case_id=case_id,
        batch_id=batch_id,
        page_count=page_count,
        ingested_at=datetime.now(timezone.utc),
    )
    session.add(doc)
    session.flush()

    log_audit_event(
        session=session,
        document_id=doc.id,
        action="ingestion",
        actor_id=ingested_by,
        detail={
            "original_filename": original_filename,
            "file_hash_sha256": file_hash_sha256,
            "storage_path": storage_path,
            "page_count": page_count,
            "batch_id": batch_id,
        },
    )
    return doc


def update_document_preprocessing(
    session: Session,
    document_id: str,
    preprocessed_storage_path: str,
    metrics: Dict[str, Any],
    actor_id: str = "system",
) -> Document:
    """Record preprocessed derivative without modifying original storage path."""
    doc = session.get(Document, document_id)
    if not doc:
        raise ValueError(f"Document {document_id} not found")

    doc.preprocessed_storage_path = preprocessed_storage_path
    session.flush()

    log_audit_event(
        session=session,
        document_id=doc.id,
        action="preprocessing",
        actor_id=actor_id,
        detail={
            "preprocessed_storage_path": preprocessed_storage_path,
            "metrics": metrics,
        },
    )
    return doc


def update_document_classification(
    session: Session,
    document_id: str,
    doc_type: str,
    actor_id: str = "system",
    model_used: Optional[str] = None,
) -> Document:
    """Record document classification."""
    doc = session.get(Document, document_id)
    if not doc:
        raise ValueError(f"Document {document_id} not found")

    doc.doc_type = doc_type
    session.flush()

    log_audit_event(
        session=session,
        document_id=doc.id,
        action="classification",
        actor_id=actor_id,
        detail={
            "doc_type": doc_type,
            "model_used": model_used,
        },
    )
    return doc


def create_extraction_record(
    session: Session,
    document_id: str,
    model_used: str,
    prompt_version: str,
    raw_output: Dict[str, Any],
    extracted_fields_json: Dict[str, Any],
    overall_confidence: float,
    validation_flags: List[Dict[str, Any]],
    is_escalated: bool = False,
    field_items: Optional[List[Dict[str, Any]]] = None,
    actor_id: str = "system",
) -> Extraction:
    """Store complete model extraction with granular extracted fields."""
    extraction = Extraction(
        document_id=document_id,
        model_used=model_used,
        prompt_version=prompt_version,
        raw_output=raw_output,
        extracted_fields_json=extracted_fields_json,
        overall_confidence=overall_confidence,
        validation_flags=validation_flags,
        is_escalated=is_escalated,
        created_at=datetime.now(timezone.utc),
    )
    session.add(extraction)
    session.flush()

    # Add granular field items if provided
    if field_items:
        for item in field_items:
            field = ExtractedField(
                extraction_id=extraction.id,
                field_name=item["field_name"],
                field_value=str(item["field_value"]),
                confidence=float(item.get("confidence", 1.0)),
                bounding_box=item.get("bounding_box"),
                human_verified=False,
            )
            session.add(field)
        session.flush()

    log_audit_event(
        session=session,
        document_id=document_id,
        action="extraction_completed" if not is_escalated else "escalation_extraction_completed",
        actor_id=actor_id,
        detail={
            "extraction_id": extraction.id,
            "model_used": model_used,
            "overall_confidence": overall_confidence,
            "validation_flag_count": len(validation_flags),
            "is_escalated": is_escalated,
        },
    )

    return extraction


def get_document_by_id(session: Session, document_id: str) -> Optional[Document]:
    """Retrieve document with all historical extractions and audit logs."""
    stmt = (
        select(Document)
        .options(
            joinedload(Document.extractions).joinedload(Extraction.field_items),
            joinedload(Document.audit_logs),
        )
        .where(Document.id == document_id)
    )
    return session.execute(stmt).unique().scalar_one_or_none()


def get_document_by_hash(session: Session, file_hash_sha256: str) -> Optional[Document]:
    """Check if file hash was already ingested."""
    stmt = select(Document).where(Document.file_hash_sha256 == file_hash_sha256)
    return session.execute(stmt).scalar_one_or_none()


def create_batch(
    session: Session,
    case_id: Optional[str] = None,
    title: Optional[str] = None,
    created_by: str = "system",
    total_documents: int = 0,
) -> DocumentBatch:
    """Initialize a multi-document ingestion batch."""
    batch = DocumentBatch(
        case_id=case_id,
        title=title,
        created_by=created_by,
        total_documents=total_documents,
        processed_count=0,
        status="processing" if total_documents > 0 else "pending",
        cross_document_analysis={},
        created_at=datetime.now(timezone.utc),
    )
    session.add(batch)
    session.flush()
    return batch


def update_batch_progress(
    session: Session,
    batch_id: str,
    processed_count: Optional[int] = None,
    status: Optional[str] = None,
    progress_state: Optional[Dict[str, Any]] = None,
) -> Optional[DocumentBatch]:
    """Update progress/completion status and an optional persisted progress payload."""
    batch = session.get(DocumentBatch, batch_id)
    if not batch:
        return None
    if processed_count is not None:
        batch.processed_count = processed_count
    if status is not None:
        batch.status = status
    if progress_state is not None:
        batch.cross_document_analysis = {"_progress": progress_state}
    session.flush()
    return batch


def save_batch_analysis(
    session: Session,
    batch_id: str,
    analysis: Dict[str, Any],
) -> Optional[DocumentBatch]:
    """Persist synthesized cross-document intelligence for a batch."""
    batch = session.get(DocumentBatch, batch_id)
    if not batch:
        return None
    batch.cross_document_analysis = analysis
    batch.status = "completed"
    session.flush()
    return batch


def get_batch_by_id(session: Session, batch_id: str) -> Optional[DocumentBatch]:
    """Retrieve batch with all its associated documents, extractions, and fields."""
    stmt = (
        select(DocumentBatch)
        .options(
            joinedload(DocumentBatch.documents)
            .joinedload(Document.extractions)
            .joinedload(Extraction.field_items),
            joinedload(DocumentBatch.documents).joinedload(Document.audit_logs),
        )
        .where(DocumentBatch.id == batch_id)
    )
    return session.execute(stmt).unique().scalar_one_or_none()


def list_batches(session: Session, limit: int = 20) -> List[DocumentBatch]:
    """List recent document batches."""
    stmt = (
        select(DocumentBatch)
        .options(joinedload(DocumentBatch.documents))
        .order_by(DocumentBatch.created_at.desc())
        .limit(limit)
    )
    return list(session.execute(stmt).unique().scalars().all())


def get_documents_by_case_id(session: Session, case_id: str) -> List[Document]:
    """Retrieve all documents ingested under a specific case ID."""
    stmt = (
        select(Document)
        .options(
            joinedload(Document.extractions).joinedload(Extraction.field_items),
            joinedload(Document.audit_logs),
        )
        .where(Document.case_id == case_id)
        .order_by(Document.ingested_at.asc())
    )
    return list(session.execute(stmt).unique().scalars().all())


def list_cases(session: Session) -> List[Dict[str, Any]]:
    """List distinct cases with their document counts."""
    from sqlalchemy import func
    stmt = (
        select(Document.case_id, func.count(Document.id).label("doc_count"))
        .where(Document.case_id.isnot(None))
        .group_by(Document.case_id)
        .order_by(Document.case_id.asc())
    )
    rows = session.execute(stmt).all()
    return [{"case_id": r[0], "document_count": r[1]} for r in rows]



def review_extracted_field(
    session: Session,
    field_id: str,
    *,
    human_verified: bool,
    corrected_value: Optional[str] = None,
    actor_id: str = "investigator",
) -> ExtractedField:
    """Record a human verification decision without changing the original extraction value."""
    field = session.get(ExtractedField, field_id)
    if not field:
        raise ValueError(f"Extracted field {field_id} not found")

    if corrected_value is not None:
        corrected_value = str(corrected_value)
    field.human_verified = bool(human_verified)
    field.corrected_value = corrected_value if human_verified else None
    field.corrected_by = actor_id if human_verified else None
    field.corrected_at = datetime.now(timezone.utc) if human_verified else None
    session.flush()

    log_audit_event(
        session=session,
        document_id=field.extraction.document_id,
        action="field_reviewed",
        actor_id=actor_id,
        detail={
            "field_id": field.id,
            "field_name": field.field_name,
            "human_verified": field.human_verified,
            "original_value": field.field_value,
            "corrected_value": field.corrected_value,
        },
    )
    return field
