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

import scripts.runtime_repeatability_campaign as campaign
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
            "_client_elapsed_ms": 150.0,
        },
        {
            "event": "token",
            "text": " world",
            "sequence": 2,
            "completion_tokens": 2,
            "_client_elapsed_ms": 175.0,
        },
        {
            "event": "done",
            "sequence": 2,
            "completion_tokens": 2,
            "finish_reason": "stop",
            "_client_elapsed_ms": 250.0,
        },
    ]
    result = _parse_stream_events(events)
    assert result["first_token_ms"] == pytest.approx(150.0)
    assert result["prefill_ms"] == pytest.approx(120.5)
    assert result["wall_ms"] == pytest.approx(250.0)
    assert result["completion_tokens"] == 2
    assert result["finish_reason"] == "stop"
    assert result["error"] is None
    assert result["queue_wait_ms"] == pytest.approx(50.0)
    assert result["decode_tps"] == pytest.approx(10.0)


def test_parse_stream_events_error_detected():
    events = [{"event": "error", "detail": {"message": "backend_error"}}]
    result = _parse_stream_events(events)
    assert result["error"] == "backend_error"


def test_parse_stream_events_prefers_server_side_timing():
    """Server-side timing from done.detail.timing overrides client-side elapsed."""
    events = [
        {
            "event": "token",
            "text": "Hello",
            "completion_tokens": 1,
            "_client_elapsed_ms": 5000.0,  # batched; all arrive at ~same time
        },
        {
            "event": "token",
            "text": " world",
            "completion_tokens": 2,
            "_client_elapsed_ms": 5001.0,
        },
        {
            "event": "done",
            "completion_tokens": 2,
            "finish_reason": "stop",
            "_client_elapsed_ms": 5002.0,  # practically same → decode_wall≈0 client-side
            "detail": {
                "pid": 999,
                "timing": {
                    "surface": "owlmlx.child_stream_timing",
                    "stream_call_start_ms": 10.0,
                    "first_response_ms": 1200.0,
                    "first_visible_token_ms": 1200.0,
                    "stream_wall_ms": 3600.0,
                },
            },
        },
    ]
    result = _parse_stream_events(events)
    # Server-side values should win
    assert result["first_token_ms"] == pytest.approx(1200.0)
    assert result["wall_ms"] == pytest.approx(3600.0)
    # decode_wall = 3600 - 1200 = 2400ms; 1 decode token → 0.417 tps (rounded 3dp)
    assert result["decode_tps"] == pytest.approx(0.417, abs=1e-3)
    # prefill derived from server timing: 1200 - 10 = 1190ms
    assert result["prefill_ms"] == pytest.approx(1190.0)
    assert result["server_timing"] is not None
    assert result["server_timing"]["stream_wall_ms"] == pytest.approx(3600.0)


def test_parse_stream_events_falls_back_to_client_timing_without_server():
    """When server_timing is absent the client-side elapsed values are used."""
    events = [
        {
            "event": "token",
            "text": "Hi",
            "completion_tokens": 1,
            "_client_elapsed_ms": 100.0,
        },
        {
            "event": "done",
            "completion_tokens": 1,
            "finish_reason": "stop",
            "_client_elapsed_ms": 200.0,
        },
    ]
    result = _parse_stream_events(events)
    assert result["first_token_ms"] == pytest.approx(100.0)
    assert result["wall_ms"] == pytest.approx(200.0)
    assert result["server_timing"] is None


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


def test_run_campaign_passes_generation_params_under_params(monkeypatch, tmp_path):
    seen_payloads: list[dict] = []

    def fake_http_json(method, url, payload=None, timeout_s=120.0):
        if url.endswith("/healthz"):
            return 200, {"ok": True, "active_model_id": None}
        if url.endswith("/v1/load"):
            return 200, {"detail": "loaded"}
        if url.endswith("/v1/unload"):
            return 200, {"detail": "unloaded"}
        raise AssertionError(f"unexpected json call: {method} {url}")

    def fake_stream(url, payload, timeout_s=180.0):
        seen_payloads.append(payload)
        return [
            {
                "event": "token",
                "text": "a",
                "completion_tokens": 1,
                "_client_elapsed_ms": 10.0,
            },
            {
                "event": "done",
                "finish_reason": "length",
                "_client_elapsed_ms": 20.0,
            },
        ]

    monkeypatch.setattr(campaign, "_http_json", fake_http_json)
    monkeypatch.setattr(campaign, "_http_ndjson_stream", fake_stream)

    result = run_campaign(
        server_url="http://127.0.0.1:9999",
        model_id="test-model",
        artifact_path=str(tmp_path),
        repeat_count=2,
        prompt="Hello",
        max_tokens=3,
        temperature=0.25,
        http_timeout_s=30.0,
        warmup_repeats=0,  # disable warmup so payload count is deterministic
    )

    assert result["error"] is None
    assert len(result["per_repeat_results"]) == 2
    assert len(seen_payloads) == 2
    for payload in seen_payloads:
        assert payload["model_id"] == "test-model"
        assert payload["prompt"] == "Hello"
        assert payload["params"] == {"max_tokens": 3, "temperature": 0.25}


