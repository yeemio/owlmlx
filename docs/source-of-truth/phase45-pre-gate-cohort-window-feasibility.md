# owlmlx Phase 45: Pre-Gate Cohort Window Feasibility

> Status: authoritative
> Updated: 2026-04-16
> Scope: runtime-only scheduler ingress exactness on the active path

## 1. Purpose

Freeze whether a pre-gate cohort window is locally expressible as a runtime-owned
mechanism on the current cache/scheduler path.

## 2. Owned Contract

`owlmlx/cache_pre_gate_cohort_window_feasibility.py` now owns:

- `build_cache_pre_gate_cohort_window_feasibility(...)`
- `cache_pre_gate_cohort_window_feasibility_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_pre_gate_cohort_window_feasibility.py`

Contract:

- `surface = "owlmlx.cache_pre_gate_cohort_window_feasibility"`
- `version = "phase45"`

Stable sections:

- `summary`
- `cohort_window`
- `safety_boundary`

## 3. Current Honest Result

The current exact result is:

- `feasibility_rung = cohort_window_boundary_exact`

The active path truth is now:

- `cohort_window_status = runtime_owned_bounded_cohort_window_present_before_gate_entry`
- `gate_boundary_status = bounded_pre_admission_window_precedes_gate_claim`
- `serial_safety_constraint = serial_safety_validated_only_after_whole_request_gate_claim`

## 4. What This Changes

Before this round, `owlmlx` could say:

- request aggregation is missing
- no pre-gate admission window exists

Now it can say something stronger:

- the current runtime path now exposes a bounded runtime-owned cohort window
  before `GenerationGate` claims the whole request
- the validated serial safety boundary still remains defined after that claim
- so the active blocker is no longer local expressibility; it has moved to the
  downstream request-aggregation dependencies

## 5. What This Does Not Claim

It does not claim:

- aggregated child dispatch exists
- stream release exists
- the active serial serving discipline is wrong

It only freezes that the cohort window is now locally expressible and
runtime-owned while downstream dependencies remain open.

## 6. Next Closure Step

The next exact local round is no longer admission-hook creation.

The next coordinator choice is whether to work the downstream child-exchange
dependency while preserving:

- `max_concurrent = 1`
- ticketed FIFO discipline after gate claim
- the validated serial safety boundary for the active path
