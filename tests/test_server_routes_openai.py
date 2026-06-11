"""Focused tests for OpenAI/Anthropic compat route registration."""

from __future__ import annotations

import json

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


def test_openai_chat_completion_exposes_tool_call_diagnostics_from_backend_detail() -> None:
    class _ToolDiagnosticBackend(FakeBackend):
        def generate_messages(self, model_id, messages, **kwargs):  # type: ignore[no-untyped-def]
            return GenerateResult(
                ok=True,
                message="generated with tool diagnostics",
                model_id=model_id,
                text="plain fallback",
                detail={
                    "tool_parser_missing": True,
                    "template_render_fallback": True,
                    "template_render_error_type": "RuntimeError",
                },
            )

    kernel = RuntimeKernel(_ToolDiagnosticBackend())
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
    diagnostics = response.json()["choices"][0]["message"]["owlmlx_tool_call_diagnostics"]
    assert diagnostics["tool_parser_missing"] is True
    assert diagnostics["template_render_fallback"] is True
    assert diagnostics["template_render_error_type"] == "RuntimeError"


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
                    "tool_parse_dropped": 1,
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
    assert '"owlmlx_tool_call_diagnostics": {"tool_parse_dropped": 1}' in response.text


def test_openai_chat_completion_normal_stream_does_not_duplicate_tool_delta() -> None:
    """A tool call carried on BOTH the tool_use event and the done event must be
    streamed exactly once. The non-buffered ("normal") branch previously emitted
    it twice (once per event), corrupting index-keyed clients."""
    from owlmlx.runtime.types import StreamEvent

    tool_call = {
        "id": "call_dup",
        "type": "function",
        "function": {"name": "Bash", "arguments": "{\"command\": \"pwd\"}"},
    }

    class _DuplicateToolStreamBackend(FakeBackend):
        def stream_generate_messages(self, model_id, messages, **kwargs):  # type: ignore[no-untyped-def]
            return [
                StreamEvent(
                    event="tool_use",
                    model_id=model_id,
                    detail={"tool_calls": [tool_call]},
                ),
                StreamEvent(
                    event="done",
                    model_id=model_id,
                    finish_reason="tool_calls",
                    detail={"tool_calls": [tool_call]},
                ),
            ]

    kernel = RuntimeKernel(_DuplicateToolStreamBackend())
    assert kernel.load_model("fake-model").ok is True
    client = TestClient(create_app(kernel))

    # No `tools` in the request -> the non-buffered ("normal") stream branch.
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fake-model",
            "messages": [{"role": "user", "content": "run pwd"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert response.text.count('"delta": {"tool_calls"') == 1
    assert response.text.count('"id": "call_dup"') == 1
    assert '"finish_reason": "tool_calls"' in response.text


def test_openai_chat_completion_returns_409_when_budget_exceeded_unresolvable(tmp_path) -> None:
    """When a model switch can't fit the budget and nothing is evictable, the
    compat route must return a non-retryable 409 (not the retryable 503 that
    makes OpenAI clients hammer the endpoint)."""
    from owlmlx.memory_budget import MachineMemoryProfile

    model_id = "Qwen3.6-27B"
    model_dir = tmp_path / model_id
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    (model_dir / "weights.safetensors").write_bytes(b"x" * 16)
    # Estimated size is floored at 1.0 GB, which alone exceeds this tiny budget.
    kernel = RuntimeKernel(
        FakeBackend(),
        profile=MachineMemoryProfile(
            system_memory_gb=4.0,
            system_reserve_gb=1.0,
            serving_budget_gb=0.5,
            warning_threshold_gb=0.4,
        ),
    )
    client = TestClient(create_app(kernel, visibility_models_root=str(tmp_path)))

    response = client.post(
        "/v1/chat/completions",
        json={"model": model_id, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 4},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "memory_budget_exceeded"


def test_openai_chat_completion_evicts_non_pinned_resident_to_switch_models(tmp_path) -> None:
    """Switching to a visible cold model that won't fit alongside a non-pinned
    resident must auto-unload the resident and succeed (no manual unload, no
    503 retry storm)."""
    from owlmlx.memory_budget import MachineMemoryProfile

    model_id = "Qwen3.6-27B"
    model_dir = tmp_path / model_id
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    (model_dir / "weights.safetensors").write_bytes(b"x" * 16)  # est 1.0 GB
    kernel = RuntimeKernel(
        FakeBackend(),
        profile=MachineMemoryProfile(
            system_memory_gb=8.0,
            system_reserve_gb=1.0,
            serving_budget_gb=1.5,
            warning_threshold_gb=1.0,
        ),
    )
    # Non-pinned resident occupies most of the budget; 1.0 resident + 1.0 cold
    # = 2.0 > 1.5, so the switch needs the resident evicted.
    assert kernel.load_model("resident-old", memory_gb=1.0).ok is True
    client = TestClient(create_app(kernel, visibility_models_root=str(tmp_path)))

    response = client.post(
        "/v1/chat/completions",
        json={"model": model_id, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 4},
    )

    assert response.status_code == 200
    loaded = {entry.model_id for entry in kernel.backend.status().loaded_models}
    assert model_id in loaded
    assert "resident-old" not in loaded


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


# --- /v1/messages non-stream: real-backend tool-call convention + cleanup -----


def test_anthropic_messages_surfaces_real_backend_tool_calls_convention() -> None:
    """Bug A: the mlx-native backend signals a tool call with
    finish_reason="tool_calls" + detail["tool_calls"] (OpenAI shape). The
    Anthropic /v1/messages route previously gated tool_use blocks on
    finish_reason=="tool_use" + detail["tool_uses"], so real tool calls were
    dropped and returned as raw text. The route must convert the real
    convention into Anthropic tool_use blocks."""

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
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "write",
                                "arguments": "{\"path\":\"a.js\",\"content\":\"x\"}",
                            },
                        }
                    ]
                },
            )

    kernel = RuntimeKernel(_ToolCallBackend())
    assert kernel.load_model("fake-model").ok is True
    client = TestClient(create_app(kernel))

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-model",
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "write a.js"}],
            "tools": [
                {
                    "name": "write",
                    "input_schema": {"type": "object"},
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stop_reason"] == "tool_use"
    tool_blocks = [block for block in body["content"] if block["type"] == "tool_use"]
    assert len(tool_blocks) == 1
    assert tool_blocks[0]["name"] == "write"
    assert tool_blocks[0]["input"] == {"path": "a.js", "content": "x"}
    assert tool_blocks[0]["id"] == "call_1"
    # Empty visible text must NOT produce a stray empty text block.
    assert all(block["type"] != "text" for block in body["content"])


def test_anthropic_messages_preserves_legacy_tool_uses_convention() -> None:
    """Regression: the legacy FakeBackend convention
    (finish_reason="tool_use" + detail["tool_uses"]=[{id,name,input}]) must
    still produce an Anthropic tool_use block."""

    class _LegacyToolUseBackend(FakeBackend):
        def generate_messages(self, model_id, messages, **kwargs):  # type: ignore[no-untyped-def]
            return GenerateResult(
                ok=True,
                message="generated tool use",
                model_id=model_id,
                text="",
                finish_reason="tool_use",
                detail={
                    "tool_uses": [
                        {
                            "id": "toolu_legacy_1",
                            "name": "Bash",
                            "input": {"command": "pwd"},
                        }
                    ]
                },
            )

    kernel = RuntimeKernel(_LegacyToolUseBackend())
    assert kernel.load_model("fake-model").ok is True
    client = TestClient(create_app(kernel))

    response = client.post(
        "/v1/messages",
        json={
            "model": "fake-model",
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "use Bash to run pwd"}],
            "tools": [
                {
                    "name": "Bash",
                    "input_schema": {"type": "object"},
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stop_reason"] == "tool_use"
    tool_blocks = [block for block in body["content"] if block["type"] == "tool_use"]
    assert len(tool_blocks) == 1
    assert tool_blocks[0]["name"] == "Bash"
    assert tool_blocks[0]["input"] == {"command": "pwd"}


def test_anthropic_messages_strips_reasoning_trace_like_openai_route() -> None:
    """Bug B: channel/reasoning markers leaked into /v1/messages text because the
    route returned result.text raw. It must apply the same reasoning-trace policy
    the OpenAI route applies (profile-driven), yielding the same cleaned text."""

    raw_text = "<|channel>thought internal reasoning<channel|>Final visible answer."

    class _ChannelTextBackend(FakeBackend):
        def generate_messages(self, model_id, messages, **kwargs):  # type: ignore[no-untyped-def]
            return GenerateResult(
                ok=True,
                message="generated channel text",
                model_id=model_id,
                text=raw_text,
                finish_reason="stop",
                detail={},
            )

    # A gemma-* id resolves to the gemma4_text profile whose thinking_policy
    # declares parser_cleanup_required -> the reasoning-trace policy applies
    # WITHOUT any per-request opt-in (the Anthropic request has no extra_body).
    model_id = "gemma-4-31B-it"

    kernel = RuntimeKernel(_ChannelTextBackend())
    assert kernel.load_model(model_id).ok is True
    client = TestClient(create_app(kernel))

    anthropic_response = client.post(
        "/v1/messages",
        json={
            "model": model_id,
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "answer please"}],
        },
    )

    assert anthropic_response.status_code == 200
    body = anthropic_response.json()
    assert body["stop_reason"] == "end_turn"
    text_blocks = [block for block in body["content"] if block["type"] == "text"]
    assert len(text_blocks) == 1
    cleaned = text_blocks[0]["text"]
    assert cleaned == "Final visible answer."
    assert "<|channel>" not in cleaned

    # Parity: the OpenAI route returns the same cleaned text for the same output.
    openai_response = client.post(
        "/v1/chat/completions",
        json={
            "model": model_id,
            "messages": [{"role": "user", "content": "answer please"}],
        },
    )
    assert openai_response.status_code == 200
    openai_text = openai_response.json()["choices"][0]["message"]["content"]
    assert openai_text == cleaned


def test_anthropic_messages_stream_strips_reasoning_trace_for_policy_profile() -> None:
    """Bug B (streaming): when the model profile declares the reasoning-trace
    policy, the /v1/messages SSE text deltas must be cleaned (channel markers
    stripped), mirroring how the OpenAI streaming route buffers-then-cleans.
    The cleaned text must equal the non-stream cleaned text for the same output."""
    from owlmlx.runtime.types import StreamEvent

    raw_tokens = [
        "<|channel>thought ",
        "internal reasoning",
        "<channel|>",
        "Final visible answer.",
    ]

    class _ChannelStreamBackend(FakeBackend):
        def stream_generate_messages(self, model_id, messages, **kwargs):  # type: ignore[no-untyped-def]
            events = [
                StreamEvent(
                    event="token",
                    model_id=model_id,
                    text=token,
                    sequence=idx,
                    completion_tokens=idx,
                )
                for idx, token in enumerate(raw_tokens, start=1)
            ]
            events.append(
                StreamEvent(
                    event="done",
                    model_id=model_id,
                    finish_reason="stop",
                    completion_tokens=len(raw_tokens),
                )
            )
            return events

    model_id = "gemma-4-31B-it"
    kernel = RuntimeKernel(_ChannelStreamBackend())
    assert kernel.load_model(model_id).ok is True
    client = TestClient(create_app(kernel))

    response = client.post(
        "/v1/messages",
        json={
            "model": model_id,
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "answer please"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    # The raw channel-open marker must NOT leak into any streamed delta.
    assert "<|channel>" not in response.text
    # Reconstruct the streamed text from text_delta events.
    streamed_chunks: list[str] = []
    for line in response.text.splitlines():
        if line.startswith("data: ") and '"text_delta"' in line:
            payload = json.loads(line[len("data: ") :])
            streamed_chunks.append(payload["delta"]["text"])
    assert "".join(streamed_chunks) == "Final visible answer."
