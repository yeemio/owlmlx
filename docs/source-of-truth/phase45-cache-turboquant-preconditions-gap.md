# owlmlx Phase 45: Cache TurboQuant Preconditions Gap

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only exact TurboQuant preconditions on the active cache path

## 1. Purpose

This document freezes the remaining TurboQuant branch after cache closure has
already narrowed through:

- exact counter ownership
- exact scheduler/TurboQuant split
- exact serial scheduler floor
- exact scheduler implementation backlog

The question it answers is:

**Which TurboQuant preconditions are still missing on the current path, and can
that remaining blocker now be treated as exact rather than generic
`safety_blocked` truth?**

## 2. Owned Contract

`owlmlx/cache_turboquant_preconditions_gap.py` now owns:

- `build_cache_turboquant_preconditions_gap(...)`
- `cache_turboquant_preconditions_gap_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_turboquant_preconditions_gap.py`

Contract:

- `surface = "owlmlx.cache_turboquant_preconditions_gap"`
- `version = "phase45"`

Stable sections:

- `summary`
- `missing_preconditions`

## 3. Current Honest Result

Current live result from the runtime-owned harness is:

- `summary.preconditions_rung = "preconditions_exact"`
- missing preconditions:
  - `bits_in_cache_key`
  - `invalidates_on_config_toggle`
  - `runtime_verified`

This means the TurboQuant branch is no longer just a generic safety posture.
It is now an exact, enumerated preconditions gap.

## 4. What This Changes

Before this round, the cache branch could already say:

- scheduler work is exact
- TurboQuant is still `safety_blocked`

But `safety_blocked` was still one layer too coarse.

Now `owlmlx` owns one narrower answer:

- which exact TurboQuant preconditions are still missing
- that this branch is exact but secondary on the current cache path
- that further work should not inflate TurboQuant readiness until those exact
  preconditions are actually satisfied

## 5. What This Does Not Claim

It does not claim:

- TurboQuant is ready for controlled validation
- TurboQuant is an optimization win
- parity with `oMLX` / `vMLX`

It only claims:

- the TurboQuant branch is now exact rather than generic
- the current path still lacks the precise preconditions required for safe
  activation
- scheduler implementation remains the dominant cache-side work on this path
