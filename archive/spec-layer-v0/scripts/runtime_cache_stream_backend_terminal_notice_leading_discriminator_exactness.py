#!/usr/bin/env python3
"""Emit exact backend terminal-notice leading-discriminator truth for owlmlx cache closure."""

from __future__ import annotations

import argparse
import json

from owlmlx import (
    build_cache_batching_mechanism_subgap,
    build_cache_child_exchange_aggregated_dispatch_exactness,
    build_cache_cohort_to_child_exchange_handoff_exactness,
    build_cache_continuous_batching_feasibility,
    build_cache_counter_feasibility,
    build_cache_counter_gap,
    build_cache_request_aggregation_window_exactness,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    build_cache_stream_backend_terminal_action_discriminant_exactness,
    build_cache_stream_backend_terminal_event_exactness,
    build_cache_stream_backend_terminal_notice_action_discriminant_exactness,
    build_cache_stream_backend_terminal_notice_action_stem_exactness,
    build_cache_stream_backend_terminal_notice_capture_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_exactness,
    build_cache_stream_backend_terminal_notice_marker_discriminant_exactness,
    build_cache_stream_backend_terminal_notice_marker_exactness,
    build_cache_stream_backend_terminal_notice_marker_key_lead_exactness,
    build_cache_stream_backend_terminal_notice_marker_prefix_exactness,
    build_cache_stream_backend_terminal_notice_marker_stem_exactness,
    build_cache_stream_backend_terminal_notice_prefix_exactness,
    build_cache_stream_backend_terminal_payload_capture_exactness,
    build_cache_stream_backend_terminal_payload_commit_exactness,
    build_cache_stream_backend_terminal_record_capture_exactness,
    build_cache_stream_backend_terminal_record_prefix_exactness,
    build_cache_stream_hold_dependency_exactness,
    cache_stream_backend_terminal_notice_leading_discriminator_exactness_to_dict,
)
from owlmlx.cache_child_exchange_aggregated_dispatch_harness import (
    run_cache_child_exchange_aggregated_dispatch_harness,
)
from owlmlx.cache_cohort_to_child_exchange_handoff_harness import (
    run_cache_cohort_to_child_exchange_handoff_harness,
)
from owlmlx.cache_pre_gate_admission_hook_harness import (
    run_pre_gate_admission_hook_harness,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)
