from __future__ import annotations

import json

from fastapi.testclient import TestClient

from owlmlx.context_concurrency import HIGH_CONTEXT_THRESHOLD_TOKENS
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
    assert payload["contract"]["surface"] == "owlmlx.healthz"
    assert payload["contract"]["version"] == "stabilization1"
    assert payload["runtime"] == "owlmlx"
    assert payload["ok"] is True
    assert payload["readiness"] == "degraded"
    assert payload["model_count"] == 0
    assert payload["backend_name"] == "fake"
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


def test_anthropic_messages_stream_missing_model_returns_error_event() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    with client.stream(
        "POST",
        "/v1/messages",
        json={
            "model": "missing",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 4,
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        chunks = [line for line in response.iter_lines() if line]

    assert "event: message_start" in chunks
    assert any(line.startswith("event: error") for line in chunks)
    assert not any(line.startswith("event: message_stop") for line in chunks)


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
    tool_start_index = next(i for i, line in enumerate(chunks) if '"type": "tool_use"' in line or '"type":"tool_use"' in line)
    assert not any(
        '"content_block":{"type":"text","text":""}' in line or '"content_block": {"type": "text", "text": ""}' in line
        for line in chunks[:tool_start_index + 1]
    )


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


def test_anthropic_messages_shell_prompt_prefers_bash_tool_use() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-a",
            "messages": [{"role": "user", "content": "Run the shell command pwd and then reply with exactly: runtime10-tool-ok"}],
            "max_tokens": 16,
            "tools": [
                {
                    "name": "Bash",
                    "description": "Run a bash command",
                    "input_schema": {"type": "object"},
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["stop_reason"] == "tool_use"
    assert payload["content"][0]["name"] == "Bash"
    assert payload["content"][0]["input"]["command"] == "pwd"


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


def test_anthropic_messages_with_tool_result_can_extract_exact_reply() -> None:
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
                            "name": "Bash",
                            "input": {"command": "pwd"},
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_fake_001",
                            "content": "/Users/yeemio",
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": "Reply with exactly: runtime10-tool-ok",
                },
            ],
            "max_tokens": 8,
            "tools": [
                {
                    "name": "Bash",
                    "description": "Run a bash command",
                    "input_schema": {"type": "object"},
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["stop_reason"] == "end_turn"
    assert payload["content"][0]["text"] == "runtime10-tool-ok"


def test_openai_models_lists_visibility_ready_models(tmp_path) -> None:
    (tmp_path / "visible-a").mkdir()
    (tmp_path / "visible-a" / "config.json").write_text("{}")
    client = TestClient(
        create_app(
            RuntimeKernel(FakeBackend(), profile=_profile()),
            visibility_models_root=str(tmp_path),
            visibility_registry=[{"model_id": "visible-a"}],
        )
    )
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get("/v1/openai/models")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    payload = response.json()
    assert payload["object"] == "list"
    assert payload["data"][0]["id"] == "visible-a"


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
    assert payload["contract"]["surface"] == "owlmlx.runtime.status"
    assert payload["contract"]["version"] == "stabilization1"
    assert "summary" in payload
    assert payload["summary"]["runtime"] == "owlmlx"
    assert payload["summary"]["model_count"] == 1
    assert payload["active_model_id"] == "fake-a"
    assert payload["backend"]["backend_name"] == "fake"
    assert payload["inventory"]["model_count"] == 1
    assert payload["health"]["readiness"] == "ready"
    assert payload["restart"]["restartable_models"] == []
    assert payload["restart"]["restart_exhausted_models"] == []
    assert payload["contract"]["diagnostic_sections"] == [
        "backend.detail",
        "governance_observations",
        "governance_policy",
        "generation_gate",
        "reclaim_barrier",
        "load_failure",
    ]
    assert payload["governance_observations"]["transition_count"] == 1
    assert payload["governance_observations"]["active_reassignment_visible"] is False
    assert payload["governance_policy"]["pinning_supported"] is True
    assert payload["governance_policy"]["ttl_supported"] is True
    assert payload["governance_policy"]["ttl_policy_mode"] == "kernel_explicit_sweep"


def test_runtime_orchestration_status_returns_contract_surface() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get("/v1/runtime/orchestration-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == "owlmlx.orchestration_status"
    assert payload["contract"]["version"] == "v1"
    assert payload["summary"]["status"] == "partial"
    assert payload["summary"]["bottleneck_layer"] == "unknown"
    assert payload["layer_assessment"]["generation_gate"]["classification_status"] == "supported"
    assert payload["layer_assessment"]["memory_pressure"]["classification_status"] == "partial"
    assert payload["child_surfaces"]["admission"]["surface"] == "owlmlx.scheduler_admission_contract"
    assert payload["child_surfaces"]["model_residency"]["surface"] == "owlmlx.model_residency_policy"
    assert payload["child_surfaces"]["memory_pressure"]["surface"] == "owlmlx.memory_pressure_contract"
    assert payload["child_surfaces"]["recovery_supervisor"]["surface"] == "owlmlx.recovery_supervisor_contract"
    assert payload["scheduler"]["queue_policy"] == "ticketed_fifo"
    assert payload["scheduler"]["request_context_length"]["classification"] == "unknown"
    assert payload["residency"]["resident_model_count"] == 1
    assert payload["pressure"]["pressure_classification"] == "within_budget"
    assert payload["recovery"]["recovery_state"] == "clean"
    assert payload["recovery"]["restartable_model_count"] == 0


def test_runtime_recovery_supervisor_contract_returns_contract_surface() -> None:
    runtime = RuntimeKernel(FakeBackend(), profile=_profile())
    client = TestClient(create_app(runtime))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.get("/v1/runtime/recovery-supervisor-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == "owlmlx.recovery_supervisor_contract"
    assert payload["summary"]["recovery_state"] == "clean"
    assert payload["summary"]["barrier_decision"] == "no_recovery_barrier"
    assert payload["barrier"]["hard_recovery_barrier"] is False


def test_runtime_request_context_length_truth_returns_contract_surface() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.get(
        "/v1/runtime/request-context-length-truth",
        params={"context_tokens": HIGH_CONTEXT_THRESHOLD_TOKENS + 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["surface"] == "owlmlx.request_context_length_truth"
    assert payload["summary"]["classification"] == "high_context"
    assert payload["source"]["tokenizer_invoked"] is False


def test_runtime_recovery_supervisor_contract_exposes_contaminated_barrier() -> None:
    runtime = RuntimeKernel(FakeBackend(), profile=_profile())
    runtime.abort_recovery.record_abort(
        context_tokens=60000,
        error_type="stream_error",
        now=1000.0,
    )
    runtime.abort_recovery.apply_probe_result(
        passed=False,
        reason="scheduler loop",
        now=1005.0,
    )
    client = TestClient(create_app(runtime))

    response = client.get("/v1/runtime/recovery-supervisor-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["recovery_state"] == "contaminated"
    assert payload["barrier"]["hard_recovery_barrier"] is True
    assert payload["request_impact"]["generation_admissible"] is False


def test_runtime_restart_endpoint_restarts_loaded_model() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
    client.post("/v1/load", json={"model_id": "fake-a", "memory_gb": 2.0})

    response = client.post("/v1/runtime/restart", json={"model_id": "fake-a"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["model_id"] == "fake-a"
    assert payload["stage"] == "completed"
    assert payload["retryable"] is False
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
    assert payload["stage"] == "preflight"
    assert payload["retryable"] is False


def test_comparative_evidence_endpoint_still_blocked_when_ledger_not_connected() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.get("/v1/runtime/comparative-evidence")

    assert response.status_code == 503
    payload = response.json()
    assert payload["surface"] == "owlmlx.comparative_evidence_record"
    assert payload["status"] == "still_blocked"
    assert payload["missing_signal"] == "comparative_evidence_ledger_not_connected"


def test_comparative_evidence_history_endpoint_still_blocked_when_ledger_not_connected() -> None:
    client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))

    response = client.get("/v1/runtime/comparative-evidence/history")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "still_blocked"


def test_comparative_evidence_endpoint_still_blocked_when_ledger_empty(tmp_path) -> None:
    ledger_path = tmp_path / "comparative-evidence-ledger.jsonl"
    client = TestClient(
        create_app(
            RuntimeKernel(FakeBackend(), profile=_profile()),
            comparative_evidence_ledger_path=str(ledger_path),
        )
    )

    response = client.get("/v1/runtime/comparative-evidence")
    assert response.status_code == 503
    assert response.json()["missing_signal"] == "no_comparative_evidence_record_appended"

    history_response = client.get("/v1/runtime/comparative-evidence/history")
    assert history_response.status_code == 503
    assert history_response.json()["missing_signal"] == "no_comparative_evidence_record_appended"


def test_comparative_evidence_endpoint_returns_real_record_when_ledger_seeded(tmp_path) -> None:
    from owlmlx.comparative_evidence_ledger import ComparativeEvidenceLedger
    from owlmlx.comparative_evidence_record import (
        ComparativeEvidenceMeasurement,
        ComparativeEvidenceRuntime,
        build_comparative_evidence_record,
    )

    ledger_path = tmp_path / "comparative-evidence-ledger.jsonl"
    ledger = ComparativeEvidenceLedger(ledger_path)
    ledger.append(
        build_comparative_evidence_record(
            recorded_at="2026-04-26T00:00:00Z",
            evidence_pointer="docs/source-of-truth/comparative-evidence-ledger.md#row-1",
            host_class="darwin-arm64-test-host",
            workload_class="single_prompt_short",
            workload_invariants={
                "model_id": "qwen3-0.6b",
                "model_quantization": "q4",
                "decode_max_tokens": 16,
                "decode_temperature": 0.0,
                "prompt_set_hash": "sha256:test",
                "serving_budget_bytes": 6 * 1024 * 1024 * 1024,
            },
            runtimes=(
                ComparativeEvidenceRuntime(
                    runtime_id="owlmlx",
                    runtime_version="0.0.0-runtime7",
                    measurement=ComparativeEvidenceMeasurement(
                        throughput_tokens_per_second=0.0,
                        first_token_latency_ms=0.0,
                        peak_resident_set_bytes=0,
                        wall_clock_ms=0.0,
                        completed_request_count=0,
                        failure_count=1,
                        failure_causes=("reference_runtime_unavailable",),
                    ),
                ),
                ComparativeEvidenceRuntime(
                    runtime_id="omlx",
                    runtime_version="unavailable",
                    measurement=ComparativeEvidenceMeasurement(
                        throughput_tokens_per_second=0.0,
                        first_token_latency_ms=0.0,
                        peak_resident_set_bytes=0,
                        wall_clock_ms=0.0,
                        completed_request_count=0,
                        failure_count=1,
                        failure_causes=("reference_runtime_unavailable",),
                    ),
                ),
            ),
            verdict_text=(
                "rejected: reference_runtime_unavailable on host_class=darwin-arm64-test-host, "
                "workload_class=single_prompt_short"
            ),
            verdict_grade="rejected",
        )
    )

    client = TestClient(
        create_app(
            RuntimeKernel(FakeBackend(), profile=_profile()),
            comparative_evidence_ledger_path=str(ledger_path),
        )
    )

    latest = client.get("/v1/runtime/comparative-evidence")
    assert latest.status_code == 200
    body = latest.json()
    assert body["surface"] == "owlmlx.comparative_evidence_record"
    assert body["version"] == "v1"
    assert body["host_class"] == "darwin-arm64-test-host"
    assert body["workload_class"] == "single_prompt_short"
    assert body["verdict_grade"] == "rejected"
    assert body["verdict_text"].startswith("rejected:")

    history = client.get("/v1/runtime/comparative-evidence/history")
    assert history.status_code == 200
    history_body = history.json()
    assert history_body["surface"] == "owlmlx.comparative_evidence_record_history"
    assert history_body["version"] == "v1"
    assert history_body["ledger_status"] == "available"
    assert len(history_body["records"]) == 1
    assert history_body["records"][0]["host_class"] == "darwin-arm64-test-host"
