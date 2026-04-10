"""Tests for owlmlx.memory_budget — serving-path memory budget truth."""

import pytest

from owlmlx.memory_budget import (
    DEFAULT_SERVING_BUDGET_GB,
    DEFAULT_SYSTEM_MEMORY_GB,
    DEFAULT_SYSTEM_RESERVE_GB,
    DEFAULT_WARNING_THRESHOLD_GB,
    BudgetEvaluation,
    BudgetVerdict,
    MachineMemoryProfile,
    budget_snapshot,
    default_machine_profile,
    evaluate_model_fit,
)


# ── Constants ──────────────────────────────────────────────────────────────────


def test_default_budget_is_116() -> None:
    """The verified serving budget on 128 GB M5 Max is 116 GB."""
    assert DEFAULT_SERVING_BUDGET_GB == 116.0


def test_default_system_memory_is_128() -> None:
    """The verified system memory is 128 GB."""
    assert DEFAULT_SYSTEM_MEMORY_GB == 128.0


def test_default_reserve_is_12() -> None:
    """The empirical system reserve is 12 GB."""
    assert DEFAULT_SYSTEM_RESERVE_GB == 12.0


def test_budget_equals_memory_minus_reserve() -> None:
    """Budget = system memory - system reserve. This is arithmetic truth."""
    assert DEFAULT_SERVING_BUDGET_GB == DEFAULT_SYSTEM_MEMORY_GB - DEFAULT_SYSTEM_RESERVE_GB


def test_warning_threshold_below_budget() -> None:
    """Warning threshold must be below the budget limit."""
    assert DEFAULT_WARNING_THRESHOLD_GB < DEFAULT_SERVING_BUDGET_GB


# ── MachineMemoryProfile ──────────────────────────────────────────────────────


def test_default_profile_matches_constants() -> None:
    """default_machine_profile() returns the M5 Max profile."""
    p = default_machine_profile()
    assert p.system_memory_gb == 128.0
    assert p.system_reserve_gb == 12.0
    assert p.serving_budget_gb == 116.0
    assert p.warning_threshold_gb == 100.0


def test_custom_profile() -> None:
    """A custom profile can describe different hardware."""
    p = MachineMemoryProfile(
        system_memory_gb=64.0,
        system_reserve_gb=8.0,
        serving_budget_gb=56.0,
        warning_threshold_gb=48.0,
    )
    assert p.serving_budget_gb == 56.0


def test_profile_rejects_zero_memory() -> None:
    """System memory must be positive."""
    with pytest.raises(ValueError, match="system_memory_gb must be positive"):
        MachineMemoryProfile(
            system_memory_gb=0.0,
            system_reserve_gb=0.0,
            serving_budget_gb=0.0,
            warning_threshold_gb=0.0,
        )


def test_profile_rejects_negative_reserve() -> None:
    """System reserve must be non-negative."""
    with pytest.raises(ValueError, match="system_reserve_gb must be non-negative"):
        MachineMemoryProfile(
            system_memory_gb=128.0,
            system_reserve_gb=-1.0,
            serving_budget_gb=129.0,
            warning_threshold_gb=100.0,
        )


def test_profile_rejects_budget_exceeding_memory() -> None:
    """Serving budget cannot exceed total system memory."""
    with pytest.raises(ValueError, match="cannot exceed"):
        MachineMemoryProfile(
            system_memory_gb=64.0,
            system_reserve_gb=8.0,
            serving_budget_gb=65.0,
            warning_threshold_gb=50.0,
        )


def test_profile_is_frozen() -> None:
    """Profile is immutable after creation."""
    p = default_machine_profile()
    with pytest.raises(AttributeError):
        p.serving_budget_gb = 200.0  # type: ignore[misc]


# ── evaluate_model_fit ─────────────────────────────────────────────────────────


def test_small_model_fits() -> None:
    """A 15 GB model on an empty machine fits easily."""
    result = evaluate_model_fit(requested_gb=15.0)
    assert result.verdict == BudgetVerdict.fits
    assert result.projected_gb == 15.0
    assert result.headroom_gb == 101.0


def test_model_fits_with_existing_load() -> None:
    """A 62 GB model with 15 GB already loaded = 77 GB, below warning threshold."""
    result = evaluate_model_fit(requested_gb=62.0, currently_loaded_gb=15.0)
    assert result.verdict == BudgetVerdict.fits
    assert result.projected_gb == 77.0


def test_model_exceeds_budget() -> None:
    """A 62 GB model with 60 GB loaded exceeds the 116 GB budget."""
    result = evaluate_model_fit(requested_gb=62.0, currently_loaded_gb=60.0)
    assert result.verdict == BudgetVerdict.exceeds
    assert result.projected_gb == 122.0
    assert result.headroom_gb == -6.0


def test_exact_budget_limit_exceeds() -> None:
    """Exactly at budget limit still exceeds (strictly greater than)."""
    result = evaluate_model_fit(requested_gb=116.01, currently_loaded_gb=0.0)
    assert result.verdict == BudgetVerdict.exceeds


def test_exactly_at_budget_fits_with_warning() -> None:
    """Exactly at budget (116.0) fits because it's not greater than budget,
    but it is above the 100 GB warning threshold."""
    result = evaluate_model_fit(requested_gb=116.0, currently_loaded_gb=0.0)
    assert result.verdict == BudgetVerdict.fits_warning


