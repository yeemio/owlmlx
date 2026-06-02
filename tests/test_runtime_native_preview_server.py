from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.runtime import FakeBackend
from owlmlx.runtime.model_path_resolving_backend import ModelPathResolvingBackend
from owlmlx.runtime.native_preview import create_native_preview_app
from owlmlx.runtime.technical_preview import model_path_resolver


def test_resolving_backend_preserves_public_id_while_loading_local_path(
    tmp_path: Path,
) -> None:
    local_model_dir = tmp_path / "demo-model"
    local_model_dir.mkdir()
    backend = ModelPathResolvingBackend(
        FakeBackend(),
        model_path_resolver=model_path_resolver(tmp_path),
    )

    loaded = backend.load("demo-model", memory_gb=1.0)
    generated = backend.generate("demo-model", "hello", max_tokens=2)
    stream_events = list(backend.stream_generate("demo-model", "hello", max_tokens=2))
    status = backend.status()

    assert loaded.ok is True
    assert loaded.model is not None
    assert loaded.model.model_id == "demo-model"
    assert generated.ok is True
    assert generated.model_id == "demo-model"
    assert stream_events
    assert {event.model_id for event in stream_events} == {"demo-model"}
    assert status.loaded_models[0].model_id == "demo-model"
    assert backend.inner.status().loaded_models[0].model_id == str(local_model_dir)
    unloaded = backend.unload("demo-model")
    assert unloaded.ok is True
    assert unloaded.model_id == "demo-model"


def test_native_preview_factory_exposes_native_backend_and_visibility(
    tmp_path: Path,
    monkeypatch,
) -> None:
    model_dir = tmp_path / "gemma-4-31B-it"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("OWLMLX_MODELS_ROOT", str(tmp_path))
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED", "1")

    client = TestClient(create_native_preview_app())

    health = client.get("/healthz")
    visibility = client.get("/v1/runtime/model-visibility")
    session_cache = client.get("/v1/runtime/session-kv-cache")

    assert health.status_code == 200
    assert health.json()["backend_name"] == "mlx-native"
    assert visibility.status_code == 200
    assert "gemma-4-31B-it" in visibility.json()["visible_model_ids"]
    assert session_cache.status_code == 200
    assert session_cache.json()["enabled"] is True
