"""Explainable suspicious-pattern and anomaly detection over EvidenceGraph.

This layer is deliberately deterministic and evidence-first.  It detects
unusual activity and structural/temporal patterns; it does not label people as
criminals or estimate guilt.  Findings are investigative leads that retain the
underlying event/relationship IDs used to produce them.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite, sqrt
from statistics import mean, pstdev
from typing import Any, Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field

from clarity.intelligence.evidence_graph import EvidenceGraph, GraphEdge, GraphNode
from clarity.intelligence.graph_analytics import GraphAnalyticsEngine, GraphAnalyticsReport
from clarity.intelligence.models import NodeKind
from clarity.intelligence.temporal_engine import TemporalEngine, TemporalEngineConfig, TemporalEvent, TimeWindow


class AnomalyEngineError(ValueError):
    """Raised when anomaly analysis cannot be completed safely."""


class AnomalyEngineConfig(BaseModel):
    """Configuration for deterministic pattern/anomaly detection."""

    model_config = ConfigDict(extra="forbid")

    target_entity_types: list[str] = Field(default_factory=lambda: ["PERSON"])
    activity_z_threshold: float = Field(default=3.0, gt=0.0, le=20.0)
    pair_burst_z_threshold: float = Field(default=3.0, gt=0.0, le=20.0)
    minimum_new_relationship_events: int = Field(default=1, ge=1, le=1_000_000)
    minimum_pair_burst_events: int = Field(default=3, ge=1, le=1_000_000)
    minimum_activity_events_for_convergence: int = Field(default=2, ge=1, le=1_000_000)
    structural_convergence_betweenness_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    structural_convergence_activity_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    max_findings: int = Field(default=100, ge=1, le=10_000)
    include_structural_activity_convergence: bool = True


class AnomalyEngineIssue(BaseModel):
    """Non-silent data/analysis quality issue."""

    model_config = ConfigDict(extra="forbid")

    severity: str
    code: str
    message: str
    object_id: str | None = None


class AnomalyFinding(BaseModel):
    """One explainable anomaly or investigative lead."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str
    anomaly_type: str
    title: str
    score: float = Field(ge=0.0, le=1.0)
    severity: str
    status: str = "INVESTIGATIVE_LEAD"
    entity_id: str | None = None
    entity_label: str | None = None
    source_entity_id: str | None = None
    target_entity_id: str | None = None
    explanation: str
    target_window: TimeWindow
    baseline_window: TimeWindow
    supporting_event_ids: list[str] = Field(default_factory=list)
    supporting_relationship_ids: list[str] = Field(default_factory=list)
    signals: dict[str, float] = Field(default_factory=dict)


class AnomalyReport(BaseModel):
    """Complete deterministic anomaly/pattern report for one graph window."""

    model_config = ConfigDict(extra="forbid")

    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    evaluated_entity_count: int = Field(ge=0)
    evaluated_event_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)
    findings: list[AnomalyFinding] = Field(default_factory=list)
    issues: list[AnomalyEngineIssue] = Field(default_factory=list)
    graph_analytics: GraphAnalyticsReport | None = None


@dataclass(frozen=True)
class _EntityActivity:
    target_count: int
    baseline_counts: tuple[int, ...]
    peak_bucket_count: int
    peak_bucket_events: tuple[str, ...]
    peak_bucket_start: datetime | None


@dataclass(frozen=True)
class _PairActivity:
    source_id: str
    target_id: str
    target_count: int
    baseline_count: int
    target_event_ids: tuple[str, ...]
    baseline_event_ids: tuple[str, ...]
    peak_target_count: int
    peak_target_event_ids: tuple[str, ...]


def _utc(window: TimeWindow) -> TimeWindow:
    return TimeWindow(start=window.start.astimezone(timezone.utc), end=window.end.astimezone(timezone.utc))


def _duration(window: TimeWindow) -> timedelta:
    return window.end - window.start


def _derive_baseline(window: TimeWindow) -> TimeWindow:
    """Create an equal-duration baseline immediately preceding the target."""
    normalized = _utc(window)
    duration = _duration(normalized)
    if duration <= timedelta(0):
        duration = timedelta(seconds=1)
    end = normalized.start
    start = end - duration
    return TimeWindow(start=start, end=end - timedelta(microseconds=1))


def _score_from_z(z_value: float, threshold: float) -> float:
    if not isfinite(z_value) or z_value <= 0.0:
        return 0.0
    return round(min(1.0, z_value / threshold), 12)


