"""Runtime-owned host-level stability contract for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .mlx_environment import (
    MlxEnvironmentReadiness,
    MlxHostForensicsReport,
    build_mlx_environment_readiness,
    build_mlx_host_forensics_report,
    host_forensics_to_dict,
    readiness_to_dict,
)


@dataclass(frozen=True, slots=True)
class HostStableExecutionStatus:
    """Stable host-level decision for runtime validation readiness."""

    default_metal_readiness: MlxEnvironmentReadiness
    force_cpu_readiness: MlxEnvironmentReadiness
    host_forensics: MlxHostForensicsReport
    status: str
    preferred_execution_mode: str | None
    blocked_reason: str | None
    recommended_next_step: str

    @property
    def ready(self) -> bool:
        return self.status == "host_ready_for_runtime_validation"


def build_host_stable_execution_status(
    *,
    include_known_candidates: bool = True,
    timeout_s: float = 20.0,
    quarantine_path: Path | None = None,
    crash_report_directory: Path | None = None,
    crash_limit: int = 5,
) -> HostStableExecutionStatus:
    """Build the host-level execution-status contract."""

    default_metal_readiness = build_mlx_environment_readiness(
        include_known_candidates=include_known_candidates,
        preferred_execution_mode="default_metal",
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
    )
    force_cpu_readiness = build_mlx_environment_readiness(
        include_known_candidates=include_known_candidates,
        preferred_execution_mode="force_cpu",
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
    )
    host_forensics = build_mlx_host_forensics_report(
        include_known_candidates=include_known_candidates,
        preferred_execution_mode="default_metal",
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
        crash_report_directory=crash_report_directory,
        crash_limit=crash_limit,
    )

    if default_metal_readiness.ok:
        return HostStableExecutionStatus(
            default_metal_readiness=default_metal_readiness,
            force_cpu_readiness=force_cpu_readiness,
            host_forensics=host_forensics,
            status="host_ready_for_runtime_validation",
            preferred_execution_mode="default_metal",
            blocked_reason=None,
            recommended_next_step="run repeated runtime validation on this host with default_metal",
        )
    if force_cpu_readiness.ok:
        return HostStableExecutionStatus(
            default_metal_readiness=default_metal_readiness,
            force_cpu_readiness=force_cpu_readiness,
            host_forensics=host_forensics,
            status="host_ready_for_runtime_validation",
            preferred_execution_mode="force_cpu",
            blocked_reason=None,
            recommended_next_step="run constrained runtime validation on this host with force_cpu",
        )
    if host_forensics.crash_reports:
        return HostStableExecutionStatus(
            default_metal_readiness=default_metal_readiness,
            force_cpu_readiness=force_cpu_readiness,
            host_forensics=host_forensics,
            status="host_blocked_move_validation",
            preferred_execution_mode=None,
            blocked_reason="no verified-safe mlx baseline exists on this host",
            recommended_next_step="move replacement-grade runtime validation to another host or system image",
        )
    return HostStableExecutionStatus(
        default_metal_readiness=default_metal_readiness,
        force_cpu_readiness=force_cpu_readiness,
        host_forensics=host_forensics,
        status="host_blocked_continue_forensics",
        preferred_execution_mode=None,
        blocked_reason="host-stable execution remains unresolved",
        recommended_next_step="continue local baseline forensics before retrying runtime validation",
    )


def host_stability_to_dict(status: HostStableExecutionStatus) -> dict[str, object]:
    """Serialize host-stable execution status."""

    return {
        "contract": {
            "surface": "owlmlx.host_stable_execution",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "default_metal_readiness",
                "force_cpu_readiness",
                "host_forensics",
            ],
        },
        "summary": {
            "status": status.status,
            "ready": status.ready,
            "preferred_execution_mode": status.preferred_execution_mode,
            "blocked_reason": status.blocked_reason,
            "recommended_next_step": status.recommended_next_step,
        },
        "default_metal_readiness": readiness_to_dict(status.default_metal_readiness),
        "force_cpu_readiness": readiness_to_dict(status.force_cpu_readiness),
        "host_forensics": host_forensics_to_dict(status.host_forensics),
    }

