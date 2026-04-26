#!/usr/bin/env python3
"""Emit runtime-owned earlier-boundary stem exactness."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorFirstUniqueBoundaryExactness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    earlier_runtime_owned_boundary_harness = None
    prefix_harness = None
    stem_harness = None
    if args.run_harness:
        earlier_runtime_owned_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness()
        )
        prefix_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness()
        )
        stem_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness()
        )

    earlier_runtime_owned_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness=CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedLeadingDiscriminatorFirstUniqueBoundaryExactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness=object(),  # type: ignore[arg-type]
                status="partial",
                exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exact",
                verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_dependency_still_blocked",
                earlier_runtime_owned_leading_discriminator_first_unique_boundary_status="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_is_first_honest_unique_boundary_visible",
                exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_is_first_honest_unique_boundary_visible",
                next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_dependency",
                next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection",
                preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
                residual_blocker="earlier runtime-owned leading-discriminator discriminant remains the first honest unique boundary",
                recommended_next_step="introduce one new earlier runtime-owned boundary if one can be made honest",
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_introduced",
            earlier_runtime_owned_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="owlmlx now owns one new earlier runtime-owned boundary record ahead of the newer runtime-owned leading-discriminator record on this path",
            recommended_next_step="freeze whether backend terminal notice leading discriminator marker earlier-runtime-owned-boundary prefix detection is already the next exact stream seam",
        )
    )
    earlier_runtime_owned_boundary_prefix_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryPrefixExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness=(
                earlier_runtime_owned_boundary_exactness
            ),
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_dependency_narrowed",
            earlier_runtime_owned_boundary_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="earlier runtime-owned boundary prefix now blocks more exactly",
            recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned boundary stem seam",
        )
    )
    exactness = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness=(
                earlier_runtime_owned_boundary_prefix_exactness
            ),
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness=(
                stem_harness
            ),
        )
    )
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness_to_dict(
            exactness
        )
    )
    if earlier_runtime_owned_boundary_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_visible": (
                earlier_runtime_owned_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_visible
            ),
            "earlier_runtime_owned_boundary_status": (
                earlier_runtime_owned_boundary_harness.earlier_runtime_owned_boundary_status
            ),
            "second_stream_blocked_before_terminal_window": (
                earlier_runtime_owned_boundary_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected": (
                earlier_runtime_owned_boundary_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected": (
                earlier_runtime_owned_boundary_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                earlier_runtime_owned_boundary_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": earlier_runtime_owned_boundary_harness.terminal_window_ms,
            "first_stream_events": list(
                earlier_runtime_owned_boundary_harness.first_stream_events
            ),
            "second_stream_events": list(
                earlier_runtime_owned_boundary_harness.second_stream_events
            ),
        }
    if prefix_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_boundary_visible": (
                prefix_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_boundary_visible
            ),
            "earlier_runtime_owned_boundary_prefix_status": (
                prefix_harness.earlier_runtime_owned_boundary_prefix_status
            ),
            "second_stream_blocked_before_terminal_window": (
                prefix_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected": (
                prefix_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected": (
                prefix_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": prefix_harness.terminal_window_ms,
            "first_stream_events": list(prefix_harness.first_stream_events),
            "second_stream_events": list(prefix_harness.second_stream_events),
        }
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
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
