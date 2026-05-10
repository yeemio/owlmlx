from __future__ import annotations

from fastapi.testclient import TestClient

from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app


def _client() -> TestClient:
    return TestClient(create_app(RuntimeKernel(FakeBackend())))


def test_cache_scheduler_status_returns_200():
    response = _client().get("/v1/runtime/cache-scheduler-status")
    assert response.status_code == 200


def test_cache_scheduler_status_contract_surface():
    payload = _client().get("/v1/runtime/cache-scheduler-status").json()
    assert payload["contract"]["surface"] == "owlmlx.cache_scheduler_status"
    assert payload["contract"]["version"] == "phase45"


def test_cache_scheduler_status_summary_fields():
    payload = _client().get("/v1/runtime/cache-scheduler-status").json()
    summary = payload["summary"]
    assert summary["status"] == "partial"
    assert summary["scheduler_depth"] == "serial_single_worker"
    assert "cache_depth" in summary
    assert "blocked_reason" in summary
    assert "recommended_next_step" in summary


def test_cache_scheduler_status_scheduler_section():
    payload = _client().get("/v1/runtime/cache-scheduler-status").json()
    scheduler = payload["scheduler"]
    assert scheduler["mode"] == "serial_single_worker"
    assert scheduler["continuous_batching"] is False


def test_cache_scheduler_status_stable_sections_present():
    payload = _client().get("/v1/runtime/cache-scheduler-status").json()
    stable = payload["contract"]["stable_sections"]
    assert "summary" in stable
    assert "scheduler" in stable
    assert "cache_profile" in stable
    assert "turboquant_cache_safety" in stable
