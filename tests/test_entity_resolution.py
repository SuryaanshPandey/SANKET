from clarity.intelligence.entity_resolution import (
    EntityResolutionConfig,
    EntityResolutionStatus,
    EntityResolver,
)
from clarity.intelligence.models import CanonicalEntity, EvidenceReference


def ref(document_id: str) -> EvidenceReference:
    return EvidenceReference(
        document_id=document_id,
        filename=f"{document_id}.txt",
        file_hash_sha256=f"hash-{document_id}",
        page=1,
        text_span="entity",
    )


def entity(
    entity_id: str,
    entity_type: str,
    name: str,
    document_id: str,
    *,
    attributes=None,
    role=None,
    confidence=0.95,
    normalized_name=None,
) -> CanonicalEntity:
    return CanonicalEntity(
        id=entity_id,
        type=entity_type,
        name=name,
        normalized_name=normalized_name or name,
        role=role,
        attributes=attributes or {},
        confidence=confidence,
        source=ref(document_id),
    )


def test_exact_duplicate_person_is_confirmed_and_clustered():
    result = EntityResolver().resolve([
        entity("E1", "PERSON", "Rahul Kumar", "D1"),
        entity("E2", "PERSON", "Rahul Kumar", "D2"),
    ])

    assert result.cluster_count == 1
    assert result.confirmed_clusters[0].member_ids == ["E1", "E2"]
    assert result.confirmed_clusters[0].canonical_name == "Rahul Kumar"
    assert result.entity_to_cluster["E1"] == result.entity_to_cluster["E2"]

    candidate = result.candidates[0]
    assert candidate.status == EntityResolutionStatus.CONFIRMED
    assert candidate.score >= 0.9


def test_strong_phone_identifier_creates_probable_review_candidate():
    result = EntityResolver().resolve([
        entity("E1", "PERSON", "Rahul Kumar", "D1", attributes={"phone": "9876543210"}),
        entity("E2", "PERSON", "R. Kumar", "D2", attributes={"phone": "+91-9876543210"}),
    ])

    assert result.cluster_count == 0
    candidate = result.candidates[0]
    assert candidate.signals.strong_identifier_match == 1.0
    assert candidate.status == EntityResolutionStatus.PROBABLE


def test_fuzzy_name_with_supporting_location_becomes_probable_or_confirmed():
    result = EntityResolver().resolve([
        entity("E1", "PERSON", "Rahul Kumar", "D1", attributes={"location": "Kanpur"}),
        entity("E2", "PERSON", "Rahul Kmar", "D2", attributes={"location": "Kanpur"}),
    ])

    candidate = result.candidates[0]
    assert candidate.status in {
        EntityResolutionStatus.PROBABLE,
        EntityResolutionStatus.CONFIRMED,
    }
    assert "supporting attributes overlap" in candidate.reasons


def test_incompatible_entity_types_are_never_compared():
    result = EntityResolver().resolve([
        entity("E1", "PERSON", "Rahul Kumar", "D1"),
        entity("E2", "ORGANIZATION", "Rahul Kumar", "D2"),
    ])

    assert result.candidates == []


def test_conflicting_phone_identifiers_block_confirmation():
    result = EntityResolver().resolve([
        entity("E1", "PERSON", "Rahul Kumar", "D1", attributes={"phone": "9876543210"}),
        entity("E2", "PERSON", "Rahul Kumar", "D2", attributes={"phone": "9123456780"}),
    ])

    candidate = result.candidates[0]
    assert candidate.signals.contradictory_strong_identifier is True
    assert candidate.status == EntityResolutionStatus.CONTRADICTED
    assert candidate.score < 0.90
    assert result.cluster_count == 0


def test_weak_similarity_remains_unresolved_and_unclustered():
    result = EntityResolver().resolve([
        entity("E1", "PERSON", "Rahul Kumar", "D1"),
        entity("E2", "PERSON", "Suresh Sharma", "D2"),
    ])

    assert result.candidates == []
    assert result.cluster_count == 0
    assert set(result.unresolved_entity_ids) == {"E1", "E2"}


def test_aliases_and_sources_are_preserved_in_cluster():
    result = EntityResolver().resolve([
        entity("E1", "PERSON", "Rahul Kumar", "D1", confidence=0.92),
        entity("E2", "PERSON", "R. Kumar", "D2", confidence=0.98, normalized_name="Rahul Kumar"),
        entity("E3", "PERSON", "Rahul K.", "D3", confidence=0.90, normalized_name="Rahul Kumar"),
    ])

    assert result.cluster_count == 1
    cluster = result.confirmed_clusters[0]
    assert cluster.member_ids == ["E1", "E2", "E3"]
    assert set(cluster.aliases) == {"R. Kumar", "Rahul K."}
    assert cluster.source_document_ids == ["D1", "D2", "D3"]


def test_deterministic_output_order_is_stable():
    entities = [
        entity("E3", "PERSON", "R. Kumar", "D3", attributes={"phone": "9876543210"}),
        entity("E1", "PERSON", "Rahul Kumar", "D1", attributes={"phone": "9876543210"}),
        entity("E2", "PERSON", "Rahul K.", "D2", attributes={"phone": "9876543210"}),
    ]
    first = EntityResolver().resolve(entities)
    second = EntityResolver().resolve(list(reversed(entities)))
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_probable_candidate_is_not_auto_clustered_when_threshold_is_high():
    resolver = EntityResolver(EntityResolutionConfig(auto_cluster_threshold=0.99))
    result = resolver.resolve([
        entity("E1", "PERSON", "Rahul Kumar", "D1"),
        entity("E2", "PERSON", "Rahul Kmar", "D2"),
    ])

    assert result.candidates
    assert result.candidates[0].status == EntityResolutionStatus.CONFIRMED
    assert result.cluster_count == 0


def test_identifier_entity_value_can_confirm_exact_match():
    result = EntityResolver().resolve([
        entity("P1", "PHONE", "+91 98765 43210", "D1"),
        entity("P2", "PHONE", "9876543210", "D2"),
    ])

    assert result.cluster_count == 1
    assert result.candidates[0].status == EntityResolutionStatus.CONFIRMED
    assert result.candidates[0].signals.strong_identifier_match == 1.0
