"""Minimal HTTP entry for owlmlx runtime."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from .backends import FakeBackend, RuntimeBackend
from .kernel import RuntimeKernel


class LoadRequest(BaseModel):
    """HTTP request body for model load."""

    model_id: str = Field(min_length=1)
    memory_gb: float | None = Field(default=None, ge=0)


class GenerateRequest(BaseModel):
    """HTTP request body for generation."""

    prompt: str
    model_id: str | None = Field(default=None, min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


class UnloadRequest(BaseModel):
    """HTTP request body for model unload."""

    model_id: str = Field(min_length=1)


class RestartRequest(BaseModel):
    """HTTP request body for runtime restart of a loaded model."""

    model_id: str = Field(min_length=1)


def _result_to_dict(result: Any) -> dict[str, Any]:
    data = asdict(result)
    error = data.get("error_code")
    if error is not None and hasattr(error, "value"):
        data["error_code"] = error.value
    return data


def create_app(kernel: RuntimeKernel | None = None) -> FastAPI:
    """Create a minimal owlmlx runtime HTTP app."""

    runtime = kernel if kernel is not None else RuntimeKernel(FakeBackend())
    app = FastAPI(title="owlmlx Runtime", version="0.0.0-runtime3")
    app.state.kernel = runtime

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        status = runtime.status_dict()
        backend_detail = status["backend"]["detail"]
        return {
            "ok": status["backend"]["healthy"],
            "readiness": status["health"]["readiness"],
            "active_model_id": status["active_model_id"],
            "model_count": status["inventory"]["model_count"],
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

    @app.get("/v1/models")
    def models() -> dict[str, Any]:
        status = runtime.status_dict()
        return {
            "active_model_id": status["active_model_id"],
            "inventory": status["inventory"],
            "budget": status["budget"],
            "health": status["health"],
            "generation_gate": status["generation_gate"],
            "backend": status["backend"],
        }

    @app.get("/v1/runtime/status")
    def runtime_status() -> dict[str, Any]:
        return runtime.status_dict()

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
