"""Tests for post-load Metal JIT warmup — Campaign 3.

Verifies that RuntimeKernel.load_model(post_load_warmup=True) triggers one
warmup generate and that the HTTP /v1/load route enables warmup by default.
The warmup fires backend.stream_generate so Metal shaders are compiled before
the first real user request, eliminating cold-start TTFT spikes.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app


# ---------------------------------------------------------------------------
# Helper: FakeBackend that counts stream_generate calls
# ---------------------------------------------------------------------------

class _CountingBackend(FakeBackend):
    def __init__(self) -> None:
        super().__init__()
        self.stream_calls: list[str] = []  # model_id per call

    def stream_generate(self, model_id: str, prompt: str, **kwargs):
        self.stream_calls.append(model_id)
        return super().stream_generate(model_id, prompt, **kwargs)


# ---------------------------------------------------------------------------
# Unit tests — RuntimeKernel direct
# ---------------------------------------------------------------------------

def test_warmup_disabled_by_default_in_kernel():
    """Direct kernel.load_model() does NOT call stream_generate (safe default)."""
    backend = _CountingBackend()
    kernel = RuntimeKernel(backend)
    result = kernel.load_model("m", memory_gb=1.0)
    assert result.ok
    assert backend.stream_calls == []


def test_warmup_enabled_calls_stream_generate_once():
    """post_load_warmup=True fires exactly one stream_generate call."""
    backend = _CountingBackend()
    kernel = RuntimeKernel(backend)
    result = kernel.load_model("m", memory_gb=1.0, post_load_warmup=True)
    assert result.ok
    assert backend.stream_calls == ["m"]


def test_warmup_status_dict_has_log_entry():
    """After warmup, status_dict["post_load_warmup"]["log"] has one entry."""
    kernel = RuntimeKernel(FakeBackend())
    kernel.load_model("m", memory_gb=1.0, post_load_warmup=True)
    d = kernel.status_dict()
    warmup_section = d["post_load_warmup"]
    assert warmup_section["total_warmup_count"] == 1
    assert len(warmup_section["log"]) == 1
    entry = warmup_section["log"][0]
    assert entry["model_id"] == "m"
    assert entry["ok"] is True
    assert isinstance(entry["warmup_ms"], float)


def test_warmup_disabled_no_log_entry():
    """No warmup → post_load_warmup log is empty."""
    kernel = RuntimeKernel(FakeBackend())
    kernel.load_model("m", memory_gb=1.0, post_load_warmup=False)
    d = kernel.status_dict()
    assert d["post_load_warmup"]["total_warmup_count"] == 0
    assert d["post_load_warmup"]["log"] == []


def test_warmup_model_starts_hot_after_warmup():
    """Warmup records a use → model residency state is 'hot' immediately after load."""
    kernel = RuntimeKernel(FakeBackend())
    kernel.load_model("m", memory_gb=1.0, post_load_warmup=True)
    d = kernel.status_dict()
    entry = d["cache_residency"]["entries"]["m"]
    assert entry["state"] == "hot"
    assert entry["use_count"] == 1


def test_warmup_without_warmup_model_starts_resident():
    """Without warmup, residency state is 'resident' (no use recorded)."""
    kernel = RuntimeKernel(FakeBackend())
    kernel.load_model("m", memory_gb=1.0, post_load_warmup=False)
    d = kernel.status_dict()
    entry = d["cache_residency"]["entries"]["m"]
    assert entry["state"] == "resident"
    assert entry["use_count"] == 0


def test_warmup_failure_does_not_fail_load():
    """A backend that raises during stream_generate must not fail the load."""

    class _BrokenStreamBackend(FakeBackend):
        def stream_generate(self, model_id, prompt, **kwargs):
            raise RuntimeError("metal oom during warmup")

    kernel = RuntimeKernel(_BrokenStreamBackend())
    result = kernel.load_model("m", memory_gb=1.0, post_load_warmup=True)
    assert result.ok  # load still succeeded
    d = kernel.status_dict()
    log = d["post_load_warmup"]["log"]
    assert len(log) == 1
    assert log[0]["ok"] is False
    assert "metal oom during warmup" in log[0]["error"]


def test_warmup_repeated_loads_accumulate_log():
    """Multiple load+unload+reload cycles accumulate warmup log entries."""
    kernel = RuntimeKernel(FakeBackend())
    for _ in range(3):
        kernel.load_model("m", memory_gb=1.0, post_load_warmup=True)
        kernel.unload_model("m")
    d = kernel.status_dict()
    assert d["post_load_warmup"]["total_warmup_count"] == 3


# ---------------------------------------------------------------------------
# Integration tests — HTTP route (warmup=True by default)
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    kernel = RuntimeKernel(_CountingBackend())
    app = create_app(kernel)
    return TestClient(app), kernel


def test_http_load_warmup_enabled_by_default(client):
    """POST /v1/load without warmup field → warmup=True → stream_generate called."""
    tc, kernel = client
    resp = tc.post("/v1/load", json={"model_id": "m", "memory_gb": 1.0})
    assert resp.status_code == 200
    d = kernel.status_dict()
    assert d["post_load_warmup"]["total_warmup_count"] == 1


def test_http_load_warmup_can_be_disabled(client):
    """POST /v1/load with warmup=false → no warmup generate."""
    tc, kernel = client
    resp = tc.post("/v1/load", json={"model_id": "m", "memory_gb": 1.0, "warmup": False})
    assert resp.status_code == 200
    d = kernel.status_dict()
    assert d["post_load_warmup"]["total_warmup_count"] == 0


def test_http_load_warmup_model_is_hot_for_first_user_request(client):
    """After HTTP load (warmup default), model is 'hot' — ready for first request."""
    tc, kernel = client
    tc.post("/v1/load", json={"model_id": "m", "memory_gb": 1.0})
    d = kernel.status_dict()
    entry = d["cache_residency"]["entries"]["m"]
    assert entry["state"] == "hot"
