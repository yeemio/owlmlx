from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_closure_rung,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_repeatability_evidence,
    build_cache_scheduler_turboquant_split,
    cache_scheduler_turboquant_split_to_dict,
)


def test_cache_scheduler_turboquant_split_defaults_to_unresolved() -> None:
    payload = cache_scheduler_turboquant_split_to_dict(
        build_cache_scheduler_turboquant_split()
    )

    assert payload["contract"]["surface"] == "owlmlx.cache_scheduler_turboquant_split"
    assert payload["summary"]["split_rung"] == "split_unresolved"
    assert payload["next_cache_branch"]["dominant_cache_branch"] == "counter_boundary"


def test_cache_scheduler_turboquant_split_marks_scheduler_depth_branch() -> None:
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

    payload = cache_scheduler_turboquant_split_to_dict(
        build_cache_scheduler_turboquant_split(
            counter_feasibility=counter_feasibility,
            scheduler=closure.scheduler,
            turboquant=closure.turboquant,
        )
    )

    assert payload["summary"]["split_rung"] == "split_exact"
    assert payload["scheduler_branch"]["scheduler_subgap"] == "serial_scheduler_exact"
    assert payload["turboquant_branch"]["turboquant_subgap"] == "safety_preconditions_exact"
    assert payload["next_cache_branch"]["dominant_cache_branch"] == "scheduler_depth"


def test_cache_scheduler_turboquant_split_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_scheduler_turboquant_split.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
