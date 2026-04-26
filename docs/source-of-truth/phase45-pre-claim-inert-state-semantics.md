# owlmlx Phase 45: Pre-Claim Inert-State Semantics

> Status: authoritative
> Updated: 2026-04-16
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

- `cohort_candidate_status = bounded_runtime_owned_cohort_membership_before_gate_claim_without_execution_rights`
- `drop_cancel_status = inert_drop_or_cancel_marker_allowed_before_gate_claim`
- `allowed_inert_semantics = ["drop_or_cancel_marker_before_gate_claim", "bounded_pre_claim_cohort_membership_without_execution_rights"]`

The forbidden inert semantics are:

- `no_execution_priority_before_gate_claim`
- `no_prefill_batch_membership_before_gate_claim`

## 4. What This Changes

Before this round, `owlmlx` could say:

- pre-claim state was inert
- metadata/ticket ownership was exact

Now it can say something narrower:

- drop/cancel markers remain inert before gate claim
- bounded cohort membership may now exist before gate claim, but still without
  execution rights
- the remaining question is no longer generic cohort absence; it is how to keep
  the widened pre-claim state from inflating into execution priority or
  downstream dispatch claims

## 5. What This Does Not Claim

It does not claim:

- execution priority before gate claim
- request aggregation exists
- inert state may gain queue ownership or execution priority

It only freezes the widened inert-state boundary more precisely.

## 6. Next Closure Step

The next exact local round is no longer generic marker-only work.

The next dependency round must preserve that:

- pre-claim cohort membership still grants no execution priority
- prefill-batch membership still does not exist before claim
- whole-request gate claim remains the first post-claim serial boundary
