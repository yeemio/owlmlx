# owlmlx Phase 45 Round 53: Admission-Carrier Locality-Access Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim admission-carrier locality
exactness is already frozen.

## Current frozen truth

- the bounded inert pre-claim record may live only in single-request staged
  locality adjacent to metadata/ticket state before gate claim
- it may not occupy queue, scheduler, child/stream, or execution-owned
  locality before claim

## This round must do

1. freeze which exact pre-claim paths may reach that bounded inert record
   before gate claim
2. distinguish allowed inert locality access from forbidden queue-, scheduler-,
   backend-, stream-, or execution-bearing access
3. keep locality-access exactness subordinate to the already-frozen post-claim
   safety invariants

## Minimum deliverables

- one narrow runtime-owned admission-carrier locality-access surface
- focused tests
- one live script run showing the exact locality-access result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let locality access reintroduce queue ownership or execution state
- do not drift back to shell/product work
