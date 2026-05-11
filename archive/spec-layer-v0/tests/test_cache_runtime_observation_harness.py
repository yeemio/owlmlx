from __future__ import annotations

from pathlib import Path

from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)


def test_cache_runtime_observation_harness_exposes_active_runtime_repeatability() -> None:
    result = run_cache_runtime_observation_harness()

    assert result.backend_observations["persistent_child_reuse_visible"] is True
    assert result.backend_observations["reuse_counter"] == 1
    assert result.repeatability.repeatability_status == "repeat_reuse_visible"
    assert result.closure.closure_rung == "repeatability_visible"


def test_cache_runtime_observation_harness_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_runtime_observation_harness.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
