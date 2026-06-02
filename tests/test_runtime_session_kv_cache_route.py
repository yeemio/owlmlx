"""HTTP wiring for experimental session KV cache hints."""

from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

from owlmlx.host_pressure import host_pressure_not_sampled_snapshot
from owlmlx.runtime.backends import FakeBackend
from owlmlx.runtime.backends import render_chat_messages
from owlmlx.runtime.kernel import RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.runtime.types import GenerateCohortResult, GenerateResult, StreamEvent


class _RecordingBackend(FakeBackend):
    def __init__(self) -> None:
        super().__init__()
        self.last_kwargs: dict[str, Any] = {}

    def generate(self, model_id: str, prompt: str, **kwargs: object):
        self.last_kwargs = dict(kwargs)
        return super().generate(model_id, prompt, **kwargs)

    def generate_messages(self, model_id: str, messages, **kwargs: object):
        self.last_kwargs = dict(kwargs)
        return super().generate_messages(model_id, messages, **kwargs)

    def generate_cohort(
        self,
        model_id: str,
        prompts: list[str],
        **kwargs: object,
    ) -> GenerateCohortResult:
        self.last_kwargs = dict(kwargs)
        return super().generate_cohort(model_id, prompts, **kwargs)


class _CacheMetadataBackend(_RecordingBackend):
    def generate_messages(self, model_id: str, messages, **kwargs: object):
        self.last_kwargs = dict(kwargs)
        return GenerateResult(
            ok=True,
            message="generated with real cache metadata",
            model_id=model_id,
            text="cached response",
            finish_reason="stop",
            prompt_tokens=8,
            completion_tokens=2,
            detail={
                "session_kv_cache": {
                    "cached_prompt_tokens": 5,
                    "cache_decision": "reuse",
                    "cache_reason_code": "session_cache_hit",
                }
            },
        )


class _NoHeaderAutoPrefixStreamingBackend(_RecordingBackend):
    def __init__(self) -> None:
        super().__init__()
        self._remembered_prompt: str | None = None
        self.seen_stream_kwargs: list[dict[str, Any]] = []

    def stream_generate_messages(self, model_id: str, messages, **kwargs: object):
        prompt = render_chat_messages(messages)
        kwargs_dict = dict(kwargs)
        self.last_kwargs = kwargs_dict
        self.seen_stream_kwargs.append(kwargs_dict)
        cached_prompt_tokens = None
        if (
            self._remembered_prompt is not None
            and prompt.startswith(self._remembered_prompt)
            and prompt != self._remembered_prompt
        ):
            cached_prompt_tokens = len(self._remembered_prompt.split())
        self._remembered_prompt = prompt
        detail = {}
        if cached_prompt_tokens is not None:
            detail = {
                "session_kv_cache": {
                    "cached_prompt_tokens": cached_prompt_tokens,
                    "cache_decision": "reuse",
                    "cache_reason_code": "session_cache_hit",
                }
            }
        return [
            StreamEvent(
                event="token",
                model_id=model_id,
                text="ok",
                prompt_tokens=len(prompt.split()),
                completion_tokens=1,
                finish_reason="stop",
                detail=detail,
            ),
            StreamEvent(
                event="done",
                model_id=model_id,
                finish_reason="stop",
                prompt_tokens=len(prompt.split()),
                completion_tokens=1,
                detail=detail,
            ),
        ]


def _client_with_recording_backend() -> tuple[TestClient, _RecordingBackend]:
    backend = _RecordingBackend()
    kernel = RuntimeKernel(
        backend,
        host_pressure_sampler=host_pressure_not_sampled_snapshot,
    )
    loaded = kernel.load_model("fake-model")
    assert loaded.ok is True
    return TestClient(create_app(kernel)), backend


def _client_with_cache_metadata_backend() -> tuple[TestClient, _CacheMetadataBackend]:
    backend = _CacheMetadataBackend()
    kernel = RuntimeKernel(
        backend,
        host_pressure_sampler=host_pressure_not_sampled_snapshot,
    )
    loaded = kernel.load_model("fake-model")
    assert loaded.ok is True
    return TestClient(create_app(kernel)), backend


def _client_with_no_header_auto_prefix_backend() -> tuple[
    TestClient,
    _NoHeaderAutoPrefixStreamingBackend,
]:
    backend = _NoHeaderAutoPrefixStreamingBackend()
    kernel = RuntimeKernel(
        backend,
        host_pressure_sampler=host_pressure_not_sampled_snapshot,
    )
    loaded = kernel.load_model("fake-model")
    assert loaded.ok is True
    return TestClient(create_app(kernel)), backend


