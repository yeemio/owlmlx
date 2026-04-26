"""Runtime-owned single-host scheduler admission contract for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from owlmlx.request_context_length_truth import (
    build_request_context_length_truth,
    request_context_length_truth_to_dict,
)
from owlmlx.recovery_supervisor_contract import (
    build_recovery_supervisor_contract,
    recovery_supervisor_contract_to_dict,
)


SCHEDULER_ADMISSION_CONTRACT_SURFACE = "owlmlx.scheduler_admission_contract"
SCHEDULER_ADMISSION_CONTRACT_VERSION = "v1"
_KNOWN_REQUEST_CLASSES = frozenset(
    {"interactive", "stream", "benchmark", "maintenance", "unknown"}
)
_SUPPORTED_GENERATION_REQUEST_CLASSES = frozenset({"interactive", "stream", "benchmark"})


@dataclass(frozen=True, slots=True)
class SchedulerAdmissionDecision:
    """Automatic admission decision built from runtime-owned signals."""

    admission_decision: str
    confidence: str
    reason_code: str
    reason_message: str


@dataclass(frozen=True, slots=True)
class SchedulerAdmissionContract:
    """Stable runtime-owned admission contract for the current scheduler floor."""

    request_class: str
    requested_model_id: str | None
    resolved_model_id: str | None
    admission_decision: str
    confidence: str
    reason_code: str
    reason_message: str
    request_class_support: dict[str, dict[str, Any]]
    boundary: dict[str, Any]
    signals: dict[str, Any]
    preserved_invariants: tuple[str, ...]
    missing_signals: tuple[dict[str, str], ...]


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _normalize_request_class(request_class: str | None) -> str:
    normalized = (request_class or "unknown").strip().lower()
    return normalized if normalized in _KNOWN_REQUEST_CLASSES else "unknown"


def _loaded_model_ids(raw_status: Mapping[str, Any]) -> tuple[str, ...]:
    backend = _mapping(raw_status.get("backend"))
    loaded_models = backend.get("loaded_models")
    if not isinstance(loaded_models, list):
        return ()
    ids = []
    for entry in loaded_models:
        loaded = _mapping(entry)
        model_id = loaded.get("model_id")
        if isinstance(model_id, str) and model_id:
            ids.append(model_id)
    return tuple(sorted(set(ids)))


def _request_class_support() -> dict[str, dict[str, Any]]:
    return {
        "interactive": {
            "classification_status": "supported",
            "automatic_decisions": ["accepted", "deferred", "rejected"],
            "reason_code": "whole_request_generation_classifiable_before_gate_claim",
        },
        "stream": {
            "classification_status": "supported",
            "automatic_decisions": ["accepted", "deferred", "rejected"],
            "reason_code": "stream_requests_share_generation_gate_admission_boundary",
        },
        "benchmark": {
            "classification_status": "supported",
            "automatic_decisions": ["accepted", "deferred", "rejected"],
            "reason_code": "benchmark_requests_follow_same_serial_generation_floor",
        },
        "maintenance": {
            "classification_status": "partial",
            "automatic_decisions": ["unknown"],
            "reason_code": "generic_maintenance_action_contract_not_frozen",
        },
        "unknown": {
            "classification_status": "supported",
            "automatic_decisions": ["unknown"],
            "reason_code": "fallback_request_class_retained_when_runtime_shape_is_weak",
        },
    }


def _build_decision(
    *,
    request_class: str,
    backend_healthy: bool,
    resolved_model_id: str | None,
    loaded_model_ids: tuple[str, ...],
    gate_signal_ready: bool,
    hook_status: str | None,
    gate_state: str | None,
    waiters: int,
    staged_count: int,
    cohort_window_status: str | None,
    recovery_hard_barrier: bool,
    recovery_barrier_decision: str | None,
    recovery_high_context_barrier: bool,
    context_length_classification: str,
) -> SchedulerAdmissionDecision:
    if request_class == "unknown":
        return SchedulerAdmissionDecision(
            admission_decision="unknown",
            confidence="low",
            reason_code="request_class_unknown",
            reason_message=(
                "The runtime does not own enough request-class semantics to make "
                "an automatic admission decision."
            ),
        )
    if request_class == "maintenance":
        return SchedulerAdmissionDecision(
            admission_decision="unknown",
            confidence="low",
            reason_code="maintenance_admission_semantics_not_frozen",
            reason_message=(
                "Generic maintenance traffic is not yet a frozen runtime-owned "
                "admission class on the active path."
            ),
        )
    if not backend_healthy:
        return SchedulerAdmissionDecision(
            admission_decision="rejected",
            confidence="high",
            reason_code="backend_unhealthy_fail_closed",
            reason_message=(
                "The backend is unhealthy, so whole-request generation admission "
                "fails closed on the runtime-owned path."
            ),
        )
    if recovery_hard_barrier:
        return SchedulerAdmissionDecision(
            admission_decision="rejected",
            confidence="high",
            reason_code="recovery_supervisor_hard_barrier",
            reason_message=(
                "The recovery supervisor contract reports a hard recovery barrier "
                f"({recovery_barrier_decision}), so admission fails closed before "
                "whole-request gate claim."
            ),
        )
    if recovery_high_context_barrier and context_length_classification == "high_context":
        return SchedulerAdmissionDecision(
            admission_decision="deferred",
            confidence="high",
            reason_code="recovery_probing_high_context_deferred",
            reason_message=(
                "The recovery supervisor is probing after a high-context abort, "
                "and this request is known high-context, so admission defers "
                "until probe truth is available."
            ),
        )
    if not resolved_model_id:
        return SchedulerAdmissionDecision(
            admission_decision="rejected",
            confidence="high",
            reason_code="no_target_model_resolved",
            reason_message=(
                "No explicit or active resident model is available, and admission "
                "does not invent a residency or load-on-demand policy."
            ),
        )
    if resolved_model_id not in loaded_model_ids:
        return SchedulerAdmissionDecision(
            admission_decision="rejected",
            confidence="high",
            reason_code="target_model_not_resident",
            reason_message=(
                "The requested model is not currently resident on the runtime-owned "
                "path, so admission rejects rather than defers into an unfrozen "
                "residency policy."
            ),
        )
    if not gate_signal_ready:
        return SchedulerAdmissionDecision(
            admission_decision="unknown",
            confidence="low",
            reason_code="generation_gate_floor_signal_missing",
            reason_message=(
                "The validated post-claim GenerationGate floor is not visible "
                "strongly enough to freeze automatic admission."
            ),
        )
    if hook_status != "present":
        return SchedulerAdmissionDecision(
            admission_decision="unknown",
            confidence="low",
            reason_code="pre_claim_admission_signal_missing",
            reason_message=(
                "The bounded pre-claim admission signal is not visible, so the "
                "runtime cannot freeze automatic admission before gate claim."
            ),
        )
    if waiters > 0:
        return SchedulerAdmissionDecision(
            admission_decision="deferred",
            confidence="high",
            reason_code="visible_generation_gate_waiters",
            reason_message=(
                "Visible gate waiters mean the serialized post-claim execution "
                "boundary is already saturated."
            ),
        )
    if gate_state == "active":
        return SchedulerAdmissionDecision(
            admission_decision="deferred",
            confidence="medium",
            reason_code="post_claim_generation_gate_active",
            reason_message=(
                "The serialized GenerationGate is already active, so new work can "
                "only defer before whole-request gate claim."
            ),
        )
    if staged_count > 0 or cohort_window_status in {"open_for_join", "closed_waiting_gate_claim"}:
        return SchedulerAdmissionDecision(
            admission_decision="deferred",
            confidence="medium",
            reason_code="pre_claim_window_already_staged",
            reason_message=(
                "A bounded pre-claim cohort is already staged, so admission defers "
                "rather than bypassing that window."
            ),
        )
    if request_class == "stream":
        return SchedulerAdmissionDecision(
            admission_decision="accepted",
            confidence="medium",
            reason_code="runtime_owned_signals_allow_stream_admission",
            reason_message=(
                "The backend is healthy, the target model is resident, and the "
                "current pre-claim/gate signals do not require defer or reject."
            ),
        )
    return SchedulerAdmissionDecision(
        admission_decision="accepted",
        confidence="medium",
        reason_code="runtime_owned_signals_allow_admission",
        reason_message=(
            "The backend is healthy, the target model is resident, and the current "
            "pre-claim/gate signals do not require defer or reject."
        ),
    )


def build_scheduler_admission_contract(
    *,
    runtime_status: Mapping[str, Any] | None = None,
    request_class: str,
    model_id: str | None = None,
    abort_recovery_snapshot: Mapping[str, Any] | None = None,
    context_tokens: int | str | None = None,
    request_context_class: str | None = None,
) -> SchedulerAdmissionContract:
    """Build the current runtime-owned scheduler admission contract."""

    raw_status = _mapping(runtime_status)
    summary = _mapping(raw_status.get("summary"))
    health = _mapping(raw_status.get("health"))
    budget = _mapping(raw_status.get("budget"))
    restart = _mapping(raw_status.get("restart"))
    generation_gate = _mapping(raw_status.get("generation_gate"))
    pre_gate_admission = _mapping(generation_gate.get("pre_gate_admission"))
    recovery_contract = recovery_supervisor_contract_to_dict(
        build_recovery_supervisor_contract(
            runtime_status=raw_status,
            abort_recovery_snapshot=abort_recovery_snapshot,
        )
    )
    recovery_summary = _mapping(recovery_contract.get("summary"))
    recovery_barrier = _mapping(recovery_contract.get("barrier"))
    context_length_truth = request_context_length_truth_to_dict(
        build_request_context_length_truth(
            context_tokens=context_tokens,
            request_context_class=request_context_class,
        )
    )
    context_length_summary = _mapping(context_length_truth.get("summary"))
    context_length_classification = str(
        context_length_summary.get("classification") or "unknown"
    )

    normalized_request_class = _normalize_request_class(request_class)
    loaded_model_ids = _loaded_model_ids(raw_status)
    active_model_id = raw_status.get("active_model_id") or summary.get("active_model_id")
    resolved_model_id = model_id or active_model_id
    backend_healthy = bool(summary.get("backend_healthy"))
    gate_state = generation_gate.get("generation_gate")
    waiters = int(generation_gate.get("waiters") or 0)
    staged_count = int(pre_gate_admission.get("staged_count") or 0)
    hook_status = pre_gate_admission.get("hook_status")
    queue_policy = generation_gate.get("queue_policy")
    queue_discipline = generation_gate.get("queue_discipline")
    max_concurrent = generation_gate.get("max_concurrent")
    gate_signal_ready = (
        queue_policy == "ticketed_fifo"
        and queue_discipline == "serial"
        and max_concurrent == 1
    )
    decision = _build_decision(
        request_class=normalized_request_class,
        backend_healthy=backend_healthy,
        resolved_model_id=resolved_model_id,
        loaded_model_ids=loaded_model_ids,
        gate_signal_ready=gate_signal_ready,
        hook_status=hook_status,
        gate_state=gate_state,
        waiters=waiters,
        staged_count=staged_count,
        cohort_window_status=pre_gate_admission.get("cohort_window_status"),
        recovery_hard_barrier=bool(recovery_barrier.get("hard_recovery_barrier", False)),
        recovery_barrier_decision=(
            str(recovery_summary.get("barrier_decision"))
            if recovery_summary.get("barrier_decision") is not None
            else None
        ),
        recovery_high_context_barrier=bool(
            recovery_barrier.get("high_context_barrier", False)
        ),
        context_length_classification=context_length_classification,
    )

    preserved_invariants = tuple(
        str(item)
        for item in pre_gate_admission.get("preserved_post_claim_invariants", [])
        if isinstance(item, str) and item
    )
    forbidden_expansions = tuple(
        str(item)
        for item in pre_gate_admission.get("forbidden_expansions", [])
        if isinstance(item, str) and item
    )
    if (
        "no_bypass_of_whole_request_gate_claim" in forbidden_expansions
        and "no_hidden_bypass_of_whole_request_gate_claim" not in preserved_invariants
    ):
        preserved_invariants = preserved_invariants + (
            "no_hidden_bypass_of_whole_request_gate_claim",
        )

    missing_signals: list[dict[str, str]] = [
        {
            "layer": "memory_pressure",
            "signal": "runtime_owned_pressure_event_or_reclaim_barrier",
            "reason": "budget truth exists but direct pressure/reclaim admission truth does not",
        },
        {
            "layer": "stream_hold",
            "signal": "live_stream_hold_counter_or_duration_signal",
            "reason": "stream requests share the same gate boundary, but hold depth is not directly visible",
        },
        {
            "layer": "maintenance",
            "signal": "runtime_owned_maintenance_action_subtype_contract",
            "reason": "generic maintenance traffic cannot be auto-classified without narrower action semantics",
        },
        {
            "layer": "model_residency",
            "signal": "runtime_owned_load_on_demand_or_defer_to_load_policy",
            "reason": "non-resident target requests reject because admission does not yet own residency deferral semantics",
        },
    ]
    if not gate_signal_ready:
        missing_signals.append(
            {
                "layer": "generation_gate",
                "signal": "validated_serial_ticketed_fifo_generation_gate_floor",
                "reason": "automatic admission depends on seeing the current post-claim safety floor exactly",
            }
        )
    if hook_status != "present":
        missing_signals.append(
            {
                "layer": "pre_gate_admission",
                "signal": "bounded_pre_claim_admission_window",
                "reason": "automatic admission before gate claim depends on the current bounded pre-claim seam",
            }
        )
    if context_length_classification == "unknown":
        missing_signals.extend(
            {
                "layer": str(item.get("layer", "request_context_length")),
                "signal": str(item.get("signal", "runtime_visible_context_tokens")),
                "reason": str(item.get("reason", "")),
            }
            for item in context_length_truth.get("missing_signals", [])
            if isinstance(item, Mapping)
        )

    request_class_support = _request_class_support()
    return SchedulerAdmissionContract(
        request_class=normalized_request_class,
        requested_model_id=model_id,
        resolved_model_id=resolved_model_id,
        admission_decision=decision.admission_decision,
        confidence=decision.confidence,
        reason_code=decision.reason_code,
        reason_message=decision.reason_message,
        request_class_support=request_class_support,
        boundary={
            "admission_boundary": pre_gate_admission.get(
                "hook_boundary", "before_whole_request_gate_claim"
            ),
            "generation_gate_role": "validated_post_claim_serial_safety_boundary",
            "post_claim_execution_floor": "serial_ticketed_fifo_max_concurrent_1",
            "decision_scope": "automatic_admission_only",
            "out_of_scope": [
                "continuous_batching",
                "multi_worker_scheduler_depth",
                "model_residency_policy",
                "memory_pressure_policy",
                "recovery_policy",
            ],
        },
        signals={
            "generation_gate": {
                "generation_gate": gate_state,
                "queue_policy": queue_policy,
                "queue_discipline": queue_discipline,
                "max_concurrent": max_concurrent,
                "waiters": waiters,
                "classification_status": "supported" if gate_signal_ready else "unknown",
                "decision_impact": (
                    "defer_when_active_or_waiters_visible"
                    if gate_signal_ready
                    else "cannot_freeze_automatic_admission"
                ),
            },
            "pre_gate_admission": {
                "hook_status": hook_status,
                "hook_boundary": pre_gate_admission.get("hook_boundary"),
                "hook_mode": pre_gate_admission.get("hook_mode"),
                "cohort_window_status": pre_gate_admission.get("cohort_window_status"),
                "cohort_count": pre_gate_admission.get("cohort_count"),
                "open_cohort_size": pre_gate_admission.get("open_cohort_size"),
                "staged_count": staged_count,
                "classification_status": "supported" if hook_status == "present" else "unknown",
                "decision_impact": (
                    "defer_when_window_is_already_staged"
                    if hook_status == "present"
                    else "cannot_freeze_pre_claim_admission"
                ),
            },
            "residency": {
                "requested_model_id": model_id,
                "resolved_model_id": resolved_model_id,
                "active_model_id": active_model_id,
                "loaded_model_ids": list(loaded_model_ids),
                "loaded_model_count": len(loaded_model_ids),
                "target_model_resident": resolved_model_id in loaded_model_ids
                if resolved_model_id
                else False,
                "classification_status": "partial",
                "decision_impact": "reject_when_no_resident_target_is_available",
            },
            "budget": {
                "serving_budget_gb": budget.get("serving_budget_gb"),
                "currently_loaded_gb": budget.get("currently_loaded_gb"),
                "available_gb": budget.get("available_gb"),
                "utilization": budget.get("utilization"),
                "classification_status": "insufficient_signal",
                "decision_impact": "informational_only_not_admission_decisive",
            },
            "recovery": {
                "backend_healthy": backend_healthy,
                "readiness": health.get("readiness") or summary.get("readiness"),
                "restartable_models": list(restart.get("restartable_models", [])),
                "restart_exhausted_models": list(restart.get("restart_exhausted_models", [])),
                "auto_restart_dead_session": bool(restart.get("auto_restart_dead_session", False)),
                "recovery_state": recovery_summary.get("recovery_state"),
                "barrier_decision": recovery_summary.get("barrier_decision"),
                "hard_recovery_barrier": recovery_barrier.get("hard_recovery_barrier"),
                "high_context_barrier": recovery_barrier.get("high_context_barrier"),
                "classification_status": (
                    "supported"
                    if recovery_barrier.get("classification_status") == "supported"
                    else "partial"
                ),
                "decision_impact": (
                    "backend_unhealthy_rejects_generation_requests"
                    if not backend_healthy
                    else "hard_recovery_barrier_rejects_generation"
                    if recovery_barrier.get("hard_recovery_barrier") is True
                    else "high_context_barrier_defers_known_high_context"
                    if recovery_barrier.get("high_context_barrier") is True
                    and context_length_classification == "high_context"
                    else "high_context_barrier_not_decisive_for_known_non_high_context"
                    if recovery_barrier.get("high_context_barrier") is True
                    and context_length_classification == "non_high_context"
                    else "high_context_barrier_visible_without_request_context_length"
                    if recovery_barrier.get("high_context_barrier") is True
                    else "non_decisive_context_only"
                ),
            },
            "request_context_length": {
                "classification": context_length_classification,
                "confidence": context_length_summary.get("confidence"),
                "context_tokens": context_length_summary.get("context_tokens"),
                "thresholds": context_length_truth.get("thresholds"),
                "source": context_length_truth.get("source"),
                "classification_status": (
                    "supported"
                    if context_length_classification
                    in {"high_context", "non_high_context"}
                    else "insufficient_signal"
                ),
                "decision_impact": (
                    "recovery_probing_defers_this_high_context_request"
                    if recovery_barrier.get("high_context_barrier") is True
                    and context_length_classification == "high_context"
                    else "recovery_probing_does_not_block_this_non_high_context_request"
                    if recovery_barrier.get("high_context_barrier") is True
                    and context_length_classification == "non_high_context"
                    else "unknown_context_keeps_recovery_probing_non_global"
                    if recovery_barrier.get("high_context_barrier") is True
                    else "informational_for_current_admission"
                ),
            },
            "stream_hold": {
                "shared_boundary": "generation_gate",
                "classification_status": "partial",
                "decision_impact": (
                    "stream_requests_use_same_admission_boundary_but_hold_depth_is_not_runtime_owned"
                ),
                "request_class_runtime_owned": normalized_request_class in _SUPPORTED_GENERATION_REQUEST_CLASSES,
            },
        },
        preserved_invariants=preserved_invariants
        or (
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
            "no_hidden_bypass_of_whole_request_gate_claim",
        ),
        missing_signals=tuple(missing_signals),
    )


def scheduler_admission_contract_to_dict(
    contract: SchedulerAdmissionContract,
) -> dict[str, Any]:
    """Serialize the runtime-owned scheduler admission contract."""

    return {
        "contract": {
            "surface": SCHEDULER_ADMISSION_CONTRACT_SURFACE,
            "version": SCHEDULER_ADMISSION_CONTRACT_VERSION,
            "stable_sections": [
                "summary",
                "reason",
                "request_class_support",
                "boundary",
                "signals",
                "preserved_invariants",
                "missing_signals",
            ],
        },
        "summary": {
            "status": "partial",
            "request_class": contract.request_class,
            "requested_model_id": contract.requested_model_id,
            "resolved_model_id": contract.resolved_model_id,
            "admission_decision": contract.admission_decision,
            "confidence": contract.confidence,
        },
        "reason": {
            "code": contract.reason_code,
            "message": contract.reason_message,
        },
        "request_class_support": contract.request_class_support,
        "boundary": contract.boundary,
        "signals": contract.signals,
        "preserved_invariants": list(contract.preserved_invariants),
        "missing_signals": list(contract.missing_signals),
    }
