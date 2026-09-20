"""Regression tests for the local Ollama multimodal transport fix."""

from __future__ import annotations

import json

from clarity.vlm import client as vlm_client
from clarity.vlm.client import VLMClient, VLMTransportError


class _FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_local_ollama_endpoint_uses_native_transport() -> None:
    client = VLMClient(api_base="http://localhost:11434/v1")
    assert client.use_native_ollama is True


def test_remote_or_non_ollama_endpoint_uses_openai_transport() -> None:
    client = VLMClient(api_base="http://localhost:8000/v1")
    assert client.use_native_ollama is False


def test_native_transport_sends_base64_image_and_json_mode(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _FakeResponse(
            {
                "message": {
                    "role": "assistant",
                    "content": '{"document_type":"fir_report"}',
                }
            }
        )

    monkeypatch.setattr(vlm_client, "urlopen", fake_urlopen)

    client = VLMClient(api_base="http://localhost:11434/v1")
    content, _, transport = client._chat(
        system_prompt="system",
        user_prompt="user",
        image_bytes=b"abc",
        model="qwen2.5vl:3b",
        temperature=0.0,
        num_predict=128,
        repeat_penalty=1.1,
    )

    assert content == '{"document_type":"fir_report"}'
    assert transport == "ollama-native"
    assert captured["payload"]["messages"][1]["images"] == ["YWJj"]
    assert captured["payload"]["format"] == "json"
    assert captured["payload"]["stream"] is False


def test_native_transport_extracts_reasoning_content_when_content_missing(monkeypatch) -> None:
    def fake_urlopen(request, timeout=None):
        return _FakeResponse(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "reasoning": '{"document_type":"fir_report"}',
                }
            }
        )

    monkeypatch.setattr(vlm_client, "urlopen", fake_urlopen)
    client = VLMClient(api_base="http://localhost:11434/v1")
    content, _, _ = client._chat(
        system_prompt="system",
        user_prompt="user",
        image_bytes=b"abc",
        model="qwen2.5vl:3b",
        temperature=0.0,
        num_predict=128,
        repeat_penalty=1.1,
    )
    assert content == '{"document_type":"fir_report"}'


def test_native_transport_raises_on_empty_message(monkeypatch) -> None:
    def fake_urlopen(request, timeout=None):
        return _FakeResponse({"message": {"role": "assistant", "content": ""}})

    monkeypatch.setattr(vlm_client, "urlopen", fake_urlopen)
    client = VLMClient(api_base="http://localhost:11434/v1")

    try:
        client._chat(
            system_prompt="system",
            user_prompt="user",
            image_bytes=b"abc",
            model="qwen2.5vl:3b",
            temperature=0.0,
            num_predict=128,
            repeat_penalty=1.1,
        )
    except VLMTransportError as exc:
        assert "empty assistant message" in str(exc)
    else:
        raise AssertionError("Expected VLMTransportError")


def test_filename_fallback_covers_police_sample_types() -> None:
    assert VLMClient.infer_document_type_from_filename("01_fir_report.png") == "fir_report"
    assert VLMClient.infer_document_type_from_filename("02_seizure_memo.png") == "seizure_memo"
    assert VLMClient.infer_document_type_from_filename("03_arrest_memo.png") == "arrest_memo"
    assert VLMClient.infer_document_type_from_filename("04_medico_legal.png") == "medical_legal"
    assert VLMClient.infer_document_type_from_filename("05_forensic_report.png") == "forensic_report"


def test_message_content_supports_dict_and_object_shapes() -> None:
    assert vlm_client._message_content({"content": "hello"}) == "hello"

    class Message:
        content = ""
        reasoning_content = "reasoned"

    assert vlm_client._message_content(Message()) == "reasoned"
