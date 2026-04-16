# owlmlx Phase 45 Round 32: Pre-Claim Metadata/Ticket Ownership

## Goal

Advance `cache_scheduler_depth` after the bounded pre-claim staging seam is
already exact.

## Current frozen truth

- `owlmlx.cache_pre_claim_staging_seam_exactness` is exact
- the only allowed staged units are:
  - `immutable_request_metadata_snapshot`
  - `ticket_reservation_without_gate_claim`
- forbidden staging expansions:
  - `no_gate_ownership_transfer_before_claim`
  - `no_child_payload_assembly_before_claim`
  - `no_stream_handle_allocation_before_claim`
  - `no_model_state_or_prefill_before_claim`

## This round must do

1. freeze the exact ownership/lifetime boundary for pre-claim ticket
   reservation
2. freeze the exact metadata boundary for immutable request metadata snapshot
3. distinguish:
   - what may exist pre-claim only as inert staging state
   - what must remain unavailable until whole-request gate claim

## Minimum deliverables

- one narrow runtime-owned ownership/boundary surface or equivalent exact
  freeze
- focused tests
- one live script run showing the exact ownership result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim request aggregation exists unless runtime-owned proof actually
  moves
- do not let ticket reservation become hidden gate ownership
- do not drift back to shell/product work
