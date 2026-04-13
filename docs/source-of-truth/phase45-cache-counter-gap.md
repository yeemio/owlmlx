# owlmlx Phase 45: Cache Counter Gap

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only exact residual cache counter/scheduler gap

## 1. Purpose

This document freezes the remaining cache blocker after the active runtime
observation harness has already lifted cache closure above the old
`truth_only` baseline.

The question it answers is:

**Has `cache_scheduler_depth` narrowed from an observation gap into an exact
counter-grade gap, and if so, what is still missing?**

## 2. Owned Contract

`owlmlx/cache_counter_gap.py` now owns:

- `build_cache_counter_gap(...)`
- `cache_counter_gap_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_counter_gap.py`

Contract:

- `surface = "owlmlx.cache_counter_gap"`
- `version = "phase45"`

Stable sections:

- `summary`
- `observed_runtime_behavior`
- `runtime_counters`

## 3. Current Honest Result

With the active runtime observation harness in place, the live result is now:

- `summary.counter_gap_rung = "counter_gap_exact"`

That is not parity. It means the remaining cache blocker is now exact:

- runtime-owned `residency_counter` is still absent
- runtime-owned `eviction_counter` is still absent
- runtime-owned `reuse_counter` is now visible on the active runtime path
- scheduler depth remains `serial_single_worker`
- TurboQuant is still below controlled validation

This surface is still intentionally narrower than the later counter-feasibility
freeze. It only says the remaining blocker is exact. It does not yet answer
whether the missing counters are honestly ownable on the current path.

## 4. What This Changes

Before this round, cache was still carried mainly as a closure rung plus a
recommended next step.

Now `owlmlx` owns a narrower answer:

- the active runtime path is frozen strongly enough to stop re-litigating
  whether cache observations exist
- the remaining blocker is no longer "refresh cache evidence"
- the remaining blocker is "implement one of the exact missing counter/scheduler
  pieces without overclaiming parity"

## 5. What This Does Not Claim

It does not claim:

- cache parity with `oMLX` / `vMLX`
- continuous batching
- non-serial scheduler depth
- safe TurboQuant rollout

It only claims:

- `cache_scheduler_depth` is no longer blocked by missing observation truth
- the remaining cache blocker is now exact and runtime-owned
