# owlmlx Phase 45 Round 39: Marker Clear/Observer Boundary

## Goal

Advance `cache_scheduler_depth` after pre-claim marker state-carrier exactness
is already frozen.

## Current frozen truth

- `owlmlx.cache_pre_claim_marker_state_carrier` is exact
- a marker may live only in a single inert write-once/clear-only record before
  whole-request gate claim
- that carrier may not become queue slot identity, batch membership, child
  payload attachment, or stream/execution state

## This round must do

1. freeze which path may clear the inert marker carrier
2. freeze which path may only observe it
3. keep clear/observe semantics free of hidden scheduler ownership or execution
   routing

## Minimum deliverables

- one narrow runtime-owned clear/observer boundary surface
- focused tests
- one live script run showing the exact clear/observer result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let marker clear ownership become hidden queue ownership
- do not let observer-only paths silently gain clearer rights
- do not drift back to shell/product work
