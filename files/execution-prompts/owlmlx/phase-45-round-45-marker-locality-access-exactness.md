# owlmlx Phase 45 Round 45: Marker Locality-Access Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim marker storage locality is
already exact.

## Current frozen truth

- before whole-request gate claim the inert boolean marker slot may live only
  adjacent to staged metadata and outside ticket identity / immutable metadata
  payload
- it may not occupy queue, scheduler, child, stream, or execution-local
  storage

## This round must do

1. freeze which exact pre-claim path may reach that adjacent inert slot
2. distinguish allowed locality reachability from forbidden ownership-bearing
   reachability expansions
3. keep locality access free of hidden queue ownership or execution routing

## Minimum deliverables

- one narrow runtime-owned locality-access surface
- focused tests
- one live script run showing the exact locality-access result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let marker locality access become hidden queue metadata
- do not introduce execution-bearing locality reachability before gate claim
- do not drift back to shell/product work
