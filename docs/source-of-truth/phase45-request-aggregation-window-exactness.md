# owlmlx Phase 45: Request Aggregation Window Exactness

> Status: authoritative
> Updated: 2026-04-16
> Scope: runtime-only scheduler ingress exactness on the active path

## 1. Purpose

Freeze the exact blocker underneath `request_aggregation_window` once that
mechanism is already selected as the next local scheduler subgap.

## 2. Owned Contract

`owlmlx/cache_request_aggregation_window_exactness.py` now owns:

- `build_cache_request_aggregation_window_exactness(...)`
- `cache_request_aggregation_window_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_request_aggregation_window_exactness.py`

Contract:

- `surface = "owlmlx.cache_request_aggregation_window_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `ingress`
- `dependencies`

## 3. Current Honest Result

The current exact result is:

- `exactness_rung = aggregation_window_blocker_exact`

The ingress truth is now:

- `ingress_window_status = bounded_pre_gate_admission_window_present`
- `admission_boundary_status = cohort_forms_before_generation_gate_claim`

The remaining dependencies are explicit:

- `child_dependency_status = cohort_handed_off_to_aggregated_child_exchange_visible`
- `stream_dependency_status = stream_session_holds_gate_until_completion`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- `request_aggregation_window` was still ingress-blocked by a missing pre-gate
  window

Now `owlmlx` can say more precisely:

- a bounded runtime-owned pre-gate admission window now forms cohorts before
  whole-request gate claim
- child exchange itself now supports one non-stream aggregated dispatch step
- the non-stream main serving path now hands that bounded cohort into one
  aggregated child exchange
- ingress is no longer the active blocker underneath `request_aggregation_window`
- the remaining blocker is now stream-session hold on that same path

## 5. What This Does Not Claim

It does not claim:

- streaming already supports interleaved cohort progress
- continuous batching is established

It only freezes the blocker at a more exact post-ingress dependency boundary.

## 6. Next Closure Step

The next exact local round is no longer another ingress-window or
child-exchange-capability round.

The next coordinator choice is whether to reduce the remaining downstream
dependency chain starting from:

- `stream_session_holds_gate_until_completion`
