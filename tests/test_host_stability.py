from __future__ import annotations

from types import SimpleNamespace

from owlmlx.runtime.host_stability import (
    build_host_stable_execution_status,
    host_stability_to_dict,
)


def _readiness(*, ok: bool, blocked_reason: str | None):
    return SimpleNamespace(
        ok=ok,
        blocked_reason=blocked_reason,
        selection=SimpleNamespace(ok=ok),
        include_known_candidates=True,
        preferred_execution_mode="default_metal",
        quarantine_count=0,
    )


def _forensics(*, crash_count: int):
    return SimpleNamespace(
        blocked=crash_count > 0,
        crash_reports=tuple(SimpleNamespace(path=f"/tmp/{idx}.ips") for idx in range(crash_count)),
        crash_report_directory="/tmp/crashes",
        readiness=SimpleNamespace(ok=False),
    )


def test_host_stability_prefers_default_metal_when_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.host_stability.build_mlx_environment_readiness",
        lambda **kwargs: (
            _readiness(ok=True, blocked_reason=None)
            if kwargs["preferred_execution_mode"] == "default_metal"
            else _readiness(ok=False, blocked_reason="blocked")
        ),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.host_stability.build_mlx_host_forensics_report",
        lambda **_: _forensics(crash_count=0),
    )

    status = build_host_stable_execution_status()

    assert status.status == "host_ready_for_runtime_validation"
    assert status.preferred_execution_mode == "default_metal"


def test_host_stability_allows_force_cpu_when_only_ready_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.host_stability.build_mlx_environment_readiness",
        lambda **kwargs: (
            _readiness(ok=False, blocked_reason="blocked")
            if kwargs["preferred_execution_mode"] == "default_metal"
            else _readiness(ok=True, blocked_reason=None)
        ),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.host_stability.build_mlx_host_forensics_report",
        lambda **_: _forensics(crash_count=0),
    )

    status = build_host_stable_execution_status()

    assert status.status == "host_ready_for_runtime_validation"
    assert status.preferred_execution_mode == "force_cpu"


def test_host_stability_recommends_move_host_when_crashes_exist(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.host_stability.build_mlx_environment_readiness",
        lambda **_: _readiness(ok=False, blocked_reason="no usable mlx-lm python environment found"),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.host_stability.build_mlx_host_forensics_report",
        lambda **_: _forensics(crash_count=4),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.host_stability.readiness_to_dict",
        lambda readiness: {"summary": {"blocked_reason": readiness.blocked_reason}},
    )
    monkeypatch.setattr(
        "owlmlx.runtime.host_stability.host_forensics_to_dict",
        lambda report: {"summary": {"crash_report_count": len(report.crash_reports)}},
    )

    status = build_host_stable_execution_status()
    payload = host_stability_to_dict(status)

    assert status.status == "host_blocked_move_validation"
    assert payload["summary"]["recommended_next_step"] == (
        "move replacement-grade runtime validation to another host or system image"
    )
    assert payload["host_forensics"]["summary"]["crash_report_count"] == 4


def test_host_stability_keeps_local_forensics_when_no_crashes(monkeypatch) -> None:
    monkeypatch.setattr(
        "owlmlx.runtime.host_stability.build_mlx_environment_readiness",
        lambda **_: _readiness(ok=False, blocked_reason="no usable mlx-lm python environment found"),
    )
    monkeypatch.setattr(
        "owlmlx.runtime.host_stability.build_mlx_host_forensics_report",
        lambda **_: _forensics(crash_count=0),
    )

    status = build_host_stable_execution_status()

    assert status.status == "host_blocked_continue_forensics"
    assert status.ready is False

