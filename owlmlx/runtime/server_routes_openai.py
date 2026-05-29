"""OpenAI and Anthropic compatibility routes for the owlmlx runtime server."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse, StreamingResponse

from owlmlx.model_profile import ModelProfile, resolve_model_profile
from owlmlx.reasoning_trace_policy import apply_reasoning_trace_policy
from owlmlx.runtime_model_visibility import derive_runtime_model_visibility_contract

from .kernel import RuntimeKernel
from .types import ChatTurn


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
    response_format: dict[str, Any] | None = None
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


def _grammar_from_openai_payload(payload: "ChatCompletionRequest") -> dict[str, Any] | None:
    """Translate an OpenAI-style structured-output request into a backend grammar spec.

    Two inputs, in priority order:
      * ``response_format`` (OpenAI standard):
        ``{"type": "json_schema", "json_schema": {"schema": {...}}}`` →
        ``{"kind": "json_schema", "schema": {...}}``.
      * ``extra_body["grammar"]``: a backend grammar spec passed through verbatim
        (escape hatch for structural_tag or other kinds the OpenAI shape can't
        express).

    Returns None when neither is present. The resulting spec rides the existing
    kwargs path: route params → kernel.generate_messages(**params) → backend →
    child runner, where the xgrammar matcher is built (see F-4.2a).
    """
    rf = payload.response_format
    if isinstance(rf, dict) and rf.get("type") == "json_schema":
        json_schema = rf.get("json_schema")
        if isinstance(json_schema, dict):
            schema = json_schema.get("schema")
            if isinstance(schema, dict):
                return {"kind": "json_schema", "schema": schema}
    if isinstance(payload.extra_body, dict):
        grammar = payload.extra_body.get("grammar")
        if isinstance(grammar, dict):
            return grammar
    return None


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


def register_openai_compat_routes(
    app: FastAPI,
    *,
    runtime: RuntimeKernel,
    visibility_models_root: str | None,
    visibility_registry: list[Any] | tuple[Any, ...] | None,
    session_id_from_request: Callable[[Request], str | None],
) -> None:
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
        grammar_spec = _grammar_from_openai_payload(payload)
        if grammar_spec is not None:
            params["grammar"] = grammar_spec
        reasoning_policy = _openai_reasoning_trace_policy(payload, profile=profile)
        session_id = session_id_from_request(request)
        if session_id is not None:
            params["session_id"] = session_id

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
        session_id = session_id_from_request(request)
        if session_id is not None:
            params["session_id"] = session_id

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
        session_id = session_id_from_request(request)
        if session_id is not None:
            params["session_id"] = session_id

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
