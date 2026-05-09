"""D-6 structured request logging contract tests.

Proves that the inline ``_request_lifecycle_log_middleware`` registered in
``runtime/server.py`` emits ``request.start`` / ``request.finish`` /
``request.exception`` records on the ``owlmlx.runtime.server.request``
logger, with structured ``extra`` fields including the request_id from
D-1's ``RequestIdMiddleware``.

Tests use pytest's ``caplog`` fixture to capture log records. No real
backend operations needed — the middleware fires on every request,
including ``/healthz``.
"""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from owlmlx.runtime.server import create_app


_LOGGER_NAME = "owlmlx.runtime.server.request"


def _records_with_event(records: list[logging.LogRecord], event: str) -> list[logging.LogRecord]:
    return [r for r in records if getattr(r, "owlmlx_event", None) == event]


def test_healthz_emits_request_start_and_request_finish_records(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
    app = create_app()
    client = TestClient(app)

    response = client.get("/healthz")
    assert response.status_code == 200

    starts = _records_with_event(caplog.records, "request.start")
    finishes = _records_with_event(caplog.records, "request.finish")
    assert len(starts) == 1, "exactly one request.start expected per request"
    assert len(finishes) == 1, "exactly one request.finish expected per request"


def test_request_finish_record_carries_method_path_status_duration(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
    app = create_app()
    client = TestClient(app)

    client.get("/healthz")
    finish = _records_with_event(caplog.records, "request.finish")[0]

    assert finish.owlmlx_http_method == "GET"
    assert finish.owlmlx_http_path == "/healthz"
    assert finish.owlmlx_http_status == 200
    # duration_ms must be a non-negative float
    assert isinstance(finish.owlmlx_duration_ms, float)
    assert finish.owlmlx_duration_ms >= 0.0


def test_request_records_carry_inbound_request_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
    app = create_app()
    client = TestClient(app)

    inbound_id = "req_test-d6-correlate-1234567890abcdef"
    client.get("/healthz", headers={"x-request-id": inbound_id})

    starts = _records_with_event(caplog.records, "request.start")
    finishes = _records_with_event(caplog.records, "request.finish")
    assert starts[0].owlmlx_request_id == inbound_id
    assert finishes[0].owlmlx_request_id == inbound_id


def test_request_records_carry_middleware_generated_id_when_no_inbound(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
    app = create_app()
    client = TestClient(app)

    client.get("/healthz")  # no x-request-id header
    starts = _records_with_event(caplog.records, "request.start")
    rid = starts[0].owlmlx_request_id
    # D-1 middleware generates ``req_<uuid4hex>`` when none inbound
    assert isinstance(rid, str)
    assert rid.startswith("req_"), f"expected req_ prefix on autogen id, got {rid!r}"


def test_404_path_still_emits_lifecycle_records(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
    app = create_app()
    client = TestClient(app)

    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404

    starts = _records_with_event(caplog.records, "request.start")
    finishes = _records_with_event(caplog.records, "request.finish")
    assert len(starts) == 1
    assert len(finishes) == 1
    assert finishes[0].owlmlx_http_status == 404


def test_lifecycle_records_use_owlmlx_runtime_server_request_logger(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """All lifecycle records must come from the documented logger name so
    operators can filter by it cleanly.
    """

    caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
    app = create_app()
    client = TestClient(app)

    client.get("/healthz")
    relevant = [r for r in caplog.records if getattr(r, "owlmlx_event", None)]
    assert len(relevant) == 2  # start + finish for one request
    for r in relevant:
        assert r.name == _LOGGER_NAME, (
            f"lifecycle record came from {r.name!r}; expected {_LOGGER_NAME!r}"
        )
