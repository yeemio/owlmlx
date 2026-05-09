"""Integration tests for D-3 UnifiedErrorEnvelope wiring on the real owlmlx app.

These tests construct the actual owlmlx FastAPI app via
``owlmlx.runtime.server.create_app(...)`` and exercise the wired
``ErrorEnvelopeBuilder`` / ``UnifiedErrorEnvelope`` end-to-end with
``fastapi.testclient.TestClient``. No uvicorn process is spawned and
no model is loaded.

The companion file ``tests/test_serving_hardening.py`` (committed in
the C-4 scaffold round) exercises ``UnifiedErrorEnvelope`` and
``ErrorEnvelopeBuilder`` against synthetic inputs. This file exists to
prove the scaffold is in fact installed on the real owlmlx app after
the D-3 wiring round and that the native lifecycle routes
(``/v1/load``, ``/v1/generate``, ``/v1/unload``) now map typed
``error_code`` values to proper HTTP status codes.

The compat routes (``/v1/chat/completions``, ``/v1/messages``,
``/v1/completions``) keep their existing ``_compat_error_response`` /
``_anthropic_error_response`` shapes — the OpenAI/Anthropic SDK
callers depend on those contracts. The last test in this file is a
guard rail asserting the compat shape is unchanged.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from owlmlx.runtime.server import create_app
from owlmlx.runtime.serving_hardening import (
    REQUEST_ID_HEADER,
    ErrorEnvelopeBuilder,
    UnifiedErrorEnvelope,
)


_UNIFIED_ENVELOPE_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "object",
        "error_code",
        "message",
        "request_id",
        "http_status",
    }
)


def _build_real_owlmlx_app() -> FastAPI:
    """Build the real owlmlx FastAPI app with no optional ledgers wired."""

    return create_app()


def _assert_unified_envelope_shape(body: dict[str, Any]) -> None:
    """The body must match :class:`UnifiedErrorEnvelope.to_response_body`."""

    assert isinstance(body, dict), f"envelope body must be a dict, got {type(body)!r}"
    assert set(body.keys()) == _UNIFIED_ENVELOPE_KEYS, (
        f"envelope keys must be exactly {_UNIFIED_ENVELOPE_KEYS}, got {set(body.keys())}"
    )
    assert body["object"] == "error"
    assert isinstance(body["id"], str) and body["id"].startswith("err_")
    assert isinstance(body["error_code"], str) and body["error_code"]
    assert isinstance(body["message"], str) and body["message"]
    assert isinstance(body["http_status"], int)


def test_load_unknown_model_arg_returns_400_or_appropriate_status() -> None:
    """POST /v1/load with empty model_id triggers pydantic validation.

    The route declares ``model_id: str = Field(min_length=1)`` so
    FastAPI's request validator returns 422 before the route body runs.
    The unified envelope is NOT applied to FastAPI's own validation
    rejection (FastAPI returns its own 422 shape). This test pins
    that behavior so a future round that wants to translate FastAPI
    422 into the unified envelope can do so deliberately.
    """

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        response = client.post(
            "/v1/load",
            json={"model_id": "", "memory_gb": 1.0},
        )
    # FastAPI/pydantic validation returns 422 with its own shape.
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


def test_load_unhealthy_backend_returns_500_with_unified_envelope() -> None:
    """Native /v1/load with backend_error returns HTTP 500 + unified envelope."""

    from owlmlx.runtime.backends import FakeBackend
    from owlmlx.runtime.kernel import RuntimeKernel
    from owlmlx.runtime.server import create_app

    unhealthy_backend = FakeBackend(healthy=False)
    app = create_app(RuntimeKernel(unhealthy_backend))
    with TestClient(app) as client:
        response = client.post(
            "/v1/load",
            json={"model_id": "alpha-model", "memory_gb": 1.0},
        )
    # Unhealthy FakeBackend produces backend_error -> 500.
    assert response.status_code == 500
    body = response.json()
    _assert_unified_envelope_shape(body)
    assert body["error_code"] == "backend_error"
    assert body["http_status"] == 500


def test_generate_unknown_model_returns_404() -> None:
    """POST /v1/generate against a non-loaded model_id -> 404 + unified envelope."""

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        response = client.post(
            "/v1/generate",
            json={"prompt": "hello", "model_id": "model-not-loaded"},
        )
    assert response.status_code == 404
    body = response.json()
    _assert_unified_envelope_shape(body)
    assert body["error_code"] == "model_not_loaded"
    assert body["http_status"] == 404


def test_unload_unknown_model_returns_404() -> None:
    """POST /v1/unload against a model that was never loaded -> 404 + envelope."""

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        response = client.post(
            "/v1/unload",
            json={"model_id": "model-was-never-loaded"},
        )
    assert response.status_code == 404
    body = response.json()
    _assert_unified_envelope_shape(body)
    assert body["error_code"] == "model_not_loaded"
    assert body["http_status"] == 404


def test_unhandled_exception_returns_500_with_clean_envelope() -> None:
    """A route that raises an arbitrary Exception returns 500 + unified envelope.

    The handler must NEVER leak the raw exception class name or message
    in the response body. We attach a synthetic route to a freshly
    constructed app (mirroring the real wiring) so the test does not
    depend on any specific runtime branch happening to raise.
    """

    app = _build_real_owlmlx_app()

    class _SecretInternalProbeError(Exception):
        """A class name the response body must not leak."""

    @app.get("/__test_unhandled_exception__")
    def _trigger() -> dict[str, str]:
        raise _SecretInternalProbeError("a leaky-looking secret message")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/__test_unhandled_exception__")
    assert response.status_code == 500
    body = response.json()
    _assert_unified_envelope_shape(body)
    assert body["error_code"] == "unexpected_error"
    assert body["http_status"] == 500
    assert body["message"] == "unexpected internal error"
    serialized = repr(body)
    assert "_SecretInternalProbeError" not in serialized
    assert "leaky-looking secret message" not in serialized


def test_envelope_carries_request_id_from_middleware() -> None:
    """Inbound x-request-id reaches the envelope's ``request_id`` field on errors."""

    app = _build_real_owlmlx_app()
    inbound_id = "req_test123_d3_envelope_wiring"
    with TestClient(app) as client:
        response = client.post(
            "/v1/generate",
            headers={REQUEST_ID_HEADER: inbound_id},
            json={"prompt": "hello", "model_id": "no-such-model"},
        )
    assert response.status_code == 404
    body = response.json()
    _assert_unified_envelope_shape(body)
    assert body["request_id"] == inbound_id


