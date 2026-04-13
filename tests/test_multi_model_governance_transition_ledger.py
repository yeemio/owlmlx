from __future__ import annotations

import asyncio
from pathlib import Path

from owlmlx import (
    build_multi_model_governance_transition_ledger,
    multi_model_governance_transition_ledger_to_dict,
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


def test_multi_model_governance_transition_ledger_defaults_to_no_transition_runs() -> None:
    payload = multi_model_governance_transition_ledger_to_dict(
        build_multi_model_governance_transition_ledger()
    )

    assert payload["contract"]["surface"] == "owlmlx.multi_model_governance_transition_ledger"
    assert payload["summary"]["ledger_rung"] == "no_transition_runs"


def test_multi_model_governance_transition_ledger_marks_transition_visibility() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")

    payload = multi_model_governance_transition_ledger_to_dict(
        build_multi_model_governance_transition_ledger(kernel.status_dict())
    )

    assert payload["summary"]["ledger_rung"] == "transition_visibility"
    assert payload["recent_window"]["transition_count"] == 1


def test_multi_model_governance_transition_ledger_marks_partial_closure() -> None:
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")
    kernel.load_model("model-b")
    explicit = asyncio.run(kernel.generate("hello-explicit", model_id="model-a"))
    unload = kernel.unload_model("model-b")
    restart = kernel.restart_model("model-a")

    payload = multi_model_governance_transition_ledger_to_dict(
        build_multi_model_governance_transition_ledger(kernel.status_dict())
    )

    assert payload["summary"]["ledger_rung"] == "partial_closure"
    assert payload["transition_signals"]["restart_restore_visible"] is True


def test_multi_model_governance_transition_ledger_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "multi_model_governance_transition_ledger.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
