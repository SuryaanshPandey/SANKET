"""API Route endpoints for document processing, multi-document batching, and cross-document auditing."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from clarity.api.schemas import (
    AuditEntryResponse,
    BatchProcessResponse,
    BatchProgressResponse,
    BatchStartResponse,
    BatchSummaryResponse,
    CaseDossierResponse,
    CaseSummaryItem,
    CrossDocumentAnalysisSchema,
    DocumentResponse,
    ExtractedFieldItemResponse,
    ExtractionProcessResponse,
    HealthResponse,
    VersionInfoResponse,
    WorkflowValidationResponse,
    WorkflowExecutionResponse,
    InvestigationGraphSummaryResponse,
    EvidenceReviewResponse,
    InvestigationPlanRequestSchema,
    InvestigationPlanResponseSchema,
    FieldReviewRequestSchema,
    FieldReviewResponseSchema,
)
from clarity import __version__
from clarity.config import settings
from clarity.db.crud import (
    create_batch,
    update_batch_progress,
    get_batch_by_id,
    get_document_by_id,
    get_documents_by_case_id,
    review_extracted_field,
    list_batches,
    list_cases,
)
from clarity.db.models import Document
from clarity.db.session import get_db
from clarity.pipeline.batch import BatchExtractionPipeline
from clarity.pipeline.cross_document import CrossDocumentAggregator
from clarity.pipeline.runner import DocumentExtractionPipeline
from clarity.contract.schemas import GraphContractResponse
from clarity.contract.transformer import build_graph_contract_for_case, build_graph_contract_for_document
from clarity.intelligence import (
    EntityResolver,
    EvidenceGraphBuilder,
    GraphBuildConfig,
    GraphContractAdapter,
    InvestigationWorkflow,
    InvestigationWorkflowEngine,
    ContradictionEngine,
    build_provenance_report,
    InvestigationPlanRequest,
    InvestigationPlanner,
    InvestigationPlannerError,
    build_investigation_report,
)

router = APIRouter(prefix="/api/v1")


def _read_upload_with_limit(upload: UploadFile) -> bytes:
    """Read one upload while enforcing the configured per-file size limit."""
    limit = max(1, int(settings.max_upload_size_mb)) * 1024 * 1024
    data = upload.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"File '{upload.filename or 'uploaded file'}' exceeds the {settings.max_upload_size_mb} MB per-file limit.",
        )
    return data


def _format_doc_dict_to_response(doc: Dict[str, Any]) -> ExtractionProcessResponse:
    return ExtractionProcessResponse(
        document_id=doc["document_id"],
        original_filename=doc["original_filename"],
        file_hash_sha256=doc["file_hash_sha256"],
        storage_path=doc["storage_path"],
        preprocessed_storage_path=doc.get("preprocessed_storage_path") or "",
        doc_type=doc.get("doc_type") or "other",
        overall_confidence=float(doc.get("overall_confidence", 0.9)),
        is_escalated=bool(doc.get("is_escalated", False)),
        extracted_data=doc.get("extracted_data") or {},
        field_items=[
            ExtractedFieldItemResponse(
                id=item.get("id"),
                field_name=item["field_name"],
                field_value=str(item["field_value"]),
                confidence=float(item.get("confidence", 1.0)),
                bounding_box=item.get("bounding_box"),
                human_verified=bool(item.get("human_verified", False)),
                corrected_value=item.get("corrected_value"),
                corrected_by=item.get("corrected_by"),
                corrected_at=item.get("corrected_at"),
            )
            for item in doc.get("field_items", [])
        ],
        validation_flags=doc.get("validation_flags") or [],
        audit_trail=[
            AuditEntryResponse(
                id=a["id"],
                action=a["action"],
                actor_id=a["actor_id"],
                timestamp=str(a["timestamp"]),
                detail=a.get("detail") or {},
            )
            for a in doc.get("audit_trail", [])
        ],
    )


def _format_orm_doc_to_dict(doc: Document) -> Dict[str, Any]:
    latest = doc.extractions[0] if doc.extractions else None
    return {
        "document_id": doc.id,
        "original_filename": doc.original_filename,
        "file_hash_sha256": doc.file_hash_sha256,
        "storage_path": doc.storage_path,
        "preprocessed_storage_path": doc.preprocessed_storage_path or "",
        "doc_type": doc.doc_type or "other",
        "overall_confidence": latest.overall_confidence if latest else 0.9,
        "is_escalated": latest.is_escalated if latest else False,
        "extracted_data": latest.extracted_fields_json if latest else {},
        "field_items": [
            {
                "id": f.id,
                "field_name": f.field_name,
                "field_value": f.field_value,
                "confidence": f.confidence,
                "bounding_box": f.bounding_box,
                "human_verified": f.human_verified,
                "corrected_value": f.corrected_value,
                "corrected_by": f.corrected_by,
                "corrected_at": f.corrected_at.isoformat() if f.corrected_at else None,
            }
            for f in (latest.field_items if latest else [])
        ],
        "validation_flags": latest.validation_flags if latest else [],
        "audit_trail": [
            {
                "id": a.id,
                "action": a.action,
                "actor_id": a.actor_id,
                "timestamp": a.timestamp.isoformat(),
                "detail": a.detail,
            }
            for a in doc.audit_logs
        ],
    }


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        version=__version__,
        vlm_model=settings.vlm_default_model,
        database=settings.database_url.split("://")[0],
        storage=settings.storage_backend,
    )


@router.get("/version", response_model=VersionInfoResponse)
def get_version_info():
    return VersionInfoResponse(
        version=__version__,
        api_version="v1",
        contract_version="1.0.0",
        status="stable",
        vlm_model=settings.vlm_default_model,
    )


# ============================================================================
# Single Document Endpoints
# ============================================================================

@router.post("/documents/process", response_model=ExtractionProcessResponse)
def process_document(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    actor_id: str = Form("investigator-api"),
    run_dual_validation: bool = Form(True),
    auto_escalate: bool = Form(True),
    db: Session = Depends(get_db),
):
    """Upload and process a single evidentiary document through the extraction pipeline."""
    contents = _read_upload_with_limit(file)
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    pipeline = DocumentExtractionPipeline()
    res = pipeline.process_file(
        file_path_or_bytes=contents,
        filename=file.filename or "uploaded_file.bin",
        session=db,
        case_id=case_id,
        actor_id=actor_id,
        run_dual_validation=run_dual_validation,
        auto_escalate=auto_escalate,
    )

    doc_dict = {
        "document_id": res.document_id,
        "original_filename": res.original_filename,
        "file_hash_sha256": res.file_hash_sha256,
        "storage_path": res.storage_path,
        "preprocessed_storage_path": res.preprocessed_storage_path,
        "doc_type": res.doc_type,
        "overall_confidence": res.overall_confidence,
        "is_escalated": res.is_escalated,
        "extracted_data": res.extracted_data,
        "field_items": res.field_items,
        "validation_flags": res.validation_report.flags,
        "audit_trail": res.audit_trail,
    }
    return _format_doc_dict_to_response(doc_dict)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(
        id=doc.id,
        original_filename=doc.original_filename,
        file_hash_sha256=doc.file_hash_sha256,
        storage_path=doc.storage_path,
        preprocessed_storage_path=doc.preprocessed_storage_path,
        ingested_at=doc.ingested_at.isoformat(),
        ingested_by=doc.ingested_by,
        doc_type=doc.doc_type,
        page_count=doc.page_count,
    )


@router.get("/documents/{document_id}/image")
def get_document_image(
    document_id: str,
    type: str = "preprocessed",
    db: Session = Depends(get_db),
):
    from clarity.storage import get_storage

    doc = get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_storage()
    path = doc.preprocessed_storage_path if (type == "preprocessed" and doc.preprocessed_storage_path) else doc.storage_path
    try:
        local_path = storage.get_local_path(path)
        media_type = "image/png" if path.endswith(".png") else "image/jpeg"
        return FileResponse(local_path, media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Image file not found: {e}")


@router.get("/documents/{document_id}/graph-contract", response_model=GraphContractResponse)
def get_document_graph_contract(document_id: str, db: Session = Depends(get_db)):
    """Export single document extractions formatted as a standardized Graph Contract for downstream intelligence."""
    doc = get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return build_graph_contract_for_document(doc)


# ============================================================================
# Multi-Document & Batch Processing Endpoints
# ============================================================================

def _progress_response(batch) -> BatchProgressResponse:
    progress = (batch.cross_document_analysis or {}).get("_progress", {})
    processed = int(batch.processed_count or 0)
    total = int(batch.total_documents or 0)
    status = batch.status or "processing"
    percentage = int(progress.get("progress_percentage", round((processed / total) * 100) if total else 0))
    started_at_epoch = progress.get("started_at_epoch")
    elapsed_seconds = int(progress.get("elapsed_seconds", 0))
    if status == "processing" and started_at_epoch:
        try:
            import time as _time
            elapsed_seconds = max(elapsed_seconds, int(_time.time() - float(started_at_epoch)))
        except (TypeError, ValueError):
            pass
    if status == "completed":
        percentage = 100
    return BatchProgressResponse(
        batch_id=batch.id,
        case_id=batch.case_id,
        title=batch.title,
        total_documents=total,
        processed_count=processed,
        status=status,
        progress_percentage=max(0, min(100, percentage)),
        current_document_index=progress.get("current_document_index"),
        current_document_filename=progress.get("current_document_filename"),
        current_stage=str(progress.get("current_stage", "processing")),
        stage_detail=str(progress.get("stage_detail", "Processing evidence.")),
        elapsed_seconds=elapsed_seconds,
        completed=bool(status == "completed"),
        error_message=progress.get("error_message"),
    )


def _run_batch_background(
    file_payloads: list[tuple[str, bytes]],
    *,
    batch_id: str,
    case_id: Optional[str],
    title: Optional[str],
    actor_id: str,
    run_dual_validation: bool,
    auto_escalate: bool,
) -> None:
    from clarity.db.session import get_db_session
    try:
        with get_db_session() as session:
            BatchExtractionPipeline().process_batch(
                files=file_payloads,
                case_id=case_id,
                batch_title=title,
                actor_id=actor_id,
                run_dual_validation=run_dual_validation,
                auto_escalate=auto_escalate,
                session=session,
                existing_batch_id=batch_id,
            )
    except Exception as exc:
        with get_db_session() as session:
            batch = get_batch_by_id(session, batch_id)
            if batch:
                progress = (batch.cross_document_analysis or {}).get("_progress", {})
                progress.update({
                    "status": "failed",
                    "completed": False,
                    "error_message": str(exc),
                    "stage_detail": "Batch processing stopped because the backend reported an error.",
                })
                update_batch_progress(session=session, batch_id=batch_id, status="failed", progress_state=progress)
                session.commit()


@router.get("/batches/{batch_id}/status", response_model=BatchProgressResponse)
def get_batch_status(batch_id: str, db: Session = Depends(get_db)):
    batch = get_batch_by_id(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _progress_response(batch)


@router.post("/documents/batch-process/start", response_model=BatchStartResponse, status_code=202)
def start_batch_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    case_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    actor_id: str = Form("investigator-api"),
    run_dual_validation: bool = Form(False),
    auto_escalate: bool = Form(False),
    db: Session = Depends(get_db),
):
    """Accept a batch immediately and process it in the background."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for batch processing")
    file_payloads = []
    for f in files:
        raw_bytes = f.file.read()
        if raw_bytes:
            file_payloads.append((f.filename or "uploaded_doc.bin", raw_bytes))
    if not file_payloads:
        raise HTTPException(status_code=400, detail="All uploaded files are empty")

    title_value = title or (f"Case Batch: {case_id}" if case_id else f"Evidence Batch ({len(file_payloads)} docs)")
    batch = create_batch(
        session=db, case_id=case_id, title=title_value, created_by=actor_id, total_documents=len(file_payloads)
    )
    db.commit()
    background_tasks.add_task(
        _run_batch_background, file_payloads, batch_id=batch.id, case_id=case_id, title=title_value,
        actor_id=actor_id, run_dual_validation=run_dual_validation, auto_escalate=auto_escalate
    )
    return BatchStartResponse(batch_id=batch.id, case_id=case_id, title=title_value, total_documents=len(file_payloads), status="processing")


