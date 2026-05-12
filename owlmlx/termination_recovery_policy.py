"""Runtime-owned termination recovery policy contract for owlmlx.

Frozen cause-to-action policy on top of the cleanup-boundary event truth
introduced by ``owlmlx.settle_barrier_event`` plus runtime-owned
load-failure events recorded inside ``RuntimeKernel.load_model``.

This module classifies termination causes and emits a frozen action per
required cause class. It does NOT execute the action: no automatic retry
loop, no automatic quarantine daemon, no operator remediation, no
background recovery supervisor. It only freezes policy.

See ``docs/source-of-truth/termination-recovery-policy.md`` for the
authoritative description.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .settle_barrier_event import build_settle_barrier_event


TERMINATION_RECOVERY_POLICY_SURFACE = "owlmlx.termination_recovery_policy"
TERMINATION_RECOVERY_POLICY_VERSION = "v1"

TERMINATION_CAUSE_CLASSES: tuple[str, ...] = (
    "load_failure",
    "oom_class_failure",
    "host_forensics_anomaly",
    "graceful_unload_failure",
    "unknown",
)

TERMINATION_RECOVERY_ACTIONS: tuple[str, ...] = (
    "retry",
    "quarantine",
    "surface_to_coordinator",
    "drop",
)

REQUIRED_DECISION_FIELDS: tuple[str, ...] = (
    "termination_cause_class",
    "next_action",
    "confidence",
    "reason_code",
    "source_signal",
    "operator_visible_message",
    "resolution_rule",
    "forbidden_automation",
    "active",
    "detected_signals",
)

# Priority order for selecting the dominant cause when more than one is
# active. Host forensics anomaly comes first because it is never safe to
# auto-retry; graceful unload failure next because residency state is
# untrusted; OOM-class next because operator must free memory; load
# failure last because it is naturally retryable.
DOMINANT_CAUSE_PRIORITY: tuple[str, ...] = (
    "host_forensics_anomaly",
    "graceful_unload_failure",
    "oom_class_failure",
    "load_failure",
    "unknown",
)


@dataclass(frozen=True, slots=True)
class TerminationCauseDecision:
    termination_cause_class: str
    next_action: str
    confidence: str
    reason_code: str
    source_signal: str
    operator_visible_message: str
    resolution_rule: str
    forbidden_automation: tuple[str, ...]
    active: bool
    detected_signals: tuple[dict[str, Any], ...]


@dataclass(frozen=True, slots=True)
class TerminationRecoveryPolicy:
    dominant_cause: str
    dominant_action: str
    confidence: str
    reason_code: str
    reason_message: str
    cause_decisions: tuple[TerminationCauseDecision, ...]
    active_causes: tuple[str, ...]
    policy_boundaries: dict[str, Any]
    preserved_invariants: tuple[str, ...]
    missing_signals: tuple[dict[str, str], ...]


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _bool_or_none(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _unresolved_load_failure_events(
    raw_status: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    section = _mapping(raw_status.get("load_failure"))
    raw_events = section.get("events")
    events: list[dict[str, Any]] = []
    if isinstance(raw_events, list):
        for entry in raw_events:
            if isinstance(entry, Mapping):
                events.append(dict(entry))
    unresolved = [event for event in events if not event.get("resolved", False)]
    return events, unresolved


def _unresolved_reclaim_barrier_events(
    raw_status: Mapping[str, Any],
) -> list[dict[str, Any]]:
    contract = build_settle_barrier_event(runtime_status=raw_status)
    unresolved = [
        dict(event)
        for event in contract.events
        if not event.get("resolved", False)
    ]
    return unresolved


def _build_graceful_unload_failure_decision(
    *,
    unresolved_reclaim_events: list[dict[str, Any]],
) -> TerminationCauseDecision:
    active = bool(unresolved_reclaim_events)
    return TerminationCauseDecision(
        termination_cause_class="graceful_unload_failure",
        next_action="quarantine",
        confidence="high" if active else "medium",
        reason_code=(
            "reclaim_barrier_event_unresolved_event_visible"
            if active
            else "no_unresolved_reclaim_barrier_event"
        ),
        source_signal="owlmlx.settle_barrier_event",
        operator_visible_message=(
            "Cleanup-boundary failure (failed unload, failed reclaim, or "
            "restart unload stage failure) is visible. Quarantine the "
            "affected model until a successful follow-up operation resolves "
            "the event; the runtime will not auto-retry."
        ),
        resolution_rule=(
            "auto_resolve_on_successful_same_model_followup_operation_in_"
            "matching_operation_family_or_explicit_runtime_kernel_resolve_"
            "reclaim_barrier_event_call"
        ),
        forbidden_automation=(
            "automatic_retry_of_failed_unload",
            "automatic_quarantine_execution",
            "background_recovery_supervisor_loop",
        ),
        active=active,
        detected_signals=tuple(
            {
                "event_id": event.get("event_id"),
                "model_id": event.get("model_id"),
                "operation": event.get("operation"),
                "stage": event.get("stage"),
                "error_code": event.get("error_code"),
            }
            for event in unresolved_reclaim_events
        ),
    )


def _build_load_failure_decision(
    *,
    unresolved_load_events: list[dict[str, Any]],
) -> TerminationCauseDecision:
    matching = [
        event
        for event in unresolved_load_events
        if event.get("cause_class") == "load_failure"
    ]
    active = bool(matching)
    return TerminationCauseDecision(
        termination_cause_class="load_failure",
        next_action="retry",
        confidence="high" if active else "medium",
        reason_code=(
            "load_failure_event_unresolved_event_visible"
            if active
            else "no_unresolved_load_failure_event"
        ),
        source_signal="runtime_kernel.load_model_operation_boundary_event",
        operator_visible_message=(
            "A runtime-owned load-failure event is visible. The request "
            "may be retried by re-invoking load_model; the runtime does "
            "not auto-retry. A successful subsequent load for the same "
            "model id auto-resolves the event."
        ),
        resolution_rule=(
            "auto_resolve_on_successful_same_model_load_through_runtime_kernel_load_model"
        ),
        forbidden_automation=(
            "automatic_retry_loop",
            "background_load_attempt_scheduler",
        ),
        active=active,
        detected_signals=tuple(
            {
                "event_id": event.get("event_id"),
                "model_id": event.get("model_id"),
                "cause_class": event.get("cause_class"),
                "error_code": event.get("error_code"),
            }
            for event in matching
        ),
    )


def _build_oom_class_failure_decision(
    *,
    unresolved_load_events: list[dict[str, Any]],
) -> TerminationCauseDecision:
    matching = [
        event
        for event in unresolved_load_events
        if event.get("cause_class") == "oom_class_failure"
    ]
    active = bool(matching)
    return TerminationCauseDecision(
        termination_cause_class="oom_class_failure",
        next_action="surface_to_coordinator",
        confidence="high" if active else "medium",
        reason_code=(
            "memory_budget_exceeded_event_visible"
            if active
            else "no_unresolved_oom_class_event"
        ),
        source_signal=(
            "runtime_kernel.load_model_event_with_error_code_memory_budget_exceeded"
        ),
        operator_visible_message=(
            "Memory-budget / OOM-class load failure is visible. The runtime "
            "cannot self-resolve this; an operator/coordinator must adjust "
            "the budget, free residency, or change the workload before "
            "retrying."
        ),
        resolution_rule=(
            "auto_resolve_on_successful_same_model_load_after_operator_adjusts_budget_or_residency"
        ),
        forbidden_automation=(
            "automatic_retry_under_oom",
            "automatic_pressure_ranked_eviction",
            "automatic_unload_under_pressure",
        ),
        active=active,
        detected_signals=tuple(
            {
                "event_id": event.get("event_id"),
                "model_id": event.get("model_id"),
                "cause_class": event.get("cause_class"),
                "error_code": event.get("error_code"),
            }
            for event in matching
        ),
    )


def _build_host_forensics_decision(
    *,
    abort_state: str | None,
    recovery_required: bool | None,
    backend_healthy: bool | None,
) -> TerminationCauseDecision:
    contaminated = abort_state == "contaminated" or recovery_required is True
    backend_unhealthy = backend_healthy is False
    active = contaminated or backend_unhealthy
    detected: list[dict[str, Any]] = []
    if contaminated:
        detected.append(
            {
                "signal": "abort_recovery_substrate_contaminated",
                "abort_state": abort_state,
                "recovery_required": recovery_required,
            }
        )
    if backend_unhealthy:
        detected.append(
            {
                "signal": "backend_health_false",
                "backend_healthy": backend_healthy,
            }
        )
    return TerminationCauseDecision(
        termination_cause_class="host_forensics_anomaly",
        next_action="surface_to_coordinator",
        confidence="high" if active else "medium",
        reason_code=(
            "abort_recovery_or_backend_health_anomaly_visible"
            if active
            else "no_host_forensics_anomaly_visible"
        ),
        source_signal=(
            "owlmlx.abort_recovery.snapshot_state_and_recovery_required_plus_runtime_status_summary_backend_healthy"
        ),
        operator_visible_message=(
            "Host-level forensics anomaly is visible (substrate "
            "contamination, recovery-required state, or backend "
            "unhealthy). Surface to coordinator/operator; do not "
            "auto-retry, do not auto-drop, do not auto-quarantine."
        ),
        resolution_rule=(
            "operator_clears_abort_recovery_state_or_restores_backend_health_through_runtime_owned_abort_recovery_apis"
        ),
        forbidden_automation=(
            "automatic_retry_under_host_forensics_anomaly",
            "automatic_drop_under_host_forensics_anomaly",
            "automatic_quarantine_under_host_forensics_anomaly",
            "background_host_forensics_remediation_loop",
        ),
        active=active,
        detected_signals=tuple(detected),
    )


def _build_unknown_decision(
    *,
    runtime_status_present: bool,
) -> TerminationCauseDecision:
    return TerminationCauseDecision(
        termination_cause_class="unknown",
        next_action="surface_to_coordinator",
        confidence="low",
        reason_code=(
            "no_runtime_status_payload_for_termination_cause_classification"
            if not runtime_status_present
            else "no_known_termination_cause_active"
        ),
        source_signal="termination_recovery_policy_fail_safe",
        operator_visible_message=(
            "No runtime-owned termination cause is decisively classifiable. "
            "Fail safe: surface to coordinator/operator and name the missing "
            "signal rather than guess an action."
        ),
        resolution_rule=(
            "wait_for_runtime_status_or_event_truth_to_become_decisive"
        ),
        forbidden_automation=(
            "automatic_retry_when_cause_is_unknown",
            "automatic_drop_when_cause_is_unknown",
            "automatic_quarantine_when_cause_is_unknown",
        ),
        active=not runtime_status_present,
        detected_signals=(
            ({"signal": "runtime_status_missing"},)
            if not runtime_status_present
            else ()
        ),
    )


def _select_dominant(
    decisions: dict[str, TerminationCauseDecision],
) -> tuple[str, str, str, str]:
    for cause in DOMINANT_CAUSE_PRIORITY:
        decision = decisions.get(cause)
        if decision is None:
            continue
        if decision.active:
            return (
                decision.termination_cause_class,
                decision.next_action,
                decision.confidence,
                decision.reason_code,
            )
    # No cause active — return the unknown decision as dominant in a
    # conservative fail-safe shape.
    unknown = decisions["unknown"]
    return (
        "none_active",
        "no_action_required",
        unknown.confidence,
        "no_active_termination_cause",
    )


def build_termination_recovery_policy(
    *,
    runtime_status: Mapping[str, Any] | None = None,
    abort_recovery_snapshot: Mapping[str, Any] | None = None,
) -> TerminationRecoveryPolicy:
    """Build the current runtime-owned termination recovery policy."""

    raw_status = _mapping(runtime_status)
    summary = _mapping(raw_status.get("summary"))
    abort_snapshot = _mapping(
        abort_recovery_snapshot or raw_status.get("abort_recovery")
    )

    backend_healthy = _bool_or_none(summary.get("backend_healthy"))
    abort_state_value = abort_snapshot.get("state")
    abort_state = (
        str(abort_state_value) if isinstance(abort_state_value, str) else None
    )
    recovery_required = _bool_or_none(abort_snapshot.get("recovery_required"))

    _all_load_events, unresolved_load_events = _unresolved_load_failure_events(
        raw_status
    )
    unresolved_reclaim_events = _unresolved_reclaim_barrier_events(raw_status)

    graceful = _build_graceful_unload_failure_decision(
        unresolved_reclaim_events=unresolved_reclaim_events
    )
    load = _build_load_failure_decision(
        unresolved_load_events=unresolved_load_events
    )
    oom = _build_oom_class_failure_decision(
        unresolved_load_events=unresolved_load_events
    )
    host = _build_host_forensics_decision(
        abort_state=abort_state,
        recovery_required=recovery_required,
        backend_healthy=backend_healthy,
    )
    unknown = _build_unknown_decision(
        runtime_status_present=bool(raw_status),
    )

    decisions: dict[str, TerminationCauseDecision] = {
        "load_failure": load,
        "oom_class_failure": oom,
        "host_forensics_anomaly": host,
        "graceful_unload_failure": graceful,
        "unknown": unknown,
    }

    active_causes = tuple(
        cause for cause in DOMINANT_CAUSE_PRIORITY if decisions[cause].active
    )

    dominant_cause, dominant_action, confidence, reason_code = _select_dominant(
        decisions
    )
    if dominant_cause == "none_active":
        reason_message = (
            "No runtime-owned termination cause is currently active. The "
            "policy remains visible for upper-layer consumption but no "
            "next action is recommended."
        )
    else:
        reason_message = decisions[dominant_cause].operator_visible_message

    return TerminationRecoveryPolicy(
        dominant_cause=dominant_cause,
        dominant_action=dominant_action,
        confidence=confidence,
        reason_code=reason_code,
        reason_message=reason_message,
        cause_decisions=tuple(decisions[cause] for cause in TERMINATION_CAUSE_CLASSES),
        active_causes=active_causes,
        policy_boundaries={
            "policy_scope": "termination_cause_classification_and_action_recommendation_only",
            "runtime_owned_termination_recovery_policy": True,
            "automatic_retry_loop": False,
            "automatic_quarantine_execution": False,
            "automatic_recovery_supervisor_loop": False,
            "pressure_ranked_eviction": False,
            "stream_hold_counter": False,
            "owned_actions_visible": [
                "classify_termination_cause_from_runtime_owned_event_truth",
                "recommend_one_of_retry_quarantine_surface_to_coordinator_drop",
                "expose_resolution_rule_per_cause",
                "auto_resolve_event_on_successful_same_model_followup_operation",
                "explicit_resolve_via_runtime_kernel_resolve_reclaim_barrier_event",
            ],
            "out_of_scope": [
                "background_recovery_supervisor_daemon",
                "automatic_retry_loop",
                "automatic_quarantine_execution",
                "operator_remediation_workflow",
                "pressure_ranked_victim_selection",
                "stream_hold_counter_or_duration_tracking",
                "load_attempt_scheduling_or_priority",
            ],
            "non_classifying_paths": [
                "invalid_request_preflight_failure",
                "model_already_loaded_redundant_request",
                "model_not_loaded_unload_preflight_failure",
                "pinned_unload_blocked_before_backend_cleanup",
                "ttl_expired_pinned_model_skipped_by_policy",
            ],
        },
        preserved_invariants=(
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "no_post_claim_gate_bypass",
            "no_hidden_retry_loop",
            "no_automatic_recovery_supervisor_loop",
            "pinned_models_never_evicted",
            "no_pressure_ranked_eviction",
        ),
        missing_signals=(
            {
                "layer": "load",
                "signal": "load_attempt_count_and_repeated_load_failure_signal",
                "reason": (
                    "load failures are recorded at the operation boundary "
                    "but no per-model load-attempt counter is owned; "
                    "load_failure stays per-event"
                ),
            },
            {
                "layer": "oom",
                "signal": "backend_oom_event_distinct_from_runtime_budget_preflight",
                "reason": (
                    "this round only classifies budget-preflight OOM "
                    "(error_code = memory_budget_exceeded) as oom_class_failure; "
                    "backend-side OOM events from runtime processes need a "
                    "future event source"
                ),
            },
            {
                "layer": "host_forensics",
                "signal": "deeper_forensics_signals_beyond_abort_recovery_and_backend_health",
                "reason": (
                    "host forensics anomaly currently consumes only "
                    "abort_recovery substrate state and backend health; "
                    "richer forensics (kernel logs, GPU faults) are future "
                    "work"
                ),
            },
            {
                "layer": "drop",
                "signal": "frozen_drop_action_use_case_for_required_cause_classes",
                "reason": (
                    "the drop action is in the frozen vocabulary but no "
                    "current cause class maps to it; reserved for future "
                    "request-level non-recoverable cases"
                ),
            },
        ),
    )


def termination_cause_decision_to_dict(
    decision: TerminationCauseDecision,
) -> dict[str, Any]:
    return {
        "termination_cause_class": decision.termination_cause_class,
        "next_action": decision.next_action,
        "confidence": decision.confidence,
        "reason_code": decision.reason_code,
        "source_signal": decision.source_signal,
        "operator_visible_message": decision.operator_visible_message,
        "resolution_rule": decision.resolution_rule,
        "forbidden_automation": list(decision.forbidden_automation),
        "active": decision.active,
        "detected_signals": [dict(signal) for signal in decision.detected_signals],
    }


def termination_recovery_policy_to_dict(
    policy: TerminationRecoveryPolicy,
) -> dict[str, Any]:
    """Serialize the runtime-owned termination recovery policy."""

    return {
        "contract": {
            "surface": TERMINATION_RECOVERY_POLICY_SURFACE,
            "version": TERMINATION_RECOVERY_POLICY_VERSION,
            "stable_sections": [
                "summary",
                "reason",
                "cause_decisions",
                "active_causes",
                "policy_boundaries",
                "preserved_invariants",
                "missing_signals",
            ],
        },
        "summary": {
            "status": "partial",
            "dominant_cause": policy.dominant_cause,
            "dominant_action": policy.dominant_action,
            "confidence": policy.confidence,
            "active_cause_count": len(policy.active_causes),
            "supported_causes": list(TERMINATION_CAUSE_CLASSES),
            "supported_actions": list(TERMINATION_RECOVERY_ACTIONS),
            "policy_depth": "termination_cause_classification_and_action_recommendation_only",
        },
        "reason": {
            "code": policy.reason_code,
            "message": policy.reason_message,
        },
        "cause_decisions": [
            termination_cause_decision_to_dict(decision)
            for decision in policy.cause_decisions
        ],
        "active_causes": list(policy.active_causes),
        "policy_boundaries": policy.policy_boundaries,
        "preserved_invariants": list(policy.preserved_invariants),
        "missing_signals": list(policy.missing_signals),
    }


__all__ = [
    "DOMINANT_CAUSE_PRIORITY",
    "REQUIRED_DECISION_FIELDS",
    "TERMINATION_CAUSE_CLASSES",
    "TERMINATION_RECOVERY_ACTIONS",
    "TERMINATION_RECOVERY_POLICY_SURFACE",
    "TERMINATION_RECOVERY_POLICY_VERSION",
    "TerminationCauseDecision",
    "TerminationRecoveryPolicy",
    "build_termination_recovery_policy",
    "termination_cause_decision_to_dict",
    "termination_recovery_policy_to_dict",
]
