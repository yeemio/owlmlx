#!/usr/bin/env python3
"""Emit runtime-owned earlier-boundary first-unique-boundary exactness."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    stem_harness = None
    first_unique_boundary_harness = None
    if args.run_harness:
        stem_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness()
        )
        first_unique_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness()
        )

    stem_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryStemExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness=CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness=object(),  # type: ignore[arg-type]
                status="partial",
                exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exact",
                verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_dependency_narrowed",
                earlier_runtime_owned_boundary_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection_visible",
                exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection",
                next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency",
                next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection",
                preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
                residual_blocker="the remaining exact stream seam is now closer than full earlier-runtime-owned-boundary detection on this path",
                recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned boundary stem seam",
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency_narrowed",
            earlier_runtime_owned_boundary_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="the remaining exact stream seam is now closer than earlier-runtime-owned-boundary prefix detection on this path",
            recommended_next_step="freeze whether backend terminal notice leading discriminator marker earlier runtime-owned boundary stem is already the first honest unique boundary on the newer runtime-owned boundary record",
        )
    )
    exactness = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness=(
                stem_exactness
            ),
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness=(
                first_unique_boundary_harness
            ),
        )
    )
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness_to_dict(
            exactness
        )
    )
    if stem_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible": (
                stem_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible
            ),
            "earlier_runtime_owned_boundary_stem_status": (
                stem_harness.earlier_runtime_owned_boundary_stem_status
            ),
            "second_stream_blocked_before_terminal_window": (
                stem_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected": (
                stem_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected": (
                stem_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                stem_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": stem_harness.terminal_window_ms,
            "first_stream_events": list(stem_harness.first_stream_events),
            "second_stream_events": list(stem_harness.second_stream_events),
        }
    if first_unique_boundary_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_visible": (
                first_unique_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_visible
            ),
            "leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_status": (
                first_unique_boundary_harness.leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_status
            ),
            "shared_non_unique_prefix": (
                first_unique_boundary_harness.shared_non_unique_prefix
            ),
            "first_honest_unique_boundary_prefix": (
                first_unique_boundary_harness.first_honest_unique_boundary_prefix
            ),
            "earlier_literal_prefix_is_not_runtime_owned_boundary": (
                first_unique_boundary_harness.earlier_literal_prefix_is_not_runtime_owned_boundary
            ),
        }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
