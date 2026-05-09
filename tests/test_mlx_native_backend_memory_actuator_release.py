"""C-3.1 memory_actuator wiring contract tests.

Proves that ``MlxNativeBackend.unload`` invokes
``memory_actuator.release_single_model`` after dropping session
references, and that the resulting receipt is observable on
``backend._last_unload_receipt`` for downstream observers.

The test pattern monkeypatches ``MlxNativeBackend._try_import_mlx_core``
rather than fighting Python's import system; this is the lowest-cost
way to switch between "mlx core not installed" and "mlx core present"
test paths without depending on the actual mlx package state in
``.venv``.
"""

from __future__ import annotations

import importlib
import sys
import types
from typing import Any

import pytest

from owlmlx.memory_actuator import ReclaimReceipt


def _build_fake_mlx_lm_with_cache_surface() -> types.ModuleType:
    fake = types.ModuleType("mlx_lm")
    models = types.ModuleType("mlx_lm.models")
    cache_mod = types.ModuleType("mlx_lm.models.cache")

    def make_prompt_cache(model: object) -> list[object]:
        return [object()]

    cache_mod.make_prompt_cache = make_prompt_cache  # type: ignore[attr-defined]
    models.cache = cache_mod  # type: ignore[attr-defined]
    fake.models = models  # type: ignore[attr-defined]

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), object())

    fake.load = fake_load  # type: ignore[attr-defined]
    return fake


class _FakeMlxCore:
    """Minimal fake of ``mlx.core`` for actuator wiring tests.

    Counts ``clear_cache`` invocations and reports synthetic memory
    snapshots; does NOT actually allocate any GPU memory.
    """

    def __init__(self) -> None:
        self.clear_cache_call_count = 0
        self._active_memory = 1_000_000_000  # 1 GB synthetic active baseline
        self._cache_memory = 500_000_000  # 0.5 GB synthetic cache baseline

    def clear_cache(self) -> None:
        self.clear_cache_call_count += 1
        # Synthetic post-clear shrink: cache pool empties, active drops too.
        self._cache_memory = 0
        self._active_memory = max(0, self._active_memory - 200_000_000)

    def get_active_memory(self) -> int:
        return self._active_memory

    def get_cache_memory(self) -> int:
        return self._cache_memory

    def get_peak_memory(self) -> int:  # pragma: no cover - used by observability surface
        return 2_000_000_000


def _reload_backend_with_fake_mlx_lm(monkeypatch: pytest.MonkeyPatch):
    fake = _build_fake_mlx_lm_with_cache_surface()
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    monkeypatch.setitem(sys.modules, "mlx_lm.models", fake.models)
    monkeypatch.setitem(sys.modules, "mlx_lm.models.cache", fake.models.cache)
    import owlmlx.runtime.mlx_native_backend as mod
    importlib.reload(mod)
    return mod


def _restore_real_mlx_lm(mod) -> None:
    importlib.reload(mod)


def test_unload_invokes_memory_actuator_and_persists_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``unload`` must populate ``backend._last_unload_receipt`` with a
    ``ReclaimReceipt`` matching the model_id and declared GB.
    """

    mod = _reload_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        # Force the actuator into no-mlx mode for predictable assertions.
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: None)

        backend.load("fake-model-A", memory_gb=12.5)
        assert backend._last_unload_receipt is None
        unload_result = backend.unload("fake-model-A")
        assert unload_result.ok is True

        receipt = backend._last_unload_receipt
        assert isinstance(receipt, ReclaimReceipt)
        assert receipt.model_id == "fake-model-A"
        assert receipt.declared_freed_gb == 12.5
        assert receipt.mlx_module_available is False
        assert receipt.actuator_invoked_clear_cache is False
        assert receipt.active_memory_before_bytes is None
        assert receipt.active_memory_after_bytes is None
    finally:
        _restore_real_mlx_lm(mod)


def test_unload_with_real_mlx_invokes_clear_cache_via_actuator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When mlx.core is importable, the actuator MUST call
    ``mlx_module.clear_cache()`` exactly once during a successful unload.
    """

    mod = _reload_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        fake_mx = _FakeMlxCore()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)

        backend.load("fake-model-B", memory_gb=8.0)
        assert fake_mx.clear_cache_call_count == 0
        backend.unload("fake-model-B")
        assert fake_mx.clear_cache_call_count == 1, (
            "actuator must invoke mlx.clear_cache exactly once per unload"
        )

        receipt = backend._last_unload_receipt
        assert isinstance(receipt, ReclaimReceipt)
        assert receipt.mlx_module_available is True
        assert receipt.actuator_invoked_clear_cache is True
        # Before/after byte readings must be present (not None) when mlx
        # is injected and exposes the observability calls.
        assert receipt.active_memory_before_bytes is not None
        assert receipt.active_memory_after_bytes is not None
        # The fake's clear_cache shrinks active by 200_000_000.
        assert (
            receipt.active_memory_before_bytes
            - receipt.active_memory_after_bytes
            == 200_000_000
        )
        # Cache memory drops to zero per the fake's clear_cache.
        assert receipt.cache_memory_before_bytes == 500_000_000
        assert receipt.cache_memory_after_bytes == 0
    finally:
        _restore_real_mlx_lm(mod)