def test_envelope_response_has_x_request_id_header() -> None:
    """The error response carries an x-request-id header set by the middleware."""

    app = _build_real_owlmlx_app()
    inbound_id = "req_test123_d3_header_propagation"
    with TestClient(app) as client:
        response = client.post(
            "/v1/generate",
            headers={REQUEST_ID_HEADER: inbound_id},
            json={"prompt": "hello", "model_id": "no-such-model"},
        )
    assert response.status_code == 404
    assert REQUEST_ID_HEADER in response.headers
    assert response.headers[REQUEST_ID_HEADER] == inbound_id


def test_envelope_shape_matches_unifiederrorenvelope_to_response_body() -> None:
    """The envelope JSON keys exactly match ``UnifiedErrorEnvelope.to_response_body``.

    This test is a structural pin: if a future round changes the
    scaffold's envelope shape, the wiring round's HTTP response body
    must change in lock-step or this test fails.
    """

    builder = ErrorEnvelopeBuilder(namespace="owlmlx_native")
    sample_envelope = builder.from_runtime_error_code(
        error_code="model_not_loaded",
        message="model not loaded: probe",
        request_id="req_probe",
        http_status=404,
    )
    expected_keys = set(sample_envelope.to_response_body().keys())
    assert expected_keys == _UNIFIED_ENVELOPE_KEYS

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        response = client.post(
            "/v1/generate",
            json={"prompt": "hi", "model_id": "absent-model"},
        )
    body = response.json()
    assert set(body.keys()) == expected_keys
    # Every key the scaffold's UnifiedErrorEnvelope advertises must
    # also resolve to the same Python type when rendered as JSON.
    sample_body = sample_envelope.to_response_body()
    for key in expected_keys:
        # request_id may be None (when no inbound id) or str — both are
        # legal per the dataclass; we only assert the key set match.
        assert type(body[key]) in {type(sample_body[key]), str, int, type(None)}
    # And the structural shape matcher passes.
    _assert_unified_envelope_shape(body)
    assert isinstance(sample_envelope, UnifiedErrorEnvelope)


def test_compat_routes_keep_their_own_error_shape() -> None:
    """Compat /v1/chat/completions error response is NOT the unified envelope.

    The OpenAI compat surface uses ``_compat_error_response`` whose
    body shape is ``{id, object, error: {message, code}}``. This test
    pins that the D-3 wiring round did NOT bleed the unified envelope
    into the compat namespace.
    """

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "compat-model-not-loaded",
                "messages": [{"role": "user", "content": "hi"}],
            },
        )
    # Either 404 (model_not_loaded) or 503 (other backend errors) —
    # the route's own status mapping is preserved.
    assert response.status_code in {404, 503}
    body = response.json()
    # Compat shape, NOT unified envelope.
    assert "error" in body and isinstance(body["error"], dict)
    assert "message" in body["error"]
    assert "code" in body["error"]
    # Crucially: the unified envelope's ``error_code`` / ``http_status``
    # top-level keys must NOT appear in the compat body.
    assert "error_code" not in body
    assert "http_status" not in body
    # The compat body's top-level keys are {id, object, error}.
    assert set(body.keys()) == {"id", "object", "error"}
