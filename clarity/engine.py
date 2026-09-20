"""ClarityEngine: A high-level, portable Python SDK for evidence-grade document extraction.

Allows any external Python application to import and run forensic VLM document extraction
and receive standardized Graph Contracts (Entities, Events, Relationships, Traceability)
in 3 lines of code.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session

from clarity.contract.schemas import GraphContractResponse
from clarity.contract.transformer import build_graph_contract_for_case, build_graph_contract_for_document
from clarity.db.models import Document
from clarity.db.session import get_db_session, init_db
from clarity.pipeline.batch import BatchExtractionPipeline
from clarity.pipeline.runner import DocumentExtractionPipeline
from clarity.storage import StorageBackend, get_storage
from clarity.vlm.client import VLMClient


class ClarityEngine:
    """Portable, evidence-grade multimodal document intelligence engine.

    Example:
        >>> from clarity import ClarityEngine
        >>> engine = ClarityEngine()
        >>> contract = engine.extract_document("fir_report.jpg")
        >>> for entity in contract.entities:
        ...     print(entity.name, entity.type)
    """

    def __init__(
        self,
        vlm_model: Optional[str] = None,
        storage: Optional[StorageBackend] = None,
        auto_init_db: bool = True,
    ):
        if auto_init_db:
            init_db()
        self.vlm_client = VLMClient(default_model=vlm_model) if vlm_model else VLMClient()
        self.storage = storage or get_storage()
        self.single_pipeline = DocumentExtractionPipeline(vlm_client=self.vlm_client, storage=self.storage)
        self.batch_pipeline = BatchExtractionPipeline(vlm_client=self.vlm_client, doc_pipeline=self.single_pipeline)

    def extract_document(
        self,
        file_path_or_bytes: Union[str, Path, bytes],
        filename: Optional[str] = None,
        case_id: Optional[str] = None,
        actor_id: str = "clarity-engine-sdk",
    ) -> GraphContractResponse:
        """Extract facts from a single document and return the standardized Graph Contract."""
        with get_db_session() as session:
            pipeline_res = self.single_pipeline.process_file(
                file_path_or_bytes=file_path_or_bytes,
                filename=filename,
                case_id=case_id,
                actor_id=actor_id,
                session=session,
            )
            doc = session.query(Document).filter_by(id=pipeline_res.document_id).first()
            if not doc:
                raise RuntimeError(f"Document {pipeline_res.document_id} was not persisted correctly.")
            return build_graph_contract_for_document(doc)

    def extract_batch(
        self,
        files: List[Union[str, Path, bytes, Tuple[str, bytes]]],
        case_id: Optional[str] = None,
        title: Optional[str] = None,
        actor_id: str = "clarity-engine-sdk",
    ) -> GraphContractResponse:
        """Process multiple corroborating documents in a batch and synthesize a unified case Graph Contract."""
        file_payloads = []
        for item in files:
            if isinstance(item, tuple) and len(item) == 2:
                file_payloads.append(item)
            elif isinstance(item, (str, Path)):
                p = Path(item)
                if not p.exists():
                    raise FileNotFoundError(f"Input file does not exist: {p}")
                file_payloads.append((p.name, p.read_bytes()))
            elif isinstance(item, bytes):
                file_payloads.append((f"doc_{len(file_payloads)+1}.bin", item))
            else:
                raise ValueError(f"Unsupported file input type: {type(item)}")

        with get_db_session() as session:
            batch_res = self.batch_pipeline.process_batch(
                files=file_payloads,
                case_id=case_id,
                batch_title=title,
                actor_id=actor_id,
                session=session,
            )
            target_case_id = batch_res.case_id or case_id
            if target_case_id:
                return build_graph_contract_for_case(session, target_case_id)
            elif batch_res.documents:
                # Return graph contract of the primary document in batch
                first_doc_id = batch_res.documents[0]["document_id"]
                doc = session.query(Document).filter_by(id=first_doc_id).first()
                return build_graph_contract_for_document(doc)
            return GraphContractResponse(case_id=target_case_id, total_documents=0)

    def get_document_contract(self, document_id: str) -> GraphContractResponse:
        """Fetch the pre-extracted Graph Contract for an already ingested document by ID."""
        with get_db_session() as session:
            doc = session.query(Document).filter_by(id=document_id).first()
            if not doc:
                raise KeyError(f"Document ID '{document_id}' not found.")
            return build_graph_contract_for_document(doc)

    def get_case_contract(self, case_id: str) -> GraphContractResponse:
        """Fetch the consolidated multi-document Graph Contract for an investigation case."""
        with get_db_session() as session:
            return build_graph_contract_for_case(session, case_id)

    def export_contract_to_file(
        self,
        identifier: str,
        output_path: Union[str, Path],
        is_case: bool = True,
    ) -> Path:
        """Save the Graph Contract JSON to disk."""
        contract = self.get_case_contract(identifier) if is_case else self.get_document_contract(identifier)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(contract.model_dump(), indent=2), encoding="utf-8")
        return out
