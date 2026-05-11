from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_multi_model_pinning_control,
    multi_model_pinning_control_to_dict,
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


def test_multi_model_pinning_control_defaults_to_absent() -> None:
    payload = multi_model_pinning_control_to_dict(build_multi_model_pinning_control())

    assert payload["contract"]["surface"] == "owlmlx.multi_model_pinning_control"
    assert payload["summary"]["control_rung"] == "control_absent"


def test_multi_model_pinning_control_marks_implemented_with_harness_evidence() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")
    kernel.pin_model("model-a")
    blocked = kernel.unload_model("model-a")
    restarted = kernel.restart_model("model-a")

    payload = multi_model_pinning_control_to_dict(
        build_multi_model_pinning_control(
            kernel.status_dict(),
            harness_evidence={
                "unload_block_visible": (not blocked.ok),
                "restart_retains_pin_visible": restarted.ok
                and "model-a"
                in kernel.status_dict()["governance_policy"]["pinned_model_ids"],
            },
        )
    )

    assert payload["summary"]["control_rung"] == "control_implemented"
    assert payload["pinning"]["pinning_supported"] is True
    assert payload["pinning"]["ttl_supported"] is True
    assert payload["policy_progress"]["remaining_controls"] == [
        "eviction_history_governance",
    ]


def test_multi_model_pinning_control_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "multi_model_pinning_control.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
