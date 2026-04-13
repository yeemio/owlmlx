from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_repeatability_evidence,
    build_cache_turboquant_preconditions_gap,
    build_turboquant_readiness,
    cache_turboquant_preconditions_gap_to_dict,
)


def test_cache_turboquant_preconditions_gap_defaults_to_exact_blocker() -> None:
    payload = cache_turboquant_preconditions_gap_to_dict(
        build_cache_turboquant_preconditions_gap()
    )

    assert payload["contract"]["surface"] == "owlmlx.cache_turboquant_preconditions_gap"
    assert payload["summary"]["preconditions_rung"] == "preconditions_exact"
    assert "bits_in_cache_key" in payload["missing_preconditions"]


def test_cache_turboquant_preconditions_gap_marks_satisfied_when_safety_passes() -> None:
    repeatability = build_cache_repeatability_evidence([])
    readiness = build_turboquant_readiness(
        bits_in_cache_key=True,
        invalidates_on_config_toggle=True,
        runtime_verified=True,
        repeatability=repeatability,
    )
    payload = cache_turboquant_preconditions_gap_to_dict(
        build_cache_turboquant_preconditions_gap(readiness=readiness)
    )

    assert payload["summary"]["preconditions_rung"] == "preconditions_satisfied"
    assert payload["missing_preconditions"] == []


def test_cache_turboquant_preconditions_gap_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "cache_turboquant_preconditions_gap.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
