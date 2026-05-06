"""Builders for ``owlmlx.model_release_candidate_record`` v1 evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .model_release_candidate_schema import (
    MODEL_RELEASE_CANDIDATE_RECORD_SURFACE,
    MODEL_RELEASE_CANDIDATE_RECORD_VERSION,
    validate_model_release_candidate_record,
)


DEFAULT_MODEL_RELEASE_CANDIDATES: tuple[dict[str, str], ...] = (
    {
        "model_id": "Qwen3.6-27B",
        "lane": "mainline",
        "artifact_path": "/Users/yeemio/AI/Agent/models/Qwen3.6-27B",
        "visibility_status": "visible",
        "verdict": "needs_optimization",
    },
    {
        "model_id": "Qwen3.6-35B-A3B",
        "lane": "mainline",
        "artifact_path": "/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B",
        "visibility_status": "visible",
        "verdict": "needs_optimization",
    },
    {
        "model_id": "gemma-4-31B-it",
        "lane": "mainline",
        "artifact_path": "/Users/yeemio/AI/Agent/models/gemma-4-31B-it",
        "visibility_status": "visible",
        "verdict": "needs_optimization",
    },
    {
        "model_id": "DeepSeek-V4-Flash-2bit-DQ",
        "lane": "flagship_experimental",
        "artifact_path": (
            "/Users/yeemio/AI/Agent/model-candidates/mlx-community/"
            "DeepSeek-V4-Flash-2bit-DQ"
        ),
        "visibility_status": "not_registered",
        "verdict": "experimental_only",
    },
)


@dataclass(frozen=True, slots=True)
class ModelReleaseCandidateOperationResult:
    """One load/generate/unload/reload result block."""

    status: str
    detail: str
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class ModelReleaseCandidateRecord:
    """Frozen model release-candidate evidence record."""

    surface: str
    version: str
    created_at: str
    model_id: str
    lane: str
    runtime_url: str
    host_class: str
    artifact_path: str
    visibility_status: str
    load_result: ModelReleaseCandidateOperationResult
    generation_result: ModelReleaseCandidateOperationResult
    unload_result: ModelReleaseCandidateOperationResult
    reload_result: ModelReleaseCandidateOperationResult
    repeat_count: int
    failure_count: int
    first_token_latency_ms: float | None
    tokens_per_second: float | None
    wall_clock_ms: float | None
    peak_resident_set_bytes: int | None
    memory_headroom_bytes: int | None
    output_sanity_label: str
    owlops_observation_path: str
    verdict: str
    blockers: tuple[str, ...]
    load_time_ms: float | None = None
    reload_time_ms: float | None = None
    unload_time_ms: float | None = None
    queue_wait_ms: float | None = None
    ttft_ms: float | None = None
    decode_tokens_per_second: float | None = None
    end_to_end_tokens_per_second: float | None = None
    resident_mode: str | None = None
    prompt_template_id: str | None = None
    quality_caveats: tuple[str, ...] = ()
    memory_peak_source: str | None = None
    runtime_stream_wall_ms: float | None = None
    runtime_first_response_ms: float | None = None
    runtime_first_visible_token_ms: float | None = None
    runtime_prompt_render_ms: float | None = None
    runtime_timing_repeat_count: int | None = None
    runtime_timing_gate_status: str | None = None
    experimental_prefill_warmup_status: str | None = None
    experimental_prefill_warmup_mode: str | None = None
    experimental_prefill_warmup_ms: float | None = None
    experimental_prefill_warmup_included_in_metrics: bool | None = None


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def operation_result_to_dict(
    result: ModelReleaseCandidateOperationResult,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": result.status,
        "detail": result.detail,
    }
    if result.error_code is not None:
        payload["error_code"] = result.error_code
    return payload


def _operation_result_from_input(
    value: ModelReleaseCandidateOperationResult | Mapping[str, Any],
) -> ModelReleaseCandidateOperationResult:
    if isinstance(value, ModelReleaseCandidateOperationResult):
        return value
    return ModelReleaseCandidateOperationResult(
        status=str(value.get("status", "unknown")),
        detail=str(value.get("detail", "unknown")),
        error_code=(
            str(value["error_code"])
            if value.get("error_code") is not None
            else None
        ),
    )


def model_release_candidate_record_to_dict(
    record: ModelReleaseCandidateRecord,
) -> dict[str, Any]:
    """Serialize a model RC record to a JSON-ready dict."""

    payload = {
        "surface": record.surface,
        "version": record.version,
        "created_at": record.created_at,
        "model_id": record.model_id,
        "lane": record.lane,
        "runtime_url": record.runtime_url,
        "host_class": record.host_class,
        "artifact_path": record.artifact_path,
        "visibility_status": record.visibility_status,
        "load_result": operation_result_to_dict(record.load_result),
        "generation_result": operation_result_to_dict(record.generation_result),
        "unload_result": operation_result_to_dict(record.unload_result),
        "reload_result": operation_result_to_dict(record.reload_result),
        "repeat_count": record.repeat_count,
        "failure_count": record.failure_count,
        "first_token_latency_ms": record.first_token_latency_ms,
        "tokens_per_second": record.tokens_per_second,
        "wall_clock_ms": record.wall_clock_ms,
        "peak_resident_set_bytes": record.peak_resident_set_bytes,
        "memory_headroom_bytes": record.memory_headroom_bytes,
        "output_sanity_label": record.output_sanity_label,
        "owlops_observation_path": record.owlops_observation_path,
        "verdict": record.verdict,
        "blockers": list(record.blockers),
        "load_time_ms": record.load_time_ms,
        "reload_time_ms": record.reload_time_ms,
        "unload_time_ms": record.unload_time_ms,
        "queue_wait_ms": record.queue_wait_ms,
        "ttft_ms": record.ttft_ms,
        "decode_tokens_per_second": record.decode_tokens_per_second,
        "end_to_end_tokens_per_second": record.end_to_end_tokens_per_second,
        "resident_mode": record.resident_mode,
        "prompt_template_id": record.prompt_template_id,
        "quality_caveats": list(record.quality_caveats),
        "memory_peak_source": record.memory_peak_source,
        "runtime_stream_wall_ms": record.runtime_stream_wall_ms,
        "runtime_first_response_ms": record.runtime_first_response_ms,
        "runtime_first_visible_token_ms": record.runtime_first_visible_token_ms,
        "runtime_prompt_render_ms": record.runtime_prompt_render_ms,
        "runtime_timing_repeat_count": record.runtime_timing_repeat_count,
        "runtime_timing_gate_status": record.runtime_timing_gate_status,
        "experimental_prefill_warmup_status": (
            record.experimental_prefill_warmup_status
        ),
        "experimental_prefill_warmup_mode": record.experimental_prefill_warmup_mode,
        "experimental_prefill_warmup_ms": record.experimental_prefill_warmup_ms,
        "experimental_prefill_warmup_included_in_metrics": (
            record.experimental_prefill_warmup_included_in_metrics
        ),
    }
    validate_model_release_candidate_record(payload)
    return payload


def build_model_release_candidate_record(
    *,
    created_at: str,
    model_id: str,
    lane: str,
    runtime_url: str,
    host_class: str,
    artifact_path: str,
    visibility_status: str,
    load_result: ModelReleaseCandidateOperationResult | Mapping[str, Any],
    generation_result: ModelReleaseCandidateOperationResult | Mapping[str, Any],
    unload_result: ModelReleaseCandidateOperationResult | Mapping[str, Any],
    reload_result: ModelReleaseCandidateOperationResult | Mapping[str, Any],
    repeat_count: int,
    failure_count: int,
    first_token_latency_ms: float | None,
    tokens_per_second: float | None,
    wall_clock_ms: float | None,
    peak_resident_set_bytes: int | None,
    memory_headroom_bytes: int | None,
    output_sanity_label: str,
    owlops_observation_path: str,
    verdict: str,
    blockers: tuple[str, ...] | list[str],
    load_time_ms: float | None = None,
    reload_time_ms: float | None = None,
    unload_time_ms: float | None = None,
    queue_wait_ms: float | None = None,
    ttft_ms: float | None = None,
    decode_tokens_per_second: float | None = None,
    end_to_end_tokens_per_second: float | None = None,
    resident_mode: str | None = None,
    prompt_template_id: str | None = None,
    quality_caveats: tuple[str, ...] | list[str] = (),
    memory_peak_source: str | None = None,
    runtime_stream_wall_ms: float | None = None,
    runtime_first_response_ms: float | None = None,
    runtime_first_visible_token_ms: float | None = None,
    runtime_prompt_render_ms: float | None = None,
    runtime_timing_repeat_count: int | None = None,
    runtime_timing_gate_status: str | None = None,
    experimental_prefill_warmup_status: str | None = None,
    experimental_prefill_warmup_mode: str | None = None,
    experimental_prefill_warmup_ms: float | None = None,
    experimental_prefill_warmup_included_in_metrics: bool | None = None,
) -> ModelReleaseCandidateRecord:
    """Build and validate one model RC v1 record with optional observability v2 fields."""

    record = ModelReleaseCandidateRecord(
        surface=MODEL_RELEASE_CANDIDATE_RECORD_SURFACE,
        version=MODEL_RELEASE_CANDIDATE_RECORD_VERSION,
        created_at=created_at,
        model_id=model_id,
        lane=lane,
        runtime_url=runtime_url,
        host_class=host_class,
        artifact_path=artifact_path,
        visibility_status=visibility_status,
        load_result=_operation_result_from_input(load_result),
        generation_result=_operation_result_from_input(generation_result),
        unload_result=_operation_result_from_input(unload_result),
        reload_result=_operation_result_from_input(reload_result),
        repeat_count=int(repeat_count),
        failure_count=int(failure_count),
        first_token_latency_ms=first_token_latency_ms,
        tokens_per_second=tokens_per_second,
        wall_clock_ms=wall_clock_ms,
        peak_resident_set_bytes=peak_resident_set_bytes,
        memory_headroom_bytes=memory_headroom_bytes,
        output_sanity_label=output_sanity_label,
        owlops_observation_path=owlops_observation_path,
        verdict=verdict,
        blockers=tuple(blockers),
        load_time_ms=load_time_ms,
        reload_time_ms=reload_time_ms,
        unload_time_ms=unload_time_ms,
        queue_wait_ms=queue_wait_ms,
        ttft_ms=ttft_ms,
        decode_tokens_per_second=decode_tokens_per_second,
        end_to_end_tokens_per_second=end_to_end_tokens_per_second,
        resident_mode=resident_mode,
        prompt_template_id=prompt_template_id,
        quality_caveats=tuple(quality_caveats),
        memory_peak_source=memory_peak_source,
        runtime_stream_wall_ms=runtime_stream_wall_ms,
        runtime_first_response_ms=runtime_first_response_ms,
        runtime_first_visible_token_ms=runtime_first_visible_token_ms,
        runtime_prompt_render_ms=runtime_prompt_render_ms,
        runtime_timing_repeat_count=runtime_timing_repeat_count,
        runtime_timing_gate_status=runtime_timing_gate_status,
        experimental_prefill_warmup_status=experimental_prefill_warmup_status,
        experimental_prefill_warmup_mode=experimental_prefill_warmup_mode,
        experimental_prefill_warmup_ms=experimental_prefill_warmup_ms,
        experimental_prefill_warmup_included_in_metrics=(
            experimental_prefill_warmup_included_in_metrics
        ),
    )
    model_release_candidate_record_to_dict(record)
    return record


def _not_run_result(detail: str) -> ModelReleaseCandidateOperationResult:
    return ModelReleaseCandidateOperationResult(status="not_run", detail=detail)


def build_dry_run_model_release_candidate_records(
    *,
    runtime_url: str = "http://127.0.0.1:8066",
    host_class: str = "Mac17,6-arm64-macOS-26.4.1-128GB",
    created_at: str | None = None,
) -> tuple[ModelReleaseCandidateRecord, ...]:
    """Return the honest A0 matrix: schema-ready, no live pass claims."""

    stamp = created_at or _now_iso_utc()
    records: list[ModelReleaseCandidateRecord] = []
    for candidate in DEFAULT_MODEL_RELEASE_CANDIDATES:
        lane = candidate["lane"]
        is_deepseek = lane == "flagship_experimental"
        blockers = (
            (
                "deepseek_runtime_adapter_not_integrated",
                "technical_preview_visibility_not_registered",
                "repeated_live_run_missing",
                "owlops_observation_missing",
            )
            if is_deepseek
            else (
                "repeated_live_run_missing",
                "owlops_observation_missing",
                "reference_runtime_comparison_missing",
            )
        )
        records.append(
            build_model_release_candidate_record(
                created_at=stamp,
                model_id=candidate["model_id"],
                lane=lane,
                runtime_url=runtime_url,
                host_class=host_class,
                artifact_path=candidate["artifact_path"],
                visibility_status=candidate["visibility_status"],
                load_result=_not_run_result("A0 dry run; no live load executed"),
                generation_result=_not_run_result(
                    "A0 dry run; no live generation executed"
                ),
                unload_result=_not_run_result("A0 dry run; no live unload executed"),
                reload_result=_not_run_result("A0 dry run; no live reload executed"),
                repeat_count=0,
                failure_count=0,
                first_token_latency_ms=None,
                tokens_per_second=None,
                wall_clock_ms=None,
                peak_resident_set_bytes=None,
                memory_headroom_bytes=None,
                output_sanity_label="not_run",
                owlops_observation_path="unknown",
                verdict=candidate["verdict"],
                blockers=blockers,
                load_time_ms=None,
                reload_time_ms=None,
                unload_time_ms=None,
                queue_wait_ms=None,
                ttft_ms=None,
                decode_tokens_per_second=None,
                end_to_end_tokens_per_second=None,
                resident_mode="unknown",
                prompt_template_id="unknown",
                quality_caveats=(),
                memory_peak_source="unknown",
                runtime_stream_wall_ms=None,
                runtime_first_response_ms=None,
                runtime_first_visible_token_ms=None,
                runtime_prompt_render_ms=None,
                runtime_timing_repeat_count=None,
                runtime_timing_gate_status="not_in_scope",
                experimental_prefill_warmup_status="not_run",
                experimental_prefill_warmup_mode=None,
                experimental_prefill_warmup_ms=None,
                experimental_prefill_warmup_included_in_metrics=None,
            )
        )
    return tuple(records)


__all__ = [
    "DEFAULT_MODEL_RELEASE_CANDIDATES",
    "ModelReleaseCandidateOperationResult",
    "ModelReleaseCandidateRecord",
    "build_dry_run_model_release_candidate_records",
    "build_model_release_candidate_record",
    "model_release_candidate_record_to_dict",
    "operation_result_to_dict",
]
