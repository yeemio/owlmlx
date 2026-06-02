"""Focused tests for OpenAI/Anthropic compat route registration."""

from __future__ import annotations

from fastapi.testclient import TestClient

from owlmlx.runtime.backends import FakeBackend
from owlmlx.runtime.kernel import RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.runtime.types import GenerateResult


def _client_with_loaded_fake_model() -> TestClient:
    kernel = RuntimeKernel(FakeBackend())
    loaded = kernel.load_model("fake-model")
    assert loaded.ok is True
    return TestClient(create_app(kernel))


def test_openai_chat_completion_stream_sse_shape() -> None:
    client = _client_with_loaded_fake_model()

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"object": "chat.completion.chunk"' in response.text
    assert "data: [DONE]" in response.text


def test_openai_completion_stream_sse_shape() -> None:
    client = _client_with_loaded_fake_model()

    response = client.post(
        "/v1/completions",
        json={"model": "fake-model", "prompt": "hello", "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"object": "text_completion"' in response.text
    assert "data: [DONE]" in response.text


def test_anthropic_messages_stream_sse_shape() -> None:
    client = _client_with_loaded_fake_model()

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 8,
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: message_start" in response.text
    assert "event: content_block_delta" in response.text
    assert "event: message_stop" in response.text


# --- F-4 #1b: grammar through the OpenAI surface (response_format) ------------


def test_grammar_from_openai_payload_parses_response_format_json_schema() -> None:
    from owlmlx.runtime.server_routes_openai import (
        ChatCompletionRequest,
        _grammar_from_openai_payload,
    )

    schema = {"type": "object", "properties": {"x": {"type": "string"}}}
    payload = ChatCompletionRequest(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
        response_format={"type": "json_schema", "json_schema": {"schema": schema}},
    )
    spec = _grammar_from_openai_payload(payload)
    assert spec == {"kind": "json_schema", "schema": schema}


def test_grammar_from_openai_payload_parses_extra_body_grammar() -> None:
    from owlmlx.runtime.server_routes_openai import (
        ChatCompletionRequest,
        _grammar_from_openai_payload,
    )

    grammar = {"kind": "json_schema", "schema": {"type": "object"}}
    payload = ChatCompletionRequest(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
        extra_body={"grammar": grammar},
    )
    assert _grammar_from_openai_payload(payload) == grammar


def test_grammar_from_openai_payload_none_when_absent() -> None:
    from owlmlx.runtime.server_routes_openai import (
        ChatCompletionRequest,
        _grammar_from_openai_payload,
    )

    payload = ChatCompletionRequest(
        model="m", messages=[{"role": "user", "content": "hi"}]
    )
    assert _grammar_from_openai_payload(payload) is None


def test_openai_chat_completion_forwards_grammar_to_backend() -> None:
    from owlmlx.runtime.backends import FakeBackend
    from owlmlx.runtime.kernel import RuntimeKernel
    from owlmlx.runtime.server import create_app

    captured: dict = {}

    class _CapturingBackend(FakeBackend):
        def generate_messages(self, model_id, messages, **kwargs):  # type: ignore[no-untyped-def]
            captured["kwargs"] = dict(kwargs)
            return super().generate_messages(model_id, messages, **kwargs)

    kernel = RuntimeKernel(_CapturingBackend())
    assert kernel.load_model("fake-model").ok is True
    client = TestClient(create_app(kernel))

    schema = {"type": "object", "properties": {"x": {"type": "string"}}}
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "hello"}],
            "response_format": {"type": "json_schema", "json_schema": {"schema": schema}},
        },
    )
    assert response.status_code == 200
    assert captured["kwargs"].get("grammar") == {"kind": "json_schema", "schema": schema}


def test_openai_chat_completion_auto_loads_visible_cold_model(tmp_path) -> None:
    model_id = "Qwen3.6-27B"
    model_dir = tmp_path / model_id
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    (model_dir / "weights.safetensors").write_bytes(b"x" * 16)
    kernel = RuntimeKernel(FakeBackend())
    client = TestClient(create_app(kernel, visibility_models_root=str(tmp_path)))

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": model_id,
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 4,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["choices"][0]["message"]["content"]
    assert kernel.active_model_id == model_id


def test_openai_chat_completion_accepts_tool_history_shape_without_422() -> None:
    client = _client_with_loaded_fake_model()

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [
                {"role": "user", "content": "List this directory."},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "Read",
                                "arguments": "{\"path\":\"/tmp\"}",
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "call_1",
                    "content": "Error: /tmp is a directory, not a file",
                },
            ],
            "max_tokens": 4,
        },
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["role"] == "assistant"


