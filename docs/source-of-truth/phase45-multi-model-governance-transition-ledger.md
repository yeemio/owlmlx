# owlmlx Phase 45: Multi-Model Governance Transition Ledger

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only transition evidence for multi-model governance

## 1. Purpose

This document advances `multi_model_lifecycle_governance` from a controls
surface into a smaller runtime-owned transition ledger.

The question it answers is:

**Are recent governance transitions visible as first-class runtime truth, and
has repeated transition evidence become strong enough to freeze the remaining
governance gap exactly?**

## 2. Owned Contract

`owlmlx/multi_model_governance_transition_ledger.py` now owns:

- `build_multi_model_governance_transition_ledger(...)`
- `multi_model_governance_transition_ledger_to_dict(...)`

Operator entry:

- `scripts/runtime_multi_model_governance_transition_ledger.py`

Contract:

- `surface = "owlmlx.multi_model_governance_transition_ledger"`
- `version = "phase45"`

Stable sections:

- `summary`
- `recent_window`
- `transition_signals`

## 3. Ledger Rungs

Current `summary.ledger_rung` values:

- `no_transition_runs`
- `transition_visibility`
- `repeated_transition_visibility`
- `partial_closure`

Interpretation:

- `no_transition_runs`
  - no repeated governance-transition evidence is visible yet
- `transition_visibility`
  - one transition window is visible
- `repeated_transition_visibility`
  - repeated governance-transition evidence is visible
  - absent lifecycle controls remain exact
- `partial_closure`
  - repeated transition evidence for active reassignment, explicit targeting,
    and restart restore is visible
  - pinning, TTL, and eviction-history governance still remain absent

## 4. Current Honest Result

This surface still returns:

- `summary.status = "partial"`

That remains the honest answer because `owlmlx` still does not own:

- pinning
- TTL policy
- eviction-history governance

## 5. What This Changes

Before this round, `owlmlx` had governance status and governance controls, but
not a narrower answer to:

- whether recent governance transitions are visible as first-class runtime truth
- whether repeated transition evidence is strong enough to freeze the remaining
  governance gap exactly

Now `owlmlx` owns that answer directly.

The recent-window transition signals no longer need to be passed in as a pure
harness-side dict. When available, this ledger now consumes
`runtime.status.governance_observations`, which is produced by the active
kernel path.

## 6. What This Does Not Claim

It does not claim:

- eviction history exists
- lifecycle TTL exists
- pinning exists
- governance parity with `oMLX` / `vMLX`

It only claims:

- `owlmlx` now has a runtime-owned transition ledger for governance
- repeated transition evidence is distinguishable from absent lifecycle controls
  through runtime-owned observations rather than harness-only synthesis
- remaining governance absences are still exact rather than narrative
