"""Deterministic, explainable entity resolution for the investigation engine.

The resolver intentionally does not make legal or criminality judgments. It only
estimates whether two extracted records likely refer to the same real-world
entity. High-confidence matches can be clustered automatically; lower-confidence
matches remain reviewable candidates.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Iterable, Mapping, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

from clarity.intelligence.models import CanonicalEntity


class EntityResolutionStatus(str):
    CONFIRMED = "CONFIRMED"
    PROBABLE = "PROBABLE"
    POSSIBLE = "POSSIBLE"
    UNRESOLVED = "UNRESOLVED"
    CONTRADICTED = "CONTRADICTED"


@dataclass(frozen=True)
class EntityResolutionConfig:
    """Resolver thresholds and signal weights.

    Scores are normalized over applicable signals, so a missing attribute does
    not unfairly lower a candidate solely because evidence was not available.
    """

    confirmed_threshold: float = 0.90
    probable_threshold: float = 0.80
    possible_threshold: float = 0.70
    auto_cluster_threshold: float = 0.90
    min_name_similarity_for_candidate: float = 0.68
    max_candidates_per_entity: int = 50

    name_weight: float = 0.55
    strong_identifier_weight: float = 0.35
    attribute_weight: float = 0.07
    role_weight: float = 0.03

    contradiction_penalty: float = 0.30


class MatchSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    strong_identifier_match: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    attribute_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    role_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    contradictory_strong_identifier: bool = False


class EntityMatchCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left_id: str
    right_id: str
    entity_type: str
    score: float = Field(ge=0.0, le=1.0)
    status: str
    signals: MatchSignal
    reasons: list[str] = Field(default_factory=list)


class ResolvedEntityCluster(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cluster_id: str
    entity_type: str
    canonical_entity_id: str
    member_ids: list[str]
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    source_document_ids: list[str] = Field(default_factory=list)


class EntityResolutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entities: list[CanonicalEntity]
    candidates: list[EntityMatchCandidate] = Field(default_factory=list)
    confirmed_clusters: list[ResolvedEntityCluster] = Field(default_factory=list)
    entity_to_cluster: dict[str, str] = Field(default_factory=dict)
    unresolved_entity_ids: list[str] = Field(default_factory=list)

    @property
    def cluster_count(self) -> int:
        return len(self.confirmed_clusters)


_PHONE_KEYS = {
    "phone", "phone_number", "mobile", "mobile_number", "contact", "msisdn"
}

_IDENTIFIER_KEYS = {
    "phone", "phone_number", "mobile", "mobile_number", "contact", "msisdn",
    "account", "account_number", "iban", "vehicle", "vehicle_number",
    "registration", "registration_number", "device", "device_id", "imei",
    "imsi", "ip", "ip_address", "identifier", "identifier_value", "email",
    "email_address", "pan", "aadhaar", "passport", "id", "identifier_id",
}

# These entity types have identifier-like values where exact normalized name
# equality is itself strong evidence.
_STRONG_ID_ENTITY_TYPES = {
    "PHONE", "ACCOUNT", "VEHICLE", "DEVICE", "IDENTIFIER", "IP", "EMAIL"
}


class EntityResolver:
    """Resolve duplicate/noisy extracted entities with transparent scoring."""

    def __init__(self, config: EntityResolutionConfig | None = None) -> None:
        self.config = config or EntityResolutionConfig()

    def resolve(self, entities: Sequence[CanonicalEntity]) -> EntityResolutionResult:
        ordered = sorted(entities, key=lambda e: (e.type, self._normalized_for_matching(e), e.id))
        candidates: list[EntityMatchCandidate] = []

        for i, left in enumerate(ordered):
            generated = 0
            for right in ordered[i + 1 :]:
                if left.type != right.type:
                    continue
                candidate = self._compare(left, right)
                if candidate is None:
                    continue
                candidates.append(candidate)
                generated += 1
                if generated >= self.config.max_candidates_per_entity:
                    break

        confirmed = [
            item for item in candidates
            if item.status == EntityResolutionStatus.CONFIRMED
            and item.score >= self.config.auto_cluster_threshold
        ]
        clusters = self._build_confirmed_clusters(ordered, confirmed)
        clustered_ids = {member for cluster in clusters for member in cluster.member_ids}
        unresolved = sorted(entity.id for entity in ordered if entity.id not in clustered_ids)

        candidates.sort(key=lambda item: (-item.score, item.left_id, item.right_id))
        return EntityResolutionResult(
            entities=ordered,
            candidates=candidates,
            confirmed_clusters=clusters,
            entity_to_cluster={
                member: cluster.cluster_id
                for cluster in clusters
                for member in cluster.member_ids
            },
            unresolved_entity_ids=unresolved,
        )

    def _compare(self, left: CanonicalEntity, right: CanonicalEntity) -> EntityMatchCandidate | None:
        name_similarity = self._name_similarity(left, right)
        strong_match, contradictory = self._strong_identifier_signal(left, right)
        attribute_similarity = self._attribute_similarity(left, right)
        role_similarity = self._role_similarity(left, right)

        reasons: list[str] = []
        if name_similarity >= 0.99:
            reasons.append("normalized names match exactly")
        elif name_similarity >= self.config.min_name_similarity_for_candidate:
            reasons.append(f"name similarity {name_similarity:.2f}")
        if strong_match is not None and strong_match >= 1.0:
            reasons.append("strong identifier overlaps")
        elif strong_match is not None and strong_match > 0:
            reasons.append("partial identifier evidence")
        if attribute_similarity is not None and attribute_similarity >= 0.75:
            reasons.append("supporting attributes overlap")
        if role_similarity is not None and role_similarity >= 0.75:
            reasons.append("role is compatible")
        if contradictory:
            reasons.append("contradictory strong identifiers detected")

        # Candidate gating: a weakly similar pair with no identifier/attribute
        # support is not useful enough to expose as a match candidate.
        has_support = (
            name_similarity >= self.config.min_name_similarity_for_candidate
            or (strong_match is not None and strong_match > 0)
            or (attribute_similarity is not None and attribute_similarity >= 0.60)
        )
        if not has_support:
            return None

        score = self._weighted_score(
            name_similarity=name_similarity,
            strong_match=strong_match,
            attribute_similarity=attribute_similarity,
            role_similarity=role_similarity,
            contradictory=contradictory,
        )
        status = self._status_for_score(score, contradictory)
        if status == EntityResolutionStatus.CONTRADICTED:
            reasons.append("automatic confirmation blocked")

        return EntityMatchCandidate(
            left_id=min(left.id, right.id),
            right_id=max(left.id, right.id),
            entity_type=left.type,
            score=score,
            status=status,
            signals=MatchSignal(
                name_similarity=name_similarity,
                strong_identifier_match=strong_match,
                attribute_similarity=attribute_similarity,
                role_similarity=role_similarity,
                contradictory_strong_identifier=contradictory,
            ),
            reasons=reasons,
        )

    def _weighted_score(
        self,
        *,
        name_similarity: float,
        strong_match: Optional[float],
        attribute_similarity: Optional[float],
        role_similarity: Optional[float],
        contradictory: bool,
    ) -> float:
        weighted_sum = 0.0
        total_weight = 0.0
        for value, weight in (
            (name_similarity, self.config.name_weight),
            (strong_match, self.config.strong_identifier_weight),
            (attribute_similarity, self.config.attribute_weight),
            (role_similarity, self.config.role_weight),
        ):
            if value is None:
                continue
            weighted_sum += value * weight
            total_weight += weight
        score = weighted_sum / total_weight if total_weight else 0.0
        if contradictory:
            score = max(0.0, score - self.config.contradiction_penalty)
        return round(score, 6)

    def _status_for_score(self, score: float, contradictory: bool) -> str:
        if contradictory and score < self.config.confirmed_threshold:
            return EntityResolutionStatus.CONTRADICTED
        if score >= self.config.confirmed_threshold:
            return EntityResolutionStatus.CONFIRMED
        if score >= self.config.probable_threshold:
            return EntityResolutionStatus.PROBABLE
        if score >= self.config.possible_threshold:
            return EntityResolutionStatus.POSSIBLE
        return EntityResolutionStatus.UNRESOLVED

    @staticmethod
    def _normalized_for_matching(entity: CanonicalEntity) -> str:
        base = entity.normalized_name or entity.name
        return _normalize_text(base)

    def _name_similarity(self, left: CanonicalEntity, right: CanonicalEntity) -> float:
        left_name = self._normalized_for_matching(left)
        right_name = self._normalized_for_matching(right)
        if left_name == right_name and left_name:
            return 1.0
        if left.type.upper() in _STRONG_ID_ENTITY_TYPES and right.type.upper() == left.type.upper():
            left_identifier = _normalize_identifier(left.name, kind=left.type)
            right_identifier = _normalize_identifier(right.name, kind=right.type)
            if left_identifier and left_identifier == right_identifier:
                return 1.0
        if not left_name or not right_name:
            return 0.0
        seq = SequenceMatcher(None, left_name, right_name).ratio()
        token = _token_similarity(left_name, right_name)
        return round(max(seq, token), 6)

    def _strong_identifier_signal(
        self,
        left: CanonicalEntity,
        right: CanonicalEntity,
    ) -> tuple[Optional[float], bool]:
        left_values = _identifier_values(left)
        right_values = _identifier_values(right)
        if not left_values or not right_values:
            # For identifier-like entity types, the entity value itself is the
            # identifier even when no structured attribute is available.
            if left.type == right.type and left.type.upper() in _STRONG_ID_ENTITY_TYPES:
                l = _normalize_identifier(left.name, kind=left.type)
                r = _normalize_identifier(right.name, kind=right.type)
                if l and r:
                    return (1.0 if l == r else 0.0), False
            return None, False

        overlap = bool(left_values.all_values & right_values.all_values)
        contradiction = False
        if left_values and right_values and not overlap:
            # If both records supply strong identifiers for the same key and
            # none agrees, treat that as contradictory evidence. Do not do this
            # for heterogeneous identifier keys where a direct comparison is
            # not meaningful.
            shared_keys = set(left_values.by_key) & set(right_values.by_key)
            contradiction = any(
                left_values.by_key[key].isdisjoint(right_values.by_key[key])
                for key in shared_keys
            )

        return (1.0 if overlap else 0.0), contradiction

    def _attribute_similarity(
        self,
        left: CanonicalEntity,
        right: CanonicalEntity,
    ) -> Optional[float]:
        if not left.attributes or not right.attributes:
            return None
        shared_keys = set(left.attributes) & set(right.attributes)
        comparable = 0
        matches = 0
        for key in shared_keys:
            normalized_key = _normalize_key(key)
            if normalized_key in _IDENTIFIER_KEYS:
                lvals = {
                    value
                    for item in _flatten_raw_values(left.attributes[key])
                    for value in [_normalize_identifier(item, key=normalized_key)]
                    if value
                }
                rvals = {
                    value
                    for item in _flatten_raw_values(right.attributes[key])
                    for value in [_normalize_identifier(item, key=normalized_key)]
                    if value
                }
            else:
                lvals = _flatten_values(left.attributes[key])
                rvals = _flatten_values(right.attributes[key])
            if not lvals or not rvals:
                continue
            comparable += 1
            if lvals & rvals:
                matches += 1
        if not comparable:
            return None
        return round(matches / comparable, 6)

    @staticmethod
    def _role_similarity(left: CanonicalEntity, right: CanonicalEntity) -> Optional[float]:
        if not left.role or not right.role:
            return None
        return 1.0 if _normalize_text(left.role) == _normalize_text(right.role) else 0.0

    def _build_confirmed_clusters(
        self,
        entities: Sequence[CanonicalEntity],
        confirmed: Sequence[EntityMatchCandidate],
    ) -> list[ResolvedEntityCluster]:
        parent = {entity.id: entity.id for entity in entities}
        entity_by_id = {entity.id: entity for entity in entities}

        def find(value: str) -> str:
            while parent[value] != value:
                parent[value] = parent[parent[value]]
                value = parent[value]
            return value

        def union(left: str, right: str) -> None:
            root_left, root_right = find(left), find(right)
            if root_left == root_right:
                return
            parent[root_right] = root_left if root_left < root_right else root_right

        for candidate in confirmed:
            union(candidate.left_id, candidate.right_id)

        groups: dict[str, list[str]] = defaultdict(list)
        for entity in entities:
            root = find(entity.id)
            groups[root].append(entity.id)

        clusters: list[ResolvedEntityCluster] = []
        for index, member_ids in enumerate(sorted(groups.values(), key=lambda ids: (len(ids) == 1, ids))):
            if len(member_ids) < 2:
                continue
            members = [entity_by_id[item] for item in sorted(member_ids)]
            canonical = min(
                members,
                key=lambda entity: (-entity.confidence, len(entity.name), entity.id),
            )
            canonical_display_name = canonical.normalized_name or canonical.name
            aliases = sorted({entity.name for entity in members if entity.name != canonical_display_name})
            source_documents = sorted({entity.source.document_id for entity in members})
            cluster_id = f"RES-{index + 1:04d}"
            clusters.append(
                ResolvedEntityCluster(
                    cluster_id=cluster_id,
                    entity_type=canonical.type,
                    canonical_entity_id=canonical.id,
                    member_ids=sorted(member_ids),
                    canonical_name=(canonical.normalized_name or canonical.name),
                    aliases=aliases,
                    source_document_ids=source_documents,
                )
            )
        return clusters


@dataclass(frozen=True)
class _IdentifierValues:
    by_key: Mapping[str, set[str]]

    @property
    def all_values(self) -> set[str]:
        result: set[str] = set()
        for values in self.by_key.values():
            result.update(values)
        return result

    def __bool__(self) -> bool:
        return bool(self.all_values)

    def __contains__(self, item: object) -> bool:
        return item in self.all_values


def _identifier_values(entity: CanonicalEntity) -> _IdentifierValues:
    by_key: dict[str, set[str]] = defaultdict(set)
    for key, value in entity.attributes.items():
        normalized_key = _normalize_key(key)
        if normalized_key not in _IDENTIFIER_KEYS:
            continue
        for item in _flatten_values(value):
            normalized = _normalize_identifier(item, key=normalized_key)
            if normalized:
                by_key[normalized_key].add(normalized)
    if entity.type.upper() in _STRONG_ID_ENTITY_TYPES:
        normalized_name = _normalize_identifier(entity.name, kind=entity.type)
        if normalized_name:
            by_key.setdefault(entity.type.lower(), set()).add(normalized_name)
    return _IdentifierValues(by_key=by_key)


def _flatten_raw_values(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, Mapping):
        values: set[str] = set()
        for item in value.values():
            values.update(_flatten_raw_values(item))
        return values
    if isinstance(value, (list, tuple, set)):
        values: set[str] = set()
        for item in value:
            values.update(_flatten_raw_values(item))
        return values
    text = str(value).strip()
    return {text} if text else set()


def _flatten_values(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, Mapping):
        values: set[str] = set()
        for item in value.values():
            values.update(_flatten_values(item))
        return values
    if isinstance(value, (list, tuple, set)):
        values: set[str] = set()
        for item in value:
            values.update(_flatten_values(item))
        return values
    text = str(value).strip()
    return {_normalize_text(text)} if text else set()


def _normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")


def _normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = text.replace("+", " plus ")
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"_+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_identifier(value: Any, *, key: str | None = None, kind: str | None = None) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    # Preserve letters/digits for identifiers but remove formatting separators.
    cleaned = re.sub(r"[^a-z0-9]", "", text)
    identifier_kind = _normalize_key(key or kind or "")
    if identifier_kind in _PHONE_KEYS or identifier_kind == "phone":
        digits = re.sub(r"[^0-9]", "", text)
        # Canonicalize common Indian domestic/international phone formatting.
        if len(digits) == 12 and digits.startswith("91"):
            return digits[-10:]
        if len(digits) == 11 and digits.startswith("0"):
            return digits[-10:]
        return digits
    return cleaned


def _token_similarity(left: str, right: str) -> float:
    lset = set(left.split())
    rset = set(right.split())
    if not lset or not rset:
        return 0.0
    return len(lset & rset) / len(lset | rset)


__all__ = [
    "EntityMatchCandidate",
    "EntityResolutionConfig",
    "EntityResolutionResult",
    "EntityResolutionStatus",
    "EntityResolver",
    "MatchSignal",
    "ResolvedEntityCluster",
]
