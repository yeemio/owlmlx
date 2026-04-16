# owlmlx Phase 45: Admission Hook Safety Contract

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only cache scheduler ingress safety on the active path

## 1. Purpose

Freeze the exact safety contract any future bounded pre-gate admission hook
must preserve on the current path.

## 2. Owned Contract

`owlmlx/cache_admission_hook_safety_contract.py` now owns:

- `build_cache_admission_hook_safety_contract(...)`
- `cache_admission_hook_safety_contract_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_admission_hook_safety_contract.py`

Contract:

- `surface = "owlmlx.cache_admission_hook_safety_contract"`
- `version = "phase45"`

Stable sections:

- `summary`
- `preserved_post_claim_invariants`
- `forbidden_bypasses`

## 3. Current Honest Result

The current exact result is:

- `contract_rung = safety_contract_exact`

The preserved post-claim invariants are:

- `max_concurrent_1_after_gate_claim`
- `ticketed_fifo_after_gate_claim`
- `serial_safety_validated_only_after_gate_claim`

The forbidden bypasses are:

- `no_bypass_of_whole_request_gate_claim`
- `no_reordering_after_gate_claim`
- `no_post_claim_parallel_generation`

## 4. What This Changes

Before this round, `owlmlx` could say:

- no bounded admission hook exists
- the first runtime-owned boundary is whole-request gate claim

Now it can say something stronger:

- the exact contract any future hook must preserve is frozen
- a future hook is not allowed to bypass whole-request gate claim
- a future hook is not allowed to reorder requests after claim
- a future hook is not allowed to weaken post-claim serial generation

## 5. What This Does Not Claim

It does not claim:

- a safe hook design already exists
- a hook can be added without changing the path
- child dispatch or stream release are next

It only freezes the next exact safety contract more precisely.

## 6. Next Closure Step

The next exact local round should decide whether `owlmlx` can define a bounded
pre-claim admission contract that stays entirely outside whole-request gate
claim while preserving all frozen post-claim invariants.
