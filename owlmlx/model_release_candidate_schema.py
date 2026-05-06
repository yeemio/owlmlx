"""Frozen schema constants for model release-candidate evidence records."""

from __future__ import annotations

from typing import Any, Mapping


MODEL_RELEASE_CANDIDATE_RECORD_SURFACE = "owlmlx.model_release_candidate_record"
MODEL_RELEASE_CANDIDATE_RECORD_HISTORY_SURFACE = (
    "owlmlx.model_release_candidate_record_history"
)
MODEL_RELEASE_CANDIDATE_RECORD_VERSION = "v1"

MODEL_RELEASE_CANDIDATE_LANES: tuple[str, ...] = (
    "mainline",
    "flagship_experimental",
)

MODEL_RELEASE_CANDIDATE_VISIBILITY_STATUSES: tuple[str, ...] = (
    "visible",
    "blocked",
    "not_registered",
    "unknown",
)

MODEL_RELEASE_CANDIDATE_VERDICTS: tuple[str, ...] = (
    "pass",
    "needs_optimization",
    "blocked",
    "experimental_only",
)

MODEL_RELEASE_CANDIDATE_RESULT_STATUSES: tuple[str, ...] = (
    "not_run",
    "pass",
    "failed",
    "unknown",
    "not_applicable",
)

BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY: tuple[str, ...] = (
    "parity",
    "replacement",
    "equivalent",
    "production_ready",
    "production-ready",
    "beats",
    "wins",
    "matches",
)

REQUIRED_MODEL_RELEASE_CANDIDATE_RECORD_FIELDS: tuple[str, ...] = (
    "surface",
    "version",
    "created_at",
    "model_id",
    "lane",
    "runtime_url",
    "host_class",
    "artifact_path",
    "visibility_status",
    "load_result",
    "generation_result",
    "unload_result",
    "reload_result",
    "repeat_count",
    "failure_count",
    "first_token_latency_ms",
    "tokens_per_second",
    "wall_clock_ms",
    "peak_resident_set_bytes",
    "memory_headroom_bytes",
    "output_sanity_label",
    "owlops_observation_path",
    "verdict",
    "blockers",
)

REQUIRED_MODEL_RELEASE_CANDIDATE_RESULT_FIELDS: tuple[str, ...] = (
    "status",
    "detail",
)

OPTIONAL_MODEL_RELEASE_CANDIDATE_OBSERVABILITY_FIELDS: tuple[str, ...] = (
    "load_time_ms",
    "reload_time_ms",
    "unload_time_ms",
    "queue_wait_ms",
    "ttft_ms",
    "decode_tokens_per_second",
    "end_to_end_tokens_per_second",
    "resident_mode",
    "prompt_template_id",
    "quality_caveats",
    "memory_peak_source",
    "runtime_stream_wall_ms",
    "runtime_first_response_ms",
    "runtime_first_visible_token_ms",
    "runtime_prompt_render_ms",
    "runtime_timing_repeat_count",
    "runtime_timing_gate_status",
    "experimental_prefill_warmup_status",
    "experimental_prefill_warmup_mode",
    "experimental_prefill_warmup_ms",
    "experimental_prefill_warmup_included_in_metrics",
)


class ModelReleaseCandidateSchemaError(ValueError):
    """Raised when a model release-candidate record violates the schema."""


def _require_keys(
    payload: Mapping[str, Any],
    required: tuple[str, ...],
    *,
    label: str,
) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise ModelReleaseCandidateSchemaError(
            f"{label} missing required fields: {sorted(missing)}"
        )


def _validate_non_empty_string(value: Any, *, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ModelReleaseCandidateSchemaError(
            f"{field} must be a non-empty string"
        )


def _validate_nullable_non_negative_number(value: Any, *, field: str) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)) or value < 0:
        raise ModelReleaseCandidateSchemaError(
            f"{field} must be null or a non-negative number"
        )


