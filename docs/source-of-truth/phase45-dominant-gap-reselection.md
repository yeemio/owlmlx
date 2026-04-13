# owlmlx Phase 45: Dominant-Gap Reselection

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only dominant-gap reselection after cache and governance exactness freezes

## 1. Purpose

This document freezes the runtime-owned answer to one narrow loop question:

**After cache scheduler backlog, TurboQuant preconditions, and governance
policy gap are all frozen exact, which locally reducible gap should `owlmlx`
work next?**

The purpose is not to restart narrative comparison. The purpose is to keep the
loop honest once multiple branches are already exact and the runtime needs one
machine-readable next-step decision.

## 2. Owned Contract

`owlmlx/dominant_gap_reselection.py` now owns:

- `build_dominant_gap_reselection(...)`
- `dominant_gap_reselection_to_dict(...)`

Operator entry:

- `scripts/runtime_dominant_gap_reselection.py`

Contract:

- `surface = "owlmlx.dominant_gap_reselection"`
- `version = "phase45"`

Stable sections:

- `summary`
- `candidate_gap_truth`

## 3. Current Honest Result

Current live result is:

- `summary.decision_rung = "reselection_exact"`
- `summary.selected_gap = "cache_scheduler_depth"`

Candidate-gap truth is now frozen as:

- `cache_scheduler_depth`
  - `scheduler_backlog_rung = "implementation_gap_exact"`
  - `turboquant_preconditions_rung = "preconditions_exact"`
- `multi_model_lifecycle_governance`
  - `policy_gap_rung = "policy_gap_exact"`
- `heavy_weight_runtime_repeatability`
  - `repeatability_rung = "local_blocked"`

## 4. Why Cache Still Wins

`cache_scheduler_depth` remains dominant because:

- the cache branch is still the clearest locally reducible runtime gap
- its remaining scheduler work is exact and implementation-grade
- TurboQuant is exact but secondary on the same branch
- governance has already narrowed to policy-grade absent controls
- heavy-weight repeatability is still externally blocked on this host

That means the loop should keep working cache/scheduler closure before
returning to governance or pretending the current host can close heavy-weight
runtime proof.

## 5. What This Does Not Claim

It does not claim:

- cache parity with `oMLX` / `vMLX`
- governance closure
- supported-host heavy-weight repeatability

It only claims:

- the next locally reducible dominant gap has been reselected exactly
- the loop no longer needs to infer the next branch from narrative comparison
