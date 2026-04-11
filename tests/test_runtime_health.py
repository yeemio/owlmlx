"""Tests for owlmlx.runtime_health — runtime health semantics.

Covers:
- Enum membership and string-enum equivalence
- Normalization functions (valid, invalid, edge cases)
- is_model_ready predicate
- derive_wait_tier (all load states, memory threshold, lab flag)
- derive_runtime_readiness (priority ordering, substrate signals)
- derive_block_reason (each blocking condition, no-block case)
- derive_platform_status (healthy, degraded, unavailable)
- runtime_health_snapshot (integration)
"""

from __future__ import annotations

import pytest

from owlmlx.runtime_health import (
    LoadState,
    InferenceHealth,
    WaitTier,
    TruthLevel,
    RuntimeReadiness,
    PlatformStatus,
    LARGE_MODEL_MEMORY_THRESHOLD_GB,
    normalize_load_state,
    normalize_inference_health,
    normalize_truth_level,
    is_model_ready,
    derive_wait_tier,
    derive_runtime_readiness,
    derive_block_reason,
    derive_platform_status,
    runtime_health_snapshot,
)
from owlmlx.abort_recovery import SubstrateState


# ── Enum membership ────────────────────────────────────────────────────────────


class TestEnumMembership:
    """All enum types have exactly the expected members."""

    def test_load_state_values(self):
        assert set(m.value for m in LoadState) == {
            "true_loaded", "inferred_loaded", "cold", "unavailable", "unknown",
        }

    def test_inference_health_values(self):
        assert set(m.value for m in InferenceHealth) == {
            "serving", "stale", "reachable_not_serving", "down", "not_applicable",
        }

    def test_wait_tier_values(self):
        assert set(m.value for m in WaitTier) == {
            "ready_now", "short_wait", "long_wait", "background_only",
            "currently_unavailable",
        }

    def test_truth_level_values(self):
        assert set(m.value for m in TruthLevel) == {
            "true", "inferred", "unavailable",
        }

    def test_runtime_readiness_values(self):
        assert set(m.value for m in RuntimeReadiness) == {
            "ready", "degraded", "blocked", "probing", "unknown",
        }

    def test_platform_status_values(self):
        assert set(m.value for m in PlatformStatus) == {
            "healthy", "degraded", "unavailable",
        }

    def test_str_enum_equality(self):
        """str(Enum) members compare equal to their string values."""
        assert LoadState.true_loaded == "true_loaded"
        assert InferenceHealth.serving == "serving"
        assert WaitTier.ready_now == "ready_now"
        assert TruthLevel.true == "true"
        assert RuntimeReadiness.ready == "ready"
        assert PlatformStatus.healthy == "healthy"

    def test_large_model_threshold(self):
        assert LARGE_MODEL_MEMORY_THRESHOLD_GB == 30.0


# ── Normalization ──────────────────────────────────────────────────────────────


class TestNormalizeLoadState:
    """normalize_load_state: valid strings → enum, invalid → unknown."""

    @pytest.mark.parametrize("raw,expected", [
        ("true_loaded", LoadState.true_loaded),
        ("inferred_loaded", LoadState.inferred_loaded),
        ("cold", LoadState.cold),
        ("unavailable", LoadState.unavailable),
        ("unknown", LoadState.unknown),
    ])
    def test_valid(self, raw, expected):
        assert normalize_load_state(raw) == expected

    def test_invalid_returns_unknown(self):
        assert normalize_load_state("bogus") == LoadState.unknown

    def test_empty_returns_unknown(self):
        assert normalize_load_state("") == LoadState.unknown


class TestNormalizeInferenceHealth:
    """normalize_inference_health: valid → enum, invalid → down."""

    @pytest.mark.parametrize("raw,expected", [
        ("serving", InferenceHealth.serving),
        ("stale", InferenceHealth.stale),
        ("reachable_not_serving", InferenceHealth.reachable_not_serving),
        ("down", InferenceHealth.down),
        ("not_applicable", InferenceHealth.not_applicable),
    ])
    def test_valid(self, raw, expected):
        assert normalize_inference_health(raw) == expected

    def test_invalid_returns_down(self):
        assert normalize_inference_health("garbage") == InferenceHealth.down


