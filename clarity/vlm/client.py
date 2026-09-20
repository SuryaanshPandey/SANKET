"""OpenAI-compatible and native Ollama VLM client for document extraction.

The original client sent images as OpenAI ``image_url`` content parts. Current
Ollama OpenAI compatibility supports multimodal chat, but its documented
OpenAI-compatible interface expects image content as base64 rather than an
``image_url`` part. This client therefore uses the native Ollama ``/api/chat``
endpoint for local Ollama servers and retains the OpenAI-compatible path for
other endpoints such as vLLM.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from clarity.config import settings
from clarity.vlm.parser import StructuredExtraction, parse_and_validate_extraction
from clarity.vlm.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    PROMPT_VERSION,
)


class VLMTransportError(RuntimeError):
    """Raised when a VLM transport request cannot be completed."""


_DOCUMENT_TYPE_HINTS = {
    "fir_report": "Focus on FIR number, police station, complainant/informant, accused, victim, occurrence/registration dates, sections/acts, GD number, locations, and incident summary.",
    "seizure_memo": "Focus on seizing officer, accused/from-whom recovered, panch witnesses, recovery/seizure place, recovered items, serial/IMEI numbers, seal status, and seizure date/time.",
    "arrest_memo": "Focus on arrestee, arresting officer, relative/friend informed, place and date/time of arrest, case/FIR number, grounds of arrest, and attesting witness.",
    "charge_sheet": "Focus on accused persons, investigating officer, prosecution witnesses, court, FIR/crime number, acts/sections, final report number, and filing dates.",
    "medical_legal": "Focus on patient/victim/deceased, doctor, hospital, MLC/PMR number, examination/autopsy date/time, injuries, nature of injury, and medical opinion/cause.",
    "forensic_report": "Focus on analyst/examiner, forwarding authority, FSL/crime reference number, evidence/parcel identifiers, seal status, hashes, receipt/report dates, and analytical findings.",
    "case_diary": "Focus on investigating officer, persons/locations/events mentioned, diary dates, case identifiers, actions and observations.",
    "bank_statement": "Focus on account holder, account identifiers, transaction dates, counterparties, amounts, references, and bank identifiers.",
    "invoice": "Focus on seller/vendor, buyer/customer, invoice identifiers, dates, itemized amounts, totals, taxes and payment identifiers.",
    "contract": "Focus on contracting parties, organizations, dates, agreement identifiers, locations and monetary obligations.",
    "id_document": "Focus on document holder, document number, issuing authority, dates, address and other identifying fields visible in the image.",
}


def _message_content(message: Any) -> str:
    """Extract assistant text across OpenAI/Ollama response shapes."""
    if message is None:
        return ""

    if isinstance(message, dict):
        for key in ("content", "reasoning", "reasoning_content"):
            value = message.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    for key in ("content", "reasoning", "reasoning_content"):
        value = getattr(message, key, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _is_local_ollama(base_url: str) -> bool:
    """Detect the normal local Ollama OpenAI-compatible endpoint."""
    parsed = urlsplit(base_url)
    host = (parsed.hostname or "").lower()
    port = parsed.port
    return host in {"localhost", "127.0.0.1", "::1"} and port == 11434


def _ollama_root(base_url: str) -> str:
    """Return the Ollama server root from an OpenAI-style base URL."""
    cleaned = base_url.rstrip("/")
    if cleaned.endswith("/v1"):
        cleaned = cleaned[:-3]
    return cleaned


class VLMClient:
    """Client for multimodal document extraction."""

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_base = api_base or settings.openai_api_base
        self.api_key = api_key or settings.openai_api_key
        self.default_model = default_model or settings.vlm_default_model
        self.timeout = timeout or settings.vlm_timeout_seconds
        self.use_native_ollama = _is_local_ollama(self.api_base)

        self.client = None

    def _format_image_b64(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("ascii")

    def _format_image_url(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{mime_type};base64,{b64}"

    def _build_extra_body(
        self,
        num_predict: int = 2048,
        repeat_penalty: float = 1.15,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Configure Ollama/vLLM generation options."""
        options: Dict[str, Any] = {
            "num_ctx": settings.vlm_num_ctx,
            "num_predict": num_predict,
            "repeat_penalty": repeat_penalty,
            "repeat_last_n": 64,
        }
        if temperature is not None:
            options["temperature"] = temperature

        body: Dict[str, Any] = {"options": options}
        if settings.vlm_disable_thinking:
            body["think"] = False
            body["chat_template_kwargs"] = {"enable_thinking": False}
        return body

    def _native_ollama_chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_bytes: bytes,
        model: str,
        temperature: float,
        num_predict: int,
        repeat_penalty: float,
    ) -> Tuple[str, Dict[str, Any]]:
        """Call Ollama's native multimodal /api/chat endpoint."""
        endpoint = f"{_ollama_root(self.api_base)}/api/chat"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_prompt,
                    "images": [self._format_image_b64(image_bytes)],
                },
            ],
            "stream": False,
            "format": "json",
            "options": {
                "num_ctx": settings.vlm_num_ctx,
                "num_predict": num_predict,
                "repeat_penalty": repeat_penalty,
                "repeat_last_n": 64,
                "temperature": temperature,
            },
        }
        if settings.vlm_disable_thinking:
            payload["think"] = False

        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise VLMTransportError(
                f"Ollama /api/chat returned HTTP {exc.code}: {body[:1000]}"
            ) from exc
        except URLError as exc:
            raise VLMTransportError(f"Unable to reach Ollama at {endpoint}: {exc}") from exc
        except TimeoutError as exc:
            raise VLMTransportError(f"Timed out reaching Ollama at {endpoint}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise VLMTransportError(f"Ollama returned non-JSON response: {raw[:500]}") from exc

        message = data.get("message") or {}
        content = _message_content(message)
        if not content:
            raise VLMTransportError(
                f"Ollama returned an empty assistant message: {json.dumps(data)[:1000]}"
            )
        return content, data

    def _openai_chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_bytes: bytes,
        model: str,
        temperature: float,
        num_predict: int,
        repeat_penalty: float,
        json_mode: bool = True,
    ) -> Tuple[str, Dict[str, Any]]:
        """Call an OpenAI-compatible multimodal endpoint (e.g. vLLM)."""
        image_url = self._format_image_url(image_bytes)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ]

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": num_predict,
            "extra_body": self._build_extra_body(
                num_predict=num_predict,
                repeat_penalty=repeat_penalty,
                temperature=temperature,
            ),
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        if self.client is None:
            try:
                from openai import OpenAI
            except ModuleNotFoundError as exc:
                raise VLMTransportError(
                    "The 'openai' package is required for non-Ollama OpenAI-compatible VLM endpoints."
                ) from exc
            self.client = OpenAI(
                base_url=self.api_base,
                api_key=self.api_key,
                timeout=self.timeout,
            )
        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            raise VLMTransportError(str(exc)) from exc

        if not response.choices:
            raise VLMTransportError("VLM returned no completion choices")

        msg = response.choices[0].message
        content = _message_content(msg)
        if not content:
            raise VLMTransportError("VLM returned an empty assistant message")
        return content, response.model_dump() if hasattr(response, "model_dump") else {}

    def _chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_bytes: bytes,
        model: str,
        temperature: float,
        num_predict: int,
        repeat_penalty: float,
    ) -> Tuple[str, Dict[str, Any], str]:
        """Select the correct transport for the configured endpoint."""
        if self.use_native_ollama:
            content, raw = self._native_ollama_chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                image_bytes=image_bytes,
                model=model,
                temperature=temperature,
                num_predict=num_predict,
                repeat_penalty=repeat_penalty,
            )
            return content, raw, "ollama-native"

        content, raw = self._openai_chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            image_bytes=image_bytes,
            model=model,
            temperature=temperature,
            num_predict=num_predict,
            repeat_penalty=repeat_penalty,
        )
        return content, raw, "openai-compatible"

    def classify_document(self, image_bytes: bytes, model: Optional[str] = None) -> Dict[str, Any]:
        """Fast classification of document category."""
        target_model = model or self.default_model

        try:
            raw_text, raw_response, transport = self._chat(
                system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
                user_prompt="Classify this document according to the requested schema. Inspect the visual layout and handwriting carefully.",
                image_bytes=image_bytes,
                model=target_model,
                temperature=0.0,
                num_predict=256,
                repeat_penalty=1.15,
            )
            from clarity.vlm.parser import extract_json_substring, repair_common_json_issues

            cleaned = repair_common_json_issues(extract_json_substring(raw_text))
            parsed = json.loads(cleaned)
            doc_type = str(parsed.get("document_type", "other")).lower().strip()
            allowed = {
                "fir_report", "seizure_memo", "arrest_memo", "charge_sheet",
                "medical_legal", "forensic_report", "case_diary", "invoice",
                "contract", "bank_statement", "id_document", "other",
            }
            doc_type = self._normalize_doc_type(doc_type, allowed)
            return {
                "document_type": doc_type,
                "confidence": float(parsed.get("confidence", 0.9)),
                "raw_output": parsed,
                "model_used": target_model,
                "transport": transport,
            }
        except Exception as exc:
            return {
                "document_type": "other",
                "confidence": 0.0,
                "raw_output": {"error": str(exc)},
                "model_used": target_model,
                "transport": "failed",
            }

    @staticmethod
    def _normalize_doc_type(doc_type: str, allowed: set[str]) -> str:
        mapping = [
            (["fir", "first information", "b.p. form 27", "iif-1"], "fir_report"),
            (["seizure", "panchnama", "fard", "mahazar", "recovery memo"], "seizure_memo"),
            (["arrest", "inspection memo", "d.k. basu", "giraftari"], "arrest_memo"),
            (["charge sheet", "chargesheet", "challan", "final report", "iif-5"], "charge_sheet"),
            (["medical", "mlc", "injury report", "post-mortem", "pmr", "autopsy", "inquest"], "medical_legal"),
            (["forensic", "fsl", "ballistics", "toxicology", "65b", "63 bsa", "cyber"], "forensic_report"),
            (["case diary", "zimni", "general diary", "station diary", "rojnamcha"], "case_diary"),
            (["invoice", "receipt", "bill"], "invoice"),
            (["contract", "agreement", "deed"], "contract"),
            (["bank", "statement", "passbook"], "bank_statement"),
            (["aadhaar", "passport", "pan", "driving license", "voter"], "id_document"),
        ]
        for needles, normalized in mapping:
            if any(needle in doc_type for needle in needles):
                return normalized
        if doc_type in allowed:
            return doc_type
        return next((cat for cat in allowed if cat in doc_type), "other")

    @classmethod
    def infer_document_type_from_filename(cls, filename: str) -> str:
        """Best-effort fallback for clearly named/local benchmark documents."""
        lower = filename.lower()
        if any(k in lower for k in ["fir", "first_information"]):
            return "fir_report"
        if any(k in lower for k in ["seizure", "panchnama", "recovery"]):
            return "seizure_memo"
        if any(k in lower for k in ["arrest", "giraftari"]):
            return "arrest_memo"
        if any(k in lower for k in ["charge", "chargesheet", "challan"]):
            return "charge_sheet"
        if any(k in lower for k in ["medico", "mlc", "medical", "postmortem", "post_mortem"]):
            return "medical_legal"
        if any(k in lower for k in ["forensic", "fsl", "cyber"]):
            return "forensic_report"
        if any(k in lower for k in ["invoice", "receipt"]):
            return "invoice"
        if any(k in lower for k in ["bank", "statement"]):
            return "bank_statement"
        return "other"

    def extract_structured(
        self,
        image_bytes: bytes,
        model: Optional[str] = None,
        temperature: float = 0.0,
        retry_on_error: bool = True,
        document_type: Optional[str] = None,
    ) -> Tuple[StructuredExtraction, Dict[str, Any]]:
        """Run schema-constrained structured extraction with defensive parsing and retry."""
        target_model = model or self.default_model
        type_hint = _DOCUMENT_TYPE_HINTS.get(document_type or "", "Inspect all visible people, identifiers, dates, amounts, locations, vehicles, organizations, and incident facts relevant to the document.")

        user_prompt = (
            "Extract all visible parties, dates, monetary amounts, identifiers, and a concise incident summary. "
            "Use only information actually present in the image. "
            "For each extracted party/date/amount/identifier, provide a bounding box with x, y, w, h normalized to 0-1000. "
            f"Document-specific focus: {type_hint} "
            "Output JSON only."
        )

        raw_content = ""
        raw_response: Dict[str, Any] = {}
        transport = "unknown"
        primary_error: Optional[str] = None
        try:
            raw_content, raw_response, transport = self._chat(
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                image_bytes=image_bytes,
                model=target_model,
                temperature=temperature,
                num_predict=2048,
                repeat_penalty=1.15,
            )
            structured = parse_and_validate_extraction(raw_content)
            return structured, {
                "raw_text": raw_content,
                "parsed": json.loads(json.dumps(structured.model_dump())),
                "model_used": target_model,
                "prompt_version": PROMPT_VERSION,
                "transport": transport,
            }
        except Exception as exc:
            primary_error = str(exc)

        if not retry_on_error:
            raise VLMTransportError(primary_error or "Primary extraction failed")

        retry_prompt = (
            "CRITICAL: Inspect the image again. Return ONLY one valid JSON object matching the schema. "
            "Do not explain your answer. Do not omit visible facts merely because handwriting is imperfect. "
            f"{type_hint}"
        )
        retry_content = ""
        retry_response: Dict[str, Any] = {}
        retry_transport = "unknown"
        retry_error: Optional[str] = None
        try:
            retry_content, retry_response, retry_transport = self._chat(
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                user_prompt=retry_prompt,
                image_bytes=image_bytes,
                model=target_model,
                temperature=0.0,
                num_predict=2048,
                repeat_penalty=1.20,
            )
            structured = parse_and_validate_extraction(retry_content)
            return structured, {
                "raw_text": retry_content,
                "parsed": json.loads(json.dumps(structured.model_dump())),
                "model_used": target_model,
                "prompt_version": PROMPT_VERSION,
                "recovered_after_retry": True,
                "transport": retry_transport,
                "primary_error": primary_error,
            }
        except Exception as exc:
            retry_error = str(exc)

        # Last-resort parser path preserves the existing behavior, but the
        # failure is now visible to the caller rather than silently discarded.
        fallback_text = retry_content or raw_content
        structured = parse_and_validate_extraction(fallback_text)
        return structured, {
            "raw_text": fallback_text,
            "parsed": json.loads(json.dumps(structured.model_dump())),
            "model_used": target_model,
            "prompt_version": PROMPT_VERSION,
            "recovered_after_retry": False,
            "transport": retry_transport if retry_content else transport,
            "primary_error": primary_error,
            "retry_error": retry_error,
            "transport_failed": not bool(fallback_text),
        }
