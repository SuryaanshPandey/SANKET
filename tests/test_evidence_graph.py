from clarity.intelligence.entity_resolution import EntityResolver
from clarity.intelligence.evidence_graph import (
    EvidenceGraphBuilder,
    EvidenceGraphError,
    GraphBuildConfig,
    GraphNode,
)
from clarity.intelligence.models import (
    CanonicalEntity,
    CanonicalEvent,
    CanonicalRelationship,
    EvidenceReference,
    InvestigationGraph,
    InvestigationStatus,
    NodeKind,
)


def ref(document_id: str) -> EvidenceReference:
    return EvidenceReference(
        document_id=document_id,
        filename=f"{document_id}.txt",
        file_hash_sha256=f"hash-{document_id}",
        page=1,
        text_span="evidence",
    )


def entity(entity_id: str, name: str, document_id: str, *, phone: str | None = None) -> CanonicalEntity:
    return CanonicalEntity(
        id=entity_id,
        type="PERSON",
        name=name,
        normalized_name=name,
        attributes={"phone": phone} if phone else {},
        confidence=0.95,
        source=ref(document_id),
    )


def base_graph() -> InvestigationGraph:
    entities = [
        entity("E1", "Rahul Kumar", "D1", phone="9876543210"),
        entity("E2", "Rahul Kumar", "D2", phone="+91-9876543210"),
        entity("E3", "Aman Singh", "D3"),
    ]
    events = [
        CanonicalEvent(
            id="EV1",
            type="CALL",
            title="Call between Rahul and Aman",
            source_entity_id="E1",
            target_entity_id="E3",
            timestamp="2026-08-12T14:30:00",
            source=ref("D3"),
        )
    ]
    relationships = [
        CanonicalRelationship(
            id="REL1",
            source_id="E1",
            target_id="E3",
            source_kind=NodeKind.ENTITY,
            target_kind=NodeKind.ENTITY,
            relationship_type="ASSOCIATED_WITH",
            confidence=0.91,
            status=InvestigationStatus.OBSERVED,
            evidence_text="They were observed together.",
            source_refs=[ref("D3")],
        ),
        CanonicalRelationship(
            id="REL2",
            source_id="E3",
            target_id="EV1",
            source_kind=NodeKind.ENTITY,
            target_kind=NodeKind.EVENT,
            relationship_type="PARTICIPATED_IN",
            confidence=0.96,
            source_refs=[ref("D3")],
        ),
    ]
    return InvestigationGraph(
        contract_version="1.0.0",
        case_id="CASE-001",
        total_documents=3,
        entities=entities,
        events=events,
        relationships=relationships,
        audit_chain={"case_id": "CASE-001"},
    )


def test_graph_collapses_confirmed_entity_cluster_to_canonical_node():
    ig = base_graph()
    resolution = EntityResolver().resolve(ig.entities)

    graph = EvidenceGraphBuilder().build(ig, resolution)

    assert graph.node_count == 3  # canonical Rahul + Aman + event
    assert "E1" in graph.nodes
    assert "E2" not in graph.nodes
    assert graph.nodes["E1"].metadata["resolution_status"] == "CONFIRMED"
    assert set(graph.entity_clusters["E1"]) == {"E1", "E2"}


def test_relationship_endpoint_is_remapped_after_entity_resolution():
    graph = EvidenceGraphBuilder().build(
        base_graph(),
        EntityResolver().resolve(base_graph().entities),
    )
    edge = graph.get_edge("REL1")
    assert edge.source_id == "E1"
    assert edge.target_id == "E3"
    assert edge.metadata["original_source_id"] == "E1"


def test_event_node_preserves_temporal_and_participant_metadata():
    graph = EvidenceGraphBuilder().build(base_graph())
    event = graph.get_node("EV1")
    assert event.kind == NodeKind.EVENT
    assert event.type == "CALL"
    assert event.metadata["timestamp"] == "2026-08-12T14:30:00"
    assert event.metadata["source_entity_id"] == "E1"
    assert event.metadata["target_entity_id"] == "E3"
    assert event.source_refs[0].document_id == "D3"


def test_neighbors_are_deterministic_and_support_directions():
    graph = EvidenceGraphBuilder().build(base_graph())
    assert graph.neighbors("E1", direction="out") == ["E3"]
    assert graph.neighbors("E3", direction="in") == ["E1"]
    assert graph.neighbors("E3", direction="out") == ["EV1"]
    assert graph.neighbors("E3", direction="both") == ["E1", "EV1"]


