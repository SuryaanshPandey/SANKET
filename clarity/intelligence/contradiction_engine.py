"""Deterministic cross-document contradiction detection.

The detector is intentionally conservative. It flags incompatible observations
about the same semantic field and never rewrites the source observations.
"""

from collections import defaultdict
import re
from typing import Any, Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field


class ContradictionObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    filename: str
    field_name: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: dict[str, float] | None = None


class ContradictionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contradiction_id: str
    type: str
    severity: str
    status: str = "REVIEW_REQUIRED"
    field_key: str
    message: str
    observations: list[ContradictionObservation] = Field(default_factory=list)


class ContradictionReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str | None = None
    contradiction_count: int = Field(ge=0)
    high_count: int = Field(ge=0)
    medium_count: int = Field(ge=0)
    low_count: int = Field(ge=0)
    items: list[ContradictionItem] = Field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


_WS_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _normalized_text(value: Any) -> str:
    value = str(value or "").strip().lower()
    return _WS_RE.sub(" ", value)


def _compact_identifier(value: Any) -> str:
    return _NON_ALNUM_RE.sub("", _normalized_text(value))


def _semantic_key(field_name: str) -> str | None:
    raw = _normalized_text(field_name)
    # Strip the UI/storage prefix while keeping the original field name in the observation.
    label = raw.split(":", 1)[-1].strip()

    if label.startswith("notes") or label.startswith("summary") or label.startswith("rule"):
        return None

    # Strong cross-document identifier group used by the case discrepancy detector.
    if any(token in label for token in ("fir", "crime", "case / fir", "case/fir", "case no", "case number")):
        if any(token in label for token in ("number", "no", "ref", "reference")):
            return "case_reference"

    if "police station" in label or "thana" in label:
        return "police_station"
    if "district" in label:
        return "district"
    if "mlc number" in label:
        return "mlc_number"
    if "fsl reference" in label and "crime" not in label:
        return "fsl_reference"
    if "date" in label:
        return "date:" + _NON_ALNUM_RE.sub(" ", label).strip()

    # Exact semantic match for other identifier-like fields.
    if raw.startswith("id:") or raw.startswith("identifier:"):
        compact = _NON_ALNUM_RE.sub(" ", label).strip()
        return "identifier:" + compact
    return None


def _safe_confidence(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 1.0


def _bbox(value: Any) -> dict[str, float] | None:
    if not isinstance(value, Mapping):
        return None
    result: dict[str, float] = {}
    for key in ("x", "y", "w", "h"):
        if key in value:
            try:
                result[key] = float(value[key])
            except (TypeError, ValueError):
                pass
    return result or None


class ContradictionEngine:
    """Conservative cross-document contradiction detector."""

    def analyze(
        self,
        documents: Iterable[Mapping[str, Any]],
        *,
        case_id: str | None = None,
    ) -> ContradictionReport:
        groups: dict[str, list[ContradictionObservation]] = defaultdict(list)
        for document in documents:
            doc_id = str(document.get("document_id", "unknown-document"))
            filename = str(document.get("original_filename", "unknown-document"))
            for field in document.get("field_items") or []:
                value = str(field.get("field_value") or "").strip()
                if not value:
                    continue
                key = _semantic_key(str(field.get("field_name") or ""))
                if key is None:
                    continue
                groups[key].append(
                    ContradictionObservation(
                        document_id=doc_id,
                        filename=filename,
                        field_name=str(field.get("field_name") or "field"),
                        value=value,
                        confidence=_safe_confidence(field.get("confidence", 1.0)),
                        bounding_box=_bbox(field.get("bounding_box")),
                    )
                )

        items: list[ContradictionItem] = []
        for field_key in sorted(groups):
            observations = groups[field_key]
            distinct = {}
            for obs in observations:
                normalized = _compact_identifier(obs.value) if field_key.startswith("case_") or field_key.startswith("identifier:") else _normalized_text(obs.value)
                distinct.setdefault(normalized, []).append(obs)
            if len(distinct) <= 1:
                continue
            severity = "high" if field_key == "case_reference" else "medium"
            values = [obs.value for _, obs_list in sorted(distinct.items()) for obs in obs_list[:1]]
            message = f"Conflicting values observed for '{field_key.replace('_', ' ')}': {', '.join(values)}"
            suffix = field_key.replace(":", "-").replace(" ", "-")
            items.append(
                ContradictionItem(
                    contradiction_id=f"CONTR-{suffix}-{len(items)+1:03d}",
                    type="IDENTIFIER_MISMATCH" if field_key == "case_reference" else "FIELD_VALUE_CONFLICT",
                    severity=severity,
                    field_key=field_key,
                    message=message,
                    observations=sorted(observations, key=lambda item: (item.filename, item.field_name, item.value)),
                )
            )

        return ContradictionReport(
            case_id=case_id,
            contradiction_count=len(items),
            high_count=sum(item.severity == "high" for item in items),
            medium_count=sum(item.severity == "medium" for item in items),
            low_count=sum(item.severity == "low" for item in items),
            items=items,
        )
