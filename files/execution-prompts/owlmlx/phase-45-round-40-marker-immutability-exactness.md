# owlmlx Phase 45 Round 40: Marker Immutability Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim marker clear/observer ownership
is already exact.

## Current frozen truth

- only explicit pre-claim drop/cancel logic and gate-claim expiry may clear the
  inert marker carrier
- pre-claim discard may only observe it
- scheduler, child/backend, stream, and execution-priority paths remain
  ineligible as clearers before gate claim

## This round must do

1. freeze whether any pre-claim path may mutate marker state beyond clear-only
   semantics
2. distinguish allowed immutability semantics from forbidden mutation
   expansions
3. keep marker mutation semantics free of hidden queue ownership or execution
   routing

## Minimum deliverables

- one narrow runtime-owned immutability surface
- focused tests
- one live script run showing the exact immutability result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let pre-claim marker state become hidden queue metadata
- do not introduce execution-bearing marker mutation before gate claim
- do not drift back to shell/product work
