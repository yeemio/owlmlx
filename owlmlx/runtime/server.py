"""Minimal HTTP entry for owlmlx runtime."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict
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
from owlmlx.reclaim_barrier_event import (
    build_reclaim_barrier_event,
    reclaim_barrier_event_to_dict,
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
    MONITOR_EVENT_SURFACE,
    RuntimeTestRunRegistry,
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
from .types import ChatTurn


class LoadRequest(BaseModel):
    """HTTP request body for model load."""

    model_id: str = Field(min_length=1)
    memory_gb: float | None = Field(default=None, ge=0)


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
    """

    runtime = kernel if kernel is not None else RuntimeKernel(FakeBackend())
    app = FastAPI(title="owlmlx Runtime", version="0.0.0-runtime7")
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
    app.state.runtime_test_runs = {}

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
    def load_model(payload: LoadRequest) -> dict[str, Any]:
        result = runtime.load_model(
            payload.model_id,
            memory_gb=payload.memory_gb,
        )
        return _result_to_dict(result)

    @app.post("/v1/generate")
    async def generate(payload: GenerateRequest) -> dict[str, Any]:
        result = await runtime.generate(
            payload.prompt,
            model_id=payload.model_id,
            **payload.params,
        )
        return _result_to_dict(result)

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
    async def chat_completions(payload: ChatCompletionRequest):
        target_model = payload.model or runtime.active_model_id
        profile = _openai_profile_for_model(target_model)
        completion_id = f"chatcmpl-{uuid.uuid4().hex}"
        request_id = f"req_{uuid.uuid4().hex}"
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
                        visible_text, policy_payload = _openai_visible_text_for_policy(
                            "".join(buffered_text),
                            finish_reason=finish_reason,
                            policy=reasoning_policy,
                        )
                        if visible_text:
                            chunk = {
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
                            yield f"data: {json.dumps(chunk)}\n\n"
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
                            pt = int(prompt_tokens or 0)
                            ct = int(completion_tokens or 0)
                            done_chunk["usage"] = {
                                "prompt_tokens": pt,
                                "completion_tokens": ct,
                                "total_tokens": pt + ct,
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
    async def anthropic_messages(payload: AnthropicMessagesRequest):
        target_model = payload.model or runtime.active_model_id
        message_id = f"msg_{uuid.uuid4().hex[:24]}"
        request_id = f"req_{uuid.uuid4().hex}"
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
    async def completions(payload: CompletionRequest):
        target_model = payload.model or runtime.active_model_id
        completion_id = f"cmpl-{uuid.uuid4().hex}"
        request_id = f"req_{uuid.uuid4().hex}"
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
    def openai_models():
        request_id = f"req_{uuid.uuid4().hex}"
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
        (
            records,
            ledger_status,
            ledger_path,
        ) = _model_release_candidate_records_and_status()
        test_run_ledger_status, test_run_ledger_path = _runtime_test_run_ledger_status()
        return build_monitor_snapshot(
            runtime_status=runtime.status_dict(),
            runtime_url=_request_runtime_url(request),
            visibility_contract=_runtime_model_visibility_contract(),
            model_load_admission=_runtime_model_load_admission_contract(),
            model_release_candidate_records=records,
            model_release_candidate_ledger_status=ledger_status,
            model_release_candidate_ledger_path=ledger_path,
            test_runs=_runtime_test_run_records(),
            test_run_audit_ledger_status=test_run_ledger_status,
            test_run_audit_ledger_path=test_run_ledger_path,
        )

    @app.get("/v1/runtime/monitor/events")
    def runtime_monitor_events() -> JSONResponse:
        return JSONResponse(
            status_code=501,
            content=unsupported_operation_payload(
                surface=MONITOR_EVENT_SURFACE,
                unsupported_feature="monitor_sse_stream",
                reason="monitor_event_stream_worker_not_implemented",
            ),
        )

    @app.post("/v1/runtime/test-runs/preflight")
    def runtime_test_runs_preflight(
        payload: TestRunRequest,
        request: Request,
    ) -> dict[str, Any]:
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
    def runtime_test_runs_launch(
        payload: TestRunRequest,
        request: Request,
    ) -> JSONResponse:
        preflight = build_test_run_preflight(
            request_payload=payload.model_dump(),
            runtime_status=runtime.status_dict(),
            runtime_url=_request_runtime_url(request),
            visibility_contract=_runtime_model_visibility_contract(),
            model_load_admission=_runtime_model_load_admission_contract(payload.model_id),
            test_runs=_runtime_test_run_records(),
        )
        registry = app.state.runtime_test_run_registry
        audit_row = None
        if registry is not None:
            audit_row = registry.append_unsupported_launch(
                request_payload=payload.model_dump(),
                preflight=preflight,
            )
        response = unsupported_operation_payload(
            surface=TEST_RUN_LAUNCH_SURFACE,
            unsupported_feature="audited_live_launch_worker",
            reason="test_run_launch_worker_not_implemented",
        )
        response["launch_decision"] = "unsupported"
        response["preflight"] = preflight
        response["audit_ledger_status"] = "available" if registry is not None else "not_connected"
        response["audit_ledger_path"] = str(registry.path) if registry is not None else None
        if audit_row is not None:
            response["run_id"] = audit_row["run_id"]
            response["run"] = audit_row
        return JSONResponse(status_code=501, content=response)

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
        known_run_ids = {
            str(run.get("run_id"))
            for run in _runtime_test_run_records()
            if run.get("run_id")
        }
        if run_id not in known_run_ids:
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
        return JSONResponse(
            status_code=501,
            content=unsupported_operation_payload(
                surface=TEST_RUN_ABORT_SURFACE,
                unsupported_feature="audited_abort_worker",
                reason="test_run_abort_worker_not_implemented",
                run_id=run_id,
            ),
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
        return reclaim_barrier_event_to_dict(
            build_reclaim_barrier_event(runtime_status=runtime.status_dict())
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
    def unload_model(payload: UnloadRequest) -> dict[str, Any]:
        result = runtime.unload_model(payload.model_id)
        return _result_to_dict(result)

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
