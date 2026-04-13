"""Runtime-owned heavy-weight repeatability status for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


def build_host_stable_execution_status(**kwargs: Any) -> object:
    """Lazy wrapper kept at module scope for testability without import cycles."""

    from .runtime.host_stability import build_host_stable_execution_status as _build

    return _build(**kwargs)


def build_large_weight_first_smoke_decision(**kwargs: Any) -> object:
    """Lazy wrapper kept at module scope for testability without import cycles."""

    from .runtime.first_smoke_decision import build_large_weight_first_smoke_decision as _build

    return _build(**kwargs)


def host_stability_to_dict(status: object) -> dict[str, Any]:
    """Lazy serializer wrapper kept at module scope for testability."""

    if not hasattr(status, "default_metal_readiness"):
        return {
            "summary": {
                "status": getattr(status, "status", "unknown"),
                "ready": bool(getattr(status, "ready", False)),
                "preferred_execution_mode": getattr(
                    status, "preferred_execution_mode", None
                ),
                "blocked_reason": getattr(status, "blocked_reason", None),
                "recommended_next_step": getattr(
                    status,
                    "recommended_next_step",
                    "continue host-stability resolution before claiming heavier runtime validation",
                ),
            }
        }

    from .runtime.host_stability import host_stability_to_dict as _to_dict

    return _to_dict(status)


def first_smoke_decision_to_dict(decision: object) -> dict[str, Any]:
    """Lazy serializer wrapper kept at module scope for testability."""

    if not hasattr(decision, "default_metal_gate"):
        return {
            "summary": {
                "decision": getattr(decision, "decision", "unknown"),
                "smoke_ready": bool(getattr(decision, "smoke_ready", False)),
                "preferred_execution_mode": getattr(
                    decision, "preferred_execution_mode", None
                ),
                "blocked_reason": getattr(decision, "blocked_reason", None),
                "recommended_next_step": getattr(
                    decision,
                    "recommended_next_step",
                    "continue specimen/host preparation before claiming local first-smoke readiness",
                ),
            }
        }

    from .runtime.first_smoke_decision import first_smoke_decision_to_dict as _to_dict

    return _to_dict(decision)


@dataclass(frozen=True, slots=True)
class HeavyWeightRuntimeRepeatabilityStatus:
    """Stable runtime-owned status for heavy-weight runtime repeatability."""

    host_stability: object
    first_smoke_decision: object
    supported_host_proof_visible: bool
    supported_host_repeat_runs: int
    status: str
    repeatability_rung: str
    blocked_reason: str | None
    recommended_next_step: str


def build_heavy_weight_runtime_repeatability_status(
    *,
    specimen_path: str,
    include_known_candidates: bool = True,
    timeout_s: float = 20.0,
    quarantine_path: Path | None = None,
    crash_report_directory: Path | None = None,
    crash_limit: int = 5,
    supported_host_proof_visible: bool = False,
    supported_host_repeat_runs: int = 0,
) -> HeavyWeightRuntimeRepeatabilityStatus:
    """Build runtime-owned heavy-weight repeatability status."""

    host_stability = build_host_stable_execution_status(
        include_known_candidates=include_known_candidates,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
        crash_report_directory=crash_report_directory,
        crash_limit=crash_limit,
    )
    first_smoke_decision = build_large_weight_first_smoke_decision(
        specimen_path=specimen_path,
        include_known_candidates=include_known_candidates,
        timeout_s=timeout_s,
        quarantine_path=quarantine_path,
        crash_report_directory=crash_report_directory,
        crash_limit=crash_limit,
    )

    repeatability_rung = "local_blocked"
    blocked_reason = first_smoke_decision.blocked_reason or host_stability.blocked_reason
    recommended_next_step = (
        "establish one supported-host heavy-weight repeatability path before claiming replacement-grade runtime depth"
    )

    if first_smoke_decision.decision == "local_preconditions_incomplete":
        repeatability_rung = "local_preconditions_incomplete"
        recommended_next_step = (
            "complete local specimen prerequisites before attempting heavy-weight repeatability validation"
        )
    elif host_stability.ready and first_smoke_decision.smoke_ready:
        repeatability_rung = "host_ready_not_repeated"
        blocked_reason = (
            "supported heavy-weight runtime path is locally ready, but repeated proof is not yet established"
        )
        recommended_next_step = (
            "run repeated heavy-weight validation on the supported host before claiming stronger runtime repeatability"
        )

    if supported_host_proof_visible and supported_host_repeat_runs >= 2:
        repeatability_rung = "supported_host_repeatability_visible"
        blocked_reason = (
            "supported-host repeatability is visible, but broader customer runtime evidence still remains below reference-grade parity"
        )
        recommended_next_step = (
            "promote supported-host repeatability into broader customer runtime evidence instead of re-running first-smoke gating"
        )

    return HeavyWeightRuntimeRepeatabilityStatus(
        host_stability=host_stability,
        first_smoke_decision=first_smoke_decision,
        supported_host_proof_visible=supported_host_proof_visible,
        supported_host_repeat_runs=max(int(supported_host_repeat_runs), 0),
        status="partial",
        repeatability_rung=repeatability_rung,
        blocked_reason=blocked_reason,
        recommended_next_step=recommended_next_step,
    )


def heavy_weight_repeatability_status_to_dict(
    status: HeavyWeightRuntimeRepeatabilityStatus,
) -> dict[str, Any]:
    """Serialize runtime-owned heavy-weight repeatability status."""

    return {
        "contract": {
            "surface": "owlmlx.heavy_weight_runtime_repeatability",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "host_stability",
                "first_smoke_decision",
                "supported_host_proof",
            ],
        },
        "summary": {
            "status": status.status,
            "repeatability_rung": status.repeatability_rung,
            "blocked_reason": status.blocked_reason,
            "recommended_next_step": status.recommended_next_step,
        },
        "host_stability": host_stability_to_dict(status.host_stability)["summary"],
        "first_smoke_decision": first_smoke_decision_to_dict(
            status.first_smoke_decision
        )["summary"],
        "supported_host_proof": {
            "visible": status.supported_host_proof_visible,
            "repeat_runs": status.supported_host_repeat_runs,
        },
    }
