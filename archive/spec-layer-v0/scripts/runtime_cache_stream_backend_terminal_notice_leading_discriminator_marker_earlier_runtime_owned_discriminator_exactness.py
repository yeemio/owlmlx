#!/usr/bin/env python3
"""Emit runtime-owned earlier-discriminator introduction exactness."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    earlier_runtime_owned_discriminator_harness = None
    first_unique_boundary_harness = None
    if args.run_harness:
        earlier_runtime_owned_discriminator_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness()
        )
        first_unique_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness()
        )

    marker_discriminant_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness(
            backend_terminal_notice_leading_discriminator_marker_stem_exactness=object(),  # type: ignore[arg-type]
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_stem_dependency_narrowed",
            leading_discriminator_marker_discriminant_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_stem_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_discriminant_detected_before_notice_leading_discriminator_marker_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker discriminant now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker first unique boundary seam",
        )
    )
    first_unique_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=(
                marker_discriminant_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_discriminant_dependency_still_blocked",
            leading_discriminator_marker_first_unique_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_discriminant_is_first_unique_boundary_visible",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_discriminant_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_discriminant_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="backend terminal notice leading discriminator marker discriminant remains the first honest unique boundary",
            recommended_next_step="introduce a new earlier runtime-owned discriminator if one can be made honest",
        )
    )
    exactness = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness(
            backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness=(
                first_unique_boundary_exactness
            ),
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness=(
                earlier_runtime_owned_discriminator_harness
            ),
        )
    )
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness_to_dict(
            exactness
        )
    )
    if first_unique_boundary_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_visible": (
                first_unique_boundary_harness.backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_visible
            ),
            "leading_discriminator_marker_first_unique_boundary_status": (
                first_unique_boundary_harness.leading_discriminator_marker_first_unique_boundary_status
            ),
            "shared_non_unique_prefix": (
                first_unique_boundary_harness.shared_non_unique_prefix
            ),
            "first_unique_boundary_prefix": (
                first_unique_boundary_harness.first_unique_boundary_prefix
            ),
            "earlier_prefix_collides_with_old_notice_record": (
                first_unique_boundary_harness.earlier_prefix_collides_with_old_notice_record
            ),
        }
    if earlier_runtime_owned_discriminator_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_boundary_visible": (
                earlier_runtime_owned_discriminator_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_boundary_visible
            ),
            "earlier_runtime_owned_discriminator_status": (
                earlier_runtime_owned_discriminator_harness.earlier_runtime_owned_discriminator_status
            ),
            "second_stream_blocked_before_terminal_window": (
                earlier_runtime_owned_discriminator_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected": (
                earlier_runtime_owned_discriminator_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_discriminant_detected": (
                earlier_runtime_owned_discriminator_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                earlier_runtime_owned_discriminator_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                earlier_runtime_owned_discriminator_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                earlier_runtime_owned_discriminator_harness.first_stream_events
            ),
            "second_stream_events": list(
                earlier_runtime_owned_discriminator_harness.second_stream_events
            ),
        }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
