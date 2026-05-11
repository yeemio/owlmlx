#!/usr/bin/env python3
"""Emit runtime-owned backend leading-discriminator marker first-unique-boundary exactness."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerDiscriminantExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    marker_discriminant_harness = None
    first_unique_boundary_harness = None
    if args.run_harness:
        marker_discriminant_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_harness()
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
    exactness = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=(
                marker_discriminant_exactness
            ),
            backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness=(
                first_unique_boundary_harness
            ),
        )
    )
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness_to_dict(
            exactness
        )
    )
    if marker_discriminant_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_discriminant_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_discriminant_boundary_visible": (
                marker_discriminant_harness.backend_terminal_notice_leading_discriminator_marker_discriminant_boundary_visible
            ),
            "leading_discriminator_marker_discriminant_status": (
                marker_discriminant_harness.leading_discriminator_marker_discriminant_status
            ),
            "second_stream_blocked_before_terminal_window": (
                marker_discriminant_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_discriminant_detected": (
                marker_discriminant_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_stem_detected": (
                marker_discriminant_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                marker_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": marker_discriminant_harness.terminal_window_ms,
            "first_stream_events": list(marker_discriminant_harness.first_stream_events),
            "second_stream_events": list(marker_discriminant_harness.second_stream_events),
        }
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
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
