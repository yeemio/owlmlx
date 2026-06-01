"""Experimental session-scoped KV cache store for the native MLX backend.

This module owns explicit session cache reuse plus an opt-in automatic prefix
scope for native streaming:

- the feature is disabled unless OWLMLX_SESSION_CACHE_ENABLED=1
- explicit callers provide a session_id
- automatic no-header reuse additionally requires
  OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1
- entries are scoped to one model_id and either one session_id or the automatic
  runtime prefix scope
- pressure watermarks at yellow/red/fatal evict live entries and refuse reuse

It does not implement default-on implicit prefix matching, paged KV, continuous
batching, or subprocess cache-handle transport.
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
_DEFAULT_MAX_PROMPT_TOKENS = 0
_DEFAULT_MAX_RESIDENT_BYTES = 0
_DEFAULT_AUTO_PREFIX_ENABLED = False


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
    byte_estimate_mode: str
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
            "byte_estimate_mode": self.byte_estimate_mode,
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
    prompt_tokens: tuple[int, ...] = ()
    token_count: int = 0
    byte_estimate: int = 0
    byte_estimate_mode: str = "unset"
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
            byte_estimate_mode=self.byte_estimate_mode,
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
    window_bypasses: int = 0
    window_evictions: int = 0
    trim_bypasses: int = 0
    trim_evictions: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "entries_created": self.entries_created,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "rejects": self.rejects,
            "drops": self.drops,
            "expirations": self.expirations,
            "window_bypasses": self.window_bypasses,
            "window_evictions": self.window_evictions,
            "trim_bypasses": self.trim_bypasses,
            "trim_evictions": self.trim_evictions,
        }


@dataclass(frozen=True, slots=True)
class SessionKVCacheDecision:
    """Result of one session cache admission attempt."""

    decision: str
    reason_code: str
    cache_object: Any | None = None
    cache_object_id: int | None = None
    suffix_tokens: tuple[int, ...] | None = None
    common_prefix_token_count: int = 0
    previous_prompt_token_count: int = 0
    created: bool = False
    reused: bool = False
    evicted_count: int = 0


@dataclass(frozen=True, slots=True)
class PrefixCacheCandidateDecision:
    """Read-only decision for future automatic prefix-cache reuse.

    This decision intentionally carries no cache object. B-2.1 only answers
    whether a request is safe to consider for prefix reuse in a later stage.
    """

    eligible: bool
    reason_code: str
    common_prefix_token_count: int = 0
    previous_prompt_token_count: int = 0
    requested_prompt_token_count: int = 0
    suffix_token_count: int = 0
    needs_trim: bool = False


def classify_prefix_cache_candidate(
    *,
    existing_model_id: str,
    requested_model_id: str,
    existing_prompt_tokens: tuple[int, ...],
    requested_prompt_tokens: tuple[int, ...],
    existing_runtime_profile_id: str | None = None,
    requested_runtime_profile_id: str | None = None,
    existing_isolation_scope: str | None = None,
    requested_isolation_scope: str | None = None,
    trim_available: bool = False,
) -> PrefixCacheCandidateDecision:
    """Classify prefix-cache eligibility without exposing a cache handle."""

    previous_count = len(existing_prompt_tokens)
    requested_count = len(requested_prompt_tokens)
    if existing_model_id != requested_model_id:
        return PrefixCacheCandidateDecision(
            eligible=False,
            reason_code="different_model",
            previous_prompt_token_count=previous_count,
            requested_prompt_token_count=requested_count,
        )
    if existing_runtime_profile_id != requested_runtime_profile_id:
        return PrefixCacheCandidateDecision(
            eligible=False,
            reason_code="different_runtime_profile",
            previous_prompt_token_count=previous_count,
            requested_prompt_token_count=requested_count,
        )
    if existing_isolation_scope != requested_isolation_scope:
        return PrefixCacheCandidateDecision(
            eligible=False,
            reason_code="unsafe_isolation_scope",
            previous_prompt_token_count=previous_count,
            requested_prompt_token_count=requested_count,
        )

    common_prefix_count = _common_prefix_len(
        existing_prompt_tokens,
        requested_prompt_tokens,
    )
    needs_trim = common_prefix_count < previous_count
    suffix_count = max(requested_count - common_prefix_count, 0)
    if common_prefix_count == 0 and (previous_count > 0 or requested_count > 0):
        return PrefixCacheCandidateDecision(
            eligible=False,
            reason_code="not_token_prefix",
            common_prefix_token_count=common_prefix_count,
            previous_prompt_token_count=previous_count,
            requested_prompt_token_count=requested_count,
            suffix_token_count=suffix_count,
            needs_trim=needs_trim,
        )
    if needs_trim and not trim_available:
        return PrefixCacheCandidateDecision(
            eligible=False,
            reason_code="trim_unavailable_for_edit",
            common_prefix_token_count=common_prefix_count,
            previous_prompt_token_count=previous_count,
            requested_prompt_token_count=requested_count,
            suffix_token_count=suffix_count,
            needs_trim=True,
        )
    return PrefixCacheCandidateDecision(
        eligible=True,
        reason_code="same_model_token_prefix",
        common_prefix_token_count=common_prefix_count,
        previous_prompt_token_count=previous_count,
        requested_prompt_token_count=requested_count,
        suffix_token_count=suffix_count,
        needs_trim=needs_trim,
    )


class SessionKVCacheStore:
    """LRU + TTL store for explicit session-scoped native KV cache handles."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        ttl_s: float = _DEFAULT_TTL_S,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
        max_prompt_tokens: int = _DEFAULT_MAX_PROMPT_TOKENS,
        max_resident_bytes: int = _DEFAULT_MAX_RESIDENT_BYTES,
        automatic_prefix_enabled: bool = _DEFAULT_AUTO_PREFIX_ENABLED,
    ) -> None:
        self.enabled = bool(enabled)
        self.ttl_s = max(float(ttl_s), 0.0)
        self.max_entries = max(int(max_entries), 1)
        self.max_prompt_tokens = max(int(max_prompt_tokens), 0)
        self.max_resident_bytes = max(int(max_resident_bytes), 0)
        self.automatic_prefix_enabled = bool(automatic_prefix_enabled)
        self._entries: dict[tuple[str, str], _SessionKVCacheEntry] = {}
        self._counters = SessionKVCacheCounters()
        self._last_drop_event: dict[str, Any] | None = None
        self._last_bypass_event: dict[str, Any] | None = None
        self._lock = threading.Lock()
        self._next_cache_object_id = 0

    @classmethod
    def from_env(cls) -> "SessionKVCacheStore":
        return cls(
            enabled=_env_bool("OWLMLX_SESSION_CACHE_ENABLED", default=False),
            ttl_s=_env_float("OWLMLX_SESSION_CACHE_TTL_S", _DEFAULT_TTL_S),
            max_entries=_env_int("OWLMLX_SESSION_CACHE_MAX_ENTRIES", _DEFAULT_MAX_ENTRIES),
            max_prompt_tokens=_env_int(
                "OWLMLX_SESSION_CACHE_MAX_PROMPT_TOKENS",
                _DEFAULT_MAX_PROMPT_TOKENS,
            ),
            max_resident_bytes=_env_int(
                "OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES",
                _DEFAULT_MAX_RESIDENT_BYTES,
            ),
            automatic_prefix_enabled=_env_bool(
                "OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED",
                default=_DEFAULT_AUTO_PREFIX_ENABLED,
            ),
        )

    def acquire_for_request(
        self,
        *,
        session_id: str | None,
        model_id: str,
        make_cache: Callable[[], Any],
        now_s: float | None = None,
        watermark: str | None = None,
        prompt_tokens: tuple[int, ...] | None = None,
        token_count: int = 0,
        byte_estimate: int = 0,
        byte_estimate_mode: str | None = None,
        strict_prefix_reuse: bool = False,
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
        requested_prompt_tokens = prompt_tokens or ()
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
        new_reason_code = "session_cache_miss"
        if self._prompt_exceeds_window(requested_prompt_tokens):
            with self._lock:
                expired = self._expire_locked(now)
                removed = self._entries.pop(key, None)
                if removed is not None:
                    self._last_bypass_event = _session_cache_event(
                        reason_code="prompt_token_window_exceeded",
                        session_id=normalized_session_id,
                        model_id=model_id,
                        removed=removed,
                        detail={
                            "requested_prompt_token_count": len(requested_prompt_tokens),
                            "max_prompt_tokens": self.max_prompt_tokens,
                        },
                    )
                self._counters = _replace_counter(
                    self._counters,
                    expirations=self._counters.expirations + expired,
                    window_bypasses=self._counters.window_bypasses + 1,
                    window_evictions=(
                        self._counters.window_evictions + (1 if removed is not None else 0)
                    ),
                )
            return SessionKVCacheDecision(
                decision="bypassed",
                reason_code="prompt_token_window_exceeded",
                evicted_count=1 if removed is not None else 0,
            )

        with self._lock:
            expired = self._expire_locked(now)
            entry = self._entries.get(key)
            if entry is not None:
                candidate = classify_prefix_cache_candidate(
                    existing_model_id=model_id,
                    requested_model_id=model_id,
                    existing_prompt_tokens=entry.prompt_tokens,
                    requested_prompt_tokens=requested_prompt_tokens,
                    existing_runtime_profile_id="explicit_session",
                    requested_runtime_profile_id="explicit_session",
                    existing_isolation_scope=normalized_session_id,
                    requested_isolation_scope=normalized_session_id,
                    trim_available=True,
                )
                if strict_prefix_reuse and not candidate.eligible:
                    removed = self._entries.pop(key, None)
                    if removed is not None:
                        self._last_bypass_event = _session_cache_event(
                            reason_code=(
                                f"auto_prefix_ineligible_{candidate.reason_code}"
                            ),
                            session_id=normalized_session_id,
                            model_id=model_id,
                            removed=removed,
                            detail={
                                "candidate_reason_code": candidate.reason_code,
                                "common_prefix_token_count": (
                                    candidate.common_prefix_token_count
                                ),
                                "previous_prompt_token_count": (
                                    candidate.previous_prompt_token_count
                                ),
                                "requested_prompt_token_count": (
                                    candidate.requested_prompt_token_count
                                ),
                                "suffix_token_count": candidate.suffix_token_count,
                                "needs_trim": candidate.needs_trim,
                            },
                        )
                    self._counters = _replace_counter(
                        self._counters,
                        trim_bypasses=self._counters.trim_bypasses + 1,
                        trim_evictions=(
                            self._counters.trim_evictions
                            + (1 if removed is not None else 0)
                        ),
                    )
                    new_reason_code = (
                        f"auto_prefix_ineligible_{candidate.reason_code}"
                    )
                else:
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
                        suffix_tokens=(
                            requested_prompt_tokens[candidate.common_prefix_token_count:]
                            if requested_prompt_tokens
                            else None
                        ),
                        common_prefix_token_count=candidate.common_prefix_token_count,
                        previous_prompt_token_count=(
                            candidate.previous_prompt_token_count
                        ),
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
                byte_estimate_mode=(
                    _normalize_byte_estimate_mode(byte_estimate_mode)
                    if int(byte_estimate) > 0
                    else "unset"
                ),
            )
            evicted_for_count = self._evict_to_max_entries_locked()
            evicted_for_resident = self._evict_to_max_resident_locked()
            evicted_total = evicted_for_count + evicted_for_resident
            self._counters = _replace_counter(
                self._counters,
                entries_created=self._counters.entries_created + 1,
                evictions=self._counters.evictions + evicted_total,
            )
        return SessionKVCacheDecision(
            decision="new",
            reason_code=new_reason_code,
            cache_object=cache_object,
            cache_object_id=cache_object_id,
            suffix_tokens=requested_prompt_tokens if requested_prompt_tokens else None,
            created=True,
            evicted_count=evicted_total,
        )

    def remember_prompt(
        self,
        *,
        session_id: str | None,
        model_id: str,
        prompt_tokens: tuple[int, ...],
        token_count: int | None = None,
        byte_estimate: int | None = None,
        byte_estimate_delta: int | None = None,
        byte_estimate_mode: str | None = None,
    ) -> bool:
        """Persist the prompt-token prefix represented by a session entry."""

        normalized_session_id = (session_id or "").strip()
        if not normalized_session_id or not model_id:
            return False
        normalized_prompt_tokens = tuple(prompt_tokens)
        with self._lock:
            entry = self._entries.get((normalized_session_id, model_id))
            if entry is None:
                return False
            if self._prompt_exceeds_window(normalized_prompt_tokens):
                removed = self._entries.pop((normalized_session_id, model_id), None)
                if removed is not None:
                    self._last_bypass_event = _session_cache_event(
                        reason_code="prompt_token_window_exceeded_after_generation",
                        session_id=normalized_session_id,
                        model_id=model_id,
                        removed=removed,
                        detail={
                            "remembered_prompt_token_count": len(
                                normalized_prompt_tokens
                            ),
                            "max_prompt_tokens": self.max_prompt_tokens,
                        },
                    )
                self._counters = _replace_counter(
                    self._counters,
                    window_bypasses=self._counters.window_bypasses + 1,
                    window_evictions=self._counters.window_evictions + 1,
                )
                return True
            entry.prompt_tokens = normalized_prompt_tokens
            if token_count is not None:
                entry.token_count = max(int(token_count), 0)
            if byte_estimate is not None:
                entry.byte_estimate = max(int(byte_estimate), 0)
                entry.byte_estimate_mode = _normalize_byte_estimate_mode(
                    byte_estimate_mode,
                    default="caller_supplied_absolute",
                )
            if byte_estimate_delta is not None:
                entry.byte_estimate = max(
                    entry.byte_estimate + int(byte_estimate_delta),
                    0,
                )
                if entry.byte_estimate_mode in {"unset", ""}:
                    entry.byte_estimate_mode = (
                        "positive_active_memory_delta_upper_bound"
                    )
            evicted_for_resident = self._evict_to_max_resident_locked()
            if evicted_for_resident:
                self._counters = _replace_counter(
                    self._counters,
                    evictions=self._counters.evictions + evicted_for_resident,
                )
            return True

    def drop_for_session_model(
        self,
        *,
        session_id: str | None,
        model_id: str,
        reason_code: str = "unsafe_session_cache_reuse",
        detail: dict[str, Any] | None = None,
    ) -> bool:
        """Drop one session/model cache entry after an aborted or unsafe reuse."""

        normalized_session_id = (session_id or "").strip()
        if not normalized_session_id or not model_id:
            return False
        with self._lock:
            removed = self._entries.pop((normalized_session_id, model_id), None)
            if removed is None:
                return False
            self._last_drop_event = _session_cache_event(
                reason_code=reason_code,
                session_id=normalized_session_id,
                model_id=model_id,
                removed=removed,
                detail=detail,
            )
            self._counters = _replace_counter(
                self._counters,
                drops=self._counters.drops + 1,
            )
            return True

    def bypass_for_session_model(
        self,
        *,
        session_id: str | None,
        model_id: str,
        reason_code: str,
        detail: dict[str, Any] | None = None,
    ) -> bool:
        """Evict one reusable entry before generation and fall back to fresh cache."""

        normalized_session_id = (session_id or "").strip()
        if not normalized_session_id or not model_id:
            return False
        with self._lock:
            removed = self._entries.pop((normalized_session_id, model_id), None)
            self._counters = _replace_counter(
                self._counters,
                trim_bypasses=self._counters.trim_bypasses + 1,
                trim_evictions=(
                    self._counters.trim_evictions + (1 if removed is not None else 0)
                ),
            )
            if removed is None:
                return False
            self._last_bypass_event = _session_cache_event(
                reason_code=reason_code,
                session_id=normalized_session_id,
                model_id=model_id,
                removed=removed,
                detail=detail,
            )
            return True

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
            resident_modes = self._resident_modes_locked()
            resident_mode = _summarize_resident_mode(resident_modes)
            last_drop_event = (
                dict(self._last_drop_event)
                if self._last_drop_event is not None
                else None
            )
            last_bypass_event = (
                dict(self._last_bypass_event)
                if self._last_bypass_event is not None
                else None
            )
        return {
            "surface": "owlmlx.session_kv_cache",
            "capability_label": "experimental",
            "enabled": self.enabled,
            "scope": (
                "native_backend_explicit_session_id_or_opt_in_auto_prefix"
                if self.automatic_prefix_enabled
                else "native_backend_explicit_session_id_only"
            ),
            "default_enabled": False,
            "ttl_s": self.ttl_s,
            "max_entries": self.max_entries,
            "max_prompt_tokens": self.max_prompt_tokens,
            "max_resident_bytes": self.max_resident_bytes,
            "automatic_prefix_enabled": self.automatic_prefix_enabled,
            "prompt_window_policy": (
                "bypass_and_evict_over_limit"
                if self.max_prompt_tokens > 0
                else "unbounded"
            ),
            "resident_pressure_policy": (
                "lru_evict_over_limit"
                if self.max_resident_bytes > 0
                else "unbounded"
            ),
            "active_entries": len(entries),
            "active_sessions": len({entry["session_id"] for entry in entries}),
            "resident_bytes_estimate": resident_bytes,
            "resident_bytes_estimate_mode": resident_mode,
            "resident_bytes_estimate_modes": resident_modes,
            "resident_bytes_estimate_used_for_promotion_gate": False,
            "counters": counters.to_dict(),
            "last_drop_event": last_drop_event,
            "last_bypass_event": last_bypass_event,
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

    def _evict_to_max_resident_locked(self) -> int:
        if self.max_resident_bytes <= 0:
            return 0
        evicted = 0
        while self._entries and self._resident_bytes_locked() > self.max_resident_bytes:
            key = min(
                self._entries,
                key=lambda candidate: self._entries[candidate].last_used_at_s,
            )
            self._entries.pop(key, None)
            evicted += 1
        return evicted

    def _resident_bytes_locked(self) -> int:
        return sum(entry.byte_estimate for entry in self._entries.values())

    def _resident_modes_locked(self) -> dict[str, int]:
        modes: dict[str, int] = {}
        for entry in self._entries.values():
            mode = entry.byte_estimate_mode or "unset"
            modes[mode] = modes.get(mode, 0) + 1
        return dict(sorted(modes.items()))

    def _prompt_exceeds_window(self, prompt_tokens: tuple[int, ...]) -> bool:
        return self.max_prompt_tokens > 0 and len(prompt_tokens) > self.max_prompt_tokens


def _normalize_watermark(watermark: str | None) -> str | None:
    if watermark is None:
        return None
    normalized = str(watermark).strip().lower()
    return normalized or None


def _common_prefix_len(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    count = 0
    for a, b in zip(left, right):
        if a != b:
            break
        count += 1
    return count


def _normalize_byte_estimate_mode(
    mode: str | None,
    *,
    default: str = "caller_supplied",
) -> str:
    normalized = str(mode or "").strip()
    return normalized or default


def _summarize_resident_mode(modes: dict[str, int]) -> str:
    meaningful = {mode for mode, count in modes.items() if count > 0 and mode != "unset"}
    if not meaningful:
        return "none"
    if len(meaningful) == 1:
        return next(iter(meaningful))
    return "mixed"


def _session_cache_event(
    *,
    reason_code: str,
    session_id: str,
    model_id: str,
    removed: _SessionKVCacheEntry,
    detail: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "reason_code": str(reason_code or "session_cache_policy_event"),
        "session_id": session_id,
        "model_id": model_id,
        "cache_object_id": removed.cache_object_id,
        "entry_token_count": removed.token_count,
        "entry_prompt_token_count": len(removed.prompt_tokens),
        "time_s": time.time(),
        "detail": dict(detail or {}),
    }


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
