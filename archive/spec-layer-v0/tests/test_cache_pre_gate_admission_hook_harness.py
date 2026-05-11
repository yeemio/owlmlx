from __future__ import annotations

from pathlib import Path

from owlmlx.cache_pre_gate_admission_hook_harness import (
    run_pre_gate_admission_hook_harness,
)


def test_pre_gate_admission_hook_harness_observes_structural_hook() -> None:
    result = run_pre_gate_admission_hook_harness()

    assert result.runtime_owned_hook_present is True
    assert result.hook_boundary == "before_whole_request_gate_claim"
    assert result.hook_mode == "bounded_runtime_owned_cohort_window"
    assert result.cohort_window_status in {"open_for_join", "closed_waiting_gate_claim"}
    assert result.observed_cohort_count >= 1
    assert result.observed_peak_cohort_size >= 2
    assert result.observed_total_cohorts_formed >= 1
    assert result.aggregation_scope == "pre_claim_window_only"
    assert result.observed_midflight_staged_count >= 1
    assert result.observed_total_staged >= 2
    assert result.observed_total_claimed >= 2
    assert result.observed_total_discarded == 0
    assert result.staging_units == (
        "immutable_request_metadata_snapshot",
        "ticket_reservation_without_gate_claim",
        "bounded_pre_claim_cohort_window_membership",
        "pre_claim_bounded_admission_bookkeeping",
    )


def test_pre_gate_admission_hook_harness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_pre_gate_admission_hook_harness.py"
    ).read_text()
    for pattern in ("llm_router", "ops_dashboard", "local-llm-desktop", "AI/Agent"):
        assert pattern not in source
