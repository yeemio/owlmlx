#!/usr/bin/env python3
"""Emit runtime-owned earlier-discriminator prefix exactness."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    earlier_runtime_owned_discriminator_harness = None
    prefix_harness = None
    if args.run_harness:
        earlier_runtime_owned_discriminator_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness()
        )
        prefix_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness()
        )

    earlier_runtime_owned_discriminator_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness(
            backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness=CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness(
                backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=object(),  # type: ignore[arg-type]
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
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_introduced",
            earlier_runtime_owned_discriminator_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected_before_notice_leading_discriminator_marker_discriminant_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="owlmlx now owns a new earlier runtime-owned terminal-notice discriminator record ahead of the current marker-discriminant seam",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned discriminator seam",
        )
    )
    exactness = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness=(
                earlier_runtime_owned_discriminator_exactness
            ),
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness=(
                prefix_harness
            ),
        )
    )
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness_to_dict(
            exactness
        )
    )
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
    if prefix_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_boundary_visible": (
                prefix_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_boundary_visible
            ),
            "earlier_runtime_owned_discriminator_prefix_status": (
                prefix_harness.earlier_runtime_owned_discriminator_prefix_status
            ),
            "second_stream_blocked_before_terminal_window": (
                prefix_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected": (
                prefix_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected": (
                prefix_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": prefix_harness.terminal_window_ms,
            "first_stream_events": list(prefix_harness.first_stream_events),
            "second_stream_events": list(prefix_harness.second_stream_events),
        }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
