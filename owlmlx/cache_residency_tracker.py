"""Cache residency tracker — runtime-owned policy surface for Campaign 2.

Tracks per-model lifecycle on the active serving path:
  resident (loaded, not yet used) → hot (recently used) → evictable (idle)

Records every unload as a CacheReleaseEvent in a bounded release ledger.
This surface is injected by RuntimeKernel at load / generate / unload
boundaries and is independent of MLX cache objects or KV cache primitives.

State classification:
  "resident"  — model is loaded; no use recorded yet (or cooling down between
                hot_window_s and evictable_idle_s)
  "hot"        — last use was within hot_window_s seconds of now
  "evictable"  — last use was more than evictable_idle_s seconds ago

Release reasons: "manual_unload" | "pressure_eviction" | "ttl_expiry"
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class CacheResidencyEntry:
    """Immutable snapshot of a single model's residency state."""

    model_id: str
    state: str          # "resident" | "hot" | "evictable"
    loaded_at_s: float
    last_used_s: float | None
    use_count: int


@dataclass(frozen=True, slots=True)
class CacheReleaseEvent:
    """Immutable record of a model being unloaded from the residency tracker."""

    model_id: str
    released_at_s: float
    reason: str         # "manual_unload" | "pressure_eviction" | "ttl_expiry"
    use_count_at_release: int
    seq: int


@dataclass(slots=True)
class _Entry:
    model_id: str
    loaded_at_s: float
    last_used_s: float | None
    use_count: int


_LEDGER_MAX = 1024


class CacheResidencyTracker:
    """Runtime-owned residency lifecycle tracker.

    Thread-safe. Clock is injectable for testing.
    """

    def __init__(
        self,
        *,
        hot_window_s: float = 60.0,
        evictable_idle_s: float = 300.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._hot_window_s = hot_window_s
        self._evictable_idle_s = evictable_idle_s
        self._clock: Callable[[], float] = clock if clock is not None else time.monotonic
        self._lock = threading.Lock()
        self._entries: dict[str, _Entry] = {}
        self._release_ledger: list[CacheReleaseEvent] = []
        self._seq = 0

    # ------------------------------------------------------------------ #
    # Lifecycle write API
    # ------------------------------------------------------------------ #

    def record_load(self, model_id: str, *, now_s: float | None = None) -> None:
        """Record a successful model load — initialises residency entry."""
        ts = float(now_s) if now_s is not None else self._clock()
        with self._lock:
            self._entries[model_id] = _Entry(
                model_id=model_id,
                loaded_at_s=ts,
                last_used_s=None,
                use_count=0,
            )

    def record_use(self, model_id: str, *, now_s: float | None = None) -> None:
        """Record a completed generation — bumps use_count and last_used_s."""
        ts = float(now_s) if now_s is not None else self._clock()
        with self._lock:
            entry = self._entries.get(model_id)
            if entry is None:
                return
            entry.last_used_s = ts
            entry.use_count += 1

    def record_unload(
        self,
        model_id: str,
        *,
        reason: str = "manual_unload",
        now_s: float | None = None,
    ) -> None:
        """Record an unload — removes entry, appends CacheReleaseEvent to ledger."""
        ts = float(now_s) if now_s is not None else self._clock()
        with self._lock:
            entry = self._entries.pop(model_id, None)
            use_count = entry.use_count if entry is not None else 0
            self._seq += 1
            event = CacheReleaseEvent(
                model_id=model_id,
                released_at_s=ts,
                reason=reason,
                use_count_at_release=use_count,
                seq=self._seq,
            )
            if len(self._release_ledger) >= _LEDGER_MAX:
                self._release_ledger.pop(0)
            self._release_ledger.append(event)

    # ------------------------------------------------------------------ #
    # Read-only observation surface
    # ------------------------------------------------------------------ #

    def residency_snapshot(self, *, now_s: float | None = None) -> dict[str, CacheResidencyEntry]:
        """Return a dict of model_id → CacheResidencyEntry with classified states."""
        ts = float(now_s) if now_s is not None else self._clock()
        with self._lock:
            return {
                model_id: CacheResidencyEntry(
                    model_id=model_id,
                    state=_classify_state(entry, ts, self._hot_window_s, self._evictable_idle_s),
                    loaded_at_s=entry.loaded_at_s,
                    last_used_s=entry.last_used_s,
                    use_count=entry.use_count,
                )
                for model_id, entry in self._entries.items()
            }

    def release_ledger_snapshot(self) -> list[CacheReleaseEvent]:
        """Return a copy of the release ledger."""
        with self._lock:
            return list(self._release_ledger)

    def status_dict(self, *, now_s: float | None = None) -> dict[str, Any]:
        """Return a JSON-ready status payload for inclusion in RuntimeKernel.status_dict()."""
        ts = float(now_s) if now_s is not None else self._clock()
        with self._lock:
            entries_out = {
                model_id: {
                    "model_id": model_id,
                    "state": _classify_state(entry, ts, self._hot_window_s, self._evictable_idle_s),
                    "loaded_at_s": entry.loaded_at_s,
                    "last_used_s": entry.last_used_s,
                    "use_count": entry.use_count,
                }
                for model_id, entry in self._entries.items()
            }
            ledger_out = [
                {
                    "model_id": ev.model_id,
                    "released_at_s": ev.released_at_s,
                    "reason": ev.reason,
                    "use_count_at_release": ev.use_count_at_release,
                    "seq": ev.seq,
                }
                for ev in self._release_ledger[-32:]
            ]
            total = self._seq
        return {
            "surface": "owlmlx.cache_residency_tracker",
            "entry_count": len(entries_out),
            "entries": entries_out,
            "release_ledger_total": total,
            "release_ledger": ledger_out,
        }


# ---------------------------------------------------------------------------
# Module-level helper (no self needed — pure function on frozen params)
# ---------------------------------------------------------------------------

def _classify_state(
    entry: _Entry,
    now_s: float,
    hot_window_s: float,
    evictable_idle_s: float,
) -> str:
    if entry.last_used_s is None:
        return "resident"
    idle_s = now_s - entry.last_used_s
    if idle_s <= hot_window_s:
        return "hot"
    if idle_s >= evictable_idle_s:
        return "evictable"
    return "resident"


__all__ = [
    "CacheResidencyTracker",
    "CacheResidencyEntry",
    "CacheReleaseEvent",
]