def test_unload_with_no_mlx_module_returns_noop_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No mlx.core in the environment → actuator returns a shaped no-op
    receipt; unload succeeds; existing 'drop refs and hope' semantics
    are preserved exactly.
    """

    mod = _reload_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: None)

        backend.load("fake-model-C", memory_gb=4.0)
        unload_result = backend.unload("fake-model-C")
        assert unload_result.ok is True
        assert unload_result.freed_gb == 4.0  # declared, unchanged

        receipt = backend._last_unload_receipt
        assert receipt is not None
        assert receipt.mlx_module_available is False
        assert receipt.actuator_invoked_clear_cache is False
    finally:
        _restore_real_mlx_lm(mod)


def test_unload_receipt_carries_declared_freed_gb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Receipt's declared_freed_gb must mirror the session's memory_gb
    used for ``UnloadResult.freed_gb`` — the actuator records what the
    backend declared, not what it measured.
    """

    mod = _reload_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: None)

        for name, gb in (("m1", 1.0), ("m2", 12.5), ("m3", 67.0)):
            backend.load(name, memory_gb=gb)
            unload_result = backend.unload(name)
            assert unload_result.freed_gb == gb
            receipt = backend._last_unload_receipt
            assert receipt is not None
            assert receipt.model_id == name
            assert receipt.declared_freed_gb == gb
    finally:
        _restore_real_mlx_lm(mod)


def test_unload_actuator_runs_after_release_active_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ordering invariant: the cache_manager release must complete before
    the memory_actuator's clear_cache fires. Otherwise the manager
    registry would still carry the handle when allocator pages are
    being reclaimed, which would inverse the dependency graph.
    """

    mod = _reload_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        events: list[str] = []
        fake_mx = _FakeMlxCore()
        original_release = backend._cache_manager.release_for_request

        def traced_release(handle: Any) -> None:
            events.append("cache_release")
            original_release(handle)

        original_clear = fake_mx.clear_cache

        def traced_clear() -> None:
            events.append("actuator_clear_cache")
            original_clear()

        monkeypatch.setattr(
            backend._cache_manager, "release_for_request", traced_release
        )
        fake_mx.clear_cache = traced_clear  # type: ignore[method-assign]
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)

        backend.load("fake-model-D", memory_gb=2.0)
        # Force a cache acquire to populate the active handle.
        session = backend._sessions["fake-model-D"]
        backend._make_fresh_prompt_cache(sys.modules["mlx_lm"], session)
        backend.unload("fake-model-D")

        assert events == ["cache_release", "actuator_clear_cache"], (
            f"expected [cache_release, actuator_clear_cache] but got {events}"
        )
    finally:
        _restore_real_mlx_lm(mod)


def test_unload_unknown_model_does_not_overwrite_last_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unload of a model that was never loaded must NOT overwrite a
    previously persisted receipt — the actuator only fires on the
    success path.
    """

    mod = _reload_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: None)

        backend.load("fake-model-E", memory_gb=3.0)
        backend.unload("fake-model-E")
        first_receipt = backend._last_unload_receipt
        assert first_receipt is not None

        # Now try to unload a model that does not exist.
        not_loaded = backend.unload("nonexistent-model")
        assert not_loaded.ok is False
        # Receipt must remain the previous one — not_loaded is not a
        # successful release.
        assert backend._last_unload_receipt is first_receipt
    finally:
        _restore_real_mlx_lm(mod)


