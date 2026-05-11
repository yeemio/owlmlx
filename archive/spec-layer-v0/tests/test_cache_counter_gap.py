from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_closure_rung,
    build_cache_counter_gap,
    build_cache_repeatability_evidence,
    cache_counter_gap_to_dict,
)


def test_cache_counter_gap_defaults_to_observation_gap_open() -> None:
    payload = cache_counter_gap_to_dict(build_cache_counter_gap())

    assert payload["contract"]["surface"] == "owlmlx.cache_counter_gap"
    assert payload["summary"]["counter_gap_rung"] == "observation_gap_open"
    assert payload["runtime_counters"]["missing_runtime_counters"] == [
        "residency_counter",
        "reuse_counter",
        "eviction_counter",
    ]


def test_cache_counter_gap_marks_counter_gap_exact() -> None:
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

    payload = cache_counter_gap_to_dict(
        build_cache_counter_gap(
            closure=closure,
            backend_observations=backend_status["detail"]["cache_runtime_observations"],
        )
    )

    assert payload["summary"]["counter_gap_rung"] == "counter_gap_exact"
    assert payload["observed_runtime_behavior"]["observed_runtime_behavior_frozen"] is True
    assert payload["runtime_counters"]["visible_runtime_counters"] == ["reuse_counter"]
    assert payload["runtime_counters"]["missing_runtime_counters"] == [
        "residency_counter",
        "eviction_counter",
    ]


def test_cache_counter_gap_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_counter_gap.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
