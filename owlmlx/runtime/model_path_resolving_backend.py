"""Model-id preserving path resolver for runtime backends."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from typing import Any

from .backends import RuntimeBackend
from .types import (
    BackendStatus,
    GenerateResult,
    LoadResult,
    LoadedModelInfo,
    StreamEvent,
    UnloadResult,
)


class ModelPathResolvingBackend:
    """Adapt public model ids to local load paths while preserving public ids.

    The technical-preview subprocess backend already has a built-in
    ``model_path_resolver``. Native backend does not, so this wrapper keeps
    consumer-facing model ids stable for HTTP clients while loading local model
    directories underneath.
    """

    def __init__(
        self,
        inner: RuntimeBackend,
        *,
        model_path_resolver: Callable[[str], str],
    ) -> None:
        self.inner = inner
        self.model_path_resolver = model_path_resolver
        self._public_to_runner: dict[str, str] = {}
        self._runner_to_public: dict[str, str] = {}

    @property
    def name(self) -> str:
        return self.inner.name

    def _runner_id_for(self, model_id: str) -> str:
        return self._public_to_runner.get(model_id) or str(
            self.model_path_resolver(model_id)
        )

    def _public_id_for(self, runner_model_id: str) -> str:
        return self._runner_to_public.get(runner_model_id, runner_model_id)

    def _map_loaded_model(self, model: LoadedModelInfo | None) -> LoadedModelInfo | None:
        if model is None:
            return None
        return replace(model, model_id=self._public_id_for(model.model_id))

    def load(self, model_id: str, *, memory_gb: float | None = None) -> LoadResult:
        runner_model_id = str(self.model_path_resolver(model_id))
        result = self.inner.load(runner_model_id, memory_gb=memory_gb)
        if result.ok:
            self._public_to_runner[model_id] = runner_model_id
            self._runner_to_public[runner_model_id] = model_id
        return replace(result, model=self._map_loaded_model(result.model))

    def generate(self, model_id: str, prompt: str, **kwargs: object) -> GenerateResult:
        runner_model_id = self._runner_id_for(model_id)
        result = self.inner.generate(runner_model_id, prompt, **kwargs)
        return replace(result, model_id=model_id if result.model_id is not None else None)

    def generate_messages(
        self,
        model_id: str,
        messages: list[Any],
        **kwargs: object,
    ) -> GenerateResult:
        runner_model_id = self._runner_id_for(model_id)
        result = self.inner.generate_messages(runner_model_id, messages, **kwargs)
        return replace(result, model_id=model_id if result.model_id is not None else None)

    def stream_generate(
        self,
        model_id: str,
        prompt: str,
        **kwargs: object,
    ) -> Iterable[StreamEvent]:
        runner_model_id = self._runner_id_for(model_id)
        for event in self.inner.stream_generate(runner_model_id, prompt, **kwargs):
            yield replace(event, model_id=model_id if event.model_id is not None else None)

    def stream_generate_messages(
        self,
        model_id: str,
        messages: list[Any],
        **kwargs: object,
    ) -> Iterable[StreamEvent]:
        runner_model_id = self._runner_id_for(model_id)
        for event in self.inner.stream_generate_messages(runner_model_id, messages, **kwargs):
            yield replace(event, model_id=model_id if event.model_id is not None else None)

    def unload(self, model_id: str) -> UnloadResult:
        runner_model_id = self._runner_id_for(model_id)
        result = self.inner.unload(runner_model_id)
        if result.ok:
            self._public_to_runner.pop(model_id, None)
            self._runner_to_public.pop(runner_model_id, None)
        return replace(result, model_id=model_id if result.model_id is not None else None)

    def status(self) -> BackendStatus:
        status = self.inner.status()
        return replace(
            status,
            loaded_models=tuple(
                replace(model, model_id=self._public_id_for(model.model_id))
                for model in status.loaded_models
            ),
        )
