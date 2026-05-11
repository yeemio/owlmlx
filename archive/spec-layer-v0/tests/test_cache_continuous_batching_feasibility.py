from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_closure_rung,
    build_cache_continuous_batching_feasibility,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_repeatability_evidence,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    cache_continuous_batching_feasibility_to_dict,
)


def test_cache_continuous_batching_feasibility_defaults_to_unresolved() -> None:
    payload = cache_continuous_batching_feasibility_to_dict(
        build_cache_continuous_batching_feasibility()
    )

    assert payload["contract"]["surface"] == "owlmlx.cache_continuous_batching_feasibility"
    assert payload["summary"]["feasibility_rung"] == "feasibility_unresolved"


def test_cache_continuous_batching_feasibility_freezes_exact_blocker() -> None:
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

    payload = cache_continuous_batching_feasibility_to_dict(
        build_cache_continuous_batching_feasibility(
            branch_selection=branch_selection
        )
    )

    assert payload["summary"]["feasibility_rung"] == "feasibility_blocker_exact"
    assert payload["runtime_path"]["generation_gate_mode"] == "serial_ticketed_fifo_whole_request"
    assert payload["runtime_path"]["child_exchange_mode"] == "single_request_per_child_exchange"
    assert payload["runtime_path"]["stream_holds_full_session"] is True
    assert "request_aggregation_window" in payload["missing_batching_mechanisms"]
    assert "interleaved_decode_scheduler" in payload["missing_batching_mechanisms"]


def test_cache_continuous_batching_feasibility_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_continuous_batching_feasibility.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
