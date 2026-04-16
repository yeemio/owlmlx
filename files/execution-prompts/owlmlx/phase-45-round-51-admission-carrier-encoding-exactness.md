# owlmlx Phase 45 Round 51: Admission-Carrier Encoding Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim admission-carrier field
exactness is already frozen.

## Current frozen truth

- a bounded pre-claim carrier may hold only immutable request metadata,
  observational ticket reservation, and a fully reset inert marker presence bit
- no queue identity, scheduler priority, batch membership, child/stream
  attachment, or execution-bearing field may exist before gate claim

## This round must do

1. freeze how those inert fields are encoded together before gate claim
2. distinguish allowed combined encodings from forbidden ownership-bearing or
   execution-bearing encodings
3. keep encoding exactness subordinate to the already-frozen post-claim safety
   invariants

## Minimum deliverables

- one narrow runtime-owned admission-carrier encoding surface
- focused tests
- one live script run showing the exact encoding result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let encoding exactness reintroduce queue ownership or execution state
- do not drift back to shell/product work
