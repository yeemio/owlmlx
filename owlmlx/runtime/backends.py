"""Runtime backend contracts and fake backend implementation."""

from __future__ import annotations

import time
from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from .types import (
    BackendStatus,
    ChatTurn,
    GenerateResult,
    LoadResult,
    LoadedModelInfo,
    RuntimeErrorCode,
    StreamEvent,
    UnloadResult,
)


@runtime_checkable
class RuntimeBackend(Protocol):
    """Backend adapter boundary consumed by RuntimeKernel."""

    name: str

    def load(self, model_id: str, *, memory_gb: float | None = None) -> LoadResult:
        """Load a model into the backend."""

    def generate(self, model_id: str, prompt: str, **kwargs: object) -> GenerateResult:
        """Generate text from an already-loaded model."""

    def generate_messages(
        self,
        model_id: str,
        messages: list[ChatTurn],
        **kwargs: object,
    ) -> GenerateResult:
        """Generate text from structured chat messages."""

    def stream_generate(
        self,
        model_id: str,
        prompt: str,
        **kwargs: object,
    ) -> Iterable[StreamEvent]:
        """Generate a streamed response from an already-loaded model."""

    def stream_generate_messages(
        self,
        model_id: str,
        messages: list[ChatTurn],
        **kwargs: object,
    ) -> Iterable[StreamEvent]:
        """Generate a streamed response from structured chat messages."""

    def unload(self, model_id: str) -> UnloadResult:
        """Unload a model from the backend."""

    def status(self) -> BackendStatus:
        """Return backend health and loaded model inventory."""


def render_chat_messages(messages: list[ChatTurn]) -> str:
    """Fallback chat rendering for backends without tokenizer templating."""

    return "\n".join(f"{message.role}: {message.content}" for message in messages)


