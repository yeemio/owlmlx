from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_closure_rung,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_repeatability_evidence,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    cache_scheduler_branch_selection_to_dict,
)


def test_cache_scheduler_branch_selection_defaults_to_unresolved() -> None:
    payload = cache_scheduler_branch_selection_to_dict(
        build_cache_scheduler_branch_selection()
    )

    assert payload["contract"]["surface"] == "owlmlx.cache_scheduler_branch_selection"
    assert payload["summary"]["selection_rung"] == "branch_selection_unresolved"


def test_cache_scheduler_branch_selection_picks_continuous_batching_first() -> None:
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

    payload = cache_scheduler_branch_selection_to_dict(
        build_cache_scheduler_branch_selection(scheduler_backlog=backlog)
    )

    assert payload["summary"]["selection_rung"] == "branch_selection_exact"
    assert payload["selected_branch"]["branch"] == "continuous_batching"
    assert payload["selected_branch"]["status"] == "locally_reducible_on_current_path"
    assert payload["secondary_branch"]["branch"] == "multi_worker_scheduler_depth"
    assert payload["secondary_branch"]["status"] == "safety_revalidation_required"


def test_cache_scheduler_branch_selection_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_scheduler_branch_selection.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
