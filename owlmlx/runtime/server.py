"""Minimal HTTP entry for owlmlx runtime."""

from __future__ import annotations

import json
import asyncio
import logging
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from starlette.responses import StreamingResponse

from owlmlx.runtime_model_visibility import (
    RegisteredRuntimeVisibleModel,
    build_runtime_model_visibility,
    derive_runtime_model_visibility_contract,
    runtime_model_visibility_contract,
)
from owlmlx.model_load_admission import (
    build_model_load_admission,
    model_load_admission_to_dict,
)
from owlmlx.nonresident_loadability_lineage import (
    build_nonresident_loadability_lineage,
    nonresident_loadability_lineage_to_dict,
)
from owlmlx.cache_scheduler_status import (
    build_cache_scheduler_status,
    cache_scheduler_status_to_dict,
)
from owlmlx.orchestration_status import (
    build_orchestration_status,
    orchestration_status_to_dict,
)
from owlmlx.scheduler_admission_contract import (
    build_scheduler_admission_contract,
    scheduler_admission_contract_to_dict,
)
from owlmlx.model_residency_policy import (
    build_model_residency_policy,
    model_residency_policy_to_dict,
)
from owlmlx.memory_pressure_contract import (
    build_memory_pressure_contract,
    memory_pressure_contract_to_dict,
)
from owlmlx.recovery_supervisor_contract import (
    build_recovery_supervisor_contract,
    recovery_supervisor_contract_to_dict,
)
from owlmlx.nonresident_model_admission_policy import (
    build_nonresident_model_admission_policy,
    nonresident_model_admission_policy_to_dict,
)
from owlmlx.memory_pressure_eviction_policy import (
    build_memory_pressure_eviction_policy,
    memory_pressure_eviction_policy_to_dict,
)
from owlmlx.settle_barrier_event import (
    build_settle_barrier_event,
    settle_barrier_event_to_dict,
)
from owlmlx.termination_recovery_policy import (
    build_termination_recovery_policy,
    termination_recovery_policy_to_dict,
)
from owlmlx.comparative_evidence_ledger import (
    ComparativeEvidenceLedger,
    history_envelope as comparative_evidence_history_envelope,
    still_blocked_payload as comparative_evidence_still_blocked_payload,
)
from owlmlx.model_release_candidate_ledger import (
    ModelReleaseCandidateLedger,
    model_release_candidate_history_envelope,
    model_release_candidate_still_blocked_payload,
)
from owlmlx.model_profile import ModelProfile, resolve_model_profile
from owlmlx.reasoning_trace_policy import apply_reasoning_trace_policy
from owlmlx.request_context_length_truth import (
    build_request_context_length_truth,
    request_context_length_truth_to_dict,
)
from owlmlx.runtime_monitor_test_console import (
    MONITOR_HISTORY_SURFACE,
    MONITOR_EVENT_SURFACE,
    RuntimeMonitorTrendRegistry,
    RuntimeTestRunRegistry,
    TEST_PROFILE_CATALOG,
    TEST_RUN_ABORT_SURFACE,
    TEST_RUN_EVENT_SURFACE,
    TEST_RUN_LAUNCH_SURFACE,
    build_monitor_snapshot,
    build_test_run_events,
    build_test_run_index,
    build_test_run_preflight,
    build_test_run_status,
    unsupported_operation_payload,
)

from .backends import FakeBackend, RuntimeBackend
from .kernel import RuntimeKernel
from .serving_hardening import (
    ErrorEnvelopeBuilder,
    GracefulShutdown,
    GracefulShutdownConfig,
    MetricsSnapshotExporter,
    RequestIdMiddleware,
    UnifiedErrorEnvelope,
)
from .types import ChatTurn


class LoadRequest(BaseModel):
    """HTTP request body for model load."""

    model_id: str = Field(min_length=1)
    memory_gb: float | None = Field(default=None, ge=0)
    warmup: bool = Field(default=True)


class GenerateRequest(BaseModel):
    """HTTP request body for generation."""

    prompt: str
    model_id: str | None = Field(default=None, min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: str
    content: str


class AnthropicTextBlock(BaseModel):
    type: str
    text: str | None = None
    cache_control: dict[str, Any] | None = None


class AnthropicToolUseInputBlock(BaseModel):
    type: str
    id: str | None = None
    name: str | None = None
    input: dict[str, Any] | None = None


class AnthropicToolResultInputBlock(BaseModel):
    type: str
    tool_use_id: str | None = None
    content: str | list[AnthropicTextBlock] | None = None
    is_error: bool = False


class AnthropicInputMessage(BaseModel):
    role: str
    content: str | list[AnthropicTextBlock | AnthropicToolUseInputBlock | AnthropicToolResultInputBlock]


class AnthropicToolDef(BaseModel):
    name: str
    description: str | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)


class CompletionRequest(BaseModel):
    model: str | None = Field(default=None, min_length=1)
    prompt: str = Field(min_length=1)
    max_tokens: int | None = Field(default=None, ge=1)
    temperature: float | None = None
    stop: str | list[str] | None = None
    stream: bool = False


class ChatCompletionRequest(BaseModel):
    model: str | None = Field(default=None, min_length=1)
    messages: list[ChatMessage]
    max_tokens: int | None = Field(default=None, ge=1)
    temperature: float | None = None
    stop: str | list[str] | None = None
    chat_template_kwargs: dict[str, Any] | None = None
    extra_body: dict[str, Any] | None = None
    stream: bool = False


class AnthropicMessagesRequest(BaseModel):
    model: str | None = Field(default=None, min_length=1)
    messages: list[AnthropicInputMessage]
    max_tokens: int | None = Field(default=None, ge=1)
    temperature: float | None = None
    system: str | list[AnthropicTextBlock] | None = None
    stream: bool = False
    tools: list[AnthropicToolDef] = Field(default_factory=list)
    tool_choice: str | dict[str, Any] | None = None


class UnloadRequest(BaseModel):
    """HTTP request body for model unload."""

    model_id: str = Field(min_length=1)


class RestartRequest(BaseModel):
    """HTTP request body for runtime restart of a loaded model."""

    model_id: str = Field(min_length=1)


class MemoryPressureEvictionRequest(BaseModel):
    """HTTP request body for explicit runtime-owned memory-pressure eviction."""

    protect_active: bool = Field(default=True)


class TestRunRequest(BaseModel):
    """HTTP request body for runtime-owned test-run preflight or launch."""

    model_id: str = Field(min_length=1)
    test_profile_id: str = Field(min_length=1)
    mode: str = Field(default="dry_run")
    parameters: dict[str, Any] = Field(default_factory=dict)
    operator: dict[str, Any] = Field(default_factory=dict)


def _result_to_dict(result: Any) -> dict[str, Any]:
    data = asdict(result)
    error = data.get("error_code")
    if error is not None and hasattr(error, "value"):
        data["error_code"] = error.value
    return data


def _messages_to_turns(messages: list[ChatMessage]) -> list[ChatTurn]:
    return [ChatTurn(role=message.role, content=message.content) for message in messages]


def _chat_template_kwargs_from_openai_payload(
    payload: ChatCompletionRequest,
    *,
    profile_defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    if isinstance(payload.extra_body, dict):
        raw_extra = payload.extra_body.get("chat_template_kwargs")
        if isinstance(raw_extra, dict):
            candidates.append(raw_extra)
    if isinstance(payload.chat_template_kwargs, dict):
        candidates.append(payload.chat_template_kwargs)

    merged: dict[str, Any] = dict(profile_defaults or {})
    for candidate in candidates:
        for key, value in candidate.items():
            if isinstance(key, str) and key:
                merged[key] = value
    return merged


def _openai_profile_for_model(model_id: str | None) -> ModelProfile | None:
    if not model_id:
        return None
    profile = resolve_model_profile(model_id)
    if profile.profile_id == "unknown":
        return None
    return profile


def _openai_reasoning_trace_policy(
    payload: ChatCompletionRequest,
    *,
    profile: ModelProfile | None = None,
) -> str | None:
    raw_policy = None
    if isinstance(payload.extra_body, dict):
        raw_policy = payload.extra_body.get("owlmlx_reasoning_trace_policy")
        if raw_policy is None:
            raw_policy = payload.extra_body.get("reasoning_trace_policy")
    if raw_policy in {"final_answer_content", "route_final_answer_content"}:
        return "final_answer_content"
    if raw_policy in {"raw", "none", "disabled"}:
        return None
    if (
        profile is not None
        and profile.thinking_policy.get("default_mode") == "parser_cleanup_required"
    ):
        return "final_answer_content"
    return None


def _openai_visible_text_for_policy(
    text: str,
    *,
    finish_reason: str | None,
    policy: str | None,
) -> tuple[str, dict[str, object] | None]:
    if policy != "final_answer_content":
        return text, None
    result = apply_reasoning_trace_policy(text, finish_reason=finish_reason)
    if not result.visible_reasoning_trace:
        return text, result.to_dict()
    return result.final_text or "", result.to_dict()


def _anthropic_messages_to_turns(
    messages: list[AnthropicInputMessage],
    *,
    system: str | list[AnthropicTextBlock] | None = None,
) -> list[ChatTurn]:
    turns: list[ChatTurn] = []
    system_text = _anthropic_system_to_text(system)
    if system_text:
        turns.append(ChatTurn(role="system", content=system_text))
    for message in messages:
        if isinstance(message.content, str):
            content = message.content
        else:
            text_parts: list[str] = []
            for block in message.content:
                if block.type == "text":
                    text_parts.append(str(getattr(block, "text", "") or ""))
                    continue
                if block.type == "tool_result":
                    result_content = getattr(block, "content", None)
                    if isinstance(result_content, str):
                        result_text = result_content
                    elif isinstance(result_content, list):
                        result_text = "".join(
                            str(text_block.text or "")
                            for text_block in result_content
                            if text_block.type == "text"
                        )
                    else:
                        result_text = ""
                    prefix = "[ERROR] " if getattr(block, "is_error", False) else ""
                    tool_use_id = str(getattr(block, "tool_use_id", "") or "")
                    text_parts.append(f"[tool_result:{tool_use_id}] {prefix}{result_text}".strip())
                    continue
                if block.type == "tool_use":
                    name = str(getattr(block, "name", "") or "")
                    tool_id = str(getattr(block, "id", "") or "")
                    tool_input = getattr(block, "input", None) or {}
                    text_parts.append(
                        f"[tool_use:{tool_id}] {name} {json.dumps(tool_input, ensure_ascii=False)}".strip()
                    )
                    continue
            content = "\n".join(part for part in text_parts if part)
        if content:
            turns.append(ChatTurn(role=message.role, content=content))
    return turns


def _anthropic_system_to_text(system: str | list[AnthropicTextBlock] | None) -> str:
    if isinstance(system, str):
        return system
    if not system:
        return ""
    text_parts: list[str] = []
    for block in system:
        if getattr(block, "type", None) == "text":
            text = str(getattr(block, "text", "") or "")
            if text:
                text_parts.append(text)
    return "\n".join(text_parts)


def _openai_response_dict(
    *,
    completion_id: str,
    model: str,
    text: str,
    finish_reason: str = "stop",
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    reasoning_trace_policy: dict[str, object] | None = None,
) -> dict[str, Any]:
    usage = None
    if prompt_tokens is not None or completion_tokens is not None:
        pt = int(prompt_tokens or 0)
        ct = int(completion_tokens or 0)
        usage = {
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "total_tokens": pt + ct,
        }
    message: dict[str, Any] = {"role": "assistant", "content": text}
    if reasoning_trace_policy is not None:
        message["owlmlx_reasoning_trace_policy"] = reasoning_trace_policy
    payload = {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": finish_reason,
            }
        ],
    }
    if usage is not None:
        payload["usage"] = usage
    return payload


