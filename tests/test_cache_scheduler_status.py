from __future__ import annotations

from pathlib import Path

from owlmlx import (
    CacheFlags,
    build_cache_scheduler_status,
    cache_scheduler_status_to_dict,
)
from owlmlx.serving import GenerationGate


def test_cache_scheduler_status_defaults_to_partial_truth_only() -> None:
    status = build_cache_scheduler_status()
    payload = cache_scheduler_status_to_dict(status)

    assert payload["contract"]["surface"] == "owlmlx.cache_scheduler_status"
    assert payload["contract"]["version"] == "phase45"
    assert payload["summary"]["status"] == "partial"
    assert payload["summary"]["scheduler_depth"] == "serial_single_worker"
    assert payload["summary"]["cache_depth"] == "truth_only"
    assert payload["scheduler"]["mode"] == "serial_single_worker"
    assert payload["scheduler"]["continuous_batching"] is False


def test_cache_scheduler_status_marks_profile_visible_when_cache_flags_exist() -> None:
    status = build_cache_scheduler_status(
        configured_flags=CacheFlags(hot_cache_max_size="8GB"),
        runtime_profile="cache-enabled",
        runtime_flags={"hot_cache_max_size": "8GB"},
    )
    payload = cache_scheduler_status_to_dict(status)

    assert payload["summary"]["cache_depth"] == "profile_visible"
    assert payload["cache_profile"]["configured_profile"] == "cache-enabled"
    assert payload["cache_profile"]["runtime_profile"] == "cache-enabled"
    assert payload["cache_profile"]["restart_required"] is False


def test_cache_scheduler_status_embeds_generation_gate_counters() -> None:
    gate = GenerationGate()
    gate.execute(lambda: "warm")

    status = build_cache_scheduler_status(gate=gate)
    payload = cache_scheduler_status_to_dict(status)

    assert payload["scheduler"]["total_served"] == 1
    assert payload["scheduler"]["max_concurrent"] == 1
    assert payload["scheduler"]["queue_discipline"] == "serial"


def test_cache_scheduler_status_carries_turboquant_safety_truth() -> None:
    status = build_cache_scheduler_status(
        bits_in_cache_key=True,
        invalidates_on_config_toggle=True,
        runtime_verified=True,
    )
    payload = cache_scheduler_status_to_dict(status)

    assert payload["turboquant_cache_safety"]["can_activate"] is True
    assert payload["turboquant_cache_safety"]["cache_safety_risk"] == "LOW"
    assert payload["summary"]["recommended_next_step"] == (
        "add runtime-owned cache residency/reuse evidence before claiming deeper cache/scheduler parity"
    )


def test_cache_scheduler_status_module_has_no_platform_dependency() -> None:
    source = (
        Path(__file__).parents[1].joinpath("owlmlx", "cache_scheduler_status.py").read_text()
    )
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
