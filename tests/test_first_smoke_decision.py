from __future__ import annotations

from types import SimpleNamespace

from owlmlx.runtime.first_smoke_decision import (
    build_large_weight_first_smoke_decision,
    first_smoke_decision_to_dict,
)


def _gate(*, smoke_ready: bool, specimen_blocked_reason: str | None, env_blocked_reason: str | None):
    return SimpleNamespace(
        smoke_ready=smoke_ready,
        blocked_reason=specimen_blocked_reason or env_blocked_reason,
        specimen_path=SimpleNamespace(blocked_reason=specimen_blocked_reason),
        mlx_environment=SimpleNamespace(blocked_reason=env_blocked_reason),
    )


def _forensics(*, crash_count: int):
    return SimpleNamespace(
        blocked=crash_count > 0,
        crash_reports=tuple(SimpleNamespace(path=f"/tmp/{idx}.ips") for idx in range(crash_count)),
        crash_report_directory="/tmp/crashes",
        readiness=SimpleNamespace(ok=False),
    )


def test_first_smoke_decision_prefers_default_metal_when_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.build_large_weight_specimen_gate",
        lambda **kwargs: (
            _gate(smoke_ready=True, specimen_blocked_reason=None, env_blocked_reason=None)
            if kwargs["preferred_execution_mode"] == "default_metal"
            else _gate(
                smoke_ready=False,
                specimen_blocked_reason=None,
                env_blocked_reason="no usable mlx-lm python environment found",
            )
        ),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.build_mlx_host_forensics_report",
        lambda **_: _forensics(crash_count=1),
    )

    decision = build_large_weight_first_smoke_decision(specimen_path="/tmp/specimen")
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.specimen_gate_to_dict",
        lambda gate: {"summary": {"smoke_ready": gate.smoke_ready}},
    )
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.host_forensics_to_dict",
        lambda report: {"summary": {"crash_report_count": len(report.crash_reports)}},
    )
    payload = first_smoke_decision_to_dict(decision)

    assert decision.decision == "local_smoke_ready"
    assert decision.preferred_execution_mode == "default_metal"
    assert payload["summary"]["smoke_ready"] is True


def test_first_smoke_decision_allows_force_cpu_when_only_ready_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.build_large_weight_specimen_gate",
        lambda **kwargs: (
            _gate(
                smoke_ready=False,
                specimen_blocked_reason=None,
                env_blocked_reason="no usable mlx-lm python environment found",
            )
            if kwargs["preferred_execution_mode"] == "default_metal"
            else _gate(smoke_ready=True, specimen_blocked_reason=None, env_blocked_reason=None)
        ),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.build_mlx_host_forensics_report",
        lambda **_: _forensics(crash_count=0),
    )

    decision = build_large_weight_first_smoke_decision(specimen_path="/tmp/specimen")

    assert decision.decision == "local_smoke_ready"
    assert decision.preferred_execution_mode == "force_cpu"


def test_first_smoke_decision_reports_incomplete_local_preconditions(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.build_large_weight_specimen_gate",
        lambda **_: _gate(
            smoke_ready=False,
            specimen_blocked_reason="specimen shard set is incomplete",
            env_blocked_reason="no usable mlx-lm python environment found",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.build_mlx_host_forensics_report",
        lambda **_: _forensics(crash_count=0),
    )

    decision = build_large_weight_first_smoke_decision(specimen_path="/tmp/specimen")

    assert decision.decision == "local_preconditions_incomplete"
    assert decision.blocked_reason == "specimen shard set is incomplete"


def test_first_smoke_decision_recommends_move_host_when_specimen_ready_but_host_blocked(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.build_large_weight_specimen_gate",
        lambda **_: _gate(
            smoke_ready=False,
            specimen_blocked_reason=None,
            env_blocked_reason="no usable mlx-lm python environment found",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.build_mlx_host_forensics_report",
        lambda **_: _forensics(crash_count=3),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.specimen_gate_to_dict",
        lambda gate: {"summary": {"smoke_ready": gate.smoke_ready}},
    )
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.host_forensics_to_dict",
        lambda report: {"summary": {"crash_report_count": len(report.crash_reports)}},
    )

    decision = build_large_weight_first_smoke_decision(specimen_path="/tmp/specimen")
    payload = first_smoke_decision_to_dict(decision)

    assert decision.decision == "move_host_recommended"
    assert payload["summary"]["recommended_next_step"] == (
        "move large-weight first smoke to another host or system image"
    )
    assert payload["host_forensics"]["summary"]["crash_report_count"] == 3


def test_first_smoke_decision_keeps_local_forensics_when_no_crash_reports(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.build_large_weight_specimen_gate",
        lambda **_: _gate(
            smoke_ready=False,
            specimen_blocked_reason=None,
            env_blocked_reason="no usable mlx-lm python environment found",
        ),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.first_smoke_decision.build_mlx_host_forensics_report",
        lambda **_: _forensics(crash_count=0),
    )

    decision = build_large_weight_first_smoke_decision(specimen_path="/tmp/specimen")

    assert decision.decision == "local_blocked_continue_forensics"
    assert decision.smoke_ready is False
