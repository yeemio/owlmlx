"""Runtime-owned exact immutability boundary for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_clear_observer_boundary import (
    CachePreClaimMarkerClearObserverBoundary,
    build_cache_pre_claim_marker_clear_observer_boundary,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerImmutabilityBoundary:
    """Exact runtime truth for pre-claim marker mutation limits."""

    clear_observer_boundary: CachePreClaimMarkerClearObserverBoundary
    status: str
    exactness_rung: str
    immutability_status: str
    allowed_mutation_semantics: tuple[str, ...]
    forbidden_mutation_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_immutability_boundary(
    *,
    clear_observer_boundary: CachePreClaimMarkerClearObserverBoundary | None = None,
) -> CachePreClaimMarkerImmutabilityBoundary:
    """Build exact pre-claim marker immutability truth."""

    boundary = (
        clear_observer_boundary
        if isinstance(
            clear_observer_boundary, CachePreClaimMarkerClearObserverBoundary
        )
        else build_cache_pre_claim_marker_clear_observer_boundary()
    )

    exactness_rung = "immutability_boundary_unresolved"
    immutability_status = "not_frozen"
    allowed_mutation_semantics = ()
    forbidden_mutation_expansions = ()
    residual_blocker = (
        "marker immutability boundary is not yet frozen because marker clear/observer ownership is not exact"
    )
    recommended_next_step = (
        "freeze marker clear/observer boundary before reducing the remaining cache blocker to exact immutability semantics"
    )

    if boundary.exactness_rung == "clear_observer_boundary_exact":
        exactness_rung = "immutability_boundary_exact"
        immutability_status = "clear_only_mutation_before_gate_claim"
        allowed_mutation_semantics = (
            "clear_only_transition_of_inert_marker_before_gate_claim",
            "no_state_change_without_explicit_clearer_or_gate_claim_expiry",
        )
        forbidden_mutation_expansions = (
            "no_marker_payload_rewrite_before_claim",
            "no_priority_flag_mutation_before_claim",
            "no_queue_membership_mutation_before_claim",
            "no_child_stream_execution_mutation_before_claim",
        )
        residual_blocker = (
            "the pre-claim marker immutability boundary is now exact: before whole-request gate claim the inert marker may only transition by clear-only semantics, and no pre-claim path may rewrite payload, mutate priority, create queue membership, or attach child/stream/execution state"
        )
        recommended_next_step = (
            "treat batching as pre-claim marker payload-shape work on this path; if a future seam expands, freeze the exact payload fields or prove that only presence/absence may exist before whole-request gate claim"
        )

    return CachePreClaimMarkerImmutabilityBoundary(
        clear_observer_boundary=boundary,
        status="partial",
        exactness_rung=exactness_rung,
        immutability_status=immutability_status,
        allowed_mutation_semantics=allowed_mutation_semantics,
        forbidden_mutation_expansions=forbidden_mutation_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_immutability_boundary_to_dict(
    exactness: CachePreClaimMarkerImmutabilityBoundary,
) -> dict[str, object]:
    """Serialize exact pre-claim marker immutability truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_immutability_boundary",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "immutability_boundary",
                "forbidden_mutation_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "immutability_boundary": {
            "immutability_status": exactness.immutability_status,
            "allowed_mutation_semantics": list(exactness.allowed_mutation_semantics),
        },
        "forbidden_mutation_expansions": list(exactness.forbidden_mutation_expansions),
    }
