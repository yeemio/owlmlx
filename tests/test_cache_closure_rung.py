from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_closure_rung,
    build_cache_repeatability_evidence,
    build_cache_residency_evidence,
    build_turboquant_readiness,
    cache_closure_rung_to_dict,
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
            metrics={"entries": 2},
        )
    ]
    return build_cache_repeatability_evidence(runs)


def test_cache_closure_rung_defaults_to_truth_only() -> None:
    payload = cache_closure_rung_to_dict(build_cache_closure_rung())

    assert payload["contract"]["surface"] == "owlmlx.cache_closure_rung"
    assert payload["summary"]["closure_rung"] == "truth_only"


def test_cache_closure_rung_marks_evidence_visible() -> None:
    residency = build_cache_residency_evidence(
        runtime_profile="cache-enabled",
        metrics={"reuse_events": 1, "hit_count": 2},
    )

    payload = cache_closure_rung_to_dict(build_cache_closure_rung(residency=residency))

    assert payload["summary"]["closure_rung"] == "evidence_visible"


def test_cache_closure_rung_marks_repeatability_visible() -> None:
    repeatability = _repeatability("runtime_activity_visible_counter_gap")

    payload = cache_closure_rung_to_dict(
        build_cache_closure_rung(repeatability=repeatability)
    )

    assert payload["summary"]["closure_rung"] == "repeatability_visible"


def test_cache_closure_rung_marks_turboquant_safety_ready() -> None:
    repeatability = _repeatability("runtime_activity_visible_counter_gap")
    readiness = build_turboquant_readiness(
        bits_in_cache_key=True,
        invalidates_on_config_toggle=True,
        runtime_verified=True,
        repeatability=repeatability,
    )

    payload = cache_closure_rung_to_dict(
        build_cache_closure_rung(
            repeatability=repeatability,
            turboquant=readiness,
        )
    )

    assert payload["summary"]["closure_rung"] == "turboquant_safety_ready"


def test_cache_closure_rung_marks_partial_closure() -> None:
    repeatability = _repeatability("repeat_reuse_visible")
    readiness = build_turboquant_readiness(
        bits_in_cache_key=True,
        invalidates_on_config_toggle=True,
        runtime_verified=True,
        repeatability=repeatability,
    )

    payload = cache_closure_rung_to_dict(
        build_cache_closure_rung(
            repeatability=repeatability,
            turboquant=readiness,
        )
    )

    assert payload["summary"]["closure_rung"] == "partial_closure"


def test_cache_closure_rung_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath("owlmlx", "cache_closure_rung.py").read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
