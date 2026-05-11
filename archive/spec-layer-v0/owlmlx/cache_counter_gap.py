"""Runtime-owned exact residual gap for cache/scheduler depth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .cache_closure_rung import CacheClosureRung, build_cache_closure_rung


@dataclass(frozen=True, slots=True)
class CacheCounterGap:
    """Exact residual cache gap after active runtime observations are frozen."""

    closure: CacheClosureRung
    status: str
    counter_gap_rung: str
    residual_blocker: str | None
    recommended_next_step: str
    observed_runtime_behavior_frozen: bool
    missing_runtime_counters: tuple[str, ...]
    visible_runtime_counters: tuple[str, ...]


def build_cache_counter_gap(
    *,
    closure: CacheClosureRung | None = None,
    backend_observations: Mapping[str, Any] | None = None,
) -> CacheCounterGap:
    """Build the exact residual cache/scheduler gap."""

    cache_closure = (
        closure if isinstance(closure, CacheClosureRung) else build_cache_closure_rung()
    )
    observations = dict(backend_observations or {})
    counter_visibility = dict(observations.get("cache_counter_visibility", {}))

    visible_runtime_counters: list[str] = []
    missing_runtime_counters: list[str] = []
    for field, label in (
        ("residency", "residency_counter"),
        ("reuse", "reuse_counter"),
        ("eviction", "eviction_counter"),
    ):
        if bool(counter_visibility.get(field)):
            visible_runtime_counters.append(label)
        else:
            missing_runtime_counters.append(label)

    observed_runtime_behavior_frozen = bool(
        observations.get("persistent_child_reuse_visible")
    ) and cache_closure.closure_rung == "repeatability_visible"

    counter_gap_rung = "observation_gap_open"
    residual_blocker = (
        "cache runtime observations are still too weak to freeze the remaining counter-grade cache/scheduler gap"
    )
    recommended_next_step = (
        "finish freezing active runtime cache observations before reducing the remaining counter-grade gap"
    )

    if observed_runtime_behavior_frozen:
        missing = ", ".join(missing_runtime_counters) if missing_runtime_counters else "no direct counters"
        counter_gap_rung = "counter_gap_exact"
        residual_blocker = (
            f"remaining cache gap is now exact: missing {missing}, scheduler depth remains serial_single_worker, and TurboQuant readiness is still below controlled validation"
        )
        recommended_next_step = (
            "either add one more lightweight runtime-owned cache counter, advance scheduler depth, or satisfy TurboQuant validation preconditions without overclaiming parity"
        )

    return CacheCounterGap(
        closure=cache_closure,
        status="partial",
        counter_gap_rung=counter_gap_rung,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
        observed_runtime_behavior_frozen=observed_runtime_behavior_frozen,
        missing_runtime_counters=tuple(missing_runtime_counters),
        visible_runtime_counters=tuple(visible_runtime_counters),
    )


def cache_counter_gap_to_dict(gap: CacheCounterGap) -> dict[str, Any]:
    """Serialize the exact residual cache counter gap."""

    return {
        "contract": {
            "surface": "owlmlx.cache_counter_gap",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "observed_runtime_behavior",
                "runtime_counters",
            ],
        },
        "summary": {
            "status": gap.status,
            "counter_gap_rung": gap.counter_gap_rung,
            "residual_blocker": gap.residual_blocker,
            "recommended_next_step": gap.recommended_next_step,
        },
        "observed_runtime_behavior": {
            "observed_runtime_behavior_frozen": gap.observed_runtime_behavior_frozen,
            "closure_rung": gap.closure.closure_rung,
            "repeatability_status": gap.closure.repeatability.repeatability_status,
            "scheduler_depth": gap.closure.scheduler.scheduler_depth,
            "turboquant_status": gap.closure.turboquant.status,
        },
        "runtime_counters": {
            "visible_runtime_counters": list(gap.visible_runtime_counters),
            "missing_runtime_counters": list(gap.missing_runtime_counters),
        },
    }