from owlmlx.cache_stream_backend_terminal_action_discriminant_harness import (
    run_cache_stream_backend_terminal_action_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_event_harness import (
    run_cache_stream_backend_terminal_event_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_action_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_action_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_action_stem_harness import (
    run_cache_stream_backend_terminal_notice_action_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_capture_harness import (
    run_cache_stream_backend_terminal_notice_capture_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_marker_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_harness import (
    run_cache_stream_backend_terminal_notice_marker_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_key_lead_harness import (
    run_cache_stream_backend_terminal_notice_marker_key_lead_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_prefix_harness import (
    run_cache_stream_backend_terminal_notice_marker_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_stem_harness import (
    run_cache_stream_backend_terminal_notice_marker_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_prefix_harness import (
    run_cache_stream_backend_terminal_notice_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_payload_capture_harness import (
    run_cache_stream_backend_terminal_payload_capture_harness,
)
from owlmlx.cache_stream_backend_terminal_payload_commit_harness import (
    run_cache_stream_backend_terminal_payload_commit_harness,
)
from owlmlx.cache_stream_backend_terminal_record_capture_harness import (
    run_cache_stream_backend_terminal_record_capture_harness,
)
from owlmlx.cache_stream_backend_terminal_record_prefix_harness import (
    run_cache_stream_backend_terminal_record_prefix_harness,
)
from owlmlx.cache_stream_hold_dependency_harness import (
    run_cache_stream_hold_dependency_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit owlmlx backend terminal-notice leading-discriminator exactness."
    )
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    if args.run_harness:
        cache_harness = run_cache_runtime_observation_harness()
        hook_harness = run_pre_gate_admission_hook_harness()
        child_exchange_harness = run_cache_child_exchange_aggregated_dispatch_harness()
        handoff_harness = run_cache_cohort_to_child_exchange_handoff_harness()
        stream_hold_harness = run_cache_stream_hold_dependency_harness()
        backend_terminal_event_harness = (
            run_cache_stream_backend_terminal_event_harness()
        )
        backend_terminal_payload_commit_harness = (
            run_cache_stream_backend_terminal_payload_commit_harness()
        )
        backend_terminal_payload_capture_harness = (
            run_cache_stream_backend_terminal_payload_capture_harness()
        )
        backend_terminal_record_capture_harness = (
            run_cache_stream_backend_terminal_record_capture_harness()
        )
        backend_terminal_record_prefix_harness = (
            run_cache_stream_backend_terminal_record_prefix_harness()
        )
        backend_terminal_action_discriminant_harness = (
            run_cache_stream_backend_terminal_action_discriminant_harness()
        )
        backend_terminal_notice_capture_harness = (
            run_cache_stream_backend_terminal_notice_capture_harness()
        )
        backend_terminal_notice_prefix_harness = (
            run_cache_stream_backend_terminal_notice_prefix_harness()
        )
        backend_terminal_notice_action_discriminant_harness = (
            run_cache_stream_backend_terminal_notice_action_discriminant_harness()
        )
        backend_terminal_notice_action_stem_harness = (
            run_cache_stream_backend_terminal_notice_action_stem_harness()
        )
        backend_terminal_notice_marker_harness = (
            run_cache_stream_backend_terminal_notice_marker_harness()
        )
        backend_terminal_notice_marker_prefix_harness = (
            run_cache_stream_backend_terminal_notice_marker_prefix_harness()
        )
        backend_terminal_notice_marker_stem_harness = (
            run_cache_stream_backend_terminal_notice_marker_stem_harness()
        )
        backend_terminal_notice_marker_discriminant_harness = (
            run_cache_stream_backend_terminal_notice_marker_discriminant_harness()
        )
        backend_terminal_notice_marker_key_lead_harness = (
            run_cache_stream_backend_terminal_notice_marker_key_lead_harness()
        )
        backend_terminal_notice_leading_discriminator_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_harness()
        )
        counter_gap = build_cache_counter_gap(
            closure=cache_harness.closure,
            backend_observations=cache_harness.backend_observations,
        )
        counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
        split = build_cache_scheduler_turboquant_split(
            counter_feasibility=counter_feasibility,
            scheduler=cache_harness.closure.scheduler,
            turboquant=cache_harness.turboquant,
        )
        floor_gap = build_cache_scheduler_floor_gap(split=split)
        backlog = build_cache_scheduler_implementation_backlog(floor_gap=floor_gap)
        branch_selection = build_cache_scheduler_branch_selection(
            scheduler_backlog=backlog
        )
        feasibility = build_cache_continuous_batching_feasibility(
            branch_selection=branch_selection
        )
        mechanism_subgap = build_cache_batching_mechanism_subgap(
            feasibility=feasibility
        )
        window_exactness = build_cache_request_aggregation_window_exactness(
            mechanism_subgap=mechanism_subgap,
            hook_harness=hook_harness,
            child_exchange_harness=child_exchange_harness,
            handoff_harness=handoff_harness,
        )
        child_exchange_exactness = build_cache_child_exchange_aggregated_dispatch_exactness(
            request_aggregation_window_exactness=window_exactness,
            child_exchange_harness=child_exchange_harness,
        )
        handoff_exactness = build_cache_cohort_to_child_exchange_handoff_exactness(
            child_exchange_exactness=child_exchange_exactness,
            handoff_harness=handoff_harness,
        )
        stream_hold_exactness = build_cache_stream_hold_dependency_exactness(
            cohort_handoff_exactness=handoff_exactness,
            stream_hold_harness=stream_hold_harness,
        )
        backend_terminal_event_exactness = (
            build_cache_stream_backend_terminal_event_exactness(
                stream_hold_exactness=stream_hold_exactness,
                backend_terminal_event_harness=backend_terminal_event_harness,
            )
        )
        backend_terminal_payload_commit_exactness = (
            build_cache_stream_backend_terminal_payload_commit_exactness(
                backend_terminal_event_exactness=backend_terminal_event_exactness,
                backend_terminal_payload_commit_harness=(
                    backend_terminal_payload_commit_harness
                ),
            )
        )
        backend_terminal_payload_capture_exactness = (
            build_cache_stream_backend_terminal_payload_capture_exactness(
                backend_terminal_payload_commit_exactness=(
                    backend_terminal_payload_commit_exactness
                ),
                backend_terminal_payload_capture_harness=(
                    backend_terminal_payload_capture_harness
                ),
            )
        )
        backend_terminal_record_capture_exactness = (
            build_cache_stream_backend_terminal_record_capture_exactness(
                backend_terminal_payload_capture_exactness=(
                    backend_terminal_payload_capture_exactness
                ),
                backend_terminal_record_capture_harness=(
                    backend_terminal_record_capture_harness
                ),
            )
        )
        backend_terminal_record_prefix_exactness = (
            build_cache_stream_backend_terminal_record_prefix_exactness(
                backend_terminal_record_capture_exactness=(
                    backend_terminal_record_capture_exactness
                ),
                backend_terminal_record_prefix_harness=(
                    backend_terminal_record_prefix_harness
                ),
            )
        )
        backend_terminal_action_discriminant_exactness = (
            build_cache_stream_backend_terminal_action_discriminant_exactness(
                backend_terminal_record_prefix_exactness=(
                    backend_terminal_record_prefix_exactness
                ),
                backend_terminal_action_discriminant_harness=(
                    backend_terminal_action_discriminant_harness
                ),
            )
        )
        backend_terminal_notice_capture_exactness = (
            build_cache_stream_backend_terminal_notice_capture_exactness(
                backend_terminal_action_discriminant_exactness=(
                    backend_terminal_action_discriminant_exactness
                ),
                backend_terminal_notice_capture_harness=(
                    backend_terminal_notice_capture_harness
                ),
            )
        )
        backend_terminal_notice_prefix_exactness = (
            build_cache_stream_backend_terminal_notice_prefix_exactness(
                backend_terminal_notice_capture_exactness=(
                    backend_terminal_notice_capture_exactness
                ),
                backend_terminal_notice_prefix_harness=(
                    backend_terminal_notice_prefix_harness
                ),
            )
        )
        backend_terminal_notice_action_discriminant_exactness = (
            build_cache_stream_backend_terminal_notice_action_discriminant_exactness(
                backend_terminal_notice_prefix_exactness=(
                    backend_terminal_notice_prefix_exactness
                ),
                backend_terminal_notice_action_discriminant_harness=(
                    backend_terminal_notice_action_discriminant_harness
                ),
            )
        )
        backend_terminal_notice_action_stem_exactness = (
            build_cache_stream_backend_terminal_notice_action_stem_exactness(
                backend_terminal_notice_action_discriminant_exactness=(
                    backend_terminal_notice_action_discriminant_exactness
                ),
                backend_terminal_notice_action_stem_harness=(
                    backend_terminal_notice_action_stem_harness
                ),
            )
        )
        backend_terminal_notice_marker_exactness = (
            build_cache_stream_backend_terminal_notice_marker_exactness(
                backend_terminal_notice_action_stem_exactness=(
                    backend_terminal_notice_action_stem_exactness
                ),
                backend_terminal_notice_marker_harness=(
                    backend_terminal_notice_marker_harness
                ),
            )
        )
        backend_terminal_notice_marker_prefix_exactness = (
            build_cache_stream_backend_terminal_notice_marker_prefix_exactness(
                backend_terminal_notice_marker_exactness=(
                    backend_terminal_notice_marker_exactness
                ),
                backend_terminal_notice_marker_prefix_harness=(
                    backend_terminal_notice_marker_prefix_harness
                ),
            )
        )
        backend_terminal_notice_marker_stem_exactness = (
            build_cache_stream_backend_terminal_notice_marker_stem_exactness(
                backend_terminal_notice_marker_prefix_exactness=(
                    backend_terminal_notice_marker_prefix_exactness
                ),
                backend_terminal_notice_marker_stem_harness=(
                    backend_terminal_notice_marker_stem_harness
                ),
            )
        )
        backend_terminal_notice_marker_discriminant_exactness = (
            build_cache_stream_backend_terminal_notice_marker_discriminant_exactness(
                backend_terminal_notice_marker_stem_exactness=(
                    backend_terminal_notice_marker_stem_exactness
                ),
                backend_terminal_notice_marker_discriminant_harness=(
                    backend_terminal_notice_marker_discriminant_harness
                ),
            )
        )
        backend_terminal_notice_marker_key_lead_exactness = (
            build_cache_stream_backend_terminal_notice_marker_key_lead_exactness(
                backend_terminal_notice_marker_discriminant_exactness=(
                    backend_terminal_notice_marker_discriminant_exactness
                ),
                backend_terminal_notice_marker_key_lead_harness=(
                    backend_terminal_notice_marker_key_lead_harness
                ),
            )
        )
        exactness = build_cache_stream_backend_terminal_notice_leading_discriminator_exactness(
            backend_terminal_notice_marker_key_lead_exactness=(
                backend_terminal_notice_marker_key_lead_exactness
            ),
            backend_terminal_notice_leading_discriminator_harness=(
                backend_terminal_notice_leading_discriminator_harness
            ),
        )
        payload = cache_stream_backend_terminal_notice_leading_discriminator_exactness_to_dict(
            exactness
        )
        payload["backend_terminal_notice_leading_discriminator_harness"] = {
            "backend_terminal_notice_leading_discriminator_boundary_visible": (
                backend_terminal_notice_leading_discriminator_harness.backend_terminal_notice_leading_discriminator_boundary_visible
            ),
            "leading_discriminator_status": (
                backend_terminal_notice_leading_discriminator_harness.leading_discriminator_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_detected": (
                backend_terminal_notice_leading_discriminator_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_marker_key_lead_detected": (
                backend_terminal_notice_leading_discriminator_harness.second_stream_request_written_before_first_terminal_notice_marker_key_lead_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_harness.second_stream_events
            ),
        }
    else:
        payload = cache_stream_backend_terminal_notice_leading_discriminator_exactness_to_dict(
            build_cache_stream_backend_terminal_notice_leading_discriminator_exactness()
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
