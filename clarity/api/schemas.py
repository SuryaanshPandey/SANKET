"""Pydantic schemas for FastAPI API layer."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    file_hash_sha256: str
    storage_path: str
    preprocessed_storage_path: Optional[str] = None
    ingested_at: str
    ingested_by: str
    doc_type: Optional[str] = None
    page_count: int


class AuditEntryResponse(BaseModel):
    id: str
    action: str
    actor_id: str
    timestamp: str
    detail: Dict[str, Any]


class ExtractedFieldItemResponse(BaseModel):
    id: Optional[str] = None
    field_name: str
    field_value: str
    confidence: float
    bounding_box: Optional[Dict[str, Any]] = None
    human_verified: bool = False
    corrected_value: Optional[str] = None
    corrected_by: Optional[str] = None
    corrected_at: Optional[str] = None


class ExtractionProcessResponse(BaseModel):
    document_id: str
    original_filename: str
    file_hash_sha256: str
    storage_path: str
    preprocessed_storage_path: str
    doc_type: str
    overall_confidence: float
    is_escalated: bool
    extracted_data: Dict[str, Any]
    field_items: List[ExtractedFieldItemResponse]
    validation_flags: List[Dict[str, Any]]
    audit_trail: List[AuditEntryResponse]


# ============================================================================
# Multi-Document & Cross-Document Intelligence Schemas
# ============================================================================

class EntityOccurrenceSchema(BaseModel):
    document_id: str
    filename: str
    doc_type: str
    role: str
    confidence: float


class ReconciledEntitySchema(BaseModel):
    canonical_name: str
    roles: List[str]
    document_count: int
    documents: List[str]
    occurrences: List[EntityOccurrenceSchema] = Field(default_factory=list)


class TimelineEventSchema(BaseModel):
    raw_date: str
    normalized_date: Optional[str] = None
    document_id: str
    filename: str
    doc_type: str
    label: str
    detail: str


class CrossReferenceItemSchema(BaseModel):
    identifier_type: str
    value: str
    document_count: int
    documents: List[str]


class DiscrepancyFlagSchema(BaseModel):
    flag_type: str
    severity: str
    documents_involved: List[str]
    message: str


class FinancialLedgerItemSchema(BaseModel):
    label: str
    value: float
    currency: str
    source_doc: str
    doc_type: str


class FinancialLedgerSchema(BaseModel):
    total_amount: float
    currency: str
    item_count: int
    items: List[FinancialLedgerItemSchema] = Field(default_factory=list)


class CrossDocumentAnalysisSchema(BaseModel):
    total_documents: int
    doc_types: Dict[str, int]
    overall_case_confidence: float
    reconciled_entities: List[ReconciledEntitySchema]
    master_timeline: List[TimelineEventSchema]
    cross_references: List[CrossReferenceItemSchema]
    financial_ledger: FinancialLedgerSchema
    discrepancies: List[DiscrepancyFlagSchema]
    case_summary: str


class BatchProcessResponse(BaseModel):
    batch_id: str
    case_id: Optional[str] = None
    title: Optional[str] = None
    total_documents: int
    successful_count: int
    failed_count: int
    documents: List[ExtractionProcessResponse]
    failed_documents: List[Dict[str, Any]] = Field(default_factory=list)
    cross_document_intelligence: CrossDocumentAnalysisSchema




class BatchStartResponse(BaseModel):
    batch_id: str
    case_id: Optional[str] = None
    title: Optional[str] = None
    total_documents: int
    status: str


class BatchProgressResponse(BaseModel):
    batch_id: str
    case_id: Optional[str] = None
    title: Optional[str] = None
    total_documents: int
    processed_count: int
    status: str
    progress_percentage: int
    current_document_index: Optional[int] = None
    current_document_filename: Optional[str] = None
    current_stage: str
    stage_detail: str
    elapsed_seconds: int = 0
    completed: bool = False
    error_message: Optional[str] = None


class BatchSummaryResponse(BaseModel):
    batch_id: str
    case_id: Optional[str] = None
    title: Optional[str] = None
    created_at: str
    created_by: str
    total_documents: int
    processed_count: int
    status: str
    cross_document_analysis: Dict[str, Any] = Field(default_factory=dict)


class CaseSummaryItem(BaseModel):
    case_id: str
    document_count: int


class CaseDossierResponse(BaseModel):
    case_id: str
    document_count: int
    documents: List[ExtractionProcessResponse]
    cross_document_intelligence: CrossDocumentAnalysisSchema


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    vlm_model: str
    database: str
    storage: str


class VersionInfoResponse(BaseModel):
    version: str
    api_version: str
    contract_version: str
    status: str
    vlm_model: str


class InvestigationPlanRequestSchema(BaseModel):
    question: str = Field(min_length=5, max_length=2000)
    selected_entity_ids: List[str] = Field(default_factory=list, max_length=20)
    max_nodes: int = Field(default=8, ge=1, le=12)


class InvestigationPlanResponseSchema(BaseModel):
    question: str
    workflow: Dict[str, Any]
    explanation: str
    warnings: List[str] = Field(default_factory=list)
    planner_model: str
    planner_transport: str


class FieldReviewRequestSchema(BaseModel):
    human_verified: bool
    corrected_value: Optional[str] = Field(default=None, max_length=5000)


class FieldReviewResponseSchema(BaseModel):
    field_id: str
    document_id: str
    field_name: str
    original_value: str
    corrected_value: Optional[str] = None
    human_verified: bool
    corrected_by: Optional[str] = None
    corrected_at: Optional[str] = None


class WorkflowValidationResponse(BaseModel):
    valid: bool
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)


class InvestigationGraphSummaryResponse(BaseModel):
    case_id: Optional[str] = None
    contract_version: str
    total_documents: int
    node_count: int
    edge_count: int
    entity_count: int
    event_count: int
    resolution_cluster_count: int
    adapter_issue_count: int
    graph_issue_count: int


class WorkflowExecutionResponse(BaseModel):
    execution: Dict[str, Any]
    graph_summary: InvestigationGraphSummaryResponse
    resolution: Dict[str, Any] = Field(default_factory=dict)
    evidence_review: Dict[str, Any] = Field(default_factory=dict)
    report: Dict[str, Any] = Field(default_factory=dict)


class EvidenceReviewResponse(BaseModel):
    case_id: str
    graph_summary: Dict[str, Any] = Field(default_factory=dict)
    contradictions: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

