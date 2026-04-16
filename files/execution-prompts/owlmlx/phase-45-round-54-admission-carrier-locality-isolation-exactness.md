# owlmlx Phase 45 Round 54: Admission-Carrier Locality-Isolation Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim admission-carrier locality-
access exactness is already frozen.

## Current frozen truth

- only staged metadata snapshot building, observational ticket reservation,
  same-request pre-claim drop/cancel reset, and same-request pre-claim discard
  observation may reach the bounded inert pre-claim carrier before claim
- queue/cohort scheduler, child/backend payload, stream-handle, and execution-
  entitlement paths may not access it

## This round must do

1. freeze whether the bounded inert pre-claim carrier remains isolated per
   staged request before gate claim
2. distinguish allowed isolated semantics from forbidden shared pending-state
   locality
3. keep locality-isolation exactness subordinate to the already-frozen
   post-claim safety invariants

## Minimum deliverables

- one narrow runtime-owned admission-carrier locality-isolation surface
- focused tests
- one live script run showing the exact locality-isolation result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let isolation exactness reintroduce queue ownership or execution state
- do not drift back to shell/product work
