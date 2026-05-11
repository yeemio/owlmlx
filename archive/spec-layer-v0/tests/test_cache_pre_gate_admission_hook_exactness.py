from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_batching_mechanism_subgap,
    build_cache_closure_rung,
    build_cache_continuous_batching_feasibility,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_pre_gate_admission_hook_exactness,
    build_cache_pre_gate_cohort_window_feasibility,
    build_cache_repeatability_evidence,
    build_cache_request_aggregation_window_exactness,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    cache_pre_gate_admission_hook_exactness_to_dict,
)
from owlmlx.cache_pre_gate_admission_hook_harness import (
    PreGateAdmissionHookHarnessResult,
)


def test_cache_pre_gate_admission_hook_exactness_defaults_to_unresolved() -> None:
    payload = cache_pre_gate_admission_hook_exactness_to_dict(
        build_cache_pre_gate_admission_hook_exactness()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_pre_gate_admission_hook_exactness"
    )
    assert payload["summary"]["exactness_rung"] == "admission_hook_unresolved"


def test_cache_pre_gate_admission_hook_exactness_freezes_exact_hook_absence() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "residency": False,
                    "reuse": True,
                    "eviction": False,
                },
            }
        }
    }
    repeatability = build_cache_repeatability_evidence([], backend_status=backend_status)
    closure = build_cache_closure_rung(repeatability=repeatability)
    counter_gap = build_cache_counter_gap(
        closure=closure,
        backend_observations=backend_status["detail"]["cache_runtime_observations"],
    )
    counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
    split = build_cache_scheduler_turboquant_split(
        counter_feasibility=counter_feasibility,
        scheduler=closure.scheduler,
        turboquant=closure.turboquant,
    )
    floor_gap = build_cache_scheduler_floor_gap(split=split)
    backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
    branch_selection = build_cache_scheduler_branch_selection(
        scheduler_backlog=backlog
    )
    feasibility = build_cache_continuous_batching_feasibility(
        branch_selection=branch_selection
    )
    mechanism_subgap = build_cache_batching_mechanism_subgap(
        feasibility=feasibility
    )
    aggregation_exactness = build_cache_request_aggregation_window_exactness(
        mechanism_subgap=mechanism_subgap
    )
    cohort_window_feasibility = build_cache_pre_gate_cohort_window_feasibility(
        aggregation_exactness=aggregation_exactness
    )

    payload = cache_pre_gate_admission_hook_exactness_to_dict(
        build_cache_pre_gate_admission_hook_exactness(
            cohort_window_feasibility=cohort_window_feasibility
        )
    )

    assert payload["summary"]["exactness_rung"] == "admission_hook_blocker_exact"
    assert (
        payload["admission_hook"]["admission_hook_status"]
        == "no_bounded_hook_before_gate_claim"
    )
    assert (
        payload["admission_hook"]["owned_boundary_status"]
        == "whole_request_gate_claim_is_first_runtime_owned_boundary"
    )
    assert "max_concurrent_1_after_gate_claim" in payload["safety_invariants"]


