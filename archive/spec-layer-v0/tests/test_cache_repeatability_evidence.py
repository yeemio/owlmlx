from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_cache_repeatability_evidence,
    build_cache_residency_evidence,
    cache_repeatability_evidence_to_dict,
)
from owlmlx.serving import GenerationGate


def _run(*, status: str, served: int = 1):
    gate = GenerationGate()
    for _ in range(served):
        gate.execute(lambda: None)
    if status == "configuration_only":
        return build_cache_residency_evidence(
            gate=gate,
            configured_flags={"hot_cache_max_size": "8GB"},
            runtime_profile="unknown",
        )
    if status == "profile_active_under_load":
        return build_cache_residency_evidence(
            gate=gate,
            configured_flags={"hot_cache_max_size": "8GB"},
            runtime_profile="cache-enabled",
            runtime_flags={"hot_cache_max_size": "8GB"},
        )
    if status == "residency_signal_visible":
        return build_cache_residency_evidence(
            gate=gate,
            runtime_profile="cache-enabled",
            metrics={"entries": 2},
        )
    if status == "reuse_signal_visible":
        return build_cache_residency_evidence(
            gate=gate,
            runtime_profile="cache-enabled",
            metrics={"reuse_events": 2, "hit_count": 4},
        )
    if status == "repeat_eviction_visible":
        return build_cache_residency_evidence(
            gate=gate,
            runtime_profile="cache-enabled",
            metrics={"reuse_events": 2, "hit_count": 4, "eviction_events": 1},
        )
    return build_cache_residency_evidence(gate=gate)


def test_cache_repeatability_defaults_to_no_repeat_runs() -> None:
    evidence = build_cache_repeatability_evidence([])
    payload = cache_repeatability_evidence_to_dict(evidence)

    assert payload["contract"]["surface"] == "owlmlx.cache_repeatability_evidence"
    assert payload["summary"]["repeatability_status"] == "no_repeat_runs"
    assert payload["run_counts"]["runs_observed"] == 0


def test_cache_repeatability_marks_repeat_profile_active_under_load() -> None:
    evidence = build_cache_repeatability_evidence(
        [_run(status="profile_active_under_load"), _run(status="profile_active_under_load")]
    )
    payload = cache_repeatability_evidence_to_dict(evidence)

    assert payload["summary"]["repeatability_status"] == "repeat_profile_active_under_load"
    assert payload["run_counts"]["runs_with_runtime_activity"] == 2


def test_cache_repeatability_marks_repeat_residency_visible() -> None:
    evidence = build_cache_repeatability_evidence(
        [_run(status="residency_signal_visible"), _run(status="residency_signal_visible")]
    )
    payload = cache_repeatability_evidence_to_dict(evidence)

    assert payload["summary"]["repeatability_status"] == "repeat_residency_visible"
    assert payload["run_counts"]["runs_with_residency_signal"] == 2


def test_cache_repeatability_marks_repeat_reuse_visible() -> None:
    evidence = build_cache_repeatability_evidence(
        [_run(status="reuse_signal_visible"), _run(status="reuse_signal_visible")]
    )
    payload = cache_repeatability_evidence_to_dict(evidence)

    assert payload["summary"]["repeatability_status"] == "repeat_reuse_visible"
    assert payload["run_counts"]["runs_with_reuse_signal"] == 2


def test_cache_repeatability_marks_repeat_eviction_visible() -> None:
    evidence = build_cache_repeatability_evidence(
        [_run(status="repeat_eviction_visible"), _run(status="reuse_signal_visible")]
    )
    payload = cache_repeatability_evidence_to_dict(evidence)

    assert payload["summary"]["repeatability_status"] == "repeat_eviction_visible"
    assert payload["run_counts"]["runs_with_eviction_signal"] == 1


def test_cache_repeatability_consumes_real_runtime_activity_observation() -> None:
    backend_status = {
        "detail": {
            "cache_runtime_observations": {
                "persistent_child_reuse_visible": True,
                "reuse_counter": 1,
                "cache_counter_visibility": {
                    "reuse": True,
                },
                "repeated_generation_models": ["model-a"],
            }
        }
    }

    evidence = build_cache_repeatability_evidence([], backend_status=backend_status)
    payload = cache_repeatability_evidence_to_dict(evidence)

    assert payload["summary"]["repeatability_status"] == "repeat_reuse_visible"
    assert payload["summary"]["highest_evidence_status"] == "reuse_signal_visible"
    assert payload["run_counts"]["backend_reuse_counter"] == 1
    assert payload["run_counts"]["runtime_path_observed"] is True
    assert payload["run_counts"]["repeated_generation_models"] == ["model-a"]


def test_cache_repeatability_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__).parents[1]
        .joinpath("owlmlx", "cache_repeatability_evidence.py")
        .read_text()
    )
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
