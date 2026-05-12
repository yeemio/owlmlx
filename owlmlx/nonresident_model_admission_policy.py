"""Runtime-owned single-host non-resident model admission policy contract for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .memory_pressure_classifier import (
    MemoryPressureContract,
    build_memory_pressure_contract,
    memory_pressure_contract_to_dict,
)
from .model_residency_policy import (
    ModelResidencyPolicy,
    build_model_residency_policy,
    model_residency_policy_to_dict,
)
from .nonresident_loadability_lineage import (
    NonResidentLoadabilityLineage,
)
from .recovery_supervisor import (
    RecoverySupervisorContract,
    build_recovery_supervisor_contract,
    recovery_supervisor_contract_to_dict,
)


NONRESIDENT_MODEL_ADMISSION_POLICY_SURFACE = (
    "owlmlx.nonresident_model_admission_policy"
)
NONRESIDENT_MODEL_ADMISSION_POLICY_VERSION = "v1"
NONRESIDENT_ADMISSION_DECISIONS = (
    "admit_and_load",
    "defer",
    "reject",
    "unknown",
)
PRESERVED_INVARIANTS: tuple[str, ...] = (
    "max_concurrent_1_after_gate_claim",
    "ticketed_fifo_after_gate_claim",
    "no_post_claim_gate_bypass",
    "pre_claim_decision_only",
)


@dataclass(frozen=True, slots=True)
class NonResidentModelAdmissionPolicy:
    """Stable runtime-owned non-resident model admission decision."""

    decision: str
    target_model_id: str | None
    confidence: str
    reason_code: str
    reason_message: str
    required_preconditions: tuple[str, ...]
    blocking_signals: tuple[dict[str, str], ...]
    preserved_invariants: tuple[str, ...]
    missing_signals: tuple[dict[str, str], ...]
    inputs: dict[str, Any]
    decision_support: dict[str, dict[str, Any]]
    policy_boundaries: dict[str, Any]


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _normalized_known_loadable(
    value: Sequence[str] | None,
) -> tuple[str, ...]:
    if value is None:
        return ()
    seen: set[str] = set()
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return tuple(out)


def _decision_support() -> dict[str, dict[str, Any]]:
    return {
        "admit_and_load": {
            "decision_status": "supported",
            "reason_code": (
                "non_resident_target_known_loadable_within_budget_no_recovery_barrier"
            ),
        },
        "defer": {
            "decision_status": "supported",
            "reason_code": (
                "named_precondition_must_resolve_before_safe_load_decision"
            ),
        },
        "reject": {
            "decision_status": "supported",
            "reason_code": (
                "non_resident_target_cannot_be_admitted_under_current_runtime_truth"
            ),
        },
        "unknown": {
            "decision_status": "supported",
            "reason_code": "required_input_truth_absent_or_too_weak",
        },
    }


def _resident_model_ids(residency: ModelResidencyPolicy) -> tuple[str, ...]:
    return tuple(
        str(entry["model_id"])
        for entry in residency.models
        if isinstance(entry, Mapping) and entry.get("model_id")
    )


def _classify(
    *,
    target_model_id: str | None,
    residency: ModelResidencyPolicy,
    pressure: MemoryPressureContract,
    recovery: RecoverySupervisorContract,
    known_loadable_model_ids: tuple[str, ...],
    request_context_class: str | None,
    loadability_lineage: NonResidentLoadabilityLineage | None,
) -> tuple[
    str,
    str,
    str,
    str,
    tuple[str, ...],
    tuple[dict[str, str], ...],
]:
    """Return (decision, confidence, reason_code, reason_message, required_preconditions, blocking_signals)."""

    if not target_model_id:
        return (
            "reject",
            "high",
            "no_target_model_requested",
            "Non-resident admission requires an explicit target model id.",
            (),
            (
                {
                    "layer": "request",
                    "signal": "target_model_id",
                    "reason": "no target model id was provided to the policy",
                },
            ),
        )

    resident_ids = _resident_model_ids(residency)
    if target_model_id in resident_ids:
        return (
            "reject",
            "high",
            "target_already_resident_no_admission_needed",
            (
                "The target model is already resident; the non-resident admission "
                "policy does not produce admit_and_load for already-loaded models."
            ),
            ("query_model_residency_policy_for_already_resident_targets",),
            (
                {
                    "layer": "residency",
                    "signal": "target_already_resident",
                    "reason": (
                        "target model is in runtime-owned loaded inventory, so "
                        "non-resident admission does not apply"
                    ),
                },
            ),
        )

    if recovery.barrier["hard_recovery_barrier"]:
        return (
            "reject",
            "high",
            "recovery_hard_barrier_fail_closed",
            (
                "Recovery supervisor reports a hard barrier, so non-resident "
                "admission rejects rather than load into an unsafe substrate."
            ),
            (
                "operator_must_clear_recovery_barrier",
                "recovery_supervisor_must_return_to_clean_or_probing",
            ),
            (
                {
                    "layer": "recovery",
                    "signal": recovery.barrier["reason_code"],
                    "reason": recovery.reason_message,
                },
            ),
        )

    if pressure.pressure_classification == "over_budget":
        return (
            "reject",
            "high",
            "over_budget_and_no_pressure_eviction_policy_owned",
            (
                "Memory pressure is over_budget and runtime does not yet own a "
                "pressure-ranked eviction execution policy, so non-resident "
                "admission rejects rather than defer into an unfrozen 3.2 path."
            ),
            (
                "release_floor_3_2_memory_pressure_decision_closure_must_close",
                "pressure_classification_must_drop_to_within_or_near_budget",
            ),
            (
                {
                    "layer": "memory_pressure",
                    "signal": "over_budget",
                    "reason": pressure.reason_message,
                },
                {
                    "layer": "eviction",
                    "signal": "pressure_ranked_eviction_execution_policy",
                    "reason": (
                        "release floor 3.2 not closed; non-resident admission "
                        "must not invent eviction in the 3.3 lane"
                    ),
                },
            ),
        )

    if (
        recovery.barrier["high_context_barrier"]
        and request_context_class == "high_context"
    ):
        return (
            "defer",
            "medium",
            "recovery_probing_defers_high_context_load",
            (
                "Recovery is probing the substrate; high-context non-resident "
                "loads should wait for the probe to confirm a clean substrate."
            ),
            (
                "abort_recovery_probe_must_complete",
                "abort_recovery_state_must_become_clean",
            ),
            (
                {
                    "layer": "recovery",
                    "signal": "abort_recovery_probing",
                    "reason": (
                        "abort recovery is probing and request is known "
                        "high-context; defer until probe is conclusive"
                    ),
                },
            ),
        )

    if pressure.pressure_classification == "near_budget":
        return (
            "defer",
            "medium",
            "near_budget_no_pressure_action_policy",
            (
                "Memory pressure is near_budget and runtime does not yet own a "
                "pressure-action policy, so non-resident admission defers until "
                "pressure drops or release floor 3.2 closes."
            ),
            (
                "pressure_classification_must_drop_to_within_budget",
                "or_release_floor_3_2_memory_pressure_decision_closure_must_close",
            ),
            (
                {
                    "layer": "memory_pressure",
                    "signal": "near_budget",
                    "reason": pressure.reason_message,
                },
            ),
        )

    if pressure.pressure_classification == "unknown":
        return (
            "unknown",
            "low",
            "pressure_truth_absent_for_admission_decision",
            (
                "Memory pressure truth is absent or incomplete; non-resident "
                "admission cannot be decided without it."
            ),
            ("budget_snapshot_must_be_present_in_runtime_status",),
            (
                {
                    "layer": "memory_pressure",
                    "signal": "budget_snapshot",
                    "reason": pressure.reason_message,
                },
            ),
        )

    if (
        loadability_lineage is not None
        and loadability_lineage.decision == "not_loadable"
    ):
        return (
            "reject",
            "high",
            "runtime_owned_loadability_lineage_says_not_loadable",
            (
                "Runtime-owned loadability lineage classifies the target as "
                "not_loadable, so non-resident admission rejects rather than "
                "load against a missing or invalid lineage. "
                + str(loadability_lineage.reason_message)
            ),
            (
                "runtime_owned_loadability_lineage_must_classify_target_as_known_loadable",
                "operator_must_align_visibility_registry_or_lineage_record_with_target",
            ),
            tuple(
                {
                    "layer": str(item.get("layer", "loadability_lineage")),
                    "signal": str(item.get("signal", "")),
                    "reason": str(item.get("reason", "")),
                }
                for item in loadability_lineage.blocking_signals
            )
            or (
                {
                    "layer": "loadability_lineage",
                    "signal": loadability_lineage.reason_code,
                    "reason": loadability_lineage.reason_message,
                },
            ),
        )

    if (
        loadability_lineage is not None
        and loadability_lineage.decision == "known_loadable"
    ):
        return (
            "admit_and_load",
            "medium",
            "non_resident_target_runtime_owned_loadability_lineage_admit",
            (
                "Target is non-resident, runtime-owned loadability lineage "
                "classifies the target as known_loadable, memory pressure is "
                "within budget, and no hard recovery barrier is active; "
                "non-resident admission admits and instructs the runtime to "
                "load before whole-request gate claim."
            ),
            (
                "memory_budget_preflight_must_still_hold_at_load_time",
                "no_hard_recovery_barrier_at_load_time",
                "no_concurrent_competing_non_resident_load_for_same_target",
                "post_claim_serial_invariants_must_remain_owned_by_GenerationGate",
                "runtime_owned_loadability_lineage_must_remain_known_loadable_at_load_time",
            ),
            (),
        )

    if target_model_id not in known_loadable_model_ids:
        return (
            "unknown",
            "low",
            "lineage_loadability_truth_missing",
            (
                "Runtime-owned loadability lineage is not connected (or "
                "returned unknown) and operator did not supply "
                "known_loadable_model_ids, so admit_and_load cannot be "
                "honestly returned for an unverified target."
            ),
            (
                "runtime_owned_loadability_lineage_must_classify_target_as_known_loadable",
                "or_operator_must_supply_known_loadable_model_ids_as_labeled_fallback",
            ),
            (
                {
                    "layer": "loadability",
                    "signal": "runtime_owned_non_resident_loadability_lineage",
                    "reason": (
                        "loadability lineage source is not connected or "
                        "returned unknown for this target"
                    ),
                },
            ),
        )

    return (
        "admit_and_load",
        "medium",
        "non_resident_target_known_loadable_admit",
        (
            "Target is non-resident, operator-supplied lineage hint marks it "
            "known loadable as a labeled fallback (runtime-owned loadability "
            "lineage is not connected), memory pressure is within budget, "
            "and no hard recovery barrier is active; non-resident admission "
            "admits and instructs the runtime to load before whole-request "
            "gate claim."
        ),
        (
            "memory_budget_preflight_must_still_hold_at_load_time",
            "no_hard_recovery_barrier_at_load_time",
            "no_concurrent_competing_non_resident_load_for_same_target",
            "post_claim_serial_invariants_must_remain_owned_by_GenerationGate",
            "operator_supplied_loadability_hint_must_remain_valid_at_load_time",
        ),
        (),
    )


def _missing_signals(
    *,
    known_loadable_model_ids: tuple[str, ...],
    request_context_class: str | None,
    loadability_lineage: NonResidentLoadabilityLineage | None,
) -> tuple[dict[str, str], ...]:
    items: list[dict[str, str]] = []
    lineage_connected_decisively = (
        loadability_lineage is not None
        and loadability_lineage.decision in {"known_loadable", "not_loadable"}
    )
    if not lineage_connected_decisively:
        items.append(
            {
                "layer": "loadability",
                "signal": "runtime_owned_non_resident_loadability_lineage",
                "reason": (
                    "loadability lineage contract is either not connected or "
                    "returned unknown for this target; pass a runtime-owned "
                    "lineage_records registry at app/kernel construction time "
                    "to close this signal"
                ),
            }
        )
    items.append(
        {
            "layer": "eviction",
            "signal": "runtime_owned_pressure_ranked_eviction_execution_policy",
            "reason": (
                "release floor 3.2 not closed; non-resident admission cannot "
                "drive eviction in the 3.3 lane"
            ),
        }
    )
    items.append(
        {
            "layer": "scheduler_admission_integration",
            "signal": "scheduler_admission_contract_consumes_nonresident_policy",
            "reason": (
                "scheduler_admission_contract does not yet consume this policy "
                "as a pre-claim defer-to-load input; integration deferred to a "
                "later round so the new contract can stabilize without "
                "regressing existing admission tests"
            ),
        }
    )
    if not known_loadable_model_ids and request_context_class is None:
        items.append(
            {
                "layer": "request_context",
                "signal": "request_context_class",
                "reason": (
                    "request_context_class is optional; supply 'high_context' "
                    "when the request is known to need high-context handling"
                ),
            }
        )
    return tuple(items)


def build_nonresident_model_admission_policy(
    *,
    runtime_status: Mapping[str, Any] | None = None,
    model_id: str | None = None,
    known_loadable_model_ids: Sequence[str] | None = None,
    request_context_class: str | None = None,
    abort_recovery_snapshot: Mapping[str, Any] | None = None,
    loadability_lineage: NonResidentLoadabilityLineage | None = None,
) -> NonResidentModelAdmissionPolicy:
    """Build the current runtime-owned non-resident model admission policy decision."""

    raw_status = _mapping(runtime_status)
    target_model_id = model_id if isinstance(model_id, str) and model_id else None
    known_loadable = _normalized_known_loadable(known_loadable_model_ids)
    normalized_context_class = (
        request_context_class
        if isinstance(request_context_class, str) and request_context_class
        else None
    )

    residency = build_model_residency_policy(
        runtime_status=raw_status,
        model_id=target_model_id,
    )
    pressure = build_memory_pressure_contract(runtime_status=raw_status)
    recovery = build_recovery_supervisor_contract(
        runtime_status=raw_status,
        abort_recovery_snapshot=abort_recovery_snapshot,
    )

    (
        decision,
        confidence,
        reason_code,
        reason_message,
        required_preconditions,
        blocking_signals,
    ) = _classify(
        target_model_id=target_model_id,
        residency=residency,
        pressure=pressure,
        recovery=recovery,
        known_loadable_model_ids=known_loadable,
        request_context_class=normalized_context_class,
        loadability_lineage=loadability_lineage,
    )

    inputs: dict[str, Any] = {
        "target_model_id": target_model_id,
        "request_context_class": normalized_context_class,
        "known_loadable_model_ids": list(known_loadable),
        "known_loadable_truth_status": (
            "operator_supplied" if known_loadable else "missing"
        ),
        "residency": {
            "target_status": dict(residency.target_status),
            "resident_model_ids": list(_resident_model_ids(residency)),
            "policy_surface": "owlmlx.model_residency_policy",
        },
        "memory_pressure": {
            "pressure_classification": pressure.pressure_classification,
            "confidence": pressure.confidence,
            "reason_code": pressure.reason_code,
            "policy_surface": "owlmlx.memory_pressure_contract",
        },
        "recovery": {
            "recovery_state": recovery.recovery_state,
            "barrier_decision": recovery.barrier_decision,
            "hard_recovery_barrier": bool(
                recovery.barrier["hard_recovery_barrier"]
            ),
            "high_context_barrier": bool(
                recovery.barrier["high_context_barrier"]
            ),
            "policy_surface": "owlmlx.recovery_supervisor_contract",
        },
        "loadability_lineage": (
            {
                "decision": loadability_lineage.decision,
                "reason_code": loadability_lineage.reason_code,
                "target_alignment": loadability_lineage.lineage.get(
                    "target_alignment"
                ),
                "visibility_truth_status": loadability_lineage.inputs.get(
                    "visibility_truth_status"
                ),
                "loadability_lineage_truth_status": (
                    loadability_lineage.inputs.get(
                        "loadability_lineage_truth_status"
                    )
                ),
                "policy_surface": "owlmlx.nonresident_loadability_lineage",
            }
            if loadability_lineage is not None
            else {
                "decision": "unknown",
                "reason_code": (
                    "loadability_lineage_contract_not_passed_to_admission_policy"
                ),
                "target_alignment": "unknown",
                "visibility_truth_status": "missing",
                "loadability_lineage_truth_status": "missing",
                "policy_surface": "owlmlx.nonresident_loadability_lineage",
            }
        ),
    }

    return NonResidentModelAdmissionPolicy(
        decision=decision,
        target_model_id=target_model_id,
        confidence=confidence,
        reason_code=reason_code,
        reason_message=reason_message,
        required_preconditions=required_preconditions,
        blocking_signals=blocking_signals,
        preserved_invariants=PRESERVED_INVARIANTS,
        missing_signals=_missing_signals(
            known_loadable_model_ids=known_loadable,
            request_context_class=normalized_context_class,
            loadability_lineage=loadability_lineage,
        ),
        inputs=inputs,
        decision_support=_decision_support(),
        policy_boundaries={
            "policy_scope": (
                "non_resident_target_pre_claim_admission_decision_only"
            ),
            "decision_vocabulary": list(NONRESIDENT_ADMISSION_DECISIONS),
            "round_trip_surfaces": [
                "owlmlx.model_residency_policy",
                "owlmlx.memory_pressure_contract",
                "owlmlx.recovery_supervisor_contract",
                "owlmlx.nonresident_loadability_lineage",
            ],
            "owned_actions_visible": [
                "non_resident_target_classification",
                "pressure_aware_admit_or_defer",
                "recovery_aware_fail_closed",
                "runtime_owned_loadability_lineage_consumption",
                "operator_supplied_loadability_hint_labeled_fallback",
            ],
            "out_of_scope": [
                "automatic_loader_implementation",
                "pressure_ranked_eviction_execution",
                "post_claim_gate_bypass",
                "continuous_batching",
                "multi_worker_scheduler_depth",
                "background_recovery_loop",
            ],
        },
    )


def nonresident_model_admission_policy_to_dict(
    policy: NonResidentModelAdmissionPolicy,
) -> dict[str, Any]:
    """Serialize the runtime-owned non-resident model admission policy."""

    return {
        "contract": {
            "surface": NONRESIDENT_MODEL_ADMISSION_POLICY_SURFACE,
            "version": NONRESIDENT_MODEL_ADMISSION_POLICY_VERSION,
            "stable_sections": [
                "summary",
                "reason",
                "required_preconditions",
                "blocking_signals",
                "preserved_invariants",
                "inputs",
                "decision_support",
                "policy_boundaries",
                "missing_signals",
            ],
        },
        "summary": {
            "status": "partial",
            "decision": policy.decision,
            "target_model_id": policy.target_model_id,
            "confidence": policy.confidence,
            "supported_decisions": list(NONRESIDENT_ADMISSION_DECISIONS),
            "policy_depth": "non_resident_target_pre_claim_admission",
        },
        "reason": {
            "code": policy.reason_code,
            "message": policy.reason_message,
        },
        "required_preconditions": list(policy.required_preconditions),
        "blocking_signals": list(policy.blocking_signals),
        "preserved_invariants": list(policy.preserved_invariants),
        "inputs": policy.inputs,
        "decision_support": policy.decision_support,
        "policy_boundaries": policy.policy_boundaries,
        "missing_signals": list(policy.missing_signals),
    }


def pre_load_check(
    model_id: str,
    *,
    runtime_status: Mapping[str, Any] | None = None,
    known_loadable_model_ids: Sequence[str] | None = None,
    request_context_class: str | None = None,
    abort_recovery_snapshot: Mapping[str, Any] | None = None,
    loadability_lineage: NonResidentLoadabilityLineage | None = None,
) -> NonResidentModelAdmissionPolicy:
    """PR #649-shaped admission check before loading a non-resident model.

    Thin alias over :func:`build_nonresident_model_admission_policy` that
    matches the public vocabulary in PR #649
    (https://github.com/jundot/omlx/pull/649). The PR's `pre_load_check()`
    inspects projected memory utilization + active-request safety + budget
    and returns a four-outcome verdict (admit / defer / reject / unknown).
    owlmlx already implements that decision via the full admission policy
    builder; this entrypoint exposes the well-known name.

    `model_id` is required positionally — admission is always about a
    specific target. All other inputs default to "snapshot from
    runtime_status" semantics, matching :func:`build_nonresident_model_admission_policy`.
    """
    return build_nonresident_model_admission_policy(
        runtime_status=runtime_status,
        model_id=model_id,
        known_loadable_model_ids=known_loadable_model_ids,
        request_context_class=request_context_class,
        abort_recovery_snapshot=abort_recovery_snapshot,
        loadability_lineage=loadability_lineage,
    )


__all__ = [
    "NONRESIDENT_ADMISSION_DECISIONS",
    "NONRESIDENT_MODEL_ADMISSION_POLICY_SURFACE",
    "NONRESIDENT_MODEL_ADMISSION_POLICY_VERSION",
    "PRESERVED_INVARIANTS",
    "NonResidentModelAdmissionPolicy",
    "build_nonresident_model_admission_policy",
    "nonresident_model_admission_policy_to_dict",
    "pre_load_check",
]
