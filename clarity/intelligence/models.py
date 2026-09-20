"""Canonical models used by the post-extraction investigation engine.

These models intentionally sit between Clarity's graph contract and later
storage/analytics layers.  They preserve source provenance without making
assumptions about a graph database, UI, or AI provider.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class InvestigationStatus(str, Enum):
    """Epistemic status for evidence-backed relationships/findings."""

    OBSERVED = "OBSERVED"
    CORRELATED = "CORRELATED"
    INFERRED = "INFERRED"
    HYPOTHESIS = "HYPOTHESIS"


class NodeKind(str, Enum):
    """Node classes accepted by the canonical investigation graph."""

    ENTITY = "ENTITY"
    EVENT = "EVENT"


class EvidenceReference(BaseModel):
    """Traceability pointer carried forward from Clarity."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    filename: str
    file_hash_sha256: str
    page: int = Field(default=1, ge=1)
    bounding_box: Optional[Dict[str, float]] = None
    text_span: Optional[str] = None


class CanonicalEntity(BaseModel):
    """Stable internal representation of a Clarity entity."""

    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    name: str
    normalized_name: str
    role: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    source: EvidenceReference
    contract_type: Optional[str] = None


class CanonicalEvent(BaseModel):
    """Stable internal representation of a Clarity event."""

    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    title: str
    source_entity_id: Optional[str] = None
    target_entity_id: Optional[str] = None
    timestamp: Optional[str] = None
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source: EvidenceReference
    contract_type: Optional[str] = None


class CanonicalRelationship(BaseModel):
    """Relationship between an entity/event node pair.

    The Clarity relationship contract does not currently contain a structured
    source document reference, so the adapter preserves its textual evidence
    and only attaches source references that are objectively derivable from a
    linked event endpoint.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    source_id: str
    target_id: str
    source_kind: NodeKind
    target_kind: NodeKind
    relationship_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    status: InvestigationStatus = InvestigationStatus.OBSERVED
    evidence_text: Optional[str] = None
    source_refs: List[EvidenceReference] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AdapterIssue(BaseModel):
    """Non-silent validation/quality issue encountered while adapting."""

    model_config = ConfigDict(extra="forbid")

    severity: str
    code: str
    message: str
    path: Optional[str] = None


class InvestigationGraph(BaseModel):
    """Canonical, database-agnostic investigation graph payload."""

    model_config = ConfigDict(extra="forbid")

    contract_version: str
    case_id: Optional[str] = None
    batch_id: Optional[str] = None
    total_documents: int = Field(default=0, ge=0)
    entities: List[CanonicalEntity] = Field(default_factory=list)
    events: List[CanonicalEvent] = Field(default_factory=list)
    relationships: List[CanonicalRelationship] = Field(default_factory=list)
    audit_chain: Dict[str, Any] = Field(default_factory=dict)
    issues: List[AdapterIssue] = Field(default_factory=list)

    @property
    def node_count(self) -> int:
        return len(self.entities) + len(self.events)

    @property
    def relationship_count(self) -> int:
        return len(self.relationships)

    def node_kinds(self) -> Dict[str, int]:
        return {
            "ENTITY": len(self.entities),
            "EVENT": len(self.events),
        }

    def to_records(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return JSON-ready records for future graph/database adapters."""
        return {
            "entities": [item.model_dump(mode="json") for item in self.entities],
            "events": [item.model_dump(mode="json") for item in self.events],
            "relationships": [item.model_dump(mode="json") for item in self.relationships],
        }
