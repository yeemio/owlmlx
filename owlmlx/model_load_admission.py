"""Model-level load-admission projection for owlmlx.

This surface turns existing runtime truth into a model-specific admission
verdict. It does not load models, sample private Metal state, or run eviction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from owlmlx.model_profile import resolve_model_profile


MODEL_LOAD_ADMISSION_SURFACE = "owlmlx.model_load_admission"
MODEL_LOAD_ADMISSION_VERSION = "v1"
MODEL_LOAD_ADMISSION_DECISIONS = (
    "admit",
    "warn",
    "blocked",
    "already_loaded",
    "unknown",
)
MODEL_LOAD_BUDGET_PROJECTIONS = (
    "fits",
    "fits_warning",
    "exceeds",
    "already_loaded",
    "unknown",
)

_BYTES_PER_GB = 1024.0 ** 3
_DEFAULT_WARNING_HEADROOM_BYTES = int(8 * _BYTES_PER_GB)


@dataclass(frozen=True, slots=True)
class ModelLoadAdmissionEntry:
    """Admission projection for one model id."""

    model_id: str
    admission_decision: str
    reason_code: str
    reason_message: str
    visibility_status: str
    profile_id: str
    profile_family: str
    budget_projection: str
    known_peak_resident_set_bytes: int | None
    projected_headroom_bytes: int | None
    current_budget_available_bytes: int | None
    host_pressure_classification: str
    cooldown_active: bool
    already_loaded: bool
    evidence: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ModelLoadAdmission:
    """Aggregate model-load admission surface."""

    target_model_id: str | None
    entries: tuple[ModelLoadAdmissionEntry, ...]
    ledger_status: str
    policy_boundaries: dict[str, Any]


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


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float) and value >= 0:
        return int(value)
    return None


def _bytes_from_gb(value: object) -> int | None:
    number = _number(value)
    if number is None:
        return None
    return int(number * _BYTES_PER_GB)


def _visibility_by_model(
    visibility_contract: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    contract = _mapping(visibility_contract)
    entries = contract.get("entries")
    by_model: dict[str, dict[str, Any]] = {}
    if isinstance(entries, list):
        for raw in entries:
            entry = _mapping(raw)
            model_id = str(entry.get("model_id") or "")
            if model_id:
                by_model[model_id] = entry
    for model_id in contract.get("visible_model_ids", []) or []:
        if not isinstance(model_id, str) or not model_id:
            continue
        by_model.setdefault(model_id, {"model_id": model_id, "visible": True})
    return by_model


def _loaded_model_ids(runtime_status: Mapping[str, Any] | None) -> set[str]:
    status = _mapping(runtime_status)
    backend = _mapping(status.get("backend"))
    loaded_models = backend.get("loaded_models")
    result: set[str] = set()
    if isinstance(loaded_models, list):
        for raw in loaded_models:
            entry = _mapping(raw)
            model_id = str(entry.get("model_id") or "")
            if model_id:
                result.add(model_id)
    active_model_id = status.get("active_model_id")
    if isinstance(active_model_id, str) and active_model_id:
        result.add(active_model_id)
    return result


def _latest_records_by_model(
    records: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None,
) -> dict[str, dict[str, Any]]:
    by_model: dict[str, dict[str, Any]] = {}
    for raw in records or []:
        record = _mapping(raw)
        model_id = str(record.get("model_id") or "")
        if model_id:
            by_model[model_id] = record
    return by_model


def _candidate_model_ids(
    *,
    target_model_id: str | None,
    visibility: Mapping[str, dict[str, Any]],
    latest_records: Mapping[str, dict[str, Any]],
) -> tuple[str, ...]:
    if target_model_id:
        return (target_model_id,)
    merged = set(visibility)
    merged.update(latest_records)
    return tuple(sorted(merged))


def _visibility_status(entry: Mapping[str, Any] | None) -> str:
    if not entry:
        return "unknown"
    if entry.get("visible") is True:
        return "visible"
    return "blocked"


def _budget_projection(
    *,
    peak_bytes: int | None,
    available_bytes: int | None,
    already_loaded: bool,
    warning_headroom_bytes: int,
) -> tuple[str, int | None]:
    if already_loaded:
        return "already_loaded", None
    if peak_bytes is None or available_bytes is None:
        return "unknown", None
    projected_headroom = available_bytes - peak_bytes
    if projected_headroom < 0:
        return "exceeds", projected_headroom
    if projected_headroom <= warning_headroom_bytes:
        return "fits_warning", projected_headroom
    return "fits", projected_headroom


def _entry_decision(
    *,
    visibility_status: str,
    budget_projection: str,
    host_pressure_classification: str,
    cooldown_active: bool,
    dead_registered_models: tuple[str, ...],
    already_loaded: bool,
    peak_bytes: int | None,
) -> tuple[str, str, str]:
    if visibility_status != "visible":
        return (
            "blocked",
            "model_not_visible",
            "The model is not visible under the owlmlx runtime visibility gate.",
        )
    if cooldown_active:
        return (
            "blocked",
            "metal_oom_cooldown_active",
            "A Metal-OOM cooldown is active, so new model loads are blocked.",
        )
    if dead_registered_models:
        return (
            "blocked",
            "dead_registered_models_require_unload",
            "Stale subprocess registrations must be cleaned before new loads.",
        )
    if host_pressure_classification == "host_pressure_block":
        return (
            "blocked",
            "host_pressure_admission_barrier_active",
            "Host pressure is below the runtime-owned load-admission threshold.",
        )
    if already_loaded:
        return (
            "already_loaded",
            "model_already_loaded",
            "The model is already loaded; no new load admission is required.",
        )
    if budget_projection == "exceeds":
        return (
            "blocked",
            "known_peak_exceeds_available_budget",
            "The latest known peak RSS exceeds current serving-budget headroom.",
        )
    if peak_bytes is None:
        return (
            "unknown",
            "known_peak_missing",
            "No model-specific peak RSS evidence exists in the Model RC ledger.",
        )
    if host_pressure_classification in {"unknown", "not_sampled"}:
        return (
            "unknown",
            "host_pressure_sample_missing",
            "Budget projection exists, but no current host-pressure sample is available.",
        )
    if host_pressure_classification == "host_pressure_warn":
        return (
            "warn",
            "host_pressure_warning_threshold_reached",
            "Host pressure is near the runtime-owned warning threshold.",
        )
    if budget_projection == "fits_warning":
        return (
            "warn",
            "known_peak_leaves_low_headroom",
            "The latest known peak RSS fits but leaves little serving-budget headroom.",
        )
    if budget_projection == "fits":
        return (
            "admit",
            "known_peak_fits_current_budget",
            "Visibility, host pressure, and known peak RSS allow a load attempt.",
        )
    return (
        "unknown",
        "admission_truth_incomplete",
        "The runtime does not have enough truth to compute a stronger admission verdict.",
    )


def build_model_load_admission(
    *,
    runtime_status: Mapping[str, Any] | None,
    visibility_contract: Mapping[str, Any] | None,
    model_release_candidate_records: list[Mapping[str, Any]]
    | tuple[Mapping[str, Any], ...]
    | None = None,
    target_model_id: str | None = None,
    ledger_status: str = "unknown",
    warning_headroom_bytes: int = _DEFAULT_WARNING_HEADROOM_BYTES,
) -> ModelLoadAdmission:
    """Build model-level load admission from current runtime-owned truth."""

    status = _mapping(runtime_status)
    visibility = _visibility_by_model(visibility_contract)
    latest_records = _latest_records_by_model(model_release_candidate_records)
    model_ids = _candidate_model_ids(
        target_model_id=target_model_id,
        visibility=visibility,
        latest_records=latest_records,
    )

    budget = _mapping(status.get("budget"))
    available_bytes = _bytes_from_gb(budget.get("available_gb"))
    host_pressure = _mapping(status.get("host_pressure"))
    host_pressure_classification = str(
        host_pressure.get("classification") or "unknown"
    )
    cooldown = _mapping(status.get("memory_pressure_cooldown"))
    cooldown_active = cooldown.get("active") is True
    backend_detail = _mapping(_mapping(status.get("backend")).get("detail"))
    dead_registered_models = tuple(
        str(item)
        for item in backend_detail.get("dead_registered_models", []) or []
        if isinstance(item, str) and item
    )
    loaded_model_ids = _loaded_model_ids(status)

    entries: list[ModelLoadAdmissionEntry] = []
    for model_id in model_ids:
        visibility_entry = visibility.get(model_id)
        record = latest_records.get(model_id, {})
        peak_bytes = _int_or_none(record.get("peak_resident_set_bytes"))
        already_loaded = model_id in loaded_model_ids
        budget_projection, projected_headroom = _budget_projection(
            peak_bytes=peak_bytes,
            available_bytes=available_bytes,
            already_loaded=already_loaded,
            warning_headroom_bytes=int(warning_headroom_bytes),
        )
        profile = resolve_model_profile(model_id)
        visibility_state = _visibility_status(visibility_entry)
        decision, reason_code, reason_message = _entry_decision(
            visibility_status=visibility_state,
            budget_projection=budget_projection,
            host_pressure_classification=host_pressure_classification,
            cooldown_active=cooldown_active,
            dead_registered_models=dead_registered_models,
            already_loaded=already_loaded,
            peak_bytes=peak_bytes,
        )
        entries.append(
            ModelLoadAdmissionEntry(
                model_id=model_id,
                admission_decision=decision,
                reason_code=reason_code,
                reason_message=reason_message,
                visibility_status=visibility_state,
                profile_id=profile.profile_id,
                profile_family=profile.profile_family,
                budget_projection=budget_projection,
                known_peak_resident_set_bytes=peak_bytes,
                projected_headroom_bytes=projected_headroom,
                current_budget_available_bytes=available_bytes,
                host_pressure_classification=host_pressure_classification,
                cooldown_active=cooldown_active,
                already_loaded=already_loaded,
                evidence={
                    "latest_model_rc_record_created_at": record.get("created_at"),
                    "latest_model_rc_verdict": record.get("verdict"),
                    "latest_model_rc_failure_count": record.get("failure_count"),
                    "memory_peak_source": record.get("memory_peak_source"),
                    "owlops_observation_path": record.get("owlops_observation_path"),
                    "host_pressure": dict(host_pressure),
                    "memory_pressure_cooldown": dict(cooldown),
                    "dead_registered_models": list(dead_registered_models),
                    "visibility_block_reason": (
                        visibility_entry or {}
                    ).get("block_reason")
                    if visibility_entry
                    else None,
                },
            )
        )

    return ModelLoadAdmission(
        target_model_id=target_model_id,
        entries=tuple(entries),
        ledger_status=ledger_status,
        policy_boundaries={
            "surface_scope": "model_load_admission_projection",
            "runtime_owned_inputs": [
                "runtime_status_budget",
                "runtime_model_visibility",
                "runtime_status_host_pressure",
                "runtime_status_metal_oom_cooldown",
                "model_profile",
                "model_release_candidate_latest_peak_rss",
            ],
            "does_not_execute_load": True,
            "does_not_sample_private_metal_allocator": True,
            "does_not_run_eviction": True,
            "unknown_when_host_pressure_not_sampled": True,
            "warning_headroom_bytes": int(warning_headroom_bytes),
        },
    )


def model_load_admission_to_dict(admission: ModelLoadAdmission) -> dict[str, Any]:
    """Serialize the model-load admission projection."""

    decision_counts: dict[str, int] = {}
    for entry in admission.entries:
        decision_counts[entry.admission_decision] = (
            decision_counts.get(entry.admission_decision, 0) + 1
        )
    return {
        "surface": MODEL_LOAD_ADMISSION_SURFACE,
        "version": MODEL_LOAD_ADMISSION_VERSION,
        "summary": {
            "status": "partial",
            "target_model_id": admission.target_model_id,
            "entry_count": len(admission.entries),
            "decision_counts": decision_counts,
            "supported_decisions": list(MODEL_LOAD_ADMISSION_DECISIONS),
            "supported_budget_projections": list(MODEL_LOAD_BUDGET_PROJECTIONS),
            "ledger_status": admission.ledger_status,
        },
        "entries": [
            {
                "model_id": entry.model_id,
                "admission_decision": entry.admission_decision,
                "reason_code": entry.reason_code,
                "reason_message": entry.reason_message,
                "visibility_status": entry.visibility_status,
                "profile_id": entry.profile_id,
                "profile_family": entry.profile_family,
                "budget_projection": entry.budget_projection,
                "known_peak_resident_set_bytes": entry.known_peak_resident_set_bytes,
                "projected_headroom_bytes": entry.projected_headroom_bytes,
                "current_budget_available_bytes": entry.current_budget_available_bytes,
                "host_pressure_classification": entry.host_pressure_classification,
                "cooldown_active": entry.cooldown_active,
                "already_loaded": entry.already_loaded,
                "evidence": dict(entry.evidence),
            }
            for entry in admission.entries
        ],
        "policy_boundaries": dict(admission.policy_boundaries),
    }
