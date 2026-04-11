"""Runtime backend contracts and fake backend implementation."""

from __future__ import annotations

import time
from typing import Protocol, runtime_checkable

from .types import (
    BackendStatus,
    GenerateResult,
    LoadResult,
    LoadedModelInfo,
    RuntimeErrorCode,
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

    def unload(self, model_id: str) -> UnloadResult:
        """Unload a model from the backend."""

    def status(self) -> BackendStatus:
        """Return backend health and loaded model inventory."""


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
        max_tokens = kwargs.get("max_tokens")
        token_note = f" max_tokens={max_tokens}" if max_tokens is not None else ""
        return GenerateResult(
            ok=True,
            message="generated",
            model_id=model_id,
            text=f"{prompt}{self.completion_suffix}{token_note}",
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(self.completion_suffix.split()),
        )

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
