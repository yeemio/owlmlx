"""Frozen schema constants and validators for comparative-evidence records.

Single authority for the surface identity, version, enumerations, required
field sets, and banned verdict vocabulary that
``docs/source-of-truth/comparative-evidence-schema-stub.md`` and
``docs/source-of-truth/comparative-evidence-harness-contract.md`` freeze.
Cross-repo consumers read these names off the wire response; this module
keeps record construction and validation in lockstep with the schema stub.
"""

from __future__ import annotations

from typing import Any, Mapping


COMPARATIVE_EVIDENCE_RECORD_SURFACE = "owlmlx.comparative_evidence_record"
COMPARATIVE_EVIDENCE_RECORD_HISTORY_SURFACE = (
    "owlmlx.comparative_evidence_record_history"
)
COMPARATIVE_EVIDENCE_RECORD_VERSION = "v1"

WORKLOAD_CLASSES: tuple[str, ...] = (
    "single_prompt_short",
    "single_prompt_long",
    "multi_prompt_serial",
    "multi_prompt_aggregated",
)

RUNTIME_IDS: tuple[str, ...] = ("owlmlx", "omlx", "vmlx")

VERDICT_GRADES: tuple[str, ...] = ("measured", "inconclusive", "rejected")

REQUIRED_RECORD_FIELDS: tuple[str, ...] = (
    "surface",
    "version",
    "recorded_at",
    "evidence_pointer",
    "host_class",
    "workload_class",
    "workload_invariants",
    "runtimes",
    "verdict_text",
    "verdict_grade",
)

REQUIRED_WORKLOAD_INVARIANT_KEYS: tuple[str, ...] = (
    "model_id",
    "model_quantization",
    "decode_max_tokens",
    "decode_temperature",
    "prompt_set_hash",
    "serving_budget_bytes",
)

REQUIRED_RUNTIME_FIELDS: tuple[str, ...] = (
    "runtime_id",
    "runtime_version",
    "measurement",
)

REQUIRED_MEASUREMENT_FIELDS: tuple[str, ...] = (
    "throughput_tokens_per_second",
    "first_token_latency_ms",
    "peak_resident_set_bytes",
    "wall_clock_ms",
    "completed_request_count",
    "failure_count",
)

BANNED_VERDICT_VOCABULARY: tuple[str, ...] = (
    "parity",
    "equivalent",
    "replaces",
    "replacement",
    "production-ready",
    "production_ready",
    "superior",
    "wins",
    "beats",
    "matches",
)


class SchemaValidationError(ValueError):
    """Raised when a record fails the frozen-schema check."""


def verdict_text_uses_banned_vocabulary(verdict_text: str) -> bool:
    """Return True when the verdict_text contains any banned phrase."""

    text = (verdict_text or "").lower()
    return any(banned in text for banned in BANNED_VERDICT_VOCABULARY)


def _require_keys(
    payload: Mapping[str, Any],
    required: tuple[str, ...],
    *,
    label: str,
) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise SchemaValidationError(
            f"{label} missing required fields: {sorted(missing)}"
        )


def _validate_measurement(measurement: Any, *, runtime_index: int) -> None:
    if not isinstance(measurement, Mapping):
        raise SchemaValidationError(
            f"runtimes[{runtime_index}].measurement must be a mapping"
        )
    _require_keys(
        measurement,
        REQUIRED_MEASUREMENT_FIELDS,
        label=f"runtimes[{runtime_index}].measurement",
    )
    failure_count = measurement.get("failure_count")
    if not isinstance(failure_count, int) or failure_count < 0:
        raise SchemaValidationError(
            f"runtimes[{runtime_index}].measurement.failure_count must be a non-negative int"
        )
    if failure_count > 0 and "failure_causes" not in measurement:
        raise SchemaValidationError(
            f"runtimes[{runtime_index}].measurement.failure_causes is required when failure_count > 0"
        )
    if "failure_causes" in measurement:
        causes = measurement["failure_causes"]
        if not isinstance(causes, list) or not all(
            isinstance(cause, str) and cause for cause in causes
        ):
            raise SchemaValidationError(
                f"runtimes[{runtime_index}].measurement.failure_causes must be a list of non-empty strings"
            )