def _severity(score: float) -> str:
    if score >= 0.80:
        return "HIGH"
    if score >= 0.55:
        return "MEDIUM"
    return "LOW"


def _undirected_pair(left: str, right: str) -> tuple[str, str] | None:
    if not left or not right or left == right:
        return None
    return (left, right) if left < right else (right, left)


def _event_pair(event: TemporalEvent) -> tuple[str, str] | None:
    return _undirected_pair(event.source_entity_id or "", event.target_entity_id or "")


def _bucket_start(value: datetime, bucket_minutes: int) -> datetime:
    value = value.astimezone(timezone.utc)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    seconds = int((value - epoch).total_seconds())
    bucket_seconds = bucket_minutes * 60
    floored = seconds - (seconds % bucket_seconds)
    return epoch + timedelta(seconds=floored)


def _bucket_starts(window: TimeWindow, bucket_minutes: int) -> list[datetime]:
    normalized = _utc(window)
    delta = timedelta(minutes=bucket_minutes)
    current = _bucket_start(normalized.start, bucket_minutes)
    last = _bucket_start(normalized.end, bucket_minutes)
    result: list[datetime] = []
    while current <= last:
        result.append(current)
        current += delta
    return result


def _count_by_entity(
    events: Iterable[TemporalEvent],
    *,
    bucket_minutes: int,
) -> tuple[dict[str, int], dict[str, dict[datetime, list[str]]]]:
    totals: dict[str, int] = defaultdict(int)
    buckets: dict[str, dict[datetime, list[str]]] = defaultdict(lambda: defaultdict(list))
    for event in events:
        bucket = _bucket_start(event.interval.start, bucket_minutes)
        for entity_id in (event.source_entity_id, event.target_entity_id):
            if not entity_id:
                continue
            totals[entity_id] += 1
            buckets[entity_id][bucket].append(event.source_id)
    return dict(totals), {entity: {key: sorted(set(ids)) for key, ids in values.items()} for entity, values in buckets.items()}


def _count_by_pair(
    events: Iterable[TemporalEvent],
    *,
    bucket_minutes: int,
) -> tuple[dict[tuple[str, str], int], dict[tuple[str, str], list[str]], dict[tuple[str, str], dict[datetime, list[str]]]]:
    totals: dict[tuple[str, str], int] = defaultdict(int)
    ids: dict[tuple[str, str], list[str]] = defaultdict(list)
    buckets: dict[tuple[str, str], dict[datetime, list[str]]] = defaultdict(lambda: defaultdict(list))
    for event in events:
        pair = _event_pair(event)
        if pair is None:
            continue
        bucket = _bucket_start(event.interval.start, bucket_minutes)
        totals[pair] += 1
        ids[pair].append(event.source_id)
        buckets[pair][bucket].append(event.source_id)
    return dict(totals), {key: sorted(set(value)) for key, value in ids.items()}, {
        key: {bucket: sorted(set(event_ids)) for bucket, event_ids in value.items()}
        for key, value in buckets.items()
    }


def _baseline_counts_for_entity(bucket_map: Mapping[datetime, list[str]], window: TimeWindow, bucket_minutes: int) -> tuple[int, ...]:
    starts = _bucket_starts(window, bucket_minutes)
    return tuple(len(bucket_map.get(start, ())) for start in starts)


def _baseline_counts_for_pair(bucket_map: Mapping[datetime, list[str]], window: TimeWindow, bucket_minutes: int) -> tuple[int, ...]:
    starts = _bucket_starts(window, bucket_minutes)
    return tuple(len(bucket_map.get(start, ())) for start in starts)


def _z_score(current: float, baseline_counts: Iterable[int]) -> float:
    values = list(baseline_counts)
    if not values:
        return 0.0
    baseline_mean = mean(values)
    baseline_std = pstdev(values)
    denominator = baseline_std + 1.0
    return (current - baseline_mean) / denominator


def _baseline_components(
    entity_ids: Iterable[str],
    baseline_pairs: Iterable[tuple[str, str]],
) -> dict[str, str]:
    """Build deterministic connected components from baseline activity only."""
    adjacency: dict[str, set[str]] = {entity_id: set() for entity_id in entity_ids}
    for left, right in baseline_pairs:
        adjacency.setdefault(left, set()).add(right)
        adjacency.setdefault(right, set()).add(left)

    component_lookup: dict[str, str] = {}
    component_index = 0
    for start in sorted(adjacency):
        if start in component_lookup:
            continue
        component_index += 1
        component_id = f"BASE_COMM_{component_index:03d}"
        stack = [start]
        component_lookup[start] = component_id
        while stack:
            current = stack.pop()
            for neighbor in sorted(adjacency.get(current, ())):
                if neighbor in component_lookup:
                    continue
                component_lookup[neighbor] = component_id
                stack.append(neighbor)
    return component_lookup


