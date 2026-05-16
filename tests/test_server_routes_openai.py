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
