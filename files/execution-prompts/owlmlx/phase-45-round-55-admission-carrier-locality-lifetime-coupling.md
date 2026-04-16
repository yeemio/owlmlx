# owlmlx Phase 45 Round 55: Admission-Carrier Locality-Lifetime Coupling

## Goal

Advance `cache_scheduler_depth` after pre-claim admission-carrier locality-
isolation exactness is already frozen.

## Current frozen truth

- the bounded inert pre-claim carrier remains isolated per staged request
  before claim
- no shared scheduler/backend/stream pending-state carrier locality or
  cross-request carrier merge may exist

## This round must do

1. freeze how isolated pre-claim carrier locality couples to same-request
   lifetime before gate claim
2. distinguish allowed reclaim/expiry coupling from forbidden retained or
   cross-request lifetime
3. keep locality-lifetime exactness subordinate to the already-frozen
   post-claim safety invariants

## Minimum deliverables

- one narrow runtime-owned admission-carrier locality-lifetime surface
- focused tests
- one live script run showing the exact locality-lifetime result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let locality-lifetime coupling reintroduce queue ownership or execution state
- do not drift back to shell/product work
