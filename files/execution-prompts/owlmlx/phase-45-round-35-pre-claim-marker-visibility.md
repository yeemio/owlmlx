# owlmlx Phase 45 Round 35: Pre-Claim Marker Visibility

## Goal

Advance `cache_scheduler_depth` after the inert pre-claim marker lifetime is
already exact.

## Current frozen truth

- `owlmlx.cache_pre_claim_marker_lifetime` is exact
- inert marker lifetime:
  - `explicit_drop_before_gate_claim`
  - `explicit_cancel_before_gate_claim`
  - `implicit_expiry_at_gate_claim`
- forbidden promotions:
  - `no_queue_ownership_from_marker_lifetime`
  - `no_cohort_hold_across_gate_claim_boundary`
  - `no_execution_entitlement_from_marker_lifetime`
  - `no_post_claim_state_transfer_from_expired_marker`

## This round must do

1. freeze the exact visibility/discard-trigger semantics for inert pre-claim
   markers
2. distinguish:
   - who may observe or clear a marker before gate claim
   - any visibility or ownership semantics that still must remain absent
3. keep markers free of hidden queue ownership or execution rights

## Minimum deliverables

- one narrow runtime-owned visibility/trigger surface or equivalent exact
  freeze
- focused tests
- one live script run showing the exact visibility result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim request aggregation exists unless runtime-owned proof actually
  moves
- do not let marker visibility become hidden queue ownership
- do not drift back to shell/product work
