from __future__ import annotations

import json

from fastapi.testclient import TestClient

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def test_healthz_uses_kernel_status() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.get("/healthz")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["readiness"] == "degraded"
    assert payload["model_count"] == 0
    assert payload["persistent_child"] is False
    assert payload["child_health"] == {}


def test_load_generate_models_unload_roundtrip() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    load = client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})
    assert load.status_code == 200
    assert load.json()["ok"] is True

    models = client.get("/v1/models")
    assert models.status_code == 200
    assert models.json()["active_model_id"] == "fake-a"
    assert models.json()["inventory"]["model_count"] == 1
    assert models.json()["health"]["readiness"] == "ready"
    assert models.json()["generation_gate"]["max_concurrent"] == 1

    generated = client.post(
        "/v1/generate",
        json={"prompt": "hello", "params": {"max_tokens": 4}},
    )
    assert generated.status_code == 200
    payload = generated.json()
    assert payload["ok"] is True
    assert payload["model_id"] == "fake-a"
    assert payload["text"].startswith("hello :: fake completion")

    unload = client.post("/v1/unload", json={"model_id": "fake-a"})
    assert unload.status_code == 200
    assert unload.json()["ok"] is True

    after = client.get("/v1/models").json()
    assert after["active_model_id"] is None
    assert after["inventory"]["model_count"] == 0


def test_http_load_respects_memory_budget() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.post("/v1/load", json={"model_id": "too-large", "memory_gb": 7.0})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error_code"] == "memory_budget_exceeded"


def test_generate_without_loaded_model_returns_runtime_error() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.post("/v1/generate", json={"prompt": "hello"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error_code"] == "model_not_loaded"


def test_generate_stream_returns_ndjson_events() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    with client.stream(
        "POST",
        "/v1/generate/stream",
        json={"prompt": "hello", "params": {"max_tokens": 4}},
    ) as response:
        assert response.status_code == 200
        lines = [line for line in response.iter_lines() if line]

    payloads = [json.loads(line) for line in lines]
    assert payloads[0]["event"] == "token"
    assert payloads[-1]["event"] == "done"
    assert payloads[0]["model_id"] == "fake-a"


def test_chat_completions_non_stream_provides_openai_shape() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-a",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 4,
        },
    )

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    payload = response.json()
    assert payload["object"] == "chat.completion"
    assert payload["model"] == "fake-a"
    assert payload["choices"][0]["message"]["role"] == "assistant"


def test_chat_completions_stream_provides_sse_chunks() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "model": "fake-a",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 4,
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "x-request-id" in response.headers
        chunks = [line for line in response.iter_lines() if line]

    assert chunks[0].startswith("data: ")
    assert chunks[-1] == "data: [DONE]"


def test_chat_completions_missing_model_returns_compat_error_status() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "missing",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 4,
        },
    )

    assert response.status_code == 404
    assert "x-request-id" in response.headers
    payload = response.json()
    assert payload["object"] == "error"
    assert payload["error"]["code"] == "model_not_loaded"


def test_openai_models_lists_loaded_models() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get("/v1/openai/models")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    payload = response.json()
    assert payload["object"] == "list"
    assert payload["data"][0]["id"] == "fake-a"


def test_load_requires_model_id_validation() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.post("/v1/load", json={"memory_gb": 1.0})

    assert response.status_code == 422


def test_unload_requires_model_id_validation() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.post("/v1/unload", json={})

    assert response.status_code == 422


def test_generate_requires_prompt_validation() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.post("/v1/generate", json={"params": {"max_tokens": 4}})

    assert response.status_code == 422


def test_load_rejects_negative_memory_validation() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.post("/v1/load", json={"model_id": "bad", "memory_gb": -1.0})

    assert response.status_code == 422


def test_runtime_status_returns_full_kernel_snapshot() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get("/v1/runtime/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_model_id"] == "fake-a"
    assert payload["backend"]["backend_name"] == "fake"
    assert payload["inventory"]["model_count"] == 1
    assert payload["health"]["readiness"] == "ready"


def test_runtime_restart_endpoint_restarts_loaded_model() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post("/v1/runtime/restart", json={"model_id": "fake-a"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["model_id"] == "fake-a"
    models = client.get("/v1/models").json()
    assert models["active_model_id"] == "fake-a"
    assert models["inventory"]["model_count"] == 1


def test_runtime_restart_endpoint_requires_loaded_model() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.post("/v1/runtime/restart", json={"model_id": "missing"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error_code"] == "model_not_loaded"
