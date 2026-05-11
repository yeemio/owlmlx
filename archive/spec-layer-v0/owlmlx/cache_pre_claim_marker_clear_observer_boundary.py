"""Runtime-owned exact clearer/observer boundary for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_state_carrier import (
    CachePreClaimMarkerStateCarrier,
    build_cache_pre_claim_marker_state_carrier,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerClearObserverBoundary:
    """Exact runtime truth for pre-claim marker clear/observe ownership."""

    state_carrier: CachePreClaimMarkerStateCarrier
    status: str
    exactness_rung: str
    clearer_boundary_status: str
    observer_boundary_status: str
    allowed_clearer_paths: tuple[str, ...]
    allowed_observer_only_paths: tuple[str, ...]
    forbidden_clearer_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_clear_observer_boundary(
    *,
    state_carrier: CachePreClaimMarkerStateCarrier | None = None,
) -> CachePreClaimMarkerClearObserverBoundary:
    """Build exact pre-claim marker clear/observe boundary truth."""

    carrier = (
        state_carrier
        if isinstance(state_carrier, CachePreClaimMarkerStateCarrier)
        else build_cache_pre_claim_marker_state_carrier()
    )

    exactness_rung = "clear_observer_boundary_unresolved"
    clearer_boundary_status = "not_frozen"
    observer_boundary_status = "not_frozen"
    allowed_clearer_paths = ()
    allowed_observer_only_paths = ()
    forbidden_clearer_expansions = ()
    residual_blocker = (
        "marker clear/observer boundary is not yet frozen because marker state-carrier exactness is not exact"
    )
    recommended_next_step = (
        "freeze marker state-carrier exactness before reducing the remaining cache blocker to exact clear/observer boundary semantics"
    )

    if carrier.exactness_rung == "state_carrier_exact":
        exactness_rung = "clear_observer_boundary_exact"
        clearer_boundary_status = (
            "clear_paths_limited_to_explicit_drop_cancel_and_gate_claim_expiry"
        )
        observer_boundary_status = (
            "observer_paths_limited_to_pre_claim_discard_without_clear_ownership"
        )
        allowed_clearer_paths = (
            "explicit_pre_claim_drop_cancel_clearer",
            "gate_claim_expiry_clearer",
        )
        allowed_observer_only_paths = ("pre_claim_discard_observer",)
        forbidden_clearer_expansions = (
            "no_scheduler_clearer_before_claim",
            "no_child_backend_clearer_before_claim",
            "no_stream_clearer_before_claim",
            "no_execution_priority_clearer_before_claim",
        )
        residual_blocker = (
            "the pre-claim marker clear/observer boundary is now exact: only explicit pre-claim drop/cancel logic and gate-claim expiry may clear the inert marker carrier before whole-request gate claim, while pre-claim discard may only observe marker presence and may not acquire clearer ownership or hidden queue control"
        )
        recommended_next_step = (
            "treat batching as pre-claim marker immutability work on this path; if a future seam expands, freeze whether any pre-claim path may mutate marker payload beyond clear-only semantics without turning the inert carrier into hidden queue ownership or execution routing"
        )

    return CachePreClaimMarkerClearObserverBoundary(
        state_carrier=carrier,
        status="partial",
        exactness_rung=exactness_rung,
        clearer_boundary_status=clearer_boundary_status,
        observer_boundary_status=observer_boundary_status,
        allowed_clearer_paths=allowed_clearer_paths,
        allowed_observer_only_paths=allowed_observer_only_paths,
        forbidden_clearer_expansions=forbidden_clearer_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_clear_observer_boundary_to_dict(
    exactness: CachePreClaimMarkerClearObserverBoundary,
) -> dict[str, object]:
    """Serialize exact pre-claim marker clear/observer boundary truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_clear_observer_boundary",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "clear_observer_boundary",
                "forbidden_clearer_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "clear_observer_boundary": {
            "clearer_boundary_status": exactness.clearer_boundary_status,
            "observer_boundary_status": exactness.observer_boundary_status,
            "allowed_clearer_paths": list(exactness.allowed_clearer_paths),
            "allowed_observer_only_paths": list(
                exactness.allowed_observer_only_paths
            ),
        },
        "forbidden_clearer_expansions": list(exactness.forbidden_clearer_expansions),
    }
