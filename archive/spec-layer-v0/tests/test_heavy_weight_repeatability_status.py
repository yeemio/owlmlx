from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from owlmlx import (
    build_heavy_weight_runtime_repeatability_status,
    heavy_weight_repeatability_status_to_dict,
)


def _host(*, ready: bool, status: str, blocked_reason: str | None):
    return SimpleNamespace(
        ready=ready,
        status=status,
        blocked_reason=blocked_reason,
        preferred_execution_mode="default_metal" if ready else None,
    )


def _decision(
    *,
    smoke_ready: bool,
    decision: str,
    blocked_reason: str | None,
):
    return SimpleNamespace(
        smoke_ready=smoke_ready,
        decision=decision,
        blocked_reason=blocked_reason,
        preferred_execution_mode="default_metal" if smoke_ready else None,
    )


def test_heavy_weight_repeatability_defaults_to_local_blocked(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_host_stable_execution_status",
        lambda **_: _host(
            ready=False,
            status="host_blocked_move_validation",
            blocked_reason="no verified-safe mlx baseline exists on this host",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_large_weight_first_smoke_decision",
        lambda **_: _decision(
            smoke_ready=False,
            decision="move_host_recommended",
            blocked_reason="no verified-safe mlx baseline exists on this host",
        ),
    )

    payload = heavy_weight_repeatability_status_to_dict(
        build_heavy_weight_runtime_repeatability_status(specimen_path="/tmp/specimen")
    )

    assert payload["contract"]["surface"] == "owlmlx.heavy_weight_runtime_repeatability"
    assert payload["summary"]["repeatability_rung"] == "local_blocked"


def test_heavy_weight_repeatability_marks_local_preconditions_incomplete(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_host_stable_execution_status",
        lambda **_: _host(
            ready=False,
            status="host_blocked_continue_forensics",
            blocked_reason="host-stable execution remains unresolved",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_large_weight_first_smoke_decision",
        lambda **_: _decision(
            smoke_ready=False,
            decision="local_preconditions_incomplete",
            blocked_reason="specimen shard set is incomplete",
        ),
    )

    payload = heavy_weight_repeatability_status_to_dict(
        build_heavy_weight_runtime_repeatability_status(specimen_path="/tmp/specimen")
    )

    assert payload["summary"]["repeatability_rung"] == "local_preconditions_incomplete"


def test_heavy_weight_repeatability_marks_host_ready_not_repeated(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_large_weight_first_smoke_decision",
        lambda **_: _decision(
            smoke_ready=True,
            decision="local_smoke_ready",
            blocked_reason=None,
        ),
    )

    payload = heavy_weight_repeatability_status_to_dict(
        build_heavy_weight_runtime_repeatability_status(specimen_path="/tmp/specimen")
    )

    assert payload["summary"]["repeatability_rung"] == "host_ready_not_repeated"
    assert payload["boundary_preconditions"]["required_memory_gb"] is None


def test_heavy_weight_repeatability_keeps_boundary_blocker_exact(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_large_weight_first_smoke_decision",
        lambda **_: _decision(
            smoke_ready=True,
            decision="local_smoke_ready",
            blocked_reason=None,
        ),
    )

    payload = heavy_weight_repeatability_status_to_dict(
        build_heavy_weight_runtime_repeatability_status(
            specimen_path="/tmp/specimen",
            boundary_required_memory_gb=122.0,
        )
    )

    assert payload["summary"]["repeatability_rung"] == "local_preconditions_incomplete"
    assert payload["boundary_preconditions"]["required_memory_gb"] == 122.0
    assert payload["boundary_preconditions"]["satisfied"] is False
    assert payload["boundary_preconditions"]["verdict"] == "exceeds"
    assert "116.0G limit" in payload["boundary_preconditions"]["reason"]


def test_heavy_weight_repeatability_marks_budget_fit_heavy_boundary_entered(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_host_stable_execution_status",
        lambda **_: _host(
            ready=True,
            status="host_ready_for_runtime_validation",
            blocked_reason=None,
        ),
    )
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_large_weight_first_smoke_decision",
        lambda **_: _decision(
            smoke_ready=True,
            decision="local_smoke_ready",
            blocked_reason=None,
        ),
    )

    payload = heavy_weight_repeatability_status_to_dict(
        build_heavy_weight_runtime_repeatability_status(
            specimen_path="/tmp/specimen",
            boundary_required_memory_gb=62.0,
            boundary_entry_visible=True,
            boundary_entry_reason="load/generate/unload succeeded on gemma-4-31B-it",
        )
    )

    assert payload["summary"]["repeatability_rung"] == "budget_fit_heavy_boundary_entered"
    assert payload["boundary_preconditions"]["required_memory_gb"] == 62.0
    assert payload["boundary_preconditions"]["satisfied"] is True
    assert payload["boundary_entry"]["visible"] is True


def test_heavy_weight_repeatability_marks_supported_host_repeatability_visible(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_host_stable_execution_status",
        lambda **_: _host(
            ready=False,
            status="host_blocked_move_validation",
            blocked_reason="no verified-safe mlx baseline exists on this host",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.heavy_weight_repeatability_status.build_large_weight_first_smoke_decision",
        lambda **_: _decision(
            smoke_ready=False,
            decision="move_host_recommended",
            blocked_reason="no verified-safe mlx baseline exists on this host",
        ),
    )

    payload = heavy_weight_repeatability_status_to_dict(
        build_heavy_weight_runtime_repeatability_status(
            specimen_path="/tmp/specimen",
            supported_host_proof_visible=True,
            supported_host_repeat_runs=2,
        )
    )

    assert payload["summary"]["repeatability_rung"] == "supported_host_repeatability_visible"
    assert payload["supported_host_proof"]["repeat_runs"] == 2


def test_heavy_weight_repeatability_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath(
        "owlmlx", "heavy_weight_repeatability_status.py"
    ).read_text()
    forbidden = [
        "llm_router",
        "ops_dashboard",
        "local-llm-desktop",
        "AI/Agent",
    ]
    for pattern in forbidden:
        assert pattern not in source