def _validate_runtime(entry: Any, *, runtime_index: int) -> None:
    if not isinstance(entry, Mapping):
        raise SchemaValidationError(
            f"runtimes[{runtime_index}] must be a mapping"
        )
    _require_keys(
        entry,
        REQUIRED_RUNTIME_FIELDS,
        label=f"runtimes[{runtime_index}]",
    )
    runtime_id = entry["runtime_id"]
    if runtime_id not in RUNTIME_IDS:
        raise SchemaValidationError(
            f"runtimes[{runtime_index}].runtime_id={runtime_id!r} is not in the frozen RUNTIME_IDS enumeration"
        )
    if not isinstance(entry["runtime_version"], str) or not entry["runtime_version"]:
        raise SchemaValidationError(
            f"runtimes[{runtime_index}].runtime_version must be a non-empty string"
        )
    _validate_measurement(entry["measurement"], runtime_index=runtime_index)


def validate_comparative_evidence_record(record: Mapping[str, Any]) -> None:
    """Raise ``SchemaValidationError`` when ``record`` violates the frozen schema."""

    if not isinstance(record, Mapping):
        raise SchemaValidationError("record must be a mapping")

    _require_keys(record, REQUIRED_RECORD_FIELDS, label="record")

    if record["surface"] != COMPARATIVE_EVIDENCE_RECORD_SURFACE:
        raise SchemaValidationError(
            f"record.surface={record['surface']!r} must equal "
            f"{COMPARATIVE_EVIDENCE_RECORD_SURFACE!r}"
        )
    if record["version"] != COMPARATIVE_EVIDENCE_RECORD_VERSION:
        raise SchemaValidationError(
            f"record.version={record['version']!r} must equal "
            f"{COMPARATIVE_EVIDENCE_RECORD_VERSION!r}"
        )

    workload_class = record["workload_class"]
    if workload_class not in WORKLOAD_CLASSES:
        raise SchemaValidationError(
            f"record.workload_class={workload_class!r} is not in the frozen WORKLOAD_CLASSES enumeration"
        )

    invariants = record["workload_invariants"]
    if not isinstance(invariants, Mapping):
        raise SchemaValidationError(
            "record.workload_invariants must be a mapping"
        )
    _require_keys(
        invariants,
        REQUIRED_WORKLOAD_INVARIANT_KEYS,
        label="record.workload_invariants",
    )

    runtimes = record["runtimes"]
    if not isinstance(runtimes, list) or not runtimes:
        raise SchemaValidationError(
            "record.runtimes must be a non-empty list"
        )
    for index, entry in enumerate(runtimes):
        _validate_runtime(entry, runtime_index=index)

    verdict_grade = record["verdict_grade"]
    if verdict_grade not in VERDICT_GRADES:
        raise SchemaValidationError(
            f"record.verdict_grade={verdict_grade!r} is not in the frozen VERDICT_GRADES enumeration"
        )

    verdict_text = record["verdict_text"]
    if not isinstance(verdict_text, str) or not verdict_text:
        raise SchemaValidationError(
            "record.verdict_text must be a non-empty string"
        )
    if verdict_text_uses_banned_vocabulary(verdict_text):
        raise SchemaValidationError(
            "record.verdict_text contains banned vocabulary; see BANNED_VERDICT_VOCABULARY"
        )

    if not isinstance(record["host_class"], str) or not record["host_class"]:
        raise SchemaValidationError(
            "record.host_class must be a non-empty string"
        )
    if not isinstance(record["recorded_at"], str) or not record["recorded_at"]:
        raise SchemaValidationError(
            "record.recorded_at must be a non-empty ISO 8601 string"
        )
    if not isinstance(record["evidence_pointer"], str) or not record["evidence_pointer"]:
        raise SchemaValidationError(
            "record.evidence_pointer must be a non-empty repo-relative string"
        )


__all__ = [
    "BANNED_VERDICT_VOCABULARY",
    "COMPARATIVE_EVIDENCE_RECORD_HISTORY_SURFACE",
    "COMPARATIVE_EVIDENCE_RECORD_SURFACE",
    "COMPARATIVE_EVIDENCE_RECORD_VERSION",
    "REQUIRED_MEASUREMENT_FIELDS",
    "REQUIRED_RECORD_FIELDS",
    "REQUIRED_RUNTIME_FIELDS",
    "REQUIRED_WORKLOAD_INVARIANT_KEYS",
    "RUNTIME_IDS",
    "SchemaValidationError",
    "VERDICT_GRADES",
    "WORKLOAD_CLASSES",
    "validate_comparative_evidence_record",
    "verdict_text_uses_banned_vocabulary",
]
