# owlmlx Phase 45 Round 36: Marker Discard Trigger Inputs

## Goal

Advance `cache_scheduler_depth` after the inert pre-claim marker visibility is
already exact.

## Current frozen truth

- `owlmlx.cache_pre_claim_marker_visibility` is exact
- inert markers are visible only to:
  - `pre_claim_discard_path`
  - `gate_claim_expiry_path`
- forbidden visibility expansions:
  - `no_scheduler_selection_visibility_before_claim`
  - `no_child_dispatch_visibility_before_claim`
  - `no_stream_visibility_before_claim`
  - `no_execution_priority_visibility_before_claim`

## This round must do

1. freeze the exact pre-claim discard-trigger inputs for inert markers
2. distinguish:
   - which trigger inputs may clear a marker before gate claim
   - which trigger inputs must still remain unavailable until gate claim
3. keep marker triggers free of hidden queue ownership or execution routing

## Minimum deliverables

- one narrow runtime-owned trigger-input surface or equivalent exact freeze
- focused tests
- one live script run showing the exact trigger-input result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim request aggregation exists unless runtime-owned proof actually
  moves
- do not let marker trigger inputs become hidden queue ownership
- do not drift back to shell/product work
