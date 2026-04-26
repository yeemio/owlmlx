# owlmlx Phase 45: Dominant-Gap Reselection

> Status: authoritative
> Updated: 2026-04-23
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
  - `policy_gap_rung = "policy_gap_closed"`
- `heavy_weight_runtime_repeatability`
  - `repeatability_rung = "supported_host_repeatability_visible"`

## 4. Why Cache-Scheduler Depth Now Reassumes Dominance

`cache_scheduler_depth` now reassumes dominance because:

- supported-host repeated heavy-weight proof is now visible on the current host
- the local governance fallback branch is now policy-closed
- cache has now reopened beyond the old structural checkpoint and the active
  blocker is now post-handoff stream-path work at the
  backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem
  seam, while fuller earlier-runtime-owned-boundary prefix detection plus
  fuller earlier-runtime-owned-boundary detection stay preserved as secondary
  stream truth, current marker-discriminant detection stays frozen as the
  first honest unique boundary on the current runtime-owned marker-first
  record and the newer earlier-runtime-owned discriminator discriminant plus
  the newer earlier-runtime-owned leading-discriminator discriminant stay
  frozen as the first honest unique boundaries on their newer runtime-owned
  records
- continuing host-branch debate would no longer reduce the governing blocker
  inventory honestly
- the next narrower local blocker is now scheduler/cache depth, not supported-
  host proof visibility

That means the loop should keep host truth frozen exact, move the active cache
surface beyond `structural_ingress_seam_introduced`, and still stop before any
parity or readiness inflation.

## 5. What This Does Not Claim

It does not claim:

- cache parity with `oMLX` / `vMLX`
- governance closure
- supported-host heavy-weight repeatability

It only claims:

- the next locally reducible dominant gap has been reselected exactly
- the loop no longer needs to infer the next branch from narrative comparison
- local fallback branch closure plus visible repeated heavy-weight proof move
  the dominant gap back onto `cache_scheduler_depth`
