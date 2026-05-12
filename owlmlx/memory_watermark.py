"""Memory watermark + watermark action — public landmark types for owlmlx.

This module makes PR #649's vocabulary first-class in owlmlx. The four-level
watermark (GREEN < 65% < YELLOW < 80% < RED < 90% < FATAL) is the canonical
public summary of memory pressure. It maps onto the finer-grained internal
pressure classifications produced by `memory_pressure_contract` without
changing those strings (they remain part of the published HTTP contract).

Reference: https://github.com/jundot/omlx/pull/649

Design boundary:
    - `MemoryWatermark` / `WatermarkAction` are *display + API* concepts.
    - `pressure_classification` strings in `memory_pressure_contract` remain
      the runtime decision keys. This module is a stable, narrow facade.
    - Thresholds (65 / 80 / 90 %) are hardcoded here; configurable thresholds
      were called out as a "known limitation" in PR #649 and remain so until
      we have hardware-diverse evidence justifying tuning.
"""

from __future__ import annotations

from enum import Enum
from typing import Mapping


class MemoryWatermark(Enum):
    """Four-level memory pressure watermark.

    Boundaries (projected memory utilization):
        GREEN   < 65 %
        YELLOW  65 – 80 %
        RED     80 – 90 %
        FATAL   ≥ 90 %
        UNKNOWN insufficient signal
    """

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    FATAL = "fatal"
    UNKNOWN = "unknown"

    @classmethod
    def from_utilization(cls, utilization: float | None) -> "MemoryWatermark":
        """Map a [0, ∞) projected utilization ratio to a watermark level.

        `None` or non-finite → UNKNOWN. Values are not clamped; > 1.0 lands
        in FATAL by design (utilization can exceed budget transiently).
        """
        if utilization is None:
            return cls.UNKNOWN
        try:
            u = float(utilization)
        except (TypeError, ValueError):
            return cls.UNKNOWN
        if u != u:  # NaN
            return cls.UNKNOWN
        if u >= GREEN_CEILING and u < YELLOW_CEILING:
            return cls.YELLOW
        if u < GREEN_CEILING:
            return cls.GREEN
        if u < RED_CEILING:
            return cls.RED
        return cls.FATAL

    @classmethod
    def from_classification(cls, classification: str | None) -> "MemoryWatermark":
        """Map a `pressure_classification` string to a watermark level.

        Unknown / missing inputs return UNKNOWN. This is the bridge from
        `memory_pressure_contract`'s finer-grained internal vocabulary to
        the PR #649-shaped public summary.
        """
        if classification is None:
            return cls.UNKNOWN
        return _CLASSIFICATION_TO_WATERMARK.get(classification, cls.UNKNOWN)


class WatermarkAction(Enum):
    """Recommended runtime action for a given watermark level.

    Encodes the action policy described in PR #649:
        - GREEN  → PROCEED with the load.
        - YELLOW → EVICT_LRU one cached model at a time, re-check.
        - RED    → AGGRESSIVE_EVICT (multiple LRU + reclaim cache).
        - FATAL  → REFUSE_LOAD.
        - UNKNOWN→ DEFER (treat as YELLOW until signal arrives).
    """

    PROCEED = "proceed"
    EVICT_LRU = "evict_lru"
    AGGRESSIVE_EVICT = "aggressive_evict"
    REFUSE_LOAD = "refuse_load"
    DEFER = "defer"

    @classmethod
    def for_watermark(cls, watermark: MemoryWatermark) -> "WatermarkAction":
        return _WATERMARK_TO_ACTION[watermark]


# Thresholds. Public so callers can present them in diagnostics.
GREEN_CEILING: float = 0.65
YELLOW_CEILING: float = 0.80
RED_CEILING: float = 0.90


WATERMARK_THRESHOLDS: Mapping[MemoryWatermark, float | None] = {
    MemoryWatermark.GREEN: GREEN_CEILING,
    MemoryWatermark.YELLOW: YELLOW_CEILING,
    MemoryWatermark.RED: RED_CEILING,
    MemoryWatermark.FATAL: None,
    MemoryWatermark.UNKNOWN: None,
}


_CLASSIFICATION_TO_WATERMARK: Mapping[str, MemoryWatermark] = {
    "within_budget": MemoryWatermark.GREEN,
    "near_budget": MemoryWatermark.YELLOW,
    "over_budget": MemoryWatermark.RED,
    "cooldown_barrier": MemoryWatermark.FATAL,
    "host_pressure_barrier": MemoryWatermark.FATAL,
    "unknown": MemoryWatermark.UNKNOWN,
    "insufficient_signal": MemoryWatermark.UNKNOWN,
}


_WATERMARK_TO_ACTION: Mapping[MemoryWatermark, WatermarkAction] = {
    MemoryWatermark.GREEN: WatermarkAction.PROCEED,
    MemoryWatermark.YELLOW: WatermarkAction.EVICT_LRU,
    MemoryWatermark.RED: WatermarkAction.AGGRESSIVE_EVICT,
    MemoryWatermark.FATAL: WatermarkAction.REFUSE_LOAD,
    MemoryWatermark.UNKNOWN: WatermarkAction.DEFER,
}


__all__ = [
    "MemoryWatermark",
    "WatermarkAction",
    "GREEN_CEILING",
    "YELLOW_CEILING",
    "RED_CEILING",
    "WATERMARK_THRESHOLDS",
]