class AnomalyEngine:
    """Deterministic, explainable anomaly/pattern engine."""

    def __init__(
        self,
        config: AnomalyEngineConfig | None = None,
        *,
        temporal_engine: TemporalEngine | None = None,
        graph_analytics_engine: GraphAnalyticsEngine | None = None,
    ) -> None:
        self.config = config or AnomalyEngineConfig()
        self.temporal_engine = temporal_engine or TemporalEngine(
            TemporalEngineConfig(bucket_size_minutes=60)
        )
        self.graph_analytics_engine = graph_analytics_engine or GraphAnalyticsEngine()

    def _eligible_entity_ids(self, graph: EvidenceGraph) -> list[str]:
        allowed = set(self.config.target_entity_types)
        return sorted(
            node.id
            for node in graph.nodes.values()
            if node.kind == NodeKind.ENTITY and node.type in allowed
        )

    def _relationship_support(self, graph: EvidenceGraph, pair: tuple[str, str]) -> list[str]:
        left, right = pair
        result: set[str] = set()
        for edge in graph.edges.values():
            if _undirected_pair(edge.source_id, edge.target_id) == pair:
                result.add(edge.id)
        return sorted(result)

    def _temporal_events(
        self,
        graph: EvidenceGraph,
        window: TimeWindow,
    ) -> tuple[list[TemporalEvent], list[AnomalyEngineIssue]]:
        events, temporal_issues = self.temporal_engine.events_in_window(graph, window)
        issues = [
            AnomalyEngineIssue(
                severity=item.severity,
                code=item.code,
                message=item.message,
                object_id=item.object_id,
            )
            for item in temporal_issues
        ]
        return events, issues

    def analyze(
        self,
        graph: EvidenceGraph,
        target_window: TimeWindow,
        *,
        baseline_window: TimeWindow | None = None,
        graph_analytics: GraphAnalyticsReport | None = None,
    ) -> AnomalyReport:
        """Analyze unusual temporal/structural patterns in a target window.

        The baseline defaults to the equal-length period immediately preceding
        the target window.  Undated events/edges are never assigned a time
        implicitly.
        """
        target = _utc(target_window)
        baseline = _utc(baseline_window or _derive_baseline(target))
        if baseline.end >= target.start:
            baseline = TimeWindow(start=baseline.start, end=target.start - timedelta(microseconds=1))
        if baseline.start >= baseline.end:
            raise AnomalyEngineError("Baseline window must contain a positive duration before the target window.")

        issues: list[AnomalyEngineIssue] = []
        target_events, target_issues = self._temporal_events(graph, target)
        baseline_events, baseline_issues = self._temporal_events(graph, baseline)
        issues.extend(target_issues)
        issues.extend(baseline_issues)

        eligible_ids = self._eligible_entity_ids(graph)
        eligible_set = set(eligible_ids)
        target_events = [
            event
            for event in target_events
            if (event.source_entity_id in eligible_set or event.target_entity_id in eligible_set)
        ]
        baseline_events = [
            event
            for event in baseline_events
            if (event.source_entity_id in eligible_set or event.target_entity_id in eligible_set)
        ]

        bucket_minutes = self.temporal_engine.config.bucket_size_minutes
        target_entity_totals, target_entity_buckets = _count_by_entity(target_events, bucket_minutes=bucket_minutes)
        baseline_entity_totals, baseline_entity_buckets = _count_by_entity(baseline_events, bucket_minutes=bucket_minutes)
        target_pair_totals, target_pair_ids, target_pair_buckets = _count_by_pair(target_events, bucket_minutes=bucket_minutes)
        baseline_pair_totals, baseline_pair_ids, baseline_pair_buckets = _count_by_pair(baseline_events, bucket_minutes=bucket_minutes)

        findings: list[AnomalyFinding] = []

        def add_finding(finding: AnomalyFinding) -> None:
            findings.append(finding)

        # 1) Entity activity spikes.
        for entity_id in eligible_ids:
            buckets = target_entity_buckets.get(entity_id, {})
            if not buckets:
                continue
            peak_bucket, peak_events = max(
                buckets.items(),
                key=lambda item: (len(item[1]), -int(item[0].timestamp())),
            )
            baseline_counts = _baseline_counts_for_entity(
                baseline_entity_buckets.get(entity_id, {}), baseline, bucket_minutes
            )
            z = _z_score(len(peak_events), baseline_counts)
            score = _score_from_z(z, self.config.activity_z_threshold)
            if score <= 0.0:
                continue
            label = graph.nodes[entity_id].label
            add_finding(
                AnomalyFinding(
                    finding_id="",
                    anomaly_type="ACTIVITY_SPIKE",
                    title=f"Unusual activity spike for {label}",
                    score=score,
                    severity=_severity(score),
                    entity_id=entity_id,
                    entity_label=label,
                    explanation=(
                        f"Activity reached {len(peak_events)} event(s) in one {bucket_minutes}-minute bucket, "
                        f"versus a baseline mean of {mean(baseline_counts) if baseline_counts else 0:.2f}."
                    ),
                    target_window=target,
                    baseline_window=baseline,
                    supporting_event_ids=sorted(set(peak_events)),
                    signals={
                        "target_peak_events": float(len(peak_events)),
                        "baseline_mean_bucket_events": round(mean(baseline_counts), 12) if baseline_counts else 0.0,
                        "baseline_std_bucket_events": round(pstdev(baseline_counts), 12) if baseline_counts else 0.0,
                        "z_like_score": round(z, 12),
                    },
                )
            )

        # 2) New relationships/interactions in the target window.
        for pair in sorted(target_pair_totals):
            target_count = target_pair_totals[pair]
            baseline_count = baseline_pair_totals.get(pair, 0)
            if baseline_count != 0 or target_count < self.config.minimum_new_relationship_events:
                continue
            score = round(min(1.0, target_count / max(1.0, self.config.minimum_new_relationship_events + 1.0)), 12)
            source_id, target_id = pair
            source_label = graph.nodes[source_id].label if source_id in graph.nodes else source_id
            target_label = graph.nodes[target_id].label if target_id in graph.nodes else target_id
            add_finding(
                AnomalyFinding(
                    finding_id="",
                    anomaly_type="NOVEL_RELATIONSHIP",
                    title=f"New interaction detected: {source_label} ↔ {target_label}",
                    score=score,
                    severity=_severity(score),
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    explanation=(
                        f"The pair has {target_count} time-stamped interaction event(s) in the target window "
                        "and no time-stamped interaction events in the baseline window."
                    ),
                    target_window=target,
                    baseline_window=baseline,
                    supporting_event_ids=target_pair_ids.get(pair, []),
                    supporting_relationship_ids=self._relationship_support(graph, pair),
                    signals={
                        "target_interaction_count": float(target_count),
                        "baseline_interaction_count": float(baseline_count),
                    },
                )
            )

        # 3) Pair-level interaction bursts.
        for pair in sorted(target_pair_totals):
            target_bucket_map = target_pair_buckets.get(pair, {})
            if not target_bucket_map:
                continue
            peak_bucket, peak_events = max(
                target_bucket_map.items(),
                key=lambda item: (len(item[1]), -int(item[0].timestamp())),
            )
            baseline_counts = _baseline_counts_for_pair(
                baseline_pair_buckets.get(pair, {}), baseline, bucket_minutes
            )
            z = _z_score(len(peak_events), baseline_counts)
            score = _score_from_z(z, self.config.pair_burst_z_threshold)
            if len(peak_events) < self.config.minimum_pair_burst_events or score <= 0.0:
                continue
            source_id, target_id = pair
            add_finding(
                AnomalyFinding(
                    finding_id="",
                    anomaly_type="INTERACTION_BURST",
                    title="Unusual interaction burst",
                    score=score,
                    severity=_severity(score),
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    explanation=(
                        f"The relationship produced {len(peak_events)} event(s) in one {bucket_minutes}-minute bucket, "
                        f"versus a baseline mean of {mean(baseline_counts) if baseline_counts else 0:.2f}."
                    ),
                    target_window=target,
                    baseline_window=baseline,
                    supporting_event_ids=sorted(set(peak_events)),
                    supporting_relationship_ids=self._relationship_support(graph, pair),
                    signals={
                        "target_peak_interactions": float(len(peak_events)),
                        "baseline_mean_bucket_interactions": round(mean(baseline_counts), 12) if baseline_counts else 0.0,
                        "baseline_std_bucket_interactions": round(pstdev(baseline_counts), 12) if baseline_counts else 0.0,
                        "z_like_score": round(z, 12),
                    },
                )
            )

        # 4) New cross-component interactions based only on the baseline graph.
        baseline_pairs = sorted(baseline_pair_totals)
        component_lookup = _baseline_components(eligible_ids, baseline_pairs)
        for pair in sorted(target_pair_totals):
            if baseline_pair_totals.get(pair, 0) != 0:
                continue
            left, right = pair
            left_component = component_lookup.get(left)
            right_component = component_lookup.get(right)
            if not left_component or not right_component or left_component == right_component:
                continue
            target_count = target_pair_totals[pair]
            score = round(min(1.0, 0.5 + 0.5 * target_count / (target_count + 1.0)), 12)
            add_finding(
                AnomalyFinding(
                    finding_id="",
                    anomaly_type="CROSS_COMMUNITY_ACTIVITY",
                    title="New cross-community interaction",
                    score=score,
                    severity=_severity(score),
                    source_entity_id=left,
                    target_entity_id=right,
                    explanation=(
                        f"The target window introduces a new interaction between baseline components "
                        f"{left_component} and {right_component}."
                    ),
                    target_window=target,
                    baseline_window=baseline,
                    supporting_event_ids=target_pair_ids.get(pair, []),
                    supporting_relationship_ids=self._relationship_support(graph, pair),
                    signals={
                        "target_interaction_count": float(target_count),
                        "baseline_interaction_count": 0.0,
                        "baseline_components_connected": 0.0,
                    },
                )
            )

        # 5) Structural + temporal convergence: important network role + new activity.
        if self.config.include_structural_activity_convergence:
            analytics = graph_analytics or self.graph_analytics_engine.analyze(graph)
            metric_by_id = {metric.node_id: metric for metric in analytics.metrics}
            for entity_id in eligible_ids:
                metric = metric_by_id.get(entity_id)
                if metric is None or metric.betweenness_centrality < self.config.structural_convergence_betweenness_threshold:
                    continue
                target_count = target_entity_totals.get(entity_id, 0)
                if target_count < self.config.minimum_activity_events_for_convergence:
                    continue
                activity_buckets = target_entity_buckets.get(entity_id, {})
                baseline_counts = _baseline_counts_for_entity(
                    baseline_entity_buckets.get(entity_id, {}), baseline, bucket_minutes
                )
                activity_z = _z_score(max(map(len, activity_buckets.values())), baseline_counts) if activity_buckets else 0.0
                activity_score = _score_from_z(activity_z, self.config.activity_z_threshold)
                if activity_score < self.config.structural_convergence_activity_threshold:
                    continue
                score = round(0.5 * metric.betweenness_centrality + 0.5 * activity_score, 12)
                label = graph.nodes[entity_id].label
                peak_events = max(activity_buckets.values(), key=lambda ids: (len(ids), ids[0]))
                add_finding(
                    AnomalyFinding(
                        finding_id="",
                        anomaly_type="STRUCTURAL_ACTIVITY_CONVERGENCE",
                        title=f"Network-bridge role coincides with unusual activity: {label}",
                        score=score,
                        severity=_severity(score),
                        entity_id=entity_id,
                        entity_label=label,
                        explanation=(
                            "The entity has a strong structural bridge role while its recent activity also "
                            "deviates materially from the baseline. This is an investigative lead, not a guilt determination."
                        ),
                        target_window=target,
                        baseline_window=baseline,
                        supporting_event_ids=sorted(set(event_id for ids in activity_buckets.values() for event_id in ids)),
                        signals={
                            "betweenness_centrality": round(metric.betweenness_centrality, 12),
                            "activity_score": round(activity_score, 12),
                            "target_event_count": float(target_count),
                        },
                    )
                )

        # Stable ordering and deterministic IDs.
        findings.sort(
            key=lambda item: (
                -item.score,
                item.anomaly_type,
                item.entity_id or item.source_entity_id or "",
                item.target_entity_id or "",
                item.title,
            )
        )
        limited = findings[: self.config.max_findings]
        final_findings = [finding.model_copy(update={"finding_id": f"ANOM_{index:04d}"}) for index, finding in enumerate(limited, start=1)]

        analytics_for_report = graph_analytics
        if self.config.include_structural_activity_convergence and analytics_for_report is None:
            analytics_for_report = self.graph_analytics_engine.analyze(graph)

        return AnomalyReport(
            node_count=graph.node_count,
            edge_count=graph.edge_count,
            evaluated_entity_count=len(eligible_ids),
            evaluated_event_count=len(target_events),
            finding_count=len(final_findings),
            findings=final_findings,
            issues=issues,
            graph_analytics=analytics_for_report,
        )
