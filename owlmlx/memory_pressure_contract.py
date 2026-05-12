"""Runtime-owned single-host memory pressure contract for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .memory_watermark import MemoryWatermark, WatermarkAction


MEMORY_PRESSURE_CONTRACT_SURFACE = "owlmlx.memory_pressure_contract"
MEMORY_PRESSURE_CONTRACT_VERSION = "v1"
PRESSURE_CLASSIFICATIONS = (
    "within_budget",
    "near_budget",
    "over_budget",
    "cooldown_barrier",
    "host_pressure_barrier",
    "unknown",
    "insufficient_signal",
)


@dataclass(frozen=True, slots=True)
class MemoryPressureContract:
    """Stable runtime-owned memory pressure contract for current budget truth."""

    pressure_classification: str
    confidence: str
    reason_code: str
    reason_message: str
    budget: dict[str, Any]
    residency_context: dict[str, Any]
    recovery_context: dict[str, Any]
    policy_boundaries: dict[str, Any]
    classification_support: dict[str, dict[str, Any]]
    missing_signals: tuple[dict[str, str], ...]


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _list_of_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if isinstance(item, str) and item)


def _classification_support() -> dict[str, dict[str, Any]]:
    return {
        "within_budget": {
            "classification_status": "supported",
            "reason_code": "budget_snapshot_has_positive_headroom_below_warning",
        },
        "near_budget": {
            "classification_status": "supported",
            "reason_code": "budget_snapshot_crosses_warning_threshold_without_exceeding_budget",
        },
        "over_budget": {
            "classification_status": "supported",
            "reason_code": "budget_snapshot_has_negative_headroom_or_utilization_above_one",
        },
        "cooldown_barrier": {
            "classification_status": "supported",
            "reason_code": "runtime_owned_metal_oom_cooldown_active",
        },
        "host_pressure_barrier": {
            "classification_status": "supported",
            "reason_code": "runtime_owned_host_pressure_sample_blocks_new_load",
        },
        "unknown": {
            "classification_status": "supported",
            "reason_code": "budget_snapshot_missing_or_incomplete",
        },
        "insufficient_signal": {
            "classification_status": "supported",
            "reason_code": "budget_truth_does_not_prove_pressure_event_or_reclaim_barrier",
        },
    }


def _classify_budget_pressure(budget: Mapping[str, Any]) -> tuple[str, str, str, str]:
    serving_budget_gb = _number(budget.get("serving_budget_gb"))
    warning_threshold_gb = _number(budget.get("warning_threshold_gb"))
    currently_loaded_gb = _number(budget.get("currently_loaded_gb"))
    available_gb = _number(budget.get("available_gb"))
    utilization = _number(budget.get("utilization"))

    if serving_budget_gb is None or currently_loaded_gb is None:
        return (
            "unknown",
            "low",
            "budget_snapshot_incomplete",
            "The runtime budget snapshot is missing serving budget or loaded-memory truth.",
        )

    if available_gb is not None and available_gb < 0:
        return (
            "over_budget",
            "high",
            "budget_headroom_negative",
            "The runtime budget snapshot reports negative serving-budget headroom.",
        )
    if utilization is not None and utilization > 1.0:
        return (
            "over_budget",
            "high",
            "budget_utilization_above_one",
            "The runtime budget snapshot reports utilization above the serving budget.",
        )
    if currently_loaded_gb > serving_budget_gb:
        return (
            "over_budget",
            "high",
            "loaded_memory_exceeds_budget",
            "Currently loaded model memory exceeds the runtime serving budget.",
        )

    if warning_threshold_gb is not None and currently_loaded_gb >= warning_threshold_gb:
        return (
            "near_budget",
            "medium",
            "budget_warning_threshold_reached",
            "Currently loaded model memory has reached the configured warning threshold.",
        )
    if utilization is not None and utilization >= 0.85:
        return (
            "near_budget",
            "medium",
            "budget_utilization_near_limit",
            "Budget utilization is high enough to warn, but does not prove direct pressure.",
        )

    return (
        "within_budget",
        "medium",
        "budget_headroom_available",
        "The runtime budget snapshot reports serving-budget headroom.",
    )


def build_memory_pressure_contract(
    *,
    runtime_status: Mapping[str, Any] | None = None,
) -> MemoryPressureContract:
    """Build the current runtime-owned memory pressure contract."""

    raw_status = _mapping(runtime_status)
    budget = _mapping(raw_status.get("budget"))
    inventory = _mapping(raw_status.get("inventory"))
    restart = _mapping(raw_status.get("restart"))
    governance_policy = _mapping(raw_status.get("governance_policy"))
    cooldown = _mapping(raw_status.get("memory_pressure_cooldown"))
    host_pressure = _mapping(raw_status.get("host_pressure"))
    cooldown_active = cooldown.get("active") is True
    host_pressure_blocks = host_pressure.get("classification") == "host_pressure_block"

    if cooldown_active:
        classification, confidence, reason_code, reason_message = (
            "cooldown_barrier",
            "high",
            "metal_oom_cooldown_active",
            (
                "A runtime-owned memory-pressure cooldown is active after a "
                "Metal insufficient-memory child-loss signal."
            ),
        )
    elif host_pressure_blocks:
        classification, confidence, reason_code, reason_message = (
            "host_pressure_barrier",
            "high",
            "host_pressure_admission_barrier_active",
            (
                "A runtime-owned host-pressure sample is below the load-admission "
                "free-memory threshold."
            ),
        )
    else:
        classification, confidence, reason_code, reason_message = _classify_budget_pressure(
            budget
        )
    ttl_expired_model_ids = _list_of_strings(governance_policy.get("ttl_expired_model_ids"))
    ttl_expired_pinned_model_ids = _list_of_strings(
        governance_policy.get("ttl_expired_pinned_model_ids")
    )
    ttl_sweep_evictable_model_ids = tuple(
        model_id
        for model_id in ttl_expired_model_ids
        if model_id not in ttl_expired_pinned_model_ids
    )

    return MemoryPressureContract(
        pressure_classification=classification,
        confidence=confidence,
        reason_code=reason_code,
        reason_message=reason_message,
        budget={
            "system_memory_gb": budget.get("system_memory_gb"),
            "system_reserve_gb": budget.get("system_reserve_gb"),
            "serving_budget_gb": budget.get("serving_budget_gb"),
            "warning_threshold_gb": budget.get("warning_threshold_gb"),
            "currently_loaded_gb": budget.get("currently_loaded_gb"),
            "available_gb": budget.get("available_gb"),
            "utilization": budget.get("utilization"),
            "classification_status": (
                "supported" if classification != "unknown" else "unknown"
            ),
            "decision_scope": "budget_pressure_classification_only",
        },
        residency_context={
            "loaded_model_count": inventory.get("model_count"),
            "total_loaded_gb": inventory.get("total_loaded_gb"),
            "ttl_expired_model_ids": list(ttl_expired_model_ids),
            "ttl_expired_pinned_model_ids": list(ttl_expired_pinned_model_ids),
            "ttl_sweep_evictable_model_ids": list(ttl_sweep_evictable_model_ids),
            "ttl_sweep_evictable_model_count": len(ttl_sweep_evictable_model_ids),
            "classification_status": "partial",
            "decision_impact": (
                "ttl_sweep_candidates_visible_but_not_pressure_victim_selection"
            ),
        },
        recovery_context={
            "restartable_models": list(restart.get("restartable_models", [])),
            "restart_exhausted_models": list(restart.get("restart_exhausted_models", [])),
            "auto_restart_dead_session": bool(restart.get("auto_restart_dead_session", False)),
            "memory_pressure_cooldown": dict(cooldown),
            "host_pressure": dict(host_pressure),
            "classification_status": (
                "supported" if cooldown_active or host_pressure_blocks else "insufficient_signal"
            ),
            "decision_impact": (
                "metal_oom_cooldown_blocks_new_loads"
                if cooldown_active
                else (
                    "host_pressure_sample_blocks_new_loads"
                    if host_pressure_blocks
                    else "not_a_recovery_barrier_decision"
                )
            ),
        },
        policy_boundaries={
            "policy_scope": "budget_and_admission_pressure_classification_only",
            "runtime_owned_pressure_event_visible": cooldown_active or host_pressure_blocks,
            "runtime_owned_pressure_victim_selection": False,
            "runtime_owned_reclaim_barrier": False,
            "runtime_owned_metal_oom_cooldown": cooldown_active,
            "runtime_owned_host_pressure_sample": host_pressure.get("available") is True,
            "runtime_owned_reclaim_attempt_result_visibility": (
                "owlmlx.settle_barrier_event_records_failed_unload_and_failed_reclaim_at_operation_boundary"
            ),
            "owned_actions_visible": [
                "memory_budget_preflight_for_load",
                "host_pressure_preflight_for_load",
                "budget_snapshot_for_current_loaded_memory",
                "ttl_sweep_candidate_visibility",
            ],
            "out_of_scope": [
                "automatic_model_unload_under_pressure",
                "pressure_ranked_eviction",
                "reclaim_engine",
                "recovery_supervisor",
                "restart_barrier",
                "continuous_batching",
                "multi_worker_scheduler_depth",
            ],
        },
        classification_support=_classification_support(),
        missing_signals=(
            {
                "layer": "pressure_event",
                "signal": "runtime_owned_metal_allocator_or_command_queue_pressure",
                "reason": "host free-percent sampling is visible, but private Metal allocator pressure is not",
            },
            {
                "layer": "eviction",
                "signal": "runtime_owned_pressure_ranked_victim_selection",
                "reason": "TTL sweep evictability is visible, but pressure victim ranking is not frozen",
            },
            {
                "layer": "recovery",
                "signal": "runtime_owned_restart_or_isolation_barrier_after_failed_reclaim",
                "reason": "restart visibility exists, but recovery barrier policy is separate; reclaim attempt-result visibility is owned by owlmlx.settle_barrier_event",
            },
        ),
    )


def memory_pressure_contract_to_dict(contract: MemoryPressureContract) -> dict[str, Any]:
    """Serialize the runtime-owned memory pressure contract."""

    return {
        "contract": {
            "surface": MEMORY_PRESSURE_CONTRACT_SURFACE,
            "version": MEMORY_PRESSURE_CONTRACT_VERSION,
            "stable_sections": [
                "summary",
                "reason",
                "budget",
                "residency_context",
                "recovery_context",
                "policy_boundaries",
                "classification_support",
                "missing_signals",
            ],
        },
        "summary": {
            "status": "partial",
            "pressure_classification": contract.pressure_classification,
            "confidence": contract.confidence,
            "supported_classifications": list(PRESSURE_CLASSIFICATIONS),
            "policy_depth": "budget_pressure_classification",
            # PR #649 watermark + recommended action. Derived from
            # pressure_classification; serialized as `.value` strings so
            # HTTP consumers don't have to import the enum.
            "watermark": MemoryWatermark.from_classification(
                contract.pressure_classification
            ).value,
            "watermark_action": WatermarkAction.for_watermark(
                MemoryWatermark.from_classification(contract.pressure_classification)
            ).value,
        },
        "reason": {
            "code": contract.reason_code,
            "message": contract.reason_message,
        },
        "budget": contract.budget,
        "residency_context": contract.residency_context,
        "recovery_context": contract.recovery_context,
        "policy_boundaries": contract.policy_boundaries,
        "classification_support": contract.classification_support,
        "missing_signals": list(contract.missing_signals),
    }