class FakeBackend:
    """Deterministic backend for RuntimeKernel and HTTP tests."""

    name = "fake"

    def __init__(
        self,
        *,
        healthy: bool = True,
        default_memory_gb: float = 1.0,
        completion_suffix: str = " :: fake completion",
        generate_delay_s: float = 0.0,
    ) -> None:
        self.healthy = healthy
        self.default_memory_gb = default_memory_gb
        self.completion_suffix = completion_suffix
        self.generate_delay_s = generate_delay_s
        self._loaded: dict[str, LoadedModelInfo] = {}

    def load(self, model_id: str, *, memory_gb: float | None = None) -> LoadResult:
        if not self.healthy:
            return LoadResult(
                ok=False,
                message="backend is unhealthy",
                error_code=RuntimeErrorCode.backend_error,
            )
        if model_id in self._loaded:
            return LoadResult(
                ok=False,
                message=f"model already loaded: {model_id}",
                error_code=RuntimeErrorCode.model_already_loaded,
                model=self._loaded[model_id],
            )
        model = LoadedModelInfo(
            model_id=model_id,
            memory_gb=memory_gb if memory_gb is not None else self.default_memory_gb,
            backend=self.name,
            loaded_at=time.time(),
        )
        self._loaded[model_id] = model
        return LoadResult(ok=True, message=f"loaded {model_id}", model=model)

    def generate(self, model_id: str, prompt: str, **kwargs: object) -> GenerateResult:
        if not self.healthy:
            return GenerateResult(
                ok=False,
                message="backend is unhealthy",
                error_code=RuntimeErrorCode.backend_error,
                model_id=model_id,
            )
        if model_id not in self._loaded:
            return GenerateResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
            )
        if self.generate_delay_s > 0:
            time.sleep(self.generate_delay_s)
        if "[tool_result:" in prompt:
            return GenerateResult(
                ok=True,
                message="generated final response after tool_result",
                model_id=model_id,
                text=f"{prompt}{self.completion_suffix}",
                finish_reason="stop",
                prompt_tokens=len(prompt.split()),
                completion_tokens=len(self.completion_suffix.split()),
            )
        tools = kwargs.get("tools")
        tool_choice = kwargs.get("tool_choice")
        if isinstance(tools, list) and tools and tool_choice != "none":
            first = tools[0]
            if isinstance(first, dict):
                name = str(first.get("name") or "tool")
                tool_use_id = "toolu_fake_001"
                return GenerateResult(
                    ok=True,
                    message="generated tool_use",
                    model_id=model_id,
                    text="",
                    finish_reason="tool_use",
                    prompt_tokens=len(prompt.split()),
                    completion_tokens=0,
                    detail={
                        "tool_uses": [
                            {
                                "id": tool_use_id,
                                "name": name,
                                "input": {"prompt": prompt},
                            }
                        ]
                    },
                )
        max_tokens = kwargs.get("max_tokens")
        token_note = f" max_tokens={max_tokens}" if max_tokens is not None else ""
        return GenerateResult(
            ok=True,
            message="generated",
            model_id=model_id,
            text=f"{prompt}{self.completion_suffix}{token_note}",
            finish_reason="stop",
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(self.completion_suffix.split()),
        )

    def generate_messages(
        self,
        model_id: str,
        messages: list[ChatTurn],
        **kwargs: object,
    ) -> GenerateResult:
        return self.generate(model_id, render_chat_messages(messages), **kwargs)

    def stream_generate(self, model_id: str, prompt: str, **kwargs: object) -> list[StreamEvent]:
        result = self.generate(model_id, prompt, **kwargs)
        if not result.ok:
            return [
                StreamEvent(
                    event="error",
                    model_id=model_id,
                    error_code=result.error_code,
                    detail={"message": result.message, **result.detail},
                )
            ]
        tool_uses = result.detail.get("tool_uses")
        if isinstance(tool_uses, list) and tool_uses:
            tool = tool_uses[0]
            return [
                StreamEvent(
                    event="tool_use",
                    model_id=model_id,
                    finish_reason="tool_use",
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=0,
                    detail={"tool_use": tool},
                ),
                StreamEvent(
                    event="done",
                    model_id=model_id,
                    finish_reason="tool_use",
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=0,
                    detail={"tool_use": tool},
                ),
            ]
        words = result.text.split()
        if not words:
            return [
                StreamEvent(
                    event="done",
                    model_id=model_id,
                    text=result.text,
                    finish_reason="stop",
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                )
            ]
        events: list[StreamEvent] = []
        assembled: list[str] = []
        for idx, word in enumerate(words, start=1):
            assembled.append(word)
            events.append(
                StreamEvent(
                    event="token",
                    model_id=model_id,
                    text=(" ".join(assembled) + (" " if idx < len(words) else "")),
                    sequence=idx,
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=idx,
                    finish_reason=result.finish_reason,
                )
            )
        events.append(
            StreamEvent(
                event="done",
                model_id=model_id,
                text=result.text,
                sequence=len(words),
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                finish_reason=result.finish_reason or "stop",
            )
        )
        return events

    def stream_generate_messages(
        self,
        model_id: str,
        messages: list[ChatTurn],
        **kwargs: object,
    ) -> list[StreamEvent]:
        return self.stream_generate(model_id, render_chat_messages(messages), **kwargs)

    def unload(self, model_id: str) -> UnloadResult:
        model = self._loaded.pop(model_id, None)
        if model is None:
            return UnloadResult(
                ok=False,
                message=f"model not loaded: {model_id}",
                error_code=RuntimeErrorCode.model_not_loaded,
                model_id=model_id,
            )
        return UnloadResult(
            ok=True,
            message=f"unloaded {model_id}",
            model_id=model_id,
            freed_gb=model.memory_gb,
        )

    def status(self) -> BackendStatus:
        return BackendStatus(
            backend_name=self.name,
            healthy=self.healthy,
            loaded_models=tuple(self._loaded.values()),
            detail={
                "model_count": len(self._loaded),
                "default_memory_gb": self.default_memory_gb,
            },
        )
