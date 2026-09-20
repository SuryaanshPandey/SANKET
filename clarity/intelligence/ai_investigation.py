"""Safe natural-language investigation planning.

The AI layer is deliberately a planner, not an executor. It converts an
investigator question into an allow-listed :class:`InvestigationWorkflow`.
The deterministic workflow engine remains responsible for validation and
execution against the evidence graph.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from clarity.config import settings
from clarity.intelligence.workflow_engine import (
    InvestigationWorkflow,
    InvestigationWorkflowEngine,
    WorkflowNodeType,
)


class InvestigationPlannerError(RuntimeError):
    """Raised when the AI planner cannot produce a safe workflow."""


class InvestigationPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=5, max_length=2000)
    selected_entity_ids: list[str] = Field(default_factory=list, max_length=20)
    max_nodes: int = Field(default=8, ge=1, le=12)


class InvestigationPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    workflow: InvestigationWorkflow
    explanation: str
    warnings: list[str] = Field(default_factory=list)
    planner_model: str
    planner_transport: str


_ALLOWED_NODE_TYPES = {item.value for item in WorkflowNodeType}

_SYSTEM_PROMPT = """You are SANKET's investigation workflow planner.

Your only task is to translate an investigator's natural-language question
into a safe, explicit, deterministic workflow. You do NOT answer the case
question, invent evidence, infer guilt, create accusations, execute tools, or
write database/system commands.

Return JSON only in this exact shape:
{
  "workflow": {
    "workflow_id": "ai-plan",
    "version": "1.0.0",
    "name": "...",
    "description": "...",
    "failure_policy": "STOP",
    "nodes": [
      {
        "id": "node-1",
        "type": "TIME_FILTER|EXPAND_NETWORK|GRAPH_ANALYTICS|KEY_INDIVIDUALS|COMMUNITY_DETECTION|BRIDGE_ANALYSIS|ANOMALY_DETECTION|SHORTEST_PATH|EVIDENCE_REVIEW|REPORT",
        "label": "...",
        "config": {},
        "enabled": true,
        "position": {"x": 0, "y": 0}
      }
    ],
    "edges": [
      {
        "id": "edge-1",
        "source_node_id": "node-1",
        "target_node_id": "node-2",
        "source_port": "output",
        "target_port": "input",
        "enabled": true
      }
    ],
    "metadata": {}
  },
  "explanation": "...",
  "warnings": []
}

Rules:
1. Use ONLY the listed workflow node types.
2. Use ONLY the config keys supported by those node types.
3. Never invent entity IDs. Use provided selected IDs only. If a question
   needs a specific entity that was not supplied, add a warning instead of
   guessing an ID.
4. Prefer workflows that filter time, expand scope, analyze structure, inspect
   evidence, and report. Keep the workflow reproducible.
5. Do not claim that any person is criminal, guilty, or responsible.
6. Treat bridge, anomaly, centrality, and other scores as investigative leads.
7. Do not fabricate findings or source references.
8. Keep node count at or below the requested limit.
9. Edge endpoints MUST copy the exact node IDs emitted in the same workflow.
   Before returning JSON, verify that every edge source_node_id and
   target_node_id matches an existing node id exactly.
10. Prefer simple DAGs. Do not create cycles or reference placeholder IDs
   that are not present in the node list.
