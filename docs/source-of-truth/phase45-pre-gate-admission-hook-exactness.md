# owlmlx Phase 45: Pre-Gate Admission Hook Exactness

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only cache scheduler ingress exactness on the active path

## 1. Purpose

Freeze the next exact ingress blocker after pre-gate cohort-window feasibility
is already boundary-exact.

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

The current exact result is:

- `exactness_rung = admission_hook_blocker_exact`

The active path truth is now:

- `admission_hook_status = no_bounded_hook_before_gate_claim`
- `owned_boundary_status = whole_request_gate_claim_is_first_runtime_owned_boundary`
- preserved safety invariants:
  - `max_concurrent_1_after_gate_claim`
  - `ticketed_fifo_after_gate_claim`
  - `serial_safety_validated_only_after_gate_claim`

## 4. What This Changes

Before this round, `owlmlx` could say:

- no pre-gate cohort window is locally expressible
- the serial safety boundary begins only after gate claim

Now it can say something stronger:

- the next exact ingress blocker is the absence of any bounded runtime-owned
  admission hook before whole-request gate claim
- this is not merely a missing queue or buffer name
- any future hook must preserve the validated post-claim safety invariants,
  rather than redefining them

## 5. What This Does Not Claim

It does not claim:

- a bounded hook already exists
- a hook is trivial to add
- child dispatch or stream interleaving should be worked next

It only freezes the next ingress blocker more precisely.

## 6. Next Closure Step

The next exact local round should decide whether a bounded pre-gate admission
hook can be introduced without violating:

- `max_concurrent = 1`
- ticketed FIFO discipline after gate claim
- the validated serial safety boundary beginning only after whole-request gate
  claim
