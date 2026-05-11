from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_closure_rung,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_repeatability_evidence,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_turboquant_split,
    cache_scheduler_floor_gap_to_dict,
)


def test_cache_scheduler_floor_gap_defaults_to_unresolved() -> None:
    payload = cache_scheduler_floor_gap_to_dict(build_cache_scheduler_floor_gap())

    assert payload["contract"]["surface"] == "owlmlx.cache_scheduler_floor_gap"
    assert payload["summary"]["floor_rung"] == "floor_unresolved"
    assert payload["scheduler_floor"]["queue_discipline"] == "serial"


def test_cache_scheduler_floor_gap_marks_serial_floor_exact() -> None:
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

    payload = cache_scheduler_floor_gap_to_dict(
        build_cache_scheduler_floor_gap(split=split)
    )

    assert payload["summary"]["floor_rung"] == "serial_floor_exact"
    assert payload["scheduler_floor"]["max_concurrent"] == 1
    assert payload["next_step"]["dominant_cache_branch"] == "scheduler_depth"


def test_cache_scheduler_floor_gap_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_scheduler_floor_gap.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
