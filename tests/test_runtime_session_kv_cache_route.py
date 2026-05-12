"""HTTP wiring for experimental session KV cache hints."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from owlmlx.host_pressure import host_pressure_not_sampled_snapshot
from owlmlx.runtime.backends import FakeBackend
from owlmlx.runtime.kernel import RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.runtime.types import GenerateCohortResult


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


def _client_with_recording_backend() -> tuple[TestClient, _RecordingBackend]:
    backend = _RecordingBackend()
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
