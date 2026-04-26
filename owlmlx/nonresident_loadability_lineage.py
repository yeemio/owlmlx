"""Runtime-owned non-resident loadability lineage contract for owlmlx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .model_lineage import (
    ModelLineage,
    model_lineage_to_dict,
    normalize_model_lineage,
    validate_model_lineage,
)
from .runtime_model_visibility import (
    RuntimeModelVisibilityGate,
    RuntimeVisibleModelState,
)


NONRESIDENT_LOADABILITY_LINEAGE_SURFACE = "owlmlx.nonresident_loadability_lineage"
NONRESIDENT_LOADABILITY_LINEAGE_VERSION = "v1"
NONRESIDENT_LOADABILITY_LINEAGE_DECISIONS = (
    "known_loadable",
    "not_loadable",
    "unknown",
)


@dataclass(frozen=True, slots=True)
class NonResidentLoadabilityLineage:
    """Stable runtime-owned loadability lineage decision for a non-resident target."""

    decision: str
    target_model_id: str | None
    confidence: str
    reason_code: str
    reason_message: str
    visibility: dict[str, Any]
    lineage: dict[str, Any]
    blocking_signals: tuple[dict[str, str], ...]
    missing_signals: tuple[dict[str, str], ...]
    decision_support: dict[str, dict[str, Any]]
    inputs: dict[str, Any]


def _decision_support() -> dict[str, dict[str, Any]]:
    return {
        "known_loadable": {
            "decision_status": "supported",
            "reason_code": (
                "target_visible_lineage_record_valid_and_aligned_with_local_artifact"
            ),
        },
        "not_loadable": {
            "decision_status": "supported",
            "reason_code": (
                "target_missing_from_registry_or_artifact_or_lineage_invalid_or_mismatched"
            ),
        },
        "unknown": {
            "decision_status": "supported",
            "reason_code": (
                "loadability_lineage_source_or_visibility_registry_not_connected"
            ),
        },
    }


def _visibility_lookup(
    gate: RuntimeModelVisibilityGate | None,
    target_model_id: str | None,
) -> tuple[bool, RuntimeVisibleModelState | None]:
    if gate is None or not target_model_id:
        return False, None
    for entry in gate.entries:
        if entry.model_id == target_model_id:
            return True, entry
    return False, None


def _normalize_lineage_records(
    records: Mapping[str, Any] | None,
) -> dict[str, Mapping[str, Any] | ModelLineage] | None:
    if records is None:
        return None
    normalized: dict[str, Mapping[str, Any] | ModelLineage] = {}
    for key, value in records.items():
        if not isinstance(key, str) or not key:
            continue
        if isinstance(value, ModelLineage) or isinstance(value, Mapping):
            normalized[key] = value
    return normalized


def _lineage_payload(
    *,
    record_present: bool,
    lineage_record: Mapping[str, Any] | ModelLineage | None,
    validation_valid: bool | None,
    validation_missing_fields: tuple[str, ...],
    validation_warnings: tuple[str, ...],
    target_alignment: str,
    expected_local_path: str | None,
    actual_local_path: str | None,
) -> dict[str, Any]:
    serialized: Mapping[str, Any] | None = None
    if lineage_record is not None:
        if isinstance(lineage_record, ModelLineage):
            serialized = model_lineage_to_dict(lineage_record)
        else:
            serialized = dict(lineage_record)
    return {
        "record_present": record_present,
        "validation_valid": validation_valid,
        "validation_missing_fields": list(validation_missing_fields),
        "validation_warnings": list(validation_warnings),
        "target_alignment": target_alignment,
        "expected_local_path": expected_local_path,
        "actual_local_path": actual_local_path,
        "record": dict(serialized) if isinstance(serialized, Mapping) else None,
    }


def _missing_signals_for(
    *,
    visibility_connected: bool,
    lineage_source_connected: bool,
) -> tuple[dict[str, str], ...]:
    items: list[dict[str, str]] = []
    if not visibility_connected:
        items.append(
            {
                "layer": "visibility",
                "signal": "runtime_model_visibility_gate",
                "reason": (
                    "runtime visibility gate was not provided to the loadability "
                    "lineage contract; consumer must build it via "
                    "build_runtime_model_visibility before calling this contract"
                ),
            }
        )
    if not lineage_source_connected:
        items.append(
            {
                "layer": "loadability_lineage_source",
                "signal": "runtime_owned_loadability_lineage_records",
                "reason": (
                    "no runtime-owned loadability lineage registry was supplied "
                    "to the contract; pass lineage_records at app/kernel "
                    "construction time"
                ),
            }
        )
    return tuple(items)


def build_nonresident_loadability_lineage(
    *,
    model_id: str | None = None,
    runtime_visibility_gate: RuntimeModelVisibilityGate | None = None,
    lineage_records: Mapping[str, Any] | None = None,
    lineage_lifecycle_state: str = "stable",
) -> NonResidentLoadabilityLineage:
    """Build the runtime-owned non-resident loadability lineage decision."""

    target_model_id = (
        model_id if isinstance(model_id, str) and model_id else None
    )
    normalized_records = _normalize_lineage_records(lineage_records)
    visibility_connected = runtime_visibility_gate is not None and bool(
        runtime_visibility_gate.entries
    )
    lineage_source_connected = normalized_records is not None
    visibility_registered, visibility_state = _visibility_lookup(
        runtime_visibility_gate, target_model_id
    )

    decision = "unknown"
    confidence = "low"
    reason_code = "loadability_lineage_inputs_insufficient"
    reason_message = (
        "Loadability lineage decision could not be made because the "
        "required runtime-owned inputs are not all connected."
    )
    blocking_signals: list[dict[str, str]] = []
    target_alignment = "unknown"
    lineage_record: Mapping[str, Any] | ModelLineage | None = None
    validation_valid: bool | None = None
    validation_missing_fields: tuple[str, ...] = ()
    validation_warnings: tuple[str, ...] = ()
    expected_local_path: str | None = (
        visibility_state.local_model_dir if visibility_state is not None else None
    )
    actual_local_path: str | None = None

    if not target_model_id:
        decision = "unknown"
        confidence = "high"
        reason_code = "no_target_model_requested"
        reason_message = (
            "Loadability lineage requires an explicit target model id."
        )
        blocking_signals.append(
            {
                "layer": "request",
                "signal": "target_model_id",
                "reason": "no target model id was provided to the contract",
            }
        )
    elif not visibility_connected:
        decision = "unknown"
        confidence = "low"
        reason_code = "visibility_registry_not_connected"
        reason_message = (
            "Runtime visibility gate is not connected; loadability lineage "
            "cannot honestly classify the target."
        )
        blocking_signals.append(
            {
                "layer": "visibility",
                "signal": "runtime_model_visibility_gate",
                "reason": (
                    "the visibility gate must be supplied so the contract "
                    "can verify registration and artifact presence"
                ),
            }
        )
    elif not visibility_registered:
        decision = "not_loadable"
        confidence = "high"
        reason_code = "target_missing_from_runtime_visibility_registry"
        reason_message = (
            "The target model is not registered in the runtime-owned "
            "visibility registry, so loadability cannot be claimed."
        )
        blocking_signals.append(
            {
                "layer": "visibility_registry",
                "signal": "runtime_owned_visibility_registration",
                "reason": (
                    "target model id is absent from "
                    "DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS or the supplied "
                    "registry override"
                ),
            }
        )
    elif visibility_state is not None and not visibility_state.visible:
        decision = "not_loadable"
        confidence = "high"
        reason_code = "required_local_artifact_or_config_truth_absent"
        reason_message = (
            "Runtime visibility gate reports the target's local artifact or "
            "config is missing, so loadability cannot be claimed."
        )
        blocking_signals.append(
            {
                "layer": "local_artifact",
                "signal": (
                    visibility_state.block_reason
                    or "base_model_artifact_or_config_missing"
                ),
                "reason": (
                    f"visibility gate block_reason={visibility_state.block_reason}"
                ),
            }
        )
    elif not lineage_source_connected:
        decision = "unknown"
        confidence = "low"
        reason_code = "loadability_lineage_source_not_connected"
        reason_message = (
            "Runtime visibility gate confirms the target is registered with "
            "local artifacts, but no runtime-owned loadability lineage "
            "registry was supplied; loadability cannot be claimed without "
            "lineage validation."
        )
        blocking_signals.append(
            {
                "layer": "loadability_lineage_source",
                "signal": "runtime_owned_loadability_lineage_records",
                "reason": (
                    "the loadability lineage registry must be passed at "
                    "app/kernel construction time"
                ),
            }
        )
    elif normalized_records is not None and target_model_id not in normalized_records:
        decision = "not_loadable"
        confidence = "high"
        reason_code = "lineage_record_missing_for_visible_target"
        reason_message = (
            "Loadability lineage registry is connected but has no record for "
            "this target, so loadability cannot be claimed."
        )
        blocking_signals.append(
            {
                "layer": "loadability_lineage_record",
                "signal": "runtime_owned_loadability_lineage_record_for_target",
                "reason": (
                    "target is not present in the supplied lineage records"
                ),
            }
        )
    else:
        assert normalized_records is not None
        lineage_record = normalized_records[target_model_id]
        validation = validate_model_lineage(
            lineage_record, lifecycle_state=lineage_lifecycle_state
        )
        validation_valid = validation.valid
        validation_missing_fields = validation.missing_fields
        validation_warnings = validation.warnings
        if not validation.valid:
            decision = "not_loadable"
            confidence = "high"
            reason_code = "lineage_record_invalid_for_lifecycle_state"
            reason_message = (
                "Lineage record exists but fails lineage validation for the "
                "target lifecycle state, so loadability cannot be claimed."
            )
            blocking_signals.append(
                {
                    "layer": "lineage_validation",
                    "signal": "model_lineage_required_fields_missing",
                    "reason": (
                        "missing fields: "
                        + ", ".join(validation.missing_fields)
                        if validation.missing_fields
                        else "lineage validation reported invalid record"
                    ),
                }
            )
        else:
            normalized_record = normalize_model_lineage(lineage_record)
            actual_local_path = normalized_record.local_path or None
            if (
                visibility_state is not None
                and actual_local_path
                and actual_local_path != visibility_state.local_model_dir
            ):
                decision = "not_loadable"
                confidence = "high"
                reason_code = "lineage_target_mismatch_with_local_artifact"
                reason_message = (
                    "Lineage record's local_path does not match the visibility "
                    "registry's local_model_dir for this target, so loadability "
                    "cannot be claimed without re-aligning lineage truth."
                )
                target_alignment = "mismatch"
                blocking_signals.append(
                    {
                        "layer": "lineage_alignment",
                        "signal": "lineage_local_path_mismatch_with_visibility_local_model_dir",
                        "reason": (
                            f"lineage.local_path={actual_local_path!r} != "
                            f"visibility.local_model_dir="
                            f"{visibility_state.local_model_dir!r}"
                        ),
                    }
                )
            else:
                decision = "known_loadable"
                confidence = "medium"
                reason_code = (
                    "target_visible_lineage_valid_and_aligned_with_local_artifact"
                )
                reason_message = (
                    "Target is registered in the runtime-owned visibility "
                    "registry, local artifact and config are present, lineage "
                    "validation passes, and lineage local_path is aligned "
                    "with the visibility entry; loadability is runtime-owned."
                )
                target_alignment = "aligned"

    visibility_payload: dict[str, Any] = {
        "registered": visibility_registered,
        "visible": (
            visibility_state.visible if visibility_state is not None else False
        ),
        "block_reason": (
            visibility_state.block_reason if visibility_state is not None else None
        ),
        "local_model_dir": (
            visibility_state.local_model_dir if visibility_state is not None else None
        ),
        "config_path": (
            visibility_state.config_path if visibility_state is not None else None
        ),
        "models_root": (
            runtime_visibility_gate.models_root
            if runtime_visibility_gate is not None
            else None
        ),
        "registered_model_count": (
            len(runtime_visibility_gate.entries)
            if runtime_visibility_gate is not None
            else 0
        ),
    }

    return NonResidentLoadabilityLineage(
        decision=decision,
        target_model_id=target_model_id,
        confidence=confidence,
        reason_code=reason_code,
        reason_message=reason_message,
        visibility=visibility_payload,
        lineage=_lineage_payload(
            record_present=(
                normalized_records is not None
                and target_model_id is not None
                and target_model_id in normalized_records
            ),
            lineage_record=lineage_record,
            validation_valid=validation_valid,
            validation_missing_fields=validation_missing_fields,
            validation_warnings=validation_warnings,
            target_alignment=target_alignment,
            expected_local_path=expected_local_path,
            actual_local_path=actual_local_path,
        ),
        blocking_signals=tuple(blocking_signals),
        missing_signals=_missing_signals_for(
            visibility_connected=visibility_connected,
            lineage_source_connected=lineage_source_connected,
        ),
        decision_support=_decision_support(),
        inputs={
            "target_model_id": target_model_id,
            "lineage_lifecycle_state": lineage_lifecycle_state,
            "visibility_truth_status": (
                "runtime_owned_connected" if visibility_connected else "missing"
            ),
            "loadability_lineage_truth_status": (
                "runtime_owned_connected" if lineage_source_connected else "missing"
            ),
            "lineage_record_count": (
                len(normalized_records) if normalized_records is not None else 0
            ),
        },
    )


def nonresident_loadability_lineage_to_dict(
    lineage: NonResidentLoadabilityLineage,
) -> dict[str, Any]:
    """Serialize the runtime-owned non-resident loadability lineage decision."""

    return {
        "contract": {
            "surface": NONRESIDENT_LOADABILITY_LINEAGE_SURFACE,
            "version": NONRESIDENT_LOADABILITY_LINEAGE_VERSION,
            "stable_sections": [
                "summary",
                "reason",
                "visibility",
                "lineage",
                "blocking_signals",
                "decision_support",
                "inputs",
                "missing_signals",
            ],
        },
        "summary": {
            "status": "partial",
            "decision": lineage.decision,
            "target_model_id": lineage.target_model_id,
            "confidence": lineage.confidence,
            "supported_decisions": list(NONRESIDENT_LOADABILITY_LINEAGE_DECISIONS),
            "policy_depth": "runtime_owned_non_resident_loadability_lineage",
        },
        "reason": {
            "code": lineage.reason_code,
            "message": lineage.reason_message,
        },
        "visibility": lineage.visibility,
        "lineage": lineage.lineage,
        "blocking_signals": list(lineage.blocking_signals),
        "decision_support": lineage.decision_support,
        "inputs": lineage.inputs,
        "missing_signals": list(lineage.missing_signals),
    }


__all__ = [
    "NONRESIDENT_LOADABILITY_LINEAGE_DECISIONS",
    "NONRESIDENT_LOADABILITY_LINEAGE_SURFACE",
    "NONRESIDENT_LOADABILITY_LINEAGE_VERSION",
    "NonResidentLoadabilityLineage",
    "build_nonresident_loadability_lineage",
    "nonresident_loadability_lineage_to_dict",
]
