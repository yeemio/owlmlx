"""Runtime-owned exact lifetime boundary for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_inert_state_semantics import (
    CachePreClaimInertStateSemantics,
    build_cache_pre_claim_inert_state_semantics,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerLifetime:
    """Exact runtime truth for inert pre-claim drop/cancel marker lifetime."""

    inert_state_semantics: CachePreClaimInertStateSemantics
    status: str
    exactness_rung: str
    marker_lifetime_status: str
    marker_expiry_boundary: str
    allowed_lifetime_events: tuple[str, ...]
    forbidden_lifetime_promotions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_lifetime(
    *,
    inert_state_semantics: CachePreClaimInertStateSemantics | None = None,
) -> CachePreClaimMarkerLifetime:
    """Build exact lifetime boundary for inert pre-claim markers."""

    semantics = (
        inert_state_semantics
        if isinstance(inert_state_semantics, CachePreClaimInertStateSemantics)
        else build_cache_pre_claim_inert_state_semantics()
    )

    exactness_rung = "marker_lifetime_unresolved"
    marker_lifetime_status = "not_frozen"
    marker_expiry_boundary = "not_frozen"
    allowed_lifetime_events = ()
    forbidden_lifetime_promotions = ()
    residual_blocker = (
        "marker lifetime exactness is not yet frozen because inert pre-claim semantics are not exact"
    )
    recommended_next_step = (
        "freeze inert pre-claim semantics before reducing the remaining cache blocker to exact drop/cancel marker lifetime"
    )

    if semantics.exactness_rung == "inert_state_semantics_exact":
        exactness_rung = "marker_lifetime_exact"
        marker_lifetime_status = (
            "marker_may_exist_only_until_gate_claim_or_explicit_pre_claim_discard"
        )
        marker_expiry_boundary = (
            "marker_expires_at_gate_claim_or_pre_claim_discard_boundary"
        )
        allowed_lifetime_events = (
            "explicit_drop_before_gate_claim",
            "explicit_cancel_before_gate_claim",
            "implicit_expiry_at_gate_claim",
        )
        forbidden_lifetime_promotions = (
            "no_queue_ownership_from_marker_lifetime",
            "no_cohort_hold_across_gate_claim_boundary",
            "no_execution_entitlement_from_marker_lifetime",
            "no_post_claim_state_transfer_from_expired_marker",
        )
        residual_blocker = (
            "the pre-claim drop/cancel marker lifetime is now exact: an inert marker may exist only until explicit pre-claim discard or whole-request gate claim, it must expire at that boundary, and it may not create queue ownership, preserve cohort hold across gate claim, or transfer execution entitlement into post-claim state"
        )
        recommended_next_step = (
            "treat batching as pre-claim marker expiry/ownership work on this path; if a future seam expands, freeze exact discard timing and marker visibility without allowing marker lifetime to become hidden queue ownership or execution state"
        )

    return CachePreClaimMarkerLifetime(
        inert_state_semantics=semantics,
        status="partial",
        exactness_rung=exactness_rung,
        marker_lifetime_status=marker_lifetime_status,
        marker_expiry_boundary=marker_expiry_boundary,
        allowed_lifetime_events=allowed_lifetime_events,
        forbidden_lifetime_promotions=forbidden_lifetime_promotions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_lifetime_to_dict(
    exactness: CachePreClaimMarkerLifetime,
) -> dict[str, object]:
    """Serialize exact marker lifetime truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_lifetime",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "marker_lifetime_boundary",
                "forbidden_lifetime_promotions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "marker_lifetime_boundary": {
            "marker_lifetime_status": exactness.marker_lifetime_status,
            "marker_expiry_boundary": exactness.marker_expiry_boundary,
            "allowed_lifetime_events": list(exactness.allowed_lifetime_events),
        },
        "forbidden_lifetime_promotions": list(
            exactness.forbidden_lifetime_promotions
        ),
    }
