"""Tests for owlmlx.abort_recovery — serving-path abort recovery state machine."""

from owlmlx.abort_recovery import (
    MAX_ABORT_HISTORY,
    SNAPSHOT_RECENT_ABORTS,
    AbortEvent,
    AbortRecoveryTracker,
    SubstrateState,
)
from owlmlx.context_concurrency import HIGH_CONTEXT_THRESHOLD_TOKENS


# ── Initial state ──────────────────────────────────────────────────────────────


def test_initial_state_is_clean() -> None:
    """A fresh tracker starts in clean state."""
    t = AbortRecoveryTracker()
    assert t.state == SubstrateState.clean
    assert t.is_clean() is True
    assert t.is_recovery_required() is False
    assert t.is_probing() is False


# ── Sub-threshold aborts ───────────────────────────────────────────────────────


def test_sub_threshold_abort_does_not_trigger_probing() -> None:
    """Aborts below the high-context threshold do not change state."""
    t = AbortRecoveryTracker()
    triggered = t.record_abort(
        context_tokens=10000,
        error_type="stream_error",
        now=1000.0,
    )
    assert triggered is False
    assert t.state == SubstrateState.clean


def test_sub_threshold_abort_still_recorded() -> None:
    """Sub-threshold aborts appear in history for audit."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=10000, error_type="timeout", now=1000.0)
    snap = t.snapshot()
    assert snap["total_aborts"] == 1
    assert snap["total_high_context_aborts"] == 0
    assert len(snap["recent_aborts"]) == 1


def test_exactly_at_threshold_does_not_trigger() -> None:
    """Exactly at threshold (49152) does NOT trigger probing.
    The condition is strictly greater than threshold."""
    t = AbortRecoveryTracker()
    triggered = t.record_abort(
        context_tokens=HIGH_CONTEXT_THRESHOLD_TOKENS,
        error_type="stream_error",
        now=1000.0,
    )
    assert triggered is False
    assert t.state == SubstrateState.clean


# ── High-context abort → probing ───────────────────────────────────────────────


def test_high_context_abort_enters_probing() -> None:
    """An abort above threshold transitions clean → probing."""
    t = AbortRecoveryTracker()
    triggered = t.record_abort(
        context_tokens=60000,
        error_type="stream_error",
        now=1000.0,
    )
    assert triggered is True
    assert t.state == SubstrateState.probing
    assert t.is_probing() is True


def test_high_context_abort_increments_counters() -> None:
    """High-context abort increments both total and high-context counters."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    snap = t.snapshot()
    assert snap["total_aborts"] == 1
    assert snap["total_high_context_aborts"] == 1


# ── Probe pass → clean ─────────────────────────────────────────────────────────


def test_probe_pass_returns_to_clean() -> None:
    """After probing, a successful probe returns state to clean."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    assert t.state == SubstrateState.probing

    result = t.apply_probe_result(passed=True, now=1005.0)
    assert result == SubstrateState.clean
    assert t.is_clean() is True
    assert t.is_recovery_required() is False


# ── Probe fail → contaminated ──────────────────────────────────────────────────


def test_probe_fail_enters_contaminated() -> None:
    """After probing, a failed probe transitions to contaminated."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    result = t.apply_probe_result(passed=False, now=1005.0)
    assert result == SubstrateState.contaminated
    assert t.is_recovery_required() is True


def test_probe_fail_records_reason() -> None:
    """Failed probe sets contamination reason."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    t.apply_probe_result(passed=False, reason="scheduler loop", now=1005.0)
    snap = t.snapshot()
    assert snap["contamination_reason"] == "scheduler loop"


def test_probe_fail_default_reason() -> None:
    """Failed probe without explicit reason gets default reason."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    t.apply_probe_result(passed=False, now=1005.0)
    snap = t.snapshot()
    assert "failed health probe" in snap["contamination_reason"]


# ── Contaminated behavior ──────────────────────────────────────────────────────


def test_contaminated_means_recovery_required() -> None:
    """Contaminated state means recovery is required."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    t.apply_probe_result(passed=False, now=1005.0)
    assert t.is_recovery_required() is True
    assert t.is_clean() is False


def test_abort_while_contaminated_does_not_reenter_probing() -> None:
    """A new abort while contaminated does NOT transition to probing."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    t.apply_probe_result(passed=False, now=1005.0)
    assert t.state == SubstrateState.contaminated

    triggered = t.record_abort(
        context_tokens=80000, error_type="stream_error", now=1010.0,
    )
    assert triggered is False
    assert t.state == SubstrateState.contaminated


