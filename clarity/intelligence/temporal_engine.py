"""Temporal intelligence primitives for the evidence graph.

The temporal layer is intentionally deterministic and database-agnostic. It
interprets timestamps carried by first-class event nodes (and temporal edge
metadata when present), exposes explicit time-window queries, produces stable
network snapshots, and compares snapshots without inventing dates for undated
evidence.

Design rules:
- ISO-8601 is accepted; naive timestamps are interpreted in a configurable
  timezone (Asia/Kolkata by default for the Indian investigative context).
- Point timestamps represent an instant. start/end timestamps represent an
  interval. Intervals are inclusive at the start and inclusive at the end.
- Invalid temporal values are surfaced as issues; they are never silently
  converted into plausible dates.
- Undated relationships are excluded from temporal edge snapshots unless
  temporal metadata is explicitly present on the edge.
- No temporal inference is performed from document order or evidence text.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from clarity.intelligence.evidence_graph import EvidenceGraph, GraphEdge, GraphNode
from clarity.intelligence.models import NodeKind


class TemporalEngineError(ValueError):
    """Raised when a temporal operation cannot be completed safely."""


class TemporalEngineConfig(BaseModel):
    """Configuration for deterministic temporal parsing and bucketing."""

    model_config = ConfigDict(extra="forbid")

    default_timezone: str = "Asia/Kolkata"
    bucket_size_minutes: int = Field(default=60, ge=1, le=7_200)


class TemporalIssue(BaseModel):
    """Non-silent temporal-data quality issue."""

    model_config = ConfigDict(extra="forbid")

    severity: str
    code: str
    message: str
    object_id: str | None = None
    field: str | None = None


class TimeWindow(BaseModel):
    """Inclusive temporal window used by all temporal queries."""

    model_config = ConfigDict(extra="forbid")

    start: datetime
    end: datetime

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.start > self.end:
            raise ValueError("TimeWindow.start must be <= TimeWindow.end")
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("TimeWindow start/end must be timezone-aware")


class TemporalInterval(BaseModel):
    """Normalized inclusive temporal interval."""

    model_config = ConfigDict(extra="forbid")

    start: datetime
    end: datetime
    source_kind: str
    source_id: str
    precision: str = "datetime"

    def overlaps(self, window: TimeWindow) -> bool:
        return self.start <= window.end and self.end >= window.start

    def contains(self, moment: datetime) -> bool:
        return self.start <= moment <= self.end


class TemporalEvent(BaseModel):
    """A graph object paired with a normalized temporal interval."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    event_type: str
    interval: TemporalInterval
    source_entity_id: str | None = None
    target_entity_id: str | None = None


class TemporalSnapshot(BaseModel):
    """Stable representation of the graph state observed in a time window."""

    model_config = ConfigDict(extra="forbid")

    window: TimeWindow
    node_ids: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    edge_ids: list[str] = Field(default_factory=list)
    active_relationship_pairs: list[tuple[str, str]] = Field(default_factory=list)
    temporal_event_count: int = 0
    undated_edge_count: int = 0


class SnapshotDelta(BaseModel):
    """Deterministic differences between two temporal snapshots."""

    model_config = ConfigDict(extra="forbid")

    from_window: TimeWindow
    to_window: TimeWindow
    added_nodes: list[str] = Field(default_factory=list)
    removed_nodes: list[str] = Field(default_factory=list)
    added_edges: list[str] = Field(default_factory=list)
    removed_edges: list[str] = Field(default_factory=list)
    new_relationship_pairs: list[tuple[str, str]] = Field(default_factory=list)
    disappeared_relationship_pairs: list[tuple[str, str]] = Field(default_factory=list)


