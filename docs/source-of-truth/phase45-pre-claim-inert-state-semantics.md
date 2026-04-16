# owlmlx Phase 45: Pre-Claim Inert-State Semantics

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only inert semantics before whole-request gate claim

## 1. Purpose

Freeze the exact inert semantics, if any, that may exist before whole-request
gate claim once metadata/ticket ownership is already exact.

## 2. Owned Contract

`owlmlx/cache_pre_claim_inert_state_semantics.py` now owns:

- `build_cache_pre_claim_inert_state_semantics(...)`
- `cache_pre_claim_inert_state_semantics_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_pre_claim_inert_state_semantics.py`

Contract:

- `surface = "owlmlx.cache_pre_claim_inert_state_semantics"`
- `version = "phase45"`

Stable sections:

- `summary`
- `inert_state_boundary`
- `forbidden_inert_semantics`

## 3. Current Honest Result

The current exact result is:

- `exactness_rung = inert_state_semantics_exact`

The inert-state boundary is:

- `cohort_candidate_status = no_runtime_owned_cohort_membership_before_gate_claim`
- `drop_cancel_status = inert_drop_or_cancel_marker_allowed_before_gate_claim`
- `allowed_inert_semantics = ["drop_or_cancel_marker_before_gate_claim"]`

The forbidden inert semantics are:

- `no_cohort_membership_before_gate_claim`
- `no_execution_priority_before_gate_claim`
- `no_prefill_batch_membership_before_gate_claim`

## 4. What This Changes

Before this round, `owlmlx` could say:

- pre-claim state was inert
- metadata/ticket ownership was exact

Now it can say something narrower:

- the only allowed inert semantics are drop/cancel markers
- cohort membership still does not exist before gate claim
- the remaining question is now marker lifetime/expiry, not generic inertness

## 5. What This Does Not Claim

It does not claim:

- a cohort window exists
- request aggregation exists
- inert state may gain queue ownership or execution priority

It only freezes the inert-state boundary more precisely.

## 6. Next Closure Step

The next exact local round should freeze ticket drop/cancel lifetime and expiry
boundaries:

- what exact lifetime a pre-claim drop/cancel marker has
- when it may expire or be discarded before gate claim
- what still must wait until whole-request gate claim occurs
