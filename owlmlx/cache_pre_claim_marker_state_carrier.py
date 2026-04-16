"""Runtime-owned exact inert state-carrier boundary for pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_reader_writer_ownership import (
    CachePreClaimMarkerReaderWriterOwnership,
    build_cache_pre_claim_marker_reader_writer_ownership,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerStateCarrier:
    """Exact runtime truth for the inert carrier that holds pre-claim markers."""

    reader_writer_ownership: CachePreClaimMarkerReaderWriterOwnership
    status: str
    exactness_rung: str
    carrier_status: str
    carrier_semantics_status: str
    allowed_carrier_semantics: tuple[str, ...]
    forbidden_carrier_semantics: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_state_carrier(
    *,
    reader_writer_ownership: CachePreClaimMarkerReaderWriterOwnership | None = None,
) -> CachePreClaimMarkerStateCarrier:
    """Build exact inert state-carrier truth for pre-claim markers."""

    ownership = (
        reader_writer_ownership
        if isinstance(reader_writer_ownership, CachePreClaimMarkerReaderWriterOwnership)
        else build_cache_pre_claim_marker_reader_writer_ownership()
    )

    exactness_rung = "state_carrier_unresolved"
    carrier_status = "not_frozen"
    carrier_semantics_status = "not_frozen"
    allowed_carrier_semantics = ()
    forbidden_carrier_semantics = ()
    residual_blocker = (
        "marker state-carrier exactness is not yet frozen because marker reader/writer ownership is not exact"
    )
    recommended_next_step = (
        "freeze marker reader/writer ownership before reducing the remaining cache blocker to exact state-carrier semantics"
    )

    if ownership.exactness_rung == "reader_writer_ownership_exact":
        exactness_rung = "state_carrier_exact"
        carrier_status = "single_inert_pre_claim_marker_record"
        carrier_semantics_status = (
            "write_once_clear_only_inert_record_before_gate_claim"
        )
        allowed_carrier_semantics = (
            "write_once_marker_record_before_gate_claim",
            "clear_only_before_gate_claim_or_at_gate_claim_expiry",
            "read_only_observation_without_queue_ownership",
        )
        forbidden_carrier_semantics = (
            "no_queue_slot_identity_before_claim",
            "no_batch_membership_before_claim",
            "no_child_payload_attachment_before_claim",
            "no_stream_or_execution_state_attachment_before_claim",
        )
        residual_blocker = (
            "the pre-claim marker state-carrier is now exact: owlmlx may hold a marker only in a single inert write-once/clear-only record before gate claim, and that record may not become a queue slot identity, batch member, child payload attachment, or stream/execution state before the first runtime-owned boundary"
        )
        recommended_next_step = (
            "treat batching as pre-claim marker clear-observer boundary work on this path; if a future seam expands, freeze which path may clear a carrier versus only observe it, without allowing the inert carrier to become hidden queue ownership or execution state"
        )

    return CachePreClaimMarkerStateCarrier(
        reader_writer_ownership=ownership,
        status="partial",
        exactness_rung=exactness_rung,
        carrier_status=carrier_status,
        carrier_semantics_status=carrier_semantics_status,
        allowed_carrier_semantics=allowed_carrier_semantics,
        forbidden_carrier_semantics=forbidden_carrier_semantics,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_state_carrier_to_dict(
    exactness: CachePreClaimMarkerStateCarrier,
) -> dict[str, object]:
    """Serialize exact pre-claim marker state-carrier truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_state_carrier",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "state_carrier_boundary",
                "forbidden_carrier_semantics",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "state_carrier_boundary": {
            "carrier_status": exactness.carrier_status,
            "carrier_semantics_status": exactness.carrier_semantics_status,
            "allowed_carrier_semantics": list(exactness.allowed_carrier_semantics),
        },
        "forbidden_carrier_semantics": list(exactness.forbidden_carrier_semantics),
    }