class ActivityBucket(BaseModel):
    """Event activity count for one entity and one time bucket."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str
    bucket_start: datetime
    bucket_end: datetime
    event_count: int = Field(ge=0)


@dataclass(frozen=True)
class _ParsedTime:
    value: datetime
    precision: str


def _coerce_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except Exception as exc:  # pragma: no cover - platform-dependent tzdata failures
        raise TemporalEngineError(f"Invalid timezone '{name}'.") from exc


def _parse_datetime(value: Any, *, default_tz: ZoneInfo) -> _ParsedTime:
    if isinstance(value, datetime):
        parsed = value
        precision = "datetime"
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.min)
        precision = "date"
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            raise TemporalEngineError("Temporal value cannot be empty.")
        candidate = raw[:-1] + "+00:00" if raw.endswith(("Z", "z")) else raw
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError as exc:
            # Accept a common ISO-like date-only value without inventing time.
            try:
                parsed_date = date.fromisoformat(raw)
            except ValueError:
                raise TemporalEngineError(f"Unsupported temporal value '{value}'.") from exc
            parsed = datetime.combine(parsed_date, time.min)
            precision = "date"
        else:
            precision = "datetime"
    else:
        raise TemporalEngineError(f"Unsupported temporal value type: {type(value).__name__}.")

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=default_tz)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return _ParsedTime(parsed, precision)


def _window_utc(window: TimeWindow) -> TimeWindow:
    return TimeWindow(
        start=window.start.astimezone(timezone.utc),
        end=window.end.astimezone(timezone.utc),
    )


class TemporalEngine:
    """Deterministic temporal query and snapshot engine over EvidenceGraph."""

    def __init__(self, config: TemporalEngineConfig | None = None) -> None:
        self.config = config or TemporalEngineConfig()
        self._tz = _coerce_timezone(self.config.default_timezone)

    @staticmethod
    def _metadata_value(metadata: Mapping[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in metadata and metadata[key] not in (None, ""):
                return metadata[key]
        return None

    def interval_for_node(self, node: GraphNode) -> TemporalInterval | None:
        """Return an interval for a temporal event node; entity nodes return None."""
        if node.kind != NodeKind.EVENT:
            return None
        return self._interval_from_metadata(node.metadata, source_id=node.id, source_kind="EVENT")

    def interval_for_edge(self, edge: GraphEdge) -> TemporalInterval | None:
        """Return explicit temporal metadata for an edge, if supplied."""
        return self._interval_from_metadata(edge.metadata, source_id=edge.id, source_kind="EDGE")

    def _interval_from_metadata(
        self,
        metadata: Mapping[str, Any],
        *,
        source_id: str,
        source_kind: str,
    ) -> TemporalInterval | None:
        start_raw = self._metadata_value(metadata, "timestamp_start", "start_time", "start")
        end_raw = self._metadata_value(metadata, "timestamp_end", "end_time", "end")
        point_raw = self._metadata_value(metadata, "timestamp", "datetime", "occurred_at")

        try:
            if start_raw is not None or end_raw is not None:
                if start_raw is None and end_raw is not None:
                    end = _parse_datetime(end_raw, default_tz=self._tz)
                    start = end
                elif start_raw is not None and end_raw is None:
                    start = _parse_datetime(start_raw, default_tz=self._tz)
                    end = start
                else:
                    start = _parse_datetime(start_raw, default_tz=self._tz)
                    end = _parse_datetime(end_raw, default_tz=self._tz)
                if start.value > end.value:
                    raise TemporalEngineError(
                        f"Start '{start_raw}' is after end '{end_raw}' for {source_kind} '{source_id}'."
                    )
                return TemporalInterval(
                    start=start.value,
                    end=end.value,
                    source_kind=source_kind,
                    source_id=source_id,
                    precision="datetime" if start.precision == end.precision == "datetime" else "date",
                )

            if point_raw is not None:
                point = _parse_datetime(point_raw, default_tz=self._tz)
                if point.precision == "date":
                    # A date-only event represents the complete local calendar day.
                    local_start = point.value.astimezone(self._tz).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    local_end = local_start + timedelta(days=1) - timedelta(microseconds=1)
                    start = local_start.astimezone(timezone.utc)
                    end = local_end.astimezone(timezone.utc)
                else:
                    start = end = point.value
                return TemporalInterval(
                    start=start,
                    end=end,
                    source_kind=source_kind,
                    source_id=source_id,
                    precision=point.precision,
                )
        except TemporalEngineError:
            raise
        except Exception as exc:
            raise TemporalEngineError(
                f"Unable to parse temporal metadata for {source_kind} '{source_id}'."
            ) from exc
        return None

    def temporal_events(self, graph: EvidenceGraph) -> tuple[list[TemporalEvent], list[TemporalIssue]]:
        """Extract all temporally dated events and report malformed timestamps."""
        events: list[TemporalEvent] = []
        issues: list[TemporalIssue] = []
        for node_id in sorted(graph.nodes):
            node = graph.nodes[node_id]
            if node.kind != NodeKind.EVENT:
                continue
            try:
                interval = self.interval_for_node(node)
            except TemporalEngineError as exc:
                issues.append(
                    TemporalIssue(
                        severity="error",
                        code="INVALID_EVENT_TIME",
                        message=str(exc),
                        object_id=node.id,
                    )
                )
                continue
            if interval is None:
                issues.append(
                    TemporalIssue(
                        severity="warning",
                        code="UNDATED_EVENT",
                        message=f"Event '{node.id}' has no usable temporal metadata.",
                        object_id=node.id,
                    )
                )
                continue
            events.append(
                TemporalEvent(
                    source_id=node.id,
                    event_type=node.type,
                    interval=interval,
                    source_entity_id=node.metadata.get("source_entity_id"),
                    target_entity_id=node.metadata.get("target_entity_id"),
                )
            )
        return events, issues

    @staticmethod
    def _entity_ids_for_event(event: TemporalEvent) -> list[str]:
        return sorted({value for value in (event.source_entity_id, event.target_entity_id) if value})

    def events_in_window(self, graph: EvidenceGraph, window: TimeWindow) -> tuple[list[TemporalEvent], list[TemporalIssue]]:
        normalized_window = _window_utc(window)
        events, issues = self.temporal_events(graph)
        filtered = [event for event in events if event.interval.overlaps(normalized_window)]
        return filtered, issues

    def active_entity_ids(self, graph: EvidenceGraph, window: TimeWindow) -> tuple[list[str], list[TemporalIssue]]:
        events, issues = self.events_in_window(graph, window)
        active: set[str] = set()
        for event in events:
            active.update(self._entity_ids_for_event(event))
        return sorted(active), issues

    def activity_buckets(
        self,
        graph: EvidenceGraph,
        window: TimeWindow,
        *,
        entity_ids: Iterable[str] | None = None,
    ) -> tuple[list[ActivityBucket], list[TemporalIssue]]:
        """Count event occurrences per entity within deterministic time buckets."""
        normalized_window = _window_utc(window)
        events, issues = self.events_in_window(graph, normalized_window)
        selected = set(entity_ids) if entity_ids is not None else None
        bucket_delta = timedelta(minutes=self.config.bucket_size_minutes)

        counts: defaultdict[tuple[str, datetime], int] = defaultdict(int)
        for event in events:
            start = max(event.interval.start, normalized_window.start)
            end = min(event.interval.end, normalized_window.end)
            current = self._floor_bucket(start)
            while current <= end:
                bucket_end = min(current + bucket_delta - timedelta(microseconds=1), normalized_window.end)
                for entity_id in self._entity_ids_for_event(event):
                    if selected is None or entity_id in selected:
                        counts[(entity_id, current)] += 1
                if bucket_end >= end:
                    break
                current += bucket_delta

        result: list[ActivityBucket] = []
        for (entity_id, bucket_start), count in sorted(counts.items(), key=lambda item: (item[0][0], item[0][1])):
            bucket_end = min(
                bucket_start + bucket_delta - timedelta(microseconds=1),
                normalized_window.end,
            )
            result.append(
                ActivityBucket(
                    entity_id=entity_id,
                    bucket_start=bucket_start,
                    bucket_end=bucket_end,
                    event_count=count,
                )
            )
        return result, issues

    def _floor_bucket(self, value: datetime) -> datetime:
        value = value.astimezone(timezone.utc)
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        seconds = int((value - epoch).total_seconds())
        bucket_seconds = self.config.bucket_size_minutes * 60
        floored = seconds - (seconds % bucket_seconds)
        return epoch + timedelta(seconds=floored)

    def snapshot(self, graph: EvidenceGraph, window: TimeWindow) -> tuple[TemporalSnapshot, list[TemporalIssue]]:
        """Build a time-filtered network snapshot without inventing edge dates."""
        normalized_window = _window_utc(window)
        events, issues = self.events_in_window(graph, normalized_window)
        event_ids = {event.source_id for event in events}
        entity_ids = {
            entity_id
            for event in events
            for entity_id in self._entity_ids_for_event(event)
        }

        temporal_edge_ids: set[str] = set()
        active_pairs: set[tuple[str, str]] = set()
        undated_edge_count = 0
        for edge_id in sorted(graph.edges):
            edge = graph.edges[edge_id]
            try:
                interval = self.interval_for_edge(edge)
            except TemporalEngineError as exc:
                issues.append(
                    TemporalIssue(
                        severity="error",
                        code="INVALID_EDGE_TIME",
                        message=str(exc),
                        object_id=edge.id,
                    )
                )
                continue
            if interval is None:
                undated_edge_count += 1
                # An undated direct relationship is intentionally not assigned
                # to the requested time window.
                continue
            if interval.overlaps(normalized_window):
                temporal_edge_ids.add(edge.id)
                active_pairs.add(tuple(sorted((edge.source_id, edge.target_id))))

        # Include structural edges connected to events in the selected window
        # because those edges document participation in the dated event.
        contextual_edge_ids = {
            edge.id
            for edge in graph.edges.values()
            if (
                edge.source_id in event_ids
                or edge.target_id in event_ids
            )
        }
        edge_ids = sorted(temporal_edge_ids | contextual_edge_ids)
        node_ids = sorted(entity_ids | event_ids | {
            graph.edges[edge_id].source_id for edge_id in edge_ids
        } | {
            graph.edges[edge_id].target_id for edge_id in edge_ids
        })
        return (
            TemporalSnapshot(
                window=normalized_window,
                node_ids=node_ids,
                entity_ids=sorted(entity_ids),
                event_ids=sorted(event_ids),
                edge_ids=edge_ids,
                active_relationship_pairs=sorted(active_pairs),
                temporal_event_count=len(events),
                undated_edge_count=undated_edge_count,
            ),
            issues,
        )

    def compare_snapshots(self, before: TemporalSnapshot, after: TemporalSnapshot) -> SnapshotDelta:
        """Compare two snapshots and expose additions/disappearances deterministically."""
        return SnapshotDelta(
            from_window=before.window,
            to_window=after.window,
            added_nodes=sorted(set(after.node_ids) - set(before.node_ids)),
            removed_nodes=sorted(set(before.node_ids) - set(after.node_ids)),
            added_edges=sorted(set(after.edge_ids) - set(before.edge_ids)),
            removed_edges=sorted(set(before.edge_ids) - set(after.edge_ids)),
            new_relationship_pairs=sorted(
                set(after.active_relationship_pairs) - set(before.active_relationship_pairs)
            ),
            disappeared_relationship_pairs=sorted(
                set(before.active_relationship_pairs) - set(after.active_relationship_pairs)
            ),
        )

    def network_at(self, graph: EvidenceGraph, moment: datetime) -> tuple[TemporalSnapshot, list[TemporalIssue]]:
        """Build a one-instant snapshot using an inclusive point window."""
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=self._tz)
        point = moment.astimezone(timezone.utc)
        return self.snapshot(graph, TimeWindow(start=point, end=point))
