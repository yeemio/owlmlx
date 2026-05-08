"""Real upstream binding for the native MLX backend KV cache handle.

These tests use the **real installed ``mlx_lm``** (not a fake stub) to prove
that ``MlxNativeBackend`` can:

1. resolve ``mlx_lm.models.cache.make_prompt_cache`` through its real
   public surface
2. call ``make_prompt_cache(model)`` on a model object that the adapter
   holds as an opaque handle (here, a minimal ``mlx.nn.Module`` subclass —
   not a downloaded model) and obtain a usable cache object
3. observe that ``_NativeSession`` records ``last_prompt_cache`` and
   ``last_prompt_cache_id`` after the bind call, and that
   ``prompt_cache_call_count`` advances per request

These tests do **not** download or load any real model. They prove the
**binding path** between owlmlx and the upstream cache API on the
installed library version, not the full lifecycle. Real-model lifecycle is
covered by ``tests/test_mlx_native_backend_real_smoke.py`` (env-var gated,
opt-in).

The full ``promoted`` upgrade of the matrix row depends on real-model
lifecycle evidence; this round produces ``partial_promoted`` evidence at
the binding layer.
"""

from __future__ import annotations

import pytest


def _mlx_lm_importable() -> bool:
    try:
        import mlx_lm  # type: ignore[import-not-found] # noqa: F401
    except ImportError:
        return False
    return True


def _make_prompt_cache_resolvable() -> bool:
    if not _mlx_lm_importable():
        return False
    try:
        import mlx_lm  # type: ignore[import-not-found]
        from mlx_lm.models.cache import make_prompt_cache  # type: ignore # noqa: F401
    except Exception:
        return False
    return True


@pytest.mark.skipif(
    not _make_prompt_cache_resolvable(),
    reason="real mlx_lm.models.cache.make_prompt_cache not reachable in this env",
)
def test_resolve_make_prompt_cache_returns_real_callable() -> None:
    import mlx_lm  # type: ignore[import-not-found]

    from owlmlx.runtime.mlx_native_backend import _resolve_make_prompt_cache

    resolved = _resolve_make_prompt_cache(mlx_lm)
    assert resolved is not None
    assert callable(resolved)
    # Must match the canonical upstream symbol so future rounds don't
    # silently bind to a different code path.
    from mlx_lm.models.cache import make_prompt_cache  # type: ignore

    assert resolved is make_prompt_cache


@pytest.mark.skipif(
    not _make_prompt_cache_resolvable(),
    reason="real mlx_lm.models.cache.make_prompt_cache not reachable in this env",
)
def test_make_prompt_cache_accepts_minimal_mlx_nn_module() -> None:
    """A minimal ``mlx.nn.Module`` (no layers) must round-trip through
    ``make_prompt_cache`` and produce an iterable cache list.

    This proves the upstream API contract that the native adapter relies
    on. Cache content is tested in real-model lifecycle, not here.
    """

    import mlx.nn as nn  # type: ignore[import-not-found]
    from mlx_lm.models.cache import make_prompt_cache  # type: ignore

    class _MinimalModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.layers = []  # explicit empty layers list

    model = _MinimalModel()
    cache = make_prompt_cache(model)
    assert cache is not None
    # A list (or list-like) is the documented return type.
    assert hasattr(cache, "__iter__")
    # An empty-layers model should produce an empty cache; we don't assert
    # the exact length because the upstream API may add per-model overhead
    # in future versions, but the call must not raise.


@pytest.mark.skipif(
    not _make_prompt_cache_resolvable(),
    reason="real mlx_lm.models.cache.make_prompt_cache not reachable in this env",
)
def test_native_backend_records_prompt_cache_per_call_with_minimal_model() -> None:
    """End-to-end binding test on the real ``mlx_lm`` cache surface.

    We bypass ``MlxNativeBackend.load`` (which would try to load a real
    model from disk) and directly install a synthetic ``_NativeSession``
    with a minimal ``mlx.nn.Module`` as the model handle. This exercises
    the adapter's internal ``_make_fresh_prompt_cache`` against the real
    upstream callable without requiring any downloaded weights.
    """

    import mlx.nn as nn  # type: ignore[import-not-found]
    import mlx_lm  # type: ignore[import-not-found]

    from owlmlx.runtime.mlx_native_backend import (
        MlxNativeBackend,
        _NativeSession,
    )
    from owlmlx.runtime.types import LoadedModelInfo

    class _MinimalModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.layers = []

    backend = MlxNativeBackend()
    info = LoadedModelInfo(
        model_id="minimal-real",
        memory_gb=0.0,
        backend="mlx-native",
        loaded_at=0.0,
    )
    session = _NativeSession(
        model_id="minimal-real",
        model=_MinimalModel(),
        tokenizer=object(),
        info=info,
    )
    # Inject directly; this is a binding-layer test, not a public-surface
    # test, so we are inside the adapter's own contract surface.
    backend._sessions["minimal-real"] = session  # type: ignore[attr-defined]

    assert session.last_prompt_cache is None
    assert session.prompt_cache_call_count == 0

    cache_a = backend._make_fresh_prompt_cache(mlx_lm, session)  # type: ignore[attr-defined]
    assert cache_a is not None
    assert session.last_prompt_cache is cache_a
    assert session.last_prompt_cache_id == id(cache_a)
    assert session.prompt_cache_call_count == 1

    # Per-request semantics: a second call must produce a *different* cache
    # object, not reuse cache_a. This locks in the "single-request only,
    # no cross-request reuse" contract on the binding layer.
    cache_b = backend._make_fresh_prompt_cache(mlx_lm, session)  # type: ignore[attr-defined]
    assert cache_b is not None
    assert cache_b is not cache_a
    assert session.last_prompt_cache is cache_b
    assert session.last_prompt_cache_id == id(cache_b)
    assert session.last_prompt_cache_id != id(cache_a)
    assert session.prompt_cache_call_count == 2

    cap = backend.capability_entry_points("minimal-real")
    assert cap["available"] is True
    assert (
        cap["kv_cache_factory"]["status"]
        == "bound_per_request_single_request_only"
    )
    assert cap["kv_cache_factory"]["cross_request_reuse_claimed"] is False
    assert cap["kv_cache_factory"]["prompt_cache_call_count"] == 2

    status = backend.status()
    assert status.detail["upstream_make_prompt_cache_reachable"] is True


@pytest.mark.skipif(
    not _mlx_lm_importable(),
    reason="real mlx_lm not installed",
)
def test_native_backend_status_reports_upstream_reachability_truthfully() -> None:
    """When real mlx_lm is installed, status must report the upstream cache
    surface as reachable; the cache binding layer is now load-bearing.
    """

    from owlmlx.runtime.mlx_native_backend import MlxNativeBackend

    backend = MlxNativeBackend()
    status = backend.status()
    assert status.healthy is True
    assert "upstream_make_prompt_cache_reachable" in status.detail
    # The actual installed mlx-lm in this venv has the cache surface, so
    # this must be True; in environments where it's not, the test is
    # already skipped above.
    assert status.detail["upstream_make_prompt_cache_reachable"] is True
