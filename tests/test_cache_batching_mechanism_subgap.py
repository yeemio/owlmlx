from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_batching_mechanism_subgap,
    build_cache_closure_rung,
    build_cache_continuous_batching_feasibility,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_repeatability_evidence,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    cache_batching_mechanism_subgap_to_dict,
)


def test_cache_batching_mechanism_subgap_defaults_to_unresolved() -> None:
    payload = cache_batching_mechanism_subgap_to_dict(
        build_cache_batching_mechanism_subgap()
    )

    assert payload["contract"]["surface"] == "owlmlx.cache_batching_mechanism_subgap"
    assert payload["summary"]["subgap_rung"] == "mechanism_subgap_unresolved"


def test_cache_batching_mechanism_subgap_selects_request_aggregation_window() -> None:
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

    payload = cache_batching_mechanism_subgap_to_dict(
        build_cache_batching_mechanism_subgap(feasibility=feasibility)
    )

    assert payload["summary"]["subgap_rung"] == "mechanism_subgap_exact"
    assert payload["selected_mechanism"]["mechanism"] == "request_aggregation_window"
    assert (
        payload["mechanism_statuses"]["shared_prefill_batch_step"]
        == "blocked_by_missing_request_aggregation_window"
    )
    assert (
        payload["mechanism_statuses"]["interleaved_decode_scheduler"]
        == "blocked_by_missing_request_aggregation_window_and_full_session_stream_hold"
    )


def test_cache_batching_mechanism_subgap_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_batching_mechanism_subgap.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
