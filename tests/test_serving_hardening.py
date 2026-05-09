"""Tests for the serving-hardening scaffold primitives.

These tests cover the middleware, async helpers, and response shapes
defined by ``owlmlx/runtime/serving_hardening.py``. They do NOT
construct a real FastAPI app, do NOT import
``owlmlx.runtime.server``, and do NOT make real HTTP requests against
a running server. Where middleware behavior must be verified, a
minimal Starlette app is constructed inside the individual test.

The scaffold's async helpers are exercised through ``asyncio.run`` —
the project's test suite does not declare a ``pytest-asyncio`` plugin
in ``pyproject.toml``, so the sync-only pattern is the supported
shape here.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from owlmlx.runtime.serving_hardening import (
    REQUEST_ID_HEADER,
    ErrorEnvelopeBuilder,
    GracefulShutdown,
    GracefulShutdownConfig,
    IdempotentLoadHelper,
    MetricsSnapshotExporter,
    RequestDisconnectedError,
    RequestIdContext,
    RequestIdMiddleware,
    RequestTimeoutHelper,
    RequestTimeoutPolicy,
    UnifiedErrorEnvelope,
    derive_request_id_context,
)


# ---------------------------------------------------------------------------
# 1. Request-id middleware
# ---------------------------------------------------------------------------


def _build_request_id_app() -> Starlette:
    """Minimal Starlette app: echoes the resolved request id from state."""

    async def echo_request_id(request: Request) -> Response:
        # Echo whatever the middleware attached, plus inbound flag.
        ctx: RequestIdContext = request.state.request_id_context
        return PlainTextResponse(
            content=f"id={ctx.request_id};inbound={ctx.inbound}",
            headers={"x-echo-id": request.state.request_id},
        )

    app = Starlette(routes=[Route("/echo", endpoint=echo_request_id)])
    app.add_middleware(RequestIdMiddleware)
    return app


def test_request_id_middleware_generates_id_when_inbound_absent() -> None:
    app = _build_request_id_app()
    with TestClient(app) as client:
        response = client.get("/echo")
    assert response.status_code == 200
    body = response.text
    assert "inbound=False" in body
    # Generated id has the documented prefix + 32-char uuid hex.
    assert body.startswith("id=req_")
    assert REQUEST_ID_HEADER in response.headers
    out_id = response.headers[REQUEST_ID_HEADER]
    assert out_id.startswith("req_") and len(out_id) == len("req_") + 32


def test_request_id_middleware_propagates_inbound_id_unchanged() -> None:
    app = _build_request_id_app()
    inbound_id = "caller-supplied-12345"
    with TestClient(app) as client:
        response = client.get("/echo", headers={REQUEST_ID_HEADER: inbound_id})
    assert response.status_code == 200
    assert f"id={inbound_id}" in response.text
    assert "inbound=True" in response.text
    assert response.headers[REQUEST_ID_HEADER] == inbound_id


def test_request_id_middleware_attaches_to_request_state() -> None:
    captured: dict[str, Any] = {}

    async def capture(request: Request) -> Response:
        captured["request_id"] = request.state.request_id
        captured["context"] = request.state.request_id_context
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/cap", endpoint=capture)])
    app.add_middleware(RequestIdMiddleware)
    with TestClient(app) as client:
        client.get("/cap", headers={REQUEST_ID_HEADER: "abc"})
    assert captured["request_id"] == "abc"
    ctx = captured["context"]
    assert isinstance(ctx, RequestIdContext)
    assert ctx.request_id == "abc"
    assert ctx.inbound is True
    assert ctx.to_dict() == {"request_id": "abc", "inbound": True}


def test_request_id_middleware_writes_outbound_header() -> None:
    """Outbound responses must always carry x-request-id."""

    app = _build_request_id_app()
    with TestClient(app) as client:
        # No inbound id: middleware should still write outbound.
        response = client.get("/echo")
    assert REQUEST_ID_HEADER in response.headers


def test_derive_request_id_context_handles_blank_inbound() -> None:
    """Empty/whitespace inbound id is treated as absent."""

    ctx_none = derive_request_id_context(None)
    ctx_blank = derive_request_id_context("   ")
    assert ctx_none.inbound is False
    assert ctx_blank.inbound is False
    assert ctx_none.request_id != ctx_blank.request_id  # uuid uniqueness
    ctx_real = derive_request_id_context("real-id")
    assert ctx_real == RequestIdContext(request_id="real-id", inbound=True)


# ---------------------------------------------------------------------------
# 2. Per-request timeout + client-disconnect detection
# ---------------------------------------------------------------------------


def test_request_timeout_helper_raises_on_timeout() -> None:
    helper = RequestTimeoutHelper(policy=RequestTimeoutPolicy(default_timeout_s=0.05))

    async def slow() -> None:
        await asyncio.sleep(1.0)

    async def runner() -> None:
        await helper.await_with_timeout(slow(), timeout_s=0.05)

    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(runner())


def test_request_timeout_helper_returns_value_when_under_timeout() -> None:
    helper = RequestTimeoutHelper()

    async def fast() -> str:
        await asyncio.sleep(0.01)
        return "fast-result"

    async def runner() -> str:
        return await helper.await_with_timeout(fast(), timeout_s=1.0)

    assert asyncio.run(runner()) == "fast-result"


def test_poll_disconnect_yields_until_disconnect_then_raises() -> None:
    """Async generator yields while connected, then raises on disconnect."""

    class FakeRequest:
        def __init__(self) -> None:
            self._calls = 0
            self.disconnected = False

        async def is_disconnected(self) -> bool:
            self._calls += 1
            return self.disconnected

    fake = FakeRequest()
    helper = RequestTimeoutHelper(
        policy=RequestTimeoutPolicy(disconnect_check_interval_s=0.001)
    )
    yields_observed = 0

    async def runner() -> None:
        nonlocal yields_observed
        async for _ in helper.poll_disconnect(fake, interval_s=0.001):  # type: ignore[arg-type]
            yields_observed += 1
            if yields_observed >= 2:
                fake.disconnected = True
            if yields_observed > 10:  # safety cap
                break

    with pytest.raises(RequestDisconnectedError):
        asyncio.run(runner())
    assert yields_observed >= 2


# ---------------------------------------------------------------------------
# 3. Graceful shutdown
# ---------------------------------------------------------------------------


def test_graceful_shutdown_drain_gate_returns_immediately_when_idle() -> None:
    shutdown = GracefulShutdown(
        config=GracefulShutdownConfig(gate_idle_timeout_s=1.0, poll_interval_s=0.01)
    )

    def gate_status() -> dict[str, Any]:
        return {"is_active": False, "waiters": 0}

    async def runner() -> dict[str, Any]:
        return await shutdown.drain_gate(gate_status_callable=gate_status)

    report = asyncio.run(runner())
    assert report["drained"] is True
    assert report["polls"] == 1
    assert report["final_status"] == {"is_active": False, "waiters": 0}
    assert report["timeout_s"] == 1.0


def test_graceful_shutdown_drain_gate_polls_until_idle() -> None:
    """Status callable transitions from active to idle after 2 polls."""

    state = {"calls": 0}

    def gate_status() -> dict[str, Any]:
        state["calls"] += 1
        return {"is_active": state["calls"] < 3, "waiters": 0}

    shutdown = GracefulShutdown(
        config=GracefulShutdownConfig(gate_idle_timeout_s=2.0, poll_interval_s=0.01)
    )

    async def runner() -> dict[str, Any]:
        return await shutdown.drain_gate(gate_status_callable=gate_status)

    report = asyncio.run(runner())
    assert report["drained"] is True
    # Polls should be 3: active, active, then idle.
    assert report["polls"] == 3


def test_graceful_shutdown_drain_gate_times_out_after_config_seconds() -> None:
    def gate_status() -> dict[str, Any]:
        return {"is_active": True, "waiters": 1}

    shutdown = GracefulShutdown(
        config=GracefulShutdownConfig(gate_idle_timeout_s=0.05, poll_interval_s=0.01)
    )

    async def runner() -> dict[str, Any]:
        return await shutdown.drain_gate(gate_status_callable=gate_status)

    report = asyncio.run(runner())
    assert report["drained"] is False
    assert report["final_status"]["is_active"] is True
    # At least one poll happened, but we did not run forever.
    assert report["elapsed_s"] >= 0.0
    assert report["timeout_s"] == 0.05


def test_graceful_shutdown_on_shutdown_orchestrates_drain_then_unload() -> None:
    """on_shutdown calls unload only after drain returns."""

    drain_call_order: list[str] = []

    def gate_status() -> dict[str, Any]:
        drain_call_order.append("status")
        return {"is_active": False}

    def unload() -> dict[str, Any]:
        drain_call_order.append("unload")
        return {"unloaded_models": ["m1"]}

    shutdown = GracefulShutdown(
        config=GracefulShutdownConfig(gate_idle_timeout_s=0.5, poll_interval_s=0.01)
    )

    async def runner() -> dict[str, Any]:
        return await shutdown.on_shutdown(
            gate_status_callable=gate_status,
            unload_models_callable=unload,
        )

    report = asyncio.run(runner())
    assert report["drain"]["drained"] is True
    assert report["unload"] == {"unloaded_models": ["m1"]}
    # Drain status read must happen at least once before unload.
    assert drain_call_order[0] == "status"
    assert "unload" in drain_call_order
    assert drain_call_order.index("unload") > drain_call_order.index("status")


# ---------------------------------------------------------------------------
# 4. Unified error envelope
# ---------------------------------------------------------------------------


def test_unified_error_envelope_to_response_body_shape() -> None:
    envelope = UnifiedErrorEnvelope(
        id="err_abc_1",
        error_code="invalid_request",
        message="bad input",
        request_id="req_caller",
        http_status=400,
    )
    body = envelope.to_response_body()
    assert body == {
        "id": "err_abc_1",
        "object": "error",
        "error_code": "invalid_request",
        "message": "bad input",
        "request_id": "req_caller",
        "http_status": 400,
    }


def test_error_envelope_from_runtime_error_code_carries_request_id() -> None:
    builder = ErrorEnvelopeBuilder(namespace="owlmlx_native")
    envelope = builder.from_runtime_error_code(
        error_code="model_not_loaded",
        message="model is not loaded",
        request_id="req_caller_1",
    )
    assert envelope.error_code == "model_not_loaded"
    assert envelope.request_id == "req_caller_1"
    assert envelope.http_status == 409
    assert envelope.message == "model is not loaded"
    assert envelope.id.startswith("err_owlmlx_native_")
    body = envelope.to_response_body()
    assert body["request_id"] == "req_caller_1"
    assert body["http_status"] == 409


def test_error_envelope_from_runtime_error_code_unknown_defaults_to_500() -> None:
    builder = ErrorEnvelopeBuilder()
    envelope = builder.from_runtime_error_code(
        error_code="some_brand_new_code",
        message="not in scaffold table",
        request_id=None,
    )
    assert envelope.http_status == 500
    assert envelope.error_code == "some_brand_new_code"


def test_error_envelope_from_unexpected_does_not_leak_exception_class() -> None:
    builder = ErrorEnvelopeBuilder()

    class _SecretInternalError(Exception):
        """A class name that should never appear in a response body."""

    exc = _SecretInternalError("a leaky-looking secret message")
    envelope = builder.from_unexpected(exc, request_id="req_caller_x")
    body = envelope.to_response_body()
    serialized = repr(body) + envelope.to_json()
    assert "_SecretInternalError" not in serialized
    assert "leaky-looking secret message" not in serialized
    assert envelope.error_code == "unexpected_error"
    assert envelope.http_status == 500
    assert envelope.message == "unexpected internal error"
    assert envelope.request_id == "req_caller_x"


# ---------------------------------------------------------------------------
# 5. Prometheus metrics exporter
# ---------------------------------------------------------------------------


def test_metrics_snapshot_renders_prometheus_text_with_type_help_lines() -> None:
    exporter = MetricsSnapshotExporter(namespace="owlmlx_native")
    gate_status = {
        "is_active": False,
        "waiters": 2,
        "total_served": 17,
        "total_queued": 4,
        "longest_wait_s": 1.234,
        "longest_exec_s": 8.5,
    }
    text = exporter.render_prometheus_text(
        gate_status=gate_status, native_admission_snapshot=None
    )
    # Each metric block must have HELP, TYPE, and value lines.
    assert "# HELP owlmlx_native_waiters " in text
    assert "# TYPE owlmlx_native_waiters gauge" in text
    assert "owlmlx_native_waiters 2" in text
    # Counters carry _total suffix per Prometheus convention.
    assert "# TYPE owlmlx_native_total_served_total counter" in text
    assert "owlmlx_native_total_served_total 17" in text
    assert "# TYPE owlmlx_native_total_queued_total counter" in text
    assert "owlmlx_native_total_queued_total 4" in text
    assert "owlmlx_native_longest_wait_seconds 1.234" in text
    assert "owlmlx_native_longest_exec_seconds 8.5" in text


def test_metrics_snapshot_includes_native_admission_when_provided() -> None:
    exporter = MetricsSnapshotExporter()
    gate_status = {"waiters": 0, "total_served": 0, "total_queued": 0}
    native = {
        "next_ticket": 5,
        "serving": 3,
        "in_critical_section": 1,
        "max_observed_concurrency": 1,
    }
    text = exporter.render_prometheus_text(
        gate_status=gate_status, native_admission_snapshot=native
    )
    assert "owlmlx_native_native_max_observed_concurrency 1" in text
    assert "owlmlx_native_native_in_critical_section 1" in text
    assert "owlmlx_native_native_serving_ticket 3" in text


def test_metrics_snapshot_omits_native_admission_when_none() -> None:
    exporter = MetricsSnapshotExporter()
    gate_status = {"waiters": 0, "total_served": 0, "total_queued": 0}
    text = exporter.render_prometheus_text(
        gate_status=gate_status, native_admission_snapshot=None
    )
    assert "owlmlx_native_native_max_observed_concurrency" not in text
    assert "owlmlx_native_native_in_critical_section" not in text
    assert "owlmlx_native_native_serving_ticket" not in text


def test_metrics_snapshot_omits_metrics_when_source_field_missing() -> None:
    """Missing input field -> metric is omitted, not zeroed out."""

    exporter = MetricsSnapshotExporter()
    text = exporter.render_prometheus_text(
        gate_status={"waiters": 1},  # no total_served / total_queued
        native_admission_snapshot=None,
    )
    assert "owlmlx_native_waiters 1" in text
    assert "owlmlx_native_total_served_total" not in text
    assert "owlmlx_native_total_queued_total" not in text


# ---------------------------------------------------------------------------
# 6. Idempotent /v1/load helper
# ---------------------------------------------------------------------------


def test_idempotent_load_helper_recognizes_model_already_loaded_as_success() -> None:
    helper = IdempotentLoadHelper()
    backend_dict = {
        "ok": False,
        "error_code": "model_already_loaded",
        "model_id": "Qwen3.6-35B-A3B",
        "memory_gb": 67.0,
        "detail": {"reason": "model_already_loaded"},
    }
    outcome = helper.interpret_backend_result(backend_result_dict=backend_dict)
    assert outcome.ok is True
    assert outcome.already_loaded is True
    assert outcome.model_id == "Qwen3.6-35B-A3B"
    assert outcome.memory_gb == 67.0
    body = outcome.to_response_body()
    assert body["ok"] is True
    assert body["already_loaded"] is True


def test_idempotent_load_helper_passes_through_genuine_failures() -> None:
    helper = IdempotentLoadHelper()
    backend_dict = {
        "ok": False,
        "error_code": "backend_error",
        "model_id": "broken-model",
        "memory_gb": 0.0,
        "detail": {"reason": "load_failed"},
    }
    outcome = helper.interpret_backend_result(backend_result_dict=backend_dict)
    assert outcome.ok is False
    assert outcome.already_loaded is False
    assert outcome.model_id == "broken-model"


def test_idempotent_load_helper_passes_through_success_unchanged() -> None:
    helper = IdempotentLoadHelper()
    backend_dict = {
        "ok": True,
        "error_code": None,
        "model_id": "ok-model",
        "memory_gb": 8.5,
        "detail": {},
    }
    outcome = helper.interpret_backend_result(backend_result_dict=backend_dict)
    assert outcome.ok is True
    assert outcome.already_loaded is False
    assert outcome.memory_gb == 8.5
