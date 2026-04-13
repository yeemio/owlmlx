from __future__ import annotations

import asyncio
from pathlib import Path

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx import (
    build_multi_model_governance_status,
    multi_model_governance_status_to_dict,
)


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=14.0,
        warning_threshold_gb=12.0,
    )


def test_multi_model_governance_defaults_to_inventory_visible() -> None:
    payload = multi_model_governance_status_to_dict(
        build_multi_model_governance_status()
    )

    assert payload["contract"]["surface"] == "owlmlx.multi_model_governance_status"
    assert payload["summary"]["governance_rung"] == "inventory_visible"
    assert payload["governance_controls"]["pinning_supported"] is False


def test_multi_model_governance_marks_active_default_visible() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")

    payload = multi_model_governance_status_to_dict(
        build_multi_model_governance_status(kernel.status_dict())
    )

    assert payload["summary"]["governance_rung"] in {
        "active_default_visible",
        "restart_visibility_visible",
    }
    assert payload["active_model"]["active_model_id"] == "model-a"
    assert payload["active_model"]["default_generation_supported"] is True


def test_multi_model_governance_marks_partial_closure_for_live_multi_model_state() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")
    kernel.load_model("model-b")
    asyncio.run(kernel.generate("hello-active"))
    asyncio.run(kernel.generate("hello-explicit", model_id="model-a"))
    kernel.restart_model("model-b")

    payload = multi_model_governance_status_to_dict(
        build_multi_model_governance_status(kernel.status_dict())
    )

    assert payload["summary"]["governance_rung"] == "partial_closure"
    assert payload["inventory"]["resident_model_count"] == 2
    assert payload["active_model"]["active_model_id"] == "model-b"
    assert payload["active_model"]["active_model_loaded"] is True
    assert payload["recoverability"]["restart_surface_visible"] is True


def test_multi_model_governance_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "multi_model_governance_status.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
