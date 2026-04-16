# owlmlx Phase 45 Round 56: Admission-Carrier Reclaim-Reset Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim admission-carrier locality-
lifetime coupling is already frozen.

## Current frozen truth

- the bounded inert pre-claim carrier is coupled only to its own staged-
  request lifetime before claim
- it may be reclaimed only by same-request pre-claim discard or gate-claim
  expiry transition
- it may not survive into cross-request reuse or retained scheduler/backend/
  stream lifetime

## This round must do

1. freeze the exact clean-state reset reclaim leaves on the bounded inert
   carrier
2. distinguish allowed reset semantics from forbidden prior-history residue
3. keep reclaim-reset exactness subordinate to the already-frozen post-claim
   safety invariants

## Minimum deliverables

- one narrow runtime-owned admission-carrier reclaim-reset surface
- focused tests
- one live script run showing the exact reclaim-reset result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let reclaim-reset exactness reintroduce queue ownership or execution state
- do not drift back to shell/product work
