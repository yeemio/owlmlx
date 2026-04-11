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


def test_fake_backend_stream_tokens_are_deltas_not_cumulative() -> None:
    backend = FakeBackend()
    backend.load("fake-a", memory_gb=1.0)

    events = backend.stream_generate("fake-a", "hello world")
    token_texts = [event.text for event in events if event.event == "token"]

    assert token_texts[0] == "hello "
    assert token_texts[1] == "world "
    assert all("hello world" not in token for token in token_texts[:-1])


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
    assert "user: hello" in payload["choices"][0]["message"]["content"]


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


def test_completions_non_stream_provides_openai_shape() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post(
        "/v1/completions",
        json={
            "model": "fake-a",
            "prompt": "hello",
            "max_tokens": 4,
        },
    )

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    payload = response.json()
    assert payload["object"] == "text_completion"
    assert payload["model"] == "fake-a"
    assert payload["choices"][0]["text"].startswith("hello :: fake completion")


def test_completions_stream_provides_sse_chunks() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    with client.stream(
        "POST",
        "/v1/completions",
        json={
            "model": "fake-a",
            "prompt": "hello",
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


def test_anthropic_messages_non_stream_provides_message_shape() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-a",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 4,
        },
    )

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    payload = response.json()
    assert payload["type"] == "message"
    assert payload["role"] == "assistant"
    assert payload["model"] == "fake-a"
    assert payload["content"][0]["type"] == "text"
    assert "user: hello" in payload["content"][0]["text"]
    assert payload["usage"]["input_tokens"] >= 0


def test_anthropic_messages_accept_structured_system_blocks() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-a",
            "system": [
                {
                    "type": "text",
                    "text": "You are OwlCoda runtime test system.",
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 4,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    text = payload["content"][0]["text"]
    assert "system: You are OwlCoda runtime test system." in text
    assert "cache_control" not in text


def test_anthropic_messages_stream_provides_sse_events() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    with client.stream(
        "POST",
        "/v1/messages",
        json={
            "model": "fake-a",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 4,
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        chunks = [line for line in response.iter_lines() if line]

    assert "event: message_start" in chunks
    assert "event: content_block_start" in chunks
    assert "event: content_block_delta" in chunks
    assert "event: message_stop" in chunks


def test_anthropic_messages_missing_model_returns_error_shape() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.post(
        "/v1/messages",
        json={
            "model": "missing",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 4,
        },
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["type"] == "error"
    assert payload["error"]["type"] == "model_not_loaded"


def test_anthropic_count_tokens_returns_estimate() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.post(
        "/v1/messages/count_tokens",
        json={
            "messages": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": [{"type": "text", "text": "world"}]},
            ],
            "system": "be terse",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["input_tokens"] >= 1


def test_anthropic_messages_accept_tool_result_blocks() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-a",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "run ls"},
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_123",
                            "content": [{"type": "text", "text": "file-a\\nfile-b"}],
                        },
                    ],
                }
            ],
            "max_tokens": 4,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    text = payload["content"][0]["text"]
    assert "run ls" in text
    assert "[tool_result:toolu_123] file-a" in text


def test_anthropic_messages_accept_assistant_tool_use_blocks() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-a",
            "messages": [
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_abc",
                            "name": "read_file",
                            "input": {"path": "README.md"},
                        }
                    ],
                }
            ],
            "max_tokens": 4,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    text = payload["content"][0]["text"]
    assert "[tool_use:toolu_abc] read_file" in text


def test_anthropic_messages_non_stream_can_return_tool_use_blocks() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-a",
            "messages": [{"role": "user", "content": "[force_tool_use] inspect files"}],
            "max_tokens": 4,
            "tools": [
                {
                    "name": "read_file",
                    "description": "Read a file",
                    "input_schema": {"type": "object"},
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["stop_reason"] == "tool_use"
    assert payload["content"][0]["type"] == "tool_use"
    assert payload["content"][0]["name"] == "read_file"
    assert payload["content"][0]["id"] == "toolu_fake_001"


def test_anthropic_messages_stream_can_return_tool_use_events() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    with client.stream(
        "POST",
        "/v1/messages",
        json={
            "model": "fake-a",
            "messages": [{"role": "user", "content": "[force_tool_use] inspect files"}],
            "max_tokens": 4,
            "stream": True,
            "tools": [
                {
                    "name": "read_file",
                    "description": "Read a file",
                    "input_schema": {"type": "object"},
                }
            ],
        },
    ) as response:
        assert response.status_code == 200
        chunks = [line for line in response.iter_lines() if line]

    assert "event: message_start" in chunks
    assert "event: content_block_start" in chunks
    assert any('"type": "tool_use"' in line or '"type":"tool_use"' in line for line in chunks)
    assert any('"type": "input_json_delta"' in line or '"type":"input_json_delta"' in line for line in chunks)
    assert any('"stop_reason": "tool_use"' in line or '"stop_reason":"tool_use"' in line for line in chunks)


def test_anthropic_messages_with_tools_do_not_force_tool_use_by_default() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-a",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 4,
            "tools": [
                {
                    "name": "Sleep",
                    "description": "Sleep briefly",
                    "input_schema": {"type": "object"},
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["stop_reason"] == "end_turn"
    assert payload["content"][0]["type"] == "text"


def test_anthropic_messages_with_tool_result_then_returns_final_text() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-a",
            "messages": [
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_fake_001",
                            "name": "read_file",
                            "input": {"path": "README.md"},
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_fake_001",
                            "content": "README contents",
                        }
                    ],
                },
            ],
            "max_tokens": 4,
            "tools": [
                {
                    "name": "read_file",
                    "description": "Read a file",
                    "input_schema": {"type": "object"},
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["stop_reason"] == "end_turn"
    assert payload["content"][0]["type"] == "text"
    assert "[tool_result:toolu_fake_001] README contents" in payload["content"][0]["text"]


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
