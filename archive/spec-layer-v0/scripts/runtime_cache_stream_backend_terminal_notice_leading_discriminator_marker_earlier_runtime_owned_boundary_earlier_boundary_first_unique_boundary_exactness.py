#!/usr/bin/env python3
"""Emit runtime-owned earlier-boundary first-unique-boundary exactness."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness_to_dict,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness import (
    CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    first_unique_boundary_harness = None
    if args.run_harness:
        first_unique_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness()
        )

    earlier_boundary_exactness = (
        CacheStreamBackendTerminalNoticeLeadingDiscriminatorMarkerEarlierRuntimeOwnedBoundaryEarlierBoundaryExactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness=object(),  # type: ignore[arg-type]
            status="partial",
            exactness_rung="stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exact",
            verdict="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_introduced",
            earlier_runtime_owned_boundary_earlier_boundary_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection_visible",
            exchange_boundary="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected_before_boundary_stem_detection",
            next_active_dependency="backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_dependency",
            next_active_dependency_status="backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detection",
            preserved_non_stream_handoff_status="cohort_handed_off_to_aggregated_child_exchange_visible",
            residual_blocker="earlier-boundary record introduced ahead of stem",
            recommended_next_step="freeze whether earlier-boundary detection is the first honest unique boundary on the new earlier-boundary record",
        )
    )
    exactness = (
        build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness(
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness=(
                earlier_boundary_exactness
            ),
            backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness=(
                first_unique_boundary_harness
            ),
        )
    )
    payload = (
        cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness_to_dict(
            exactness
        )
    )
    if first_unique_boundary_harness is not None:
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_visible": (
                first_unique_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_visible
            ),
            "leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status": (
                first_unique_boundary_harness.leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_status
            ),
            "shared_non_unique_prefix": (
                first_unique_boundary_harness.shared_non_unique_prefix
            ),
            "first_honest_unique_boundary_prefix": (
                first_unique_boundary_harness.first_honest_unique_boundary_prefix
            ),
            "earlier_literal_prefix_is_not_runtime_owned_earlier_boundary": (
                first_unique_boundary_harness.earlier_literal_prefix_is_not_runtime_owned_earlier_boundary
            ),
        }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
