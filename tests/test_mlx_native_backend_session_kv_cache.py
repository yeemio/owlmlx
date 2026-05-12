"""Native backend wiring for experimental session KV cache reuse."""

from __future__ import annotations

import importlib
import sys
import types

import pytest


def _build_fake_mlx_lm_with_observable_cache() -> types.ModuleType:
    fake = types.ModuleType("mlx_lm")
    models = types.ModuleType("mlx_lm.models")
    cache_mod = types.ModuleType("mlx_lm.models.cache")
    created_caches: list[list[object]] = []
    seen_prompt_caches: list[object | None] = []

    def make_prompt_cache(model: object) -> list[object]:
        cache = [object()]
        created_caches.append(cache)
        return cache

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    def fake_generate(
        model,
        tokenizer,
        *,
        prompt,
        max_tokens,
        prompt_cache=None,
    ) -> str:
        seen_prompt_caches.append(prompt_cache)
        return f"generated:{prompt}:{max_tokens}"

    cache_mod.make_prompt_cache = make_prompt_cache  # type: ignore[attr-defined]
    models.cache = cache_mod  # type: ignore[attr-defined]
    fake.models = models  # type: ignore[attr-defined]
    fake.load = fake_load  # type: ignore[attr-defined]
    fake.generate = fake_generate  # type: ignore[attr-defined]
    fake._created_caches = created_caches  # type: ignore[attr-defined]
    fake._seen_prompt_caches = seen_prompt_caches  # type: ignore[attr-defined]
    return fake


def _reload_native_backend_with_fake_mlx_lm(
    monkeypatch: pytest.MonkeyPatch,
):
    fake = _build_fake_mlx_lm_with_observable_cache()
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    monkeypatch.setitem(sys.modules, "mlx_lm.models", fake.models)
    monkeypatch.setitem(sys.modules, "mlx_lm.models.cache", fake.models.cache)
    import owlmlx.runtime.mlx_native_backend as mod
    importlib.reload(mod)
    return mod, fake


def test_native_session_kv_cache_reuses_prompt_cache_for_same_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        assert backend.load("fake-model").ok is True

        first = backend.generate("fake-model", "hello", session_id="s1")
        second = backend.generate("fake-model", "hello again", session_id="s1")

        assert first.ok is True
        assert second.ok is True
        assert len(fake._created_caches) == 1
        assert fake._seen_prompt_caches[0] is fake._seen_prompt_caches[1]
        assert backend._cache_manager.counters().entries == 0
        status = backend.status().detail["session_kv_cache"]
        assert status["enabled"] is True
        assert status["active_entries"] == 1
        assert status["counters"]["entries_created"] == 1
        assert status["counters"]["hits"] == 1
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_drops_model_entries_before_unload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, _fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")
        backend.generate("fake-model", "hello", session_id="s1")
        assert backend.status().detail["session_kv_cache"]["active_entries"] == 1

        unload = backend.unload("fake-model")

        assert unload.ok is True
        session_cache = backend.status().detail["session_kv_cache"]
        assert session_cache["active_entries"] == 0
        assert session_cache["counters"]["drops"] == 1
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_pressure_falls_back_to_single_request_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")
        backend.generate("fake-model", "hello", session_id="s1")

        pressured = backend.generate(
            "fake-model",
            "hello under pressure",
            session_id="s1",
            session_kv_cache_watermark="yellow",
        )

        assert pressured.ok is True
        assert len(fake._created_caches) == 2
        assert fake._seen_prompt_caches[0] is not fake._seen_prompt_caches[1]
        assert backend._cache_manager.counters().entries == 1
        session_cache = backend.status().detail["session_kv_cache"]
        assert session_cache["active_entries"] == 0
        assert session_cache["counters"]["rejects"] == 1
        assert session_cache["counters"]["evictions"] == 1
    finally:
        importlib.reload(mod)
