# owlmlx Phase 45 Round 38: Marker State-Carrier Exactness

## Goal

Advance `cache_scheduler_depth` after the inert pre-claim marker
reader/writer ownership is already exact.

## Current frozen truth

- `owlmlx.cache_pre_claim_marker_reader_writer_ownership` is exact
- allowed writer paths:
  - `explicit_pre_claim_drop_cancel_writer`
  - `gate_claim_expiry_writer`
- allowed reader-only path:
  - `pre_claim_discard_observer`
- forbidden writer expansions:
  - `no_scheduler_writer_before_claim`
  - `no_child_backend_writer_before_claim`
  - `no_stream_writer_before_claim`
  - `no_execution_priority_writer_before_claim`

## This round must do

1. freeze the exact inert state carrier for pre-claim markers
2. distinguish:
   - which carrier semantics may exist before gate claim
   - which carrier semantics must still remain unavailable until gate claim
3. keep marker state-carrier semantics free of hidden queue ownership or
   execution routing

## Minimum deliverables

- one narrow runtime-owned state-carrier surface or equivalent exact freeze
- focused tests
- one live script run showing the exact state-carrier result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim request aggregation exists unless runtime-owned proof actually moves
- do not let marker state-carrier semantics become hidden queue ownership
- do not drift back to shell/product work
