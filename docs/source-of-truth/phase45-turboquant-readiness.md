# owlmlx Phase 45: TurboQuant Readiness

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only TurboQuant safety/readiness for replacement-grade alignment

## 1. Purpose

This document keeps TurboQuant inside the replacement-grade cache gap without
pretending it is already a runtime optimization win.

The question it answers is:

**Is TurboQuant still safety-blocked, merely evidence-blocked, or actually
ready for controlled runtime validation inside `owlmlx`?**

## 2. Owned Contract

`owlmlx/turboquant_readiness.py` now owns:

- `build_turboquant_readiness(...)`
- `turboquant_readiness_to_dict(...)`

Operator entries:

- `scripts/runtime_turboquant_readiness.py`
- `scripts/runtime_cache_runtime_observation_harness.py`

Contract:

- `surface = "owlmlx.turboquant_readiness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `turboquant_cache_safety`
- `cache_repeatability`

## 3. Readiness Semantics

Current `summary.status` values:

- `safety_blocked`
- `evidence_blocked`
- `ready_for_controlled_validation`

Interpretation:

- `safety_blocked`
  - cache key isolation, config-toggle invalidation, or runtime verification is
    still missing
- `evidence_blocked`
  - safety preconditions are satisfied
  - repeated-serving cache evidence is still too shallow
- `ready_for_controlled_validation`
  - safety preconditions are satisfied
  - repeated-serving evidence has reached reuse/eviction visibility strong
    enough for a controlled runtime validation rung

## 4. Current Honest Result

Current default result from the runtime-owned TurboQuant readiness surface is:

- `summary.status = "safety_blocked"`
- `summary.ready = false`

Even when safety passes, the honest next default is still often:

- `summary.status = "evidence_blocked"`

because `owlmlx` still does not own direct runtime reuse/eviction counters on
the active cache-capable path.

## 5. What This Changes

Before this round, `owlmlx` had:

- TurboQuant cache-safety rules
- cache repeatability evidence

But it still lacked one runtime-owned answer to this narrower question:

- are the current safety and repeated-serving evidence rungs jointly strong
  enough to justify controlled TurboQuant validation

Now `owlmlx` owns that answer directly.

## 6. What This Does Not Claim

It does not claim:

- TurboQuant is production-ready
- TurboQuant is already an optimization win
- cache parity with `oMLX` / `vMLX`

It only claims:

- TurboQuant is now inside `owlmlx` as a runtime-owned readiness decision
- the current readiness still remains conservative
- the next honest cache step is a stronger closure rung that combines
  scheduler truth, runtime evidence, and this readiness surface
