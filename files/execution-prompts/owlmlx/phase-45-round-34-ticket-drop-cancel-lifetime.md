# owlmlx Phase 45 Round 34: Ticket Drop/Cancel Lifetime

## Goal

Advance `cache_scheduler_depth` after the inert pre-claim semantics are
already exact.

## Current frozen truth

- `owlmlx.cache_pre_claim_inert_state_semantics` is exact
- the only allowed inert semantics before gate claim are:
  - `drop_or_cancel_marker_before_gate_claim`
- forbidden inert semantics:
  - `no_cohort_membership_before_gate_claim`
  - `no_execution_priority_before_gate_claim`
  - `no_prefill_batch_membership_before_gate_claim`

## This round must do

1. freeze the exact lifetime/expiry boundary for pre-claim drop/cancel markers
2. distinguish:
   - inert marker lifetime that may exist before gate claim
   - any queue ownership or execution semantics that still must remain absent
3. keep inert markers free of hidden queue ownership

## Minimum deliverables

- one narrow runtime-owned lifetime surface or equivalent exact freeze
- focused tests
- one live script run showing the exact lifetime result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim request aggregation exists unless runtime-owned proof actually
  moves
- do not let drop/cancel markers become hidden queue ownership
- do not drift back to shell/product work
