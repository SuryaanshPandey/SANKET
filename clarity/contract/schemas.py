"""Pydantic schemas for the Downstream Graph, Entity Resolution & Temporal Engine."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    PERSON = "PERSON"
    PHONE = "PHONE"
    ACCOUNT = "ACCOUNT"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    VEHICLE = "VEHICLE"
    WEAPON = "WEAPON"
    IDENTIFIER = "IDENTIFIER"
    OTHER = "OTHER"


class EventType(str, Enum):
    CALL = "CALL"
    TRANSACTION = "TRANSACTION"
    FINANCIAL_FRAUD = "FINANCIAL_FRAUD"
    FIR_REGISTRATION = "FIR_REGISTRATION"
    SEIZURE = "SEIZURE"
    ARREST = "ARREST"
    MEDICAL_EXAM = "MEDICAL_EXAM"
    FORENSIC_REPORT = "FORENSIC_REPORT"
    INCIDENT = "INCIDENT"


class BoundingBoxCoordinates(BaseModel):
    x: float = Field(..., description="Top-left X normalized 0-1000")
    y: float = Field(..., description="Top-left Y normalized 0-1000")
    w: float = Field(..., description="Width normalized 0-1000")
    h: float = Field(..., description="Height normalized 0-1000")


class SourceTraceability(BaseModel):
    document_id: str
    filename: str
    file_hash_sha256: str
    page: int = Field(default=1, description="1-indexed page number")
    bounding_box: Optional[BoundingBoxCoordinates] = None
    text_span: Optional[str] = Field(default=None, description="Exact textual evidence extracted")


class EntityContractItem(BaseModel):
    id: str = Field(..., description="Unique entity ID, e.g. ENT-001")
    type: EntityType = Field(..., description="Entity category: PERSON, PHONE, ACCOUNT, etc.")
    name: str = Field(..., description="Extracted entity mention")
    normalized_name: str = Field(..., description="Syntactically cleaned canonical name")
    role: Optional[str] = Field(default=None, description="Role within document: complainant, accused, etc.")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom domain attributes")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: SourceTraceability


class EventContractItem(BaseModel):
    id: str = Field(..., description="Unique event ID, e.g. EVT-001")
    type: EventType = Field(..., description="Event type: FIR_REGISTRATION, SEIZURE, etc.")
    title: str = Field(..., description="Short title of the event")
    source_entity: Optional[str] = Field(default=None, description="Entity initiating or originating the event")
    target_entity: Optional[str] = Field(default=None, description="Entity receiving or target of the event")
    timestamp: Optional[str] = Field(default=None, description="Normalized ISO date (YYYY-MM-DD) or timestamp")
    timestamp_start: Optional[str] = Field(default=None, description="Start date/time of incident interval")
    timestamp_end: Optional[str] = Field(default=None, description="End date/time of incident interval")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Event metadata: amounts, count, etc.")
    source: SourceTraceability


class RelationshipContractItem(BaseModel):
    id: str = Field(..., description="Unique relationship ID, e.g. REL-001")
    source_entity: str = Field(..., description="Source entity/event ID")
    target_entity: str = Field(..., description="Target entity/event ID")
    relationship_type: str = Field(..., description="Semantic edge type: ACCOUNT_HOLDER, COMPLAINANT_OF, etc.")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: Optional[str] = Field(default=None, description="Supporting textual or contextual basis")


class GraphContractResponse(BaseModel):
    contract_version: str = Field(default="1.0.0", description="Specification version of the graph contract")
    case_id: Optional[str] = Field(default=None, description="Investigation case identifier")
    batch_id: Optional[str] = Field(default=None, description="Batch ingestion run identifier")
    total_documents: int = Field(default=1, description="Number of corroborating documents")
    entities: List[EntityContractItem] = Field(default_factory=list)
    events: List[EventContractItem] = Field(default_factory=list)
    relationships: List[RelationshipContractItem] = Field(default_factory=list)
    audit_chain: Dict[str, Any] = Field(default_factory=dict, description="Cryptographic custody & quality gate metadata")