@router.post("/documents/batch-process", response_model=BatchProcessResponse)
def process_batch_documents(
    files: List[UploadFile] = File(...),
    case_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    actor_id: str = Form("investigator-api"),
    run_dual_validation: bool = Form(False),
    auto_escalate: bool = Form(False),
    db: Session = Depends(get_db),
):
    """Upload and process multiple documents simultaneously, synthesizing cross-document intelligence."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for batch processing")

    file_payloads = []
    for f in files:
        raw_bytes = f.file.read()
        if raw_bytes:
            file_payloads.append((f.filename or "uploaded_doc.bin", raw_bytes))

    if not file_payloads:
        raise HTTPException(status_code=400, detail="All uploaded files are empty")

    pipeline = BatchExtractionPipeline()
    res = pipeline.process_batch(
        files=file_payloads,
        case_id=case_id,
        batch_title=title,
        actor_id=actor_id,
        run_dual_validation=run_dual_validation,
        auto_escalate=auto_escalate,
        session=db,
    )

    formatted_docs = [_format_doc_dict_to_response(d) for d in res.documents]

    return BatchProcessResponse(
        batch_id=res.batch_id,
        case_id=res.case_id,
        title=res.title,
        total_documents=res.total_documents,
        successful_count=res.successful_count,
        failed_count=res.failed_count,
        documents=formatted_docs,
        failed_documents=res.failed_documents,
        cross_document_intelligence=res.cross_document_intelligence,
    )


@router.get("/batches", response_model=List[BatchSummaryResponse])
def get_batches(limit: int = 20, db: Session = Depends(get_db)):
    """List recent document batches."""
    batches = list_batches(db, limit=limit)
    return [
        BatchSummaryResponse(
            batch_id=b.id,
            case_id=b.case_id,
            title=b.title,
            created_at=b.created_at.isoformat(),
            created_by=b.created_by,
            total_documents=b.total_documents,
            processed_count=b.processed_count,
            status=b.status,
            cross_document_analysis=b.cross_document_analysis or {},
        )
        for b in batches
    ]


@router.get("/batches/{batch_id}", response_model=BatchProcessResponse)
def get_batch(batch_id: str, db: Session = Depends(get_db)):
    """Retrieve full batch details, document extractions, and synthesized cross-document intelligence."""
    batch = get_batch_by_id(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    docs_dict = [_format_orm_doc_to_dict(doc) for doc in batch.documents]
    formatted_docs = [_format_doc_dict_to_response(d) for d in docs_dict]

    # Recompute analysis if not stored
    analysis = batch.cross_document_analysis
    if not analysis and docs_dict:
        analysis = CrossDocumentAggregator().analyze(docs_dict).to_dict()

    return BatchProcessResponse(
        batch_id=batch.id,
        case_id=batch.case_id,
        title=batch.title,
        total_documents=batch.total_documents,
        successful_count=len(batch.documents),
        failed_count=0,
        documents=formatted_docs,
        failed_documents=[],
        cross_document_intelligence=analysis or {},
    )


@router.get("/cases", response_model=List[CaseSummaryItem])
def get_cases(db: Session = Depends(get_db)):
    """List distinct investigation / audit cases with document counts."""
    cases = list_cases(db)
    return [CaseSummaryItem(case_id=c["case_id"], document_count=c["document_count"]) for c in cases]


@router.get("/cases/{case_id}/dossier", response_model=CaseDossierResponse)
def get_case_dossier(case_id: str, db: Session = Depends(get_db)):
    """Synthesize a complete cross-document case dossier for all documents under a case ID."""
    docs = get_documents_by_case_id(db, case_id)
    if not docs:
        raise HTTPException(status_code=404, detail=f"No documents found for case {case_id}")

    docs_dict = [_format_orm_doc_to_dict(doc) for doc in docs]
    formatted_docs = [_format_doc_dict_to_response(d) for d in docs_dict]

    # Run cross-document synthesis across the entire case
    aggregator = CrossDocumentAggregator()
    analysis = aggregator.analyze(docs_dict).to_dict()

    return CaseDossierResponse(
        case_id=case_id,
        document_count=len(docs),
        documents=formatted_docs,
        cross_document_intelligence=analysis,
    )


@router.get("/cases/{case_id}/graph-contract", response_model=GraphContractResponse)
def get_case_graph_contract(case_id: str, db: Session = Depends(get_db)):
    """Export unified multi-document case extractions as a standardized Graph Contract for downstream intelligence."""
    contract = build_graph_contract_for_case(db, case_id)
    if contract.total_documents == 0:
        raise HTTPException(status_code=404, detail=f"No documents found for case '{case_id}'")
    return contract


@router.post("/engine/extract", response_model=GraphContractResponse)
def engine_extract_files(
    files: List[UploadFile] = File(...),
    case_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    actor_id: str = Form("clarity-engine-api"),
    db: Session = Depends(get_db),
):
    """Headless microservice endpoint: upload one or more documents and directly receive the Graph Contract."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for extraction")

    file_payloads = []
    for f in files:
        raw = _read_upload_with_limit(f)
        if raw:
            file_payloads.append((f.filename or "uploaded_doc.bin", raw))

    if not file_payloads:
        raise HTTPException(status_code=400, detail="All uploaded files are empty")

    from clarity.engine import ClarityEngine

    engine = ClarityEngine(auto_init_db=False)
    return engine.extract_batch(file_payloads, case_id=case_id, title=title, actor_id=actor_id)


