# owlmlx Phase 45 Round 59: Continuous-Batching Branch Reduction

## Goal

Advance `cache_scheduler_depth` after scheduler-vs-TurboQuant branch
reselection is already frozen.

## Current frozen truth

- scheduler depth is the selected next branch on the current path
- the selected scheduler sub-branch remains `continuous_batching`
- TurboQuant stays exact-but-secondary on the same path

## This round must do

1. reduce the selected scheduler-depth branch honestly
2. keep TurboQuant exact-but-secondary
3. preserve already-frozen ingress and post-claim serial safety invariants

## Minimum deliverables

- one narrow runtime-owned continuous-batching branch surface
- focused tests
- one live script run showing the exact result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not reopen carrier-local exactness
- do not inflate scheduler branch reduction into scheduler closure or parity
