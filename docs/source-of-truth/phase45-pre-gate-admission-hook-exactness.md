# owlmlx Phase 45: Pre-Gate Admission Hook Exactness

> Status: authoritative
> Updated: 2026-04-16
> Scope: runtime-only cache scheduler ingress exactness on the active path

## 1. Purpose

Freeze the next exact ingress blocker after pre-gate cohort-window feasibility
is already boundary-exact and the bounded structural ingress seam has been
revalidated on the active path.

## 2. Owned Contract

`owlmlx/cache_pre_gate_admission_hook_exactness.py` now owns:

- `build_cache_pre_gate_admission_hook_exactness(...)`
- `cache_pre_gate_admission_hook_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_pre_gate_admission_hook_exactness.py`

Contract:

- `surface = "owlmlx.cache_pre_gate_admission_hook_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `admission_hook`
- `safety_invariants`

## 3. Current Honest Result

The current exact result remains:

- `exactness_rung = admission_hook_blocker_exact`

But the hook truth has now advanced again after the authorized window round:

- `admission_hook_status = bounded_request_aggregation_window_present_before_gate_claim`
- `owned_boundary_status = bounded_cohort_window_precedes_whole_request_gate_claim_without_gate_transfer`
- preserved safety invariants:
  - `max_concurrent_1_after_gate_claim`
  - `ticketed_fifo_after_gate_claim`
  - `serial_safety_validated_only_after_gate_claim`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- no pre-gate cohort window is locally expressible
- the serial safety boundary begins only after gate claim
- the exact ingress blocker was an existing bounded hook that still remained
  inert

Now it can say something stronger and more honest:

- the bounded runtime-owned hook has now widened into a real pre-claim cohort
  window before whole-request gate claim
- that widened hook still does not bypass whole-request gate claim
- the remaining blocker is no longer the hook/window seam itself
- the remaining blockers are now downstream child-exchange and stream-path
  dependencies
- any later widening must still preserve the validated post-claim serial
  invariants

## 5. What This Does Not Claim

It does not claim:

- aggregated child dispatch
- stream interleaving
- continuous batching or parity

It only freezes that the ingress hook has now widened into a bounded
request-aggregation window more precisely.

## 6. Next Closure Step

The next exact local round is no longer about whether a window can be created.

The next coordinator choice is whether the downstream child-exchange
dependency may be reduced without violating:

- `max_concurrent = 1`
- ticketed FIFO discipline after gate claim
- the validated serial safety boundary beginning only after whole-request gate
  claim
