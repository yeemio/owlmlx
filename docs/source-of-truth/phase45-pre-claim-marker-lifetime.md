# owlmlx Phase 45: Pre-Claim Marker Lifetime

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only inert drop/cancel marker lifetime before gate claim

## 1. Purpose

Freeze the exact lifetime and expiry boundary for inert pre-claim drop/cancel
markers once inert-state semantics are already exact.

## 2. Owned Contract

`owlmlx/cache_pre_claim_marker_lifetime.py` now owns:

- `build_cache_pre_claim_marker_lifetime(...)`
- `cache_pre_claim_marker_lifetime_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_pre_claim_marker_lifetime.py`

Contract:

- `surface = "owlmlx.cache_pre_claim_marker_lifetime"`
- `version = "phase45"`

Stable sections:

- `summary`
- `marker_lifetime_boundary`
- `forbidden_lifetime_promotions`

## 3. Current Honest Result

The current exact result is:

- `exactness_rung = marker_lifetime_exact`

The marker lifetime boundary is:

- `marker_lifetime_status = marker_may_exist_only_until_gate_claim_or_explicit_pre_claim_discard`
- `marker_expiry_boundary = marker_expires_at_gate_claim_or_pre_claim_discard_boundary`
- `allowed_lifetime_events = ["explicit_drop_before_gate_claim", "explicit_cancel_before_gate_claim", "implicit_expiry_at_gate_claim"]`

The forbidden lifetime promotions are:

- `no_queue_ownership_from_marker_lifetime`
- `no_cohort_hold_across_gate_claim_boundary`
- `no_execution_entitlement_from_marker_lifetime`
- `no_post_claim_state_transfer_from_expired_marker`

## 4. What This Changes

Before this round, `owlmlx` could say:

- drop/cancel markers were the only allowed inert semantics
- inert state was still free of cohort membership and execution priority

Now it can say something narrower:

- marker lifetime is exact
- marker expiry boundary is exact
- the remaining question is now marker visibility and discard-trigger behavior,
  not generic lifetime

## 5. What This Does Not Claim

It does not claim:

- markers own queue position
- markers survive across gate claim
- markers can promote into execution state

It only freezes the lifetime/expiry boundary more precisely.

## 6. Next Closure Step

The next exact local round should freeze marker visibility and discard-trigger
semantics:

- who may observe a pre-claim marker
- what exact discard trigger exists before gate claim
- what still must remain unavailable until whole-request gate claim occurs