def _sse_json_payloads(response_text: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for line in response_text.splitlines():
        if not line.startswith("data: "):
            continue
        data = line.removeprefix("data: ").strip()
        if data == "[DONE]":
            continue
        payloads.append(json.loads(data))
    return payloads


def test_openai_completion_header_sets_session_id_kwarg() -> None:
    client, backend = _client_with_recording_backend()

    response = client.post(
        "/v1/completions",
        headers={"x-owlmlx-session-id": "session-a"},
        json={"model": "fake-model", "prompt": "hi", "max_tokens": 2},
    )

    assert response.status_code == 200
    assert backend.last_kwargs["session_id"] == "session-a"


def test_native_generate_header_sets_session_id_kwarg() -> None:
    client, backend = _client_with_recording_backend()

    response = client.post(
        "/v1/generate",
        headers={"x-owlmlx-session-id": "session-native"},
        json={"model_id": "fake-model", "prompt": "hi", "params": {"max_tokens": 2}},
    )

    assert response.status_code == 200
    assert backend.last_kwargs["session_id"] == "session-native"


def test_session_kv_cache_status_fallback_for_non_native_backend() -> None:
    client, _backend = _client_with_recording_backend()

    response = client.get("/v1/runtime/session-kv-cache")

    assert response.status_code == 200
    payload = response.json()
    assert payload["surface"] == "owlmlx.session_kv_cache"
    assert payload["capability_label"] == "experimental"
    assert payload["enabled"] is False
    assert payload["reason_code"] == "backend_does_not_expose_session_kv_cache"


def test_openai_chat_usage_does_not_fabricate_cached_tokens() -> None:
    client, _backend = _client_with_recording_backend()

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 2,
        },
    )

    assert response.status_code == 200
    usage = response.json()["usage"]
    assert usage["prompt_tokens"] >= 1
    assert "prompt_tokens_details" not in usage


def test_openai_chat_usage_maps_real_cached_tokens_from_backend_detail() -> None:
    client, _backend = _client_with_cache_metadata_backend()

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 2,
        },
    )

    assert response.status_code == 200
    usage = response.json()["usage"]
    assert usage["prompt_tokens"] == 8
    assert usage["completion_tokens"] == 2
    assert usage["prompt_tokens_details"]["cached_tokens"] == 5


def test_anthropic_usage_maps_real_cached_tokens_from_backend_detail() -> None:
    client, _backend = _client_with_cache_metadata_backend()

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 2,
        },
    )

    assert response.status_code == 200
    usage = response.json()["usage"]
    assert usage["input_tokens"] == 8
    assert usage["output_tokens"] == 2
    assert usage["cache_read_input_tokens"] == 5


def test_openai_stream_no_header_auto_prefix_hit_maps_cached_tokens() -> None:
    client, backend = _client_with_no_header_auto_prefix_backend()

    first = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "shared prefix"}],
            "stream": True,
            "max_tokens": 1,
        },
    )
    second = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "shared prefix plus suffix"}],
            "stream": True,
            "max_tokens": 1,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    for kwargs in backend.seen_stream_kwargs:
        assert "session_id" not in kwargs
    second_payloads = _sse_json_payloads(second.text)
    usage_chunks = [payload["usage"] for payload in second_payloads if "usage" in payload]
    assert usage_chunks[-1]["prompt_tokens_details"]["cached_tokens"] == len(
        "user: shared prefix".split()
    )


def test_anthropic_stream_no_header_auto_prefix_hit_maps_cache_read_tokens() -> None:
    client, backend = _client_with_no_header_auto_prefix_backend()

    first = client.post(
        "/v1/messages",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "shared prefix"}],
            "stream": True,
            "max_tokens": 1,
        },
    )
    second = client.post(
        "/v1/messages",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "shared prefix plus suffix"}],
            "stream": True,
            "max_tokens": 1,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    for kwargs in backend.seen_stream_kwargs:
        assert "session_id" not in kwargs
    message_deltas = [
        payload
        for payload in _sse_json_payloads(second.text)
        if payload.get("type") == "message_delta"
    ]
    assert message_deltas[-1]["usage"]["cache_read_input_tokens"] == len(
        "user: shared prefix".split()
    )
