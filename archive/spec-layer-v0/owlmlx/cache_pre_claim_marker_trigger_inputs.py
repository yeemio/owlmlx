"""Runtime-owned exact discard-trigger inputs for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_visibility import (
    CachePreClaimMarkerVisibility,
    build_cache_pre_claim_marker_visibility,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerTriggerInputs:
    """Exact runtime truth for pre-claim marker discard-trigger inputs."""

    marker_visibility: CachePreClaimMarkerVisibility
    status: str
    exactness_rung: str
    trigger_input_status: str
    unavailable_trigger_status: str
    allowed_trigger_inputs: tuple[str, ...]
    forbidden_trigger_inputs: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_trigger_inputs(
    *,
    marker_visibility: CachePreClaimMarkerVisibility | None = None,
) -> CachePreClaimMarkerTriggerInputs:
    """Build exact discard-trigger input truth for inert pre-claim markers."""

    visibility = (
        marker_visibility
        if isinstance(marker_visibility, CachePreClaimMarkerVisibility)
        else build_cache_pre_claim_marker_visibility()
    )

    exactness_rung = "trigger_inputs_unresolved"
    trigger_input_status = "not_frozen"
    unavailable_trigger_status = "not_frozen"
    allowed_trigger_inputs = ()
    forbidden_trigger_inputs = ()
    residual_blocker = (
        "marker trigger-input exactness is not yet frozen because marker visibility is not exact"
    )
    recommended_next_step = (
        "freeze marker visibility before reducing the remaining cache blocker to exact discard-trigger inputs"
    )

    if visibility.exactness_rung == "marker_visibility_exact":
        exactness_rung = "trigger_inputs_exact"
        trigger_input_status = (
            "trigger_inputs_limited_to_explicit_pre_claim_drop_cancel_or_gate_claim_expiry"
        )
        unavailable_trigger_status = (
            "scheduler_child_stream_and_priority_inputs_unavailable_before_gate_claim"
        )
        allowed_trigger_inputs = (
            "explicit_pre_claim_drop_signal",
            "explicit_pre_claim_cancel_signal",
            "gate_claim_expiry_transition",
        )
        forbidden_trigger_inputs = (
            "no_scheduler_pressure_input_before_claim",
            "no_child_backend_input_before_claim",
            "no_stream_disconnect_input_before_claim",
            "no_execution_priority_input_before_claim",
        )
        residual_blocker = (
            "the pre-claim discard-trigger inputs are now exact: an inert marker may be cleared only by explicit pre-claim drop/cancel signals or by gate-claim expiry transition, and scheduler pressure, child/backend events, stream events, or execution-priority signals remain unavailable before the first runtime-owned boundary"
        )
        recommended_next_step = (
            "treat batching as pre-claim marker reader/writer ownership work on this path; if a future seam expands, freeze which runtime-owned path may author a marker versus only observe it, without allowing trigger inputs to become hidden queue ownership or execution routing"
        )

    return CachePreClaimMarkerTriggerInputs(
        marker_visibility=visibility,
        status="partial",
        exactness_rung=exactness_rung,
        trigger_input_status=trigger_input_status,
        unavailable_trigger_status=unavailable_trigger_status,
        allowed_trigger_inputs=allowed_trigger_inputs,
        forbidden_trigger_inputs=forbidden_trigger_inputs,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_trigger_inputs_to_dict(
    exactness: CachePreClaimMarkerTriggerInputs,
) -> dict[str, object]:
    """Serialize exact pre-claim marker discard-trigger input truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_trigger_inputs",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "trigger_input_boundary",
                "forbidden_trigger_inputs",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "trigger_input_boundary": {
            "trigger_input_status": exactness.trigger_input_status,
            "unavailable_trigger_status": exactness.unavailable_trigger_status,
            "allowed_trigger_inputs": list(exactness.allowed_trigger_inputs),
        },
        "forbidden_trigger_inputs": list(exactness.forbidden_trigger_inputs),
    }