def test_parse_stream_events_keeps_partial_text_and_error():
    events = [
        {
            "event": "token",
            "text": "partial",
            "completion_tokens": 1,
            "_client_elapsed_ms": 1.0,
        },
        {"event": "error", "detail": {"message": "backend_error"}},
    ]

    result = _parse_stream_events(events)

    assert result["text"] == "partial"
    assert result["error"] == "backend_error"


def test_run_campaign_warmup_repeats_excluded_from_stats(monkeypatch, tmp_path):
    """warmup_repeats generates are not counted in per_repeat_results or samples."""
    call_log: list[str] = []

    def fake_http_json(method, url, payload=None, timeout_s=120.0):
        if url.endswith("/healthz"):
            return 200, {"ok": True, "active_model_id": None}
        if url.endswith("/v1/load"):
            return 200, {"detail": "loaded"}
        if url.endswith("/v1/unload"):
            return 200, {"detail": "unloaded"}
        raise AssertionError(f"unexpected: {method} {url}")

    def fake_stream(url, payload, timeout_s=180.0):
        call_log.append("stream")
        return [
            {"event": "token", "text": "x", "completion_tokens": 1, "_client_elapsed_ms": 10.0},
            {"event": "done", "finish_reason": "stop", "_client_elapsed_ms": 20.0},
        ]

    monkeypatch.setattr(campaign, "_http_json", fake_http_json)
    monkeypatch.setattr(campaign, "_http_ndjson_stream", fake_stream)

    result = run_campaign(
        server_url="http://127.0.0.1:9999",
        model_id="m",
        artifact_path=str(tmp_path),
        repeat_count=3,
        prompt="p",
        max_tokens=2,
        http_timeout_s=10.0,
        warmup_repeats=2,
    )

    assert result["error"] is None
    # 2 warmup + 3 measured = 5 total stream calls
    assert len(call_log) == 5
    # per_repeat_results only covers the 3 measured repeats
    assert len(result["per_repeat_results"]) == 3
    stats = result["repeatability_stats_dict"]
    assert stats["n"] == 3


def test_write_per_repeat_evidence_creates_jsonl(tmp_path):
    """write_per_repeat_evidence creates a JSONL with one row per repeat."""
    from scripts.runtime_repeatability_campaign import write_per_repeat_evidence

    per_repeat = [
        {
            "repeat_index": 1,
            "first_token_ms": 1200.0,
            "prefill_ms": 50.0,
            "wall_ms": 3500.0,
            "decode_tps": 4.2,
            "completion_tokens": 10,
            "finish_reason": "stop",
            "error": None,
            "server_timing": {"stream_wall_ms": 3500.0, "first_visible_token_ms": 1200.0, "stream_call_start_ms": 5.0},
        },
        {
            "repeat_index": 2,
            "first_token_ms": 1100.0,
            "prefill_ms": 45.0,
            "wall_ms": 3400.0,
            "decode_tps": 4.4,
            "completion_tokens": 10,
            "finish_reason": "stop",
            "error": None,
            "server_timing": None,
        },
    ]
    record_kwargs = {"created_at": "2026-05-11T00:00:00Z", "model_id": "TestModel"}

    path = write_per_repeat_evidence(per_repeat, record_kwargs, str(tmp_path / "ev"))

    lines = (tmp_path / "ev" / path.split("/")[-1]).read_text().splitlines()
    assert len(lines) == 2
    row0 = json.loads(lines[0])
    assert row0["repeat_index"] == 1
    assert row0["timing_source"] == "server"
    assert row0["server_stream_wall_ms"] == 3500.0
    row1 = json.loads(lines[1])
    assert row1["timing_source"] == "client"
