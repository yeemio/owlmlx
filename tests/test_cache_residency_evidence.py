from __future__ import annotations

from pathlib import Path

from owlmlx import (
    CacheFlags,
    build_cache_residency_evidence,
    cache_residency_evidence_to_dict,
)
from owlmlx.serving import GenerationGate


def test_cache_residency_evidence_defaults_to_no_runtime_evidence() -> None:
    evidence = build_cache_residency_evidence()
    payload = cache_residency_evidence_to_dict(evidence)

    assert payload["contract"]["surface"] == "owlmlx.cache_residency_evidence"
    assert payload["summary"]["status"] == "partial"
    assert payload["summary"]["evidence_status"] == "no_runtime_evidence"
    assert payload["scheduler_activity"]["requests_served"] == 0


def test_cache_residency_evidence_marks_configuration_only() -> None:
    evidence = build_cache_residency_evidence(
        configured_flags=CacheFlags(hot_cache_max_size="8GB"),
        runtime_profile="unknown",
    )
    payload = cache_residency_evidence_to_dict(evidence)

    assert payload["summary"]["evidence_status"] == "configuration_only"
    assert "cache profile visibility exists" in payload["summary"]["blocked_reason"]


def test_cache_residency_evidence_marks_profile_active_under_load() -> None:
    gate = GenerationGate()
    gate.execute(lambda: "warm")

    evidence = build_cache_residency_evidence(
        gate=gate,
        configured_flags=CacheFlags(hot_cache_max_size="8GB"),
        runtime_profile="cache-enabled",
        runtime_flags={"hot_cache_max_size": "8GB"},
    )
    payload = cache_residency_evidence_to_dict(evidence)

    assert payload["summary"]["evidence_status"] == "profile_active_under_load"
    assert payload["scheduler_activity"]["requests_served"] == 1


def test_cache_residency_evidence_marks_residency_signal_visible() -> None:
    evidence = build_cache_residency_evidence(
        runtime_profile="cache-enabled",
        metrics={"entries": 3, "resident_bytes": 1024},
    )
    payload = cache_residency_evidence_to_dict(evidence)

    assert payload["summary"]["evidence_status"] == "residency_signal_visible"
    assert payload["residency_metrics"]["entries"] == 3
    assert "explicit reuse evidence is still missing" in payload["summary"]["blocked_reason"]


def test_cache_residency_evidence_marks_reuse_signal_visible() -> None:
    evidence = build_cache_residency_evidence(
        runtime_profile="cache-enabled",
        metrics={"reuse_events": 2, "hit_count": 5},
    )
    payload = cache_residency_evidence_to_dict(evidence)

    assert payload["summary"]["evidence_status"] == "reuse_signal_visible"
    assert payload["residency_metrics"]["reuse_events"] == 2
    assert payload["residency_metrics"]["hit_count"] == 5


def test_cache_residency_evidence_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__).parents[1]
        .joinpath("owlmlx", "cache_residency_evidence.py")
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
