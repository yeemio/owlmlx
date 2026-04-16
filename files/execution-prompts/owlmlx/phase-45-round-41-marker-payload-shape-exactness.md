# owlmlx Phase 45 Round 41: Marker Payload-Shape Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim marker immutability is already
exact.

## Current frozen truth

- before whole-request gate claim, marker state may change only by clear-only
  semantics
- no pre-claim path may rewrite payload, mutate priority, create queue
  membership, or attach child/stream/execution state through marker state

## This round must do

1. freeze whether any marker payload fields exist at all before gate claim
2. distinguish allowed presence/absence semantics from forbidden payload shape
   expansions
3. keep marker payload shape free of hidden queue ownership or execution
   routing

## Minimum deliverables

- one narrow runtime-owned payload-shape surface
- focused tests
- one live script run showing the exact payload-shape result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let pre-claim marker payload become hidden queue metadata
- do not introduce execution-bearing marker shape before gate claim
- do not drift back to shell/product work
