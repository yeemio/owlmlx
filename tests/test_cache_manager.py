"""Tests for the owlmlx KV cache manager scaffold.

These tests do **not** require ``mlx_lm`` to be installed. They drive the
``CacheManager`` scaffold using a hand-built fake module that mirrors
``mlx_lm.models.cache.make_prompt_cache``'s attribute path. The scaffold
contract under test is:

- zero-baseline counter ledger
- single-request semantics (consecutive ``acquire_for_request`` produces
  distinct cache objects)
- defensive attribute-walk resolver fails loudly when the upstream
  surface is missing
- ``status_dict`` shape matches what residency-evidence consumers expect

This scaffold round does not exercise wiring into ``MlxNativeBackend``.
"""

from __future__ import annotations

import types

import pytest

from owlmlx.cache_manager import (
    CacheManager,
    CacheManagerCounters,
    CachedRequestHandle,
)


# --------------------------------------------------------------------------- #
# Fake mlx_lm helpers
# --------------------------------------------------------------------------- #


def _build_fake_mlx_lm_with_cache_surface() -> types.ModuleType:
    """Build a fake ``mlx_lm`` module whose ``models.cache.make_prompt_cache``
    returns a fresh sentinel object on every call.

    The path matches the upstream layout
    ``mlx_lm.models.cache.make_prompt_cache`` so the manager's defensive
    attribute walk traverses the same shape it would in production.
    """

    fake = types.ModuleType("mlx_lm")
    models = types.ModuleType("mlx_lm.models")
    cache = types.ModuleType("mlx_lm.models.cache")

    def fake_make_prompt_cache(model: object) -> object:
        # Return a fresh object on every call so consecutive ``acquire_for_request``
        # calls observe distinct ``id()`` values.
        return object()

    cache.make_prompt_cache = fake_make_prompt_cache  # type: ignore[attr-defined]
    models.cache = cache  # type: ignore[attr-defined]
    fake.models = models  # type: ignore[attr-defined]
    return fake


def _build_fake_mlx_lm_without_cache_surface() -> types.ModuleType:
    """Build a fake ``mlx_lm`` module with an empty ``models`` namespace."""

    fake = types.ModuleType("mlx_lm")
    models = types.ModuleType("mlx_lm.models")
    fake.models = models  # type: ignore[attr-defined]
    return fake


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


def test_cache_manager_starts_with_zero_counters() -> None:
    manager = CacheManager()
    counters = manager.counters()
    assert isinstance(counters, CacheManagerCounters)
    assert counters.entries == 0
    assert counters.resident_bytes == 0
    assert counters.reuse_events == 0
    assert counters.hit_count == 0
    assert counters.eviction_events == 0


def test_acquire_for_request_returns_handle_with_correct_model_id() -> None:
    manager = CacheManager()
    fake_mlx_lm = _build_fake_mlx_lm_with_cache_surface()
    handle, _cache = manager.acquire_for_request(
        model_id="fake-model-A",
        mlx_lm_module=fake_mlx_lm,
        model=object(),
    )
    assert isinstance(handle, CachedRequestHandle)
    assert handle.model_id == "fake-model-A"
    assert isinstance(handle.cache_object_id, int)
    assert handle.cross_request_reuse_claimed is False
    assert handle.created_at > 0.0


def test_acquire_returns_handle_and_cache_object_tuple() -> None:
    """Wiring contract: ``acquire_for_request`` returns ``(handle, cache_object)``.

    The cache_object is the value returned by upstream ``make_prompt_cache``.
    The caller owns the strong reference; the manager intentionally does not
    retain it (single-request semantics).
    """

    manager = CacheManager()
    sentinel = object()
    fake = types.ModuleType("mlx_lm")
    models = types.ModuleType("mlx_lm.models")
    cache_mod = types.ModuleType("mlx_lm.models.cache")
    cache_mod.make_prompt_cache = lambda model: sentinel  # type: ignore[attr-defined]
    models.cache = cache_mod  # type: ignore[attr-defined]
    fake.models = models  # type: ignore[attr-defined]

    handle, cache_object = manager.acquire_for_request(
        model_id="m",
        mlx_lm_module=fake,
        model=object(),
    )

    assert isinstance(handle, CachedRequestHandle)
    assert cache_object is sentinel


def test_acquire_calls_make_prompt_cache_via_attribute_walk() -> None:
    """The manager must resolve ``make_prompt_cache`` through the passed
    module's attribute path, not via a top-level import.
    """

    fake = types.ModuleType("mlx_lm")
    models = types.ModuleType("mlx_lm.models")
    cache_mod = types.ModuleType("mlx_lm.models.cache")

    call_log: list[object] = []
    sentinel_cache = object()

    def fake_make_prompt_cache(model: object) -> object:
        call_log.append(model)
        return sentinel_cache

    cache_mod.make_prompt_cache = fake_make_prompt_cache  # type: ignore[attr-defined]
    models.cache = cache_mod  # type: ignore[attr-defined]
    fake.models = models  # type: ignore[attr-defined]

    manager = CacheManager()
    model_obj = object()
    handle, cache_object = manager.acquire_for_request(
        model_id="fake-attr-walk",
        mlx_lm_module=fake,
        model=model_obj,
    )
    assert call_log == [model_obj]
    # ``cache_object_id`` is a per-manager monotonic counter, not
    # ``id(sentinel_cache)`` — see ``CachedRequestHandle`` docstring.
    # Anchor: first acquire on a fresh manager assigns id 1.
    assert handle.cache_object_id == 1
    # Cache object passes through unmodified.
    assert cache_object is sentinel_cache


