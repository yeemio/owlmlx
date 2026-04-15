"""Runtime-owned exact batching-mechanism subgap on the active cache path."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_continuous_batching_feasibility import (
    CacheContinuousBatchingFeasibility,
    build_cache_continuous_batching_feasibility,
)


@dataclass(frozen=True, slots=True)
class CacheBatchingMechanismSubgap:
    """Exact next batching mechanism subgap on the current runtime path."""

    feasibility: CacheContinuousBatchingFeasibility
    status: str
    subgap_rung: str
    selected_mechanism: str
    selected_mechanism_status: str
    request_aggregation_window_status: str
    shared_prefill_batch_step_status: str
    interleaved_decode_scheduler_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_batching_mechanism_subgap(
    *,
    feasibility: CacheContinuousBatchingFeasibility | None = None,
) -> CacheBatchingMechanismSubgap:
    """Build the next exact batching-mechanism subgap."""

    batching_feasibility = (
        feasibility
        if isinstance(feasibility, CacheContinuousBatchingFeasibility)
        else build_cache_continuous_batching_feasibility()
    )

    subgap_rung = "mechanism_subgap_unresolved"
    selected_mechanism = "continuous_batching_not_frozen"
    selected_mechanism_status = "not_frozen"
    request_aggregation_window_status = "not_frozen"
    shared_prefill_batch_step_status = "not_frozen"
    interleaved_decode_scheduler_status = "not_frozen"
    residual_blocker = (
        "batching mechanism subgap is not yet exact because continuous-batching feasibility is not frozen strongly enough"
    )
    recommended_next_step = (
        "freeze continuous-batching feasibility before selecting the next batching mechanism subgap"
    )

    if batching_feasibility.feasibility_rung == "feasibility_blocker_exact":
        subgap_rung = "mechanism_subgap_exact"
        selected_mechanism = "request_aggregation_window"
        selected_mechanism_status = "locally_reducible_first_blocker"
        request_aggregation_window_status = "locally_reducible_first_blocker"
        shared_prefill_batch_step_status = "blocked_by_missing_request_aggregation_window"
        interleaved_decode_scheduler_status = (
            "blocked_by_missing_request_aggregation_window_and_full_session_stream_hold"
        )
        residual_blocker = (
            "continuous batching is now narrowed to an exact first mechanism blocker: the current path has no request-aggregation window before the whole-request generation gate and one-request-per-exchange child boundary claim the session, so shared prefill and decode interleaving cannot begin honestly"
        )
        recommended_next_step = (
            "treat request_aggregation_window as the next scheduler mechanism subgap on this path; keep shared_prefill_batch_step and interleaved_decode_scheduler secondary until aggregated admission exists ahead of the serial gate and child exchange boundary"
        )

    return CacheBatchingMechanismSubgap(
        feasibility=batching_feasibility,
        status="partial",
        subgap_rung=subgap_rung,
        selected_mechanism=selected_mechanism,
        selected_mechanism_status=selected_mechanism_status,
        request_aggregation_window_status=request_aggregation_window_status,
        shared_prefill_batch_step_status=shared_prefill_batch_step_status,
        interleaved_decode_scheduler_status=interleaved_decode_scheduler_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_batching_mechanism_subgap_to_dict(
    subgap: CacheBatchingMechanismSubgap,
) -> dict[str, object]:
    """Serialize the exact batching-mechanism subgap."""

    return {
        "contract": {
            "surface": "owlmlx.cache_batching_mechanism_subgap",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "selected_mechanism",
                "mechanism_statuses",
            ],
        },
        "summary": {
            "status": subgap.status,
            "subgap_rung": subgap.subgap_rung,
            "residual_blocker": subgap.residual_blocker,
            "recommended_next_step": subgap.recommended_next_step,
        },
        "selected_mechanism": {
            "mechanism": subgap.selected_mechanism,
            "status": subgap.selected_mechanism_status,
        },
        "mechanism_statuses": {
            "request_aggregation_window": subgap.request_aggregation_window_status,
            "shared_prefill_batch_step": subgap.shared_prefill_batch_step_status,
            "interleaved_decode_scheduler": subgap.interleaved_decode_scheduler_status,
        },
    }
