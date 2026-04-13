from __future__ import annotations

import asyncio
from pathlib import Path

from owlmlx import (
    build_multi_model_governance_controls,
    build_multi_model_governance_policy_gap,
    build_multi_model_governance_transition_ledger,
    multi_model_governance_policy_gap_to_dict,
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


def test_multi_model_governance_policy_gap_defaults_to_observation_gap_open() -> None:
    payload = multi_model_governance_policy_gap_to_dict(
        build_multi_model_governance_policy_gap()
    )

    assert payload["contract"]["surface"] == "owlmlx.multi_model_governance_policy_gap"
    assert payload["summary"]["policy_gap_rung"] == "observation_gap_open"
    assert payload["policy_controls"]["absent_policy_controls"] == [
        "pinning",
        "ttl_policy",
        "eviction_history_governance",
    ]


def test_multi_model_governance_policy_gap_marks_policy_gap_exact() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")
    kernel.load_model("model-b")
    explicit = asyncio.run(kernel.generate("hello-explicit", model_id="model-a"))
    unload = kernel.unload_model("model-b")
    restart = kernel.restart_model("model-a")

    assert explicit.ok is True
    assert unload.ok is True
    assert restart.ok is True

    runtime_status = kernel.status_dict()
    payload = multi_model_governance_policy_gap_to_dict(
        build_multi_model_governance_policy_gap(
            controls=build_multi_model_governance_controls(runtime_status),
            transition_ledger=build_multi_model_governance_transition_ledger(
                runtime_status
            ),
        )
    )

    assert payload["summary"]["policy_gap_rung"] == "policy_gap_exact"
    assert payload["observed_runtime_behavior"]["observed_runtime_behavior_frozen"] is True
    assert payload["policy_controls"]["absent_policy_controls"] == [
        "pinning",
        "ttl_policy",
        "eviction_history_governance",
    ]


def test_multi_model_governance_policy_gap_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "multi_model_governance_policy_gap.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
