"""HTTP wiring for experimental session KV cache hints."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from owlmlx.host_pressure import host_pressure_not_sampled_snapshot
from owlmlx.runtime.backends import FakeBackend
from owlmlx.runtime.kernel import RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.runtime.types import GenerateCohortResult, GenerateResult


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
