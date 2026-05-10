"""Tests for the repeatability campaign harness.

Verifies that run_campaign() computes variance statistics correctly and
writes the expected fields to the Model RC ledger. Uses a real uvicorn
server on a random port backed by FakeBackend so the HTTP surface is
identical to production.
"""

from __future__ import annotations

import json
import socket
import threading
import time

import pytest
import uvicorn

from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.model_release_candidate_ledger import ModelReleaseCandidateLedger
from scripts.runtime_repeatability_campaign import (
    _campaign_label,
    _parse_stream_events,
    run_campaign,
    write_to_ledger,
)


# ---------------------------------------------------------------------------
# Free-port helper
# ---------------------------------------------------------------------------

def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# Ephemeral uvicorn fixture
# ---------------------------------------------------------------------------

class _Server(threading.Thread):
    def __init__(self, app, host: str, port: int) -> None:
        super().__init__(daemon=True)
        self._cfg = uvicorn.Config(app, host=host, port=port, log_level="error")
        self._server = uvicorn.Server(self._cfg)

    def run(self) -> None:
        self._server.run()

    def stop(self) -> None:
        self._server.should_exit = True


@pytest.fixture()
def fake_server():
    """Spin up a real uvicorn server with FakeBackend; yield base_url; tear down."""
    kernel = RuntimeKernel(FakeBackend())
    app = create_app(kernel)
    port = _free_port()
    host = "127.0.0.1"
    srv = _Server(app, host, port)
    srv.start()
    # Wait until the server is ready
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            s = socket.create_connection((host, port), timeout=0.1)
            s.close()
            break
        except OSError:
            time.sleep(0.05)
    base_url = f"http://{host}:{port}"
    yield base_url
    srv.stop()
    srv.join(timeout=3.0)


# ---------------------------------------------------------------------------
# Unit tests (no server needed)
# ---------------------------------------------------------------------------

def test_campaign_label_smoke():
    assert _campaign_label(1) == "smoke"
    assert _campaign_label(4) == "smoke"


def test_campaign_label_candidate():
    assert _campaign_label(5) == "repeatability_candidate"
    assert _campaign_label(19) == "repeatability_candidate"


def test_campaign_label_evidence():
    assert _campaign_label(20) == "repeatability_evidence"
    assert _campaign_label(50) == "repeatability_evidence"


def test_parse_stream_events_extracts_first_token_and_prefill():
    events = [
        {
            "event": "token",
            "text": "Hello",
            "sequence": 1,
            "completion_tokens": 1,
            "wait_time_s": 0.05,
            "prefill_ms": 120.5,
        },
        {
            "event": "token",
            "text": " world",
            "sequence": 2,
            "completion_tokens": 2,
        },
        {
            "event": "done",
            "sequence": 2,
            "completion_tokens": 2,
            "finish_reason": "stop",
        },
    ]
    result = _parse_stream_events(events)
    assert result["prefill_ms"] == pytest.approx(120.5)
    assert result["completion_tokens"] == 2
    assert result["finish_reason"] == "stop"
    assert result["error"] is None
    assert result["queue_wait_ms"] == pytest.approx(50.0)


def test_parse_stream_events_error_detected():
    events = [{"event": "error", "detail": {"message": "backend_error"}}]
    result = _parse_stream_events(events)
    assert result["error"] == "backend_error"


# ---------------------------------------------------------------------------
# Integration tests (real server)
# ---------------------------------------------------------------------------

def test_run_campaign_smoke_n2_succeeds(fake_server, tmp_path):
    """N=2 smoke run completes without error and returns repeatability fields."""
    result = run_campaign(
        server_url=fake_server,
        model_id="test-model",
        artifact_path=str(tmp_path),
        repeat_count=2,
        prompt="Hello",
        max_tokens=4,
        http_timeout_s=30.0,
    )
    assert result["error"] is None
    assert result["campaign_label"] == "smoke"
    stats = result["repeatability_stats_dict"]
    assert stats["n"] == 2
    # 2 samples → insufficient_samples (n < 5)
    assert stats["stability_label"] == "insufficient_samples"


def test_run_campaign_writes_repeatability_fields_to_ledger(fake_server, tmp_path):
    """Ledger record contains all required repeatability_* and runtime_prefill_phase_ms fields."""
    ledger_path = tmp_path / "ledger.jsonl"

    result = run_campaign(
        server_url=fake_server,
        model_id="test-model",
        artifact_path=str(tmp_path),
        repeat_count=2,
        prompt="Hello",
        max_tokens=4,
        http_timeout_s=30.0,
    )

    assert result["error"] is None
    write_to_ledger(result["record_kwargs"], str(ledger_path))

    records = ModelReleaseCandidateLedger(str(ledger_path)).history()
    assert len(records) == 1
    d = records[0]

    assert "repeatability_n" in d
    assert d["repeatability_n"] == 2
    assert "repeatability_stability_label" in d
    assert d["repeatability_stability_label"] == "insufficient_samples"
    # stddev may be None for N=2 insufficient, but the field must exist
    assert "repeatability_ttft_ms_stddev" in d
    assert "repeatability_decode_tps_stddev" in d


def test_run_campaign_post_health_check_runs(fake_server, tmp_path):
    """post_health_clean is present in the result."""
    result = run_campaign(
        server_url=fake_server,
        model_id="test-model",
        artifact_path=str(tmp_path),
        repeat_count=2,
        prompt="Test",
        max_tokens=4,
        http_timeout_s=30.0,
    )
    assert result["error"] is None
    assert "post_health_clean" in result
    # FakeBackend unload always succeeds; health should be clean
    assert result["post_health_clean"] is True


def test_run_campaign_returns_per_repeat_results(fake_server, tmp_path):
    """per_repeat_results list has one entry per repeat."""
    result = run_campaign(
        server_url=fake_server,
        model_id="test-model",
        artifact_path=str(tmp_path),
        repeat_count=3,
        prompt="Test",
        max_tokens=4,
        http_timeout_s=30.0,
    )
    assert result["error"] is None
    assert len(result["per_repeat_results"]) == 3
    for r in result["per_repeat_results"]:
        assert "repeat_index" in r
        assert "completion_tokens" in r
