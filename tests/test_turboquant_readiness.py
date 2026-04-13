from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_repeatability_evidence,
    build_cache_residency_evidence,
    build_turboquant_readiness,
    turboquant_readiness_to_dict,
)
from owlmlx.serving import GenerationGate


def _repeatability(status: str):
    gate = GenerationGate()
    gate.execute(lambda: None)
    gate.execute(lambda: None)

    if status == "runtime_activity_visible_counter_gap":
        return build_cache_repeatability_evidence(
            [],
            backend_status={
                "detail": {
                    "cache_runtime_observations": {
                        "persistent_child_reuse_visible": True,
                        "repeated_generation_models": ["model-a"],
                    }
                }
            },
        )
    if status == "repeat_profile_active_under_load":
        runs = [
            build_cache_residency_evidence(
                gate=gate,
                configured_flags={"hot_cache_max_size": "8GB"},
                runtime_profile="cache-enabled",
                runtime_flags={"hot_cache_max_size": "8GB"},
            ),
            build_cache_residency_evidence(
                gate=gate,
                configured_flags={"hot_cache_max_size": "8GB"},
                runtime_profile="cache-enabled",
                runtime_flags={"hot_cache_max_size": "8GB"},
            ),
        ]
        return build_cache_repeatability_evidence(runs)
    if status == "repeat_reuse_visible":
        runs = [
            build_cache_residency_evidence(
                gate=gate,
                runtime_profile="cache-enabled",
                metrics={"reuse_events": 2, "hit_count": 4},
            ),
            build_cache_residency_evidence(
                gate=gate,
                runtime_profile="cache-enabled",
                metrics={"reuse_events": 3, "hit_count": 6},
            ),
        ]
        return build_cache_repeatability_evidence(runs)
    runs = [
        build_cache_residency_evidence(
            gate=gate,
            runtime_profile="cache-enabled",
            metrics={"reuse_events": 2, "hit_count": 4, "eviction_events": 1},
        ),
        build_cache_residency_evidence(
            gate=gate,
            runtime_profile="cache-enabled",
            metrics={"reuse_events": 3, "hit_count": 6},
        ),
    ]
    return build_cache_repeatability_evidence(runs)


def test_turboquant_readiness_defaults_to_safety_blocked() -> None:
    readiness = build_turboquant_readiness()
    payload = turboquant_readiness_to_dict(readiness)

    assert payload["contract"]["surface"] == "owlmlx.turboquant_readiness"
    assert payload["summary"]["status"] == "safety_blocked"
    assert payload["summary"]["ready"] is False
    assert payload["turboquant_cache_safety"]["can_activate"] is False


def test_turboquant_readiness_requires_repeatability_evidence_even_when_safe() -> None:
    readiness = build_turboquant_readiness(
        bits_in_cache_key=True,
        invalidates_on_config_toggle=True,
        runtime_verified=True,
        repeatability=_repeatability("runtime_activity_visible_counter_gap"),
    )
    payload = turboquant_readiness_to_dict(readiness)

    assert payload["summary"]["status"] == "evidence_blocked"
    assert payload["summary"]["ready"] is False
    assert payload["cache_repeatability"]["repeatability_status"] == (
        "runtime_activity_visible_counter_gap"
    )


def test_turboquant_readiness_can_consume_serialized_repeatability() -> None:
    repeatability = turboquant_readiness_to_dict(
        build_turboquant_readiness(
            bits_in_cache_key=True,
            invalidates_on_config_toggle=True,
            runtime_verified=True,
            repeatability=_repeatability("repeat_reuse_visible"),
        )
    )["cache_repeatability"]
    readiness = build_turboquant_readiness(
        bits_in_cache_key=True,
        invalidates_on_config_toggle=True,
        runtime_verified=True,
        repeatability={
            "summary": repeatability,
            "run_counts": {
                "runs_observed": 2,
                "runs_with_runtime_activity": 2,
                "runs_with_residency_signal": 2,
                "runs_with_reuse_signal": 2,
                "runs_with_eviction_signal": 0,
                "runtime_path_observed": False,
                "repeated_generation_models": [],
            },
        },
    )
    payload = turboquant_readiness_to_dict(readiness)

    assert payload["summary"]["status"] == "ready_for_controlled_validation"
    assert payload["summary"]["ready"] is True


def test_turboquant_readiness_ready_for_controlled_validation_on_repeat_reuse() -> None:
    readiness = build_turboquant_readiness(
        bits_in_cache_key=True,
        invalidates_on_config_toggle=True,
        runtime_verified=True,
        repeatability=_repeatability("repeat_reuse_visible"),
    )
    payload = turboquant_readiness_to_dict(readiness)

    assert payload["summary"]["status"] == "ready_for_controlled_validation"
    assert payload["summary"]["ready"] is True
    assert payload["cache_repeatability"]["repeatability_status"] == "repeat_reuse_visible"


def test_turboquant_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath("owlmlx", "turboquant_readiness.py").read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
