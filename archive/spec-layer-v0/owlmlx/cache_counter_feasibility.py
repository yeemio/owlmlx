"""Runtime-owned ownership boundary for cache counters on the active path."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_counter_gap import CacheCounterGap, build_cache_counter_gap


@dataclass(frozen=True, slots=True)
class CacheCounterFeasibility:
    """Exact ownership feasibility for runtime cache counters."""

    counter_gap: CacheCounterGap
    status: str
    feasibility_rung: str
    reuse_counter_feasibility: str
    residency_counter_feasibility: str
    eviction_counter_feasibility: str
    next_cache_subgap: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_counter_feasibility(
    *,
    counter_gap: CacheCounterGap | None = None,
) -> CacheCounterFeasibility:
    """Build the active-path cache counter ownership boundary."""

    gap = counter_gap if isinstance(counter_gap, CacheCounterGap) else build_cache_counter_gap()

    feasibility_rung = "counter_ownership_unresolved"
    reuse_counter_feasibility = "not_visible"
    residency_counter_feasibility = "unresolved"
    eviction_counter_feasibility = "unresolved"
    next_cache_subgap = "counter_boundary"
    residual_blocker = (
        "cache counter ownership is not yet frozen strongly enough to split the remaining cache closure work"
    )
    recommended_next_step = (
        "freeze whether residency and eviction counters are runtime-owned on the current active path before narrowing the next cache closure step"
    )

    if gap.counter_gap_rung == "counter_gap_exact":
        feasibility_rung = "counter_ownership_exact"
        reuse_counter_feasibility = (
            "runtime_owned_visible"
            if "reuse_counter" in gap.visible_runtime_counters
            else "runtime_owned_absent"
        )
        residency_counter_feasibility = "not_runtime_owned_on_current_path"
        eviction_counter_feasibility = "not_runtime_owned_on_current_path"
        next_cache_subgap = "scheduler_depth"
        residual_blocker = (
            "remaining cache closure is no longer about counter ownership: scheduler depth remains serial_single_worker and TurboQuant is still below controlled validation"
        )
        recommended_next_step = (
            "treat cache as a scheduler-depth/TurboQuant closure problem on this path; do not chase fake residency or eviction counters"
        )

    return CacheCounterFeasibility(
        counter_gap=gap,
        status="partial",
        feasibility_rung=feasibility_rung,
        reuse_counter_feasibility=reuse_counter_feasibility,
        residency_counter_feasibility=residency_counter_feasibility,
        eviction_counter_feasibility=eviction_counter_feasibility,
        next_cache_subgap=next_cache_subgap,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_counter_feasibility_to_dict(
    feasibility: CacheCounterFeasibility,
) -> dict[str, object]:
    """Serialize cache counter ownership feasibility."""

    return {
        "contract": {
            "surface": "owlmlx.cache_counter_feasibility",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "counter_ownership",
                "next_cache_subgap",
            ],
        },
        "summary": {
            "status": feasibility.status,
            "feasibility_rung": feasibility.feasibility_rung,
            "residual_blocker": feasibility.residual_blocker,
            "recommended_next_step": feasibility.recommended_next_step,
        },
        "counter_ownership": {
            "reuse_counter": feasibility.reuse_counter_feasibility,
            "residency_counter": feasibility.residency_counter_feasibility,
            "eviction_counter": feasibility.eviction_counter_feasibility,
        },
        "next_cache_subgap": {
            "next_cache_subgap": feasibility.next_cache_subgap,
        },
    }
