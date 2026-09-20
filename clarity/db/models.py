"""SQLAlchemy models for evidence-grade document extraction.

Uses native PostgreSQL JSONB when running on PostgreSQL,
and standard JSON when running on SQLite for development and testing.
"""

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

# Cross-dialect JSONB on Postgres, JSON on SQLite
JSONType = JSON().with_variant(JSONB(), "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class DocumentBatch(Base):
    """Record of a multi-document ingestion batch and cross-document analysis."""

    __tablename__ = "document_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_by: Mapped[str] = mapped_column(String(128), default="system", nullable=False)
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    cross_document_analysis: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="batch", order_by="Document.ingested_at.asc()"
    )


class Document(Base):
    """Immutable record of an ingested document."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    batch_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("document_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    case_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    preprocessed_storage_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ingested_by: Mapped[str] = mapped_column(String(128), default="system", nullable=False)
    doc_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    page_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    batch: Mapped[Optional["DocumentBatch"]] = relationship("DocumentBatch", back_populates="documents")
    extractions: Mapped[List["Extraction"]] = relationship(
        "Extraction", back_populates="document", cascade="all, delete-orphan", order_by="Extraction.created_at.desc()"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="document", cascade="all, delete-orphan", order_by="AuditLog.timestamp.asc()"
    )

    # Indexes are declared directly on mapped_column (file_hash_sha256, case_id, doc_type, batch_id)


class Extraction(Base):
    """Immutable record of a model extraction run against a document."""

    __tablename__ = "extractions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_used: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_output: Mapped[Dict[str, Any]] = mapped_column(JSONType, nullable=False)
    extracted_fields_json: Mapped[Dict[str, Any]] = mapped_column(JSONType, nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    validation_flags: Mapped[List[Dict[str, Any]]] = mapped_column(JSONType, default=list, nullable=False)
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="extractions")
    field_items: Mapped[List["ExtractedField"]] = relationship(
        "ExtractedField", back_populates="extraction", cascade="all, delete-orphan"
    )


class ExtractedField(Base):
    """Granular field extracted with relative pixel bounding box and review status."""

    __tablename__ = "extracted_fields"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    extraction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    field_value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    # bounding_box: {"x": int/float, "y": int/float, "w": int/float, "h": int/float}
    bounding_box: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    human_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    corrected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    corrected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    extraction: Mapped["Extraction"] = relationship("Extraction", back_populates="field_items")


class AuditLog(Base):
    """Cryptographic chain-of-custody audit log for every action on a document."""

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(128), default="system", nullable=False)
    detail: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationship
    document: Mapped["Document"] = relationship("Document", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_doc_action", "document_id", "action"),
    )
