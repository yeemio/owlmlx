from __future__ import annotations

from pathlib import Path

from owlmlx import (
    build_multi_model_ttl_policy_control,
    multi_model_ttl_policy_control_to_dict,
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


def _clock_box(start: float = 100.0):
    state = {"now": float(start)}

    def clock() -> float:
        return float(state["now"])

    return state, clock


def test_multi_model_ttl_policy_control_defaults_to_absent() -> None:
    payload = multi_model_ttl_policy_control_to_dict(build_multi_model_ttl_policy_control())

    assert payload["contract"]["surface"] == "owlmlx.multi_model_ttl_policy_control"
    assert payload["summary"]["control_rung"] == "control_absent"


def test_multi_model_ttl_policy_control_marks_implemented_with_harness_evidence() -> None:
    state, clock = _clock_box()
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile(), clock=clock)
    kernel.load_model("model-a")
    kernel.load_model("model-b")
    kernel.pin_model("model-a")
    kernel.set_model_ttl("model-a", 30.0)
    kernel.set_model_ttl("model-b", 30.0)

    state["now"] = 140.0
    sweep = kernel.sweep_expired_models()

    payload = multi_model_ttl_policy_control_to_dict(
        build_multi_model_ttl_policy_control(
            kernel.status_dict(),
            harness_evidence={
                "sweep_unloaded_visible": "model-b" in sweep.unloaded_model_ids,
                "pinned_expiry_block_visible": "model-a" in sweep.skipped_pinned_model_ids,
            },
        )
    )

    assert payload["summary"]["control_rung"] == "control_implemented"
    assert payload["ttl_policy"]["ttl_supported"] is True
    assert payload["policy_progress"]["remaining_controls"] == [
        "eviction_history_governance",
    ]


def test_multi_model_ttl_policy_control_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "multi_model_ttl_policy_control.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
