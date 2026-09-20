"""Tests for the Clarity -> investigation-engine Graph Contract adapter."""

import json

import pytest

from clarity.contract.schemas import GraphContractResponse
from clarity.intelligence import (
    GraphContractAdapter,
    GraphContractAdapterError,
    InvestigationStatus,
    NodeKind,
)


def sample_contract_dict():
    return {
        "contract_version": "1.0.0",
        "case_id": "CASE-001",
        "batch_id": "BATCH-001",
        "total_documents": 2,
        "entities": [
            {
                "id": "ENT-001",
                "type": "PERSON",
                "name": "Rahul Kumar",
                "normalized_name": "Rahul Kumar",
                "role": "accused",
                "attributes": {"raw_field_name": "party:accused_1"},
                "confidence": 0.96,
                "source": {
                    "document_id": "DOC-001",
                    "filename": "fir.png",
                    "file_hash_sha256": "hash-1",
                    "page": 2,
                    "bounding_box": {"x": 10, "y": 20, "w": 100, "h": 50},
                    "text_span": "Rahul Kumar",
                },
            },
            {
                "id": "ENT-002",
                "type": "ACCOUNT",
                "name": "1234567890",
                "normalized_name": "1234567890",
                "role": "victim_account",
                "attributes": {},
                "confidence": 0.91,
                "source": {
                    "document_id": "DOC-002",
                    "filename": "bank.png",
                    "file_hash_sha256": "hash-2",
                    "page": 1,
                    "text_span": "1234567890",
                },
            },
        ],
        "events": [
            {
                "id": "EVT-001",
                "type": "FINANCIAL_FRAUD",
                "title": "Fraudulent transaction",
                "source_entity": "ENT-002",
                "target_entity": "ENT-001",
                "timestamp": "2026-08-12",
                "timestamp_start": None,
                "timestamp_end": None,
                "attributes": {"total_amount": 50000.0, "currency": "INR"},
                "source": {
                    "document_id": "DOC-002",
                    "filename": "bank.png",
                    "file_hash_sha256": "hash-2",
                    "page": 3,
                    "text_span": "Transaction on 12 Aug 2026",
                },
            }
        ],
        "relationships": [
            {
                "id": "REL-001",
                "source_entity": "ENT-001",
                "target_entity": "EVT-001",
                "relationship_type": "ACCUSED_IN",
                "confidence": 0.95,
                "evidence": "Accused implicated in fraudulent event.",
            }
        ],
        "audit_chain": {"document_count": 2, "integrity": "verified"},
    }


def test_adapts_pydantic_contract_preserving_core_data():
    contract = GraphContractResponse.model_validate(sample_contract_dict())
    graph = GraphContractAdapter().adapt(contract)

    assert graph.case_id == "CASE-001"
    assert graph.total_documents == 2
    assert graph.node_count == 3
    assert graph.relationship_count == 1
    assert graph.entities[0].id == "ENT-001"
    assert graph.entities[0].source.page == 2
    assert graph.entities[0].source.text_span == "Rahul Kumar"
    assert graph.events[0].timestamp == "2026-08-12"
    assert graph.audit_chain["integrity"] == "verified"


def test_adapts_json_string():
    payload = json.dumps(sample_contract_dict())
    graph = GraphContractAdapter().adapt_json(payload)

    assert graph.entities[1].type == "ACCOUNT"
    assert graph.relationships[0].target_kind == NodeKind.EVENT
    assert graph.relationships[0].status == InvestigationStatus.OBSERVED
    assert len(graph.relationships[0].source_refs) == 1
    assert graph.relationships[0].source_refs[0].document_id == "DOC-002"


def test_event_source_and_target_are_preserved():
    graph = GraphContractAdapter().adapt(sample_contract_dict())
    event = graph.events[0]

    assert event.source_entity_id == "ENT-002"
    assert event.target_entity_id == "ENT-001"


def test_missing_relationship_endpoint_is_not_silent():
    payload = sample_contract_dict()
    payload["relationships"][0]["target_entity"] = "ENT-DOES-NOT-EXIST"

    with pytest.raises(GraphContractAdapterError, match="DANGLING_TARGET_ENDPOINT"):
        GraphContractAdapter(strict=True).adapt(payload)


def test_non_strict_mode_returns_quality_issue():
    payload = sample_contract_dict()
    payload["relationships"][0]["source_entity"] = "ENT-MISSING"

    graph = GraphContractAdapter(strict=False).adapt(payload)

    assert any(issue.code == "DANGLING_SOURCE_ENDPOINT" for issue in graph.issues)
    assert graph.relationships[0].source_id == "ENT-MISSING"


def test_duplicate_node_ids_are_reported():
    payload = sample_contract_dict()
    payload["events"][0]["id"] = "ENT-001"

    with pytest.raises(GraphContractAdapterError, match="NODE_ID_COLLISION"):
        GraphContractAdapter(strict=True).adapt(payload)


def test_invalid_json_is_rejected():
    with pytest.raises(GraphContractAdapterError, match="Invalid Graph Contract JSON"):
        GraphContractAdapter().adapt("not-json")


def test_model_serialization_is_json_ready():
    graph = GraphContractAdapter().adapt(sample_contract_dict())
    records = graph.to_records()

    assert records["entities"][0]["source"]["file_hash_sha256"] == "hash-1"
    assert records["relationships"][0]["source_kind"] == "ENTITY"
    assert records["relationships"][0]["target_kind"] == "EVENT"


def test_missing_event_endpoint_is_not_silent():
    payload = sample_contract_dict()
    payload["events"][0]["source_entity"] = "ENT-MISSING"

    with pytest.raises(GraphContractAdapterError, match="DANGLING_EVENT_SOURCE"):
        GraphContractAdapter(strict=True).adapt(payload)


def test_event_endpoint_must_reference_entity_not_event():
    payload = sample_contract_dict()
    payload["events"][0]["source_entity"] = "EVT-001"

    with pytest.raises(GraphContractAdapterError, match="INVALID_EVENT_SOURCE_KIND"):
        GraphContractAdapter(strict=True).adapt(payload)


def test_duplicate_relationship_ids_are_rejected():
    payload = sample_contract_dict()
    payload["relationships"].append(dict(payload["relationships"][0]))

    with pytest.raises(GraphContractAdapterError, match="DUPLICATE_RELATIONSHIP_ID"):
        GraphContractAdapter(strict=True).adapt(payload)
