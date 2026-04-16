#!/usr/bin/env python3
"""Emit the runtime-owned customer runtime evidence ledger for owlmlx."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from owlmlx import (
    FakeBackend,
    RuntimeKernel,
    build_cache_counter_gap,
    build_cache_counter_feasibility,
    build_cache_pre_claim_staging_seam_exactness,
    build_cache_pre_gate_admission_window_seam,
    build_cache_scheduler_turboquant_split,
    build_cache_closure_rung,
    build_cache_structural_ingress_seam,
    build_customer_runtime_evidence,
    build_multi_model_governance_controls,
    build_multi_model_governance_policy_gap,
    build_multi_model_governance_status,
    build_multi_model_governance_transition_ledger,
    customer_runtime_evidence_to_dict,
)
from owlmlx.cache_runtime_observation_harness import (
    run_cache_runtime_observation_harness,
)
from owlmlx.cache_pre_gate_admission_hook_harness import (
    run_pre_gate_admission_hook_harness,
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
    kernel = RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=_profile())
    kernel.load_model("model-a")
    kernel.load_model("model-b")

    import asyncio

    asyncio.run(kernel.generate("hello-explicit", model_id="model-a"))
    kernel.unload_model("model-b")
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
    cache_counter_gap = build_cache_counter_gap(
        closure=cache_bundle.closure,
        backend_observations=cache_bundle.backend_observations,
    )
    cache_counter_feasibility = build_cache_counter_feasibility(
        counter_gap=cache_counter_gap
    )

    payload = customer_runtime_evidence_to_dict(
        build_customer_runtime_evidence(
            specimen_path=args.specimen_path,
            cache_closure=build_cache_closure_rung(
                repeatability=cache_bundle.repeatability,
                turboquant=cache_bundle.turboquant,
            ),
            cache_counter_gap=cache_counter_gap,
            cache_counter_feasibility=cache_counter_feasibility,
            cache_scheduler_turboquant_split=build_cache_scheduler_turboquant_split(
                counter_feasibility=cache_counter_feasibility,
                scheduler=cache_bundle.closure.scheduler,
                turboquant=cache_bundle.turboquant,
            ),
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
    if governance_bundle is not None:
        payload["governance_harness"] = governance_bundle["observations"]
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