# ============================================================================
# Investigation Workflow Endpoints
# ============================================================================

def _build_case_evidence_graph(db: Session, case_id: str):
    contract = build_graph_contract_for_case(db, case_id)
    if contract.total_documents == 0:
        raise HTTPException(status_code=404, detail=f"No documents found for case '{case_id}'")

    adapted = GraphContractAdapter(strict=False).adapt(contract)
    resolution = EntityResolver().resolve(adapted.entities)
    evidence_graph = EvidenceGraphBuilder(
        GraphBuildConfig(
            merge_confirmed_entities=True,
            include_events=True,
            reject_dangling_relationships=False,
        )
    ).build(adapted, resolution)
    return contract, adapted, resolution, evidence_graph


def _case_documents_dict(db: Session, case_id: str) -> list[dict[str, Any]]:
    docs = get_documents_by_case_id(db, case_id)
    if not docs:
        raise HTTPException(status_code=404, detail=f"No documents found for case '{case_id}'")
    return [_format_orm_doc_to_dict(doc) for doc in docs]


@router.get("/cases/{case_id}/evidence-review", response_model=EvidenceReviewResponse)
def get_case_evidence_review(case_id: str, db: Session = Depends(get_db)):
    """Return deterministic provenance inventory and cross-document contradictions."""
    docs_dict = _case_documents_dict(db, case_id)
    _, adapted, resolution, graph = _build_case_evidence_graph(db, case_id)
    contradictions = ContradictionEngine().analyze(docs_dict, case_id=case_id)
    provenance = build_provenance_report(case_id=case_id, documents=docs_dict, graph=graph)
    return EvidenceReviewResponse(
        case_id=case_id,
        graph_summary={
            "contract_version": adapted.contract_version,
            "total_documents": adapted.total_documents,
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
            "entity_count": graph.entity_count,
            "event_count": graph.event_count,
            "resolution_cluster_count": resolution.cluster_count,
            "adapter_issue_count": len(adapted.issues),
            "graph_issue_count": len(graph.issues),
        },
        contradictions=contradictions.to_json_dict(),
        provenance=provenance.to_json_dict(),
    )


