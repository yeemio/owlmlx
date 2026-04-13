# owlmlx Phase 45: Multi-Model Governance Controls

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only governance-control evidence for replacement-grade alignment

## 1. Purpose

This document advances `multi_model_lifecycle_governance` from a visible status
surface into a narrower runtime-owned controls/evidence surface.

The question it answers is:

**Which multi-model governance controls are actually present today, and what
transition evidence does `owlmlx` now own without inventing pinning, TTL, or
eviction policy?**

## 2. Owned Contract

`owlmlx/multi_model_governance_controls.py` now owns:

- `build_multi_model_governance_controls(...)`
- `multi_model_governance_controls_to_dict(...)`

Operator entry:

- `scripts/runtime_multi_model_governance_controls.py`

Contract:

- `surface = "owlmlx.multi_model_governance_controls"`
- `version = "phase45"`

Stable sections:

- `summary`
- `control_presence`
- `transition_evidence`

## 3. Controls Rungs

Current `summary.controls_rung` values:

- `controls_visible`
- `transition_evidence_visible`
- `partial_closure`

Interpretation:

- `controls_visible`
  - active/default policy and absent controls are explicit
- `transition_evidence_visible`
  - runtime-owned transition evidence exists
  - absent controls remain explicit
- `partial_closure`
  - active reassignment, explicit targeting, and restart-restore evidence are visible
  - pinning, TTL, and eviction-history governance still remain absent

## 4. Current Honest Result

This surface still returns:

- `summary.status = "partial"`

That remains the honest answer because `owlmlx` still does not own:

- pinning
- TTL policy
- eviction-history governance

## 5. What This Changes

Before this round, `owlmlx` had a governance status surface, but not a narrower
answer to:

- which controls are present versus absent
- whether transition evidence exists for active reassignment
- whether restart keeps the active model honest under repeated transitions

Now `owlmlx` owns that answer directly.

The repeated transition signals no longer need to be passed in as a pure
harness-side dict. When available, this surface now consumes
`runtime.status.governance_observations`, which comes from the active kernel
path itself.

## 6. What This Does Not Claim

It does not claim:

- policy-owned TTL exists
- pinning exists
- eviction history exists
- multi-model governance parity with `oMLX` / `vMLX`

It only claims:

- `owlmlx` now has a runtime-owned governance-controls surface
- transition evidence can be expressed from runtime-owned governance
  observations without inflating absent controls
- remaining governance absences are exact rather than narrative