def test_openai_chat_completion_forwards_tools_tool_choice_and_top_p_to_backend() -> None:
    captured: dict[str, object] = {}

    class _CapturingBackend(FakeBackend):
        def generate_messages(self, model_id, messages, **kwargs):  # type: ignore[no-untyped-def]
            captured["kwargs"] = dict(kwargs)
            captured["messages"] = list(messages)
            return super().generate_messages(model_id, messages, **kwargs)

    kernel = RuntimeKernel(_CapturingBackend())
    assert kernel.load_model("fake-model").ok is True
    client = TestClient(create_app(kernel))

    tools = [
        {
            "type": "function",
            "function": {
                "name": "Bash",
                "description": "Run shell commands",
                "parameters": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
            },
        }
    ]
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "Use Bash to run pwd"}],
            "tools": tools,
            "tool_choice": "auto",
            "top_p": 0.9,
        },
    )

    assert response.status_code == 200
    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["tools"] == tools
    assert kwargs["tool_choice"] == "auto"
    assert kwargs["top_p"] == 0.9


def test_openai_chat_completion_returns_openai_tool_calls_from_backend_detail() -> None:
    class _ToolCallBackend(FakeBackend):
        def generate_messages(self, model_id, messages, **kwargs):  # type: ignore[no-untyped-def]
            return GenerateResult(
                ok=True,
                message="generated tool calls",
                model_id=model_id,
                text="",
                finish_reason="tool_calls",
                detail={
                    "tool_calls": [
                        {
                            "id": "call_test",
                            "type": "function",
                            "function": {
                                "name": "Bash",
                                "arguments": "{\"command\":\"pwd\"}",
                            },
                        }
                    ]
                },
            )

    kernel = RuntimeKernel(_ToolCallBackend())
    assert kernel.load_model("fake-model").ok is True
    client = TestClient(create_app(kernel))

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "Use Bash to run pwd"}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "Bash",
                        "parameters": {"type": "object"},
                    },
                }
            ],
        },
    )

    assert response.status_code == 200
    choice = response.json()["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert choice["message"]["content"] is None
    assert choice["message"]["tool_calls"][0]["id"] == "call_test"
    assert choice["message"]["tool_calls"][0]["function"]["name"] == "Bash"


def test_openai_chat_completion_converts_backend_tool_uses_to_tool_calls() -> None:
    client = _client_with_loaded_fake_model()

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "Use Bash to run pwd"}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "Bash",
                        "parameters": {"type": "object"},
                    },
                }
            ],
            "tool_choice": "auto",
        },
    )

    assert response.status_code == 200
    choice = response.json()["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert choice["message"]["tool_calls"][0]["id"].startswith("call_")
    assert choice["message"]["tool_calls"][0]["function"]["name"] == "Bash"


def test_openai_chat_completion_stream_buffers_tool_generation_into_single_delta() -> None:
    class _StreamToolBackend(FakeBackend):
        def generate_messages(self, model_id, messages, **kwargs):  # type: ignore[no-untyped-def]
            return GenerateResult(
                ok=True,
                message="generated tool calls",
                model_id=model_id,
                finish_reason="tool_calls",
                detail={
                    "tool_calls": [
                        {
                            "id": "call_stream",
                            "type": "function",
                            "function": {
                                "name": "Bash",
                                "arguments": "{\"command\":\"pwd\"}",
                            },
                        }
                    ]
                },
            )

        def stream_generate_messages(self, model_id, messages, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("tool streaming must use buffered non-stream generation")

    kernel = RuntimeKernel(_StreamToolBackend())
    assert kernel.load_model("fake-model").ok is True
    client = TestClient(create_app(kernel))

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "Use Bash to run pwd"}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "Bash",
                        "parameters": {"type": "object"},
                    },
                }
            ],
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert '"finish_reason": "tool_calls"' in response.text
    assert '"tool_calls": [{"index": 0, "id": "call_stream"' in response.text


def test_openai_reasoning_policy_defaults_to_profile_declared_trace_policy() -> None:
    from owlmlx.model_profile import resolve_model_profile
    from owlmlx.runtime.server_routes_openai import (
        ChatCompletionRequest,
        _openai_reasoning_trace_policy,
    )

    payload = ChatCompletionRequest(
        model="Qwen3.6-35B-A3B",
        messages=[{"role": "user", "content": "hi"}],
    )

    assert _openai_reasoning_trace_policy(
        payload,
        profile=resolve_model_profile("Qwen3.6-35B-A3B"),
    ) == "final_answer_content"
