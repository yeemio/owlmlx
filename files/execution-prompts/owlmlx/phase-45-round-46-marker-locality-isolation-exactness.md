# owlmlx Phase 45 Round 46: Marker Locality-Isolation Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim marker locality access is
already exact.

## Current frozen truth

- before whole-request gate claim only explicit pre-claim drop/cancel logic,
  gate-claim expiry, and pre-claim discard observation may reach the adjacent
  inert marker slot
- scheduler, child/backend, stream, and execution-priority paths may not access
  it

## This round must do

1. freeze whether the adjacent inert slot is isolated per staged request
2. distinguish allowed per-request locality from forbidden shared pending-state
   locality expansions
3. keep locality isolation free of hidden queue ownership or execution routing

## Minimum deliverables

- one narrow runtime-owned locality-isolation surface
- focused tests
- one live script run showing the exact locality-isolation result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let marker locality isolation become hidden queue metadata
- do not introduce execution-bearing shared pending-state locality before gate
  claim
- do not drift back to shell/product work
