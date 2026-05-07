#!/usr/bin/env python3
"""Emit runtime-owned request-aggregation active seam truth."""

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
    build_cache_request_aggregation_active_seam,
    build_cache_request_aggregation_window_exactness,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
    build_cache_scheduler_turboquant_split,
    build_cache_stream_backend_terminal_action_discriminant_exactness,
    build_cache_stream_backend_terminal_event_exactness,
    build_cache_stream_backend_terminal_notice_action_discriminant_exactness,
    build_cache_stream_backend_terminal_notice_action_stem_exactness,
    build_cache_stream_backend_terminal_notice_marker_exactness,
    build_cache_stream_backend_terminal_notice_marker_discriminant_exactness,
    build_cache_stream_backend_terminal_notice_marker_key_lead_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness,
    build_cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness,
    build_cache_stream_backend_terminal_notice_marker_prefix_exactness,
    build_cache_stream_backend_terminal_notice_marker_stem_exactness,
    build_cache_stream_backend_terminal_notice_capture_exactness,
    build_cache_stream_backend_terminal_notice_prefix_exactness,
    build_cache_stream_backend_terminal_payload_capture_exactness,
    build_cache_stream_backend_terminal_payload_commit_exactness,
    build_cache_stream_backend_terminal_record_capture_exactness,
    build_cache_stream_backend_terminal_record_prefix_exactness,
    build_cache_stream_hold_dependency_exactness,
    cache_request_aggregation_active_seam_to_dict,
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
from owlmlx.cache_request_aggregation_window_reentry import (
    CacheRequestAggregationWindowReentry,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)
