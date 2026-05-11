from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_batching_mechanism_subgap,
    build_cache_closure_rung,
    build_cache_continuous_batching_feasibility,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_repeatability_evidence,
    build_cache_request_aggregation_window_exactness,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    cache_request_aggregation_window_exactness_to_dict,
)
from owlmlx.cache_child_exchange_aggregated_dispatch_harness import (
    CacheChildExchangeAggregatedDispatchHarnessResult,
)
from owlmlx.cache_cohort_to_child_exchange_handoff_harness import (
    CacheCohortToChildExchangeHandoffHarnessResult,
)
from owlmlx.cache_pre_gate_admission_hook_harness import (
    PreGateAdmissionHookHarnessResult,
)


def test_cache_request_aggregation_window_exactness_defaults_to_unresolved() -> None:
    payload = cache_request_aggregation_window_exactness_to_dict(
        build_cache_request_aggregation_window_exactness()
    )

    assert (
        payload["contract"]["surface"]
        == "owlmlx.cache_request_aggregation_window_exactness"
    )
    assert payload["summary"]["exactness_rung"] == "aggregation_window_unresolved"


def test_cache_request_aggregation_window_exactness_freezes_ingress_blocker() -> None:
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

    payload = cache_request_aggregation_window_exactness_to_dict(
        build_cache_request_aggregation_window_exactness(
            mechanism_subgap=mechanism_subgap
        )
    )

    assert payload["summary"]["exactness_rung"] == "aggregation_window_blocker_exact"
    assert (
        payload["ingress"]["ingress_window_status"]
        == "missing_pre_gate_admission_window"
    )
    assert (
        payload["ingress"]["admission_boundary_status"]
        == "generation_gate_claims_session_before_cohort_formation"
    )
    assert (
        payload["dependencies"]["child_dependency_status"]
        == "single_request_per_child_exchange_blocks_aggregated_dispatch"
    )


def test_cache_request_aggregation_window_exactness_revalidates_after_window_entry() -> None:
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

    payload = cache_request_aggregation_window_exactness_to_dict(
        build_cache_request_aggregation_window_exactness(
            mechanism_subgap=mechanism_subgap,
            hook_harness=hook_harness,
        )
    )

    assert payload["summary"]["exactness_rung"] == "aggregation_window_blocker_exact"
    assert (
        payload["ingress"]["ingress_window_status"]
        == "bounded_pre_gate_admission_window_present"
    )
    assert (
        payload["ingress"]["admission_boundary_status"]
        == "cohort_forms_before_generation_gate_claim"
    )
    assert (
        payload["dependencies"]["stream_dependency_status"]
        == "stream_session_holds_gate_until_completion"
    )


def test_cache_request_aggregation_window_exactness_revalidates_after_child_exchange_widening() -> None:
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
    hook_harness = PreGateAdmissionHookHarnessResult(
        runtime_owned_hook_present=True,
        hook_boundary="before_whole_request_gate_claim",
        hook_mode="bounded_runtime_owned_cohort_window",
        cohort_window_status="closed_waiting_gate_claim",
        observed_cohort_count=1,
        observed_open_cohort_size=0,
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
    child_harness = CacheChildExchangeAggregatedDispatchHarnessResult(
        aggregated_dispatch_visible=True,
        child_exchange_mode="aggregated_non_stream_child_exchange_visible",
        exchange_count=1,
        batch_size=2,
        aggregated_request_count=2,
        max_aggregated_batch_size=2,
        pid=123,
        stream_secondary_status="stream_session_holds_gate_until_completion",
        texts=("a :: child", "b :: child"),
    )

    payload = cache_request_aggregation_window_exactness_to_dict(
        build_cache_request_aggregation_window_exactness(
            mechanism_subgap=mechanism_subgap,
            hook_harness=hook_harness,
            child_exchange_harness=child_harness,
        )
    )

    assert payload["summary"]["exactness_rung"] == "aggregation_window_blocker_exact"
    assert (
        payload["dependencies"]["child_dependency_status"]
        == "aggregated_non_stream_child_exchange_visible"
    )
    assert (
        payload["dependencies"]["stream_dependency_status"]
        == "stream_session_holds_gate_until_completion"
    )


def test_cache_request_aggregation_window_exactness_advances_after_main_path_handoff() -> None:
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
    hook_harness = PreGateAdmissionHookHarnessResult(
        runtime_owned_hook_present=True,
        hook_boundary="before_whole_request_gate_claim",
        hook_mode="bounded_runtime_owned_cohort_window",
        cohort_window_status="closed_waiting_gate_claim",
        observed_cohort_count=1,
        observed_open_cohort_size=0,
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
    child_harness = CacheChildExchangeAggregatedDispatchHarnessResult(
        aggregated_dispatch_visible=True,
        child_exchange_mode="aggregated_non_stream_child_exchange_visible",
        exchange_count=1,
        batch_size=2,
        aggregated_request_count=2,
        max_aggregated_batch_size=2,
        pid=123,
        stream_secondary_status="stream_session_holds_gate_until_completion",
        texts=("a :: child", "b :: child"),
    )
    handoff_harness = CacheCohortToChildExchangeHandoffHarnessResult(
        cohort_handoff_visible=True,
        handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
        child_exchange_mode="aggregated_non_stream_child_exchange_visible",
        aggregated_batch_count=1,
        aggregated_request_count=2,
        max_aggregated_batch_size=2,
        gate_total_served=2,
        gate_total_queued=2,
        max_concurrent=1,
        queue_discipline="serial",
        handoff_request_count=2,
        stream_secondary_status="stream_session_holds_gate_until_completion",
        texts=("a :: child", "b :: child"),
    )

    payload = cache_request_aggregation_window_exactness_to_dict(
        build_cache_request_aggregation_window_exactness(
            mechanism_subgap=mechanism_subgap,
            hook_harness=hook_harness,
            child_exchange_harness=child_harness,
            handoff_harness=handoff_harness,
        )
    )

    assert payload["summary"]["exactness_rung"] == "aggregation_window_blocker_exact"
    assert (
        payload["dependencies"]["child_dependency_status"]
        == "cohort_handed_off_to_aggregated_child_exchange_visible"
    )
    assert (
        payload["dependencies"]["stream_dependency_status"]
        == "stream_session_holds_gate_until_completion"
    )


def test_cache_request_aggregation_window_exactness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_request_aggregation_window_exactness.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
