# owlmlx Phase 45 Round 50: Admission-Carrier Field Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim admission-carrier construction
is already exact.

## Current frozen truth

- any bounded pre-claim admission carrier may be constructed only from
  immutable request metadata, observational ticket reservation, and a fully
  reset inert marker slot
- no queue-owned, execution-bearing, child/stream-attached, or
  scheduler-priority carrier may exist before gate claim

## This round must do

1. freeze what exact fields may inhabit that bounded inert carrier
2. distinguish allowed inert field sets from forbidden ownership-bearing or
   execution-bearing field expansions
3. keep field exactness subordinate to the already-frozen post-claim safety
   invariants

## Minimum deliverables

- one narrow runtime-owned admission-carrier field surface
- focused tests
- one live script run showing the exact field result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let field exactness reintroduce queue ownership or execution state
- do not drift back to shell/product work