"""


def _is_local_ollama(base_url: str) -> bool:
    parsed = urlsplit(base_url)
    return (parsed.hostname or "").lower() in {"localhost", "127.0.0.1", "::1"} and parsed.port == 11434


def _ollama_root(base_url: str) -> str:
    cleaned = base_url.rstrip("/")
    return cleaned[:-3] if cleaned.endswith("/v1") else cleaned


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].lstrip()
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            payload = json.loads(raw[start : end + 1])
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError as exc:
            raise InvestigationPlannerError(f"Planner returned invalid JSON: {exc}") from exc
    raise InvestigationPlannerError("Planner returned no JSON object.")


def _post_json(endpoint: str, payload: Mapping[str, Any], timeout: float, api_key: str | None = None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise InvestigationPlannerError(f"Planner endpoint returned HTTP {exc.code}: {detail[:500]}") from exc
    except URLError as exc:
        raise InvestigationPlannerError(f"Unable to reach planner endpoint: {exc}") from exc
    except TimeoutError as exc:
        raise InvestigationPlannerError("Investigation planner timed out.") from exc
    try:
        result = json.loads(body)
    except json.JSONDecodeError as exc:
        raise InvestigationPlannerError(f"Planner endpoint returned non-JSON response: {body[:300]}") from exc
    if not isinstance(result, dict):
        raise InvestigationPlannerError("Planner endpoint returned an unexpected payload.")
    return result


def _chat_local_ollama(*, question: str, context: Mapping[str, Any], timeout: float, model: str) -> tuple[str, str]:
    endpoint = f"{_ollama_root(settings.openai_api_base)}/api/chat"
    user_prompt = json.dumps({"question": question, "context": context}, ensure_ascii=False)
    response = _post_json(
        endpoint,
        {
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.0, "num_predict": 1800, "num_ctx": settings.vlm_num_ctx},
            "think": False,
        },
        timeout,
    )
    content = ((response.get("message") or {}).get("content") or "").strip()
    if not content:
        raise InvestigationPlannerError("Planner returned an empty response.")
    return content, f"ollama-native:{model}"


def _chat_openai_compatible(*, question: str, context: Mapping[str, Any], timeout: float, model: str) -> tuple[str, str]:
    endpoint = settings.openai_api_base.rstrip("/") + "/chat/completions"
    user_prompt = json.dumps({"question": question, "context": context}, ensure_ascii=False)
    response = _post_json(
        endpoint,
        {
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 1800,
            "response_format": {"type": "json_object"},
        },
        timeout,
        api_key=settings.openai_api_key,
    )
    try:
        message = response["choices"][0]["message"]
        content = str(message.get("content") or "").strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise InvestigationPlannerError("Planner returned no completion choices.") from exc
    if not content:
        raise InvestigationPlannerError("Planner returned an empty response.")
    return content, f"openai-compatible:{model}"


def _reference_alias_index(value: str, node_ids: list[str]) -> str | None:
    """Resolve common small-model placeholder IDs such as node-2 to a real node.

    Small local models sometimes emit ordinal placeholders in edge endpoints
    even though the actual node IDs were serialized correctly. The repair is
    deterministic, local to the returned workflow, and surfaced to the caller
    as a warning. Arbitrary unknown IDs are never guessed.
    """
    if value in node_ids:
        return value
    match = re.fullmatch(r"(?:node|step|n)[_-]?(\d+)", value.strip(), flags=re.IGNORECASE)
    if not match:
        return None
    ordinal = int(match.group(1))
    if 1 <= ordinal <= len(node_ids):
        return node_ids[ordinal - 1]
    if 0 <= ordinal < len(node_ids):
        return node_ids[ordinal]
    return None


def _repair_workflow_edge_references(workflow: InvestigationWorkflow) -> tuple[InvestigationWorkflow, list[str]]:
    """Repair deterministic ordinal edge aliases emitted by local LLMs.

    The planner still rejects arbitrary unknown IDs; this only turns common
    placeholders like ``node-2`` into the exact node ID at ordinal position 2.
    """
    node_ids = [node.id for node in workflow.nodes]
    known = set(node_ids)
    warnings: list[str] = []
    repaired_edges = []
    for edge in workflow.edges:
        source = _reference_alias_index(edge.source_node_id, node_ids)
        target = _reference_alias_index(edge.target_node_id, node_ids)
        if source is None:
            raise InvestigationPlannerError(
                f"AI plan referenced unknown source node '{edge.source_node_id}'. "
                "Use an exact node ID from the workflow nodes list."
            )
        if target is None:
            raise InvestigationPlannerError(
                f"AI plan referenced unknown target node '{edge.target_node_id}'. "
                "Use an exact node ID from the workflow nodes list."
            )
        if source != edge.source_node_id:
            warnings.append(
                f"Repaired AI edge '{edge.id}' source reference '{edge.source_node_id}' -> '{source}'."
            )
        if target != edge.target_node_id:
            warnings.append(
                f"Repaired AI edge '{edge.id}' target reference '{edge.target_node_id}' -> '{target}'."
            )
        if source == target:
            raise InvestigationPlannerError(
                f"AI plan edge '{edge.id}' would create a self-loop on node '{source}'."
            )
        repaired_edges.append(
            edge.model_copy(update={"source_node_id": source, "target_node_id": target})
        )

    repaired = workflow.model_copy(update={"edges": repaired_edges})
    for edge in repaired.edges:
        if edge.source_node_id not in known or edge.target_node_id not in known:
            raise InvestigationPlannerError("AI plan edge repair produced an invalid node reference.")
    return repaired, warnings


def _validate_references(workflow: InvestigationWorkflow, allowed_entity_ids: set[str], graph_node_ids: set[str]) -> list[str]:
    warnings: list[str] = []
    for node in workflow.nodes:
        if node.type == WorkflowNodeType.EXPAND_NETWORK:
            seeds = node.config.get("seed_entity_ids", [])
            for seed in seeds if isinstance(seeds, list) else []:
                seed_id = str(seed)
                if seed_id not in allowed_entity_ids:
                    raise InvestigationPlannerError(
                        f"AI plan referenced seed entity '{seed_id}' that was not explicitly selected by the investigator."
                    )
                if graph_node_ids and seed_id not in graph_node_ids:
                    raise InvestigationPlannerError(f"AI plan referenced an unknown graph node ID '{seed_id}'.")
        if node.type == WorkflowNodeType.SHORTEST_PATH:
            for key in ("source_id", "target_id"):
                value = str(node.config.get(key, ""))
                if not value:
                    raise InvestigationPlannerError(f"SHORTEST_PATH is missing required '{key}'.")
                if value not in allowed_entity_ids:
                    raise InvestigationPlannerError(
                        f"AI plan referenced {key} '{value}' that was not explicitly selected by the investigator."
                    )
                if graph_node_ids and value not in graph_node_ids:
                    raise InvestigationPlannerError(f"AI plan referenced an unknown graph node ID '{value}'.")
    return warnings


class InvestigationPlanner:
    """Generate validated workflows from natural-language questions."""

    def __init__(self, *, model: str | None = None, timeout: float | None = None):
        self.model = model or settings.vlm_default_model
        self.timeout = float(timeout or settings.vlm_timeout_seconds)
        self.engine = InvestigationWorkflowEngine()

    def plan(
        self,
        request: InvestigationPlanRequest,
        *,
        case_context: Mapping[str, Any],
        allowed_entity_ids: set[str] | None = None,
        graph_node_ids: set[str] | None = None,
    ) -> InvestigationPlanResponse:
        context = dict(case_context)
        context["selected_entity_ids"] = request.selected_entity_ids
        context["max_nodes"] = request.max_nodes

        if _is_local_ollama(settings.openai_api_base):
            content, transport = _chat_local_ollama(
                question=request.question,
                context=context,
                timeout=self.timeout,
                model=self.model,
            )
        else:
            content, transport = _chat_openai_compatible(
                question=request.question,
                context=context,
                timeout=self.timeout,
                model=self.model,
            )

        payload = _extract_json_object(content)
        if "workflow" not in payload:
            raise InvestigationPlannerError("Planner response is missing the workflow object.")
        try:
            workflow = InvestigationWorkflow.model_validate(payload["workflow"])
        except ValidationError as exc:
            raise InvestigationPlannerError(f"AI plan failed workflow schema validation: {exc}") from exc

        if len(workflow.nodes) > request.max_nodes:
            raise InvestigationPlannerError(
                f"AI plan exceeds requested node limit ({len(workflow.nodes)} > {request.max_nodes})."
            )

        workflow, repair_warnings = _repair_workflow_edge_references(workflow)

        issues = self.engine.validate(workflow)
        errors = [issue.message for issue in issues if issue.severity == "error"]
        warnings = [issue.message for issue in issues if issue.severity != "error"]
        warnings.extend(repair_warnings)
        if errors:
            raise InvestigationPlannerError("AI plan failed deterministic validation: " + " | ".join(errors[:6]))
        warnings.extend(
            _validate_references(
                workflow,
                set(allowed_entity_ids or set()),
                set(graph_node_ids or set()),
            )
        )

        explanation = str(payload.get("explanation") or "Workflow generated from the investigator question and validated before execution.")
        planner_warnings = payload.get("warnings") or []
        if isinstance(planner_warnings, list):
            warnings.extend(str(item) for item in planner_warnings if str(item).strip())

        return InvestigationPlanResponse(
            question=request.question,
            workflow=workflow,
            explanation=explanation,
            warnings=sorted(set(warnings)),
            planner_model=self.model,
            planner_transport=transport,
        )
