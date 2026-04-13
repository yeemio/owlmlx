# owlmlx Phase 45: Cache Residency/Reuse Evidence

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only cache residency/reuse evidence for replacement-grade alignment

## 1. Purpose

This document advances `cache_scheduler_depth` one step past pure status truth.

The question it answers is:

**What runtime-owned evidence does `owlmlx` actually have today for cache
residency or reuse behavior?**

This is still narrower than cache parity. It exists so the runtime can separate:

- cache profile visibility
- scheduler depth truth
- actual runtime-owned evidence of residency or reuse

## 2. Owned Contract

`owlmlx/cache_residency_evidence.py` now owns:

- `build_cache_residency_evidence(...)`
- `cache_residency_evidence_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_residency_evidence.py`

Contract:

- `surface = "owlmlx.cache_residency_evidence"`
- `version = "phase45"`

Stable sections:

- `summary`
- `cache_profile`
- `scheduler_activity`
- `residency_metrics`

## 3. Evidence Semantics

Current `summary.evidence_status` values:

- `no_runtime_evidence`
- `configuration_only`
- `profile_active_under_load`
- `residency_signal_visible`
- `reuse_signal_visible`

Interpretation:

- `no_runtime_evidence`
  - no cache profile visibility and no runtime-owned evidence signal
- `configuration_only`
  - cache profile visibility exists, but runtime-owned serving evidence does not
- `profile_active_under_load`
  - the cache-capable runtime profile is active and has served requests
  - residency/reuse signals are still not visible
- `residency_signal_visible`
  - runtime-owned residency evidence is visible
  - explicit reuse evidence is still missing
- `reuse_signal_visible`
  - runtime-owned reuse or hit signals are visible
  - this still does not claim full cache closure or deeper scheduler parity

## 4. Current Honest Result

Current default result from the runtime-owned evidence surface is:

- `summary.status = "partial"`
- `summary.evidence_status = "no_runtime_evidence"`
- `summary.blocked_reason = "runtime-owned cache residency and reuse evidence remain below replacement-grade closure"`

This is the honest starting point because `owlmlx` still does not own:

- cache hit counters in live runtime status
- eviction policy evidence
- repeated-serving cache closure evidence

What it can now express honestly is the rung where current evidence sits.

## 5. What This Changes

Before this round, `owlmlx` had:

- cache truth
- cache/scheduler depth status

But it still lacked a runtime-owned way to say:

- whether any runtime-serving evidence exists yet
- whether that evidence is only configuration, profile-under-load, residency,
  or reuse

Now `owlmlx` owns that answer directly.

## 6. What This Does Not Claim

It does not claim:

- paged cache closure
- disk-tier cache closure
- eviction closure
- cache parity with `oMLX` / `vMLX`
- customer-grade scheduler depth

It only claims:

- `owlmlx` can now express cache residency/reuse evidence as a runtime-owned
  contract
- the current closure level remains partial
- the next honest step is stronger repeated-serving and eviction evidence
