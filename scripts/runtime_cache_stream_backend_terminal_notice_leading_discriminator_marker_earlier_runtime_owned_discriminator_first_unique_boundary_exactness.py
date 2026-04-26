#!/usr/bin/env python3
"""Emit runtime-owned earlier-discriminator first-unique-boundary exactness."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorStemExactness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    discriminant_harness = None
    first_unique_boundary_harness = None
    if args.run_harness:
        discriminant_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness()
        )
        first_unique_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness()
        )

    discriminant_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorDiscriminantExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness=CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorStemExactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness=object(),  # type: ignore[arg-type]
                status="partial",
                exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exact",
                verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_dependency_narrowed",
                earlier_runtime_owned_discriminator_stem_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection_visible",
                exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection",
                next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_dependency",
                next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection",
                preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
                residual_blocker="the remaining exact stream seam is now closer than earlier-runtime-owned-discriminator prefix detection",
                recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned discriminator discriminant seam",
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_dependency_narrowed",
            earlier_runtime_owned_discriminator_discriminant_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="the remaining exact stream seam is now closer than earlier-runtime-owned-discriminator stem detection",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned discriminator first-unique-boundary seam",
        )
    )
    exactness = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness=(
                discriminant_exactness
            ),
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness=(
                first_unique_boundary_harness
            ),
        )
    )
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness_to_dict(
            exactness
        )
    )
    if discriminant_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_boundary_visible": (
                discriminant_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_boundary_visible
            ),
            "earlier_runtime_owned_discriminator_discriminant_status": (
                discriminant_harness.earlier_runtime_owned_discriminator_discriminant_status
            ),
            "second_stream_blocked_before_terminal_window": (
                discriminant_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected": (
                discriminant_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected": (
                discriminant_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": discriminant_harness.terminal_window_ms,
            "first_stream_events": list(discriminant_harness.first_stream_events),
            "second_stream_events": list(discriminant_harness.second_stream_events),
        }
    if first_unique_boundary_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_visible": (
                first_unique_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_visible
            ),
            "leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_status": (
                first_unique_boundary_harness.leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_status
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
