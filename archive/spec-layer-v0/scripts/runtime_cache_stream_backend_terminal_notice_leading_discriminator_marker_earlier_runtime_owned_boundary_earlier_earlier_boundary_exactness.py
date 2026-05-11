#!/usr/bin/env python3
"""Emit runtime-owned earlier-earlier-boundary exactness."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryExactness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    earlier_earlier_boundary_harness = None
    if args.run_harness:
        earlier_earlier_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness()
        )

    first_unique_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryFirstUniqueBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness=object(),  # type: ignore[arg-type]
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency_still_blocked",
            earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_is_first_honest_unique_boundary_visible",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="earlier-boundary detection is the first honest unique boundary on the newer earlier-boundary record",
            recommended_next_step="introduce one new earlier-earlier runtime-owned boundary",
        )
    )
    exactness = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness=(
                first_unique_boundary_exactness
            ),
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness=(
                earlier_earlier_boundary_harness
            ),
        )
    )
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness_to_dict(
            exactness
        )
    )
    if earlier_earlier_boundary_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_visible": (
                earlier_earlier_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_visible
            ),
            "earlier_runtime_owned_boundary_earlier_earlier_boundary_status": (
                earlier_earlier_boundary_harness.earlier_runtime_owned_boundary_earlier_earlier_boundary_status
            ),
            "second_stream_blocked_before_terminal_window": (
                earlier_earlier_boundary_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detected": (
                earlier_earlier_boundary_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected": (
                earlier_earlier_boundary_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                earlier_earlier_boundary_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": earlier_earlier_boundary_harness.terminal_window_ms,
            "first_stream_events": list(earlier_earlier_boundary_harness.first_stream_events),
            "second_stream_events": list(earlier_earlier_boundary_harness.second_stream_events),
        }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
