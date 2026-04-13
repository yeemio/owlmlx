"""Runtime-owned decision contract for large-weight first-smoke locality."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .mlx_environment import (
    MlxHostForensicsReport,
    build_mlx_host_forensics_report,
    host_forensics_to_dict,
)
from .specimen_gate import (
    LargeWeightSpecimenGate,
    build_large_weight_specimen_gate,
    specimen_gate_to_dict,
)


@dataclass(frozen=True, slots=True)
class LargeWeightFirstSmokeDecision:
    """Stable locality decision before attempting first smoke."""

    default_metal_gate: LargeWeightSpecimenGate
    force_cpu_gate: LargeWeightSpecimenGate
    host_forensics: MlxHostForensicsReport
    decision: str
    smoke_ready: bool
    preferred_execution_mode: str | None
    blocked_reason: str | None
    recommended_next_step: str


def build_large_weight_first_smoke_decision(
    *,
    specimen_path: str,
    include_known_candidates: bool = True,
    timeout_s: float = 20.0,
    quarantine_path: Path | None = None,
    crash_report_directory: Path | None = None,
    crash_limit: int = 5,
) -> LargeWeightFirstSmokeDecision:
    """Build the stable runtime-owned locality decision for first smoke."""

    default_metal_gate = build_large_weight_specimen_gate(
        specimen_path=specimen_path,
        include_known_candidates=include_known_candidates,
        preferred_execution_mode="default_metal",
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
    )
    force_cpu_gate = build_large_weight_specimen_gate(
        specimen_path=specimen_path,
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

    specimen_blocked_reason = (
        default_metal_gate.specimen_path.blocked_reason
        or force_cpu_gate.specimen_path.blocked_reason
    )
    if default_metal_gate.smoke_ready:
        return LargeWeightFirstSmokeDecision(
            default_metal_gate=default_metal_gate,
            force_cpu_gate=force_cpu_gate,
            host_forensics=host_forensics,
            decision="local_smoke_ready",
            smoke_ready=True,
            preferred_execution_mode="default_metal",
            blocked_reason=None,
            recommended_next_step="run local large-weight first smoke with default_metal",
        )
    if force_cpu_gate.smoke_ready:
        return LargeWeightFirstSmokeDecision(
            default_metal_gate=default_metal_gate,
            force_cpu_gate=force_cpu_gate,
            host_forensics=host_forensics,
            decision="local_smoke_ready",
            smoke_ready=True,
            preferred_execution_mode="force_cpu",
            blocked_reason=None,
            recommended_next_step="run local large-weight first smoke with force_cpu",
        )
    if specimen_blocked_reason is not None:
        return LargeWeightFirstSmokeDecision(
            default_metal_gate=default_metal_gate,
            force_cpu_gate=force_cpu_gate,
            host_forensics=host_forensics,
            decision="local_preconditions_incomplete",
            smoke_ready=False,
            preferred_execution_mode=None,
            blocked_reason=specimen_blocked_reason,
            recommended_next_step="complete local specimen prerequisites before first smoke",
        )
    if host_forensics.crash_reports:
        return LargeWeightFirstSmokeDecision(
            default_metal_gate=default_metal_gate,
            force_cpu_gate=force_cpu_gate,
            host_forensics=host_forensics,
            decision="move_host_recommended",
            smoke_ready=False,
            preferred_execution_mode=None,
            blocked_reason="no verified-safe mlx baseline exists on this host",
            recommended_next_step=(
                "move large-weight first smoke to another host or system image"
            ),
        )
    return LargeWeightFirstSmokeDecision(
        default_metal_gate=default_metal_gate,
        force_cpu_gate=force_cpu_gate,
        host_forensics=host_forensics,
        decision="local_blocked_continue_forensics",
        smoke_ready=False,
        preferred_execution_mode=None,
        blocked_reason="local mlx baseline remains unresolved",
        recommended_next_step=(
            "continue local MLX baseline forensics before retrying first smoke"
        ),
    )


def first_smoke_decision_to_dict(
    decision: LargeWeightFirstSmokeDecision,
) -> dict[str, object]:
    """Serialize the large-weight first-smoke locality decision."""

    return {
        "contract": {
            "surface": "owlmlx.large_weight_first_smoke_decision",
            "version": "stabilization3",
            "stable_sections": [
                "summary",
                "default_metal_gate",
                "force_cpu_gate",
                "host_forensics",
            ],
        },
        "summary": {
            "decision": decision.decision,
            "smoke_ready": decision.smoke_ready,
            "preferred_execution_mode": decision.preferred_execution_mode,
            "blocked_reason": decision.blocked_reason,
            "recommended_next_step": decision.recommended_next_step,
        },
        "default_metal_gate": specimen_gate_to_dict(decision.default_metal_gate),
        "force_cpu_gate": specimen_gate_to_dict(decision.force_cpu_gate),
        "host_forensics": host_forensics_to_dict(decision.host_forensics),
    }

