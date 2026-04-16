"""Runtime-owned exact visibility boundary for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_lifetime import (
    CachePreClaimMarkerLifetime,
    build_cache_pre_claim_marker_lifetime,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerVisibility:
    """Exact runtime truth for inert pre-claim marker visibility semantics."""

    marker_lifetime: CachePreClaimMarkerLifetime
    status: str
    exactness_rung: str
    marker_visibility_status: str
    discard_trigger_status: str
    allowed_visibility_readers: tuple[str, ...]
    forbidden_visibility_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_visibility(
    *,
    marker_lifetime: CachePreClaimMarkerLifetime | None = None,
) -> CachePreClaimMarkerVisibility:
    """Build exact visibility boundary for inert pre-claim markers."""

    lifetime = (
        marker_lifetime
        if isinstance(marker_lifetime, CachePreClaimMarkerLifetime)
        else build_cache_pre_claim_marker_lifetime()
    )

    exactness_rung = "marker_visibility_unresolved"
    marker_visibility_status = "not_frozen"
    discard_trigger_status = "not_frozen"
    allowed_visibility_readers = ()
    forbidden_visibility_expansions = ()
    residual_blocker = (
        "marker visibility exactness is not yet frozen because marker lifetime is not exact"
    )
    recommended_next_step = (
        "freeze marker lifetime before reducing the remaining cache blocker to exact visibility/discard-trigger semantics"
    )

    if lifetime.exactness_rung == "marker_lifetime_exact":
        exactness_rung = "marker_visibility_exact"
        marker_visibility_status = (
            "marker_visible_only_to_pre_claim_discard_and_gate_expiry_paths"
        )
        discard_trigger_status = (
            "discard_trigger_limited_to_explicit_pre_claim_discard_or_gate_claim_expiry"
        )
        allowed_visibility_readers = (
            "pre_claim_discard_path",
            "gate_claim_expiry_path",
        )
        forbidden_visibility_expansions = (
            "no_scheduler_selection_visibility_before_claim",
            "no_child_dispatch_visibility_before_claim",
            "no_stream_visibility_before_claim",
            "no_execution_priority_visibility_before_claim",
        )
        residual_blocker = (
            "the pre-claim marker visibility boundary is now exact: an inert marker may be observed only by explicit pre-claim discard logic or gate-claim expiry logic, and marker visibility may not leak into scheduler selection, child dispatch, stream handling, or execution-priority paths before the first runtime-owned boundary"
        )
        recommended_next_step = (
            "treat batching as pre-claim marker trigger-boundary work on this path; if a future seam expands, freeze exact discard-trigger inputs without allowing marker visibility to become hidden queue ownership or execution routing"
        )

    return CachePreClaimMarkerVisibility(
        marker_lifetime=lifetime,
        status="partial",
        exactness_rung=exactness_rung,
        marker_visibility_status=marker_visibility_status,
        discard_trigger_status=discard_trigger_status,
        allowed_visibility_readers=allowed_visibility_readers,
        forbidden_visibility_expansions=forbidden_visibility_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_visibility_to_dict(
    exactness: CachePreClaimMarkerVisibility,
) -> dict[str, object]:
    """Serialize exact marker visibility/discard-trigger truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_visibility",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "marker_visibility_boundary",
                "forbidden_visibility_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "marker_visibility_boundary": {
            "marker_visibility_status": exactness.marker_visibility_status,
            "discard_trigger_status": exactness.discard_trigger_status,
            "allowed_visibility_readers": list(exactness.allowed_visibility_readers),
        },
        "forbidden_visibility_expansions": list(
            exactness.forbidden_visibility_expansions
        ),
    }
