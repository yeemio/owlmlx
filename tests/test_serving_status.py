"""Tests for owlmlx.serving_status — large-weight path status builder."""

import time

from owlmlx.serving import GenerationGate
from owlmlx.serving_status import (
    build_large_weight_serving_status,
    merge_specimen_identity,
)


def _make_gate_with_one_served() -> GenerationGate:
    gate = GenerationGate()
    gate.execute(lambda: "warmup")
    return gate


def test_build_status_has_required_fields() -> None:
    """Status must contain all path-level required fields."""
    gate = GenerationGate()
    status = build_large_weight_serving_status(
        gate=gate,
        active_memory_bytes=52_000_000_000,
        peak_memory_bytes=55_000_000_000,
        memory_budget_gb=55.0,
    )
    assert status["status"] == "ok"
    assert status["runtime"] == "owlmlx"
    assert status["tier"] == "background"
    assert status["interactive_status"] == "background_only"
    assert status["lifecycle_mode"] == "manual_start"
    assert "memory" in status
    assert "generation" in status


def test_memory_utilization_calculated() -> None:
    """Memory utilization is active/budget ratio."""
    gate = GenerationGate()
    status = build_large_weight_serving_status(
        gate=gate,
        active_memory_bytes=int(27.5 * (1 << 30)),
        peak_memory_bytes=int(30 * (1 << 30)),
        memory_budget_gb=55.0,
    )
    assert status["memory"]["utilization"] == 0.5


def test_memory_utilization_zero_budget() -> None:
    """Zero budget yields None utilization, not division error."""
    gate = GenerationGate()
    status = build_large_weight_serving_status(
        gate=gate,
        active_memory_bytes=1_000_000,
        peak_memory_bytes=2_000_000,
        memory_budget_gb=0.0,
    )
    assert status["memory"]["utilization"] is None


def test_uptime_calculated_when_start_time_provided() -> None:
    """uptime_s appears only when start_time is given."""
    gate = GenerationGate()
    start = time.time() - 120
    status = build_large_weight_serving_status(
        gate=gate,
        active_memory_bytes=0,
        peak_memory_bytes=0,
        memory_budget_gb=55.0,
        start_time=start,
    )
    assert status["uptime_s"] >= 119


def test_uptime_absent_without_start_time() -> None:
    """uptime_s is not in status when start_time is omitted."""
    gate = GenerationGate()
    status = build_large_weight_serving_status(
        gate=gate,
        active_memory_bytes=0,
        peak_memory_bytes=0,
        memory_budget_gb=55.0,
    )
    assert "uptime_s" not in status


def test_generation_gate_status_embedded() -> None:
    """Generation gate status is embedded under 'generation' key."""
    gate = _make_gate_with_one_served()
    status = build_large_weight_serving_status(
        gate=gate,
        active_memory_bytes=0,
        peak_memory_bytes=0,
        memory_budget_gb=55.0,
    )
    gen = status["generation"]
    assert gen["total_served"] == 1
    assert gen["max_concurrent"] == 1
    assert gen["queue_discipline"] == "serial"


def test_extra_fields_merged() -> None:
    """Extra fields from caller are merged into the status dict."""
    gate = GenerationGate()
    status = build_large_weight_serving_status(
        gate=gate,
        active_memory_bytes=0,
        peak_memory_bytes=0,
        memory_budget_gb=55.0,
        extra={"port": 8014, "custom_flag": True},
    )
    assert status["port"] == 8014
    assert status["custom_flag"] is True


def test_merge_specimen_identity() -> None:
    """Specimen identity merges on top of base status."""
    gate = GenerationGate()
    base = build_large_weight_serving_status(
        gate=gate,
        active_memory_bytes=52_000_000_000,
        peak_memory_bytes=55_000_000_000,
        memory_budget_gb=55.0,
    )
    full = merge_specimen_identity(
        base,
        model="Kimi-K2.5-3bit",
        path_variant="expert-sharded",
        layers=61,
        layout="merged",
    )
    # Path-level fields preserved
    assert full["runtime"] == "owlmlx"
    assert full["generation"]["max_concurrent"] == 1
    # Specimen-specific fields added
    assert full["model"] == "Kimi-K2.5-3bit"
    assert full["path_variant"] == "expert-sharded"
    assert full["layers"] == 61
    assert full["layout"] == "merged"


def test_merge_does_not_mutate_base() -> None:
    """merge_specimen_identity returns a new dict, not mutate base."""
    gate = GenerationGate()
    base = build_large_weight_serving_status(
        gate=gate,
        active_memory_bytes=0,
        peak_memory_bytes=0,
        memory_budget_gb=55.0,
    )
    full = merge_specimen_identity(
        base,
        model="TestModel",
        path_variant="test-variant",
    )
    assert "model" not in base
    assert "model" in full


def test_custom_tier_and_lifecycle() -> None:
    """Non-default tier and lifecycle mode are respected."""
    gate = GenerationGate()
    status = build_large_weight_serving_status(
        gate=gate,
        active_memory_bytes=0,
        peak_memory_bytes=0,
        memory_budget_gb=55.0,
        tier="foreground",
        interactive_status="interactive",
        lifecycle_mode="auto_start",
    )
    assert status["tier"] == "foreground"
    assert status["interactive_status"] == "interactive"
    assert status["lifecycle_mode"] == "auto_start"
