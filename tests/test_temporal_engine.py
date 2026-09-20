from datetime import datetime, timezone

from clarity.intelligence.evidence_graph import EvidenceGraphBuilder
from clarity.intelligence.models import (
    CanonicalEntity,
    CanonicalEvent,
    CanonicalRelationship,
    EvidenceReference,
    InvestigationGraph,
    NodeKind,
)
from clarity.intelligence.temporal_engine import (
    TemporalEngine,
    TemporalEngineConfig,
    TimeWindow,
)


def ref(document_id: str) -> EvidenceReference:
    return EvidenceReference(
        document_id=document_id,
        filename=f"{document_id}.txt",
        file_hash_sha256=f"hash-{document_id}",
        page=1,
        text_span="evidence",
    )


def graph() -> object:
    entities = [
        CanonicalEntity(
            id="P1", type="PERSON", name="Alice", normalized_name="alice",
            confidence=0.95, source=ref("D1")
        ),
        CanonicalEntity(
            id="P2", type="PERSON", name="Bob", normalized_name="bob",
            confidence=0.95, source=ref("D2")
        ),
        CanonicalEntity(
            id="P3", type="PERSON", name="Carol", normalized_name="carol",
            confidence=0.95, source=ref("D3")
        ),
    ]
    events = [
        CanonicalEvent(
            id="EV1", type="CALL", title="Alice calls Bob",
            source_entity_id="P1", target_entity_id="P2",
            timestamp="2026-08-02T10:00:00+00:00", source=ref("D1")
        ),
        CanonicalEvent(
            id="EV2", type="CALL", title="Bob calls Carol",
            source_entity_id="P2", target_entity_id="P3",
            timestamp_start="2026-08-10T10:00:00+00:00",
            timestamp_end="2026-08-10T12:00:00+00:00",
            source=ref("D2")
        ),
        CanonicalEvent(
            id="EV3", type="CALL", title="Undated",
            source_entity_id="P1", target_entity_id="P3",
            source=ref("D3")
        ),
    ]
    relationships = [
        CanonicalRelationship(
            id="R1", source_id="P1", target_id="EV1",
            source_kind=NodeKind.ENTITY, target_kind=NodeKind.EVENT,
            relationship_type="PARTICIPATED_IN", confidence=0.9, source_refs=[ref("D1")]
        ),
        CanonicalRelationship(
            id="R2", source_id="P2", target_id="EV2",
            source_kind=NodeKind.ENTITY, target_kind=NodeKind.EVENT,
            relationship_type="PARTICIPATED_IN", confidence=0.9, source_refs=[ref("D2")]
        ),
        CanonicalRelationship(
            id="R3", source_id="P1", target_id="P2",
            source_kind=NodeKind.ENTITY, target_kind=NodeKind.ENTITY,
            relationship_type="ASSOCIATED_WITH", confidence=0.8,
            metadata={"timestamp": "2026-08-02T10:00:00+00:00"}
        ),
        CanonicalRelationship(
            id="R4", source_id="P2", target_id="P3",
            source_kind=NodeKind.ENTITY, target_kind=NodeKind.ENTITY,
            relationship_type="ASSOCIATED_WITH", confidence=0.8,
            metadata={
                "timestamp_start": "2026-08-10T10:00:00+00:00",
                "timestamp_end": "2026-08-10T12:00:00+00:00",
            }
        ),
        CanonicalRelationship(
            id="R5", source_id="P1", target_id="P3",
            source_kind=NodeKind.ENTITY, target_kind=NodeKind.ENTITY,
            relationship_type="ASSOCIATED_WITH", confidence=0.8
        ),
    ]
    investigation = InvestigationGraph(
        contract_version="1.0.0", case_id="CASE-TEMP", total_documents=3,
        entities=entities, events=events, relationships=relationships,
    )
    return EvidenceGraphBuilder().build(investigation)


def window(start: str, end: str) -> TimeWindow:
    return TimeWindow(
        start=datetime.fromisoformat(start).replace(tzinfo=timezone.utc),
        end=datetime.fromisoformat(end).replace(tzinfo=timezone.utc),
    )


def test_event_point_timestamp_is_indexed_and_windowed():
    tg = TemporalEngine()
    events, issues = tg.events_in_window(
        graph(),
        window("2026-08-01T00:00:00", "2026-08-03T00:00:00"),
    )
    assert [event.source_id for event in events] == ["EV1"]
    assert not any(issue.code == "INVALID_EVENT_TIME" for issue in issues)


