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
