"""Tests for CacheResidencyTracker — Campaign 2 cache status surface.

Unit tests: state classification, release ledger, repeated cycles.
Integration tests: tracker wired into RuntimeKernel under FakeBackend,
including the "repeated load" test that satisfies the non-exactness
scheduler capability criterion.
"""

from __future__ import annotations

import asyncio

import pytest

from owlmlx.cache_residency_tracker import CacheReleaseEvent, CacheResidencyTracker
from owlmlx.runtime import FakeBackend, RuntimeKernel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tracker(hot_window_s: float = 60.0, evictable_idle_s: float = 300.0) -> CacheResidencyTracker:
    return CacheResidencyTracker(hot_window_s=hot_window_s, evictable_idle_s=evictable_idle_s)


# ---------------------------------------------------------------------------
# Unit tests — state classification
# ---------------------------------------------------------------------------

def test_record_load_creates_resident_entry():
    t = _tracker()
    t.record_load("m", now_s=0.0)
    snap = t.residency_snapshot(now_s=1.0)
    assert "m" in snap
    assert snap["m"].state == "resident"
    assert snap["m"].use_count == 0
    assert snap["m"].last_used_s is None


def test_record_use_increments_use_count():
    t = _tracker()
    t.record_load("m", now_s=0.0)
    t.record_use("m", now_s=1.0)
    snap = t.residency_snapshot(now_s=2.0)
    assert snap["m"].use_count == 1
    assert snap["m"].last_used_s == pytest.approx(1.0)


def test_state_hot_after_recent_use():
    t = _tracker(hot_window_s=60.0)
    t.record_load("m", now_s=0.0)
    t.record_use("m", now_s=1.0)
    snap = t.residency_snapshot(now_s=5.0)  # 4s idle < 60s hot_window
    assert snap["m"].state == "hot"


def test_state_resident_when_cooling_between_hot_and_evictable():
    t = _tracker(hot_window_s=10.0, evictable_idle_s=100.0)
    t.record_load("m", now_s=0.0)
    t.record_use("m", now_s=1.0)
    snap = t.residency_snapshot(now_s=50.0)  # 49s idle: > hot (10s) but < evictable (100s)
    assert snap["m"].state == "resident"


def test_state_evictable_after_idle_threshold():
    t = _tracker(hot_window_s=10.0, evictable_idle_s=30.0)
    t.record_load("m", now_s=0.0)
    t.record_use("m", now_s=1.0)
    snap = t.residency_snapshot(now_s=40.0)  # 39s idle >= 30s evictable_idle
    assert snap["m"].state == "evictable"


def test_multiple_uses_track_last_only():
    t = _tracker(hot_window_s=60.0)
    t.record_load("m", now_s=0.0)
    t.record_use("m", now_s=1.0)
    t.record_use("m", now_s=2.0)
    t.record_use("m", now_s=3.0)
    snap = t.residency_snapshot(now_s=4.0)
    assert snap["m"].use_count == 3
    assert snap["m"].last_used_s == pytest.approx(3.0)
    assert snap["m"].state == "hot"


# ---------------------------------------------------------------------------
# Unit tests — release ledger
# ---------------------------------------------------------------------------

def test_record_unload_writes_to_ledger():
    t = _tracker()
    t.record_load("m", now_s=0.0)
    t.record_use("m", now_s=1.0)
    t.record_unload("m", reason="manual_unload", now_s=2.0)
    ledger = t.release_ledger_snapshot()
    assert len(ledger) == 1
    ev = ledger[0]
    assert isinstance(ev, CacheReleaseEvent)
    assert ev.model_id == "m"
    assert ev.reason == "manual_unload"
    assert ev.use_count_at_release == 1
    assert ev.seq == 1


def test_record_unload_removes_entry_from_active():
    t = _tracker()
    t.record_load("m", now_s=0.0)
    t.record_unload("m", now_s=1.0)
    snap = t.residency_snapshot(now_s=2.0)
    assert "m" not in snap


def test_unload_without_prior_load_still_writes_ledger():
    """Defensive: unload of an untracked model creates a ledger entry."""
    t = _tracker()
    t.record_unload("ghost", reason="manual_unload", now_s=0.0)
    ledger = t.release_ledger_snapshot()
    assert len(ledger) == 1
    assert ledger[0].use_count_at_release == 0


def test_release_reasons_pressure_eviction():
    t = _tracker()
    t.record_load("m", now_s=0.0)
    t.record_unload("m", reason="pressure_eviction", now_s=1.0)
    ledger = t.release_ledger_snapshot()
    assert ledger[0].reason == "pressure_eviction"