@router.get("/cases/{case_id}/investigation-graph")
def get_investigation_graph(case_id: str, db: Session = Depends(get_db)):
    """Build and return the canonical post-extraction evidence graph for a case."""
    _, adapted, resolution, graph = _build_case_evidence_graph(db, case_id)
    return {
        "case_id": case_id,
        "graph": graph.to_records(),
        "summary": {
            "contract_version": adapted.contract_version,
            "total_documents": adapted.total_documents,
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
            "entity_count": graph.entity_count,
            "event_count": graph.event_count,
            "resolution_cluster_count": resolution.cluster_count,
            "adapter_issue_count": len(adapted.issues),
            "graph_issue_count": len(graph.issues),
        },
        "resolution": resolution.model_dump(mode="json"),
    }


@router.post("/cases/{case_id}/investigate/plan", response_model=InvestigationPlanResponseSchema)
def plan_investigation(case_id: str, request: InvestigationPlanRequestSchema, db: Session = Depends(get_db)):
    """Translate an investigator question into a validated, non-executing workflow."""
    _, adapted, resolution, graph = _build_case_evidence_graph(db, case_id)
    entity_context = [
        {
            "id": node.id,
            "type": node.type,
            "label": node.label,
            "confidence": node.confidence,
        }
        for node in sorted(graph.nodes.values(), key=lambda item: item.id)
        if getattr(node.kind, "value", node.kind) == "ENTITY"
    ][:80]
    context = {
        "case_id": case_id,
        "graph_summary": {
            "documents": adapted.total_documents,
            "entities": graph.entity_count,
            "events": graph.event_count,
            "relationships": graph.edge_count,
            "resolution_clusters": resolution.cluster_count,
            "graph_issues": len(graph.issues),
        },
        "entities": entity_context,
        "investigator_selected_entity_ids": request.selected_entity_ids,
    }
    try:
        result = InvestigationPlanner().plan(
            InvestigationPlanRequest(
                question=request.question,
                selected_entity_ids=request.selected_entity_ids,
                max_nodes=request.max_nodes,
            ),
            case_context=context,
            allowed_entity_ids=set(request.selected_entity_ids),
            graph_node_ids=set(graph.nodes),
        )
    except InvestigationPlannerError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return InvestigationPlanResponseSchema(
        question=result.question,
        workflow=result.workflow.model_dump(mode="json"),
        explanation=result.explanation,
        warnings=result.warnings,
        planner_model=result.planner_model,
        planner_transport=result.planner_transport,
    )


