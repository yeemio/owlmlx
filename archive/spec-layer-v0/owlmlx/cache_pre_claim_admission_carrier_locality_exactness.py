"""Runtime-owned exact locality boundary for bounded pre-claim admission carriers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_admission_carrier_encoding_exactness import (
    CachePreClaimAdmissionCarrierEncodingExactness,
    build_cache_pre_claim_admission_carrier_encoding_exactness,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimAdmissionCarrierLocalityExactness:
    """Exact runtime truth for where a bounded pre-claim carrier may live."""

    encoding_exactness: CachePreClaimAdmissionCarrierEncodingExactness
    status: str
    exactness_rung: str
    locality_status: str
    allowed_localities: tuple[str, ...]
    forbidden_locality_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_admission_carrier_locality_exactness(
    *,
    encoding_exactness: CachePreClaimAdmissionCarrierEncodingExactness | None = None,
) -> CachePreClaimAdmissionCarrierLocalityExactness:
    """Build exact pre-claim admission-carrier locality truth."""

    encoding = (
        encoding_exactness
        if isinstance(encoding_exactness, CachePreClaimAdmissionCarrierEncodingExactness)
        else build_cache_pre_claim_admission_carrier_encoding_exactness()
    )

    exactness_rung = "admission_carrier_locality_unresolved"
    locality_status = "not_frozen"
    allowed_localities = ()
    forbidden_locality_expansions = ()
    residual_blocker = (
        "pre-claim admission-carrier locality exactness is not yet frozen because admission-carrier encoding exactness is not exact"
    )
    recommended_next_step = (
        "freeze admission-carrier encoding exactness before reducing the remaining cache blocker to exact carrier-locality semantics"
    )

    if encoding.exactness_rung == "admission_carrier_encoding_exact":
        exactness_rung = "admission_carrier_locality_exact"
        locality_status = (
            "bounded_inert_record_may_live_only_in_staged_request_locality_before_gate_claim"
        )
        allowed_localities = (
            "adjacent_to_staged_request_metadata_ticket_locality_before_claim",
            "single_staged_request_scoped_locality_before_claim",
            "outside_queue_scheduler_execution_owned_locality_before_claim",
        )
        forbidden_locality_expansions = (
            "no_queue_slot_or_queue_bucket_locality_before_claim",
            "no_scheduler_priority_heap_or_batch_locality_before_claim",
            "no_child_payload_or_stream_handle_locality_before_claim",
            "no_execution_state_or_model_runtime_locality_before_claim",
        )
        residual_blocker = (
            "the pre-claim admission-carrier locality is now exact: before whole-request gate claim the bounded inert pre-claim record may live only in single-request staged locality adjacent to request metadata/ticket state, and it may not occupy queue, scheduler, child/stream, or execution-owned locality on this path"
        )
        recommended_next_step = (
            "treat batching as admission-carrier locality-access exactness work on this path; if a future carrier expands, freeze which exact pre-claim paths may reach that bounded inert record before gate claim without turning locality into hidden queue ownership"
        )

    return CachePreClaimAdmissionCarrierLocalityExactness(
        encoding_exactness=encoding,
        status="partial",
        exactness_rung=exactness_rung,
        locality_status=locality_status,
        allowed_localities=allowed_localities,
        forbidden_locality_expansions=forbidden_locality_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_admission_carrier_locality_exactness_to_dict(
    exactness: CachePreClaimAdmissionCarrierLocalityExactness,
) -> dict[str, object]:
    """Serialize exact pre-claim admission-carrier locality truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_admission_carrier_locality_exactness",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "carrier_locality_boundary",
                "forbidden_locality_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "carrier_locality_boundary": {
            "locality_status": exactness.locality_status,
            "allowed_localities": list(exactness.allowed_localities),
        },
        "forbidden_locality_expansions": list(exactness.forbidden_locality_expansions),
    }
