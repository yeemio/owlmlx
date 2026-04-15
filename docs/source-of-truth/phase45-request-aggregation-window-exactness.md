# owlmlx Phase 45: Request Aggregation Window Exactness

> Status: authoritative
> Updated: 2026-04-15
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

The ingress blocker is now narrowed to:

- `ingress_window_status = missing_pre_gate_admission_window`
- `admission_boundary_status = generation_gate_claims_session_before_cohort_formation`

The remaining dependencies are explicit:

- `child_dependency_status = single_request_per_child_exchange_blocks_aggregated_dispatch`
- `stream_dependency_status = stream_session_holds_gate_until_completion`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- `request_aggregation_window` is the first exact missing mechanism

Now `owlmlx` can say more precisely:

- the missing part is not generic ingress logic
- the missing part is a pre-gate cohorting window before whole-request session
  claim
- even if that existed, aggregated child dispatch and stream release are still
  downstream dependencies

## 5. What This Does Not Claim

It does not claim:

- a request-aggregation window already exists
- child exchange already supports aggregated dispatch
- streaming already supports interleaved cohort progress

It only freezes the blocker at a more exact ingress/dependency boundary.

## 6. Next Closure Step

The next exact local round should decide whether pre-gate cohort formation can
become a runtime-owned mechanism on the active path without violating the
validated serial safety boundary.
