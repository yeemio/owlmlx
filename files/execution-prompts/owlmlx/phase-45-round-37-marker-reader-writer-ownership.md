# owlmlx Phase 45 Round 37: Marker Reader/Writer Ownership

## Goal

Advance `cache_scheduler_depth` after the inert pre-claim marker trigger inputs
are already exact.

## Current frozen truth

- `owlmlx.cache_pre_claim_marker_trigger_inputs` is exact
- allowed trigger inputs:
  - `explicit_pre_claim_drop_signal`
  - `explicit_pre_claim_cancel_signal`
  - `gate_claim_expiry_transition`
- forbidden trigger inputs:
  - `no_scheduler_pressure_input_before_claim`
  - `no_child_backend_input_before_claim`
  - `no_stream_disconnect_input_before_claim`
  - `no_execution_priority_input_before_claim`

## This round must do

1. freeze the exact reader/writer ownership boundary for pre-claim markers
2. distinguish:
   - which runtime-owned path may author a marker
   - which may only observe or clear a marker
   - which writer ownership must remain unavailable before gate claim
3. keep marker writer ownership free of hidden queue ownership or execution
   routing

## Minimum deliverables

- one narrow runtime-owned reader/writer-ownership surface or equivalent exact
  freeze
- focused tests
- one live script run showing the exact reader/writer result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim request aggregation exists unless runtime-owned proof actually
  moves
- do not let marker writer ownership become hidden queue ownership
- do not drift back to shell/product work
