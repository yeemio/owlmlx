"""Runtime-owned single-host memory-pressure eviction policy contract for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .memory_pressure_contract import (
    MemoryPressureContract,
    build_memory_pressure_contract,
)
from .model_residency_policy import (
    ModelResidencyPolicy,
    build_model_residency_policy,
)
from .recovery_supervisor_contract import (
    RecoverySupervisorContract,
    build_recovery_supervisor_contract,
)


MEMORY_PRESSURE_EVICTION_POLICY_SURFACE = "owlmlx.memory_pressure_eviction_policy"
MEMORY_PRESSURE_EVICTION_POLICY_VERSION = "v1"
MEMORY_PRESSURE_EVICTION_DECISIONS = (
    "evict",
    "defer",
    "reject",
    "unknown",
)
PRESERVED_INVARIANTS: tuple[str, ...] = (
    "max_concurrent_1_after_gate_claim",
    "ticketed_fifo_after_gate_claim",
    "no_post_claim_gate_bypass",
    "pinned_models_never_evicted",
    "no_automatic_background_eviction_loop",
)


@dataclass(frozen=True, slots=True)
class MemoryPressureEvictionPolicy:
    """Stable runtime-owned memory-pressure eviction decision."""

    decision: str
    confidence: str
    reason_code: str
    reason_message: str
    selected_victim: dict[str, Any] | None
    candidate_order: tuple[dict[str, Any], ...]
    pressure: dict[str, Any]
    residency_summary: dict[str, Any]
    recovery_summary: dict[str, Any]
    blocking_signals: tuple[dict[str, str], ...]
    preserved_invariants: tuple[str, ...]
    decision_support: dict[str, dict[str, Any]]
    missing_signals: tuple[dict[str, str], ...]
    inputs: dict[str, Any]


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _list_of_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) and not isinstance(value, tuple):
        return ()
    return tuple(str(item) for item in value if isinstance(item, str) and item)


def _decision_support() -> dict[str, dict[str, Any]]:
    return {
        "evict": {
            "decision_status": "supported",
            "reason_code": "over_budget_with_safe_unpinned_candidate_available",
        },
        "defer": {
            "decision_status": "supported",
            "reason_code": "pressure_not_strong_enough_or_named_precondition_pending",
        },
        "reject": {
            "decision_status": "supported",
            "reason_code": "over_budget_but_no_safe_candidate_or_recovery_unsafe",
        },
        "unknown": {
            "decision_status": "supported",
            "reason_code": "required_pressure_or_residency_truth_absent",
        },
    }


def _candidate_sort_key(candidate: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        1 if candidate["pinned"] else 0,
        0 if candidate["ttl_expired_unpinned"] else 1,
        1 if candidate["active_protected"] else 0,
        -float(candidate["memory_gb"] or 0.0),
        str(candidate["model_id"]),
    )


def _build_candidates(
    *,
    raw_status: Mapping[str, Any],
    protect_active: bool,
) -> tuple[list[dict[str, Any]], str | None]:
    backend = _mapping(raw_status.get("backend"))
    summary = _mapping(raw_status.get("summary"))
    governance_policy = _mapping(raw_status.get("governance_policy"))

    active_raw = raw_status.get("active_model_id") or summary.get("active_model_id")
    active_model_id = active_raw if isinstance(active_raw, str) and active_raw else None

    pinned_ids = set(_list_of_strings(governance_policy.get("pinned_model_ids")))
    ttl_expired_ids = set(
        _list_of_strings(governance_policy.get("ttl_expired_model_ids"))
    )
    ttl_expired_pinned_ids = set(
        _list_of_strings(governance_policy.get("ttl_expired_pinned_model_ids"))
    )

    loaded_raw = backend.get("loaded_models")
    loaded = loaded_raw if isinstance(loaded_raw, list) else []

    candidates: list[dict[str, Any]] = []
    for entry in loaded:
        if not isinstance(entry, Mapping):
            continue
        model_id = entry.get("model_id")
        if not isinstance(model_id, str) or not model_id:
            continue
        memory_value = entry.get("memory_gb")
        try:
            memory_gb = float(memory_value) if memory_value is not None else 0.0
        except (TypeError, ValueError):
            memory_gb = 0.0
        is_pinned = model_id in pinned_ids
        is_active = model_id == active_model_id
        is_ttl_expired_unpinned = (
            model_id in ttl_expired_ids and model_id not in ttl_expired_pinned_ids
        )
        active_protected = bool(protect_active and is_active)
        eligible = (not is_pinned) and (not active_protected)
        if is_pinned:
            ordering_reason = "blocked_by_pin"
        elif is_ttl_expired_unpinned:
            ordering_reason = "ttl_expired_unpinned"
        elif active_protected:
            ordering_reason = "active_model_protected"
        else:
            ordering_reason = "manual_unload_eligible"
        candidates.append(
            {
                "model_id": model_id,
                "memory_gb": memory_gb,
                "pinned": is_pinned,
                "active": is_active,
                "active_protected": active_protected,
                "ttl_expired_unpinned": is_ttl_expired_unpinned,
                "eligible": eligible,
                "ordering_reason": ordering_reason,
            }
        )

    candidates.sort(key=_candidate_sort_key)
    return candidates, active_model_id


def _classify(
    *,
    pressure: MemoryPressureContract,
    recovery: RecoverySupervisorContract,
    candidates: list[dict[str, Any]],
    active_model_id: str | None,
    protect_active: bool,
) -> tuple[
    str,
    str,
    str,
    str,
    dict[str, Any] | None,
    tuple[dict[str, str], ...],
]:
    """Return (decision, confidence, reason_code, reason_message, selected_victim, blocking_signals)."""

    if recovery.barrier["hard_recovery_barrier"]:
        return (
            "reject",
            "high",
            "recovery_hard_barrier_eviction_unsafe",
            (
                "Recovery supervisor reports a hard barrier; eviction would land "
                "into an unsafe substrate, so memory-pressure eviction rejects."
            ),
            None,
            (
                {
                    "layer": "recovery",
                    "signal": recovery.barrier["reason_code"],
                    "reason": recovery.reason_message,
                },
            ),
        )

    if pressure.pressure_classification in {"unknown", "insufficient_signal"}:
        return (
            "unknown",
            "low",
            "pressure_truth_absent_for_eviction_decision",
            (
                "Memory pressure truth is absent or incomplete; eviction cannot "
                "be honestly decided without a runtime-owned pressure signal."
            ),
            None,
            (
                {
                    "layer": "memory_pressure",
                    "signal": "budget_snapshot",
                    "reason": pressure.reason_message,
                },
            ),
        )

    if pressure.pressure_classification == "within_budget":
        return (
            "defer",
            "medium",
            "within_budget_no_pressure_trigger",
            (
                "Memory pressure is within_budget; runtime does not evict "
                "without a pressure trigger."
            ),
            None,
            (),
        )

    if pressure.pressure_classification == "near_budget":
        return (
            "defer",
            "medium",
            "near_budget_pressure_not_strong_enough_to_evict",
            (
                "Memory pressure is near_budget; the policy defers eviction "
                "until pressure escalates to over_budget."
            ),
            None,
            (),
        )

    # Over-budget path: select first eligible candidate.
    eligible_candidates = [c for c in candidates if c["eligible"]]
    if not candidates:
        return (
            "reject",
            "high",
            "over_budget_but_no_resident_candidate",
            (
                "Memory pressure is over_budget but no resident model is "
                "available to evict."
            ),
            None,
            (
                {
                    "layer": "residency",
                    "signal": "no_resident_models",
                    "reason": (
                        "loaded inventory is empty, so no eviction candidate "
                        "can be selected"
                    ),
                },
            ),
        )
    if not eligible_candidates:
        all_pinned = all(c["pinned"] for c in candidates)
        only_active_protected = (
            not all_pinned
            and all(c["pinned"] or c["active_protected"] for c in candidates)
        )
        if all_pinned:
            return (
                "reject",
                "high",
                "over_budget_but_all_candidates_pinned",
                (
                    "Memory pressure is over_budget but every resident model is "
                    "pinned; pinned models are never evicted, so the policy "
                    "rejects rather than violate the pin invariant."
                ),
                None,
                (
                    {
                        "layer": "residency",
                        "signal": "all_candidates_pinned",
                        "reason": (
                            "every resident model is in the pinned set; "
                            "pinned_models_never_evicted invariant prevents "
                            "selection"
                        ),
                    },
                ),
            )
        if only_active_protected:
            return (
                "reject",
                "high",
                "over_budget_but_only_candidate_is_protected_active_model",
                (
                    "Memory pressure is over_budget but the only unpinned "
                    "candidate is the active model and active reassignment is "
                    "not yet frozen by this policy; rejecting rather than "
                    "evict the active model under default protection."
                ),
                None,
                (
                    {
                        "layer": "residency",
                        "signal": "active_model_protected",
                        "reason": (
                            "policy default protects the active model from "
                            "eviction; pass protect_active=False to override"
                        ),
                    },
                ),
            )
        return (
            "reject",
            "high",
            "over_budget_but_no_safe_candidate",
            (
                "Memory pressure is over_budget but no safe eviction candidate "
                "exists under current protections."
            ),
            None,
            (
                {
                    "layer": "residency",
                    "signal": "no_safe_candidate",
                    "reason": (
                        "no resident model is both unpinned and not "
                        "active-protected"
                    ),
                },
            ),
        )

    selected = eligible_candidates[0]
    return (
        "evict",
        "medium",
        "over_budget_with_safe_unpinned_candidate",
        (
            "Memory pressure is over_budget and a safe unpinned candidate is "
            "available; the policy selects the deterministic first eligible "
            "candidate for eviction."
        ),
        dict(selected),
        (),
    )


def _missing_signals(
    *,
    protect_active: bool,
) -> tuple[dict[str, str], ...]:
    return (
        {
            "layer": "pressure_event",
            "signal": "runtime_owned_os_pressure_event_or_pressure_sample",
            "reason": (
                "policy classifies budget pressure but does not yet observe "
                "OS-level pressure events directly"
            ),
        },
        {
            "layer": "scheduler_admission_integration",
            "signal": "scheduler_admission_contract_consumes_eviction_policy",
            "reason": (
                "scheduler_admission_contract does not yet consume this "
                "eviction policy as a pre-claim defer-to-evict input; "
                "integration deferred to a later round"
            ),
        },
        {
            "layer": "active_reassignment",
            "signal": "frozen_active_reassignment_under_pressure_policy",
            "reason": (
                "active model is protected by default (protect_active="
                f"{protect_active!s}); explicit active reassignment policy is "
                "deferred"
            ),
        },
    )


def build_memory_pressure_eviction_policy(
    *,
    runtime_status: Mapping[str, Any] | None = None,
    abort_recovery_snapshot: Mapping[str, Any] | None = None,
    protect_active: bool = True,
) -> MemoryPressureEvictionPolicy:
    """Build the current runtime-owned memory-pressure eviction decision."""

    raw_status = _mapping(runtime_status)
    pressure = build_memory_pressure_contract(runtime_status=raw_status)
    recovery = build_recovery_supervisor_contract(
        runtime_status=raw_status,
        abort_recovery_snapshot=abort_recovery_snapshot,
    )
    residency = build_model_residency_policy(runtime_status=raw_status)
    candidates, active_model_id = _build_candidates(
        raw_status=raw_status,
        protect_active=protect_active,
    )

    decision, confidence, reason_code, reason_message, selected_victim, blocking = (
        _classify(
            pressure=pressure,
            recovery=recovery,
            candidates=candidates,
            active_model_id=active_model_id,
            protect_active=protect_active,
        )
    )

    return MemoryPressureEvictionPolicy(
        decision=decision,
        confidence=confidence,
        reason_code=reason_code,
        reason_message=reason_message,
        selected_victim=selected_victim,
        candidate_order=tuple(candidates),
        pressure={
            "pressure_classification": pressure.pressure_classification,
            "confidence": pressure.confidence,
            "reason_code": pressure.reason_code,
            "policy_surface": "owlmlx.memory_pressure_contract",
        },
        residency_summary={
            "resident_model_count": len(residency.models),
            "active_model_id": active_model_id,
            "resident_model_ids": [
                str(entry["model_id"]) for entry in residency.models
            ],
            "policy_surface": "owlmlx.model_residency_policy",
        },
        recovery_summary={
            "recovery_state": recovery.recovery_state,
            "barrier_decision": recovery.barrier_decision,
            "hard_recovery_barrier": bool(recovery.barrier["hard_recovery_barrier"]),
            "policy_surface": "owlmlx.recovery_supervisor_contract",
        },
        blocking_signals=blocking,
        preserved_invariants=PRESERVED_INVARIANTS,
        decision_support=_decision_support(),
        missing_signals=_missing_signals(protect_active=protect_active),
        inputs={
            "protect_active": protect_active,
            "candidate_count": len(candidates),
            "eligible_candidate_count": sum(
                1 for c in candidates if c["eligible"]
            ),
            "ordering_rule": (
                "unpinned_first; ttl_expired_unpinned_before_manual_unload; "
                "non_active_before_protected_active; "
                "larger_memory_first; lexical_model_id_tiebreak"
            ),
        },
    )


def memory_pressure_eviction_policy_to_dict(
    policy: MemoryPressureEvictionPolicy,
) -> dict[str, Any]:
    """Serialize the runtime-owned memory-pressure eviction policy."""

    return {
        "contract": {
            "surface": MEMORY_PRESSURE_EVICTION_POLICY_SURFACE,
            "version": MEMORY_PRESSURE_EVICTION_POLICY_VERSION,
            "stable_sections": [
                "summary",
                "reason",
                "selected_victim",
                "candidate_order",
                "pressure",
                "residency_summary",
                "recovery_summary",
                "blocking_signals",
                "preserved_invariants",
                "decision_support",
                "missing_signals",
                "inputs",
            ],
        },
        "summary": {
            "status": "partial",
            "decision": policy.decision,
            "confidence": policy.confidence,
            "pressure_classification": policy.pressure.get("pressure_classification"),
            "selected_victim_model_id": (
                policy.selected_victim["model_id"]
                if policy.selected_victim is not None
                else None
            ),
            "supported_decisions": list(MEMORY_PRESSURE_EVICTION_DECISIONS),
            "policy_depth": "memory_pressure_eviction_decision_only",
        },
        "reason": {
            "code": policy.reason_code,
            "message": policy.reason_message,
        },
        "selected_victim": (
            dict(policy.selected_victim)
            if policy.selected_victim is not None
            else None
        ),
        "candidate_order": [dict(c) for c in policy.candidate_order],
        "pressure": policy.pressure,
        "residency_summary": policy.residency_summary,
        "recovery_summary": policy.recovery_summary,
        "blocking_signals": list(policy.blocking_signals),
        "preserved_invariants": list(policy.preserved_invariants),
        "decision_support": policy.decision_support,
        "missing_signals": list(policy.missing_signals),
        "inputs": policy.inputs,
    }


__all__ = [
    "MEMORY_PRESSURE_EVICTION_DECISIONS",
    "MEMORY_PRESSURE_EVICTION_POLICY_SURFACE",
    "MEMORY_PRESSURE_EVICTION_POLICY_VERSION",
    "PRESERVED_INVARIANTS",
    "MemoryPressureEvictionPolicy",
    "build_memory_pressure_eviction_policy",
    "memory_pressure_eviction_policy_to_dict",
]
