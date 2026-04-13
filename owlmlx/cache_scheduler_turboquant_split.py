"""Runtime-owned split of remaining cache closure between scheduler and TurboQuant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cache_counter_feasibility import (
    CacheCounterFeasibility,
    build_cache_counter_feasibility,
)
from .cache_scheduler_status import CacheSchedulerStatus, build_cache_scheduler_status
from .turboquant_readiness import TurboQuantReadiness, build_turboquant_readiness


@dataclass(frozen=True, slots=True)
class CacheSchedulerTurboQuantSplit:
    """Exact split of the remaining cache closure work."""

    counter_feasibility: CacheCounterFeasibility
    scheduler: CacheSchedulerStatus
    turboquant: TurboQuantReadiness
    status: str
    split_rung: str
    scheduler_subgap: str
    turboquant_subgap: str
    dominant_cache_branch: str
    residual_blocker: str | None
    recommended_next_step: str


def _counter(
    value: CacheCounterFeasibility | Any | None,
) -> CacheCounterFeasibility:
    if isinstance(value, CacheCounterFeasibility):
        return value
    feasibility_rung = getattr(value, "feasibility_rung", None)
    if isinstance(feasibility_rung, str):
        exact = feasibility_rung == "counter_ownership_exact"
        return CacheCounterFeasibility(
            counter_gap=build_cache_counter_feasibility().counter_gap,
            status=str(getattr(value, "status", "partial")),
            feasibility_rung=feasibility_rung,
            reuse_counter_feasibility=str(
                getattr(
                    value,
                    "reuse_counter_feasibility",
                    "runtime_owned_visible" if exact else "not_visible",
                )
            ),
            residency_counter_feasibility=str(
                getattr(
                    value,
                    "residency_counter_feasibility",
                    "not_runtime_owned_on_current_path" if exact else "unresolved",
                )
            ),
            eviction_counter_feasibility=str(
                getattr(
                    value,
                    "eviction_counter_feasibility",
                    "not_runtime_owned_on_current_path" if exact else "unresolved",
                )
            ),
            next_cache_subgap=str(
                getattr(
                    value,
                    "next_cache_subgap",
                    "scheduler_depth" if exact else "counter_boundary",
                )
            ),
            residual_blocker=getattr(value, "residual_blocker", None),
            recommended_next_step=str(
                getattr(
                    value,
                    "recommended_next_step",
                    (
                        "treat cache as a scheduler-depth/TurboQuant closure problem on this path; do not chase fake residency or eviction counters"
                        if exact
                        else "freeze cache counter ownership first so the remaining cache work can split cleanly"
                    ),
                )
            ),
        )
    return build_cache_counter_feasibility()


def build_cache_scheduler_turboquant_split(
    *,
    counter_feasibility: CacheCounterFeasibility | Any | None = None,
    scheduler: CacheSchedulerStatus | None = None,
    turboquant: TurboQuantReadiness | None = None,
) -> CacheSchedulerTurboQuantSplit:
    """Build the remaining cache closure split after counter ownership is exact."""

    counter = _counter(counter_feasibility)
    scheduler_status = (
        scheduler if isinstance(scheduler, CacheSchedulerStatus) else build_cache_scheduler_status()
    )
    turboquant_status = (
        turboquant if isinstance(turboquant, TurboQuantReadiness) else build_turboquant_readiness()
    )

    split_rung = "split_unresolved"
    scheduler_subgap = "scheduler_depth_unresolved"
    turboquant_subgap = "turboquant_unresolved"
    dominant_cache_branch = "counter_boundary"
    residual_blocker = (
        "cache closure is not yet split strongly enough between scheduler depth and TurboQuant readiness"
    )
    recommended_next_step = (
        "freeze cache counter ownership first so the remaining cache work can split cleanly"
    )

    if counter.feasibility_rung == "counter_ownership_exact":
        split_rung = "split_exact"
        scheduler_subgap = (
            "serial_scheduler_exact"
            if scheduler_status.scheduler_depth == "serial_single_worker"
            else "scheduler_depth_advanced"
        )
        turboquant_subgap = (
            "safety_preconditions_exact"
            if turboquant_status.status == "safety_blocked"
            else turboquant_status.status
        )
        dominant_cache_branch = (
            "scheduler_depth"
            if scheduler_subgap == "serial_scheduler_exact"
            else "turboquant_preconditions"
        )
        residual_blocker = (
            "remaining cache closure has split cleanly: scheduler depth is still serial_single_worker and TurboQuant is still safety-blocked"
        )
        recommended_next_step = (
            "treat cache as scheduler-depth-first work on this path, while keeping TurboQuant preconditions exact and non-inflated"
        )
        if dominant_cache_branch == "turboquant_preconditions":
            recommended_next_step = (
                "treat cache as TurboQuant-preconditions work on this path, without regressing the already-frozen scheduler truth"
            )

    return CacheSchedulerTurboQuantSplit(
        counter_feasibility=counter,
        scheduler=scheduler_status,
        turboquant=turboquant_status,
        status="partial",
        split_rung=split_rung,
        scheduler_subgap=scheduler_subgap,
        turboquant_subgap=turboquant_subgap,
        dominant_cache_branch=dominant_cache_branch,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_scheduler_turboquant_split_to_dict(
    split: CacheSchedulerTurboQuantSplit,
) -> dict[str, object]:
    """Serialize the remaining cache closure split."""

    return {
        "contract": {
            "surface": "owlmlx.cache_scheduler_turboquant_split",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "scheduler_branch",
                "turboquant_branch",
                "next_cache_branch",
            ],
        },
        "summary": {
            "status": split.status,
            "split_rung": split.split_rung,
            "residual_blocker": split.residual_blocker,
            "recommended_next_step": split.recommended_next_step,
        },
        "scheduler_branch": {
            "scheduler_subgap": split.scheduler_subgap,
            "scheduler_depth": split.scheduler.scheduler_depth,
        },
        "turboquant_branch": {
            "turboquant_subgap": split.turboquant_subgap,
            "turboquant_status": split.turboquant.status,
            "ready": split.turboquant.ready,
        },
        "next_cache_branch": {
            "dominant_cache_branch": split.dominant_cache_branch,
        },
    }
