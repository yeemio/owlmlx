"""Minimal HTTP entry for owlmlx runtime."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from starlette.responses import StreamingResponse

from owlmlx.runtime_model_visibility import (
    RegisteredRuntimeVisibleModel,
    build_runtime_model_visibility,
    derive_runtime_model_visibility_contract,
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
from owlmlx.request_context_length_truth import (
    build_request_context_length_truth,
    request_context_length_truth_to_dict,
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
    stream: bool = False


class ChatCompletionRequest(BaseModel):
    model: str | None = Field(default=None, min_length=1)
    messages: list[ChatMessage]
    max_tokens: int | None = Field(default=None, ge=1)
    temperature: float | None = None
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


def _result_to_dict(result: Any) -> dict[str, Any]:
    data = asdict(result)
    error = data.get("error_code")
    if error is not None and hasattr(error, "value"):
        data["error_code"] = error.value
    return data


def _messages_to_turns(messages: list[ChatMessage]) -> list[ChatTurn]:
    return [ChatTurn(role=message.role, content=message.content) for message in messages]


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
    payload = {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
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
) -> FastAPI:
    """Create a minimal owlmlx runtime HTTP app.

    `loadability_lineage_records` is the runtime-owned non-resident
    loadability lineage registry. It is connected at app construction time and
    consumed by the nonresident-loadability-lineage and
    nonresident-model-admission-policy endpoints. It is intentionally not a
    per-request hint.
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
        completion_id = f"chatcmpl-{uuid.uuid4().hex}"
        request_id = f"req_{uuid.uuid4().hex}"
        messages = _messages_to_turns(payload.messages)
        params: dict[str, Any] = {}
        if payload.max_tokens is not None:
            params["max_tokens"] = payload.max_tokens
        if payload.temperature is not None:
            params["temperature"] = payload.temperature

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
            return JSONResponse(
                headers={"x-request-id": request_id},
                content=_openai_response_dict(
                    completion_id=completion_id,
                    model=target_model or "unknown",
                    text=result.text,
                    finish_reason="stop",
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                ),
            )

        async def sse_source():
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
        return derive_runtime_model_visibility_contract(
            runtime.inventory_snapshot(),
            models_root=visibility_models_root,
            registry=visibility_registry,
        )

    @app.get("/v1/runtime/status")
    def runtime_status() -> dict[str, Any]:
        return runtime.status_dict()

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
    """Create Runtime-0 app backed by FakeBackend."""

    return create_app(RuntimeKernel(FakeBackend()))


def create_app_for_backend(backend: RuntimeBackend) -> FastAPI:
    """Create Runtime-0 app for a provided backend adapter."""

    return create_app(RuntimeKernel(backend))
