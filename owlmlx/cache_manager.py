"""owlmlx KV cache manager scaffold.

Owns the in-process, per-request KV cache lifetime for the native MLX
backend. Distinct from ``cache_truth.py`` (legacy oMLX SSD/hot-cache
schema). Distinct from the upstream ``mlx_lm.models.cache`` primitives
(which provide ``make_prompt_cache``, ``KVCache``, ``LRUPromptCache``).

Scaffold-grade. The current binding enforces single-request semantics:
each ``acquire_for_request`` produces a fresh upstream cache object via
``mlx_lm.models.cache.make_prompt_cache``; cross-request prefix reuse,
LRU eviction, and residency tracking beyond a zero-baseline counter
ledger are explicit extension points, not implementations. See
``docs/source-of-truth/cache-manager-architecture.md``.

This module is NOT wired into ``MlxNativeBackend`` in this scaffold
round. Wiring is a follow-up round and requires a §1a-style promotion
walkthrough on the native MLX backend capability matrix.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


# --------------------------------------------------------------------------- #
# Counter ledger
#
# The five counter names are owned directly by CacheManagerCounters. The older
# cache_residency_evidence scaffold was archived in Stage 1; live native
# backend code reads this manager instead of a standalone evidence module.
# In this scaffold round all counters except ``entries`` remain at zero by
# design.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CacheManagerCounters:
    """Zero-baseline counter ledger for the KV cache manager scaffold.

    The scaffold publishes every field as an integer (never ``None``) so
    consumers can read a stable shape. Real accounting for
    ``resident_bytes``, ``reuse_events``, ``hit_count``, and
    ``eviction_events`` is an extension point, not an implementation.
    """

    entries: int = 0
    resident_bytes: int = 0
    reuse_events: int = 0
    hit_count: int = 0
    eviction_events: int = 0

    def to_dict(self) -> dict[str, int]:
        """Return the counter ledger as a plain dict for status payloads."""

        return {
            "entries": self.entries,
            "resident_bytes": self.resident_bytes,
            "reuse_events": self.reuse_events,
            "hit_count": self.hit_count,
            "eviction_events": self.eviction_events,
        }


# --------------------------------------------------------------------------- #
# Per-request handle
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CachedRequestHandle:
    """Single-request handle for an in-process KV cache object.

    ``cache_object_id`` is a **per-manager monotonic counter** assigned by
    ``CacheManager.acquire_for_request``; it is *not* Python's ``id()`` of
    the upstream cache object. The monotonic-counter shape avoids
    ``id()``-collision bugs that arise when the manager does not hold a
    strong reference to the upstream object (consistent with single-request
    semantics, which forbid the manager from keeping caches alive across
    requests). ``cross_request_reuse_claimed`` is always ``False`` in
    scaffold semantics; it is materialized as a field so that any future
    cross-request keying extension surfaces the claim explicitly rather
    than retrofitting a flag.
    """

    model_id: str
    cache_object_id: int
    created_at: float
    cross_request_reuse_claimed: bool = False


# --------------------------------------------------------------------------- #
# Manager
# --------------------------------------------------------------------------- #


class CacheManager:
    """In-process KV cache lifetime owner — scaffold contract.

    Ownership statement:

    - owns the in-process, per-request lifetime of KV cache objects produced
      by ``mlx_lm.models.cache.make_prompt_cache``
    - does NOT own SSD / hot-cache profile semantics (those belong to
      ``cache_truth.py``)
    - does NOT own pre-claim metadata staging (the
      ``cache_pre_claim_admission_contract.py`` family forbids cache touching
      from the staging seam, and this scaffold respects that — the manager
      is touched only after gate claim, never from pre-claim staging)
    - does NOT yet provide eviction, residency, cohort admission, or
      cross-request reuse — those are explicit extension points

    Single-request semantics are enforced: every ``acquire_for_request``
    produces a fresh upstream cache object; the manager does NOT key
    handles by prefix, does NOT consult any prior handle, and does NOT
    emit reuse / hit / eviction events.

    This module is NOT yet bound into ``MlxNativeBackend``. Wiring is a
    follow-up round.
    """

    def __init__(self) -> None:
        # Per-model handle registry. Lists are intentional — each
        # ``acquire_for_request`` appends; ``release_for_request`` drops
        # the handle reference. No keyed lookup is performed in scaffold.
        self._handles_by_model: dict[str, list[CachedRequestHandle]] = {}
        self._counters = CacheManagerCounters()
        self._lock = threading.Lock()
        # Monotonic counter for ``cache_object_id``. Distinct from Python's
        # ``id()`` precisely because the manager intentionally does not hold
        # a strong reference to upstream cache objects (single-request
        # semantics), which would otherwise cause ``id()`` collisions when
        # GC reuses memory addresses across acquires.
        self._next_cache_object_id = 0

    # ------------------------------------------------------------------ #
    # Lifetime API
    # ------------------------------------------------------------------ #
    def acquire_for_request(
        self,
        *,
        model_id: str,
        mlx_lm_module: Any,
        model: Any,
    ) -> tuple[CachedRequestHandle, Any]:
        """Produce a fresh per-request KV cache via upstream ``make_prompt_cache``.

        Returns a ``(handle, cache_object)`` tuple. The caller owns the
        ``cache_object`` strong reference (single-request semantics: the
        manager intentionally does NOT retain the cache object beyond this
        call so that GC reclaims it after the caller releases its ref).
        ``handle.cache_object_id`` is a per-manager monotonic counter
        independent of Python's ``id(cache_object)``.

        Resolves ``mlx_lm_module.models.cache.make_prompt_cache`` through a
        defensive attribute walk (matching the pattern in
        ``mlx_native_backend._resolve_make_prompt_cache``) so fake-injected
        ``mlx_lm`` stubs in tests can honestly fail with a clear error
        rather than masking the missing surface.

        Single-request semantics: this method does NOT key by prefix, does
        NOT look up prior handles, and does NOT emit any reuse / hit /
        eviction event. Each call increments ``counters.entries`` only.
        """

        if not model_id:
            raise ValueError("model_id must be non-empty")

        make_cache = self._resolve_make_prompt_cache(mlx_lm_module)
        cache_object = make_cache(model)

        with self._lock:
            self._next_cache_object_id += 1
            assigned_cache_object_id = self._next_cache_object_id

        handle = CachedRequestHandle(
            model_id=model_id,
            cache_object_id=assigned_cache_object_id,
            created_at=time.time(),
            cross_request_reuse_claimed=False,
        )
        with self._lock:
            self._handles_by_model.setdefault(model_id, []).append(handle)
            self._counters = CacheManagerCounters(
                entries=self._counters.entries + 1,
                resident_bytes=self._counters.resident_bytes,
                reuse_events=self._counters.reuse_events,
                hit_count=self._counters.hit_count,
                eviction_events=self._counters.eviction_events,
            )
        return handle, cache_object

    def release_for_request(self, handle: CachedRequestHandle) -> None:
        """Drop the handle reference for a completed single-request cache.

        Counters are not updated on release — release is incidental in
        single-request mode and does not represent an eviction event. The
        ``eviction_events`` counter is reserved for the future eviction
        extension point.
        """

        with self._lock:
            handles = self._handles_by_model.get(handle.model_id)
            if not handles:
                return
            try:
                handles.remove(handle)
            except ValueError:
                # Releasing a handle the manager does not know about is a
                # no-op in scaffold semantics. A future round may tighten
                # this into an error once cross-request keying is real.
                return
            if not handles:
                self._handles_by_model.pop(handle.model_id, None)

    # ------------------------------------------------------------------ #
    # Read-only observation surface
    # ------------------------------------------------------------------ #
    def counters(self) -> CacheManagerCounters:
        """Return a frozen snapshot of the current counter ledger."""

        with self._lock:
            return self._counters

    def status_dict(self) -> dict[str, Any]:
        """Return a status payload shape suitable for runtime status endpoints.

        The ``counters`` key exposes the live runtime-owned counter names
        directly; the archived cache_residency_evidence scaffold is no longer
        required as a translation layer.
        """

        with self._lock:
            counters_snapshot = self._counters
            handles_count_by_model = {
                model_id: len(handles)
                for model_id, handles in self._handles_by_model.items()
            }
        return {
            "manager_kind": "owlmlx_kv_cache_manager_scaffold",
            "single_request_semantics_enforced": True,
            "cross_request_reuse_claimed": False,
            "wired_into_native_backend": True,
            "counters": counters_snapshot.to_dict(),
            "handles_count_by_model": handles_count_by_model,
        }

    # ------------------------------------------------------------------ #
    # Private — defensive resolver mirroring the native backend pattern
    # ------------------------------------------------------------------ #
    @staticmethod
    def _resolve_make_prompt_cache(mlx_lm_module: Any) -> Any:
        """Walk ``mlx_lm_module.models.cache.make_prompt_cache`` defensively.

        Raises ``RuntimeError`` with a clear, actionable message when the
        upstream attribute path is missing or the resolved attribute is
        not callable. This is stricter than the equivalent helper in
        ``mlx_native_backend.py`` which returns ``None`` to allow silent
        cache-binding skip — the manager's contract is to fail loudly
        because callers reach the manager only when they intend to bind.
        """

        models_attr = getattr(mlx_lm_module, "models", None)
        if models_attr is None:
            raise RuntimeError(
                "cache_manager: mlx_lm module does not expose .models; "
                "cannot resolve make_prompt_cache"
            )
        cache_attr = getattr(models_attr, "cache", None)
        if cache_attr is None:
            raise RuntimeError(
                "cache_manager: mlx_lm.models does not expose .cache; "
                "cannot resolve make_prompt_cache"
            )
        candidate = getattr(cache_attr, "make_prompt_cache", None)
        if candidate is None or not callable(candidate):
            raise RuntimeError(
                "cache_manager: mlx_lm.models.cache.make_prompt_cache "
                "is missing or not callable"
            )
        return candidate


# --------------------------------------------------------------------------- #
# Future extension points (NOT implemented in this scaffold round)
#
# (a) Eviction policy
#     A future round may adopt ``mlx_lm.models.cache.LRUPromptCache.trim_to``
#     as the per-model eviction primitive. The ``eviction_events`` counter
#     is reserved for that surface; in scaffold it stays at zero.
#
# (b) Prefix reuse
#     A future round may key handles by tokenized prefix using
#     ``mlx_lm.models.cache.PromptTrie.search``. The ``reuse_events`` and
#     ``hit_count`` counters are reserved for that surface; in scaffold
#     they stay at zero, and ``CachedRequestHandle.cross_request_reuse_claimed``
#     stays ``False``.
#
# (c) Cross-request handle keying
#     A future round may introduce a stable handle key (model_id + prefix
#     hash + dtype + max_kv_size) so the manager can return an existing
#     handle instead of always producing a fresh one. Scaffold deliberately
#     does NOT pre-stub this method; introducing it requires a §1a-style
#     promotion walkthrough on the native MLX backend capability matrix.
#
# These extension points are documented in
# ``docs/source-of-truth/cache-manager-architecture.md`` §7. They are NOT
# code in this round.
# --------------------------------------------------------------------------- #


__all__ = [
    "CacheManager",
    "CacheManagerCounters",
    "CachedRequestHandle",
]
