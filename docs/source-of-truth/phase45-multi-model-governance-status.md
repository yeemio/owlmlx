# owlmlx Phase 45: Multi-Model Governance Status

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only multi-model lifecycle governance for replacement-grade alignment

## 1. Purpose

This document advances `multi_model_lifecycle_governance` from a narrative gap
 into a runtime-owned contract.

The question it answers is:

**What multi-model lifecycle behavior does `owlmlx` actually own today, and
what still remains absent relative to `oMLX` / `vMLX`?**

## 2. Owned Contract

`owlmlx/multi_model_governance_status.py` now owns:

- `build_multi_model_governance_status(...)`
- `multi_model_governance_status_to_dict(...)`

Operator entry:

- `scripts/runtime_multi_model_governance_status.py`

Contract:

- `surface = "owlmlx.multi_model_governance_status"`
- `version = "phase45"`

Stable sections:

- `summary`
- `inventory`
- `budget`
- `active_model`
- `governance_controls`
- `recoverability`

## 3. Governance Rungs

Current `summary.governance_rung` values:

- `inventory_visible`
- `active_default_visible`
- `restart_visibility_visible`
- `partial_closure`

Interpretation:

- `inventory_visible`
  - resident-model truth exists, but no live active/default behavior is visible yet
- `active_default_visible`
  - active/default selection semantics are visible
  - deeper recoverability/governance is still partial
- `restart_visibility_visible`
  - restart/unload recoverability is visible
  - pinning, TTL, and eviction-history governance remain absent
- `partial_closure`
  - live multi-model residency, active/default semantics, and recoverability are all visible
  - this is still below reference-grade parity because absent controls remain explicit

## 4. Current Honest Result

This surface still returns:

- `summary.status = "partial"`

That remains the honest answer because `owlmlx` still does not own:

- pinning
- TTL policy
- eviction-history governance

## 5. What This Changes

Before this round, `owlmlx` had:

- inventory truth
- budget truth
- restartability truth

But it still lacked one runtime-owned answer to:

- how active/default model semantics actually work
- what resident multi-model behavior is visible right now
- which lifecycle controls are genuinely absent instead of merely undocumented

Now `owlmlx` owns that answer directly.

## 6. What This Does Not Claim

It does not claim:

- policy-owned TTL exists in the runtime
- pinning exists in the runtime
- eviction history exists in the runtime
- multi-model parity with `oMLX` / `vMLX`

It only claims:

- `owlmlx` now has a runtime-owned multi-model governance surface
- current closure remains conservative and partial
- remaining absent controls are explicit instead of narrative
