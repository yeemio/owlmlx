# owlmlx Phase 45: Cache Closure Rung

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only cache closure summary for replacement-grade alignment

## 1. Purpose

This document turns the current cache work from a set of separate surfaces into
one conservative closure rung.

The question it answers is:

**How far has `owlmlx` actually progressed inside `cache_scheduler_depth`,
without pretending parity with `oMLX` / `vMLX`?**

## 2. Owned Contract

`owlmlx/cache_closure_rung.py` now owns:

- `build_cache_closure_rung(...)`
- `cache_closure_rung_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_closure_rung.py`

Contract:

- `surface = "owlmlx.cache_closure_rung"`
- `version = "phase45"`

Stable sections:

- `summary`
- `scheduler`
- `residency`
- `repeatability`
- `turboquant`

## 3. Closure Labels

Current `summary.closure_rung` values:

- `truth_only`
- `evidence_visible`
- `repeatability_visible`
- `turboquant_safety_ready`
- `partial_closure`

Interpretation:

- `truth_only`
  - the runtime has cache/scheduler truth, but evidence is still too shallow
- `evidence_visible`
  - one-shot cache evidence exists, but repeated-serving closure is still open
- `repeatability_visible`
  - repeated-serving evidence exists, but direct runtime-owned
    residency/eviction counters or deeper scheduler depth still remain open
- `turboquant_safety_ready`
  - TurboQuant safety preconditions are met
  - broader cache closure still remains partial
- `partial_closure`
  - repeated-serving reuse/eviction evidence plus TurboQuant readiness are both
    visible
  - this is stronger than earlier rungs, but still below reference-grade parity

## 4. Current Honest Result

This surface still returns:

- `summary.status = "partial"`

That remains the honest top-level answer because `owlmlx` still does not own:

- deeper scheduler behavior than `serial_single_worker`
- direct runtime-owned residency/eviction counters on the active cache path strong
  enough to claim broader cache closure

With the active runtime observation harness in place, the stronger live cache
answer is no longer the old `truth_only` baseline. The live harness currently
pushes cache closure to:

- `summary.closure_rung = "repeatability_visible"`

That is still partial. It means the active runtime path now shows repeated
serving strongly enough to freeze the remaining cache blocker more narrowly:

- direct runtime-owned `reuse_counter` is now visible
- direct runtime-owned `residency_counter` and `eviction_counter` are still absent
- deeper scheduler behavior remains serial-only

## 5. What This Changes

Before this round, `owlmlx` had:

- cache scheduler status
- one-shot residency/reuse evidence
- repeated-serving evidence
- TurboQuant readiness

But it still lacked one runtime-owned answer to:

- what the current cache closure rung actually is
- what exact blocker still prevents a stronger claim

Now `owlmlx` owns that answer directly.

## 6. What This Does Not Claim

It does not claim:

- cache parity with `oMLX` / `vMLX`
- continuous batching or deeper scheduler parity
- customer-grade runtime cache stability

It only claims:

- `owlmlx` now has a runtime-owned cache closure rung
- the current result remains partial and conservative
- the next honest dominant gap can move off cache once this blocker is frozen
