#!/usr/bin/env python3
"""Emit runtime-owned earlier-discriminator discriminant exactness."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorPrefixExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorStemExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerFirstUniqueBoundaryExactness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    stem_harness = None
    discriminant_harness = None
    if args.run_harness:
        stem_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness()
        )
        discriminant_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness()
        )

    stem_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorStemExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness=CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorPrefixExactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness=CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedDiscriminatorExactness(
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
                ),
                status="partial",
                exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exact",
                verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_dependency_narrowed",
                earlier_runtime_owned_discriminator_prefix_status="backend_serial_boundary_decoupled_from_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection_visible",
                exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected_before_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detection",
                next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_dependency",
                next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detection",
                preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
                residual_blocker="the remaining exact stream seam is now closer than full earlier-runtime-owned-discriminator detection",
                recommended_next_step="freeze backend terminal notice leading discriminator marker earlier runtime-owned discriminator stem seam",
            ),
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
        )
    )
    exactness = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness=(
                stem_exactness
            ),
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness=(
                discriminant_harness
            ),
        )
    )
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness_to_dict(
            exactness
        )
    )
    if stem_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_boundary_visible": (
                stem_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_boundary_visible
            ),
            "earlier_runtime_owned_discriminator_stem_status": (
                stem_harness.earlier_runtime_owned_discriminator_stem_status
            ),
            "second_stream_blocked_before_terminal_window": (
                stem_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected": (
                stem_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected": (
                stem_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                stem_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": stem_harness.terminal_window_ms,
            "first_stream_events": list(stem_harness.first_stream_events),
            "second_stream_events": list(stem_harness.second_stream_events),
        }
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
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
