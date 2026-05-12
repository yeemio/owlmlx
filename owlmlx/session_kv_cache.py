"""Experimental session-scoped KV cache store for the native MLX backend.

This module owns only explicit session cache reuse:

- callers must provide a session_id
- entries are scoped to one model_id and one session_id
- the feature is disabled unless OWLMLX_SESSION_CACHE_ENABLED=1
- pressure watermarks at yellow/red/fatal evict live entries and refuse reuse

It does not implement implicit prefix matching, paged KV, continuous batching,
or subprocess cache-handle transport.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


_TRUE_VALUES = {"1", "true", "yes", "on"}
_PRESSURE_WATERMARKS = {"yellow", "red", "fatal"}
_DEFAULT_TTL_S = 60.0
_DEFAULT_MAX_ENTRIES = 64


@dataclass(frozen=True, slots=True)
class SessionKVCacheEntrySnapshot:
    """Public snapshot for one session cache entry."""

    session_id: str
    model_id: str
    cache_object_id: int
    created_at_s: float
    last_used_at_s: float
    token_count: int
    byte_estimate: int
    hit_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "model_id": self.model_id,
            "cache_object_id": self.cache_object_id,
            "created_at_s": self.created_at_s,
            "last_used_at_s": self.last_used_at_s,
            "token_count": self.token_count,
            "byte_estimate": self.byte_estimate,
            "hit_count": self.hit_count,
        }


@dataclass(slots=True)
class _SessionKVCacheEntry:
    session_id: str
    model_id: str
    cache_object: Any
    cache_object_id: int
    created_at_s: float
    last_used_at_s: float
    token_count: int = 0
    byte_estimate: int = 0
    hit_count: int = 0

    def snapshot(self) -> SessionKVCacheEntrySnapshot:
        return SessionKVCacheEntrySnapshot(
            session_id=self.session_id,
            model_id=self.model_id,
            cache_object_id=self.cache_object_id,
            created_at_s=self.created_at_s,
            last_used_at_s=self.last_used_at_s,
            token_count=self.token_count,
            byte_estimate=self.byte_estimate,
            hit_count=self.hit_count,
        )


@dataclass(frozen=True, slots=True)
class SessionKVCacheCounters:
    """Monotonic counters for the experimental session cache."""

    entries_created: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    rejects: int = 0
    drops: int = 0
    expirations: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "entries_created": self.entries_created,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "rejects": self.rejects,
            "drops": self.drops,
            "expirations": self.expirations,
        }


@dataclass(frozen=True, slots=True)
class SessionKVCacheDecision:
    """Result of one session cache admission attempt."""

    decision: str
    reason_code: str
    cache_object: Any | None = None
    cache_object_id: int | None = None
    created: bool = False
    reused: bool = False
    evicted_count: int = 0


class SessionKVCacheStore:
    """LRU + TTL store for explicit session-scoped native KV cache handles."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        ttl_s: float = _DEFAULT_TTL_S,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
    ) -> None:
        self.enabled = bool(enabled)
        self.ttl_s = max(float(ttl_s), 0.0)
        self.max_entries = max(int(max_entries), 1)
        self._entries: dict[tuple[str, str], _SessionKVCacheEntry] = {}
        self._counters = SessionKVCacheCounters()
        self._lock = threading.Lock()
        self._next_cache_object_id = 0

    @classmethod
    def from_env(cls) -> "SessionKVCacheStore":
        return cls(
            enabled=_env_bool("OWLMLX_SESSION_CACHE_ENABLED", default=False),
            ttl_s=_env_float("OWLMLX_SESSION_CACHE_TTL_S", _DEFAULT_TTL_S),
            max_entries=_env_int("OWLMLX_SESSION_CACHE_MAX_ENTRIES", _DEFAULT_MAX_ENTRIES),
        )

    def acquire_for_request(
        self,
        *,
        session_id: str | None,
        model_id: str,
        make_cache: Callable[[], Any],
        now_s: float | None = None,
        watermark: str | None = None,
        token_count: int = 0,
        byte_estimate: int = 0,
    ) -> SessionKVCacheDecision:
        """Return a reusable session cache handle, or a refusal decision.

        ``make_cache`` is called only when the store is enabled, a non-empty
        session_id is present, pressure policy allows persistent cache reuse,
        and no valid entry already exists.
        """

        if not self.enabled:
            return SessionKVCacheDecision(
                decision="disabled",
                reason_code="feature_flag_disabled",
            )
        normalized_session_id = (session_id or "").strip()
        if not normalized_session_id:
            return SessionKVCacheDecision(
                decision="miss",
                reason_code="session_id_missing",
            )
        if not model_id:
            raise ValueError("model_id must be non-empty")

        now = time.time() if now_s is None else float(now_s)
        pressure = _normalize_watermark(watermark)
        if pressure in _PRESSURE_WATERMARKS:
            evicted = self.evict_lru_until(
                target_resident_bytes=0,
                now_s=now,
                reason_code=f"watermark_{pressure}",
            )
            with self._lock:
                self._counters = _replace_counter(
                    self._counters,
                    rejects=self._counters.rejects + 1,
                )
            return SessionKVCacheDecision(
                decision="rejected",
                reason_code=f"watermark_{pressure}",
                evicted_count=evicted,
            )

        key = (normalized_session_id, model_id)
        with self._lock:
            expired = self._expire_locked(now)
            entry = self._entries.get(key)
            if entry is not None:
                entry.last_used_at_s = now
                entry.hit_count += 1
                self._counters = _replace_counter(
                    self._counters,
                    hits=self._counters.hits + 1,
                    expirations=self._counters.expirations + expired,
                )
                return SessionKVCacheDecision(
                    decision="reuse",
                    reason_code="session_cache_hit",
                    cache_object=entry.cache_object,
                    cache_object_id=entry.cache_object_id,
                    reused=True,
                )
            counters_after_expiry = _replace_counter(
                self._counters,
                misses=self._counters.misses + 1,
                expirations=self._counters.expirations + expired,
            )
            self._counters = counters_after_expiry

        cache_object = make_cache()
        with self._lock:
            self._next_cache_object_id += 1
            cache_object_id = self._next_cache_object_id
            self._entries[key] = _SessionKVCacheEntry(
                session_id=normalized_session_id,
                model_id=model_id,
                cache_object=cache_object,
                cache_object_id=cache_object_id,
                created_at_s=now,
                last_used_at_s=now,
                token_count=max(int(token_count), 0),
                byte_estimate=max(int(byte_estimate), 0),
            )
            evicted_for_count = self._evict_to_max_entries_locked()
            self._counters = _replace_counter(
                self._counters,
                entries_created=self._counters.entries_created + 1,
                evictions=self._counters.evictions + evicted_for_count,
            )
        return SessionKVCacheDecision(
            decision="new",
            reason_code="session_cache_miss",
            cache_object=cache_object,
            cache_object_id=cache_object_id,
            created=True,
            evicted_count=evicted_for_count,
        )

    def drop_for_model(self, model_id: str) -> int:
        """Drop all session cache entries for a model before unload."""

        with self._lock:
            keys = [key for key in self._entries if key[1] == model_id]
            for key in keys:
                self._entries.pop(key, None)
            if keys:
                self._counters = _replace_counter(
                    self._counters,
                    drops=self._counters.drops + len(keys),
                )
            return len(keys)

    def evict_lru_until(
        self,
        *,
        target_resident_bytes: int,
        now_s: float | None = None,
        reason_code: str = "lru_pressure",
    ) -> int:
        """Evict least-recently-used entries until estimated bytes fit.

        ``target_resident_bytes=0`` drops all session cache entries. The
        reason_code is accepted for call-site readability; counters only
        publish aggregate evictions in this first experimental slice.
        """

        _ = reason_code
        now = time.time() if now_s is None else float(now_s)
        with self._lock:
            expired = self._expire_locked(now)
            target = max(int(target_resident_bytes), 0)
            evicted = 0
            if target == 0:
                evicted = len(self._entries)
                self._entries.clear()
            while self._entries and self._resident_bytes_locked() > target:
                key = min(
                    self._entries,
                    key=lambda candidate: self._entries[candidate].last_used_at_s,
                )
                self._entries.pop(key, None)
                evicted += 1
            if evicted or expired:
                self._counters = _replace_counter(
                    self._counters,
                    evictions=self._counters.evictions + evicted,
                    expirations=self._counters.expirations + expired,
                )
            return evicted

    def status_dict(self) -> dict[str, Any]:
        with self._lock:
            entries = [entry.snapshot().to_dict() for entry in self._entries.values()]
            counters = self._counters
            resident_bytes = self._resident_bytes_locked()
        return {
            "surface": "owlmlx.session_kv_cache",
            "capability_label": "experimental",
            "enabled": self.enabled,
            "scope": "native_backend_explicit_session_id_only",
            "default_enabled": False,
            "ttl_s": self.ttl_s,
            "max_entries": self.max_entries,
            "active_entries": len(entries),
            "active_sessions": len({entry["session_id"] for entry in entries}),
            "resident_bytes_estimate": resident_bytes,
            "counters": counters.to_dict(),
            "entries": sorted(
                entries,
                key=lambda entry: (entry["model_id"], entry["session_id"]),
            ),
            "non_goals": [
                "implicit_prefix_matching",
                "paged_kv",
                "continuous_batching",
                "subprocess_cache_handle_transport",
            ],
        }

    def _expire_locked(self, now_s: float) -> int:
        if self.ttl_s <= 0:
            expired_keys = list(self._entries)
        else:
            expired_keys = [
                key
                for key, entry in self._entries.items()
                if now_s - entry.last_used_at_s > self.ttl_s
            ]
        for key in expired_keys:
            self._entries.pop(key, None)
        return len(expired_keys)

    def _evict_to_max_entries_locked(self) -> int:
        evicted = 0
        while len(self._entries) > self.max_entries:
            key = min(
                self._entries,
                key=lambda candidate: self._entries[candidate].last_used_at_s,
            )
            self._entries.pop(key, None)
            evicted += 1
        return evicted

    def _resident_bytes_locked(self) -> int:
        return sum(entry.byte_estimate for entry in self._entries.values())


def _normalize_watermark(watermark: str | None) -> str | None:
    if watermark is None:
        return None
    normalized = str(watermark).strip().lower()
    return normalized or None


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE_VALUES


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _replace_counter(counters: SessionKVCacheCounters, **updates: int) -> SessionKVCacheCounters:
    values = counters.to_dict()
    values.update(updates)
    return SessionKVCacheCounters(**values)


__all__ = [
    "SessionKVCacheCounters",
    "SessionKVCacheDecision",
    "SessionKVCacheEntrySnapshot",
    "SessionKVCacheStore",
]