@router.patch("/extracted-fields/{field_id}/review", response_model=FieldReviewResponseSchema)
def update_extracted_field_review(
    field_id: str,
    request: FieldReviewRequestSchema,
    actor_id: str = "investigator",
    db: Session = Depends(get_db),
):
    """Record human verification while preserving the original extraction value."""
    try:
        field = review_extracted_field(
            db,
            field_id,
            human_verified=request.human_verified,
            corrected_value=request.corrected_value,
            actor_id=actor_id,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FieldReviewResponseSchema(
        field_id=field.id,
        document_id=field.extraction.document_id,
        field_name=field.field_name,
        original_value=field.field_value,
        corrected_value=field.corrected_value,
        human_verified=field.human_verified,
        corrected_by=field.corrected_by,
        corrected_at=field.corrected_at.isoformat() if field.corrected_at else None,
    )


@router.post("/cases/{case_id}/workflows/validate", response_model=WorkflowValidationResponse)
def validate_investigation_workflow(case_id: str, workflow: InvestigationWorkflow, db: Session = Depends(get_db)):
    """Validate a workflow against the case-independent allow-listed execution model."""
    # Ensure the case exists before validating a workflow for it.
    _, _, _, _ = _build_case_evidence_graph(db, case_id)
    issues = InvestigationWorkflowEngine().validate(workflow)
    errors = [issue.model_dump(mode="json") for issue in issues if issue.severity == "error"]
    warnings = [issue.model_dump(mode="json") for issue in issues if issue.severity != "error"]
    return WorkflowValidationResponse(valid=not errors, errors=errors, warnings=warnings)


@router.post("/cases/{case_id}/workflows/execute", response_model=WorkflowExecutionResponse)
def execute_investigation_workflow(case_id: str, workflow: InvestigationWorkflow, db: Session = Depends(get_db)):
    """Execute a validated workflow against the case evidence graph."""
    _, adapted, resolution, graph = _build_case_evidence_graph(db, case_id)
    engine = InvestigationWorkflowEngine()
    result = engine.execute(graph, workflow)
    if result.status == "VALIDATION_FAILED":
        raise HTTPException(status_code=422, detail=result.to_json_dict())

    summary = InvestigationGraphSummaryResponse(
        case_id=case_id,
        contract_version=adapted.contract_version,
        total_documents=adapted.total_documents,
        node_count=graph.node_count,
        edge_count=graph.edge_count,
        entity_count=graph.entity_count,
        event_count=graph.event_count,
        resolution_cluster_count=resolution.cluster_count,
        adapter_issue_count=len(adapted.issues),
        graph_issue_count=len(graph.issues),
    )
    docs_dict = _case_documents_dict(db, case_id)
    findings: list[dict[str, Any]] = []
    for node_result in result.node_results:
        for key in ("bridge_candidates", "key_individuals", "findings"):
            values = node_result.output.get(key, [])
            if isinstance(values, list):
                findings.extend(item for item in values if isinstance(item, dict))
    contradictions = ContradictionEngine().analyze(docs_dict, case_id=case_id)
    provenance = build_provenance_report(
        case_id=case_id, documents=docs_dict, graph=graph, findings=findings
    )
    review_payload = {
        "contradictions": contradictions.to_json_dict(),
        "provenance": provenance.to_json_dict(),
    }
    report = build_investigation_report(
        case_id=case_id,
        workflow=workflow,
        execution=result,
        graph_summary=summary.model_dump(mode="json"),
        evidence_review=review_payload,
        question=str(workflow.metadata.get("investigation_question")) if workflow.metadata.get("investigation_question") else None,
    )
    report_payload = report.model_dump(mode="json")
    report_payload["markdown"] = report.to_markdown()
    return WorkflowExecutionResponse(
        execution=result.to_json_dict(),
        graph_summary=summary,
        resolution={
            "cluster_count": resolution.cluster_count,
            "candidate_count": len(resolution.candidates),
            "unresolved_entity_count": len(resolution.unresolved_entity_ids),
            "confirmed_clusters": [item.model_dump(mode="json") for item in resolution.confirmed_clusters],
        },
        evidence_review=review_payload,
        report=report_payload,
    )


# ============================================================================
# Dataset Catalog & Benchmark Endpoints
# ============================================================================

DATASET_METADATA = {
    "police_case": {
        "key": "police_case",
        "name": "Forensic Police Dossier",
        "category": "Forensic & Legal",
        "description": "5 connected case records: FIR, Seizure Memo, Arrest Memo, Injury Certificate, Ballistics Report",
        "case_id": "CASE-2026-DL-184",
        "title": "Vasant Vihar Police Investigation & Recovery Case",
        "dir": "police_case",
    },
    "receipts": {
        "key": "receipts",
        "name": "ICDAR SROIE Scanned Receipts",
        "category": "Kaggle / ICDAR Benchmark",
        "description": "Authentic scanned retail and supermarket receipts with OCR and field items",
        "case_id": "RECEIPTS-ICDAR-2019",
        "title": "ICDAR SROIE Benchmark Scanned Receipts",
        "dir": "receipts",
    },
    "invoices": {
        "key": "invoices",
        "name": "Commercial B2B Tax Invoices",
        "category": "Corporate & Finance",
        "description": "Itemized tax invoices with line items, HSN codes, and arithmetic reconciliation",
        "case_id": "INV-CORP-2026",
        "title": "Commercial Enterprise Invoices & Tax Audits",
        "dir": "invoices",
    },
    "financial": {
        "key": "financial",
        "name": "Bank Account & Payment Statements",
        "category": "Banking & Audits",
        "description": "Transaction ledgers, debit/credit entries, account balances, and IFSC records",
        "case_id": "FIN-BANK-2026",
        "title": "Financial Ledger & Wire Settlement Audit",
        "dir": "financial",
    },
    "contracts": {
        "key": "contracts",
        "name": "Legal Contracts & NDAs",
        "category": "Legal & Corporate",
        "description": "Non-Disclosure and Service Agreements with clauses, parties, and effective dates",
        "case_id": "LEGAL-AGR-2026",
        "title": "Corporate Contracts & Mutual NDAs",
        "dir": "contracts",
    },
    "degraded": {
        "key": "degraded",
        "name": "Scanner Degraded / Skewed Test",
        "category": "Stress Testing",
        "description": "Low-contrast, noisy, and rotated document scans testing the OpenCV preprocessing pipeline",
        "case_id": "STRESS-SCAN-2026",
        "title": "Scanner Degraded & Rotated Stress Test",
        "dir": "degraded",
    },
}


@router.get("/samples/catalog")
def get_sample_catalog():
    """Return catalog of available benchmark and domain datasets with live counts."""
    samples_dir = Path(__file__).resolve().parent.parent.parent / "samples"
    diverse_dir = samples_dir / "diverse"

    catalog = []
    for key, meta in DATASET_METADATA.items():
        folder = diverse_dir / meta["dir"]
        if folder.exists():
            count = len([f for f in folder.iterdir() if f.is_file() and not f.name.startswith(".")])
        else:
            count = 0
        catalog.append({
            "key": key,
            "name": meta["name"],
            "category": meta["category"],
            "description": meta["description"],
            "count": count,
        })
    return catalog


@router.post("/samples/load-dataset/{dataset_key}/start", response_model=BatchStartResponse, status_code=202)
def start_diverse_dataset(
    dataset_key: str,
    background_tasks: BackgroundTasks,
    actor_id: str = "lead_investigator",
    db: Session = Depends(get_db),
):
    """Accept a sample dataset for background ingestion and return its batch ID immediately."""
    if dataset_key not in DATASET_METADATA:
        raise HTTPException(status_code=404, detail=f"Unknown dataset '{dataset_key}'. Available: {list(DATASET_METADATA.keys())}")
    meta = DATASET_METADATA[dataset_key]
    samples_dir = Path(__file__).resolve().parent.parent.parent / "samples"
    folder = samples_dir / "diverse" / meta["dir"]
    file_payloads = []
    if folder.exists():
        for f in sorted([f for f in folder.iterdir() if f.is_file() and not f.name.startswith(".")]):
            file_payloads.append((f.name, f.read_bytes()))
    if not file_payloads and dataset_key == "police_case":
        sample_files = [
            ("01_fir_report.png", samples_dir / "sample_fir_report.png"),
            ("02_seizure_memo.png", samples_dir / "sample_seizure_memo.png"),
            ("03_arrest_memo.png", samples_dir / "sample_arrest_memo.png"),
            ("04_medico_legal.png", samples_dir / "sample_medical_legal.png"),
            ("05_forensic_report.png", samples_dir / "sample_forensic_report.png"),
        ]
        for fname, fpath in sample_files:
            if fpath.exists(): file_payloads.append((fname, fpath.read_bytes()))
    if not file_payloads:
        raise HTTPException(status_code=404, detail=f"No document files found for dataset '{dataset_key}'")
    batch = create_batch(
        session=db, case_id=meta["case_id"], title=meta["title"], created_by=actor_id, total_documents=len(file_payloads)
    )
    db.commit()
    background_tasks.add_task(
        _run_batch_background, file_payloads, batch_id=batch.id, case_id=meta["case_id"], title=meta["title"],
        actor_id=actor_id, run_dual_validation=False, auto_escalate=False
    )
    return BatchStartResponse(batch_id=batch.id, case_id=meta["case_id"], title=meta["title"], total_documents=len(file_payloads), status="processing")


@router.api_route("/samples/load-dataset/{dataset_key}", methods=["GET", "POST"], response_model=BatchProcessResponse)
def load_diverse_dataset(
    dataset_key: str,
    actor_id: str = "lead_investigator",
    db: Session = Depends(get_db),
):
    """Load and process an entire diverse dataset bundle as an evidentiary batch."""
    if dataset_key not in DATASET_METADATA:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown dataset '{dataset_key}'. Available: {list(DATASET_METADATA.keys())}",
        )

    meta = DATASET_METADATA[dataset_key]
    samples_dir = Path(__file__).resolve().parent.parent.parent / "samples"
    folder = samples_dir / "diverse" / meta["dir"]

    # Fallback to root samples directory for police case if diverse folder is empty
    file_payloads = []
    if folder.exists():
        files = sorted([f for f in folder.iterdir() if f.is_file() and not f.name.startswith(".")])
        for f in files:
            file_payloads.append((f.name, f.read_bytes()))

    if not file_payloads and dataset_key == "police_case":
        sample_files = [
            ("01_fir_report.png", samples_dir / "sample_fir_report.png"),
            ("02_seizure_memo.png", samples_dir / "sample_seizure_memo.png"),
            ("03_arrest_memo.png", samples_dir / "sample_arrest_memo.png"),
            ("04_medico_legal.png", samples_dir / "sample_medical_legal.png"),
            ("05_forensic_report.png", samples_dir / "sample_forensic_report.png"),
        ]
        for fname, fpath in sample_files:
            if fpath.exists():
                file_payloads.append((fname, fpath.read_bytes()))

    if not file_payloads:
        raise HTTPException(status_code=404, detail=f"No document files found for dataset '{dataset_key}'")

    pipeline = BatchExtractionPipeline()
    res = pipeline.process_batch(
        files=file_payloads,
        case_id=meta["case_id"],
        batch_title=meta["title"],
        actor_id=actor_id,
        run_dual_validation=False,
        auto_escalate=False,
        session=db,
    )

    formatted_docs = [_format_doc_dict_to_response(d) for d in res.documents]

    return BatchProcessResponse(
        batch_id=res.batch_id,
        case_id=res.case_id,
        title=res.title,
        total_documents=res.total_documents,
        successful_count=res.successful_count,
        failed_count=res.failed_count,
        documents=formatted_docs,
        failed_documents=res.failed_documents,
        cross_document_intelligence=res.cross_document_intelligence,
    )


