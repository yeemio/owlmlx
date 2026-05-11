"""Runtime-owned exact reader/writer ownership for inert pre-claim markers."""

from __future__ import annotations

from dataclasses import dataclass

from .cache_pre_claim_marker_trigger_inputs import (
    CachePreClaimMarkerTriggerInputs,
    build_cache_pre_claim_marker_trigger_inputs,
)


@dataclass(frozen=True, slots=True)
class CachePreClaimMarkerReaderWriterOwnership:
    """Exact runtime truth for pre-claim marker reader/writer ownership."""

    trigger_inputs: CachePreClaimMarkerTriggerInputs
    status: str
    exactness_rung: str
    writer_ownership_status: str
    reader_ownership_status: str
    allowed_writer_paths: tuple[str, ...]
    allowed_reader_only_paths: tuple[str, ...]
    forbidden_writer_expansions: tuple[str, ...]
    residual_blocker: str | None
    recommended_next_step: str


def build_cache_pre_claim_marker_reader_writer_ownership(
    *,
    trigger_inputs: CachePreClaimMarkerTriggerInputs | None = None,
) -> CachePreClaimMarkerReaderWriterOwnership:
    """Build exact pre-claim marker reader/writer ownership truth."""

    inputs = (
        trigger_inputs
        if isinstance(trigger_inputs, CachePreClaimMarkerTriggerInputs)
        else build_cache_pre_claim_marker_trigger_inputs()
    )

    exactness_rung = "reader_writer_ownership_unresolved"
    writer_ownership_status = "not_frozen"
    reader_ownership_status = "not_frozen"
    allowed_writer_paths = ()
    allowed_reader_only_paths = ()
    forbidden_writer_expansions = ()
    residual_blocker = (
        "marker reader/writer ownership is not yet frozen because trigger-input exactness is not exact"
    )
    recommended_next_step = (
        "freeze marker trigger inputs before reducing the remaining cache blocker to exact reader/writer ownership"
    )

    if inputs.exactness_rung == "trigger_inputs_exact":
        exactness_rung = "reader_writer_ownership_exact"
        writer_ownership_status = (
            "writer_paths_limited_to_explicit_pre_claim_drop_cancel_and_gate_claim_expiry"
        )
        reader_ownership_status = (
            "reader_paths_limited_to_writer_paths_plus_pre_claim_discard_observation"
        )
        allowed_writer_paths = (
            "explicit_pre_claim_drop_cancel_writer",
            "gate_claim_expiry_writer",
        )
        allowed_reader_only_paths = ("pre_claim_discard_observer",)
        forbidden_writer_expansions = (
            "no_scheduler_writer_before_claim",
            "no_child_backend_writer_before_claim",
            "no_stream_writer_before_claim",
            "no_execution_priority_writer_before_claim",
        )
        residual_blocker = (
            "the pre-claim marker reader/writer ownership is now exact: only explicit pre-claim drop/cancel logic and gate-claim expiry may author a marker, pre-claim discard may only observe it, and scheduler, child/backend, stream, or execution-priority paths may not gain writer ownership before the first runtime-owned boundary"
        )
        recommended_next_step = (
            "treat batching as pre-claim marker state-carrier work on this path; if a future seam expands, freeze the exact inert state carrier and write-once/clear-only boundary without allowing writer ownership to become hidden queue ownership or execution routing"
        )

    return CachePreClaimMarkerReaderWriterOwnership(
        trigger_inputs=inputs,
        status="partial",
        exactness_rung=exactness_rung,
        writer_ownership_status=writer_ownership_status,
        reader_ownership_status=reader_ownership_status,
        allowed_writer_paths=allowed_writer_paths,
        allowed_reader_only_paths=allowed_reader_only_paths,
        forbidden_writer_expansions=forbidden_writer_expansions,
        residual_blocker=residual_blocker,
        recommended_next_step=recommended_next_step,
    )


def cache_pre_claim_marker_reader_writer_ownership_to_dict(
    exactness: CachePreClaimMarkerReaderWriterOwnership,
) -> dict[str, object]:
    """Serialize exact pre-claim marker reader/writer ownership truth."""

    return {
        "contract": {
            "surface": "owlmlx.cache_pre_claim_marker_reader_writer_ownership",
            "version": "phase45",
            "stable_sections": [
                "summary",
                "reader_writer_boundary",
                "forbidden_writer_expansions",
            ],
        },
        "summary": {
            "status": exactness.status,
            "exactness_rung": exactness.exactness_rung,
            "residual_blocker": exactness.residual_blocker,
            "recommended_next_step": exactness.recommended_next_step,
        },
        "reader_writer_boundary": {
            "writer_ownership_status": exactness.writer_ownership_status,
            "reader_ownership_status": exactness.reader_ownership_status,
            "allowed_writer_paths": list(exactness.allowed_writer_paths),
            "allowed_reader_only_paths": list(exactness.allowed_reader_only_paths),
        },
        "forbidden_writer_expansions": list(exactness.forbidden_writer_expansions),
    }
