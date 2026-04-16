from __future__ import annotations

import asyncio
from pathlib import Path

from owlmlx import (
    build_multi_model_governance_controls,
    multi_model_governance_controls_to_dict,
)
from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import FakeBackend, RuntimeKernel


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=14.0,
        warning_threshold_gb=12.0,
    )


def test_multi_model_governance_controls_default_to_controls_visible() -> None:
    payload = multi_model_governance_controls_to_dict(
        build_multi_model_governance_controls()
    )

    assert payload["contract"]["surface"] == "owlmlx.multi_model_governance_controls"
    assert payload["summary"]["controls_rung"] == "controls_visible"
    assert payload["control_presence"]["ttl_supported"] is False


def test_multi_model_governance_controls_mark_transition_evidence_visible() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")

    payload = multi_model_governance_controls_to_dict(
        build_multi_model_governance_controls(kernel.status_dict())
    )

    assert payload["summary"]["controls_rung"] == "transition_evidence_visible"
    assert payload["transition_evidence"]["transition_history_visible"] is True


def test_multi_model_governance_controls_mark_partial_closure() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")
    kernel.load_model("model-b")
    explicit = asyncio.run(kernel.generate("hello-explicit", model_id="model-a"))
    unload = kernel.unload_model("model-b")
    restart = kernel.restart_model("model-a")

    payload = multi_model_governance_controls_to_dict(
        build_multi_model_governance_controls(kernel.status_dict())
    )

    assert payload["summary"]["controls_rung"] == "partial_closure"
    assert payload["transition_evidence"]["active_reassignment_visible"] is True
    assert payload["transition_evidence"]["restart_restore_visible"] is True


def test_multi_model_governance_controls_reflect_runtime_pinning_support() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")
    kernel.pin_model("model-a")

    payload = multi_model_governance_controls_to_dict(
        build_multi_model_governance_controls(kernel.status_dict())
    )

    assert payload["control_presence"]["pinning_supported"] is True
    assert payload["control_presence"]["ttl_supported"] is True
    assert payload["summary"]["blocked_reason"] == (
        "owlmlx now owns runtime pinning and TTL policy, but eviction-history governance remains absent"
    )


def test_multi_model_governance_controls_reflect_runtime_ttl_support() -> None:
    state = {"now": 100.0}

    def clock() -> float:
        return float(state["now"])

    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0),
        profile=_profile(),
        clock=clock,
    )
    kernel.load_model("model-a")
    kernel.load_model("model-b")
    kernel.pin_model("model-a")
    kernel.set_model_ttl("model-a", 30.0)
    kernel.set_model_ttl("model-b", 30.0)

    payload = multi_model_governance_controls_to_dict(
        build_multi_model_governance_controls(kernel.status_dict())
    )

    assert payload["control_presence"]["ttl_supported"] is True
    assert payload["summary"]["blocked_reason"] == (
        "owlmlx now owns runtime pinning and TTL policy, but eviction-history governance remains absent"
    )


def test_multi_model_governance_controls_reflect_eviction_history_closure() -> None:
    state = {"now": 100.0}

    def clock() -> float:
        return float(state["now"])

    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0),
        profile=_profile(),
        clock=clock,
    )
    kernel.load_model("model-a")
    kernel.load_model("model-b")
    kernel.pin_model("model-a")
    kernel.set_model_ttl("model-a", 30.0)
    kernel.set_model_ttl("model-b", 30.0)
    state["now"] = 140.0
    kernel.sweep_expired_models()

    payload = multi_model_governance_controls_to_dict(
        build_multi_model_governance_controls(kernel.status_dict())
    )

    assert payload["control_presence"]["eviction_history_visible"] is True
    assert payload["summary"]["blocked_reason"] == (
        "governance policy controls now exist locally; remaining closure is no longer policy-grade on this host"
    )


def test_multi_model_governance_controls_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "multi_model_governance_controls.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
