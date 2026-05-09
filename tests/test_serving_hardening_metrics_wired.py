"""Integration tests for D-4 MetricsSnapshotExporter wiring on the real owlmlx app.

These tests construct the actual owlmlx FastAPI app via
``owlmlx.runtime.server.create_app(...)`` and exercise the wired
``MetricsSnapshotExporter`` end-to-end with
``fastapi.testclient.TestClient``. No uvicorn process is spawned and
no model is loaded; the ``/metrics`` route reads only the runtime
kernel's status surface (which the ``FakeBackend`` populates with a
deterministic snapshot of an idle gate).

The companion file ``tests/test_serving_hardening.py`` (committed in
the C-4 scaffold round) exercises ``MetricsSnapshotExporter`` against
synthetic gate-status / native-admission-snapshot dicts. This file
exists to prove the scaffold is in fact installed on the real owlmlx
app after the D-4 wiring round and that the route returns the
Prometheus text-exposition format with the canonical
``text/plain; version=0.0.4`` content-type rather than a JSON
envelope.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from owlmlx.runtime.server import create_app
from owlmlx.runtime.serving_hardening import REQUEST_ID_HEADER


def _build_real_owlmlx_app() -> FastAPI:
    """Build the real owlmlx FastAPI app with no optional ledgers wired.

    Constructed via ``create_app()`` with default kwargs so the
    ``FakeBackend`` is used and no ledger paths are touched. The
    ``FakeBackend`` does not populate ``backend.detail.admission`` —
    so the ``/metrics`` route receives ``None`` as the native admission
    snapshot, which is exactly the case the C-4 scaffold's exporter
    documents (omit the native-admission metric block, do not fabricate
    zeros).
    """

    return create_app()


def test_metrics_endpoint_returns_200_with_prometheus_text_media_type() -> None:
    """GET /metrics returns 200 with content-type starting with ``text/plain``.

    Prometheus scrapers explicitly require the text-exposition format
    advertised via ``text/plain; version=0.0.4`` — JSON envelopes are
    rejected by the standard scrapers. This test pins both the status
    code and the leading ``text/plain`` portion of the content-type.
    """

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 200, response.text
    content_type = response.headers.get("content-type") or ""
    assert content_type.startswith("text/plain"), (
        f"/metrics must use Prometheus text-exposition content-type; "
        f"got {content_type!r}"
    )
    # The version=0.0.4 marker is the canonical Prometheus text-format
    # version label. We accept either the exact string or any leading
    # ``text/plain`` form (Starlette may append a charset).
    assert "version=0.0.4" in content_type


def test_metrics_endpoint_includes_owlmlx_native_namespace_prefix() -> None:
    """The body carries the ``owlmlx_native_`` namespace prefix.

    The exporter is constructed with ``namespace="owlmlx_native"``, so
    every emitted metric name must start with that string.
    """

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "owlmlx_native_" in body, (
        f"/metrics body must contain the configured namespace prefix; got: {body!r}"
    )


def test_metrics_endpoint_includes_gate_counters() -> None:
    """The body contains gate-counter metric names per the scaffold contract.

    The C-4 scaffold's ``render_prometheus_text`` is contracted to emit
    ``<namespace>_waiters``, ``<namespace>_total_served_total``, and
    ``<namespace>_total_queued_total`` whenever the gate-status dict
    carries those keys (which the kernel's ``GenerationGate.status``
    always populates). The longest-wait / longest-exec gauges are also
    asserted because the kernel always populates them.
    """

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    # Counter (cumulative) metrics carry ``_total`` suffix per scaffold.
    assert "owlmlx_native_waiters" in body
    assert "owlmlx_native_total_served_total" in body
    assert "owlmlx_native_total_queued_total" in body
    # Gauges
    assert "owlmlx_native_longest_wait_seconds" in body
    assert "owlmlx_native_longest_exec_seconds" in body


def test_metrics_endpoint_includes_TYPE_HELP_lines() -> None:
    """Each metric block has the Prometheus-required ``# HELP`` and ``# TYPE`` lines.

    Per the Prometheus text-exposition spec, every metric must be
    preceded by a ``# HELP <name> <text>`` line and a ``# TYPE <name>
    <kind>`` line. The C-4 scaffold renders both. This test pins that
    the wired route preserves them — a regression that strips them
    breaks Prometheus ingestion silently.
    """

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    # At least one HELP and one TYPE line per metric block.
    assert "# HELP owlmlx_native_waiters " in body
    assert "# TYPE owlmlx_native_waiters gauge" in body
    assert "# HELP owlmlx_native_total_served_total " in body
    assert "# TYPE owlmlx_native_total_served_total counter" in body
    assert "# HELP owlmlx_native_total_queued_total " in body
    assert "# TYPE owlmlx_native_total_queued_total counter" in body


def test_metrics_endpoint_idempotent_on_repeated_get() -> None:
    """Two consecutive scrapes return 200 and the same metric-name shape.

    The exporter is pure: it reads the current runtime status and
    renders it. Without intervening generation activity, two scrapes
    against the FakeBackend-backed kernel must return the same set of
    metric names (the values may differ if e.g. timestamps were
    embedded, but the scaffold renders only counters / gauges).
    """

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        first = client.get("/metrics")
        second = client.get("/metrics")
    assert first.status_code == 200
    assert second.status_code == 200

    def _metric_names(text: str) -> set[str]:
        names: set[str] = set()
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            head, _, _ = stripped.partition(" ")
            if head:
                names.add(head)
        return names

    assert _metric_names(first.text) == _metric_names(second.text)


def test_metrics_endpoint_works_with_no_native_admission_snapshot() -> None:
    """When ``backend.detail`` carries no ``admission`` key, the route still renders.

    The C-4 scaffold's ``render_prometheus_text`` accepts
    ``native_admission_snapshot=None`` and simply omits the native
    metric block. The default ``FakeBackend`` does NOT populate
    ``backend.detail.admission`` — so this is the live case for the
    wiring's default path. The body must still contain the gate-counter
    metrics and must NOT contain any ``native_max_observed_concurrency``
    / ``native_in_critical_section`` / ``native_serving_ticket`` line.
    """

    app = _build_real_owlmlx_app()
    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    # Gate-counter metrics still present.
    assert "owlmlx_native_waiters" in body
    assert "owlmlx_native_total_served_total" in body
    # Native admission metrics absent because FakeBackend does not
    # populate ``backend.detail.admission``.
    assert "owlmlx_native_native_max_observed_concurrency" not in body
    assert "owlmlx_native_native_in_critical_section" not in body
    assert "owlmlx_native_native_serving_ticket" not in body


def test_metrics_endpoint_carries_request_id_propagation() -> None:
    """Inbound x-request-id is echoed on the /metrics response.

    The D-1 ``RequestIdMiddleware`` is registered at the app level and
    therefore wraps every route, including ``/metrics``. This test
    closes the loop on D-1 + D-4 by asserting that an inbound
    ``x-request-id`` header is preserved on the metrics response, even
    though the route body itself never reads ``request.state``.
    """

    app = _build_real_owlmlx_app()
    inbound_id = "req_test123_d4_metrics_request_id_propagation"
    with TestClient(app) as client:
        response = client.get(
            "/metrics", headers={REQUEST_ID_HEADER: inbound_id}
        )
    assert response.status_code == 200
    assert REQUEST_ID_HEADER in response.headers
    assert response.headers[REQUEST_ID_HEADER] == inbound_id