# ---------------------------------------------------------------------------
# C-3.2 measured-freed-bytes plumbing tests
# ---------------------------------------------------------------------------


def test_unload_result_carries_measured_active_freed_bytes_when_mlx_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C-3.2: ``UnloadResult.active_memory_freed_bytes`` must equal
    ``before - after`` from the actuator receipt when mlx.core is
    injected. The fake's ``clear_cache`` shrinks active by 200_000_000
    per call, so the delta is exactly that.
    """

    mod = _reload_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        fake_mx = _FakeMlxCore()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)

        backend.load("fake-model-F1", memory_gb=8.0)
        result = backend.unload("fake-model-F1")
        assert result.ok is True
        assert result.freed_gb == 8.0  # declared, unchanged
        assert result.active_memory_freed_bytes == 200_000_000
        assert result.cache_memory_freed_bytes == 500_000_000
    finally:
        _restore_real_mlx_lm(mod)


def test_unload_result_measured_fields_are_none_without_mlx(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When mlx.core is not importable, ``active_memory_freed_bytes`` and
    ``cache_memory_freed_bytes`` must be ``None`` — the no-op receipt
    has no before/after readings to compute deltas from.
    """

    mod = _reload_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: None)

        backend.load("fake-model-F2", memory_gb=4.0)
        result = backend.unload("fake-model-F2")
        assert result.ok is True
        assert result.freed_gb == 4.0
        assert result.active_memory_freed_bytes is None
        assert result.cache_memory_freed_bytes is None
    finally:
        _restore_real_mlx_lm(mod)


def test_unload_result_clamps_negative_deltas_to_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the allocator GREW during the measurement window (before <
    after), the delta must be reported as ``0`` rather than a negative
    "freed bytes" value that would mislead aggregators.
    """

    mod = _reload_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()

        # Build a fake mlx that GROWS active memory on clear_cache
        # (pathological — to lock the clamp behavior).
        class _GrowingMlx:
            def __init__(self) -> None:
                self._active = 1_000_000_000
                self._cache = 100_000_000
                self.clear_cache_call_count = 0

            def clear_cache(self) -> None:
                self.clear_cache_call_count += 1
                # Growth instead of shrink (simulates fragmentation /
                # OS reservation increase during clear).
                self._active += 50_000_000
                self._cache += 25_000_000

            def get_active_memory(self) -> int:
                return self._active

            def get_cache_memory(self) -> int:
                return self._cache

        growing = _GrowingMlx()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: growing)

        backend.load("fake-model-F3", memory_gb=1.0)
        result = backend.unload("fake-model-F3")
        # Negative deltas are clamped to 0 — caller sees no spurious
        # "negative freed bytes" value.
        assert result.active_memory_freed_bytes == 0
        assert result.cache_memory_freed_bytes == 0
        # Receipt itself still carries the raw before/after (the clamp
        # is at the UnloadResult layer, not the receipt layer).
        receipt = backend._last_unload_receipt
        assert receipt is not None
        assert receipt.active_memory_after_bytes is not None
        assert receipt.active_memory_before_bytes is not None
        assert receipt.active_memory_after_bytes > receipt.active_memory_before_bytes
    finally:
        _restore_real_mlx_lm(mod)


def test_unload_result_preserves_freed_gb_when_measurement_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``freed_gb`` must remain the **declared** value even when measured
    bytes are present. Declared and measured are distinct semantic
    fields; one must not overwrite the other.
    """

    mod = _reload_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        fake_mx = _FakeMlxCore()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)

        backend.load("fake-model-F4", memory_gb=12.5)
        result = backend.unload("fake-model-F4")
        # Declared (operator-known) GB unchanged.
        assert result.freed_gb == 12.5
        # Measured bytes are the actuator's view (a different unit and a
        # different number); the two coexist by design.
        assert result.active_memory_freed_bytes == 200_000_000
    finally:
        _restore_real_mlx_lm(mod)
