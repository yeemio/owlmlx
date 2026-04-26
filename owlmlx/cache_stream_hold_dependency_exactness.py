"""Runtime-owned exactness for the post-handoff stream-hold dependency."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_cohort_to_child_exchange_handoff_exactness import (
    CacheCohortToChildExchangeHandoffExactness,
    build_cache_cohort_to_child_exchange_handoff_exactness,
)
from .cache_stream_hold_dependency_harness import (
    CacheStreamHoldDependencyHarnessResult,
)


@dataclass(frozen=True, slots=True)
class CacheStreamHoldDependencyExactness:
    """Exact stream-hold truth after non-stream cohort handoff is already visible."""

    cohort_handoff_exactness: CacheCohortToChildExchangeHandoffExactness
    status: str
    exactness_rung: str
    verdict: str
    hold_status: str
    gate_release_boundary: str
    next_active_dependency: str
    next_active_dependency_status: str
    preserved_non_stream_handoff_status: str
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_stream_hold_dependency_exactness(
    *,
    cohort_handoff_exactness: CacheCohortToChildExchangeHandoffExactness | None = None,
    stream_hold_harness: CacheStreamHoldDependencyHarnessResult | None = None,
) -> CacheStreamHoldDependencyExactness:
    """Build exact stream-hold truth on the active request-aggregation path."""

    handoff_exactness = (
        cohort_handoff_exactness
        if isinstance(
            cohort_handoff_exactness,
            CacheCohortToChildExchangeHandoffExactness,
        )
        else build_cache_cohort_to_child_exchange_handoff_exactness()
    )

    exactness_rung = "stream_hold_dependency_unresolved"
    verdict = "stream_hold_dependency_still_blocked"
    hold_status = "not_frozen"
    gate_release_boundary = "not_frozen"
    next_active_dependency = "stream_session_hold_dependency"
    next_active_dependency_status = "not_selected"
    preserved_non_stream_handoff_status = "not_frozen"
    residual_blocker = (
        "stream-hold exactness is not yet frozen because non-stream cohort handoff is not exact"
    )
    recommended_next_step = (
        "freeze non-stream cohort handoff before reducing the active stream-hold dependency"
    )

    if handoff_exactness.exactness_rung == "cohort_to_child_handoff_exact":
        exactness_rung = "stream_hold_dependency_exact"
        hold_status = "stream_session_holds_gate_until_completion"
        gate_release_boundary = "stream_session_completion"
        next_active_dependency = "stream_session_hold_dependency"
        next_active_dependency_status = "stream_session_holds_gate_until_completion"
        preserved_non_stream_handoff_status = handoff_exactness.handoff_status
        residual_blocker = (
            "the stream path still holds the claimed gate through whole-session consumer completion on this path, even though a bounded pre-gate cohort already reaches one aggregated non-stream child exchange while post-claim serial safety remains intact"
        )
        recommended_next_step = (
            "observe the exact stream hold boundary next without reopening non-stream handoff, child exchange capability, or continuous batching"
        )

        if (
            stream_hold_harness is not None
            and stream_hold_harness.hold_dependency_narrowed
            and stream_hold_harness.gate_release_boundary
            == "backend_stream_iterator_completion_before_consumer_drain"
            and stream_hold_harness.second_stream_started_before_first_consumer_completed
            and stream_hold_harness.max_concurrent == 1
            and stream_hold_harness.queue_policy == "ticketed_fifo"
        ):
            verdict = "stream_hold_dependency_narrowed"
            hold_status = (
                "stream_gate_release_decoupled_from_consumer_completion_visible"
            )
            gate_release_boundary = stream_hold_harness.gate_release_boundary
            next_active_dependency = "stream_backend_iterator_completion_dependency"
            next_active_dependency_status = (
                "stream_backend_iterator_holds_gate_until_completion"
            )
            residual_blocker = (
                "stream gate release no longer waits for whole-session consumer drain on this path: once the backend stream iterator completes, the claimed gate is released while serial FIFO remains intact, so the remaining exact stream seam is now the backend iterator itself rather than outer session completion"
            )
            recommended_next_step = (
                "freeze backend-iterator completion as the next exact stream seam without inflating this into continuous batching, stream interleaving, or cache parity"
            )

    return CacheStreamHoldDependencyExactness(
        cohort_handoff_exactness=handoff_exactness,
        status="partial",
        exactness_rung=exactness_rung,
        verdict=verdict,
        hold_status=hold_status,
        gate_release_boundary=gate_release_boundary,
        next_active_dependency=next_active_dependency,
        next_active_dependency_status=next_active_dependency_status,
        preserved_non_stream_handoff_status=preserved_non_stream_handoff_status,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_stream_hold_dependency_exactness_to_dict(
    exactness: CacheStreamHoldDependencyExactness,
) -> dict[str, object]:
    """Serialize stream-hold dependency exactness."""

    return {
        "contract": {
            "surface": "owlmlx.cache_stream_hold_dependency_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "stream_hold",
                "next_active_dependency",
                "preserved_non_stream_handoff",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "verdict": exactness.verdict,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "stream_hold": {
            "hold_status": exactness.hold_status,
            "gate_release_boundary": exactness.gate_release_boundary,
        },
        "next_active_dependency": {
            "dependency": exactness.next_active_dependency,
            "status": exactness.next_active_dependency_status,
        },
        "preserved_non_stream_handoff": {
            "status": exactness.preserved_non_stream_handoff_status,
        },
    }