class TestNormalizeTruthLevel:
    """normalize_truth_level: valid → enum, invalid → unavailable."""

    @pytest.mark.parametrize("raw,expected", [
        ("true", TruthLevel.true),
        ("inferred", TruthLevel.inferred),
        ("unavailable", TruthLevel.unavailable),
    ])
    def test_valid(self, raw, expected):
        assert normalize_truth_level(raw) == expected

    def test_invalid_returns_unavailable(self):
        assert normalize_truth_level("nope") == TruthLevel.unavailable


# ── is_model_ready ─────────────────────────────────────────────────────────────


class TestIsModelReady:
    """is_model_ready: True only when loaded AND serving."""

    def test_true_loaded_and_serving(self):
        assert is_model_ready(LoadState.true_loaded, InferenceHealth.serving) is True

    def test_inferred_loaded_and_serving(self):
        assert is_model_ready(LoadState.inferred_loaded, InferenceHealth.serving) is True

    def test_cold_not_ready(self):
        assert is_model_ready(LoadState.cold, InferenceHealth.serving) is False

    def test_loaded_but_stale(self):
        assert is_model_ready(LoadState.true_loaded, InferenceHealth.stale) is False

    def test_loaded_but_down(self):
        assert is_model_ready(LoadState.true_loaded, InferenceHealth.down) is False

    def test_unavailable_not_ready(self):
        assert is_model_ready(LoadState.unavailable, InferenceHealth.serving) is False

    def test_unknown_not_ready(self):
        assert is_model_ready(LoadState.unknown, InferenceHealth.serving) is False

    def test_accepts_raw_strings(self):
        assert is_model_ready("true_loaded", "serving") is True
        assert is_model_ready("cold", "serving") is False


# ── derive_wait_tier ───────────────────────────────────────────────────────────


class TestDeriveWaitTier:
    """derive_wait_tier: load state × model characteristics → wait tier."""

    def test_loaded_ready_now(self):
        assert derive_wait_tier(LoadState.true_loaded) == WaitTier.ready_now

    def test_inferred_loaded_ready_now(self):
        assert derive_wait_tier(LoadState.inferred_loaded) == WaitTier.ready_now

    def test_cold_small_short_wait(self):
        assert derive_wait_tier(LoadState.cold, memory_gb=10.0) == WaitTier.short_wait

    def test_cold_large_long_wait(self):
        assert derive_wait_tier(LoadState.cold, memory_gb=30.0) == WaitTier.long_wait

    def test_cold_exactly_threshold(self):
        """Memory exactly at threshold → long_wait (>= comparison)."""
        assert derive_wait_tier(
            LoadState.cold, memory_gb=LARGE_MODEL_MEMORY_THRESHOLD_GB
        ) == WaitTier.long_wait

    def test_cold_below_threshold(self):
        assert derive_wait_tier(
            LoadState.cold, memory_gb=LARGE_MODEL_MEMORY_THRESHOLD_GB - 0.1
        ) == WaitTier.short_wait

    def test_cold_no_memory_short_wait(self):
        """Default memory_gb=0 → short_wait."""
        assert derive_wait_tier(LoadState.cold) == WaitTier.short_wait

    def test_unavailable(self):
        assert derive_wait_tier(LoadState.unavailable) == WaitTier.currently_unavailable

    def test_unknown(self):
        assert derive_wait_tier(LoadState.unknown) == WaitTier.currently_unavailable

    def test_lab_flag_overrides(self):
        """is_lab=True always returns background_only regardless of load state."""
        assert derive_wait_tier(LoadState.true_loaded, is_lab=True) == WaitTier.background_only
        assert derive_wait_tier(LoadState.cold, is_lab=True) == WaitTier.background_only

    def test_accepts_raw_string(self):
        assert derive_wait_tier("true_loaded") == WaitTier.ready_now
        assert derive_wait_tier("cold", memory_gb=50) == WaitTier.long_wait

    def test_invalid_string_currently_unavailable(self):
        assert derive_wait_tier("bogus") == WaitTier.currently_unavailable


# ── derive_runtime_readiness ───────────────────────────────────────────────────


