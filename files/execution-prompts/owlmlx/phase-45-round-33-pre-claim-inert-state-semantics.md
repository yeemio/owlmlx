# owlmlx Phase 45 Round 33: Pre-Claim Inert-State Semantics

## Goal

Advance `cache_scheduler_depth` after the pre-claim metadata/ticket ownership
boundary is already exact.

## Current frozen truth

- `owlmlx.cache_pre_claim_metadata_ticket_ownership` is exact
- ticket reservation is observational-only and grants no execution rights
  before gate claim
- immutable request metadata is read-only before gate claim
- forbidden promotions:
  - `no_gate_claim_rights_from_ticket_reservation`
  - `no_mutable_request_state_from_metadata_snapshot`
  - `no_child_or_stream_handle_derivation_before_claim`
  - `no_model_execution_entitlement_before_claim`

## This round must do

1. freeze the exact cohort/drop semantics, if any, that may exist on inert
   pre-claim state
2. distinguish:
   - inert cohort candidacy or drop/cancel markers that may be allowed
   - any semantics that must still wait until whole-request gate claim
3. keep inert pre-claim state free of execution rights

## Minimum deliverables

- one narrow runtime-owned inert-state semantics surface or equivalent exact
  freeze
- focused tests
- one live script run showing the exact inert-state result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim request aggregation exists unless runtime-owned proof actually
  moves
- do not let inert state become hidden gate ownership or hidden execution
- do not drift back to shell/product work