# ── Recovery ───────────────────────────────────────────────────────────────────


def test_successful_recovery_returns_to_clean() -> None:
    """Successful recovery transitions contaminated → clean."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    t.apply_probe_result(passed=False, now=1005.0)

    result = t.apply_recovery_result(passed=True, now=1060.0)
    assert result == SubstrateState.clean
    assert t.is_clean() is True


def test_successful_recovery_increments_counter() -> None:
    """Successful recovery increments recovery count."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    t.apply_probe_result(passed=False, now=1005.0)
    t.apply_recovery_result(passed=True, now=1060.0)

    snap = t.snapshot()
    assert snap["total_recoveries"] == 1
    assert snap["last_recovery_at"] == 1060.0


def test_failed_recovery_stays_contaminated() -> None:
    """Failed recovery attempt stays contaminated."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    t.apply_probe_result(passed=False, now=1005.0)

    result = t.apply_recovery_result(passed=False, now=1060.0)
    assert result == SubstrateState.contaminated
    assert t.is_recovery_required() is True
    assert t.snapshot()["total_recoveries"] == 0


# ── Force clean ────────────────────────────────────────────────────────────────


def test_force_clean_from_contaminated() -> None:
    """Force clean transitions contaminated → clean and records previous."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    t.apply_probe_result(passed=False, now=1005.0)

    previous = t.force_clean(now=1060.0)
    assert previous == "contaminated"
    assert t.is_clean() is True
    assert t.snapshot()["total_recoveries"] == 1


def test_force_clean_from_clean() -> None:
    """Force clean from clean is a no-op (stays clean, no recovery count)."""
    t = AbortRecoveryTracker()
    previous = t.force_clean(now=1000.0)
    assert previous == "clean"
    assert t.is_clean() is True
    assert t.snapshot()["total_recoveries"] == 0


def test_force_clean_from_probing() -> None:
    """Force clean from probing transitions to clean without recovery count."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    assert t.is_probing() is True

    previous = t.force_clean(now=1005.0)
    assert previous == "probing"
    assert t.is_clean() is True
    assert t.snapshot()["total_recoveries"] == 0


def test_force_clean_clears_contamination_reason() -> None:
    """Force clean clears the contamination reason."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    t.apply_probe_result(passed=False, reason="scheduler loop", now=1005.0)
    t.force_clean(now=1060.0)
    assert t.snapshot()["contamination_reason"] == ""


# ── Abort history bounding ─────────────────────────────────────────────────────


def test_history_bounded_to_max() -> None:
    """Abort history never exceeds MAX_ABORT_HISTORY entries."""
    t = AbortRecoveryTracker()
    for i in range(MAX_ABORT_HISTORY + 10):
        t.record_abort(
            context_tokens=1000,
            error_type="test",
            now=float(i),
        )
    # Internal history is bounded
    assert t.snapshot()["total_aborts"] == MAX_ABORT_HISTORY + 10


def test_snapshot_recent_aborts_bounded() -> None:
    """Snapshot only shows the most recent SNAPSHOT_RECENT_ABORTS."""
    t = AbortRecoveryTracker()
    for i in range(10):
        t.record_abort(
            context_tokens=1000,
            error_type=f"err_{i}",
            now=float(i),
        )
    snap = t.snapshot()
    assert len(snap["recent_aborts"]) == SNAPSHOT_RECENT_ABORTS


# ── Snapshot structure ─────────────────────────────────────────────────────────


def test_snapshot_has_required_fields() -> None:
    """Snapshot includes all expected runtime truth fields."""
    t = AbortRecoveryTracker()
    snap = t.snapshot()
    expected_keys = {
        "state",
        "recovery_required",
        "contamination_reason",
        "total_aborts",
        "total_high_context_aborts",
        "total_recoveries",
        "last_abort_at",
        "last_probe_at",
        "last_probe_ok",
        "last_recovery_at",
        "recent_aborts",
        "high_context_threshold_tokens",
    }
    assert set(snap.keys()) == expected_keys


