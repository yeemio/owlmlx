# owlmlx Phase 45: Cache Repeatability Evidence

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only repeated-serving cache evidence for replacement-grade alignment

## 1. Purpose

This document advances `cache_scheduler_depth` one step past one-shot evidence.

The question it answers is:

**Across repeated serving runs, what level of cache evidence does `owlmlx`
actually own today?**

This matters because replacement-grade cache depth is not established by one
config snapshot or one reuse signal. It requires evidence that survives
repeated serving.

## 2. Owned Contract

`owlmlx/cache_repeatability_evidence.py` now owns:

- `build_cache_repeatability_evidence(...)`
- `cache_repeatability_evidence_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_repeatability_evidence.py`

Contract:

- `surface = "owlmlx.cache_repeatability_evidence"`
- `version = "phase45"`

Stable sections:

- `summary`
- `run_counts`

## 3. Repeatability Semantics

Current `summary.repeatability_status` values:

- `no_repeat_runs`
- `runtime_activity_visible_counter_gap`
- `repeat_profile_active_under_load`
- `repeat_residency_visible`
- `repeat_reuse_visible`
- `repeat_eviction_visible`

Interpretation:

- `no_repeat_runs`
  - no repeated-serving evidence has been observed yet
- `runtime_activity_visible_counter_gap`
  - the active runtime path already shows repeated serving
  - direct runtime-owned reuse/eviction counters are still missing
- `repeat_profile_active_under_load`
  - repeated-serving activity exists under a cache-capable profile
  - repeated residency/reuse evidence is still missing
- `repeat_residency_visible`
  - repeated residency signals exist
  - explicit repeated reuse evidence is still missing
- `repeat_reuse_visible`
  - repeated reuse signals exist
  - broader eviction/scheduler closure still remains open
- `repeat_eviction_visible`
  - repeated-serving eviction evidence exists
  - this is stronger than reuse alone, but still below full cache parity

## 4. Current Honest Result

Current default result from the runtime-owned repeatability surface is:

- `summary.status = "partial"`
- `summary.repeatability_status = "no_repeat_runs"`
- `summary.blocked_reason = "runtime-owned repeated-serving cache evidence is still below replacement-grade closure"`

This is still the honest default because `owlmlx` does not yet own:

- direct runtime-owned reuse or eviction counters from the active runtime path
- stronger eviction-policy evidence tied to the actual runtime path

What it owns now is the contract that can express those rungs once the
evidence exists.

## 5. What This Changes

Before this round, `owlmlx` could express:

- cache profile truth
- cache/scheduler depth status
- one-shot residency/reuse evidence

But it still lacked a runtime-owned way to answer:

- whether evidence survives repeated serving
- whether that repeated evidence is only profile activity, residency, reuse, or
  eviction

Now `owlmlx` owns that answer directly.

The active runtime observation harness now proves one stronger live rung:

- active persistent-child runtime activity plus one runtime-owned `reuse_counter`
  now promote the live surface to `repeat_reuse_visible`
- this distinguishes "runtime path visible but counters absent" from "one real
  runtime-owned reuse counter is already visible on the active path"

## 6. What This Does Not Claim

It does not claim:

- cache parity with `oMLX` / `vMLX`
- eviction-policy closure
- continuous batching or deeper scheduler parity
- customer-grade runtime cache stability

It only claims:

- repeated-serving cache evidence now has a runtime-owned contract
- active runtime-path repeated serving plus one runtime-owned `reuse_counter`
  can now promote the live surface to `repeat_reuse_visible`
- the current closure level remains partial
- the next honest step is wiring real runtime counters or repeated serving
  observations into a stronger cache closure rung
