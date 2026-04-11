"""Minimal HTTP entry for owlmlx Runtime-0."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI

from .backends import FakeBackend, RuntimeBackend
from .kernel import RuntimeKernel


def _result_to_dict(result: Any) -> dict[str, Any]:
    data = asdict(result)
    error = data.get("error_code")
    if error is not None and hasattr(error, "value"):
        data["error_code"] = error.value
    return data


def create_app(kernel: RuntimeKernel | None = None) -> FastAPI:
    """Create a minimal owlmlx runtime HTTP app."""

    runtime = kernel if kernel is not None else RuntimeKernel(FakeBackend())
    app = FastAPI(title="owlmlx Runtime", version="0.0.0-runtime0")
    app.state.kernel = runtime

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        status = runtime.status_dict()
        return {
            "ok": status["backend"]["healthy"],
            "readiness": status["health"]["readiness"],
            "active_model_id": status["active_model_id"],
            "model_count": status["inventory"]["model_count"],
        }

    @app.post("/v1/load")
    def load_model(payload: dict[str, Any]) -> dict[str, Any]:
        result = runtime.load_model(
            str(payload["model_id"]),
            memory_gb=payload.get("memory_gb"),
        )
        return _result_to_dict(result)

    @app.post("/v1/generate")
    async def generate(payload: dict[str, Any]) -> dict[str, Any]:
        result = await runtime.generate(
            str(payload.get("prompt", "")),
            model_id=payload.get("model_id"),
            **dict(payload.get("params") or {}),
        )
        return _result_to_dict(result)

    @app.get("/v1/models")
    def models() -> dict[str, Any]:
        status = runtime.status_dict()
        return {
            "active_model_id": status["active_model_id"],
            "inventory": status["inventory"],
            "budget": status["budget"],
            "backend": status["backend"],
        }

    @app.post("/v1/unload")
    def unload_model(payload: dict[str, Any]) -> dict[str, Any]:
        result = runtime.unload_model(str(payload["model_id"]))
        return _result_to_dict(result)

    return app


def create_fake_app() -> FastAPI:
    """Create Runtime-0 app backed by FakeBackend."""

    return create_app(RuntimeKernel(FakeBackend()))


def create_app_for_backend(backend: RuntimeBackend) -> FastAPI:
    """Create Runtime-0 app for a provided backend adapter."""

    return create_app(RuntimeKernel(backend))
