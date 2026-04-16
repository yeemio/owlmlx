# owlmlx Phase 45 Round 44: Marker Storage-Locality Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim marker encoding carrier is
already exact.

## Current frozen truth

- before whole-request gate claim marker presence may live only in one inert
  boolean slot
- that slot may not encode queue identity, ticket identity, child payload, or
  stream/execution handles

## This round must do

1. freeze where that inert boolean slot is stored relative to staged
   metadata/ticket units
2. distinguish allowed storage locality from forbidden ownership-bearing
   locality expansions
3. keep storage locality free of hidden queue ownership or execution routing

## Minimum deliverables

- one narrow runtime-owned storage-locality surface
- focused tests
- one live script run showing the exact storage-locality result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let marker storage locality become hidden queue metadata
- do not introduce execution-bearing storage locality before gate claim
- do not drift back to shell/product work
