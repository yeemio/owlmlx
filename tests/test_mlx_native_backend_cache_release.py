"""C-1.2 release-wiring contract tests.

Proves that ``MlxNativeBackend`` hands the active cache_manager handle
back to the manager on the lifecycle points where the cache is no
longer needed:

- after a ``generate(...)`` returns
- after a ``stream_generate(...)`` reaches its terminal ``done`` event
- when a stream's iterator is closed early (Python ``finally``
  semantics)
- when ``unload(...)`` drops the session

The contract is observable through ``backend._cache_manager`` — when
the manager's per-model registry is empty for a model_id, the round
has fully released. ``counters().entries`` is monotonic on acquire and
is **not** decremented on release (see ``cache_manager`` scaffold §
release_for_request).

Tests use fake ``mlx_lm`` injection so they run without the optional
``runtime`` extra installed.
"""

from __future__ import annotations

import importlib
import sys
import types

import pytest


def _build_fake_mlx_lm_with_cache_surface() -> types.ModuleType:
    """Construct a fake ``mlx_lm`` module that owns a working cache surface."""

    fake = types.ModuleType("mlx_lm")
    models = types.ModuleType("mlx_lm.models")
    cache_mod = types.ModuleType("mlx_lm.models.cache")

    def make_prompt_cache(model: object) -> list[object]:
        # Return a fresh list per call so cache_object identity is per-acquire.
        return [object()]

    cache_mod.make_prompt_cache = make_prompt_cache  # type: ignore[attr-defined]
    models.cache = cache_mod  # type: ignore[attr-defined]
    fake.models = models  # type: ignore[attr-defined]

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    class _FakeToken:
        def __init__(self, text: str, finish_reason: str | None = None) -> None:
            self.text = text
            self.finish_reason = finish_reason

    def fake_stream_generate(model, tokenizer, *, prompt, max_tokens, **kwargs):
        # Two-chunk stream; ``finish_reason`` only on the last chunk.
        yield _FakeToken("hello")
        yield _FakeToken(" world", finish_reason="stop")

    def fake_generate(model, tokenizer, *, prompt, max_tokens, **kwargs) -> str:
        return "hello world"

    fake.load = fake_load  # type: ignore[attr-defined]
    fake.stream_generate = fake_stream_generate  # type: ignore[attr-defined]
    fake.generate = fake_generate  # type: ignore[attr-defined]
    return fake


def _reload_native_backend_with_fake_mlx_lm(
    monkeypatch: pytest.MonkeyPatch,
):
    """Inject a fake mlx_lm into sys.modules and reload the adapter module."""

    fake = _build_fake_mlx_lm_with_cache_surface()
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    monkeypatch.setitem(sys.modules, "mlx_lm.models", fake.models)
    monkeypatch.setitem(sys.modules, "mlx_lm.models.cache", fake.models.cache)
    import owlmlx.runtime.mlx_native_backend as mod
    importlib.reload(mod)
    return mod, fake


def _restore_real_mlx_lm(mod) -> None:
    """Reload the adapter module with the real mlx_lm restored."""

    importlib.reload(mod)


def test_release_fires_after_generate_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod, _fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        load_result = backend.load("fake-model-A")
        assert load_result.ok is True

        result = backend.generate("fake-model-A", "say hi", max_tokens=4)
        assert result.ok is True

        # Per-model handle list must be empty after release.
        assert (
            "fake-model-A"
            not in backend._cache_manager._handles_by_model
        ), "release should drop the handle from the per-model registry"
        # Counter does not decrement on release; ``entries`` reflects the
        # acquire-side count (1 for one generate).
        assert backend._cache_manager.counters().entries == 1
        # Session-side mirror retains the cache reference (backward-compat),
        # but the manager-canonical ledger is empty for active handles.
        session = backend._sessions["fake-model-A"]
        assert session.active_cache_handle is None
    finally:
        _restore_real_mlx_lm(mod)


def test_release_fires_after_stream_generate_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod, _fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model-B")

        events = list(backend.stream_generate("fake-model-B", "hi"))
        assert [e.event for e in events] == ["token", "token", "done"]

        assert (
            "fake-model-B"
            not in backend._cache_manager._handles_by_model
        )
        assert backend._cache_manager.counters().entries == 1
        session = backend._sessions["fake-model-B"]
        assert session.active_cache_handle is None
    finally:
        _restore_real_mlx_lm(mod)


def test_release_fires_on_early_stream_close(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Caller closes the iterator before ``done`` — release must still fire.

    Python guarantees the generator's ``finally`` runs on close, which
    is exactly the path C-1.2 wires the release into.
    """

    mod, _fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model-C")

        gen = backend.stream_generate("fake-model-C", "hi")
        first_event = next(gen)
        assert first_event.event == "token"
        # Caller drops the iterator without consuming further.
        gen.close()

        assert (
            "fake-model-C"
            not in backend._cache_manager._handles_by_model
        )
        # Counter still reflects the acquire (release does not decrement).
        assert backend._cache_manager.counters().entries == 1
        session = backend._sessions["fake-model-C"]
        assert session.active_cache_handle is None
    finally:
        _restore_real_mlx_lm(mod)


def test_release_fires_on_unload_with_pending_handle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If a handle is somehow still pending on the session at unload time,
    unload must hand it back to the manager before dropping the session.

    In normal flows this should not happen (generate / stream / close all
    release first). The test forces the condition by setting
    ``session.active_cache_handle`` directly.
    """

    mod, _fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model-D")
        # Force-acquire one handle and stash it on the session without
        # releasing — simulates the "pathological pending handle" case.
        session = backend._sessions["fake-model-D"]
        handle, _cache = backend._cache_manager.acquire_for_request(
            model_id="fake-model-D",
            mlx_lm_module=sys.modules["mlx_lm"],
            model=session.model,
        )
        session.active_cache_handle = handle
        assert (
            "fake-model-D"
            in backend._cache_manager._handles_by_model
        ), "precondition: handle is in the registry before unload"

        unload_result = backend.unload("fake-model-D")
        assert unload_result.ok is True

        assert (
            "fake-model-D"
            not in backend._cache_manager._handles_by_model
        ), "unload must release the pending handle"
    finally:
        _restore_real_mlx_lm(mod)


def test_release_idempotent_when_no_active_handle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod, _fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model-E")
        session = backend._sessions["fake-model-E"]
        assert session.active_cache_handle is None

        # Calling release with no active handle must not raise.
        backend._release_active_cache(session)
        backend._release_active_cache(session)
        assert session.active_cache_handle is None
    finally:
        _restore_real_mlx_lm(mod)


def test_active_cache_handle_set_during_make_fresh_prompt_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``_make_fresh_prompt_cache`` returns a real cache, the session's
    ``active_cache_handle`` must be populated so the eventual release
    has something to release.
    """

    mod, fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model-F")
        session = backend._sessions["fake-model-F"]

        cache = backend._make_fresh_prompt_cache(fake, session)
        assert cache is not None
        assert session.active_cache_handle is not None
        assert session.active_cache_handle.model_id == "fake-model-F"

        # Release it manually; subsequent state matches post-release.
        backend._release_active_cache(session)
        assert session.active_cache_handle is None
    finally:
        _restore_real_mlx_lm(mod)
