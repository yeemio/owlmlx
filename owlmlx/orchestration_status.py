"""Runtime-owned single-host orchestration assessment surface for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from owlmlx.memory_pressure_contract import (
    build_memory_pressure_contract,
    memory_pressure_contract_to_dict,
)
from owlmlx.model_residency_policy import (
    build_model_residency_policy,
    model_residency_policy_to_dict,
)
from owlmlx.scheduler_admission_contract import (
    build_scheduler_admission_contract,
    scheduler_admission_contract_to_dict,
)
from owlmlx.recovery_supervisor_contract import (
    build_recovery_supervisor_contract,
    recovery_supervisor_contract_to_dict,
)


ORCHESTRATION_STATUS_SURFACE = "owlmlx.orchestration_status"
ORCHESTRATION_STATUS_VERSION = "v1"


@dataclass(frozen=True, slots=True)
class OrchestrationLayerAssessment:
    """Assessment status for one orchestration bottleneck layer."""

    classification_status: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class OrchestrationStatus:
    """Stable runtime-owned orchestration assessment for current owlmlx truth."""

    bottleneck_layer: str
    confidence: str
    layer_assessment: dict[str, OrchestrationLayerAssessment]
    scheduler: dict[str, Any]
    stream: dict[str, Any]
    residency: dict[str, Any]
    pressure: dict[str, Any]
    recovery: dict[str, Any]
    child_surfaces: dict[str, Any]
    preserved_invariants: tuple[str, ...]
    upstream_truth_sources: tuple[str, ...]
    missing_signals: tuple[dict[str, str], ...]


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _prefixed_missing_signals(
    *,
    source: str,
    missing_signals: object,
) -> tuple[dict[str, str], ...]:
    prefixed = []
    for item in _items(missing_signals):
        layer = item.get("layer")
        signal = item.get("signal")
        reason = item.get("reason")
        if not isinstance(layer, str) or not isinstance(signal, str):
            continue
        prefixed.append(
            {
                "source": source,
                "layer": layer,
                "signal": signal,
                "reason": reason if isinstance(reason, str) else "",
            }
        )
    return tuple(prefixed)


def _infer_bottleneck_layer(
    *,
    admission: Mapping[str, Any],
    pressure: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> tuple[str, str, str]:
    pressure_summary = _mapping(pressure.get("summary"))
    admission_summary = _mapping(admission.get("summary"))
    admission_reason = _mapping(admission.get("reason"))
    recovery_barrier = _mapping(recovery.get("barrier"))
    recovery_reason = _mapping(recovery.get("reason"))

    if recovery_barrier.get("hard_recovery_barrier") is True:
        reason_code = recovery_reason.get("code")
        return (
            "recovery",
            "high",
            str(reason_code or "recovery_supervisor_hard_barrier"),
        )
    if pressure_summary.get("pressure_classification") == "over_budget":
        return ("memory_pressure", "high", "memory_pressure_contract_over_budget")
    if admission_summary.get("admission_decision") == "deferred":
        reason_code = admission_reason.get("code")
        if reason_code == "pre_claim_window_already_staged":
            return ("admission", "high", "scheduler_admission_deferred_pre_claim")
        if reason_code in {
            "visible_generation_gate_waiters",
            "post_claim_generation_gate_active",
        }:
            return ("generation_gate", "high", "scheduler_admission_deferred_generation_gate")
        return ("admission", "medium", "scheduler_admission_deferred")
    return ("unknown", "low", "no_composed_child_surface_dominant_layer")


def build_orchestration_status(
    *,
    runtime_status: Mapping[str, Any] | None = None,
    abort_recovery_snapshot: Mapping[str, Any] | None = None,
) -> OrchestrationStatus:
    """Build the current runtime-owned orchestration assessment."""

    raw_status = _mapping(runtime_status)
    summary = _mapping(raw_status.get("summary"))
    generation_gate = _mapping(raw_status.get("generation_gate"))
    pre_gate_admission = _mapping(generation_gate.get("pre_gate_admission"))
    admission_contract = scheduler_admission_contract_to_dict(
        build_scheduler_admission_contract(
            runtime_status=raw_status,
            request_class="interactive",
            abort_recovery_snapshot=abort_recovery_snapshot,
        )
    )
    residency_policy = model_residency_policy_to_dict(
        build_model_residency_policy(runtime_status=raw_status)
    )
    pressure_contract = memory_pressure_contract_to_dict(
        build_memory_pressure_contract(runtime_status=raw_status)
    )
    recovery_contract = recovery_supervisor_contract_to_dict(
        build_recovery_supervisor_contract(
            runtime_status=raw_status,
            abort_recovery_snapshot=abort_recovery_snapshot,
        )
    )

    admission_summary = _mapping(admission_contract.get("summary"))
    admission_reason = _mapping(admission_contract.get("reason"))
    residency_summary = _mapping(residency_policy.get("summary"))
    target_model = _mapping(residency_policy.get("target_model"))
    pressure_summary = _mapping(pressure_contract.get("summary"))
    pressure_reason = _mapping(pressure_contract.get("reason"))
    pressure_boundaries = _mapping(pressure_contract.get("policy_boundaries"))
    recovery_summary = _mapping(recovery_contract.get("summary"))
    recovery_barrier = _mapping(recovery_contract.get("barrier"))
    recovery_restart = _mapping(recovery_contract.get("restart"))
    recovery_lifecycle = _mapping(recovery_contract.get("lifecycle"))
    residency_signals = _mapping(residency_policy.get("signals"))
    pressure_residency_context = _mapping(pressure_contract.get("residency_context"))
    recovery_context = _mapping(pressure_contract.get("recovery_context"))
    admission_signals = _mapping(admission_contract.get("signals"))
    admission_gate = _mapping(admission_signals.get("generation_gate"))
    admission_pre_gate = _mapping(admission_signals.get("pre_gate_admission"))
    admission_context_length = _mapping(admission_signals.get("request_context_length"))

    bottleneck_layer, confidence, summary_reason_code = _infer_bottleneck_layer(
        admission=admission_contract,
        pressure=pressure_contract,
        recovery=recovery_contract,
    )

    layer_assessment = {
        "admission": OrchestrationLayerAssessment(
            classification_status="supported",
            reason_code=str(admission_reason.get("code") or "scheduler_admission_contract_visible"),
        ),
        "generation_gate": OrchestrationLayerAssessment(
            classification_status=(
                "supported"
                if admission_gate.get("classification_status") == "supported"
                else "unknown"
            ),
            reason_code=(
                "serial_ticketed_fifo_generation_gate_floor_composed"
                if admission_gate.get("classification_status") == "supported"
                else "generation_gate_signal_absent"
            ),
        ),
        "stream_hold": OrchestrationLayerAssessment(
            classification_status="partial",
            reason_code="shared_stream_boundary_visible_without_live_hold_counter",
        ),
        "model_residency": OrchestrationLayerAssessment(
            classification_status="partial",
            reason_code=str(
                target_model.get("reason_code")
                or "model_residency_policy_visible_without_load_on_demand"
            ),
        ),
        "memory_pressure": OrchestrationLayerAssessment(
            classification_status=(
                "partial"
                if pressure_summary.get("pressure_classification")
                in {"within_budget", "near_budget", "over_budget"}
                else "insufficient_signal"
            ),
            reason_code=str(pressure_reason.get("code") or "pressure_contract_missing"),
        ),
        "recovery": OrchestrationLayerAssessment(
            classification_status="partial",
            reason_code=str(
                recovery_barrier.get("reason_code")
                or "recovery_supervisor_contract_visible_without_full_recovery_loop"
            ),
        ),
        "unknown": OrchestrationLayerAssessment(
            classification_status="supported",
            reason_code="fallback_layer_retained_when_runtime_signal_is_weak",
        ),
    }

    child_missing_signals = (
        _prefixed_missing_signals(
            source="owlmlx.scheduler_admission_contract",
            missing_signals=admission_contract.get("missing_signals"),
        )
        + _prefixed_missing_signals(
            source="owlmlx.model_residency_policy",
            missing_signals=residency_policy.get("missing_signals"),
        )
        + _prefixed_missing_signals(
            source="owlmlx.memory_pressure_contract",
            missing_signals=pressure_contract.get("missing_signals"),
        )
        + _prefixed_missing_signals(
            source="owlmlx.recovery_supervisor_contract",
            missing_signals=recovery_contract.get("missing_signals"),
        )
    )
    preserved_invariants = tuple(
        str(item)
        for item in admission_contract.get("preserved_invariants", [])
        if isinstance(item, str) and item
    )

    return OrchestrationStatus(
        bottleneck_layer=bottleneck_layer,
        confidence=confidence,
        layer_assessment=layer_assessment,
        scheduler={
            "admission_decision": admission_summary.get("admission_decision"),
            "request_class": admission_summary.get("request_class"),
            "resolved_model_id": admission_summary.get("resolved_model_id"),
            "reason_code": summary_reason_code,
            "admission_reason_code": admission_reason.get("code"),
            "generation_gate": admission_gate.get("generation_gate"),
            "queue_policy": admission_gate.get("queue_policy"),
            "queue_discipline": admission_gate.get("queue_discipline"),
            "max_concurrent": admission_gate.get("max_concurrent"),
            "waiters": admission_gate.get("waiters", 0),
            "pre_gate_admission": {
                "hook_status": admission_pre_gate.get("hook_status"),
                "hook_boundary": admission_pre_gate.get("hook_boundary")
                or pre_gate_admission.get("hook_boundary"),
                "hook_mode": admission_pre_gate.get("hook_mode"),
                "cohort_window_status": admission_pre_gate.get("cohort_window_status"),
                "cohort_count": admission_pre_gate.get("cohort_count"),
                "staged_count": admission_pre_gate.get("staged_count", 0),
            },
            "request_context_length": {
                "classification": admission_context_length.get("classification"),
                "confidence": admission_context_length.get("confidence"),
                "context_tokens": admission_context_length.get("context_tokens"),
                "classification_status": admission_context_length.get(
                    "classification_status"
                ),
                "decision_impact": admission_context_length.get("decision_impact"),
            },
        },
        stream={
            "shared_boundary": "generation_gate",
            "hold_scope": "backend_producer_turn",
            "consumer_drain_position": "outside_generation_gate",
            "classification_status": layer_assessment["stream_hold"].classification_status,
            "reason_code": layer_assessment["stream_hold"].reason_code,
        },
        residency={
            "active_model_id": _mapping(residency_signals.get("inventory")).get(
                "active_model_id"
            )
            or raw_status.get("active_model_id")
            or summary.get("active_model_id"),
            "resident_model_count": residency_summary.get("resident_model_count"),
            "target_model": target_model,
            "pinned_model_count": _mapping(residency_signals.get("pinning")).get(
                "pinned_model_count"
            ),
            "ttl_policy_count": _mapping(residency_signals.get("ttl")).get(
                "ttl_policy_count"
            ),
            "eviction_history_count": _mapping(
                residency_signals.get("eviction_history")
            ).get("eviction_history_count"),
            "classification_status": layer_assessment["model_residency"].classification_status,
            "reason_code": layer_assessment["model_residency"].reason_code,
        },
        pressure={
            "pressure_classification": pressure_summary.get("pressure_classification"),
            "serving_budget_gb": _mapping(pressure_contract.get("budget")).get(
                "serving_budget_gb"
            ),
            "currently_loaded_gb": _mapping(pressure_contract.get("budget")).get(
                "currently_loaded_gb"
            ),
            "available_gb": _mapping(pressure_contract.get("budget")).get("available_gb"),
            "utilization": _mapping(pressure_contract.get("budget")).get("utilization"),
            "ttl_sweep_evictable_model_count": pressure_residency_context.get(
                "ttl_sweep_evictable_model_count"
            ),
            "runtime_owned_pressure_victim_selection": pressure_boundaries.get(
                "runtime_owned_pressure_victim_selection"
            ),
            "classification_status": layer_assessment["memory_pressure"].classification_status,
            "reason_code": layer_assessment["memory_pressure"].reason_code,
        },
        recovery={
            "recovery_state": recovery_summary.get("recovery_state"),
            "barrier_decision": recovery_summary.get("barrier_decision"),
            "hard_recovery_barrier": recovery_barrier.get("hard_recovery_barrier"),
            "high_context_barrier": recovery_barrier.get("high_context_barrier"),
            "backend_healthy": recovery_restart.get("backend_healthy"),
            "restartable_model_count": len(recovery_restart.get("restartable_models", [])),
            "restart_exhausted_model_count": len(
                recovery_restart.get("restart_exhausted_models", [])
            ),
            "auto_restart_dead_session": bool(
                recovery_restart.get("auto_restart_dead_session", False)
            ),
            "recovery_context_classification_status": recovery_context.get(
                "classification_status"
            ),
            "recent_window_runs": recovery_lifecycle.get("recent_window_runs", 0),
            "restart_restore_visible": bool(recovery_lifecycle.get("restart_restore_visible", False)),
            "classification_status": layer_assessment["recovery"].classification_status,
            "reason_code": layer_assessment["recovery"].reason_code,
        },
        child_surfaces={
            "admission": {
                "surface": admission_contract["contract"]["surface"],
                "version": admission_contract["contract"]["version"],
                "summary": admission_contract["summary"],
                "reason": admission_contract["reason"],
            },
            "model_residency": {
                "surface": residency_policy["contract"]["surface"],
                "version": residency_policy["contract"]["version"],
                "summary": residency_policy["summary"],
                "target_model": residency_policy["target_model"],
            },
            "memory_pressure": {
                "surface": pressure_contract["contract"]["surface"],
                "version": pressure_contract["contract"]["version"],
                "summary": pressure_contract["summary"],
                "reason": pressure_contract["reason"],
            },
            "recovery_supervisor": {
                "surface": recovery_contract["contract"]["surface"],
                "version": recovery_contract["contract"]["version"],
                "summary": recovery_contract["summary"],
                "reason": recovery_contract["reason"],
            },
        },
        preserved_invariants=preserved_invariants
        or (
            "max_concurrent_1_after_gate_claim",
            "ticketed_fifo_after_gate_claim",
            "serial_safety_validated_only_after_gate_claim",
            "no_hidden_bypass_of_whole_request_gate_claim",
        ),
        upstream_truth_sources=(
            "owlmlx.scheduler_admission_contract",
            "owlmlx.request_context_length_truth",
            "owlmlx.model_residency_policy",
            "owlmlx.memory_pressure_contract",
            "owlmlx.recovery_supervisor_contract",
            "owlmlx.runtime.status.restart",
            "owlmlx.runtime.status.governance_observations",
        ),
        missing_signals=child_missing_signals
        + (
            {
                "layer": "memory_pressure",
                "signal": "runtime_owned_pressure_event_or_reclaim_barrier",
                "reason": "budget truth exists but direct pressure/reclaim bottleneck truth does not",
            },
            {
                "layer": "recovery",
                "signal": "runtime_owned_recovery_barrier_or_failed_reclaim_contract",
                "reason": "restart visibility exists but full recovery bottleneck truth does not",
            },
            {
                "layer": "stream_hold",
                "signal": "live_stream_hold_counter_or_duration_signal",
                "reason": "shared-boundary stream semantics are visible but direct hold counters are not",
            },
        ),
    )


def orchestration_status_to_dict(status: OrchestrationStatus) -> dict[str, Any]:
    """Serialize the runtime-owned orchestration assessment."""

    return {
        "contract": {
            "surface": ORCHESTRATION_STATUS_SURFACE,
            "version": ORCHESTRATION_STATUS_VERSION,
            "stable_sections": [
                "summary",
                "layer_assessment",
                "scheduler",
                "stream",
                "residency",
                "pressure",
                "recovery",
                "child_surfaces",
                "preserved_invariants",
                "upstream_truth_sources",
                "missing_signals",
            ],
        },
        "summary": {
            "status": "partial",
            "bottleneck_layer": status.bottleneck_layer,
            "confidence": status.confidence,
        },
        "layer_assessment": {
            layer: {
                "classification_status": assessment.classification_status,
                "reason_code": assessment.reason_code,
            }
            for layer, assessment in status.layer_assessment.items()
        },
        "scheduler": status.scheduler,
        "stream": status.stream,
        "residency": status.residency,
        "pressure": status.pressure,
        "recovery": status.recovery,
        "child_surfaces": status.child_surfaces,
        "preserved_invariants": list(status.preserved_invariants),
        "upstream_truth_sources": list(status.upstream_truth_sources),
        "missing_signals": list(status.missing_signals),
    }