from owlmlx.cache_stream_hold_dependency_harness import (
    run_cache_stream_hold_dependency_harness,
)
from owlmlx.cache_stream_backend_terminal_event_harness import (
    run_cache_stream_backend_terminal_event_harness,
)
from owlmlx.cache_stream_backend_terminal_payload_commit_harness import (
    run_cache_stream_backend_terminal_payload_commit_harness,
)
from owlmlx.cache_stream_backend_terminal_payload_capture_harness import (
    run_cache_stream_backend_terminal_payload_capture_harness,
)
from owlmlx.cache_stream_backend_terminal_record_capture_harness import (
    run_cache_stream_backend_terminal_record_capture_harness,
)
from owlmlx.cache_stream_backend_terminal_record_prefix_harness import (
    run_cache_stream_backend_terminal_record_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_action_discriminant_harness import (
    run_cache_stream_backend_terminal_action_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_capture_harness import (
    run_cache_stream_backend_terminal_notice_capture_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_prefix_harness import (
    run_cache_stream_backend_terminal_notice_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_action_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_action_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_action_stem_harness import (
    run_cache_stream_backend_terminal_notice_action_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_harness import (
    run_cache_stream_backend_terminal_notice_marker_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_prefix_harness import (
    run_cache_stream_backend_terminal_notice_marker_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_marker_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_key_lead_harness import (
    run_cache_stream_backend_terminal_notice_marker_key_lead_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_prefix_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_stem_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_stem_harness import (
    run_cache_stream_backend_terminal_notice_marker_stem_harness,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-harness", action="store_true")
    args = parser.parse_args()

    if args.run_harness:
        harness = run_cache_runtime_observation_harness()
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
        backend_terminal_notice_marker_discriminant_harness = (
            run_cache_stream_backend_terminal_notice_marker_discriminant_harness()
        )
        backend_terminal_notice_marker_key_lead_harness = (
            run_cache_stream_backend_terminal_notice_marker_key_lead_harness()
        )
        backend_terminal_notice_leading_discriminator_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_harness()
        )
        backend_terminal_notice_leading_discriminator_prefix_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_prefix_harness()
        )
        backend_terminal_notice_leading_discriminator_stem_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_stem_harness()
        )
        backend_terminal_notice_leading_discriminator_discriminant_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_prefix_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_discriminant_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness()
        )
        backend_terminal_notice_leading_discriminator_marker_stem_harness = (
            run_cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_harness()
        )
        backend_terminal_notice_marker_stem_harness = (
            run_cache_stream_backend_terminal_notice_marker_stem_harness()
        )
        counter_gap = build_cache_counter_gap(
            closure=harness.closure,
            backend_observations=harness.backend_observations,
        )
        counter_feasibility = build_cache_counter_feasibility(counter_gap=counter_gap)
        split = build_cache_scheduler_turboquant_split(
            counter_feasibility=counter_feasibility,
            scheduler=harness.closure.scheduler,
            turboquant=harness.turboquant,
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
        aggregation_exactness = build_cache_request_aggregation_window_exactness(
            mechanism_subgap=mechanism_subgap,
            hook_harness=hook_harness,
            child_exchange_harness=child_exchange_harness,
            handoff_harness=handoff_harness,
        )
        child_exchange_exactness = build_cache_child_exchange_aggregated_dispatch_exactness(
            request_aggregation_window_exactness=aggregation_exactness,
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
        backend_terminal_notice_leading_discriminator_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_exactness(
                backend_terminal_notice_marker_key_lead_exactness=(
                    backend_terminal_notice_marker_key_lead_exactness
                ),
                backend_terminal_notice_leading_discriminator_harness=(
                    backend_terminal_notice_leading_discriminator_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_prefix_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_prefix_exactness(
                backend_terminal_notice_leading_discriminator_exactness=(
                    backend_terminal_notice_leading_discriminator_exactness
                ),
                backend_terminal_notice_leading_discriminator_prefix_harness=(
                    backend_terminal_notice_leading_discriminator_prefix_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_stem_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_stem_exactness(
                backend_terminal_notice_leading_discriminator_prefix_exactness=(
                    backend_terminal_notice_leading_discriminator_prefix_exactness
                ),
                backend_terminal_notice_leading_discriminator_stem_harness=(
                    backend_terminal_notice_leading_discriminator_stem_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_discriminant_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_discriminant_exactness(
                backend_terminal_notice_leading_discriminator_stem_exactness=(
                    backend_terminal_notice_leading_discriminator_stem_exactness
                ),
                backend_terminal_notice_leading_discriminator_discriminant_harness=(
                    backend_terminal_notice_leading_discriminator_discriminant_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_exactness(
                backend_terminal_notice_leading_discriminator_discriminant_exactness=(
                    backend_terminal_notice_leading_discriminator_discriminant_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_harness=(
                    backend_terminal_notice_leading_discriminator_marker_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_prefix_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness(
                backend_terminal_notice_leading_discriminator_marker_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_prefix_harness=(
                    backend_terminal_notice_leading_discriminator_marker_prefix_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_stem_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness(
                backend_terminal_notice_leading_discriminator_marker_prefix_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_prefix_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_stem_harness=(
                    backend_terminal_notice_leading_discriminator_marker_stem_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_discriminant_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness(
                backend_terminal_notice_leading_discriminator_marker_stem_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_stem_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_discriminant_harness=(
                    backend_terminal_notice_leading_discriminator_marker_discriminant_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_discriminant_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness=(
                    backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness(
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_harness
                ),
            )
        )
        backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness = (
            build_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness
                ),
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness
                ),
            )
        )
        reentry = CacheRequestAggregationWindowReentry(
            continuous_batching_branch_reduction=object(),
            request_aggregation_window_exactness=aggregation_exactness,
            status="partial",
            reentry_rung="aggregation_reentry_exact",
            selected_reentry_target="request_aggregation_window",
            selected_reentry_target_status="reentered_as_active_cache_subchain",
            preserved_secondary_scheduler_reduction=(
                "shared_prefill_batch_step",
                "interleaved_decode_scheduler",
            ),
            preserved_secondary_runtime_branch="turboquant_preconditions",
            preserved_secondary_runtime_branch_status="preconditions_exact",
            residual_blocker="request aggregation reentered",
            recommended_next_step="active seam",
        )
        payload = cache_request_aggregation_active_seam_to_dict(
            build_cache_request_aggregation_active_seam(
                request_aggregation_window_reentry=reentry,
                request_aggregation_window_exactness=aggregation_exactness,
                child_exchange_exactness=child_exchange_exactness,
                cohort_handoff_exactness=handoff_exactness,
                stream_hold_exactness=stream_hold_exactness,
                stream_backend_terminal_event_exactness=backend_terminal_event_exactness,
                stream_backend_terminal_payload_commit_exactness=(
                    backend_terminal_payload_commit_exactness
                ),
                stream_backend_terminal_payload_capture_exactness=(
                    backend_terminal_payload_capture_exactness
                ),
                stream_backend_terminal_record_capture_exactness=(
                    backend_terminal_record_capture_exactness
                ),
                stream_backend_terminal_record_prefix_exactness=(
                    backend_terminal_record_prefix_exactness
                ),
                stream_backend_terminal_action_discriminant_exactness=(
                    backend_terminal_action_discriminant_exactness
                ),
                stream_backend_terminal_notice_capture_exactness=(
                    backend_terminal_notice_capture_exactness
                ),
                stream_backend_terminal_notice_prefix_exactness=(
                    backend_terminal_notice_prefix_exactness
                ),
                stream_backend_terminal_notice_action_discriminant_exactness=(
                    backend_terminal_notice_action_discriminant_exactness
                ),
                stream_backend_terminal_notice_action_stem_exactness=(
                    backend_terminal_notice_action_stem_exactness
                ),
                stream_backend_terminal_notice_marker_exactness=(
                    backend_terminal_notice_marker_exactness
                ),
                stream_backend_terminal_notice_marker_prefix_exactness=(
                    backend_terminal_notice_marker_prefix_exactness
                ),
                stream_backend_terminal_notice_marker_stem_exactness=(
                    backend_terminal_notice_marker_stem_exactness
                ),
                stream_backend_terminal_notice_marker_discriminant_exactness=(
                    backend_terminal_notice_marker_discriminant_exactness
                ),
                stream_backend_terminal_notice_marker_key_lead_exactness=(
                    backend_terminal_notice_marker_key_lead_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_exactness=(
                    backend_terminal_notice_leading_discriminator_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_prefix_exactness=(
                    backend_terminal_notice_leading_discriminator_prefix_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_stem_exactness=(
                    backend_terminal_notice_leading_discriminator_stem_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_discriminant_exactness=(
                    backend_terminal_notice_leading_discriminator_discriminant_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_prefix_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_prefix_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_discriminant_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_discriminant_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_first_unique_boundary_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_first_unique_boundary_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness
                ),
                stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness=(
                    backend_terminal_notice_leading_discriminator_marker_stem_exactness
                ),
            )
        )
        payload["cache_harness"] = harness.backend_observations
        payload["pre_gate_hook_harness"] = {
            "runtime_owned_hook_present": hook_harness.runtime_owned_hook_present,
            "hook_boundary": hook_harness.hook_boundary,
            "hook_mode": hook_harness.hook_mode,
            "cohort_window_status": hook_harness.cohort_window_status,
            "observed_peak_cohort_size": hook_harness.observed_peak_cohort_size,
            "observed_total_cohorts_formed": hook_harness.observed_total_cohorts_formed,
            "aggregation_scope": hook_harness.aggregation_scope,
        }
        payload["child_exchange_harness"] = {
            "aggregated_dispatch_visible": child_exchange_harness.aggregated_dispatch_visible,
            "child_exchange_mode": child_exchange_harness.child_exchange_mode,
            "exchange_count": child_exchange_harness.exchange_count,
            "batch_size": child_exchange_harness.batch_size,
            "aggregated_request_count": child_exchange_harness.aggregated_request_count,
            "max_aggregated_batch_size": child_exchange_harness.max_aggregated_batch_size,
            "stream_secondary_status": child_exchange_harness.stream_secondary_status,
        }
        payload["cohort_handoff_harness"] = {
            "cohort_handoff_visible": handoff_harness.cohort_handoff_visible,
            "handoff_status": handoff_harness.handoff_status,
            "aggregated_batch_count": handoff_harness.aggregated_batch_count,
            "aggregated_request_count": handoff_harness.aggregated_request_count,
            "max_aggregated_batch_size": handoff_harness.max_aggregated_batch_size,
            "handoff_request_count": handoff_harness.handoff_request_count,
            "stream_secondary_status": handoff_harness.stream_secondary_status,
        }
        payload["stream_hold_harness"] = {
            "hold_dependency_narrowed": stream_hold_harness.hold_dependency_narrowed,
            "hold_verdict": stream_hold_harness.hold_verdict,
            "hold_status": stream_hold_harness.hold_status,
            "gate_release_boundary": stream_hold_harness.gate_release_boundary,
            "second_stream_started_before_first_consumer_completed": (
                stream_hold_harness.second_stream_started_before_first_consumer_completed
            ),
            "max_concurrent": stream_hold_harness.max_concurrent,
            "queue_policy": stream_hold_harness.queue_policy,
            "gate_total_served": stream_hold_harness.gate_total_served,
            "gate_total_queued": stream_hold_harness.gate_total_queued,
            "preserved_post_claim_invariants": list(
                stream_hold_harness.preserved_post_claim_invariants
            ),
            "first_stream_events": list(stream_hold_harness.first_stream_events),
            "second_stream_events": list(stream_hold_harness.second_stream_events),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_visible
            ),
            "earlier_runtime_owned_boundary_earlier_earlier_boundary_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.earlier_runtime_owned_boundary_earlier_earlier_boundary_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.second_stream_events
            ),
        }
        payload["backend_terminal_event_harness"] = {
            "backend_terminal_event_boundary_visible": (
                backend_terminal_event_harness.backend_terminal_event_boundary_visible
            ),
            "terminal_event_status": backend_terminal_event_harness.terminal_event_status,
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_event_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_started_before_first_terminal_event_consumed": (
                backend_terminal_event_harness.second_stream_started_before_first_terminal_event_consumed
            ),
            "second_stream_started_before_first_iterator_completed": (
                backend_terminal_event_harness.second_stream_started_before_first_iterator_completed
            ),
            "terminal_window_ms": backend_terminal_event_harness.terminal_window_ms,
            "first_stream_events": list(
                backend_terminal_event_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_event_harness.second_stream_events
            ),
        }
        payload["backend_terminal_payload_commit_harness"] = {
            "backend_terminal_payload_commit_boundary_visible": (
                backend_terminal_payload_commit_harness.backend_terminal_payload_commit_boundary_visible
            ),
            "payload_commit_status": (
                backend_terminal_payload_commit_harness.payload_commit_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_payload_commit_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_started_before_first_terminal_payload_committed": (
                backend_terminal_payload_commit_harness.second_stream_started_before_first_terminal_payload_committed
            ),
            "second_stream_started_before_first_terminal_event_consumed": (
                backend_terminal_payload_commit_harness.second_stream_started_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": backend_terminal_payload_commit_harness.terminal_window_ms,
            "first_stream_events": list(
                backend_terminal_payload_commit_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_payload_commit_harness.second_stream_events
            ),
        }
        payload["backend_terminal_payload_capture_harness"] = {
            "backend_terminal_payload_capture_boundary_visible": (
                backend_terminal_payload_capture_harness.backend_terminal_payload_capture_boundary_visible
            ),
            "payload_capture_status": (
                backend_terminal_payload_capture_harness.payload_capture_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_payload_capture_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_started_before_first_terminal_payload_captured": (
                backend_terminal_payload_capture_harness.second_stream_started_before_first_terminal_payload_captured
            ),
            "second_stream_started_before_first_terminal_event_consumed": (
                backend_terminal_payload_capture_harness.second_stream_started_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_payload_capture_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_payload_capture_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_payload_capture_harness.second_stream_events
            ),
        }
        payload["backend_terminal_record_capture_harness"] = {
            "backend_terminal_record_capture_boundary_visible": (
                backend_terminal_record_capture_harness.backend_terminal_record_capture_boundary_visible
            ),
            "record_capture_status": (
                backend_terminal_record_capture_harness.record_capture_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_record_capture_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_record_captured": (
                backend_terminal_record_capture_harness.second_stream_request_written_before_first_terminal_record_captured
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_record_capture_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_record_capture_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_record_capture_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_record_capture_harness.second_stream_events
            ),
        }
        payload["backend_terminal_record_prefix_harness"] = {
            "backend_terminal_record_prefix_boundary_visible": (
                backend_terminal_record_prefix_harness.backend_terminal_record_prefix_boundary_visible
            ),
            "prefix_status": backend_terminal_record_prefix_harness.prefix_status,
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_record_prefix_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_record_prefix_detected": (
                backend_terminal_record_prefix_harness.second_stream_request_written_before_first_terminal_record_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_record_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": backend_terminal_record_prefix_harness.terminal_window_ms,
            "first_stream_events": list(
                backend_terminal_record_prefix_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_record_prefix_harness.second_stream_events
            ),
        }
        payload["backend_terminal_action_discriminant_harness"] = {
            "backend_terminal_action_discriminant_boundary_visible": (
                backend_terminal_action_discriminant_harness.backend_terminal_action_discriminant_boundary_visible
            ),
            "action_discriminant_status": (
                backend_terminal_action_discriminant_harness.action_discriminant_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_action_discriminant_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_action_discriminant_detected": (
                backend_terminal_action_discriminant_harness.second_stream_request_written_before_first_terminal_action_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_action_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": backend_terminal_action_discriminant_harness.terminal_window_ms,
            "first_stream_events": list(
                backend_terminal_action_discriminant_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_action_discriminant_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_capture_harness"] = {
            "backend_terminal_notice_capture_boundary_visible": (
                backend_terminal_notice_capture_harness.backend_terminal_notice_capture_boundary_visible
            ),
            "notice_capture_status": (
                backend_terminal_notice_capture_harness.notice_capture_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_capture_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_notice_captured": (
                backend_terminal_notice_capture_harness.second_stream_request_written_before_first_terminal_notice_captured
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_capture_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_capture_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_capture_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_capture_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_prefix_harness"] = {
            "backend_terminal_notice_prefix_boundary_visible": (
                backend_terminal_notice_prefix_harness.backend_terminal_notice_prefix_boundary_visible
            ),
            "notice_prefix_status": (
                backend_terminal_notice_prefix_harness.notice_prefix_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_prefix_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_notice_prefix_detected": (
                backend_terminal_notice_prefix_harness.second_stream_request_written_before_first_terminal_notice_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_prefix_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_prefix_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_prefix_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_action_discriminant_harness"] = {
            "backend_terminal_notice_action_discriminant_boundary_visible": (
                backend_terminal_notice_action_discriminant_harness.backend_terminal_notice_action_discriminant_boundary_visible
            ),
            "notice_action_discriminant_status": (
                backend_terminal_notice_action_discriminant_harness.notice_action_discriminant_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_action_discriminant_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_notice_action_discriminant_detected": (
                backend_terminal_notice_action_discriminant_harness.second_stream_request_written_before_first_terminal_notice_action_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_action_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_action_discriminant_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_action_discriminant_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_action_discriminant_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_action_stem_harness"] = {
            "backend_terminal_notice_action_stem_boundary_visible": (
                backend_terminal_notice_action_stem_harness.backend_terminal_notice_action_stem_boundary_visible
            ),
            "notice_action_stem_status": (
                backend_terminal_notice_action_stem_harness.notice_action_stem_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_action_stem_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_notice_action_stem_detected": (
                backend_terminal_notice_action_stem_harness.second_stream_request_written_before_first_terminal_notice_action_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_action_stem_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_action_stem_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_action_stem_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_action_stem_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_marker_harness"] = {
            "backend_terminal_notice_marker_boundary_visible": (
                backend_terminal_notice_marker_harness.backend_terminal_notice_marker_boundary_visible
            ),
            "notice_marker_status": (
                backend_terminal_notice_marker_harness.notice_marker_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_marker_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_notice_marker_detected": (
                backend_terminal_notice_marker_harness.second_stream_request_written_before_first_terminal_notice_marker_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_marker_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_marker_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_marker_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_marker_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_marker_prefix_harness"] = {
            "backend_terminal_notice_marker_prefix_boundary_visible": (
                backend_terminal_notice_marker_prefix_harness.backend_terminal_notice_marker_prefix_boundary_visible
            ),
            "notice_marker_prefix_status": (
                backend_terminal_notice_marker_prefix_harness.notice_marker_prefix_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_marker_prefix_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_notice_marker_prefix_detected": (
                backend_terminal_notice_marker_prefix_harness.second_stream_request_written_before_first_terminal_notice_marker_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_marker_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_marker_prefix_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_marker_prefix_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_marker_prefix_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_marker_stem_harness"] = {
            "backend_terminal_notice_marker_stem_boundary_visible": (
                backend_terminal_notice_marker_stem_harness.backend_terminal_notice_marker_stem_boundary_visible
            ),
            "notice_marker_stem_status": (
                backend_terminal_notice_marker_stem_harness.notice_marker_stem_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_marker_stem_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_notice_marker_stem_detected": (
                backend_terminal_notice_marker_stem_harness.second_stream_request_written_before_first_terminal_notice_marker_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_marker_stem_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_marker_stem_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_marker_stem_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_marker_stem_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_marker_discriminant_harness"] = {
            "backend_terminal_notice_marker_discriminant_boundary_visible": (
                backend_terminal_notice_marker_discriminant_harness.backend_terminal_notice_marker_discriminant_boundary_visible
            ),
            "notice_marker_discriminant_status": (
                backend_terminal_notice_marker_discriminant_harness.notice_marker_discriminant_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_marker_discriminant_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_before_first_terminal_notice_marker_discriminant_detected": (
                backend_terminal_notice_marker_discriminant_harness.second_stream_request_written_before_first_terminal_notice_marker_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_marker_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_marker_discriminant_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_marker_discriminant_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_marker_discriminant_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_marker_key_lead_harness"] = {
            "backend_terminal_notice_marker_key_lead_boundary_visible": (
                backend_terminal_notice_marker_key_lead_harness.backend_terminal_notice_marker_key_lead_boundary_visible
            ),
            "notice_marker_key_lead_status": (
                backend_terminal_notice_marker_key_lead_harness.notice_marker_key_lead_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_marker_key_lead_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_marker_key_lead_detected": (
                backend_terminal_notice_marker_key_lead_harness.second_stream_request_written_after_first_terminal_notice_marker_key_lead_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_marker_key_lead_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_marker_key_lead_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_marker_key_lead_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_marker_key_lead_harness.second_stream_events
            ),
        }
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
        payload["backend_terminal_notice_leading_discriminator_prefix_harness"] = {
            "backend_terminal_notice_leading_discriminator_prefix_boundary_visible": (
                backend_terminal_notice_leading_discriminator_prefix_harness.backend_terminal_notice_leading_discriminator_prefix_boundary_visible
            ),
            "leading_discriminator_prefix_status": (
                backend_terminal_notice_leading_discriminator_prefix_harness.leading_discriminator_prefix_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_prefix_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_prefix_detected": (
                backend_terminal_notice_leading_discriminator_prefix_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_detected": (
                backend_terminal_notice_leading_discriminator_prefix_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_prefix_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_prefix_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_prefix_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_leading_discriminator_stem_harness"] = {
            "backend_terminal_notice_leading_discriminator_stem_boundary_visible": (
                backend_terminal_notice_leading_discriminator_stem_harness.backend_terminal_notice_leading_discriminator_stem_boundary_visible
            ),
            "leading_discriminator_stem_status": (
                backend_terminal_notice_leading_discriminator_stem_harness.leading_discriminator_stem_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_stem_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_stem_detected": (
                backend_terminal_notice_leading_discriminator_stem_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_prefix_detected": (
                backend_terminal_notice_leading_discriminator_stem_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_stem_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_stem_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_stem_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_stem_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_leading_discriminator_discriminant_harness"] = {
            "backend_terminal_notice_leading_discriminator_discriminant_boundary_visible": (
                backend_terminal_notice_leading_discriminator_discriminant_harness.backend_terminal_notice_leading_discriminator_discriminant_boundary_visible
            ),
            "leading_discriminator_discriminant_status": (
                backend_terminal_notice_leading_discriminator_discriminant_harness.leading_discriminator_discriminant_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_discriminant_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_discriminant_detected": (
                backend_terminal_notice_leading_discriminator_discriminant_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_stem_detected": (
                backend_terminal_notice_leading_discriminator_discriminant_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_discriminant_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_discriminant_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_discriminant_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_leading_discriminator_marker_harness"] = {
            "backend_terminal_notice_leading_discriminator_marker_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_harness.backend_terminal_notice_leading_discriminator_marker_boundary_visible
            ),
            "leading_discriminator_marker_status": (
                backend_terminal_notice_leading_discriminator_marker_harness.leading_discriminator_marker_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_detected": (
                backend_terminal_notice_leading_discriminator_marker_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_discriminant_detected": (
                backend_terminal_notice_leading_discriminator_marker_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_leading_discriminator_marker_prefix_harness"] = {
            "backend_terminal_notice_leading_discriminator_marker_prefix_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_prefix_harness.backend_terminal_notice_leading_discriminator_marker_prefix_boundary_visible
            ),
            "leading_discriminator_marker_prefix_status": (
                backend_terminal_notice_leading_discriminator_marker_prefix_harness.leading_discriminator_marker_prefix_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_prefix_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_prefix_detected": (
                backend_terminal_notice_leading_discriminator_marker_prefix_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_detected": (
                backend_terminal_notice_leading_discriminator_marker_prefix_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_prefix_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_prefix_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_prefix_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_leading_discriminator_marker_discriminant_harness"] = {
            "backend_terminal_notice_leading_discriminator_marker_discriminant_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_discriminant_harness.backend_terminal_notice_leading_discriminator_marker_discriminant_boundary_visible
            ),
            "leading_discriminator_marker_discriminant_status": (
                backend_terminal_notice_leading_discriminator_marker_discriminant_harness.leading_discriminator_marker_discriminant_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_discriminant_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_discriminant_detected": (
                backend_terminal_notice_leading_discriminator_marker_discriminant_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_stem_detected": (
                backend_terminal_notice_leading_discriminator_marker_discriminant_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_discriminant_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_discriminant_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_discriminant_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness.backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_visible
            ),
            "leading_discriminator_marker_first_unique_boundary_status": (
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness.leading_discriminator_marker_first_unique_boundary_status
            ),
            "shared_non_unique_prefix": (
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness.shared_non_unique_prefix
            ),
            "first_unique_boundary_prefix": (
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness.first_unique_boundary_prefix
            ),
            "earlier_prefix_collides_with_old_notice_record": (
                backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness.earlier_prefix_collides_with_old_notice_record
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_boundary_visible
            ),
            "earlier_runtime_owned_discriminator_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.earlier_runtime_owned_discriminator_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_discriminant_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_boundary_visible
            ),
            "earlier_runtime_owned_discriminator_prefix_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness.earlier_runtime_owned_discriminator_prefix_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_boundary_visible
            ),
            "earlier_runtime_owned_discriminator_stem_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness.earlier_runtime_owned_discriminator_stem_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_boundary_visible
            ),
            "earlier_runtime_owned_discriminator_discriminant_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness.earlier_runtime_owned_discriminator_discriminant_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_visible
            ),
            "leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness.leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_status
            ),
            "shared_non_unique_prefix": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness.shared_non_unique_prefix
            ),
            "first_honest_unique_boundary_prefix": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness.first_honest_unique_boundary_prefix
            ),
            "earlier_literal_prefix_is_not_runtime_owned_boundary": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_first_unique_boundary_harness.earlier_literal_prefix_is_not_runtime_owned_boundary
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_boundary_visible
            ),
            "earlier_runtime_owned_leading_discriminator_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness.earlier_runtime_owned_leading_discriminator_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_discriminator_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_boundary_visible
            ),
            "earlier_runtime_owned_leading_discriminator_prefix_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.earlier_runtime_owned_leading_discriminator_prefix_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_boundary_visible
            ),
            "earlier_runtime_owned_leading_discriminator_stem_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness.earlier_runtime_owned_leading_discriminator_stem_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_boundary_visible
            ),
            "earlier_runtime_owned_leading_discriminator_discriminant_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.earlier_runtime_owned_leading_discriminator_discriminant_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_visible
            ),
            "earlier_runtime_owned_boundary_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness.earlier_runtime_owned_boundary_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_leading_discriminator_discriminant_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_boundary_visible
            ),
            "earlier_runtime_owned_boundary_prefix_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness.earlier_runtime_owned_boundary_prefix_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_boundary_visible
            ),
            "earlier_runtime_owned_boundary_stem_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.earlier_runtime_owned_boundary_stem_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.second_stream_events
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_visible
            ),
            "leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness.leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_status
            ),
            "shared_non_unique_prefix": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness.shared_non_unique_prefix
            ),
            "first_honest_unique_boundary_prefix": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness.first_honest_unique_boundary_prefix
            ),
            "earlier_literal_prefix_is_not_runtime_owned_boundary": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_first_unique_boundary_harness.earlier_literal_prefix_is_not_runtime_owned_boundary
            ),
        }
        payload[
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness"
        ] = {
            "backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_visible
            ),
            "earlier_runtime_owned_boundary_earlier_boundary_status": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.earlier_runtime_owned_boundary_earlier_boundary_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_boundary_harness.second_stream_events
            ),
        }
        payload["backend_terminal_notice_leading_discriminator_marker_stem_harness"] = {
            "backend_terminal_notice_leading_discriminator_marker_stem_boundary_visible": (
                backend_terminal_notice_leading_discriminator_marker_stem_harness.backend_terminal_notice_leading_discriminator_marker_stem_boundary_visible
            ),
            "leading_discriminator_marker_stem_status": (
                backend_terminal_notice_leading_discriminator_marker_stem_harness.leading_discriminator_marker_stem_status
            ),
            "second_stream_blocked_before_terminal_window": (
                backend_terminal_notice_leading_discriminator_marker_stem_harness.second_stream_blocked_before_terminal_window
            ),
            "second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_stem_detected": (
                backend_terminal_notice_leading_discriminator_marker_stem_harness.second_stream_request_written_after_first_terminal_notice_leading_discriminator_marker_stem_detected
            ),
            "second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_prefix_detected": (
                backend_terminal_notice_leading_discriminator_marker_stem_harness.second_stream_request_written_before_first_terminal_notice_leading_discriminator_marker_prefix_detected
            ),
            "second_stream_request_written_before_first_terminal_event_consumed": (
                backend_terminal_notice_leading_discriminator_marker_stem_harness.second_stream_request_written_before_first_terminal_event_consumed
            ),
            "terminal_window_ms": (
                backend_terminal_notice_leading_discriminator_marker_stem_harness.terminal_window_ms
            ),
            "first_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_stem_harness.first_stream_events
            ),
            "second_stream_events": list(
                backend_terminal_notice_leading_discriminator_marker_stem_harness.second_stream_events
            ),
        }
    else:
        payload = cache_request_aggregation_active_seam_to_dict(
            build_cache_request_aggregation_active_seam()
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