def test_release_reasons_ttl_expiry():
    t = _tracker()
    t.record_load("m", now_s=0.0)
    t.record_unload("m", reason="ttl_expiry", now_s=1.0)
    ledger = t.release_ledger_snapshot()
    assert ledger[0].reason == "ttl_expiry"


# ---------------------------------------------------------------------------
# Unit tests — repeated cycles (the non-exactness criterion)
# ---------------------------------------------------------------------------

def test_repeated_cycles_produce_ledger_entries():
    """5 load/use/unload cycles → 5 release events in ledger."""
    t = _tracker()
    n = 5
    for i in range(n):
        t.record_load("m", now_s=float(i * 10))
        t.record_use("m", now_s=float(i * 10 + 1))
        t.record_unload("m", reason="manual_unload", now_s=float(i * 10 + 2))
    ledger = t.release_ledger_snapshot()
    assert len(ledger) == n
    for idx, ev in enumerate(ledger, start=1):
        assert ev.seq == idx
        assert ev.model_id == "m"
        assert ev.use_count_at_release == 1


def test_status_dict_reflects_active_entries_and_ledger():
    t = _tracker()
    t.record_load("a", now_s=0.0)
    t.record_load("b", now_s=1.0)
    t.record_use("a", now_s=2.0)
    t.record_unload("b", reason="manual_unload", now_s=3.0)

    d = t.status_dict(now_s=4.0)
    assert d["surface"] == "owlmlx.cache_residency_tracker"
    assert d["entry_count"] == 1
    assert "a" in d["entries"]
    assert d["entries"]["a"]["state"] == "hot"
    assert d["release_ledger_total"] == 1
    assert len(d["release_ledger"]) == 1
    assert d["release_ledger"][0]["model_id"] == "b"


# ---------------------------------------------------------------------------
# Integration tests — RuntimeKernel + FakeBackend
# ---------------------------------------------------------------------------

def _kernel() -> RuntimeKernel:
    return RuntimeKernel(FakeBackend())


def test_tracker_wired_into_kernel_after_load():
    """load_model success → model appears as 'resident' in kernel.status_dict()."""
    kernel = _kernel()
    result = kernel.load_model("test-model", memory_gb=1.0)
    assert result.ok
    d = kernel.status_dict()
    residency = d["cache_residency"]
    assert "test-model" in residency["entries"]
    assert residency["entries"]["test-model"]["state"] == "resident"
    assert residency["entry_count"] == 1


def test_tracker_wired_into_kernel_after_generate():
    """generate success → model transitions to 'hot' in residency surface."""
    kernel = _kernel()
    kernel.load_model("test-model", memory_gb=1.0)
    asyncio.run(kernel.generate("hello", model_id="test-model"))
    d = kernel.status_dict()
    entry = d["cache_residency"]["entries"]["test-model"]
    assert entry["state"] == "hot"
    assert entry["use_count"] == 1


def test_tracker_wired_into_kernel_after_unload():
    """unload success → model gone from entries, appears in release_ledger."""
    kernel = _kernel()
    kernel.load_model("test-model", memory_gb=1.0)
    result = kernel.unload_model("test-model")
    assert result.ok
    d = kernel.status_dict()
    residency = d["cache_residency"]
    assert "test-model" not in residency["entries"]
    assert residency["release_ledger_total"] == 1
    assert residency["release_ledger"][0]["model_id"] == "test-model"
    assert residency["release_ledger"][0]["reason"] == "manual_unload"


def test_tracker_repeated_load_generate_unload_in_kernel():
    """3 repeated load/generate/unload cycles → 3 entries in release_ledger.

    This is the non-exactness, under-repeated-load test satisfying Campaign 2.
    """
    kernel = _kernel()
    n = 3
    for _ in range(n):
        kernel.load_model("test-model", memory_gb=1.0)
        asyncio.run(kernel.generate("hello", model_id="test-model"))
        kernel.unload_model("test-model")

    d = kernel.status_dict()
    residency = d["cache_residency"]
    assert residency["entry_count"] == 0  # nothing currently loaded
    assert residency["release_ledger_total"] == n
    assert len(residency["release_ledger"]) == n
    for ev in residency["release_ledger"]:
        assert ev["model_id"] == "test-model"
        assert ev["reason"] == "manual_unload"
        assert ev["use_count_at_release"] == 1


def test_tracker_stream_generate_records_use():
    """stream_generate success also records use via mark_success callback."""
    kernel = _kernel()
    kernel.load_model("test-model", memory_gb=1.0)

    async def run_stream() -> None:
        async for _ in kernel.generate_stream("hello", model_id="test-model"):
            pass

    asyncio.run(run_stream())
    d = kernel.status_dict()
    entry = d["cache_residency"]["entries"]["test-model"]
    assert entry["use_count"] == 1
