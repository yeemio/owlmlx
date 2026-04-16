# owlmlx Phase 45 Round 43: Marker Encoding-Carrier Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim marker payload shape is already
exact.

## Current frozen truth

- before whole-request gate claim marker state collapses to pure
  presence/absence only
- no reason-code, priority, queue-metadata, or child/stream/execution payload
  fields may exist

## This round must do

1. freeze what exact inert encoding carrier holds that presence/absence bit
2. distinguish allowed inert encoding from forbidden ownership-bearing encoding
   expansions
3. keep the encoding carrier free of hidden queue ownership or execution
   routing

## Minimum deliverables

- one narrow runtime-owned encoding-carrier surface
- focused tests
- one live script run showing the exact encoding-carrier result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let pre-claim marker encoding become hidden queue metadata
- do not introduce execution-bearing encoding before gate claim
- do not drift back to shell/product work
