# owlmlx Phase 45: Dominant-Gap Reselection

> Status: authoritative
> Updated: 2026-04-16
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
- `summary.selected_gap = "host_stable_execution"`

Candidate-gap truth is now frozen as:

- `cache_scheduler_depth`
  - `scheduler_backlog_rung = "implementation_gap_exact"`
  - `turboquant_preconditions_rung = "preconditions_exact"`
- `multi_model_lifecycle_governance`
  - `policy_gap_rung = "policy_gap_closed"`
- `heavy_weight_runtime_repeatability`
  - `repeatability_rung = "local_blocked"`

## 4. Why Supported-Host Baseline Re-Assumes Dominance

`host_stable_execution` now re-assumes dominance because:

- the supported-host branch remains the real gating program priority
- the local governance fallback branch is now policy-closed
- cache remains intentionally frozen at `structural_ingress_seam_introduced`
- heavy-weight repeatability remains externally blocked on this host
- continuing local cache/governance micro-rounds would no longer reduce the
  governing blocker inventory honestly

That means the loop should return to supported-host baseline establishment or
stop for a coordinator decision, not continue widening local cache/governance
work.

## 5. What This Does Not Claim

It does not claim:

- cache parity with `oMLX` / `vMLX`
- governance closure
- supported-host heavy-weight repeatability

It only claims:

- the next locally reducible dominant gap has been reselected exactly
- the loop no longer needs to infer the next branch from narrative comparison
- local fallback branch closure can move dominance back to the externally gated
  supported-host branch without inflating runtime maturity
