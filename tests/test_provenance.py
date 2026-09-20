from clarity.intelligence.provenance import build_provenance_report
from clarity.intelligence.evidence_graph import EvidenceGraph
from clarity.intelligence.models import EvidenceReference
from clarity.intelligence.evidence_graph import GraphNode
from clarity.intelligence.models import NodeKind


def test_builds_field_and_graph_provenance():
    docs = [{
        "document_id": "doc-1",
        "original_filename": "fir.png",
        "file_hash_sha256": "a" * 64,
        "field_items": [{
            "field_name": "id:FIR Number", "field_value": "29/17", "confidence": 0.9,
            "bounding_box": {"x": 1, "y": 2, "w": 30, "h": 4}
        }],
    }]
    graph = EvidenceGraph(
        contract_version="1.0.0", case_id="CASE-1", total_documents=1,
        nodes={"P1": GraphNode(
            id="P1", kind=NodeKind.ENTITY, type="PERSON", label="Ravi", confidence=0.8,
            source_refs=[EvidenceReference(document_id="doc-1", filename="fir.png", file_hash_sha256="a"*64)]
        )}
    )
    report = build_provenance_report(case_id="CASE-1", documents=docs, graph=graph)
    assert report.summary.field_items == 1
    assert report.summary.entity_items == 1
    assert report.summary.total_items == 2
    field = next(item for item in report.items if item.object_type == "FIELD")
    assert field.source_references[0].bounding_box["w"] == 30.0


def test_finding_provenance_links_graph_objects():
    graph = EvidenceGraph(
        contract_version="1.0.0", case_id="CASE-1",
        nodes={"P1": GraphNode(
            id="P1", kind=NodeKind.ENTITY, type="PERSON", label="Ravi", confidence=0.9,
            source_refs=[EvidenceReference(document_id="d1", filename="a.png", file_hash_sha256="b"*64)]
        )}
    )
    report = build_provenance_report(
        case_id="CASE-1", documents=[], graph=graph,
        findings=[{"finding_id": "F1", "label": "Bridge lead", "bridge_score": 0.81, "supporting_entity_ids": ["P1"]}],
    )
    finding = next(item for item in report.items if item.object_type == "FINDING")
    assert finding.derived_from == ["P1"]
    assert finding.source_references[0].filename == "a.png"