class TestDeriveRuntimeReadiness:
    """derive_runtime_readiness: priority-ordered composite assessment."""

    # Priority 1: Substrate contaminated → blocked
    def test_contaminated_blocks(self):
        assert derive_runtime_readiness(
            LoadState.true_loaded, InferenceHealth.serving,
            SubstrateState.contaminated,
        ) == RuntimeReadiness.blocked

    # Priority 1: Substrate probing → probing
    def test_substrate_probing(self):
        assert derive_runtime_readiness(
            LoadState.true_loaded, InferenceHealth.serving,
            SubstrateState.probing,
        ) == RuntimeReadiness.probing

    # Substrate clean doesn't interfere with normal assessment
    def test_substrate_clean_passes_through(self):
        assert derive_runtime_readiness(
            LoadState.true_loaded, InferenceHealth.serving,
            SubstrateState.clean,
        ) == RuntimeReadiness.ready

    # Substrate None (default) is same as clean
    def test_substrate_none_defaults_clean(self):
        assert derive_runtime_readiness(
            LoadState.true_loaded, InferenceHealth.serving,
        ) == RuntimeReadiness.ready

    # Priority 2: Unknown load state → unknown
    def test_unknown_load_state(self):
        assert derive_runtime_readiness(
            LoadState.unknown, InferenceHealth.serving,
        ) == RuntimeReadiness.unknown

    # Priority 2: Unavailable or down → blocked
    def test_unavailable_blocked(self):
        assert derive_runtime_readiness(
            LoadState.unavailable, InferenceHealth.serving,
        ) == RuntimeReadiness.blocked

    def test_backend_down_blocked(self):
        assert derive_runtime_readiness(
            LoadState.true_loaded, InferenceHealth.down,
        ) == RuntimeReadiness.blocked

    # Priority 3: Loaded + serving → ready
    def test_true_loaded_serving_ready(self):
        assert derive_runtime_readiness(
            LoadState.true_loaded, InferenceHealth.serving,
        ) == RuntimeReadiness.ready

    def test_inferred_loaded_serving_ready(self):
        assert derive_runtime_readiness(
            LoadState.inferred_loaded, InferenceHealth.serving,
        ) == RuntimeReadiness.ready

    # Priority 4: Degraded states
    def test_stale_degraded(self):
        assert derive_runtime_readiness(
            LoadState.true_loaded, InferenceHealth.stale,
        ) == RuntimeReadiness.degraded

    def test_reachable_not_serving_degraded(self):
        assert derive_runtime_readiness(
            LoadState.true_loaded, InferenceHealth.reachable_not_serving,
        ) == RuntimeReadiness.degraded

    def test_cold_serving_degraded(self):
        """Cold model even if backend is serving → degraded (model not loaded)."""
        assert derive_runtime_readiness(
            LoadState.cold, InferenceHealth.serving,
        ) == RuntimeReadiness.degraded

    def test_cold_not_applicable_degraded(self):
        assert derive_runtime_readiness(
            LoadState.cold, InferenceHealth.not_applicable,
        ) == RuntimeReadiness.degraded

    # Accepts raw strings
    def test_accepts_strings(self):
        assert derive_runtime_readiness("true_loaded", "serving") == RuntimeReadiness.ready

    def test_accepts_substrate_string(self):
        assert derive_runtime_readiness(
            "true_loaded", "serving", "contaminated"
        ) == RuntimeReadiness.blocked

    def test_invalid_substrate_string_ignored(self):
        """Invalid substrate string treated as clean."""
        assert derive_runtime_readiness(
            "true_loaded", "serving", "not_a_state"
        ) == RuntimeReadiness.ready


# ── derive_block_reason ────────────────────────────────────────────────────────


class TestDeriveBlockReason:
    """derive_block_reason: returns human-readable reason or None."""

    def test_contaminated(self):
        reason = derive_block_reason(substrate_state=SubstrateState.contaminated)
        assert reason is not None
        assert "contaminated" in reason

    def test_budget_infeasible(self):
        reason = derive_block_reason(budget_feasible=False)
        assert reason is not None
        assert "memory" in reason or "budget" in reason

    def test_backend_down(self):
        reason = derive_block_reason(inference_health=InferenceHealth.down)
        assert reason is not None
        assert "down" in reason

    def test_unavailable(self):
        reason = derive_block_reason(load_state=LoadState.unavailable)
        assert reason is not None
        assert "unreachable" in reason

    def test_no_block(self):
        assert derive_block_reason() is None

    def test_clean_substrate_no_block(self):
        assert derive_block_reason(substrate_state=SubstrateState.clean) is None

    def test_budget_feasible_no_block(self):
        assert derive_block_reason(budget_feasible=True) is None

    def test_serving_no_block(self):
        assert derive_block_reason(inference_health=InferenceHealth.serving) is None

    def test_priority_contaminated_over_budget(self):
        """Contamination reported first even if budget also infeasible."""
        reason = derive_block_reason(
            substrate_state=SubstrateState.contaminated,
            budget_feasible=False,
        )
        assert "contaminated" in reason

    def test_accepts_strings(self):
        reason = derive_block_reason(substrate_state="contaminated")
        assert reason is not None
        assert "contaminated" in reason


