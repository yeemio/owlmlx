"""Runtime-owned failed-unload / failed-reclaim barrier event contract for owlmlx.

This module owns the narrow operation-boundary truth needed by release floor
3.4 sub-round 3.4A0:

    *Given runtime-owned lifecycle operation events, is there an unresolved
    failed unload or failed reclaim event that requires a recovery barrier?*

It does NOT implement automatic retry, quarantine execution, restart loops,
operator remediation, a background recovery supervisor daemon, pressure-ranked
victim selection, or stream-hold counters. The event surface is read-only:
recording happens inside ``RuntimeKernel`` at the operation boundary; this
module classifies the snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


RECLAIM_BARRIER_EVENT_SURFACE = "owlmlx.reclaim_barrier_event"
RECLAIM_BARRIER_EVENT_VERSION = "v1"

OPERATION_VOCABULARY: tuple[str, ...] = (
    "explicit_unload",
    "ttl_sweep_reclaim",
    "restart_unload_stage",
    "unknown",
)

BARRIER_STATE_VOCABULARY: tuple[str, ...] = (
    "clean",
    "failed_unload",
    "failed_reclaim",
    "restart_unload_failed",
    "unknown",
)

REQUIRED_EVENT_FIELDS: tuple[str, ...] = (
    "event_id",
    "model_id",
    "operation",
    "source",
    "stage",
    "error_code",
    "message",
    "recorded_at_s",
    "requires_recovery_barrier",
    "resolved",
)


@dataclass(frozen=True, slots=True)
class ReclaimBarrierEventContract:
    """Stable runtime-owned reclaim-barrier-event assessment."""

    barrier_state: str
    confidence: str
    reason_code: str
    reason_message: str
    barrier: dict[str, Any]
    events: tuple[dict[str, Any], ...]
    operation_support: dict[str, dict[str, Any]]
    policy_boundaries: dict[str, Any]
    preserved_invariants: tuple[str, ...]
    missing_signals: tuple[dict[str, str], ...]


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _operation_support() -> dict[str, dict[str, Any]]:
    return {
        "explicit_unload": {
            "classification_status": "supported",
            "reason_code": "explicit_unload_records_failed_unload_at_backend_unload_boundary",
        },
        "ttl_sweep_reclaim": {
            "classification_status": "supported",
            "reason_code": "ttl_sweep_records_failed_reclaim_at_backend_unload_boundary",
        },
        "restart_unload_stage": {
            "classification_status": "supported",
            "reason_code": "restart_records_restart_unload_failed_at_unload_stage_boundary",
        },
        "unknown": {
            "classification_status": "supported",
            "reason_code": "operation_boundary_truth_absent_for_event",
        },
    }


def _classify_barrier_state(
    *,
    section_visible: bool,
    unresolved_events: list[dict[str, Any]],
) -> tuple[str, str, str, str]:
    if not section_visible:
        return (
            "unknown",
            "low",
            "reclaim_barrier_section_not_exposed_by_runtime_status",
            (
                "The runtime status snapshot does not expose the reclaim_barrier "
                "section, so the contract cannot determine operation-boundary truth."
            ),
        )
    if not unresolved_events:
        return (
            "clean",
            "high",
            "no_unresolved_failed_unload_or_failed_reclaim_event",
            (
                "No unresolved failed unload, failed reclaim, or restart unload "
                "stage event is currently visible in runtime-owned event truth."
            ),
        )

    # Pick the latest unresolved event's operation as the dominant barrier
    # class. Ordering inside the events list is append order, so the last
    # entry is the most recent. Sorting by event_id is equivalent because
    # event_id is a monotonically increasing integer assigned by the kernel.
    latest = max(unresolved_events, key=lambda event: int(event.get("event_id") or 0))
    operation = str(latest.get("operation") or "unknown")

    if operation == "ttl_sweep_reclaim":
        return (
            "failed_reclaim",
            "high",
            "ttl_sweep_reclaim_failed_at_backend_unload_boundary",
            (
                "A TTL sweep reclaim attempt reached the backend unload boundary "
                "and that unload returned a failure result."
            ),
        )
    if operation == "restart_unload_stage":
        return (
            "restart_unload_failed",
            "high",
            "restart_unload_stage_failed_at_backend_unload_boundary",
            (
                "A restart attempt reached its unload stage and the backend "
                "unload at that stage returned a failure result."
            ),
        )
    if operation == "explicit_unload":
        return (
            "failed_unload",
            "high",
            "explicit_unload_failed_at_backend_unload_boundary",
            (
                "An explicit unload reached the backend unload boundary and "
                "returned a failure result."
            ),
        )
    return (
        "failed_unload",
        "medium",
        "unresolved_event_with_unrecognized_operation",
        (
            "An unresolved reclaim-barrier event exists but its operation is "
            "not in the frozen operation vocabulary; treating as failed_unload."
        ),
    )


def build_reclaim_barrier_event(
    *,
    runtime_status: Mapping[str, Any] | None = None,
) -> ReclaimBarrierEventContract:
    """Build the current runtime-owned reclaim-barrier-event assessment."""

    raw_status = _mapping(runtime_status)
    section = raw_status.get("reclaim_barrier")
    section_visible = isinstance(section, Mapping)
    section_map = _mapping(section)

    raw_events = section_map.get("events")
    events: list[dict[str, Any]] = []
    if isinstance(raw_events, list):
        for entry in raw_events:
            if isinstance(entry, Mapping):
                events.append(dict(entry))

    unresolved = [event for event in events if not event.get("resolved", False)]

    barrier_state, confidence, reason_code, reason_message = _classify_barrier_state(
        section_visible=section_visible,
        unresolved_events=unresolved,
    )

    hard_recovery_barrier = barrier_state in {
        "failed_unload",
        "failed_reclaim",
        "restart_unload_failed",
    }

    return ReclaimBarrierEventContract(
        barrier_state=barrier_state,
        confidence=confidence,
        reason_code=reason_code,
        reason_message=reason_message,
        barrier={
            "barrier_state": barrier_state,
            "hard_recovery_barrier": hard_recovery_barrier,
            "unresolved_event_count": len(unresolved),
            "total_event_count": len(events),
            "classification_status": (
                "supported" if section_visible else "insufficient_signal"
            ),
            "reason_code": reason_code,
        },
        events=tuple(events),
        operation_support=_operation_support(),
        policy_boundaries={
            "policy_scope": "operation_boundary_event_recording_only",
            "runtime_owned_failed_unload_event": True,
            "runtime_owned_failed_reclaim_event": True,
            "runtime_owned_restart_unload_failed_event": True,
            "automatic_retry": False,
            "automatic_quarantine": False,
            "automatic_recovery_supervisor_loop": False,
            "pressure_ranked_eviction": False,
            "stream_hold_counter": False,
            "owned_actions_visible": [
                "record_event_at_explicit_unload_boundary_failure",
                "record_event_at_ttl_sweep_reclaim_boundary_failure",
                "record_event_at_restart_unload_stage_boundary_failure",
                "expose_event_snapshot_in_runtime_status",
                "expose_read_only_contract_via_http",
            ],
            "out_of_scope": [
                "automatic_retry_or_quarantine_or_drop_policy",
                "background_recovery_supervisor_daemon",
                "pressure_ranked_victim_selection",
                "stream_hold_counter_or_duration_tracking",
                "operator_remediation_workflow",
                "full_four_class_termination_cause_recovery_policy",
            ],
            "non_classifying_paths": [
                "pinned_unload_blocked_before_backend_cleanup",
                "missing_model_preflight_failure",
                "ttl_expired_pinned_model_skipped_by_policy",
                "over_budget_pressure_without_unload_attempt",
                "restart_visibility_without_failed_cleanup_event",
            ],
        },
        preserved_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "no_post_claim_gate_bypass",
            "no_hidden_retry_loop",
            "no_automatic_recovery_supervisor_loop",
            "pinned_models_never_evicted",
        ),
        missing_signals=(
            {
                "layer": "recovery",
                "signal": "frozen_event_resolution_policy",
                "reason": (
                    "this round records events but does not freeze when an "
                    "event becomes resolved; resolution is part of the future "
                    "four-class recovery policy"
                ),
            },
            {
                "layer": "recovery",
                "signal": "automatic_recovery_supervisor_loop",
                "reason": (
                    "no background daemon consumes events; consumers must read "
                    "the contract or the runtime status snapshot directly"
                ),
            },
            {
                "layer": "termination_cause",
                "signal": "load_failure_oom_class_host_forensics_event_classes",
                "reason": (
                    "this round only covers unload-stage cleanup boundary "
                    "events; load-failure and OOM-class events remain future "
                    "four-class recovery policy work"
                ),
            },
        ),
    )


def reclaim_barrier_event_to_dict(
    contract: ReclaimBarrierEventContract,
) -> dict[str, Any]:
    """Serialize the runtime-owned reclaim-barrier-event contract."""

    return {
        "contract": {
            "surface": RECLAIM_BARRIER_EVENT_SURFACE,
            "version": RECLAIM_BARRIER_EVENT_VERSION,
            "stable_sections": [
                "summary",
                "barrier",
                "events",
                "operation_support",
                "policy_boundaries",
                "preserved_invariants",
                "missing_signals",
            ],
        },
        "summary": {
            "status": "partial",
            "barrier_state": contract.barrier_state,
            "confidence": contract.confidence,
            "supported_barrier_states": list(BARRIER_STATE_VOCABULARY),
            "supported_operations": list(OPERATION_VOCABULARY),
            "policy_depth": "operation_boundary_event_recording_only",
        },
        "reason": {
            "code": contract.reason_code,
            "message": contract.reason_message,
        },
        "barrier": contract.barrier,
        "events": [dict(event) for event in contract.events],
        "operation_support": contract.operation_support,
        "policy_boundaries": contract.policy_boundaries,
        "preserved_invariants": list(contract.preserved_invariants),
        "missing_signals": list(contract.missing_signals),
    }


__all__ = [
    "BARRIER_STATE_VOCABULARY",
    "OPERATION_VOCABULARY",
    "RECLAIM_BARRIER_EVENT_SURFACE",
    "RECLAIM_BARRIER_EVENT_VERSION",
    "REQUIRED_EVENT_FIELDS",
    "ReclaimBarrierEventContract",
    "build_reclaim_barrier_event",
    "reclaim_barrier_event_to_dict",
]
