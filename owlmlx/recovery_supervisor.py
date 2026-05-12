"""Runtime-owned recovery supervisor barrier contract for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .settle_barrier_event import build_settle_barrier_event


RECOVERY_SUPERVISOR_CONTRACT_SURFACE = "owlmlx.recovery_supervisor_contract"
RECOVERY_SUPERVISOR_CONTRACT_VERSION = "v1"


@dataclass(frozen=True, slots=True)
class RecoverySupervisorContract:
    """Stable runtime-owned recovery barrier assessment."""

    recovery_state: str
    barrier_decision: str
    confidence: str
    reason_code: str
    reason_message: str
    barrier: dict[str, Any]
    substrate: dict[str, Any]
    restart: dict[str, Any]
    lifecycle: dict[str, Any]
    request_impact: dict[str, Any]
    policy_boundaries: dict[str, Any]
    missing_signals: tuple[dict[str, str], ...]


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _list_of_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if isinstance(item, str) and item)


def _bool_or_none(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _classify_recovery(
    *,
    backend_healthy: bool | None,
    restart_exhausted_models: tuple[str, ...],
    abort_state: str | None,
    recovery_required: bool | None,
    reclaim_barrier_state: str,
    reclaim_barrier_unresolved_count: int,
) -> tuple[str, str, str, str, str]:
    if backend_healthy is False:
        return (
            "backend_unhealthy",
            "block_runtime_generation",
            "high",
            "backend_unhealthy_runtime_unavailable",
            "The runtime backend is unhealthy, so generation should fail closed.",
        )
    if restart_exhausted_models:
        return (
            "restart_exhausted",
            "operator_recovery_required",
            "high",
            "restart_attempts_exhausted",
            "One or more loaded models have exhausted runtime-owned restart attempts.",
        )
    if reclaim_barrier_state in {
        "failed_unload",
        "failed_reclaim",
        "restart_unload_failed",
    }:
        return (
            "failed_reclaim_barrier",
            "recovery_barrier_required",
            "high",
            f"reclaim_barrier_event_unresolved_{reclaim_barrier_state}",
            (
                f"Runtime-owned settle_barrier_event reports {reclaim_barrier_state} "
                f"with {reclaim_barrier_unresolved_count} unresolved event(s); "
                "recovery barrier required until the four-class recovery policy "
                "resolves them."
            ),
        )
    if abort_state == "contaminated" or recovery_required is True:
        return (
            "contaminated",
            "recovery_barrier_required",
            "high",
            "substrate_contaminated_recovery_required",
            "Abort recovery state reports substrate contamination or required recovery.",
        )
    if abort_state == "probing":
        return (
            "probing",
            "defer_high_context_until_probe",
            "medium",
            "abort_recovery_probe_pending",
            "Abort recovery state is probing; high-context work should wait for probe truth.",
        )
    if abort_state == "clean":
        return (
            "clean",
            "no_recovery_barrier",
            "medium",
            "substrate_clean_and_no_restart_exhaustion",
            "Runtime-owned recovery inputs show no current recovery barrier.",
        )
    return (
        "unknown",
        "insufficient_signal",
        "low",
        "abort_recovery_snapshot_missing",
        "Runtime restart visibility exists, but abort recovery state is not visible.",
    )


def build_recovery_supervisor_contract(
    *,
    runtime_status: Mapping[str, Any] | None = None,
    abort_recovery_snapshot: Mapping[str, Any] | None = None,
) -> RecoverySupervisorContract:
    """Build the current runtime-owned recovery supervisor barrier assessment."""

    raw_status = _mapping(runtime_status)
    summary = _mapping(raw_status.get("summary"))
    health = _mapping(raw_status.get("health"))
    restart = _mapping(raw_status.get("restart"))
    governance = _mapping(raw_status.get("governance_observations"))
    abort_snapshot = _mapping(abort_recovery_snapshot or raw_status.get("abort_recovery"))

    backend_healthy = _bool_or_none(summary.get("backend_healthy"))
    restartable_models = _list_of_strings(restart.get("restartable_models"))
    restart_exhausted_models = _list_of_strings(restart.get("restart_exhausted_models"))
    abort_state_value = abort_snapshot.get("state")
    abort_state = str(abort_state_value) if isinstance(abort_state_value, str) else None
    recovery_required = _bool_or_none(abort_snapshot.get("recovery_required"))
    reclaim_barrier_contract = build_settle_barrier_event(runtime_status=raw_status)
    reclaim_barrier_state = reclaim_barrier_contract.barrier_state
    reclaim_barrier_unresolved_count = int(
        reclaim_barrier_contract.barrier.get("unresolved_event_count", 0)
    )

    state, decision, confidence, reason_code, reason_message = _classify_recovery(
        backend_healthy=backend_healthy,
        restart_exhausted_models=restart_exhausted_models,
        abort_state=abort_state,
        recovery_required=recovery_required,
        reclaim_barrier_state=reclaim_barrier_state,
        reclaim_barrier_unresolved_count=reclaim_barrier_unresolved_count,
    )
    hard_barrier = decision in {
        "block_runtime_generation",
        "operator_recovery_required",
        "recovery_barrier_required",
    }
    reclaim_barrier_active = reclaim_barrier_state in {
        "failed_unload",
        "failed_reclaim",
        "restart_unload_failed",
    }
    high_context_barrier = decision == "defer_high_context_until_probe"

    return RecoverySupervisorContract(
        recovery_state=state,
        barrier_decision=decision,
        confidence=confidence,
        reason_code=reason_code,
        reason_message=reason_message,
        barrier={
            "barrier_decision": decision,
            "hard_recovery_barrier": hard_barrier,
            "high_context_barrier": high_context_barrier or hard_barrier,
            "general_admission_block_required": hard_barrier,
            "classification_status": (
                "supported" if state != "unknown" else "insufficient_signal"
            ),
            "reason_code": reason_code,
        },
        substrate={
            "abort_recovery_state": abort_state,
            "recovery_required": recovery_required,
            "contamination_reason": abort_snapshot.get("contamination_reason"),
            "last_probe_ok": abort_snapshot.get("last_probe_ok"),
            "last_probe_at": abort_snapshot.get("last_probe_at"),
            "last_recovery_at": abort_snapshot.get("last_recovery_at"),
            "total_high_context_aborts": abort_snapshot.get("total_high_context_aborts"),
            "classification_status": (
                "supported" if abort_state in {"clean", "probing", "contaminated"}
                else "insufficient_signal"
            ),
        },
        restart={
            "backend_healthy": backend_healthy,
            "readiness": health.get("readiness"),
            "block_reason": health.get("block_reason"),
            "restartable_models": list(restartable_models),
            "restart_exhausted_models": list(restart_exhausted_models),
            "auto_restart_dead_session": bool(restart.get("auto_restart_dead_session", False)),
            "classification_status": "supported",
        },
        lifecycle={
            "restart_restore_visible": bool(governance.get("restart_restore_visible", False)),
            "recent_window_runs": governance.get("recent_window_runs", 0),
            "eviction_history_events_visible": bool(
                governance.get("eviction_history_events_visible", False)
            ),
            "reclaim_barrier_state": reclaim_barrier_state,
            "reclaim_barrier_unresolved_event_count": reclaim_barrier_unresolved_count,
            "reclaim_barrier_active": reclaim_barrier_active,
            "classification_status": (
                "supported" if reclaim_barrier_state != "unknown" else "partial"
            ),
            "reason_code": (
                f"reclaim_barrier_state_{reclaim_barrier_state}"
                if reclaim_barrier_state != "unknown"
                else "reclaim_barrier_section_absent_from_runtime_status"
            ),
        },
        request_impact={
            "generation_admissible": not hard_barrier,
            "high_context_generation_admissible": not (hard_barrier or high_context_barrier),
            "interactive_generation_admissible": not hard_barrier,
            "impact_scope": (
                "all_generation"
                if hard_barrier
                else "high_context_only"
                if high_context_barrier
                else "no_current_recovery_barrier"
                if state == "clean"
                else "unknown"
            ),
        },
        policy_boundaries={
            "policy_scope": "recovery_barrier_classification_only",
            "runtime_owned_recovery_barrier": hard_barrier or high_context_barrier,
            "automatic_recovery_loop": False,
            "pressure_ranked_eviction": False,
            "reclaim_engine": False,
            "continuous_batching": False,
            "preserved_invariants": [
                "max_concurrent_1_after_gate_claim",
                "ticketed_fifo_after_gate_claim",
                "no_hidden_retry_loop",
                "no_pressure_ranked_eviction",
            ],
        },
        missing_signals=(
            {
                "layer": "recovery",
                "signal": "worker_pollution_detector_beyond_abort_recovery",
                "reason": "abort recovery state is owned, but broader worker-pollution detection is not",
            },
            {
                "layer": "recovery",
                "signal": "automatic_recovery_supervisor_loop",
                "reason": "this contract classifies barriers but does not run background recovery actions",
            },
            {
                "layer": "recovery",
                "signal": "frozen_four_class_termination_cause_recovery_policy",
                "reason": "settle_barrier_event records cleanup-boundary failures, but the four-class termination-cause recovery policy and event-resolution rules remain future 3.4 work",
            },
        ),
    )


def recovery_supervisor_contract_to_dict(
    contract: RecoverySupervisorContract,
) -> dict[str, Any]:
    """Serialize the runtime-owned recovery supervisor contract."""

    return {
        "contract": {
            "surface": RECOVERY_SUPERVISOR_CONTRACT_SURFACE,
            "version": RECOVERY_SUPERVISOR_CONTRACT_VERSION,
            "stable_sections": [
                "summary",
                "barrier",
                "substrate",
                "restart",
                "lifecycle",
                "request_impact",
                "policy_boundaries",
                "missing_signals",
            ],
        },
        "summary": {
            "recovery_state": contract.recovery_state,
            "barrier_decision": contract.barrier_decision,
            "confidence": contract.confidence,
        },
        "reason": {
            "code": contract.reason_code,
            "message": contract.reason_message,
        },
        "barrier": contract.barrier,
        "substrate": contract.substrate,
        "restart": contract.restart,
        "lifecycle": contract.lifecycle,
        "request_impact": contract.request_impact,
        "policy_boundaries": contract.policy_boundaries,
        "missing_signals": list(contract.missing_signals),
    }