# ── derive_platform_status ─────────────────────────────────────────────────────


class TestDerivePlatformStatus:
    """derive_platform_status: check results → system-wide status."""

    def test_all_pass_healthy(self):
        assert derive_platform_status(
            check_statuses=["pass", "pass", "pass"],
            up_stable_backends=2,
        ) == PlatformStatus.healthy

    def test_fail_no_backends_unavailable(self):
        assert derive_platform_status(
            check_statuses=["fail", "pass"],
            up_stable_backends=0,
        ) == PlatformStatus.unavailable

    def test_fail_with_backends_degraded(self):
        assert derive_platform_status(
            check_statuses=["fail", "pass"],
            up_stable_backends=1,
        ) == PlatformStatus.degraded

    def test_warn_degraded(self):
        assert derive_platform_status(
            check_statuses=["pass", "warn"],
            up_stable_backends=2,
        ) == PlatformStatus.degraded

    def test_partial_degraded(self):
        assert derive_platform_status(
            check_statuses=["pass", "partial"],
            up_stable_backends=2,
        ) == PlatformStatus.degraded

    def test_empty_checks_healthy(self):
        assert derive_platform_status(
            check_statuses=[],
            up_stable_backends=1,
        ) == PlatformStatus.healthy


# ── runtime_health_snapshot (integration) ──────────────────────────────────────


class TestRuntimeHealthSnapshot:
    """runtime_health_snapshot: builds a complete health dict."""

    def test_ready_snapshot(self):
        snap = runtime_health_snapshot(
            load_state="true_loaded",
            inference_health="serving",
            truth_level="true",
        )
        assert snap["readiness"] == "ready"
        assert snap["wait_tier"] == "ready_now"
        assert snap["is_ready"] is True
        assert snap["block_reason"] is None
        assert snap["load_state"] == "true_loaded"
        assert snap["inference_health"] == "serving"
        assert snap["truth_level"] == "true"

    def test_blocked_snapshot(self):
        snap = runtime_health_snapshot(
            load_state="unavailable",
            inference_health="down",
            truth_level="unavailable",
        )
        assert snap["readiness"] == "blocked"
        assert snap["wait_tier"] == "currently_unavailable"
        assert snap["is_ready"] is False
        assert snap["block_reason"] is not None

    def test_degraded_cold_model(self):
        snap = runtime_health_snapshot(
            load_state="cold",
            inference_health="serving",
            truth_level="inferred",
            memory_gb=50.0,
        )
        assert snap["readiness"] == "degraded"
        assert snap["wait_tier"] == "long_wait"
        assert snap["is_ready"] is False

    def test_contaminated_substrate(self):
        snap = runtime_health_snapshot(
            load_state="true_loaded",
            inference_health="serving",
            truth_level="true",
            substrate_state="contaminated",
        )
        assert snap["readiness"] == "blocked"
        assert snap["block_reason"] is not None
        assert "contaminated" in snap["block_reason"]

    def test_lab_model(self):
        snap = runtime_health_snapshot(
            load_state="true_loaded",
            inference_health="serving",
            truth_level="true",
            is_lab=True,
        )
        assert snap["wait_tier"] == "background_only"
        assert snap["readiness"] == "ready"

    def test_budget_infeasible(self):
        snap = runtime_health_snapshot(
            load_state="true_loaded",
            inference_health="serving",
            truth_level="true",
            budget_feasible=False,
        )
        assert snap["block_reason"] is not None
        assert "budget" in snap["block_reason"] or "memory" in snap["block_reason"]

    def test_snapshot_has_all_keys(self):
        snap = runtime_health_snapshot(
            load_state="cold",
            inference_health="stale",
            truth_level="inferred",
        )
        expected_keys = {
            "load_state", "inference_health", "truth_level",
            "readiness", "wait_tier", "is_ready", "block_reason",
        }
        assert set(snap.keys()) == expected_keys

    def test_accepts_enum_values(self):
        snap = runtime_health_snapshot(
            load_state=LoadState.true_loaded,
            inference_health=InferenceHealth.serving,
            truth_level=TruthLevel.true,
            substrate_state=SubstrateState.clean,
        )
        assert snap["readiness"] == "ready"