def test_snapshot_initial_values() -> None:
    """Fresh tracker snapshot has zeroed counters and None timestamps."""
    t = AbortRecoveryTracker()
    snap = t.snapshot()
    assert snap["state"] == "clean"
    assert snap["recovery_required"] is False
    assert snap["contamination_reason"] == ""
    assert snap["total_aborts"] == 0
    assert snap["total_high_context_aborts"] == 0
    assert snap["total_recoveries"] == 0
    assert snap["last_abort_at"] is None
    assert snap["last_probe_at"] is None
    assert snap["last_probe_ok"] is None
    assert snap["last_recovery_at"] is None
    assert snap["recent_aborts"] == []


def test_snapshot_has_no_transport_fields() -> None:
    """Snapshot must NOT contain HTTP, URL, semaphore, or router fields."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="stream_error", now=1000.0)
    t.apply_probe_result(passed=False, now=1005.0)
    snap = t.snapshot()

    forbidden_patterns = [
        "url", "http", "endpoint", "semaphore", "lock",
        "asyncio", "task", "omlx_base", "probe_model",
    ]
    snap_str = str(snap).lower()
    for pattern in forbidden_patterns:
        assert pattern not in snap_str, f"snapshot contains '{pattern}' — transport leak"


# ── Threshold alignment with context_concurrency ───────────────────────────────


def test_threshold_matches_context_concurrency() -> None:
    """Abort threshold must match the canonical high-context threshold."""
    t = AbortRecoveryTracker()
    snap = t.snapshot()
    assert snap["high_context_threshold_tokens"] == HIGH_CONTEXT_THRESHOLD_TOKENS
    assert snap["high_context_threshold_tokens"] == 49152


# ── AbortEvent immutability ────────────────────────────────────────────────────


def test_abort_event_is_frozen() -> None:
    """AbortEvent is immutable."""
    event = AbortEvent(
        timestamp=1000.0,
        context_tokens=60000,
        error_type="stream_error",
    )
    try:
        event.timestamp = 2000.0  # type: ignore[misc]
        assert False, "Should have raised AttributeError"
    except AttributeError:
        pass


def test_abort_event_detail_truncated() -> None:
    """Detail is truncated to 200 characters on recording."""
    t = AbortRecoveryTracker()
    long_detail = "x" * 500
    t.record_abort(
        context_tokens=60000,
        error_type="stream_error",
        detail=long_detail,
        now=1000.0,
    )
    snap = t.snapshot()
    assert len(snap["recent_aborts"][0]["detail"]) == 200


# ── Deterministic transitions ──────────────────────────────────────────────────


def test_full_lifecycle() -> None:
    """Walk through a complete abort → probe → contaminate → recover cycle."""
    t = AbortRecoveryTracker()
    assert t.state == SubstrateState.clean

    # High-context abort
    t.record_abort(context_tokens=60000, error_type="prefill_abort", now=100.0)
    assert t.state == SubstrateState.probing

    # Probe fails
    t.apply_probe_result(passed=False, reason="scheduler loop", now=105.0)
    assert t.state == SubstrateState.contaminated
    assert t.is_recovery_required() is True

    # Recovery fails first time
    t.apply_recovery_result(passed=False, now=200.0)
    assert t.state == SubstrateState.contaminated

    # Recovery succeeds second time
    t.apply_recovery_result(passed=True, now=300.0)
    assert t.state == SubstrateState.clean
    assert t.is_recovery_required() is False

    snap = t.snapshot()
    assert snap["total_aborts"] == 1
    assert snap["total_high_context_aborts"] == 1
    assert snap["total_recoveries"] == 1
    assert snap["last_recovery_at"] == 300.0


def test_clean_after_probe_pass_allows_new_cycle() -> None:
    """After recovery, a new abort can restart the cycle."""
    t = AbortRecoveryTracker()
    t.record_abort(context_tokens=60000, error_type="err", now=100.0)
    t.apply_probe_result(passed=True, now=105.0)
    assert t.is_clean() is True

    # New abort starts a fresh probing cycle
    triggered = t.record_abort(context_tokens=80000, error_type="err", now=200.0)
    assert triggered is True
    assert t.state == SubstrateState.probing


# ── SubstrateState enum ────────────────────────────────────────────────────────


def test_substrate_state_values() -> None:
    """SubstrateState enum has exactly the expected values."""
    assert set(SubstrateState) == {
        SubstrateState.clean,
        SubstrateState.probing,
        SubstrateState.contaminated,
    }


def test_substrate_state_is_string() -> None:
    """SubstrateState values are strings for easy serialization."""
    assert SubstrateState.clean == "clean"
    assert SubstrateState.probing == "probing"
    assert SubstrateState.contaminated == "contaminated"