def test_cache_pre_gate_admission_hook_exactness_revalidates_after_structural_ingress() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "residency": False,
                    "reuse": True,
                    "eviction": False,
                },
            }
        }
    }
    repeatability = build_cache_repeatability_evidence([], backend_status=backend_status)
    closure = build_cache_closure_rung(repeatability=repeatability)
    counter_gap = build_cache_counter_gap(
        closure=closure,
        backend_observations=backend_status["detail"]["cache_runtime_observations"],
    )
    counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
    split = build_cache_scheduler_turboquant_split(
        counter_feasibility=counter_feasibility,
        scheduler=closure.scheduler,
        turboquant=closure.turboquant,
    )
    floor_gap = build_cache_scheduler_floor_gap(split=split)
    backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
    branch_selection = build_cache_scheduler_branch_selection(
        scheduler_backlog=backlog
    )
    feasibility = build_cache_continuous_batching_feasibility(
        branch_selection=branch_selection
    )
    mechanism_subgap = build_cache_batching_mechanism_subgap(
        feasibility=feasibility
    )
    aggregation_exactness = build_cache_request_aggregation_window_exactness(
        mechanism_subgap=mechanism_subgap
    )
    cohort_window_feasibility = build_cache_pre_gate_cohort_window_feasibility(
        aggregation_exactness=aggregation_exactness
    )
    hook_harness = PreGateAdmissionHookHarnessResult(
        runtime_owned_hook_present=True,
        hook_boundary="before_whole_request_gate_claim",
        hook_mode="bounded_runtime_owned_staging",
        cohort_window_status="idle",
        observed_cohort_count=0,
        observed_open_cohort_size=0,
        observed_peak_cohort_size=1,
        observed_total_cohorts_formed=1,
        aggregation_scope="pre_claim_window_only",
        observed_midflight_staged_count=1,
        observed_total_staged=2,
        observed_total_claimed=2,
        observed_total_discarded=0,
        staging_units=(
            "immutable_request_metadata_snapshot",
            "ticket_reservation_without_gate_claim",
            "bounded_pre_claim_admission_bookkeeping",
        ),
        preserved_post_claim_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        ),
    )

    payload = cache_pre_gate_admission_hook_exactness_to_dict(
        build_cache_pre_gate_admission_hook_exactness(
            cohort_window_feasibility=cohort_window_feasibility,
            hook_harness=hook_harness,
        )
    )

    assert payload["summary"]["exactness_rung"] == "admission_hook_blocker_exact"
    assert (
        payload["admission_hook"]["admission_hook_status"]
        == "bounded_hook_present_but_no_request_aggregation_window"
    )
    assert (
        payload["admission_hook"]["owned_boundary_status"]
        == "bounded_hook_precedes_whole_request_gate_claim_without_gate_transfer"
    )
    assert "ticketed_fifo_after_gate_claim" in payload["safety_invariants"]


def test_cache_pre_gate_admission_hook_exactness_revalidates_after_window_entry() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "residency": False,
                    "reuse": True,
                    "eviction": False,
                },
            }
        }
    }
    repeatability = build_cache_repeatability_evidence([], backend_status=backend_status)
    closure = build_cache_closure_rung(repeatability=repeatability)
    counter_gap = build_cache_counter_gap(
        closure=closure,
        backend_observations=backend_status["detail"]["cache_runtime_observations"],
    )
    counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
    split = build_cache_scheduler_turboquant_split(
        counter_feasibility=counter_feasibility,
        scheduler=closure.scheduler,
        turboquant=closure.turboquant,
    )
    floor_gap = build_cache_scheduler_floor_gap(split=split)
    backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
    branch_selection = build_cache_scheduler_branch_selection(
        scheduler_backlog=backlog
    )
    feasibility = build_cache_continuous_batching_feasibility(
        branch_selection=branch_selection
    )
    mechanism_subgap = build_cache_batching_mechanism_subgap(
        feasibility=feasibility
    )
    aggregation_exactness = build_cache_request_aggregation_window_exactness(
        mechanism_subgap=mechanism_subgap
    )
    cohort_window_feasibility = build_cache_pre_gate_cohort_window_feasibility(
        aggregation_exactness=aggregation_exactness
    )
    hook_harness = PreGateAdmissionHookHarnessResult(
        runtime_owned_hook_present=True,
        hook_boundary="before_whole_request_gate_claim",
        hook_mode="bounded_runtime_owned_cohort_window",
        cohort_window_status="open_for_join",
        observed_cohort_count=1,
        observed_open_cohort_size=2,
        observed_peak_cohort_size=2,
        observed_total_cohorts_formed=1,
        aggregation_scope="pre_claim_window_only",
        observed_midflight_staged_count=2,
        observed_total_staged=2,
        observed_total_claimed=2,
        observed_total_discarded=0,
        staging_units=(
            "immutable_request_metadata_snapshot",
            "ticket_reservation_without_gate_claim",
            "bounded_pre_claim_cohort_window_membership",
            "pre_claim_bounded_admission_bookkeeping",
        ),
        preserved_post_claim_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
        ),
    )

    payload = cache_pre_gate_admission_hook_exactness_to_dict(
        build_cache_pre_gate_admission_hook_exactness(
            cohort_window_feasibility=cohort_window_feasibility,
            hook_harness=hook_harness,
        )
    )

    assert payload["summary"]["exactness_rung"] == "admission_hook_blocker_exact"
    assert (
        payload["admission_hook"]["admission_hook_status"]
        == "bounded_request_aggregation_window_present_before_gate_claim"
    )
    assert (
        payload["admission_hook"]["owned_boundary_status"]
        == "bounded_cohort_window_precedes_whole_request_gate_claim_without_gate_transfer"
    )


def test_cache_pre_gate_admission_hook_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_pre_gate_admission_hook_exactness.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