def _validate_string_list(value: Any, *, field: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ModelReleaseCandidateSchemaError(
            f"{field} must be a list of non-empty strings"
        )


def _validate_result(value: Any, *, field: str) -> None:
    if not isinstance(value, Mapping):
        raise ModelReleaseCandidateSchemaError(f"{field} must be a mapping")
    _require_keys(
        value,
        REQUIRED_MODEL_RELEASE_CANDIDATE_RESULT_FIELDS,
        label=field,
    )
    status = value["status"]
    if status not in MODEL_RELEASE_CANDIDATE_RESULT_STATUSES:
        raise ModelReleaseCandidateSchemaError(
            f"{field}.status={status!r} is not in the frozen result-status enumeration"
        )
    _validate_non_empty_string(value["detail"], field=f"{field}.detail")
    if "error_code" in value and value["error_code"] is not None:
        _validate_non_empty_string(value["error_code"], field=f"{field}.error_code")


def model_release_candidate_text_uses_banned_vocabulary(text: str) -> bool:
    """Return True when ``text`` contains banned release/parity wording."""

    lowered = (text or "").lower()
    return any(
        banned in lowered
        for banned in BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY
    )


def validate_model_release_candidate_record(record: Mapping[str, Any]) -> None:
    """Raise when ``record`` violates the model RC v1 schema."""

    if not isinstance(record, Mapping):
        raise ModelReleaseCandidateSchemaError("record must be a mapping")

    _require_keys(
        record,
        REQUIRED_MODEL_RELEASE_CANDIDATE_RECORD_FIELDS,
        label="record",
    )

    if record["surface"] != MODEL_RELEASE_CANDIDATE_RECORD_SURFACE:
        raise ModelReleaseCandidateSchemaError(
            f"record.surface={record['surface']!r} must equal "
            f"{MODEL_RELEASE_CANDIDATE_RECORD_SURFACE!r}"
        )
    if record["version"] != MODEL_RELEASE_CANDIDATE_RECORD_VERSION:
        raise ModelReleaseCandidateSchemaError(
            f"record.version={record['version']!r} must equal "
            f"{MODEL_RELEASE_CANDIDATE_RECORD_VERSION!r}"
        )

    for field in (
        "created_at",
        "model_id",
        "runtime_url",
        "host_class",
        "artifact_path",
        "output_sanity_label",
        "owlops_observation_path",
    ):
        _validate_non_empty_string(record[field], field=f"record.{field}")

    lane = record["lane"]
    if lane not in MODEL_RELEASE_CANDIDATE_LANES:
        raise ModelReleaseCandidateSchemaError(
            f"record.lane={lane!r} is not in the frozen lane enumeration"
        )

    visibility_status = record["visibility_status"]
    if visibility_status not in MODEL_RELEASE_CANDIDATE_VISIBILITY_STATUSES:
        raise ModelReleaseCandidateSchemaError(
            f"record.visibility_status={visibility_status!r} is not in the frozen visibility enumeration"
        )

    verdict = record["verdict"]
    if verdict not in MODEL_RELEASE_CANDIDATE_VERDICTS:
        raise ModelReleaseCandidateSchemaError(
            f"record.verdict={verdict!r} is not in the frozen verdict enumeration"
        )
    if model_release_candidate_text_uses_banned_vocabulary(verdict):
        raise ModelReleaseCandidateSchemaError(
            "record.verdict contains banned vocabulary"
        )

    for field in (
        "load_result",
        "generation_result",
        "unload_result",
        "reload_result",
    ):
        _validate_result(record[field], field=f"record.{field}")

    for field in ("repeat_count", "failure_count"):
        value = record[field]
        if not isinstance(value, int) or value < 0:
            raise ModelReleaseCandidateSchemaError(
                f"record.{field} must be a non-negative int"
            )

    for field in (
        "first_token_latency_ms",
        "tokens_per_second",
        "wall_clock_ms",
        "peak_resident_set_bytes",
        "memory_headroom_bytes",
        "load_time_ms",
        "reload_time_ms",
        "unload_time_ms",
        "queue_wait_ms",
        "ttft_ms",
        "decode_tokens_per_second",
        "end_to_end_tokens_per_second",
        "runtime_stream_wall_ms",
        "runtime_first_response_ms",
        "runtime_first_visible_token_ms",
        "runtime_prompt_render_ms",
        "experimental_prefill_warmup_ms",
    ):
        if field in record:
            _validate_nullable_non_negative_number(
                record[field],
                field=f"record.{field}",
            )

    _validate_string_list(record["blockers"], field="record.blockers")

    for field in ("resident_mode", "prompt_template_id", "memory_peak_source"):
        if field in record and record[field] is not None:
            _validate_non_empty_string(record[field], field=f"record.{field}")

    if "quality_caveats" in record:
        _validate_string_list(record["quality_caveats"], field="record.quality_caveats")

    if "runtime_timing_repeat_count" in record and record["runtime_timing_repeat_count"] is not None:
        value = record["runtime_timing_repeat_count"]
        if not isinstance(value, int) or value < 0:
            raise ModelReleaseCandidateSchemaError(
                "record.runtime_timing_repeat_count must be null or a non-negative int"
            )

    if "runtime_timing_gate_status" in record and record["runtime_timing_gate_status"] is not None:
        status = record["runtime_timing_gate_status"]
        if status not in ("supported", "partial", "unsupported", "not_in_scope"):
            raise ModelReleaseCandidateSchemaError(
                "record.runtime_timing_gate_status must be supported, partial, unsupported, or not_in_scope"
            )

    if (
        "experimental_prefill_warmup_status" in record
        and record["experimental_prefill_warmup_status"] is not None
    ):
        status = record["experimental_prefill_warmup_status"]
        if status not in ("not_run", "completed", "failed"):
            raise ModelReleaseCandidateSchemaError(
                "record.experimental_prefill_warmup_status must be not_run, completed, or failed"
            )

    if (
        "experimental_prefill_warmup_mode" in record
        and record["experimental_prefill_warmup_mode"] is not None
    ):
        _validate_non_empty_string(
            record["experimental_prefill_warmup_mode"],
            field="record.experimental_prefill_warmup_mode",
        )

    if (
        "experimental_prefill_warmup_included_in_metrics" in record
        and record["experimental_prefill_warmup_included_in_metrics"] is not None
        and not isinstance(record["experimental_prefill_warmup_included_in_metrics"], bool)
    ):
        raise ModelReleaseCandidateSchemaError(
            "record.experimental_prefill_warmup_included_in_metrics must be null or bool"
        )

    if record["lane"] == "flagship_experimental" and record["verdict"] == "pass":
        raise ModelReleaseCandidateSchemaError(
            "flagship_experimental lane cannot use verdict='pass'"
        )


__all__ = [
    "BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY",
    "MODEL_RELEASE_CANDIDATE_LANES",
    "MODEL_RELEASE_CANDIDATE_RECORD_HISTORY_SURFACE",
    "MODEL_RELEASE_CANDIDATE_RECORD_SURFACE",
    "MODEL_RELEASE_CANDIDATE_RECORD_VERSION",
    "MODEL_RELEASE_CANDIDATE_RESULT_STATUSES",
    "MODEL_RELEASE_CANDIDATE_VERDICTS",
    "MODEL_RELEASE_CANDIDATE_VISIBILITY_STATUSES",
    "ModelReleaseCandidateSchemaError",
    "OPTIONAL_MODEL_RELEASE_CANDIDATE_OBSERVABILITY_FIELDS",
    "REQUIRED_MODEL_RELEASE_CANDIDATE_RECORD_FIELDS",
    "REQUIRED_MODEL_RELEASE_CANDIDATE_RESULT_FIELDS",
    "model_release_candidate_text_uses_banned_vocabulary",
    "validate_model_release_candidate_record",
]
