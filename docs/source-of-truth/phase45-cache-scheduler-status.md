# owlmlx Phase 45: Cache/Scheduler Status

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only cache/scheduler depth truth for replacement-grade alignment

## 1. Purpose

This document turns `cache_scheduler_depth` from a narrative replacement gap
into a runtime-owned status contract.

The question it answers is:

**What cache/scheduler depth does `owlmlx` actually own today, and why is that
still below `oMLX` / `vMLX` replacement-grade closure?**

This is narrower than full parity. It exists so the runtime can answer the gap
honestly without relying on shell-level control-plane narration.

## 2. Owned Contract

`owlmlx/cache_scheduler_status.py` now owns:

- `build_cache_scheduler_status(...)`
- `cache_scheduler_status_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_scheduler_status.py`

Contract:

- `surface = "owlmlx.cache_scheduler_status"`
- `version = "phase45"`

Stable sections:

- `summary`
- `scheduler`
- `cache_profile`
- `turboquant_cache_safety`

## 3. Status Semantics

Current `summary.status` value:

- `partial`

Current `summary.scheduler_depth` values:

- `serial_single_worker`

Current `summary.cache_depth` values:

- `truth_only`
- `profile_visible`

Interpretation:

- `serial_single_worker`
  - `owlmlx` owns the generation gate and honest serialized scheduler truth
  - it does not yet prove deeper scheduler depth such as continuous batching
- `truth_only`
  - `owlmlx` can expose cache truth, but runtime-owned cache profile evidence
    is not yet present in the current status input
- `profile_visible`
  - `owlmlx` can combine configured/runtime cache profile truth with scheduler
    truth in one runtime-owned surface
  - this is still below replacement-grade cache closure

## 4. Current Verified Result

Current verified result from the runtime-owned status contract is:

- `summary.status = "partial"`
- `summary.scheduler_depth = "serial_single_worker"`
- `summary.cache_depth = "truth_only"` when no runtime cache profile is
  supplied
- `summary.blocked_reason = "runtime-owned cache reuse, eviction, and deeper scheduler behavior remain below reference-grade closure"`
- `summary.recommended_next_step = "add runtime-owned cache residency/reuse evidence before claiming deeper cache/scheduler parity"`

What is already owned:

- queue-based serialized generation discipline
- cache profile truth
- TurboQuant cache-safety truth

What is still missing:

- runtime-owned cache residency/reuse evidence
- deeper scheduler behavior closer to reference-grade serving
- cache eviction/reuse proof that goes beyond profile visibility

## 5. What This Changes

Before this round, `owlmlx` could describe:

- cache truth
- scheduler truth

But it still lacked one runtime-owned answer to:

- how deep the combined cache/scheduler story actually is today
- what exact blocked reason still prevents stronger parity claims

Now `owlmlx` owns that answer directly.

## 6. What This Does Not Claim

It does not claim:

- paged cache closure
- disk-tier cache closure
- continuous batching
- parity with `oMLX` / `vMLX`
- customer-grade runtime stability

It only claims:

- `cache_scheduler_depth` now has a runtime-owned status contract
- the current closure level is still partial
- the next honest runtime-owned step after this status surface is stronger
  repeated-serving reuse/eviction evidence on top of the live
  `owlmlx.cache_manager` counter surface