def test_event_interval_overlaps_window():
    tg = TemporalEngine()
    events, _ = tg.events_in_window(
        graph(),
        window("2026-08-10T11:00:00", "2026-08-10T11:30:00"),
    )
    assert [event.source_id for event in events] == ["EV2"]


def test_undated_event_is_reported_without_inventing_time():
    tg = TemporalEngine()
    events, issues = tg.events_in_window(
        graph(),
        window("2026-08-01T00:00:00", "2026-08-31T23:59:59"),
    )
    assert {event.source_id for event in events} == {"EV1", "EV2"}
    assert any(issue.code == "UNDATED_EVENT" and issue.object_id == "EV3" for issue in issues)


def test_active_entities_come_from_dated_event_participants():
    tg = TemporalEngine()
    ids, _ = tg.active_entity_ids(
        graph(),
        window("2026-08-01T00:00:00", "2026-08-03T00:00:00"),
    )
    assert ids == ["P1", "P2"]


def test_snapshot_includes_event_context_edges_and_explicit_temporal_edges():
    tg = TemporalEngine()
    snapshot, issues = tg.snapshot(
        graph(),
        window("2026-08-01T00:00:00", "2026-08-03T00:00:00"),
    )
    assert snapshot.event_ids == ["EV1"]
    assert snapshot.entity_ids == ["P1", "P2"]
    assert "R1" in snapshot.edge_ids
    assert "R3" in snapshot.edge_ids
    assert "R4" not in snapshot.edge_ids
    assert "R5" not in snapshot.edge_ids
    assert snapshot.undated_edge_count == 3
    assert not any(issue.severity == "error" for issue in issues)


def test_snapshot_at_point_uses_inclusive_interval_semantics():
    tg = TemporalEngine()
    snapshot, _ = tg.network_at(
        graph(), datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)
    )
    assert "EV2" in snapshot.event_ids
    assert "R4" in snapshot.edge_ids


def test_compare_snapshots_detects_added_and_removed_relationships():
    tg = TemporalEngine()
    before, _ = tg.snapshot(
        graph(), window("2026-08-01T00:00:00", "2026-08-03T00:00:00")
    )
    after, _ = tg.snapshot(
        graph(), window("2026-08-10T10:00:00", "2026-08-10T12:00:00")
    )
    delta = tg.compare_snapshots(before, after)
    assert ("P2", "P3") in delta.new_relationship_pairs
    assert ("P1", "P2") in delta.disappeared_relationship_pairs


def test_activity_buckets_count_events_for_participants():
    tg = TemporalEngine(TemporalEngineConfig(bucket_size_minutes=60))
    buckets, _ = tg.activity_buckets(
        graph(), window("2026-08-02T09:00:00", "2026-08-02T11:00:00")
    )
    assert any(bucket.entity_id == "P1" and bucket.event_count == 1 for bucket in buckets)
    assert any(bucket.entity_id == "P2" and bucket.event_count == 1 for bucket in buckets)


def test_invalid_event_time_is_reported_as_error():
    tg_graph = graph()
    tg_graph.nodes["EV1"].metadata["timestamp"] = "not-a-date"
    tg = TemporalEngine()
    events, issues = tg.temporal_events(tg_graph)
    assert all(event.source_id != "EV1" for event in events)
    assert any(issue.code == "INVALID_EVENT_TIME" and issue.object_id == "EV1" for issue in issues)


def test_invalid_edge_time_is_reported_without_dropping_graph_edge():
    tg_graph = graph()
    tg_graph.edges["R3"].metadata["timestamp"] = "not-a-date"
    tg = TemporalEngine()
    snapshot, issues = tg.snapshot(
        tg_graph,
        window("2026-08-01T00:00:00", "2026-08-03T00:00:00"),
    )
    assert "R3" not in snapshot.edge_ids
    assert any(issue.code == "INVALID_EDGE_TIME" and issue.object_id == "R3" for issue in issues)


def test_naive_datetime_uses_configured_timezone():
    tg = TemporalEngine(TemporalEngineConfig(default_timezone="Asia/Kolkata"))
    parsed = tg.interval_for_node(graph().nodes["EV1"])
    assert parsed is not None
    assert parsed.start.tzinfo is not None