def _compat_error_response(
    *,
    request_id: str,
    message: str,
    code: str,
    status_code: int,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers={"x-request-id": request_id},
        content={
            "id": request_id,
            "object": "error",
            "error": {
                "message": message,
                "code": code,
            },
        },
    )


def _anthropic_error_response(
    *,
    request_id: str,
    message: str,
    code: str,
    status_code: int,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers={"x-request-id": request_id},
        content={
            "type": "error",
            "error": {
                "type": code,
                "message": message,
            },
        },
    )


def _openai_completion_dict(
    *,
    completion_id: str,
    model: str,
    text: str,
    finish_reason: str = "stop",
) -> dict[str, Any]:
    return {
        "id": completion_id,
        "object": "text_completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "text": text,
                "finish_reason": finish_reason,
            }
        ],
    }


def _anthropic_usage_dict(*, input_tokens: int | None, output_tokens: int | None) -> dict[str, int]:
    return {
        "input_tokens": int(input_tokens or 0),
        "output_tokens": int(output_tokens or 0),
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }


def _anthropic_message_dict(
    *,
    message_id: str,
    model: str,
    text: str,
    stop_reason: str = "end_turn",
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> dict[str, Any]:
    return {
        "id": message_id,
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": _anthropic_usage_dict(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ),
    }


def _estimate_input_tokens_from_turns(turns: list[ChatTurn]) -> int:
    return max(1, sum(len(turn.content) for turn in turns) // 4) if turns else 0


def create_app(
    kernel: RuntimeKernel | None = None,
    *,
    visibility_models_root: str | None = None,
    visibility_registry: list[Any] | tuple[Any, ...] | None = None,
    loadability_lineage_records: dict[str, Any] | None = None,
    comparative_evidence_ledger_path: str | None = None,
    model_release_candidate_ledger_path: str | None = None,
    runtime_test_run_ledger_path: str | None = None,
    runtime_monitor_trend_ledger_path: str | None = None,
    runtime_monitor_sample_interval_s: float = 0,
    runtime_monitor_max_samples: int = 20160,
    runtime_monitor_url: str = "http://127.0.0.1:8066",
) -> FastAPI:
    """Create a minimal owlmlx runtime HTTP app.

    `loadability_lineage_records` is the runtime-owned non-resident
    loadability lineage registry. It is connected at app construction time and
    consumed by the nonresident-loadability-lineage and
    nonresident-model-admission-policy endpoints. It is intentionally not a
    per-request hint.

    `comparative_evidence_ledger_path` is the runtime-owned JSONL ledger that
    backs `/v1/runtime/comparative-evidence` and
    `/v1/runtime/comparative-evidence/history`. It is connected at app
    construction time. When ``None``, both endpoints fail visibly as
    ``still_blocked``.

    `model_release_candidate_ledger_path` is the runtime-owned JSONL ledger
    that backs `/v1/runtime/model-release-candidates` and
    `/v1/runtime/model-release-candidates/history`.

    `runtime_test_run_ledger_path` is the runtime-owned JSONL audit ledger
    that backs Runtime Monitor test-run index/status/event replay surfaces.
    When absent, launch remains structured `unsupported` without writing a
    persisted registry row.

    `runtime_monitor_trend_ledger_path` is the runtime-owned rolling JSONL
    history store for long-running monitor samples. When connected and
    `runtime_monitor_sample_interval_s` is positive, the runtime also samples
    itself in the background without loading or generating models.
    """

    runtime = kernel if kernel is not None else RuntimeKernel(FakeBackend())
    app = FastAPI(title="owlmlx Runtime", version="0.0.0-runtime7")

    # D-6 structured request logging: log every request lifecycle through a
    # single logger named ``owlmlx.runtime.server.request``. Reads
    # ``request.state.request_id`` (set by D-1 ``RequestIdMiddleware``) so
    # every log line is correlatable. INFO on start + finish; WARNING on
    # exception (the unified error envelope handler at app-level still
    # produces the response, so the log line is the only forensic
    # breadcrumb that the exception happened on this request id).
    #
    # IMPORTANT: this middleware is registered BEFORE ``RequestIdMiddleware``
    # below, so that ``RequestIdMiddleware`` becomes the OUTER middleware
    # in Starlette's stacking model (later-registered = outer = runs first
    # on inbound). That ordering guarantees ``request.state.request_id``
    # is set by the time this logging middleware reads it.
    _request_logger = logging.getLogger("owlmlx.runtime.server.request")

    @app.middleware("http")
    async def _request_lifecycle_log_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = getattr(request.state, "request_id", None)
        method = request.method
        path = request.url.path
        started = time.monotonic()
        _request_logger.info(
            "request.start",
            extra={
                "owlmlx_event": "request.start",
                "owlmlx_request_id": request_id,
                "owlmlx_http_method": method,
                "owlmlx_http_path": path,
            },
        )
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.monotonic() - started) * 1000.0, 3)
            _request_logger.warning(
                "request.exception",
                extra={
                    "owlmlx_event": "request.exception",
                    "owlmlx_request_id": request_id,
                    "owlmlx_http_method": method,
                    "owlmlx_http_path": path,
                    "owlmlx_duration_ms": duration_ms,
                    "owlmlx_exception_class": type(exc).__name__,
                },
            )
            raise
        duration_ms = round((time.monotonic() - started) * 1000.0, 3)
        _request_logger.info(
            "request.finish",
            extra={
                "owlmlx_event": "request.finish",
                "owlmlx_request_id": request_id,
                "owlmlx_http_method": method,
                "owlmlx_http_path": path,
                "owlmlx_http_status": response.status_code,
                "owlmlx_duration_ms": duration_ms,
            },
        )
        return response

    # RequestIdMiddleware MUST be registered AFTER the logging middleware
    # above so it becomes the outer wrapper (earlier-defined middleware is
    # innermost in Starlette's stacking model). This ordering ensures
    # ``request.state.request_id`` is populated by the time the logging
    # middleware's start log fires.
    app.add_middleware(RequestIdMiddleware)

    app.state.kernel = runtime
    app.state.loadability_lineage_records = (
        dict(loadability_lineage_records)
        if loadability_lineage_records is not None
        else None
    )
    app.state.visibility_models_root = visibility_models_root
    app.state.visibility_registry = visibility_registry
    app.state.comparative_evidence_ledger = (
        ComparativeEvidenceLedger(comparative_evidence_ledger_path)
        if comparative_evidence_ledger_path is not None
        else None
    )
    app.state.model_release_candidate_ledger = (
        ModelReleaseCandidateLedger(model_release_candidate_ledger_path)
        if model_release_candidate_ledger_path is not None
        else None
    )
    app.state.runtime_test_run_registry = (
        RuntimeTestRunRegistry(runtime_test_run_ledger_path)
        if runtime_test_run_ledger_path is not None
        else None
    )
    app.state.runtime_monitor_trend_registry = (
        RuntimeMonitorTrendRegistry(
            runtime_monitor_trend_ledger_path,
            max_rows=runtime_monitor_max_samples,
        )
        if runtime_monitor_trend_ledger_path is not None
        else None
    )
    app.state.runtime_monitor_sample_interval_s = runtime_monitor_sample_interval_s
    app.state.runtime_monitor_url = runtime_monitor_url.rstrip("/") or "http://127.0.0.1:8066"
    app.state.runtime_monitor_sampler_task = None
    app.state.runtime_test_runs = {}
    app.state.runtime_test_run_abort_requested = set()
    app.state.runtime_test_run_tasks = {}

    def _request_runtime_url(request: Request) -> str:
        return str(request.base_url).rstrip("/")

    def _runtime_model_visibility_contract() -> dict[str, Any]:
        return derive_runtime_model_visibility_contract(
            runtime.inventory_snapshot(),
            models_root=visibility_models_root,
            registry=visibility_registry,
        )

    def _model_release_candidate_records_and_status() -> tuple[
        list[dict[str, Any]],
        str,
        str | None,
    ]:
        ledger = app.state.model_release_candidate_ledger
        if ledger is None:
            return [], "not_connected", None
        records = ledger.history()
        return records, "available" if records else "empty", str(ledger.path)

    def _runtime_test_run_records() -> list[dict[str, Any]]:
        registry = app.state.runtime_test_run_registry
        records: list[dict[str, Any]] = []
        if registry is not None:
            records.extend(registry.history())
        records_by_id = {
            str(record.get("run_id")): record
            for record in records
            if record.get("run_id")
        }
        for run_id, run in app.state.runtime_test_runs.items():
            records_by_id[str(run_id)] = dict(run)
        return list(records_by_id.values())

    def _runtime_test_run_ledger_status() -> tuple[str, str | None]:
        registry = app.state.runtime_test_run_registry
        if registry is None:
            return "not_connected", None
        return "available", str(registry.path)

    def _runtime_monitor_trend_ledger_status() -> tuple[str, str | None]:
        registry = app.state.runtime_monitor_trend_registry
        if registry is None:
            return "not_connected", None
        return "available", str(registry.path)

    def _build_runtime_monitor_snapshot(runtime_url: str) -> dict[str, Any]:
        (
            records,
            ledger_status,
            ledger_path,
        ) = _model_release_candidate_records_and_status()
        test_run_ledger_status, test_run_ledger_path = _runtime_test_run_ledger_status()
        return build_monitor_snapshot(
            runtime_status=runtime.status_dict(),
            runtime_url=runtime_url,
            visibility_contract=_runtime_model_visibility_contract(),
            model_load_admission=_runtime_model_load_admission_contract(),
            model_release_candidate_records=records,
            model_release_candidate_ledger_status=ledger_status,
            model_release_candidate_ledger_path=ledger_path,
            test_runs=_runtime_test_run_records(),
            test_run_audit_ledger_status=test_run_ledger_status,
            test_run_audit_ledger_path=test_run_ledger_path,
        )

    def _record_runtime_monitor_sample(
        snapshot: Mapping[str, Any],
        *,
        source: str,
    ) -> dict[str, Any] | None:
        registry = app.state.runtime_monitor_trend_registry
        if registry is None:
            return None
        return registry.append_snapshot(snapshot, source=source)

    async def _runtime_monitor_sampler_loop() -> None:
        interval = float(app.state.runtime_monitor_sample_interval_s or 0)
        registry = app.state.runtime_monitor_trend_registry
        runtime_url = str(app.state.runtime_monitor_url)
        if registry is None or interval <= 0:
            return
        while True:
            try:
                runtime.sample_host_pressure()
                snapshot = _build_runtime_monitor_snapshot(runtime_url)
                registry.append_snapshot(
                    snapshot,
                    source="runtime_monitor_background_sampler",
                )
            except Exception as exc:  # pragma: no cover - defensive sampler guard
                registry.append_error(
                    runtime_url=runtime_url,
                    source="runtime_monitor_background_sampler",
                    error=f"{type(exc).__name__}: {exc}",
                )
            await asyncio.sleep(interval)

    async def _start_runtime_monitor_sampler() -> None:
        interval = float(app.state.runtime_monitor_sample_interval_s or 0)
        if app.state.runtime_monitor_trend_registry is None or interval <= 0:
            return
        if app.state.runtime_monitor_sampler_task is None:
            app.state.runtime_monitor_sampler_task = asyncio.create_task(
                _runtime_monitor_sampler_loop()
            )

    async def _stop_runtime_monitor_sampler() -> None:
        task = app.state.runtime_monitor_sampler_task
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        app.state.runtime_monitor_sampler_task = None

    app.router.on_startup.append(_start_runtime_monitor_sampler)
    app.router.on_shutdown.append(_stop_runtime_monitor_sampler)

    graceful_shutdown = GracefulShutdown(config=GracefulShutdownConfig())

    def _graceful_shutdown_gate_status() -> dict[str, Any]:
        gate_status = runtime.status_dict().get("generation_gate") or {}
        return dict(gate_status)

    def _graceful_shutdown_unload_models() -> dict[str, Any]:
        loaded = runtime.status_dict().get("backend", {}).get("loaded_models") or []
        unloaded: list[str] = []
        failed: list[dict[str, Any]] = []
        for entry in loaded:
            model_id = entry.get("model_id") if isinstance(entry, dict) else None
            if not isinstance(model_id, str) or not model_id:
                continue
            result = runtime.unload_model(model_id)
            if getattr(result, "ok", False):
                unloaded.append(model_id)
            else:
                failed.append(
                    {
                        "model_id": model_id,
                        "message": getattr(result, "message", None),
                    }
                )
        return {"unloaded_model_ids": unloaded, "failed": failed}

    async def _graceful_shutdown_drain() -> None:
        await graceful_shutdown.on_shutdown(
            gate_status_callable=_graceful_shutdown_gate_status,
            unload_models_callable=_graceful_shutdown_unload_models,
        )

    app.router.on_shutdown.append(_graceful_shutdown_drain)

    # ------------------------------------------------------------------
    # D-3: Unified error envelope wiring
    # ------------------------------------------------------------------
    #
    # Two surfaces are wired here, both backed by ``ErrorEnvelopeBuilder``
    # from ``serving_hardening.py``:
    #
    # 1. A generic ``Exception`` handler so any unhandled exception that
    #    escapes a route (native or compat) returns a unified error
    #    envelope with HTTP 500 and NO leak of the raw exception class
    #    name or message.
    # 2. A small adapter ``_native_runtime_response`` used only by the
    #    three native lifecycle routes (``/v1/load``, ``/v1/generate``,
    #    ``/v1/unload``) that today return ``ok=False`` inside an HTTP
    #    200 body. The adapter maps the typed ``error_code`` to a proper
    #    HTTP status (400/404/500) and renders the unified envelope.
    #
    # Compat routes (``/v1/chat/completions``, ``/v1/messages``,
    # ``/v1/completions``) keep their own ``_compat_error_response`` /
    # ``_anthropic_error_response`` shapes — OpenAI/Anthropic SDK callers
    # depend on the existing contract.
    error_envelope_builder = ErrorEnvelopeBuilder(namespace="owlmlx_native")

    # ------------------------------------------------------------------
    # D-4: Prometheus metrics snapshot exporter wiring
    # ------------------------------------------------------------------
    #
    # The C-4 scaffold's ``MetricsSnapshotExporter`` is instantiated once
    # per app and consulted on every ``GET /metrics`` scrape. The
    # exporter is pure: it reads the gate status dict and the optional
    # native admission snapshot dict, then renders a Prometheus
    # text-exposition snapshot via ``io.StringIO`` (stdlib only, no
    # ``prometheus_client`` dependency). Per the D-4 wiring discipline,
    # ``/metrics`` is served as plain text (NOT a JSON envelope) because
    # Prometheus scrapers expect ``text/plain; version=0.0.4`` line-based
    # output. The route is also unauthenticated by default — operators
    # are responsible for network-level access control.
    _metrics_exporter = MetricsSnapshotExporter(namespace="owlmlx_native")

    def _request_id_from_request(request: Request | None) -> str | None:
        if request is None:
            return None
        try:
            return getattr(request.state, "request_id", None)
        except Exception:  # pragma: no cover - defensive guard
            return None

    async def _unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Convert any unhandled exception into a unified error envelope.

        The handler MUST NEVER raise. If the builder itself fails for any
        reason (e.g. an exotic exception type), fall back to a literal
        dict response with status 500 and a generic message.
        """

        request_id = _request_id_from_request(request)
        try:
            envelope = error_envelope_builder.from_unexpected(
                exc, request_id=request_id
            )
            body = envelope.to_response_body()
            status_code = envelope.http_status
        except Exception:  # pragma: no cover - last-resort fallback
            body = {
                "id": "err_owlmlx_native_fallback",
                "object": "error",
                "error_code": "unexpected_error",
                "message": "unexpected internal error",
                "request_id": request_id,
                "http_status": 500,
            }
            status_code = 500
        headers: dict[str, str] = {}
        if request_id:
            headers["x-request-id"] = request_id
        return JSONResponse(
            status_code=status_code,
            headers=headers,
            content=body,
        )

    app.add_exception_handler(Exception, _unhandled_exception_handler)

    # Native error_code -> HTTP status. The scaffold's default mapping
    # collapses ``model_not_loaded`` and ``model_already_loaded`` to 409;
    # the native namespace promotes ``model_not_loaded`` to 404 ("the
    # named resource does not exist on this runtime") and treats
    # ``model_already_loaded`` as success-with-detail (HTTP 200 via the
    # idempotent-load path).
    _NATIVE_ERROR_CODE_TO_HTTP_STATUS: dict[str, int] = {
        "invalid_request": 400,
        "model_not_loaded": 404,
        "model_not_found": 404,
        "unsupported_model_family": 400,
        "memory_budget_exceeded": 400,
        "backend_error": 500,
        "model_pinned": 409,
    }

    def _native_runtime_response(
        result: Any,
        *,
        request: Request,
        success_status: int = 200,
        idempotent_already_loaded: bool = False,
    ) -> JSONResponse:
        """Render a native runtime ``RuntimeOperationResult`` as JSON.

        On ``ok=True`` (or on the idempotent ``model_already_loaded``
        case for ``/v1/load``) returns the existing dict shape with
        ``success_status``. On ``ok=False`` returns the unified
        envelope with the mapped HTTP status. The success body is
        unchanged from the prior contract; only the error path gets the
        new envelope.
        """

        body = _result_to_dict(result)
        request_id = _request_id_from_request(request)
        headers: dict[str, str] = {}
        if request_id:
            headers["x-request-id"] = request_id

        ok = bool(body.get("ok", False))
        error_code = body.get("error_code")

        # Idempotent /v1/load: model_already_loaded is success-with-detail.
        if (
            idempotent_already_loaded
            and not ok
            and error_code == "model_already_loaded"
        ):
            return JSONResponse(
                status_code=success_status,
                headers=headers,
                content=body,
            )

        if ok:
            return JSONResponse(
                status_code=success_status,
                headers=headers,
                content=body,
            )

        # ok=False. Build a unified envelope and pick the HTTP status.
        message = str(body.get("message") or "runtime operation failed")
        normalized_error_code = (
            str(error_code) if isinstance(error_code, str) and error_code else "backend_error"
        )
        http_status = _NATIVE_ERROR_CODE_TO_HTTP_STATUS.get(
            normalized_error_code, 500
        )
        envelope: UnifiedErrorEnvelope = (
            error_envelope_builder.from_runtime_error_code(
                error_code=normalized_error_code,
                message=message,
                request_id=request_id,
                http_status=http_status,
            )
        )
        return JSONResponse(
            status_code=envelope.http_status,
            headers=headers,
            content=envelope.to_response_body(),
        )

    def _store_runtime_test_run(row: dict[str, Any]) -> dict[str, Any]:
        run_id = str(row.get("run_id") or "")
        if run_id:
            app.state.runtime_test_runs[run_id] = dict(row)
        return row

    def _runtime_test_run_terminal(row: Mapping[str, Any]) -> bool:
        return str(row.get("status") or "") in {
            "succeeded",
            "failed",
            "error",
            "refused",
            "unsupported",
            "aborted",
        }

    def _runtime_test_abort_requested(run_id: str) -> bool:
        return run_id in app.state.runtime_test_run_abort_requested

    def _loaded_model_ids() -> set[str]:
        return {
            str(model.model_id)
            for model in runtime.backend.status().loaded_models
            if getattr(model, "model_id", None)
        }

    def _runtime_test_prompt(profile_id: str, test_kind: str) -> str:
        if profile_id == "qwen36-27b-decode" or test_kind == "decode":
            return (
                "Write a concise operational note about an on-device runtime "
                "monitor. Keep it under 90 words and avoid lists."
            )
        if profile_id == "qwen36-35b-ttft-template" or test_kind == "ttft_template":
            return (
                "Answer in final form only: explain why first-token latency "
                "matters for a local model operator in two sentences."
            )
        if profile_id == "gemma-repetitive-output-template" or test_kind == "repetitive_output_template":
            return (
                "Answer once, without repetition: summarize the health of a "
                "clean idle runtime in one short paragraph."
            )
        return "Return a short runtime smoke-test response."

    def _runtime_test_messages(profile_id: str, test_kind: str) -> list[ChatTurn] | None:
        if profile_id == "qwen36-27b-decode" and test_kind == "decode":
            return None
        return [
            ChatTurn(
                role="system",
                content=(
                    "You are a local runtime smoke-test assistant. Answer in "
                    "the final response only, concisely."
                ),
            ),
            ChatTurn(role="user", content=_runtime_test_prompt(profile_id, test_kind)),
        ]

    def _runtime_test_evidence_path(registry: RuntimeTestRunRegistry, run_id: str) -> Path:
        return registry.path.parent / run_id / "result.json"

    def _dump_runtime_test_evidence(
        *,
        registry: RuntimeTestRunRegistry,
        row: Mapping[str, Any],
        repeats: list[dict[str, Any]],
        post_run_health: Mapping[str, Any],
    ) -> str:
        evidence_path = _runtime_test_evidence_path(registry, str(row["run_id"]))
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "contract": {
                "surface": "owlmlx.runtime.test_run.evidence",
                "version": "v1",
            },
            "run": dict(row),
            "repeats": repeats,
            "post_run_health": dict(post_run_health),
            "policy_boundaries": {
                "runtime_owner": "owlmlx",
                "initiated_by": "owlops_runtime_monitor",
                "does_not_touch_legacy_listeners": ["8001", "8009"],
            },
        }
        evidence_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return str(evidence_path)

    def _safe_error_code(value: Any) -> str | None:
        if value is None:
            return None
        raw = getattr(value, "value", value)
        return str(raw)

    def _metrics_from_repeats(
        *,
        repeats: list[dict[str, Any]],
        load_ms: float | None,
        unload_ms: float | None,
        wall_ms: float,
    ) -> dict[str, Any]:
        successful = [repeat for repeat in repeats if repeat.get("status") == "succeeded"]
        output_tokens = sum(int(repeat.get("output_tokens") or 0) for repeat in successful)
        ttft_values = [
            float(repeat["ttft_ms"])
            for repeat in successful
            if repeat.get("ttft_ms") is not None
        ]
        decode_values = [
            float(repeat["decode_tokens_per_second"])
            for repeat in successful
            if repeat.get("decode_tokens_per_second") is not None
        ]
        return {
            "load_ms": load_ms,
            "unload_ms": unload_ms,
            "wall_ms": round(wall_ms, 3),
            "ttft_ms": round(sum(ttft_values) / len(ttft_values), 3) if ttft_values else None,
            "decode_tokens_per_second": (
                round(sum(decode_values) / len(decode_values), 6) if decode_values else None
            ),
            "output_tokens": output_tokens,
            "repeat_count": len(repeats),
            "successful_repeat_count": len(successful),
        }

    async def _execute_runtime_test_run(
        *,
        row: dict[str, Any],
        request_payload: dict[str, Any],
        registry: RuntimeTestRunRegistry,
    ) -> None:
        run_id = str(row["run_id"])
        model_id = str(row.get("model_id") or "")
        parameters = dict(row.get("parameters") or {})
        profile_id = str(row.get("test_profile_id") or "")
        test_kind = str(parameters.get("test_kind") or "decode")
        repeat_count = max(1, min(int(parameters.get("repeat_count") or 1), 50))
        max_tokens = max(1, int(parameters.get("max_tokens") or 64))
        temperature = float(parameters.get("temperature") or 0.0)
        memory_gb = parameters.get("memory_gb")
        if memory_gb is None:
            profile = TEST_PROFILE_CATALOG.get(profile_id) or {}
            memory_gb = profile.get("estimated_memory_gb")
        load_ms: float | None = None
        unload_ms: float | None = None
        repeats: list[dict[str, Any]] = []
        loaded_by_run = False
        started_s = time.monotonic()
        latest_row = row

        def persist_event(**kwargs: Any) -> dict[str, Any]:
            nonlocal latest_row
            latest_row = registry.add_event(latest_row, **kwargs)
            _store_runtime_test_run(latest_row)
            return latest_row

        try:
            latest_row = registry.update(
                latest_row,
                status="running",
                phase="load",
                reason="runtime_worker_started",
            )
            _store_runtime_test_run(latest_row)

            if _runtime_test_abort_requested(run_id):
                persist_event(
                    event_type="test_run.abort_observed",
                    phase="abort",
                    severity="warning",
                    status="aborted",
                    reason="operator_abort_requested_before_load",
                    payload={"reason": "operator_abort_requested_before_load"},
                )
                return

            loaded_before = model_id in _loaded_model_ids()
            if loaded_before:
                persist_event(
                    event_type="test_run.load_skipped_already_loaded",
                    phase="load",
                    severity="info",
                    payload={"model_id": model_id},
                )
            else:
                persist_event(
                    event_type="test_run.load_started",
                    phase="load",
                    severity="info",
                    payload={"model_id": model_id, "memory_gb": memory_gb},
                )
                load_started_s = time.monotonic()
                load_result = await asyncio.to_thread(
                    runtime.load_model,
                    model_id,
                    memory_gb=float(memory_gb) if memory_gb is not None else None,
                )
                load_ms = (time.monotonic() - load_started_s) * 1000.0
                if not load_result.ok:
                    persist_event(
                        event_type="test_run.load_failed",
                        phase="load",
                        severity="error",
                        status="failed",
                        reason=load_result.message,
                        payload={
                            "ok": load_result.ok,
                            "message": load_result.message,
                            "error_code": _safe_error_code(load_result.error_code),
                            "detail": dict(load_result.detail),
                            "load_ms": round(load_ms, 3),
                        },
                    )
                    evidence_path = _dump_runtime_test_evidence(
                        registry=registry,
                        row=latest_row,
                        repeats=repeats,
                        post_run_health=runtime.status_dict(),
                    )
                    latest_row = registry.update(
                        latest_row,
                        status="failed",
                        phase="load",
                        reason=load_result.message,
                        evidence_path=evidence_path,
                        metrics=_metrics_from_repeats(
                            repeats=repeats,
                            load_ms=load_ms,
                            unload_ms=unload_ms,
                            wall_ms=(time.monotonic() - started_s) * 1000.0,
                        ),
                    )
                    _store_runtime_test_run(latest_row)
                    return
                loaded_by_run = True
                persist_event(
                    event_type="test_run.load_completed",
                    phase="load",
                    severity="info",
                    payload={
                        "ok": load_result.ok,
                        "message": load_result.message,
                        "load_ms": round(load_ms, 3),
                    },
                )

            messages = _runtime_test_messages(profile_id, test_kind)
            prompt = _runtime_test_prompt(profile_id, test_kind)
            for index in range(1, repeat_count + 1):
                if _runtime_test_abort_requested(run_id):
                    persist_event(
                        event_type="test_run.abort_observed",
                        phase="abort",
                        severity="warning",
                        status="aborting",
                        reason="operator_abort_requested_between_repeats",
                        payload={"repeat": index},
                    )
                    break
                repeat_started_s = time.monotonic()
                first_token_s: float | None = None
                done_s: float | None = None
                output_parts: list[str] = []
                output_tokens = 0
                prompt_tokens: int | None = None
                finish_reason: str | None = None
                persist_event(
                    event_type="test_run.generate_started",
                    phase="generate",
                    severity="info",
                    status="running",
                    payload={
                        "repeat": index,
                        "model_id": model_id,
                        "request_mode": "messages" if messages is not None else "raw_prompt",
                        "max_tokens": max_tokens,
                    },
                )
                stream = (
                    runtime.generate_stream_messages(
                        messages,
                        model_id=model_id,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    if messages is not None
                    else runtime.generate_stream(
                        prompt,
                        model_id=model_id,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                )
                async for event in stream:
                    if event.event == "error":
                        repeat = {
                            "repeat": index,
                            "status": "failed",
                            "error_code": _safe_error_code(event.error_code),
                            "message": event.detail.get("message", "generation failed"),
                            "detail": dict(event.detail),
                        }
                        repeats.append(repeat)
                        persist_event(
                            event_type="test_run.generate_failed",
                            phase="generate",
                            severity="error",
                            status="failed",
                            reason=repeat["message"],
                            payload=repeat,
                        )
                        break
                    if event.event == "token":
                        if first_token_s is None:
                            first_token_s = time.monotonic()
                            persist_event(
                                event_type="test_run.first_token",
                                phase="generate",
                                severity="info",
                                payload={
                                    "repeat": index,
                                    "ttft_ms": round((first_token_s - repeat_started_s) * 1000.0, 3),
                                    "was_queued": event.was_queued,
                                    "wait_time_s": event.wait_time_s,
                                },
                            )
                        output_parts.append(event.text)
                        output_tokens = int(event.completion_tokens or output_tokens + 1)
                        prompt_tokens = event.prompt_tokens or prompt_tokens
                        continue
                    if event.event == "done":
                        done_s = time.monotonic()
                        output_tokens = int(event.completion_tokens or output_tokens)
                        prompt_tokens = event.prompt_tokens or prompt_tokens
                        finish_reason = event.finish_reason
                        break
                if repeats and repeats[-1].get("repeat") == index and repeats[-1].get("status") == "failed":
                    break
                done_s = done_s or time.monotonic()
                ttft_ms = (
                    (first_token_s - repeat_started_s) * 1000.0
                    if first_token_s is not None
                    else None
                )
                decode_window_s = (
                    max(done_s - first_token_s, 0.000001)
                    if first_token_s is not None
                    else max(done_s - repeat_started_s, 0.000001)
                )
                decode_tokens = max(output_tokens - (1 if first_token_s is not None else 0), 0)
                decode_tps = decode_tokens / decode_window_s if decode_tokens > 0 else None
                repeat = {
                    "repeat": index,
                    "status": "succeeded",
                    "ttft_ms": round(ttft_ms, 3) if ttft_ms is not None else None,
                    "decode_tokens_per_second": round(decode_tps, 6) if decode_tps is not None else None,
                    "output_tokens": output_tokens,
                    "prompt_tokens": prompt_tokens,
                    "wall_ms": round((done_s - repeat_started_s) * 1000.0, 3),
                    "finish_reason": finish_reason,
                    "output_preview": "".join(output_parts)[:1000],
                }
                repeats.append(repeat)
                persist_event(
                    event_type="test_run.generate_completed",
                    phase="generate",
                    severity="info",
                    payload=repeat,
                )

            aborted = _runtime_test_abort_requested(run_id)
            if loaded_by_run:
                persist_event(
                    event_type="test_run.unload_started",
                    phase="unload",
                    severity="info",
                    status="running",
                    payload={"model_id": model_id},
                )
                unload_started_s = time.monotonic()
                unload_result = await asyncio.to_thread(runtime.unload_model, model_id)
                unload_ms = (time.monotonic() - unload_started_s) * 1000.0
                persist_event(
                    event_type=(
                        "test_run.unload_completed"
                        if unload_result.ok
                        else "test_run.unload_failed"
                    ),
                    phase="unload",
                    severity="info" if unload_result.ok else "error",
                    status="running" if unload_result.ok else "failed",
                    reason=None if unload_result.ok else unload_result.message,
                    payload={
                        "ok": unload_result.ok,
                        "message": unload_result.message,
                        "error_code": _safe_error_code(unload_result.error_code),
                        "unload_ms": round(unload_ms, 3),
                    },
                )

            post_run_health = runtime.status_dict()
            wall_ms = (time.monotonic() - started_s) * 1000.0
            metrics = _metrics_from_repeats(
                repeats=repeats,
                load_ms=load_ms,
                unload_ms=unload_ms,
                wall_ms=wall_ms,
            )
            final_status = (
                "aborted"
                if aborted
                else "succeeded"
                if repeats and all(repeat.get("status") == "succeeded" for repeat in repeats)
                else "failed"
            )
            final_reason = (
                "operator_abort_requested"
                if aborted
                else "runtime_test_completed"
                if final_status == "succeeded"
                else "runtime_test_failed"
            )
            evidence_path = _dump_runtime_test_evidence(
                registry=registry,
                row=latest_row,
                repeats=repeats,
                post_run_health=post_run_health,
            )
            persist_event(
                event_type="test_run.completed" if final_status == "succeeded" else f"test_run.{final_status}",
                phase="completed",
                severity="info" if final_status == "succeeded" else "warning",
                status=final_status,
                reason=final_reason,
                metrics=metrics,
                evidence_path=evidence_path,
                payload={
                    "status": final_status,
                    "reason": final_reason,
                    "metrics": metrics,
                    "evidence_path": evidence_path,
                },
            )
        except Exception as exc:  # pragma: no cover - defensive live worker
            evidence_path = _dump_runtime_test_evidence(
                registry=registry,
                row=latest_row,
                repeats=repeats,
                post_run_health=runtime.status_dict(),
            )
            latest_row = registry.add_event(
                latest_row,
                event_type="test_run.worker_error",
                phase="error",
                severity="error",
                status="error",
                reason=str(exc),
                evidence_path=evidence_path,
                payload={"message": str(exc), "evidence_path": evidence_path},
            )
            _store_runtime_test_run(latest_row)
        finally:
            app.state.runtime_test_run_abort_requested.discard(run_id)

    def _sse_replay_response(events: list[dict[str, Any]]) -> StreamingResponse:
        def event_stream():
            for event in events:
                yield f"event: {event.get('type', 'runtime_test_run_event')}\n"
                yield f"id: {event.get('event_id', '')}\n"
                yield f"data: {json.dumps(event, sort_keys=True)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    def _runtime_model_load_admission_contract(
        target_model_id: str | None = None,
    ) -> dict[str, Any]:
        visibility_gate = build_runtime_model_visibility(
            runtime.inventory_snapshot(),
            models_root=visibility_models_root,
            registry=visibility_registry,
        )
        (
            records,
            ledger_status,
            _ledger_path,
        ) = _model_release_candidate_records_and_status()
        return model_load_admission_to_dict(
            build_model_load_admission(
                runtime_status=runtime.status_dict(),
                visibility_contract=runtime_model_visibility_contract(visibility_gate),
                model_release_candidate_records=records,
                target_model_id=target_model_id,
                ledger_status=ledger_status,
            )
        )

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        status = runtime.status_dict()
        backend_detail = status["backend"]["detail"]
        return {
            "contract": {
                "surface": "owlmlx.healthz",
                "version": "stabilization1",
            },
            "runtime": "owlmlx",
            "ok": status["backend"]["healthy"],
            "readiness": status["health"]["readiness"],
            "active_model_id": status["active_model_id"],
            "model_count": status["inventory"]["model_count"],
            "backend_name": status["backend"]["backend_name"],
            "backend_error": backend_detail.get("last_error"),
            "persistent_child": backend_detail.get("persistent_child", False),
            "child_health": backend_detail.get("child_health", {}),
        }

    @app.post("/v1/load")
    def load_model(payload: LoadRequest, request: Request) -> JSONResponse:
        result = runtime.load_model(
            payload.model_id,
            memory_gb=payload.memory_gb,
            post_load_warmup=payload.warmup,
        )
        # Idempotent: model_already_loaded is success-with-detail (HTTP 200).
        return _native_runtime_response(
            result,
            request=request,
            idempotent_already_loaded=True,
        )

    @app.post("/v1/generate")
    async def generate(payload: GenerateRequest, request: Request) -> JSONResponse:
        result = await runtime.generate(
            payload.prompt,
            model_id=payload.model_id,
            **payload.params,
        )
        return _native_runtime_response(result, request=request)

    @app.post("/v1/generate/stream")
    async def generate_stream(payload: GenerateRequest) -> StreamingResponse:
        async def event_source():
            async for event in runtime.generate_stream(
                payload.prompt,
                model_id=payload.model_id,
                **payload.params,
            ):
                data = asdict(event)
                error = data.get("error_code")
                if error is not None and hasattr(error, "value"):
                    data["error_code"] = error.value
                yield json.dumps(data) + "\n"

        return StreamingResponse(event_source(), media_type="application/x-ndjson")

    @app.post("/v1/chat/completions")
    async def chat_completions(payload: ChatCompletionRequest, request: Request):
        target_model = payload.model or runtime.active_model_id
        profile = _openai_profile_for_model(target_model)
        completion_id = f"chatcmpl-{uuid.uuid4().hex}"
        # D-5: request_id sourced from D-1 RequestIdMiddleware-set
        # ``request.state.request_id`` rather than locally regenerated.
        # The middleware honors inbound ``x-request-id`` and otherwise
        # generates ``req_<uuid4hex>`` — that single source is the
        # value compat responses now carry.
        request_id = request.state.request_id
        messages = _messages_to_turns(payload.messages)
        params: dict[str, Any] = {}
        if payload.max_tokens is not None:
            params["max_tokens"] = payload.max_tokens
        if payload.temperature is not None:
            params["temperature"] = payload.temperature
        if payload.stop is not None:
            params["stop"] = payload.stop
        elif profile is not None and profile.stop_token_strings:
            params["stop"] = list(profile.stop_token_strings)
        chat_template_kwargs = _chat_template_kwargs_from_openai_payload(
            payload,
            profile_defaults=profile.chat_template_kwargs if profile is not None else None,
        )
        if chat_template_kwargs:
            params["chat_template_kwargs"] = chat_template_kwargs
        reasoning_policy = _openai_reasoning_trace_policy(payload, profile=profile)

        if not payload.stream:
            result = await runtime.generate_messages(messages, model_id=target_model, **params)
            if not result.ok:
                status_code = 404 if result.error_code and result.error_code.value == "model_not_loaded" else 503
                return _compat_error_response(
                    request_id=request_id,
                    message=result.message,
                    code=result.error_code.value if result.error_code is not None else "backend_error",
                        status_code=status_code,
                )
            visible_text, reasoning_policy_payload = _openai_visible_text_for_policy(
                result.text,
                finish_reason=result.finish_reason,
                policy=reasoning_policy,
            )
            return JSONResponse(
                headers={"x-request-id": request_id},
                content=_openai_response_dict(
                    completion_id=completion_id,
                    model=target_model or "unknown",
                    text=visible_text,
                    finish_reason=result.finish_reason or "stop",
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                    reasoning_trace_policy=reasoning_policy_payload,
                ),
            )

        async def sse_source():
            if reasoning_policy == "final_answer_content":
                buffered_text: list[str] = []
                finish_reason = "stop"
                prompt_tokens: int | None = None
                completion_tokens: int | None = None
                async for event in runtime.generate_stream_messages(
                    messages,
                    model_id=target_model,
                    **params,
                ):
                    if event.prompt_tokens is not None:
                        prompt_tokens = event.prompt_tokens
                    if event.completion_tokens is not None:
                        completion_tokens = event.completion_tokens
                    if event.finish_reason:
                        finish_reason = event.finish_reason
                    if event.event == "token":
                        buffered_text.append(event.text)
                    elif event.event == "done":
                        raw_text = "".join(buffered_text)
                        visible_text, policy_payload = _openai_visible_text_for_policy(
                            raw_text,
                            finish_reason=finish_reason,
                            policy=reasoning_policy,
                        )
                        if visible_text:
                            content_chunk = {
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": target_model or "unknown",
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {"content": visible_text},
                                        "finish_reason": None,
                                    }
                                ],
                            }
                            yield f"data: {json.dumps(content_chunk)}\n\n"
                        done_chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": target_model or "unknown",
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": finish_reason or "stop",
                                }
                            ],
                        }
                        if policy_payload is not None:
                            done_chunk["owlmlx_reasoning_trace_policy"] = policy_payload
                        if prompt_tokens is not None or completion_tokens is not None:
                            done_chunk["usage"] = {
                                "prompt_tokens": int(prompt_tokens or 0),
                                "completion_tokens": int(completion_tokens or 0),
                                "total_tokens": int(prompt_tokens or 0)
                                + int(completion_tokens or 0),
                            }
                        yield f"data: {json.dumps(done_chunk)}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                    elif event.event == "error":
                        chunk = {
                            "id": completion_id,
                            "object": "error",
                            "error": {
                                "message": event.detail.get("message", "stream generation failed"),
                                "code": event.error_code.value if event.error_code is not None else "backend_error",
                            },
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                return

            async for event in runtime.generate_stream_messages(
                messages,
                model_id=target_model,
                **params,
            ):
                if event.event == "token":
                    chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": target_model or "unknown",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": event.text},
                                "finish_reason": None,
                            }
                        ],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif event.event == "done":
                    chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": target_model or "unknown",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": event.finish_reason or "stop",
                            }
                        ],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                elif event.event == "error":
                    chunk = {
                        "id": completion_id,
                        "object": "error",
                        "error": {
                            "message": event.detail.get("message", "stream generation failed"),
                            "code": event.error_code.value if event.error_code is not None else "backend_error",
                        },
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

        return StreamingResponse(
            sse_source(),
            media_type="text/event-stream",
            headers={"x-request-id": request_id},
        )

    @app.post("/v1/messages")
    async def anthropic_messages(payload: AnthropicMessagesRequest, request: Request):
        target_model = payload.model or runtime.active_model_id
        message_id = f"msg_{uuid.uuid4().hex[:24]}"
        # D-5: request_id sourced from RequestIdMiddleware (see D-1).
        request_id = request.state.request_id
        turns = _anthropic_messages_to_turns(payload.messages, system=payload.system)
        params: dict[str, Any] = {}
        if payload.max_tokens is not None:
            params["max_tokens"] = payload.max_tokens
        if payload.temperature is not None:
            params["temperature"] = payload.temperature
        if payload.tools:
            params["tools"] = [tool.model_dump() for tool in payload.tools]
        if payload.tool_choice is not None:
            params["tool_choice"] = payload.tool_choice
        input_tokens = _estimate_input_tokens_from_turns(turns)

        if not payload.stream:
            result = await runtime.generate_messages(turns, model_id=target_model, **params)
            if not result.ok:
                status_code = 404 if result.error_code and result.error_code.value == "model_not_loaded" else 503
                return _anthropic_error_response(
                    request_id=request_id,
                    message=result.message,
                    code=result.error_code.value if result.error_code is not None else "backend_error",
                    status_code=status_code,
                )
            return JSONResponse(
                headers={"x-request-id": request_id},
                content=(
                    {
                        **_anthropic_message_dict(
                            message_id=message_id,
                            model=target_model or "unknown",
                            text=result.text,
                            stop_reason="tool_use" if result.finish_reason == "tool_use" else "end_turn",
                            input_tokens=result.prompt_tokens or input_tokens,
                            output_tokens=result.completion_tokens,
                        ),
                        "content": (
                            [
                                {
                                    "type": "tool_use",
                                    "id": tool["id"],
                                    "name": tool["name"],
                                    "input": tool["input"],
                                }
                                for tool in result.detail.get("tool_uses", [])
                            ]
                            if result.finish_reason == "tool_use"
                            else [{"type": "text", "text": result.text}]
                        ),
                    }
                ),
            )

        async def anthropic_sse_source():
            yield (
                "event: message_start\n"
                f"data: {json.dumps({'type': 'message_start', 'message': _anthropic_message_dict(message_id=message_id, model=target_model or 'unknown', text='', stop_reason=None, input_tokens=input_tokens, output_tokens=0)})}\n\n"
            )
            text_block_started = False
            async for event in runtime.generate_stream_messages(
                turns,
                model_id=target_model,
                **params,
            ):
                if event.event == "token":
                    if not text_block_started:
                        yield (
                            "event: content_block_start\n"
                            "data: {\"type\":\"content_block_start\",\"index\":0,"
                            "\"content_block\":{\"type\":\"text\",\"text\":\"\"}}\n\n"
                        )
                        text_block_started = True
                    chunk = {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "text_delta", "text": event.text},
                    }
                    yield f"event: content_block_delta\ndata: {json.dumps(chunk)}\n\n"
                    continue
                if event.event == "tool_use":
                    tool = dict(event.detail.get("tool_use") or {})
                    tool_input = tool.get("input") or {}
                    start = {
                        "type": "content_block_start",
                        "index": 0,
                        "content_block": {
                            "type": "tool_use",
                            "id": tool.get("id"),
                            "name": tool.get("name"),
                            "input": {},
                        },
                    }
                    yield f"event: content_block_start\ndata: {json.dumps(start)}\n\n"
                    if tool_input:
                        delta = {
                            "type": "content_block_delta",
                            "index": 0,
                            "delta": {
                                "type": "input_json_delta",
                                "partial_json": json.dumps(tool_input, ensure_ascii=False),
                            },
                        }
                        yield f"event: content_block_delta\ndata: {json.dumps(delta)}\n\n"
                    yield "event: content_block_stop\ndata: {\"type\":\"content_block_stop\",\"index\":0}\n\n"
                    continue
                if event.event == "done":
                    if event.finish_reason != "tool_use":
                        if text_block_started:
                            yield "event: content_block_stop\ndata: {\"type\":\"content_block_stop\",\"index\":0}\n\n"
                    message_delta = {
                        "type": "message_delta",
                        "delta": {"stop_reason": "tool_use" if event.finish_reason == "tool_use" else "end_turn", "stop_sequence": None},
                        "usage": {"output_tokens": int(event.completion_tokens or 0)},
                    }
                    yield f"event: message_delta\ndata: {json.dumps(message_delta)}\n\n"
                    yield "event: message_stop\ndata: {\"type\":\"message_stop\"}\n\n"
                    return
                if event.event == "error":
                    error_obj = {
                        "type": "error",
                        "error": {
                            "type": event.error_code.value if event.error_code is not None else "api_error",
                            "message": event.detail.get("message", "stream generation failed"),
                        },
                    }
                    yield f"event: error\ndata: {json.dumps(error_obj)}\n\n"
                    return

        return StreamingResponse(
            anthropic_sse_source(),
            media_type="text/event-stream",
            headers={"x-request-id": request_id},
        )

    @app.post("/v1/messages/count_tokens")
    def anthropic_count_tokens(payload: AnthropicMessagesRequest) -> dict[str, Any]:
        turns = _anthropic_messages_to_turns(payload.messages, system=payload.system)
        return {"input_tokens": _estimate_input_tokens_from_turns(turns)}

    @app.post("/v1/completions")
    async def completions(payload: CompletionRequest, request: Request):
        target_model = payload.model or runtime.active_model_id
        completion_id = f"cmpl-{uuid.uuid4().hex}"
        # D-5: request_id sourced from RequestIdMiddleware (see D-1).
        request_id = request.state.request_id
        params: dict[str, Any] = {}
        if payload.max_tokens is not None:
            params["max_tokens"] = payload.max_tokens
        if payload.temperature is not None:
            params["temperature"] = payload.temperature
        if payload.stop is not None:
            params["stop"] = payload.stop

        if not payload.stream:
            result = await runtime.generate(payload.prompt, model_id=target_model, **params)
            if not result.ok:
                status_code = 404 if result.error_code and result.error_code.value == "model_not_loaded" else 503
                return _compat_error_response(
                    request_id=request_id,
                    message=result.message,
                    code=result.error_code.value if result.error_code is not None else "backend_error",
                    status_code=status_code,
                )
            return JSONResponse(
                headers={"x-request-id": request_id},
                content=_openai_completion_dict(
                    completion_id=completion_id,
                    model=target_model or "unknown",
                    text=result.text,
                    finish_reason="stop",
                ),
            )

        async def sse_completion_source():
            async for event in runtime.generate_stream(
                payload.prompt,
                model_id=target_model,
                **params,
            ):
                if event.event == "token":
                    chunk = {
                        "id": completion_id,
                        "object": "text_completion",
                        "created": int(time.time()),
                        "model": target_model or "unknown",
                        "choices": [
                            {
                                "index": 0,
                                "text": event.text,
                                "finish_reason": None,
                            }
                        ],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    continue
                if event.event == "done":
                    chunk = {
                        "id": completion_id,
                        "object": "text_completion",
                        "created": int(time.time()),
                        "model": target_model or "unknown",
                        "choices": [
                            {
                                "index": 0,
                                "text": "",
                                "finish_reason": event.finish_reason or "stop",
                            }
                        ],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                if event.event == "error":
                    chunk = {
                        "id": completion_id,
                        "object": "error",
                        "error": {
                            "message": event.detail.get("message", "stream generation failed"),
                            "code": event.error_code.value if event.error_code is not None else "backend_error",
                        },
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

        return StreamingResponse(
            sse_completion_source(),
            media_type="text/event-stream",
            headers={"x-request-id": request_id},
        )

    @app.get("/v1/openai/models")
    def openai_models(request: Request):
        # D-5: request_id sourced from RequestIdMiddleware (see D-1).
        request_id = request.state.request_id
        visibility_contract = derive_runtime_model_visibility_contract(
            runtime.inventory_snapshot(),
            models_root=visibility_models_root,
            registry=visibility_registry,
        )
        return JSONResponse(
            headers={"x-request-id": request_id},
            content={
                "object": "list",
                "data": [
                    {
                        "id": model_id,
                        "object": "model",
                        "owned_by": "owlmlx",
                    }
                    for model_id in visibility_contract["visible_model_ids"]
                ],
            },
        )

    @app.get("/v1/models")
    def models() -> dict[str, Any]:
        status = runtime.status_dict()
        visibility_contract = derive_runtime_model_visibility_contract(
            runtime.inventory_snapshot(),
            models_root=visibility_models_root,
            registry=visibility_registry,
        )
        return {
            "active_model_id": status["active_model_id"],
            "inventory": status["inventory"],
            "budget": status["budget"],
            "health": status["health"],
            "generation_gate": status["generation_gate"],
            "backend": status["backend"],
            "visibility_contract": visibility_contract,
        }

    @app.get("/v1/runtime/model-visibility")
    def runtime_model_visibility() -> dict[str, Any]:
        return _runtime_model_visibility_contract()

    @app.get("/v1/runtime/model-load-admission")
    def runtime_model_load_admission(model_id: str | None = None) -> dict[str, Any]:
        return _runtime_model_load_admission_contract(model_id)

    @app.post("/v1/runtime/host-pressure-sample")
    def runtime_host_pressure_sample() -> dict[str, Any]:
        snapshot = runtime.sample_host_pressure()
        return {
            "surface": "owlmlx.host_pressure_sample",
            "version": "v1",
            "snapshot": snapshot,
            "policy_boundaries": {
                "action_scope": "explicit_operator_sample",
                "updates_runtime_status_host_pressure_cache": True,
                "does_not_load_model": True,
                "does_not_sample_private_metal_allocator": True,
                "does_not_run_eviction": True,
            },
        }

    @app.get("/v1/runtime/status")
    def runtime_status() -> dict[str, Any]:
        return runtime.status_dict()

    @app.get("/v1/runtime/monitor/snapshot")
    def runtime_monitor_snapshot(request: Request) -> dict[str, Any]:
        snapshot = _build_runtime_monitor_snapshot(_request_runtime_url(request))
        _record_runtime_monitor_sample(snapshot, source="runtime_monitor_snapshot_route")
        return snapshot

    @app.get("/v1/runtime/monitor/history")
    def runtime_monitor_history(
        limit: int = Query(default=720, ge=1, le=20160),
        window_s: int | None = Query(default=None, ge=1),
    ) -> JSONResponse:
        registry = app.state.runtime_monitor_trend_registry
        if registry is None:
            status, path = _runtime_monitor_trend_ledger_status()
            return JSONResponse(
                status_code=503,
                content={
                    "contract": {
                        "surface": MONITOR_HISTORY_SURFACE,
                        "version": "v1",
                    },
                    "sampled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "status": "not_connected",
                    "ledger_status": status,
                    "ledger_path": path,
                    "history_count": 0,
                    "samples": [],
                    "policy_boundaries": {
                        "read_only": True,
                        "runtime_owned_history": True,
                        "does_not_load_model": True,
                        "does_not_generate": True,
                        "does_not_abort_process": True,
                    },
                },
            )
        return JSONResponse(
            status_code=200,
            content=registry.envelope(limit=limit, window_s=window_s),
        )

    @app.get("/v1/runtime/monitor/events")
    def runtime_monitor_events() -> StreamingResponse:
        events: list[dict[str, Any]] = []
        for run in _runtime_test_run_records()[-20:]:
            events.extend(
                dict(event)
                for event in run.get("events", [])
                if isinstance(event, dict)
            )
        events.sort(key=lambda event: str(event.get("sampled_at") or ""))
        return _sse_replay_response(events[-100:])

    @app.post("/v1/runtime/test-runs/preflight")
    def runtime_test_runs_preflight(
        payload: TestRunRequest,
        request: Request,
    ) -> dict[str, Any]:
        runtime.sample_host_pressure()
        return build_test_run_preflight(
            request_payload=payload.model_dump(),
            runtime_status=runtime.status_dict(),
            runtime_url=_request_runtime_url(request),
            visibility_contract=_runtime_model_visibility_contract(),
            model_load_admission=_runtime_model_load_admission_contract(payload.model_id),
            test_runs=_runtime_test_run_records(),
        )

    @app.get("/v1/runtime/test-runs")
    def runtime_test_runs() -> dict[str, Any]:
        ledger_status, ledger_path = _runtime_test_run_ledger_status()
        return build_test_run_index(
            test_runs=_runtime_test_run_records(),
            audit_ledger_status=ledger_status,
            audit_ledger_path=ledger_path,
        )

    @app.post("/v1/runtime/test-runs")
    async def runtime_test_runs_launch(
        payload: TestRunRequest,
        request: Request,
    ) -> JSONResponse:
        runtime.sample_host_pressure()
        preflight = build_test_run_preflight(
            request_payload=payload.model_dump(),
            runtime_status=runtime.status_dict(),
            runtime_url=_request_runtime_url(request),
            visibility_contract=_runtime_model_visibility_contract(),
            model_load_admission=_runtime_model_load_admission_contract(payload.model_id),
            test_runs=_runtime_test_run_records(),
        )
        registry = app.state.runtime_test_run_registry
        if registry is None:
            response = unsupported_operation_payload(
                surface=TEST_RUN_LAUNCH_SURFACE,
                unsupported_feature="runtime_test_run_ledger",
                reason="runtime_test_run_ledger_not_connected",
            )
            response["preflight"] = preflight
            response["audit_ledger_status"] = "not_connected"
            response["audit_ledger_path"] = None
            return JSONResponse(status_code=503, content=response)

        decision = str(preflight.get("decision") or "unknown")
        reason = str(preflight.get("reason") or "unknown")
        if decision != "admit":
            audit_row = registry.create_launch(
                request_payload=payload.model_dump(),
                preflight=preflight,
                status="refused",
                launch_decision="refused",
                reason=f"preflight_{decision}: {reason}",
            )
            _store_runtime_test_run(audit_row)
            response = {
                "contract": {
                    "surface": TEST_RUN_LAUNCH_SURFACE,
                    "version": "v1",
                },
                "sampled_at": audit_row["updated_at"],
                "status": "refused",
                "launch_decision": "refused",
                "reason": audit_row["reason"],
                "preflight": preflight,
                "audit_ledger_status": "available",
                "audit_ledger_path": str(registry.path),
                "run_id": audit_row["run_id"],
                "run": audit_row,
                "policy_boundaries": {
                    "does_not_load_model": True,
                    "does_not_generate": True,
                    "does_not_touch_legacy_listeners": ["8001", "8009"],
                },
            }
            return JSONResponse(status_code=409, content=response)

        audit_row = registry.create_launch(
            request_payload=payload.model_dump(),
            preflight=preflight,
            status="queued",
            launch_decision="accepted",
            reason="runtime_test_run_worker_queued",
        )
        _store_runtime_test_run(audit_row)
        task = asyncio.create_task(
            _execute_runtime_test_run(
                row=audit_row,
                request_payload=payload.model_dump(),
                registry=registry,
            )
        )
        app.state.runtime_test_run_tasks[audit_row["run_id"]] = task
        response = {
            "contract": {
                "surface": TEST_RUN_LAUNCH_SURFACE,
                "version": "v1",
            },
            "sampled_at": audit_row["updated_at"],
            "status": "queued",
            "launch_decision": "accepted",
            "reason": "runtime_test_run_worker_queued",
            "preflight": preflight,
            "audit_ledger_status": "available",
            "audit_ledger_path": str(registry.path),
            "run_id": audit_row["run_id"],
            "run": audit_row,
            "policy_boundaries": {
                "launched_by_runtime": True,
                "does_not_touch_legacy_listeners": ["8001", "8009"],
                "abort_is_audited_only": True,
            },
        }
        return JSONResponse(status_code=202, content=response)

    @app.get("/v1/runtime/test-runs/{run_id}/events")
    def runtime_test_run_events(run_id: str):
        payload = build_test_run_events(
            run_id=run_id,
            test_runs=_runtime_test_run_records(),
        )
        if payload.get("status") == "not_found":
            return JSONResponse(status_code=404, content=payload)
        return _sse_replay_response(payload["events"])

    @app.post("/v1/runtime/test-runs/{run_id}/abort")
    def runtime_test_run_abort(run_id: str) -> JSONResponse:
        known_runs = {
            str(run.get("run_id")): dict(run)
            for run in _runtime_test_run_records()
            if run.get("run_id")
        }
        run = known_runs.get(run_id)
        if run is None:
            return JSONResponse(
                status_code=404,
                content={
                    "contract": {
                        "surface": TEST_RUN_ABORT_SURFACE,
                        "version": "v1",
                    },
                    "status": "not_found",
                    "run_id": run_id,
                    "reason": "runtime_test_run_not_found",
                    "policy_boundaries": {
                        "does_not_abort_process": True,
                        "does_not_touch_legacy_listeners": ["8001", "8009"],
                    },
                },
            )
        if _runtime_test_run_terminal(run):
            return JSONResponse(
                status_code=409,
                content={
                    "contract": {
                        "surface": TEST_RUN_ABORT_SURFACE,
                        "version": "v1",
                    },
                    "status": "not_applicable",
                    "run_id": run_id,
                    "reason": f"run_already_terminal:{run.get('status')}",
                    "policy_boundaries": {
                        "does_not_abort_process": True,
                        "does_not_touch_legacy_listeners": ["8001", "8009"],
                    },
                },
            )
        registry = app.state.runtime_test_run_registry
        app.state.runtime_test_run_abort_requested.add(run_id)
        if registry is not None:
            updated = registry.add_event(
                run,
                event_type="test_run.abort_requested",
                phase="abort",
                severity="warning",
                status="aborting",
                reason="operator_abort_requested",
                payload={
                    "reason": "operator_abort_requested",
                    "does_not_abort_process": True,
                },
            )
            _store_runtime_test_run(updated)
        return JSONResponse(
            status_code=202,
            content={
                "contract": {
                    "surface": TEST_RUN_ABORT_SURFACE,
                    "version": "v1",
                },
                "status": "aborting",
                "run_id": run_id,
                "reason": "operator_abort_requested",
                "policy_boundaries": {
                    "does_not_abort_process": True,
                    "worker_observes_abort_between_phases": True,
                    "does_not_touch_legacy_listeners": ["8001", "8009"],
                },
            },
        )

    @app.get("/v1/runtime/test-runs/{run_id}")
    def runtime_test_run_status(run_id: str) -> JSONResponse:
        payload = build_test_run_status(
            run_id=run_id,
            test_runs=_runtime_test_run_records(),
        )
        return JSONResponse(
            status_code=404 if payload.get("status") == "not_found" else 200,
            content=payload,
        )

    @app.get("/v1/runtime/cache-scheduler-status")
    def runtime_cache_scheduler_status() -> dict[str, Any]:
        return cache_scheduler_status_to_dict(
            build_cache_scheduler_status(gate=runtime.generation_gate)
        )

    @app.get("/v1/runtime/orchestration-status")
    def runtime_orchestration_status() -> dict[str, Any]:
        return orchestration_status_to_dict(
            build_orchestration_status(
                runtime_status=runtime.status_dict(),
                abort_recovery_snapshot=runtime.abort_recovery.snapshot(),
            )
        )

    @app.get("/v1/runtime/scheduler-admission-contract")
    def runtime_scheduler_admission_contract(
        request_class: str = "unknown",
        model_id: str | None = None,
        context_tokens: int | None = None,
        request_context_class: str | None = None,
    ) -> dict[str, Any]:
        return scheduler_admission_contract_to_dict(
            build_scheduler_admission_contract(
                runtime_status=runtime.status_dict(),
                request_class=request_class,
                model_id=model_id,
                abort_recovery_snapshot=runtime.abort_recovery.snapshot(),
                context_tokens=context_tokens,
                request_context_class=request_context_class,
            )
        )

    @app.get("/v1/runtime/request-context-length-truth")
    def runtime_request_context_length_truth(
        context_tokens: int | None = None,
        request_context_class: str | None = None,
    ) -> dict[str, Any]:
        return request_context_length_truth_to_dict(
            build_request_context_length_truth(
                context_tokens=context_tokens,
                request_context_class=request_context_class,
            )
        )

    @app.get("/v1/runtime/model-residency-policy")
    def runtime_model_residency_policy(
        model_id: str | None = None,
    ) -> dict[str, Any]:
        return model_residency_policy_to_dict(
            build_model_residency_policy(
                runtime_status=runtime.status_dict(),
                model_id=model_id,
            )
        )

    @app.get("/v1/runtime/memory-pressure-contract")
    def runtime_memory_pressure_contract() -> dict[str, Any]:
        return memory_pressure_contract_to_dict(
            build_memory_pressure_contract(runtime_status=runtime.status_dict())
        )

    @app.get("/v1/runtime/recovery-supervisor-contract")
    def runtime_recovery_supervisor_contract() -> dict[str, Any]:
        return recovery_supervisor_contract_to_dict(
            build_recovery_supervisor_contract(
                runtime_status=runtime.status_dict(),
                abort_recovery_snapshot=runtime.abort_recovery.snapshot(),
            )
        )

    def _build_loadability_lineage_for_request(
        target_model_id: str | None,
    ):
        records = app.state.loadability_lineage_records
        if records is None:
            return None
        snapshot = (
            runtime.inventory.snapshot()
            if hasattr(runtime, "inventory")
            and hasattr(runtime.inventory, "snapshot")
            else None
        )
        visibility_gate = build_runtime_model_visibility(
            snapshot,
            models_root=app.state.visibility_models_root,
            registry=app.state.visibility_registry,
        )
        return build_nonresident_loadability_lineage(
            model_id=target_model_id,
            runtime_visibility_gate=visibility_gate,
            lineage_records=records,
        )

    @app.get("/v1/runtime/nonresident-loadability-lineage")
    def runtime_nonresident_loadability_lineage(
        model_id: str | None = None,
    ) -> dict[str, Any]:
        snapshot = (
            runtime.inventory.snapshot()
            if hasattr(runtime, "inventory")
            and hasattr(runtime.inventory, "snapshot")
            else None
        )
        visibility_gate = build_runtime_model_visibility(
            snapshot,
            models_root=app.state.visibility_models_root,
            registry=app.state.visibility_registry,
        )
        return nonresident_loadability_lineage_to_dict(
            build_nonresident_loadability_lineage(
                model_id=model_id,
                runtime_visibility_gate=visibility_gate,
                lineage_records=app.state.loadability_lineage_records,
            )
        )

    @app.get("/v1/runtime/nonresident-model-admission-policy")
    def runtime_nonresident_model_admission_policy(
        model_id: str | None = None,
        request_context_class: str | None = None,
        known_loadable_model_ids: list[str] | None = Query(default=None),
    ) -> dict[str, Any]:
        loadability_lineage = _build_loadability_lineage_for_request(model_id)
        return nonresident_model_admission_policy_to_dict(
            build_nonresident_model_admission_policy(
                runtime_status=runtime.status_dict(),
                model_id=model_id,
                known_loadable_model_ids=known_loadable_model_ids,
                request_context_class=request_context_class,
                abort_recovery_snapshot=runtime.abort_recovery.snapshot(),
                loadability_lineage=loadability_lineage,
            )
        )

    @app.get("/v1/runtime/memory-pressure-eviction-policy")
    def runtime_memory_pressure_eviction_policy(
        protect_active: bool = True,
    ) -> dict[str, Any]:
        return memory_pressure_eviction_policy_to_dict(
            build_memory_pressure_eviction_policy(
                runtime_status=runtime.status_dict(),
                abort_recovery_snapshot=runtime.abort_recovery.snapshot(),
                protect_active=protect_active,
            )
        )

    @app.post("/v1/runtime/memory-pressure-eviction")
    def runtime_memory_pressure_eviction(
        payload: MemoryPressureEvictionRequest | None = None,
    ) -> dict[str, Any]:
        request = payload if payload is not None else MemoryPressureEvictionRequest()
        result = runtime.execute_memory_pressure_eviction(
            protect_active=request.protect_active,
        )
        records = app.state.loadability_lineage_records
        victim = result.get("selected_victim") if isinstance(result, dict) else None
        if (
            isinstance(result, dict)
            and result.get("executed")
            and isinstance(victim, dict)
            and records is not None
        ):
            snapshot = (
                runtime.inventory.snapshot()
                if hasattr(runtime, "inventory")
                and hasattr(runtime.inventory, "snapshot")
                else None
            )
            visibility_gate = build_runtime_model_visibility(
                snapshot,
                models_root=app.state.visibility_models_root,
                registry=app.state.visibility_registry,
            )
            result["loadability_lineage_after"] = nonresident_loadability_lineage_to_dict(
                build_nonresident_loadability_lineage(
                    model_id=str(victim.get("model_id")),
                    runtime_visibility_gate=visibility_gate,
                    lineage_records=records,
                )
            )
        return result

    @app.get("/v1/runtime/reclaim-barrier-event")
    def runtime_reclaim_barrier_event() -> dict[str, Any]:
        return settle_barrier_event_to_dict(
            build_settle_barrier_event(runtime_status=runtime.status_dict())
        )

    @app.get("/v1/runtime/termination-recovery-policy")
    def runtime_termination_recovery_policy() -> dict[str, Any]:
        return termination_recovery_policy_to_dict(
            build_termination_recovery_policy(
                runtime_status=runtime.status_dict(),
                abort_recovery_snapshot=runtime.abort_recovery.snapshot(),
            )
        )

    @app.get("/v1/runtime/comparative-evidence")
    def runtime_comparative_evidence() -> JSONResponse:
        ledger = app.state.comparative_evidence_ledger
        if ledger is None:
            return JSONResponse(
                status_code=503,
                content=comparative_evidence_still_blocked_payload(
                    missing_signal="comparative_evidence_ledger_not_connected",
                    ledger_path=None,
                ),
            )
        latest = ledger.latest()
        if latest is None:
            return JSONResponse(
                status_code=503,
                content=comparative_evidence_still_blocked_payload(
                    missing_signal="no_comparative_evidence_record_appended",
                    ledger_path=str(ledger.path),
                ),
            )
        return JSONResponse(status_code=200, content=latest)

    @app.get("/v1/runtime/comparative-evidence/history")
    def runtime_comparative_evidence_history() -> JSONResponse:
        ledger = app.state.comparative_evidence_ledger
        if ledger is None:
            return JSONResponse(
                status_code=503,
                content=comparative_evidence_still_blocked_payload(
                    missing_signal="comparative_evidence_ledger_not_connected",
                    ledger_path=None,
                ),
            )
        records = ledger.history()
        if not records:
            return JSONResponse(
                status_code=503,
                content=comparative_evidence_still_blocked_payload(
                    missing_signal="no_comparative_evidence_record_appended",
                    ledger_path=str(ledger.path),
                ),
            )
        return JSONResponse(
            status_code=200,
            content=comparative_evidence_history_envelope(
                records=records,
                ledger_status="available",
            ),
        )

    @app.get("/v1/runtime/model-release-candidates")
    def runtime_model_release_candidates() -> JSONResponse:
        ledger = app.state.model_release_candidate_ledger
        if ledger is None:
            return JSONResponse(
                status_code=503,
                content=model_release_candidate_still_blocked_payload(
                    missing_signal="model_release_candidate_ledger_not_connected",
                    ledger_path=None,
                ),
            )
        latest = ledger.latest()
        if latest is None:
            return JSONResponse(
                status_code=503,
                content=model_release_candidate_still_blocked_payload(
                    missing_signal="no_model_release_candidate_record_appended",
                    ledger_path=str(ledger.path),
                ),
            )
        return JSONResponse(status_code=200, content=latest)

    @app.get("/v1/runtime/model-release-candidates/history")
    def runtime_model_release_candidates_history() -> JSONResponse:
        ledger = app.state.model_release_candidate_ledger
        if ledger is None:
            return JSONResponse(
                status_code=503,
                content=model_release_candidate_still_blocked_payload(
                    missing_signal="model_release_candidate_ledger_not_connected",
                    ledger_path=None,
                ),
            )
        records = ledger.history()
        if not records:
            return JSONResponse(
                status_code=503,
                content=model_release_candidate_still_blocked_payload(
                    missing_signal="no_model_release_candidate_record_appended",
                    ledger_path=str(ledger.path),
                ),
            )
        return JSONResponse(
            status_code=200,
            content=model_release_candidate_history_envelope(
                records=records,
                ledger_status="available",
            ),
        )

    @app.post("/v1/runtime/restart")
    def restart_model(payload: RestartRequest) -> dict[str, Any]:
        result = runtime.restart_model(payload.model_id)
        return _result_to_dict(result)

    @app.post("/v1/unload")
    def unload_model(payload: UnloadRequest, request: Request) -> JSONResponse:
        result = runtime.unload_model(payload.model_id)
        return _native_runtime_response(result, request=request)

    @app.get("/metrics")
    def metrics_endpoint() -> Any:
        """Render a Prometheus text-exposition snapshot of runtime gate state.

        Each scrape produces a fresh snapshot from the current
        ``runtime.status_dict()``; there is no background sampler and no
        cache. Counter metrics carry the ``_total`` suffix per Prometheus
        convention. Gauges do not. Each metric block emits a ``# HELP``
        and ``# TYPE`` line per the C-4 ``MetricsSnapshotExporter``
        contract.

        The route is **not** wrapped by the unified error envelope:
        Prometheus scrapers expect plain text, not a JSON envelope. If
        the exporter itself raises during render, the route returns a
        literal ``# owlmlx_metrics_render_error 1`` text line with HTTP
        200 so the scrape does not fail outright.
        """

        # Function-local import so the top-level import block is not
        # broadened beyond ``MetricsSnapshotExporter``. ``Response`` is
        # the plain-text base class shipped by Starlette / re-exported
        # by FastAPI; FastAPI already depends on Starlette.
        from starlette.responses import Response

        try:
            status = runtime.status_dict()
            gate_status = status.get("generation_gate") or {}
            backend_section = status.get("backend") or {}
            backend_detail = backend_section.get("detail") or {}
            native_admission_snapshot = backend_detail.get("admission")
            if not isinstance(gate_status, dict):
                gate_status = {}
            if native_admission_snapshot is not None and not isinstance(
                native_admission_snapshot, dict
            ):
                native_admission_snapshot = None
            text = _metrics_exporter.render_prometheus_text(
                gate_status=gate_status,
                native_admission_snapshot=native_admission_snapshot,
            )
        except Exception:  # pragma: no cover - defensive guard
            # Prometheus scrapers expect a 200 with text content; emit a
            # diagnostic counter line so the operator sees the failure
            # in their dashboard rather than a hard scrape failure.
            text = "# owlmlx_metrics_render_error 1\n"
        return Response(
            content=text,
            media_type="text/plain; version=0.0.4",
        )

    return app


def create_fake_app() -> FastAPI:
    """Create Runtime-0 app backed by FakeBackend.

    Honors ``OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH`` so the live uvicorn
    factory mode can mount the comparative-evidence surface against an
    operator-managed ledger without touching ``create_fake_app`` arguments.
    """

    import os

    return create_app(
        RuntimeKernel(FakeBackend()),
        comparative_evidence_ledger_path=os.environ.get(
            "OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH"
        ),
        model_release_candidate_ledger_path=os.environ.get(
            "OWLMLX_MODEL_RELEASE_CANDIDATE_LEDGER_PATH"
        ),
    )


def create_app_for_backend(backend: RuntimeBackend) -> FastAPI:
    """Create Runtime-0 app for a provided backend adapter."""

    return create_app(RuntimeKernel(backend))