def test_acquire_increments_entries_counter() -> None:
    manager = CacheManager()
    fake_mlx_lm = _build_fake_mlx_lm_with_cache_surface()
    assert manager.counters().entries == 0
    manager.acquire_for_request(
        model_id="m",
        mlx_lm_module=fake_mlx_lm,
        model=object(),
    )
    assert manager.counters().entries == 1
    manager.acquire_for_request(
        model_id="m",
        mlx_lm_module=fake_mlx_lm,
        model=object(),
    )
    assert manager.counters().entries == 2
    # Other counters stay at zero baseline by design.
    final = manager.counters()
    assert final.resident_bytes == 0
    assert final.reuse_events == 0
    assert final.hit_count == 0
    assert final.eviction_events == 0


def test_consecutive_acquires_produce_distinct_cache_object_ids() -> None:
    """Single-request semantics: every acquire must produce a fresh cache
    object. This locks the contract by test, not by convention.
    """

    manager = CacheManager()
    fake_mlx_lm = _build_fake_mlx_lm_with_cache_surface()
    h1, _c1 = manager.acquire_for_request(
        model_id="m",
        mlx_lm_module=fake_mlx_lm,
        model=object(),
    )
    h2, _c2 = manager.acquire_for_request(
        model_id="m",
        mlx_lm_module=fake_mlx_lm,
        model=object(),
    )
    h3, _c3 = manager.acquire_for_request(
        model_id="m",
        mlx_lm_module=fake_mlx_lm,
        model=object(),
    )
    ids = {h1.cache_object_id, h2.cache_object_id, h3.cache_object_id}
    assert len(ids) == 3, "scaffold must produce distinct cache objects per acquire"
    # Cross-request reuse is not claimed.
    for handle in (h1, h2, h3):
        assert handle.cross_request_reuse_claimed is False


def test_release_drops_handle_reference_without_changing_counters() -> None:
    manager = CacheManager()
    fake_mlx_lm = _build_fake_mlx_lm_with_cache_surface()
    handle, _cache = manager.acquire_for_request(
        model_id="m",
        mlx_lm_module=fake_mlx_lm,
        model=object(),
    )
    counters_before_release = manager.counters()
    manager.release_for_request(handle)
    counters_after_release = manager.counters()

    assert counters_before_release == counters_after_release
    # Releasing again is a no-op (the handle is unknown after the first release).
    manager.release_for_request(handle)
    assert manager.counters() == counters_after_release

    # ``status_dict`` must reflect the empty per-model registry.
    snapshot = manager.status_dict()
    assert snapshot["handles_count_by_model"] == {}


def test_status_dict_shape_exposes_live_counter_vocabulary() -> None:
    """``status_dict`` exposes the live runtime-owned counter names."""

    manager = CacheManager()
    fake_mlx_lm = _build_fake_mlx_lm_with_cache_surface()
    manager.acquire_for_request(
        model_id="m",
        mlx_lm_module=fake_mlx_lm,
        model=object(),
    )
    snapshot = manager.status_dict()

    # Top-level shape.
    assert snapshot["manager_kind"] == "owlmlx_kv_cache_manager_scaffold"
    assert snapshot["single_request_semantics_enforced"] is True
    assert snapshot["cross_request_reuse_claimed"] is False
    assert snapshot["wired_into_native_backend"] is True
    assert snapshot["handles_count_by_model"] == {"m": 1}

    # Counter shape — five expected keys, all integers.
    counters_payload = snapshot["counters"]
    assert set(counters_payload.keys()) == {
        "entries",
        "resident_bytes",
        "reuse_events",
        "hit_count",
        "eviction_events",
    }
    assert counters_payload["entries"] == 1
    for key in ("resident_bytes", "reuse_events", "hit_count", "eviction_events"):
        assert counters_payload[key] == 0
        assert isinstance(counters_payload[key], int)


def test_acquire_when_make_prompt_cache_attribute_missing_raises_clear_error() -> None:
    """When the upstream ``mlx_lm.models.cache.make_prompt_cache`` is missing,
    the manager must raise a clear ``RuntimeError``. The manager's contract
    is to fail loudly — callers reach the manager only when they intend to
    bind, so silent skip would mask a real upstream gap.
    """

    manager = CacheManager()
    fake_mlx_lm = _build_fake_mlx_lm_without_cache_surface()
    with pytest.raises(RuntimeError) as excinfo:
        manager.acquire_for_request(
            model_id="m",
            mlx_lm_module=fake_mlx_lm,
            model=object(),
        )
    assert "cache_manager" in str(excinfo.value)

    # Counters must be untouched on the failure path.
    counters = manager.counters()
    assert counters.entries == 0
    assert counters.resident_bytes == 0
    assert counters.reuse_events == 0
    assert counters.hit_count == 0
    assert counters.eviction_events == 0


def test_acquire_rejects_empty_model_id() -> None:
    manager = CacheManager()
    fake_mlx_lm = _build_fake_mlx_lm_with_cache_surface()
    with pytest.raises(ValueError):
        manager.acquire_for_request(
            model_id="",
            mlx_lm_module=fake_mlx_lm,
            model=object(),
        )
