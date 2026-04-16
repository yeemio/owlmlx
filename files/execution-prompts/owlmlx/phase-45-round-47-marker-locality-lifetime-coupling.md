# owlmlx Phase 45 Round 47: Marker Locality-Lifetime Coupling

## Goal

Advance `cache_scheduler_depth` after pre-claim marker locality isolation is
already exact.

## Current frozen truth

- before whole-request gate claim the adjacent inert marker slot is isolated per
  staged request
- no shared pending-state scheduler/backend/stream locality or cross-request
  marker merge may exist

## This round must do

1. freeze how isolated marker locality is reclaimed or expired relative to
   staged request lifetime
2. distinguish allowed lifetime coupling from forbidden ownership-bearing
   lifetime coupling expansions
3. keep locality lifetime coupling free of hidden queue ownership or execution
   routing

## Minimum deliverables

- one narrow runtime-owned locality-lifetime surface
- focused tests
- one live script run showing the exact locality-lifetime result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let marker locality lifetime become hidden queue metadata
- do not introduce execution-bearing lifetime coupling before gate claim
- do not drift back to shell/product work
