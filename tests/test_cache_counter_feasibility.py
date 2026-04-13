from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_closure_rung,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_repeatability_evidence,
    cache_counter_feasibility_to_dict,
)


def test_cache_counter_feasibility_defaults_to_unresolved() -> None:
    payload = cache_counter_feasibility_to_dict(build_cache_counter_feasibility())

    assert payload["contract"]["surface"] == "owlmlx.cache_counter_feasibility"
    assert payload["summary"]["feasibility_rung"] == "counter_ownership_unresolved"
    assert payload["next_cache_subgap"]["next_cache_subgap"] == "counter_boundary"


def test_cache_counter_feasibility_marks_counter_ownership_exact() -> None:
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

    payload = cache_counter_feasibility_to_dict(
        build_cache_counter_feasibility(counter_gap=counter_gap)
    )

    assert payload["summary"]["feasibility_rung"] == "counter_ownership_exact"
    assert payload["counter_ownership"] == {
        "reuse_counter": "runtime_owned_visible",
        "residency_counter": "not_runtime_owned_on_current_path",
        "eviction_counter": "not_runtime_owned_on_current_path",
    }
    assert payload["next_cache_subgap"]["next_cache_subgap"] == "scheduler_depth"


def test_cache_counter_feasibility_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_counter_feasibility.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
