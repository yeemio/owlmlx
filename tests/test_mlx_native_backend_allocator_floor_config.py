"""C-3.3 allocator floor configuration wiring contract tests.

Proves that ``MlxNativeBackend.load`` invokes
``memory_actuator.configure_allocator_floor`` exactly once per
backend instance, only when at least one of
``OWLMLX_NATIVE_CACHE_LIMIT_BYTES`` / ``OWLMLX_NATIVE_WIRED_LIMIT_BYTES``
is set, and is observable via ``backend._last_allocator_floor_config``.

Tests use fake ``mlx_lm`` injection (so load succeeds) and monkeypatched
``_try_import_mlx_core`` (so the actuator branch is deterministic).
"""

from __future__ import annotations

import importlib
import sys
import types

import pytest

from owlmlx.memory_actuator import AllocatorFloorConfig


def _build_fake_mlx_lm_with_cache_surface() -> types.ModuleType:
    fake = types.ModuleType("mlx_lm")
    models = types.ModuleType("mlx_lm.models")
    cache_mod = types.ModuleType("mlx_lm.models.cache")
    cache_mod.make_prompt_cache = lambda model: [object()]  # type: ignore[attr-defined]
    models.cache = cache_mod  # type: ignore[attr-defined]
    fake.models = models  # type: ignore[attr-defined]
    fake.load = lambda model_id: (object(), object())  # type: ignore[attr-defined]
    return fake


class _FakeMlxCoreWithFloorTracker:
    """Minimal fake of ``mlx.core`` that records allocator-floor calls."""

    def __init__(self) -> None:
        self.set_cache_limit_calls: list[int] = []
        self.set_wired_limit_calls: list[int] = []
        self._previous_cache_limit = 0

    def set_cache_limit(self, limit: int) -> int:
        self.set_cache_limit_calls.append(limit)
        prior = self._previous_cache_limit
        self._previous_cache_limit = limit
        return prior

    def set_wired_limit(self, limit: int) -> int:
        self.set_wired_limit_calls.append(limit)
        return 0

    # Required by other actuator paths but irrelevant to floor config tests.
    def clear_cache(self) -> None:  # pragma: no cover
        pass

    def get_active_memory(self) -> int:  # pragma: no cover
        return 0

    def get_cache_memory(self) -> int:  # pragma: no cover
        return 0


class _FakeMlxCoreWithoutWiredLimit:
    """Variant without ``set_wired_limit`` (older mlx versions / non-15+)."""

    def __init__(self) -> None:
        self.set_cache_limit_calls: list[int] = []

    def set_cache_limit(self, limit: int) -> int:
        self.set_cache_limit_calls.append(limit)
        return 0

    def clear_cache(self) -> None:  # pragma: no cover
        pass

    def get_active_memory(self) -> int:  # pragma: no cover
        return 0

    def get_cache_memory(self) -> int:  # pragma: no cover
        return 0


def _reload_backend(monkeypatch: pytest.MonkeyPatch):
    fake = _build_fake_mlx_lm_with_cache_surface()
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    monkeypatch.setitem(sys.modules, "mlx_lm.models", fake.models)
    monkeypatch.setitem(sys.modules, "mlx_lm.models.cache", fake.models.cache)
    import owlmlx.runtime.mlx_native_backend as mod
    importlib.reload(mod)
    return mod


def _restore(mod) -> None:
    importlib.reload(mod)


