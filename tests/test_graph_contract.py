"""Unit and integration tests for Graph Contract schemas, transformer, and ClarityEngine SDK."""

import pytest
from fastapi.testclient import TestClient

from clarity import ClarityEngine, EntityType, EventType, GraphContractResponse
from clarity.api.app import app
from clarity.contract.schemas import (
    EntityContractItem,
    EventContractItem,
    RelationshipContractItem,
    SourceTraceability,
)
from clarity.contract.transformer import _determine_entity_type, build_graph_contract_for_case, build_graph_contract_for_document
from clarity.db.models import Document, ExtractedField, Extraction
from clarity.db.session import SessionLocal


def test_entity_type_classification():
    assert _determine_entity_type("party:complainant_1", "Raj Kumar") == EntityType.PERSON
    assert _determine_entity_type("party:accused_1", "Vikram Singh") == EntityType.PERSON
    assert _determine_entity_type("id:Bank Account Number", "11094988534") == EntityType.ACCOUNT
    assert _determine_entity_type("id:Police Station", "Madhyamgram") == EntityType.ORGANIZATION
    assert _determine_entity_type("id:FIR Number & Year", "FIR No. 45/2018") == EntityType.IDENTIFIER
    assert _determine_entity_type("id:Phone", "9876543210") == EntityType.PHONE
    assert _determine_entity_type("id:Vehicle Reg No", "DL-01-AB-1234") == EntityType.VEHICLE
    assert _determine_entity_type("id:Weapon Description", "Country-made pistol") == EntityType.WEAPON


def test_graph_contract_pydantic_validation():
    entity = EntityContractItem(
        id="ENT-001",
        type=EntityType.PERSON,
        name="Rahul Kumar",
        normalized_name="Rahul Kumar",
        role="complainant",
        attributes={"organization": "Air India"},
        confidence=0.95,
        source=SourceTraceability(
            document_id="doc-123",
            filename="fir.jpg",
            file_hash_sha256="abc123hash",
            page=1,
            text_span="Rahul Kumar",
        ),
    )

    event = EventContractItem(
        id="EVT-001",
        type=EventType.FIR_REGISTRATION,
        title="FIR Registered",
        source_entity="ENT-001",
        target_entity=None,
        timestamp="2026-08-12",
        attributes={"fir_number": "45/2026"},
        source=SourceTraceability(
            document_id="doc-123",
            filename="fir.jpg",
            file_hash_sha256="abc123hash",
            page=1,
        ),
    )

    rel = RelationshipContractItem(
        id="REL-001",
        source_entity="ENT-001",
        target_entity="EVT-001",
        relationship_type="COMPLAINANT_OF",
        confidence=0.99,
        evidence="Rahul Kumar signed FIR complaint",
    )

    response = GraphContractResponse(
        case_id="CASE-001",
        total_documents=1,
        entities=[entity],
        events=[event],
        relationships=[rel],
    )

    dumped = response.model_dump()
    assert dumped["case_id"] == "CASE-001"
    assert len(dumped["entities"]) == 1
    assert dumped["entities"][0]["name"] == "Rahul Kumar"
    assert len(dumped["events"]) == 1
    assert dumped["events"][0]["type"] == "FIR_REGISTRATION"
    assert len(dumped["relationships"]) == 1
    assert dumped["relationships"][0]["relationship_type"] == "COMPLAINANT_OF"


def test_build_graph_contract_from_db_document():
    with SessionLocal() as session:
        doc = session.query(Document).filter(Document.doc_type == "fir_report").first()
        if not doc:
            pytest.skip("No fir_report found in test DB")

        contract = build_graph_contract_for_document(doc)
        assert isinstance(contract, GraphContractResponse)
        assert contract.total_documents == 1
        assert len(contract.entities) >= 1

        # Check entity structure
        person = next((e for e in contract.entities if e.type == EntityType.PERSON), None)
        assert person is not None
        assert person.source.document_id == doc.id
        assert person.source.file_hash_sha256 == doc.file_hash_sha256


def test_clarity_engine_sdk_case_contract():
    engine = ClarityEngine(auto_init_db=False)
    with SessionLocal() as session:
        doc = session.query(Document).filter(Document.case_id.isnot(None)).first()
        if not doc:
            pytest.skip("No document with case_id found in test DB")

        contract = engine.get_case_contract(doc.case_id)
        assert isinstance(contract, GraphContractResponse)
        assert contract.case_id == doc.case_id
        assert contract.total_documents >= 1


def test_api_graph_contract_endpoints():
    client = TestClient(app)
    with SessionLocal() as session:
        doc = session.query(Document).filter(Document.case_id.isnot(None)).first()
        if not doc:
            pytest.skip("No document with case_id found in test DB")

        # Test single document contract
        res_doc = client.get(f"/api/v1/documents/{doc.id}/graph-contract")
        assert res_doc.status_code == 200
        data_doc = res_doc.json()
        assert "entities" in data_doc
        assert "events" in data_doc
        assert "relationships" in data_doc

        # Test case contract
        res_case = client.get(f"/api/v1/cases/{doc.case_id}/graph-contract")
        assert res_case.status_code == 200
        data_case = res_case.json()
        assert data_case["case_id"] == doc.case_id
        assert len(data_case["entities"]) >= 1