def test_incident_edges_and_relationship_query():
    graph = EvidenceGraphBuilder().build(base_graph())
    assert [edge.id for edge in graph.incident_edges("E3")] == ["REL1", "REL2"]
    assert [edge.id for edge in graph.relationship_between("E1", "E3")] == ["REL1"]


def test_shortest_path_is_undirected_and_deterministic():
    graph = EvidenceGraphBuilder().build(base_graph())
    assert graph.shortest_path("E1", "EV1") == ["E1", "E3", "EV1"]


def test_relationship_provenance_and_status_are_preserved():
    graph = EvidenceGraphBuilder().build(base_graph())
    edge = graph.get_edge("REL1")
    assert edge.status == InvestigationStatus.OBSERVED
    assert edge.confidence == 0.91
    assert edge.evidence_text == "They were observed together."
    assert edge.source_refs[0].file_hash_sha256 == "hash-D3"


def test_dangling_relationship_fails_in_strict_mode():
    ig = base_graph().model_copy(deep=True)
    ig.relationships.append(
        CanonicalRelationship(
            id="BROKEN",
            source_id="E1",
            target_id="NO_SUCH_NODE",
            source_kind=NodeKind.ENTITY,
            target_kind=NodeKind.ENTITY,
            relationship_type="BAD_REFERENCE",
            confidence=0.5,
        )
    )
    try:
        EvidenceGraphBuilder().build(ig)
    except EvidenceGraphError as exc:
        assert "BROKEN" in str(exc)
    else:
        raise AssertionError("Expected EvidenceGraphError")


def test_dangling_relationship_can_be_reported_non_strictly():
    ig = base_graph().model_copy(deep=True)
    ig.relationships.append(
        CanonicalRelationship(
            id="BROKEN",
            source_id="E1",
            target_id="NO_SUCH_NODE",
            source_kind=NodeKind.ENTITY,
            target_kind=NodeKind.ENTITY,
            relationship_type="BAD_REFERENCE",
            confidence=0.5,
        )
    )
    graph = EvidenceGraphBuilder(
        GraphBuildConfig(reject_dangling_relationships=False)
    ).build(ig)
    assert any(issue.code == "DANGLING_RELATIONSHIP" for issue in graph.issues)
    assert "BROKEN" not in graph.edges


def test_to_records_is_json_ready():
    graph = EvidenceGraphBuilder().build(base_graph())
    records = graph.to_records()
    assert set(records) == {"nodes", "edges", "entity_clusters", "issues"}
    assert any(item["id"] == "E1" for item in records["nodes"])
    assert any(item["id"] == "REL1" for item in records["edges"])


def test_isolated_entity_is_kept_in_graph():
    graph = EvidenceGraphBuilder().build(base_graph())
    assert "E2" in graph.nodes
    assert graph.neighbors("E2") == []


def test_merge_can_be_disabled_for_debugging():
    ig = base_graph()
    resolution = EntityResolver().resolve(ig.entities)
    graph = EvidenceGraphBuilder(
        GraphBuildConfig(merge_confirmed_entities=False)
    ).build(ig, resolution)
    assert {"E1", "E2", "E3", "EV1"}.issubset(graph.nodes)
    assert graph.entity_count == 3


def test_node_collision_is_detected_if_event_id_matches_entity_id():
    ig = base_graph()
    ig.events[0].id = "E1"
    try:
        EvidenceGraphBuilder().build(ig)
    except EvidenceGraphError as exc:
        assert "E1" in str(exc)
    else:
        raise AssertionError("Expected EvidenceGraphError")


def test_confirmed_cluster_aggregates_sources_and_conflicting_attributes():
    ig = base_graph()
    ig.entities[0].attributes["address"] = "Kanpur"
    ig.entities[1].attributes["address"] = "Lucknow"
    resolution = EntityResolver().resolve(ig.entities)
    graph = EvidenceGraphBuilder().build(ig, resolution)
    node = graph.get_node("E1")
    assert {ref.document_id for ref in node.source_refs} == {"D1", "D2"}
    assert node.attributes["address"] == ["Kanpur", "Lucknow"]
    assert node.metadata["attribute_conflicts"]["address"] == ["Kanpur", "Lucknow"]