def test_at_warning_threshold_triggers_warning() -> None:
    """Projected memory above warning threshold triggers fits_warning."""
    result = evaluate_model_fit(requested_gb=101.0, currently_loaded_gb=0.0)
    assert result.verdict == BudgetVerdict.fits_warning
    assert "approaches budget limit" in result.message


def test_below_warning_threshold_clean_fit() -> None:
    """Below warning threshold is a clean fit."""
    result = evaluate_model_fit(requested_gb=50.0, currently_loaded_gb=40.0)
    assert result.verdict == BudgetVerdict.fits
    assert "fits within budget" in result.message


def test_exceeds_message_includes_numbers() -> None:
    """The exceeds message includes loaded, requested, and limit."""
    result = evaluate_model_fit(requested_gb=62.0, currently_loaded_gb=60.0)
    assert "60.0G loaded" in result.message
    assert "62.0G requested" in result.message
    assert "116.0G limit" in result.message


def test_custom_profile_budget() -> None:
    """evaluate_model_fit respects custom profiles."""
    small_machine = MachineMemoryProfile(
        system_memory_gb=32.0,
        system_reserve_gb=4.0,
        serving_budget_gb=28.0,
        warning_threshold_gb=22.0,
    )
    result = evaluate_model_fit(requested_gb=15.0, profile=small_machine)
    assert result.verdict == BudgetVerdict.fits
    assert result.budget_gb == 28.0


def test_custom_profile_exceeds() -> None:
    """A model that fits on 128 GB may exceed on 32 GB."""
    small_machine = MachineMemoryProfile(
        system_memory_gb=32.0,
        system_reserve_gb=4.0,
        serving_budget_gb=28.0,
        warning_threshold_gb=22.0,
    )
    result = evaluate_model_fit(
        requested_gb=62.0,
        currently_loaded_gb=0.0,
        profile=small_machine,
    )
    assert result.verdict == BudgetVerdict.exceeds


def test_evaluation_is_pure() -> None:
    """Same inputs always produce same outputs — no side effects."""
    r1 = evaluate_model_fit(requested_gb=15.0, currently_loaded_gb=50.0)
    r2 = evaluate_model_fit(requested_gb=15.0, currently_loaded_gb=50.0)
    assert r1 == r2


def test_evaluation_result_is_frozen() -> None:
    """BudgetEvaluation is immutable."""
    result = evaluate_model_fit(requested_gb=15.0)
    with pytest.raises(AttributeError):
        result.verdict = BudgetVerdict.exceeds  # type: ignore[misc]


def test_zero_currently_loaded() -> None:
    """Zero currently loaded is the default — empty machine."""
    result = evaluate_model_fit(requested_gb=15.0)
    assert result.currently_loaded_gb == 0.0


# ── Gemma co-residency scenario ───────────────────────────────────────────────


def test_gemma_cannot_coreside_with_120b() -> None:
    """Gemma (~62 GB) + gpt-oss-120b (~58 GB) = 120 GB > 116 GB budget.
    This is the real-world scenario from model-line-placement.md."""
    result = evaluate_model_fit(requested_gb=58.0, currently_loaded_gb=62.0)
    assert result.verdict == BudgetVerdict.exceeds


def test_gemma_plus_distilled_fits() -> None:
    """Gemma (~62 GB) + Distilled-27B (~15 GB) = 77 GB, below 100 GB warning."""
    result = evaluate_model_fit(requested_gb=15.0, currently_loaded_gb=62.0)
    assert result.verdict == BudgetVerdict.fits


def test_distilled_resident_plus_qwen_fits() -> None:
    """Distilled-27B (~15 GB) + Qwen3.5 (~8 GB) = 23 GB, clean fit."""
    result = evaluate_model_fit(requested_gb=8.0, currently_loaded_gb=15.0)
    assert result.verdict == BudgetVerdict.fits


# ── budget_snapshot ────────────────────────────────────────────────────────────


def test_snapshot_has_required_fields() -> None:
    """Budget snapshot includes all fields needed for status exposure."""
    snap = budget_snapshot(currently_loaded_gb=15.0)
    assert snap["system_memory_gb"] == 128.0
    assert snap["system_reserve_gb"] == 12.0
    assert snap["serving_budget_gb"] == 116.0
    assert snap["warning_threshold_gb"] == 100.0
    assert snap["currently_loaded_gb"] == 15.0
    assert snap["available_gb"] == 101.0
    assert 0.0 <= snap["utilization"] <= 1.0


def test_snapshot_utilization_is_ratio() -> None:
    """Utilization = currently_loaded / serving_budget."""
    snap = budget_snapshot(currently_loaded_gb=58.0)
    assert snap["utilization"] == round(58.0 / 116.0, 3)


def test_snapshot_empty_machine() -> None:
    """Empty machine has full budget available."""
    snap = budget_snapshot()
    assert snap["currently_loaded_gb"] == 0.0
    assert snap["available_gb"] == 116.0
    assert snap["utilization"] == 0.0


def test_snapshot_custom_profile() -> None:
    """Snapshot respects custom profiles."""
    small = MachineMemoryProfile(
        system_memory_gb=64.0,
        system_reserve_gb=8.0,
        serving_budget_gb=56.0,
        warning_threshold_gb=48.0,
    )
    snap = budget_snapshot(currently_loaded_gb=20.0, profile=small)
    assert snap["serving_budget_gb"] == 56.0
    assert snap["available_gb"] == 36.0


def test_snapshot_over_budget_shows_negative_available() -> None:
    """If more is loaded than budget allows, available goes negative."""
    snap = budget_snapshot(currently_loaded_gb=120.0)
    assert snap["available_gb"] == -4.0
