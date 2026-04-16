# owlmlx Phase 45 Round 52: Admission-Carrier Locality Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim admission-carrier encoding
exactness is already frozen.

## Current frozen truth

- immutable request metadata, observational ticket reservation, and a fully
  reset inert marker presence bit may be encoded only as one bounded inert
  pre-claim record
- no queue identity, scheduler priority, batch membership, child/stream
  attachment, or execution-bearing encoding may exist before gate claim

## This round must do

1. freeze where that bounded inert pre-claim record may live before gate claim
2. distinguish allowed inert localities from forbidden ownership-bearing or
   execution-bearing localities
3. keep locality exactness subordinate to the already-frozen post-claim safety
   invariants

## Minimum deliverables

- one narrow runtime-owned admission-carrier locality surface
- focused tests
- one live script run showing the exact locality result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let carrier locality reintroduce queue ownership or execution state
- do not drift back to shell/product work
