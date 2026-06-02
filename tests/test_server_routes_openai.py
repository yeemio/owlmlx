"""Focused tests for OpenAI/Anthropic compat route registration."""

from __future__ import annotations

from fastapi.testclient import TestClient

from owlmlx.runtime.backends import FakeBackend
from owlmlx.runtime.kernel import RuntimeKernel
from owlmlx.runtime.server import create_app


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
