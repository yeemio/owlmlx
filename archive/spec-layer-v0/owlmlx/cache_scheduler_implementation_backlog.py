"""Runtime-owned scheduler implementation backlog after the serial floor is exact."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_scheduler_floor_gap import (
    CacheSchedulerFloorGap,
    build_cache_scheduler_floor_gap,
)


@dataclass(frozen=True, slots=True)
class CacheSchedulerImplementationBacklog:
    """Exact scheduler implementation backlog for the active cache path."""

    floor_gap: CacheSchedulerFloorGap
    status: str
    backlog_rung: str
    owned_scheduler_truth: tuple[str, ...]
    missing_scheduler_capabilities: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_scheduler_implementation_backlog(
    *,
    floor_gap: CacheSchedulerFloorGap | None = None,
) -> CacheSchedulerImplementationBacklog:
    """Build the active-path scheduler implementation backlog."""

    gap = (
        floor_gap if isinstance(floor_gap, CacheSchedulerFloorGap) else build_cache_scheduler_floor_gap()
    )

    backlog_rung = "implementation_backlog_unresolved"
    owned_scheduler_truth = ("queue_discipline_serial",)
    missing_scheduler_capabilities = ("scheduler_depth_not_frozen",)
    residual_blocker = (
        "scheduler implementation backlog is not yet exact because the active scheduler floor is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze the active scheduler floor before claiming an exact scheduler implementation backlog"
    )

    if gap.floor_rung == "serial_floor_exact":
        backlog_rung = "implementation_gap_exact"
        owned_scheduler_truth = (
            "queue_discipline_serial",
            "max_concurrent_1",
            "generation_gate_wait_counters_visible",
            "ticketed_fifo_queue_policy_visible",
        )
        missing_scheduler_capabilities = (
            "continuous_batching",
            "multi_worker_scheduler_depth",
        )
        residual_blocker = (
            "remaining cache closure on this path is now scheduler implementation work: the runtime still lacks continuous batching and multi-worker scheduler depth beyond the serial ticketed FIFO gate"
        )
        recommended_next_step = (
            "treat cache as scheduler-implementation backlog on this path; the serial ticketed FIFO gate is now explicit, but parity still depends on scheduler depth moving beyond single-worker execution"
        )

    return CacheSchedulerImplementationBacklog(
        floor_gap=gap,
        status="partial",
        backlog_rung=backlog_rung,
        owned_scheduler_truth=owned_scheduler_truth,
        missing_scheduler_capabilities=missing_scheduler_capabilities,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_scheduler_implementation_backlog_to_dict(
    backlog: CacheSchedulerImplementationBacklog,
) -> dict[str, object]:
    """Serialize the scheduler implementation backlog."""

    return {
        "contract": {
            "surface": "owlmlx.cache_scheduler_implementation_backlog",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "owned_scheduler_truth",
                "missing_scheduler_capabilities",
            ],
        },
        "summary": {
            "status": backlog.status,
            "backlog_rung": backlog.backlog_rung,
            "residual_blocker": backlog.residual_blocker,
            "recommended_next_step": backlog.recommended_next_step,
        },
        "owned_scheduler_truth": list(backlog.owned_scheduler_truth),
        "missing_scheduler_capabilities": list(backlog.missing_scheduler_capabilities),
    }
