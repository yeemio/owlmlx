"""Runtime-owned continuous-batching feasibility on the active cache path."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_scheduler_branch_selection import (
    CacheSchedulerBranchSelection,
    build_cache_scheduler_branch_selection,
)


@dataclass(frozen=True, slots=True)
class CacheContinuousBatchingFeasibility:
    """Exact feasibility truth for continuous batching on the current path."""

    branch_selection: CacheSchedulerBranchSelection
    status: str
    feasibility_rung: str
    generation_gate_mode: str
    child_exchange_mode: str
    stream_holds_full_session: bool
    missing_batching_mechanisms: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_continuous_batching_feasibility(
    *,
    branch_selection: CacheSchedulerBranchSelection | None = None,
) -> CacheContinuousBatchingFeasibility:
    """Build exact continuous-batching feasibility for the active path."""

    selection = (
        branch_selection
        if isinstance(branch_selection, CacheSchedulerBranchSelection)
        else build_cache_scheduler_branch_selection()
    )

    feasibility_rung = "feasibility_unresolved"
    generation_gate_mode = "unknown"
    child_exchange_mode = "unknown"
    stream_holds_full_session = False
    missing_batching_mechanisms = ("scheduler_branch_not_frozen",)
    residual_blocker = (
        "continuous batching feasibility is not yet exact because scheduler branch selection is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze the next scheduler branch before judging continuous batching on the active path"
    )

    if selection.selection_rung == "branch_selection_exact":
        generation_gate_mode = "serial_ticketed_fifo_whole_request"
        child_exchange_mode = "single_request_per_child_exchange"
        stream_holds_full_session = True
        feasibility_rung = "feasibility_blocker_exact"
        missing_batching_mechanisms = (
            "request_aggregation_window",
            "shared_prefill_batch_step",
            "interleaved_decode_scheduler",
        )
        residual_blocker = (
            "continuous batching is not just absent on this path: the active scheduler still gates whole requests serially, the child protocol still exchanges one request at a time, and streamed responses still hold the full gate session"
        )
        recommended_next_step = (
            "do not describe continuous batching as a small follow-up on this path; first introduce one explicit request-aggregation or interleaved scheduling mechanism without violating the validated serial safety boundary"
        )

    return CacheContinuousBatchingFeasibility(
        branch_selection=selection,
        status="partial",
        feasibility_rung=feasibility_rung,
        generation_gate_mode=generation_gate_mode,
        child_exchange_mode=child_exchange_mode,
        stream_holds_full_session=stream_holds_full_session,
        missing_batching_mechanisms=missing_batching_mechanisms,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_continuous_batching_feasibility_to_dict(
    feasibility: CacheContinuousBatchingFeasibility,
) -> dict[str, object]:
    """Serialize continuous-batching feasibility."""

    return {
        "contract": {
            "surface": "owlmlx.cache_continuous_batching_feasibility",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "runtime_path",
                "missing_batching_mechanisms",
            ],
        },
        "summary": {
            "status": feasibility.status,
            "feasibility_rung": feasibility.feasibility_rung,
            "residual_blocker": feasibility.residual_blocker,
            "recommended_next_step": feasibility.recommended_next_step,
        },
        "runtime_path": {
            "generation_gate_mode": feasibility.generation_gate_mode,
            "child_exchange_mode": feasibility.child_exchange_mode,
            "stream_holds_full_session": feasibility.stream_holds_full_session,
        },
        "missing_batching_mechanisms": list(feasibility.missing_batching_mechanisms),
    }