@router.api_route("/samples/batch-case", methods=["GET", "POST"], response_model=BatchProcessResponse)
def process_sample_case_bundle(
    case_id: str = "CASE-2026-DL-184",
    actor_id: str = "lead_investigator",
    db: Session = Depends(get_db),
):
    """Backwards-compatible endpoint: processes the police case bundle."""
    return load_diverse_dataset(dataset_key="police_case", actor_id=actor_id, db=db)


# ============================================================================
# Static Sample File Endpoints
# ============================================================================

@router.get("/samples/invoice")
def get_sample_invoice():
    sample_path = Path(__file__).resolve().parent.parent.parent / "samples" / "test_invoice.jpg"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample invoice not found")
    return FileResponse(str(sample_path), media_type="image/jpeg", filename="test_invoice.jpg")


@router.get("/samples/fir")
def get_sample_fir():
    sample_path = Path(__file__).resolve().parent.parent.parent / "samples" / "sample_fir_report.png"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample FIR not found")
    return FileResponse(str(sample_path), media_type="image/png", filename="sample_fir_report.png")


@router.get("/samples/seizure_memo")
def get_sample_seizure_memo():
    sample_path = Path(__file__).resolve().parent.parent.parent / "samples" / "sample_seizure_memo.png"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample Seizure Memo not found")
    return FileResponse(str(sample_path), media_type="image/png", filename="sample_seizure_memo.png")


@router.get("/samples/arrest_memo")
def get_sample_arrest_memo():
    sample_path = Path(__file__).resolve().parent.parent.parent / "samples" / "sample_arrest_memo.png"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample Arrest Memo not found")
    return FileResponse(str(sample_path), media_type="image/png", filename="sample_arrest_memo.png")


@router.get("/samples/chargesheet")
def get_sample_chargesheet():
    sample_path = Path(__file__).resolve().parent.parent.parent / "samples" / "sample_chargesheet.png"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample Charge Sheet not found")
    return FileResponse(str(sample_path), media_type="image/png", filename="sample_chargesheet.png")


@router.get("/samples/medical_legal")
def get_sample_medical_legal():
    sample_path = Path(__file__).resolve().parent.parent.parent / "samples" / "sample_medical_legal.png"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample Medico-Legal Report not found")
    return FileResponse(str(sample_path), media_type="image/png", filename="sample_medical_legal.png")


@router.get("/samples/forensic_report")
def get_sample_forensic_report():
    sample_path = Path(__file__).resolve().parent.parent.parent / "samples" / "sample_forensic_report.png"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample Forensic Report not found")
    return FileResponse(str(sample_path), media_type="image/png", filename="sample_forensic_report.png")
