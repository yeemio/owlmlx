#!/usr/bin/env python3
"""Emit the runtime-owned customer runtime evidence ledger for owlmlx."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from owlmlx import (
    FakeBackend,
    RuntimeKernel,
    build_cache_batching_mechanism_subgap,
    build_cache_child_exchange_aggregated_dispatch_exactness,
    build_cache_counter_gap,
    build_cache_counter_feasibility,
    build_cache_cohort_to_child_exchange_handoff_exactness,
    build_cache_continuous_batching_feasibility,
    build_cache_pre_claim_staging_seam_exactness,
    build_cache_pre_gate_admission_window_seam,
    build_cache_request_aggregation_active_seam,
    build_cache_request_aggregation_window_exactness,
    build_cache_scheduler_branch_selection,
    build_cache_scheduler_floor_gap,
    build_cache_scheduler_implementation_backlog,
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
    build_cache_scheduler_turboquant_split,
    build_cache_closure_rung,
    build_cache_structural_ingress_seam,
    build_cache_stream_hold_dependency_exactness,
    build_customer_runtime_evidence,
    build_heavy_weight_runtime_repeatability_status,
    build_multi_model_governance_controls,
    build_multi_model_governance_policy_gap,
    build_multi_model_governance_status,
    build_multi_model_governance_transition_ledger,
    customer_runtime_evidence_to_dict,
)
from owlmlx.cache_child_exchange_aggregated_dispatch_harness import (
    run_cache_child_exchange_aggregated_dispatch_harness,
)
from owlmlx.cache_cohort_to_child_exchange_handoff_harness import (
    run_cache_cohort_to_child_exchange_handoff_harness,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)
from owlmlx.cache_request_aggregation_window_reentry import (
    CacheRequestAggregationWindowReentry,
)
from owlmlx.cache_pre_gate_admission_hook_harness import (
    run_pre_gate_admission_hook_harness,
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
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_first_unique_boundary_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_harness import (
    run_cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_harness,
)
from owlmlx.cache_stream_backend_terminal_notice_marker_stem_harness import (
    run_cache_stream_backend_terminal_notice_marker_stem_harness,
)
from owlmlx.memory_budget import MachineMemoryProfile


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=16.0,
        system_reserve_gb=2.0,
        serving_budget_gb=14.0,
        warning_threshold_gb=12.0,
    )


def _run_governance_harness() -> dict[str, object]:
    state = {"now": 100.0}

    def clock() -> float:
        return float(state["now"])

    kernel = RuntimeKernel(
        FakeBackend(default_memory_gb=1.0),
        profile=_profile(),
        clock=clock,
    )
    kernel.load_model("model-a")
    kernel.load_model("model-b")
    kernel.load_model("model-c")
    kernel.pin_model("model-a")
    kernel.set_model_ttl("model-a", 30.0)
    kernel.set_model_ttl("model-b", 30.0)

    import asyncio

    asyncio.run(kernel.generate("hello-explicit", model_id="model-a"))
    kernel.unload_model("model-c")
    state["now"] = 140.0
    kernel.sweep_expired_models()
    kernel.restart_model("model-a")
    runtime_status = kernel.status_dict()
    return {
        "status": build_multi_model_governance_status(runtime_status),
        "controls": build_multi_model_governance_controls(runtime_status),
        "transition_ledger": build_multi_model_governance_transition_ledger(runtime_status),
        "policy_gap": build_multi_model_governance_policy_gap(
            controls=build_multi_model_governance_controls(runtime_status),
            transition_ledger=build_multi_model_governance_transition_ledger(
                runtime_status
            ),
        ),
        "observations": runtime_status.get("governance_observations"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--specimen-path", required=True)
    parser.add_argument("--include-known-venvs", action="store_true")
    parser.add_argument("--heavy-boundary-memory-gb", type=float)
    parser.add_argument("--heavy-boundary-entered", action="store_true")
    parser.add_argument("--heavy-boundary-entry-reason")
    parser.add_argument("--supported-host-proof-visible", action="store_true")
    parser.add_argument("--supported-host-repeat-runs", type=int, default=0)
    parser.add_argument("--timeout-s", type=float, default=20.0)
    parser.add_argument("--quarantine-path", type=Path)
    parser.add_argument("--crash-report-directory", type=Path)
    parser.add_argument("--crash-limit", type=int, default=5)
    parser.add_argument("--skip-governance-harness", action="store_true")
    args = parser.parse_args()

    governance_bundle = None
    cache_bundle = None
    if not args.skip_governance_harness:
        governance_bundle = _run_governance_harness()
    cache_bundle = run_cache_runtime_observation_harness()
    structural_ingress_harness = run_pre_gate_admission_hook_harness()
    child_exchange_harness = run_cache_child_exchange_aggregated_dispatch_harness()
    handoff_harness = run_cache_cohort_to_child_exchange_handoff_harness()
    stream_hold_harness = run_cache_stream_hold_dependency_harness()
    backend_terminal_event_harness = run_cache_stream_backend_terminal_event_harness()
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
    backend_terminal_notice_leading_discriminator_marker_stem_harness = (
        run_cache_stream_backend_terminal_notice_leading_discriminator_marker_stem_harness()
    )
    backend_terminal_notice_marker_stem_harness = (
        run_cache_stream_backend_terminal_notice_marker_stem_harness()
    )
    cache_counter_gap = build_cache_counter_gap(
        closure=cache_bundle.closure,
        backend_observations=cache_bundle.backend_observations,
    )
    cache_counter_feasibility = build_cache_counter_feasibility(
        counter_gap=cache_counter_gap
    )
    cache_scheduler_turboquant_split = build_cache_scheduler_turboquant_split(
        counter_feasibility=cache_counter_feasibility,
        scheduler=cache_bundle.closure.scheduler,
        turboquant=cache_bundle.turboquant,
    )
    cache_scheduler_floor_gap = build_cache_scheduler_floor_gap(
        split=cache_scheduler_turboquant_split
    )
    cache_scheduler_backlog = build_cache_scheduler_implementation_backlog(
        floor_gap=cache_scheduler_floor_gap
    )
    cache_scheduler_branch_selection = build_cache_scheduler_branch_selection(
        scheduler_backlog=cache_scheduler_backlog
    )
    cache_batching_feasibility = build_cache_continuous_batching_feasibility(
        branch_selection=cache_scheduler_branch_selection
    )
    cache_batching_subgap = build_cache_batching_mechanism_subgap(
        feasibility=cache_batching_feasibility
    )
    request_aggregation_window_exactness = build_cache_request_aggregation_window_exactness(
        mechanism_subgap=cache_batching_subgap,
        hook_harness=structural_ingress_harness,
        child_exchange_harness=child_exchange_harness,
        handoff_harness=handoff_harness,
    )
    child_exchange_exactness = build_cache_child_exchange_aggregated_dispatch_exactness(
        request_aggregation_window_exactness=request_aggregation_window_exactness,
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
    request_aggregation_reentry = CacheRequestAggregationWindowReentry(
        continuous_batching_branch_reduction=object(),
        request_aggregation_window_exactness=request_aggregation_window_exactness,
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
    request_aggregation_active_seam = build_cache_request_aggregation_active_seam(
        request_aggregation_window_reentry=request_aggregation_reentry,
        request_aggregation_window_exactness=request_aggregation_window_exactness,
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
        stream_backend_terminal_notice_leading_discriminator_marker_stem_exactness=(
            backend_terminal_notice_leading_discriminator_marker_stem_exactness
        ),
    )
    heavy_weight_status = build_heavy_weight_runtime_repeatability_status(
        specimen_path=args.specimen_path,
        include_known_candidates=args.include_known_venvs,
        timeout_s=args.timeout_s,
        quarantine_path=args.quarantine_path,
        crash_report_directory=args.crash_report_directory,
        crash_limit=args.crash_limit,
        boundary_required_memory_gb=args.heavy_boundary_memory_gb,
        boundary_entry_visible=args.heavy_boundary_entered,
        boundary_entry_reason=args.heavy_boundary_entry_reason,
        supported_host_proof_visible=args.supported_host_proof_visible,
        supported_host_repeat_runs=args.supported_host_repeat_runs,
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path=args.specimen_path,
            heavy_weight_repeatability=heavy_weight_status,
            cache_closure=build_cache_closure_rung(
                repeatability=cache_bundle.repeatability,
                turboquant=cache_bundle.turboquant,
            ),
            cache_counter_gap=cache_counter_gap,
            cache_counter_feasibility=cache_counter_feasibility,
            cache_scheduler_turboquant_split=cache_scheduler_turboquant_split,
            cache_request_aggregation_active_seam=request_aggregation_active_seam,
            cache_pre_gate_admission_hook_harness=structural_ingress_harness,
            cache_child_exchange_aggregated_dispatch_harness=child_exchange_harness,
            cache_cohort_to_child_exchange_handoff_harness=handoff_harness,
            cache_structural_ingress_seam=build_cache_structural_ingress_seam(
                pre_gate_admission_window_seam=build_cache_pre_gate_admission_window_seam(),
                pre_claim_staging_seam_exactness=build_cache_pre_claim_staging_seam_exactness(),
                hook_harness=structural_ingress_harness,
            ),
            multi_model_governance=(
                governance_bundle["status"] if governance_bundle is not None else None
            ),
            multi_model_governance_controls=(
                governance_bundle["controls"] if governance_bundle is not None else None
            ),
            multi_model_governance_transition_ledger=(
                governance_bundle["transition_ledger"]
                if governance_bundle is not None
                else None
            ),
            multi_model_governance_policy_gap=(
                governance_bundle["policy_gap"] if governance_bundle is not None else None
            ),
            include_known_candidates=args.include_known_venvs,
            timeout_s=args.timeout_s,
            quarantine_path=args.quarantine_path,
            crash_report_directory=args.crash_report_directory,
            crash_limit=args.crash_limit,
        )
    )
    payload["cache_harness"] = cache_bundle.backend_observations
    payload["structural_ingress_harness"] = {
        "runtime_owned_hook_present": structural_ingress_harness.runtime_owned_hook_present,
        "hook_boundary": structural_ingress_harness.hook_boundary,
        "hook_mode": structural_ingress_harness.hook_mode,
        "observed_midflight_staged_count": structural_ingress_harness.observed_midflight_staged_count,
        "observed_total_staged": structural_ingress_harness.observed_total_staged,
        "observed_total_claimed": structural_ingress_harness.observed_total_claimed,
        "observed_total_discarded": structural_ingress_harness.observed_total_discarded,
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
        "child_exchange_mode": handoff_harness.child_exchange_mode,
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
        "terminal_window_ms": backend_terminal_payload_capture_harness.terminal_window_ms,
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
        "terminal_window_ms": backend_terminal_record_capture_harness.terminal_window_ms,
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
    if governance_bundle is not None:
        payload["governance_harness"] = governance_bundle["observations"]
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