def test_load_does_not_configure_when_no_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When neither env var is set, the floor configure call is skipped
    entirely — ``_last_allocator_floor_config`` remains ``None``.
    """

    monkeypatch.delenv("OWLMLX_NATIVE_CACHE_LIMIT_BYTES", raising=False)
    monkeypatch.delenv("OWLMLX_NATIVE_WIRED_LIMIT_BYTES", raising=False)
    mod = _reload_backend(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        fake_mx = _FakeMlxCoreWithFloorTracker()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)

        backend.load("fake-model-A1", memory_gb=1.0)

        assert backend._last_allocator_floor_config is None
        assert fake_mx.set_cache_limit_calls == []
        assert fake_mx.set_wired_limit_calls == []
        # The idempotent flag IS still set after the load — opting out
        # is also a one-shot decision.
        assert backend._allocator_floor_configured is True
    finally:
        _restore(mod)


def test_load_configures_when_cache_limit_env_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_NATIVE_CACHE_LIMIT_BYTES", "8589934592")  # 8 GB
    monkeypatch.delenv("OWLMLX_NATIVE_WIRED_LIMIT_BYTES", raising=False)
    mod = _reload_backend(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        fake_mx = _FakeMlxCoreWithFloorTracker()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)

        backend.load("fake-model-A2", memory_gb=1.0)

        assert fake_mx.set_cache_limit_calls == [8589934592]
        assert fake_mx.set_wired_limit_calls == []  # wired not requested

        config = backend._last_allocator_floor_config
        assert isinstance(config, AllocatorFloorConfig)
        assert config.cache_limit_bytes == 8589934592
        assert config.wired_limit_bytes is None
        assert config.wired_limit_supported is True  # fake exposes it
    finally:
        _restore(mod)


def test_load_configures_when_wired_limit_env_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OWLMLX_NATIVE_CACHE_LIMIT_BYTES", raising=False)
    monkeypatch.setenv("OWLMLX_NATIVE_WIRED_LIMIT_BYTES", "4294967296")  # 4 GB
    mod = _reload_backend(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        fake_mx = _FakeMlxCoreWithFloorTracker()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)

        backend.load("fake-model-A3", memory_gb=1.0)

        assert fake_mx.set_wired_limit_calls == [4294967296]
        assert fake_mx.set_cache_limit_calls == []
        config = backend._last_allocator_floor_config
        assert config is not None
        assert config.wired_limit_bytes == 4294967296
    finally:
        _restore(mod)


def test_load_configures_only_once_across_multiple_loads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The idempotent flag must prevent repeat configure calls even
    when multiple models are loaded sequentially.
    """

    monkeypatch.setenv("OWLMLX_NATIVE_CACHE_LIMIT_BYTES", "1000000000")
    monkeypatch.delenv("OWLMLX_NATIVE_WIRED_LIMIT_BYTES", raising=False)
    mod = _reload_backend(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        fake_mx = _FakeMlxCoreWithFloorTracker()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)

        backend.load("model-1")
        backend.load("model-2")
        backend.load("model-3")

        assert fake_mx.set_cache_limit_calls == [1000000000], (
            "configure must fire exactly once across multiple loads"
        )
    finally:
        _restore(mod)


def test_load_with_no_mlx_returns_noop_config_when_env_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env set but mlx.core not importable → actuator no-op branch fires;
    config is recorded with the operator-supplied bytes echoed back.
    """

    monkeypatch.setenv("OWLMLX_NATIVE_CACHE_LIMIT_BYTES", "5000000000")
    monkeypatch.delenv("OWLMLX_NATIVE_WIRED_LIMIT_BYTES", raising=False)
    mod = _reload_backend(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: None)

        backend.load("model-no-mlx")

        config = backend._last_allocator_floor_config
        assert isinstance(config, AllocatorFloorConfig)
        assert config.cache_limit_bytes == 5000000000
        assert config.wired_limit_supported is False
    finally:
        _restore(mod)


def test_load_handles_invalid_env_var_value_gracefully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Misconfigured env var (e.g. non-integer) must not block load.
    Per the helper contract, parse failures fall back to ``None``,
    treated as "not set". The load still succeeds.
    """

    monkeypatch.setenv("OWLMLX_NATIVE_CACHE_LIMIT_BYTES", "not_a_number")
    monkeypatch.setenv("OWLMLX_NATIVE_WIRED_LIMIT_BYTES", "")
    mod = _reload_backend(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        fake_mx = _FakeMlxCoreWithFloorTracker()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)

        result = backend.load("model-bad-env")
        assert result.ok is True

        # Both unparseable → both treated as None → no configure call.
        assert backend._last_allocator_floor_config is None
        assert fake_mx.set_cache_limit_calls == []
    finally:
        _restore(mod)


def test_load_skips_wired_limit_when_mlx_lacks_attribute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the mlx module lacks ``set_wired_limit`` (older mlx / non-
    macOS-15), the actuator skips it without raising; config records
    ``wired_limit_supported=False``.
    """

    monkeypatch.setenv("OWLMLX_NATIVE_CACHE_LIMIT_BYTES", "100000000")
    monkeypatch.setenv("OWLMLX_NATIVE_WIRED_LIMIT_BYTES", "200000000")
    mod = _reload_backend(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        fake_mx = _FakeMlxCoreWithoutWiredLimit()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)

        backend.load("model-no-wired")

        # cache_limit_bytes was set; wired was requested but mlx variant
        # has no setter — actuator must record wired_limit_supported=False.
        assert fake_mx.set_cache_limit_calls == [100000000]
        config = backend._last_allocator_floor_config
        assert config is not None
        assert config.cache_limit_bytes == 100000000
        assert config.wired_limit_supported is False
    finally:
        _restore(mod)
