"""Runtime-owned exact branch selection inside the scheduler backlog."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_scheduler_implementation_backlog import (
    CacheSchedulerImplementationBacklog,
    build_cache_scheduler_implementation_backlog,
)
from .serving import MAX_GENERATION_CONCURRENCY


@dataclass(frozen=True, slots=True)
class CacheSchedulerBranchSelection:
    """Exact next-branch selection after scheduler backlog is already frozen."""

    scheduler_backlog: CacheSchedulerImplementationBacklog
    status: str
    selection_rung: str
    selected_branch: str
    selected_branch_status: str
    secondary_branch: str
    secondary_branch_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_scheduler_branch_selection(
    *,
    scheduler_backlog: CacheSchedulerImplementationBacklog | None = None,
) -> CacheSchedulerBranchSelection:
    """Select the next exact scheduler branch on the active cache path."""

    backlog = (
        scheduler_backlog
        if isinstance(scheduler_backlog, CacheSchedulerImplementationBacklog)
        else build_cache_scheduler_implementation_backlog()
    )

    selection_rung = "branch_selection_unresolved"
    selected_branch = "scheduler_backlog_unresolved"
    selected_branch_status = "not_frozen"
    secondary_branch = "scheduler_backlog_unresolved"
    secondary_branch_status = "not_frozen"
    residual_blocker = (
        "scheduler branch selection is not yet exact because the scheduler implementation backlog itself is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze the scheduler implementation backlog before selecting the next scheduler branch"
    )

    if backlog.backlog_rung == "implementation_gap_exact":
        selection_rung = "branch_selection_exact"
        selected_branch = "continuous_batching"
        selected_branch_status = "locally_reducible_on_current_path"
        secondary_branch = "multi_worker_scheduler_depth"
        secondary_branch_status = (
            "safety_revalidation_required"
            if MAX_GENERATION_CONCURRENCY == 1
            else "locally_reducible_on_current_path"
        )
        residual_blocker = (
            "scheduler implementation still remains below reference-grade closure: continuous batching is absent on the active path, and multi-worker scheduler depth still requires concurrency-safety revalidation beyond the validated serial boundary"
        )
        recommended_next_step = (
            "treat the scheduler backlog as continuous-batching-first work on this path; keep multi-worker depth secondary until the concurrency boundary is honestly revalidated"
        )

    return CacheSchedulerBranchSelection(
        scheduler_backlog=backlog,
        status="partial",
        selection_rung=selection_rung,
        selected_branch=selected_branch,
        selected_branch_status=selected_branch_status,
        secondary_branch=secondary_branch,
        secondary_branch_status=secondary_branch_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_scheduler_branch_selection_to_dict(
    selection: CacheSchedulerBranchSelection,
) -> dict[str, object]:
    """Serialize the scheduler branch selection."""

    return {
        "contract": {
            "surface": "owlmlx.cache_scheduler_branch_selection",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "selected_branch",
                "secondary_branch",
            ],
        },
        "summary": {
            "status": selection.status,
            "selection_rung": selection.selection_rung,
            "residual_blocker": selection.residual_blocker,
            "recommended_next_step": selection.recommended_next_step,
        },
        "selected_branch": {
            "branch": selection.selected_branch,
            "status": selection.selected_branch_status,
        },
        "secondary_branch": {
            "branch": selection.secondary_branch,
            "status": selection.secondary_branch_status,
        },
    }
