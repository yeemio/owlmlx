"""Runtime-owned exact scheduler-floor gap for the active cache path."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_scheduler_turboquant_split import (
    CacheSchedulerTurboQuantSplit,
    build_cache_scheduler_turboquant_split,
)
from .serving import MAX_GENERATION_CONCURRENCY


@dataclass(frozen=True, slots=True)
class CacheSchedulerFloorGap:
    """Exact scheduler-floor truth after the cache branch has split cleanly."""

    split: CacheSchedulerTurboQuantSplit
    status: str
    floor_rung: str
    active_scheduler_mode: str
    queue_discipline: str
    max_concurrent: int
    continuous_batching: bool
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_scheduler_floor_gap(
    *,
    split: CacheSchedulerTurboQuantSplit | None = None,
) -> CacheSchedulerFloorGap:
    """Build the active-path scheduler floor gap once cache has split cleanly."""

    split_status = (
        split if isinstance(split, CacheSchedulerTurboQuantSplit) else build_cache_scheduler_turboquant_split()
    )
    scheduler = split_status.scheduler
    scheduler_status = scheduler.scheduler_status

    floor_rung = "floor_unresolved"
    residual_blocker = (
        "cache closure has not yet narrowed strongly enough to freeze the active scheduler floor"
    )
    recommended_next_step = (
        "split cache closure cleanly between scheduler depth and TurboQuant before freezing the scheduler floor"
    )

    if (
        split_status.split_rung == "split_exact"
        and split_status.dominant_cache_branch == "scheduler_depth"
    ):
        floor_rung = "serial_floor_exact"
        residual_blocker = (
            "remaining cache closure on this path is now scheduler-grade: queue discipline stays serial, max_concurrent stays 1, and no deeper scheduler behavior is runtime-owned yet"
        )
        recommended_next_step = (
            "treat cache as scheduler-implementation work on this path; keep TurboQuant exact but secondary until scheduler depth moves above serial_single_worker"
        )

    return CacheSchedulerFloorGap(
        split=split_status,
        status="partial",
        floor_rung=floor_rung,
        active_scheduler_mode=str(scheduler_status.get("generation_gate", "idle")),
        queue_discipline=str(scheduler_status.get("queue_discipline", "serial")),
        max_concurrent=int(
            scheduler_status.get("max_concurrent", MAX_GENERATION_CONCURRENCY)
        ),
        continuous_batching=False,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_scheduler_floor_gap_to_dict(
    gap: CacheSchedulerFloorGap,
) -> dict[str, object]:
    """Serialize the active-path scheduler floor gap."""

    return {
        "contract": {
            "surface": "owlmlx.cache_scheduler_floor_gap",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "scheduler_floor",
                "next_step",
            ],
        },
        "summary": {
            "status": gap.status,
            "floor_rung": gap.floor_rung,
            "residual_blocker": gap.residual_blocker,
            "recommended_next_step": gap.recommended_next_step,
        },
        "scheduler_floor": {
            "active_scheduler_mode": gap.active_scheduler_mode,
            "queue_discipline": gap.queue_discipline,
            "max_concurrent": gap.max_concurrent,
            "continuous_batching": gap.continuous_batching,
            "scheduler_depth": gap.split.scheduler.scheduler_depth,
        },
        "next_step": {
            "dominant_cache_branch": gap.split.dominant_cache_branch,
        },
    }
