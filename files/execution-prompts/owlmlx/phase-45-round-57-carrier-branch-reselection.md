# owlmlx Phase 45 Round 57: Admission-Carrier Branch Reselection

## Goal

Advance `cache_scheduler_depth` after pre-claim admission-carrier reclaim-reset
exactness is already frozen.

## Current frozen truth

- reclaim resets the bounded inert pre-claim carrier back to a fully empty
  inert state before any later reuse
- no prior request history or execution-bearing residue remains visible after
  reclaim
- later staged requests may reuse adjacent locality only after that clean
  empty reset

## This round must do

1. decide whether the admission-carrier sub-branch is now complete enough for
   honest branch reselection
2. if not, freeze the single next residual carrier subgap exactly
3. keep already-frozen post-claim serial safety invariants unchanged

## Minimum deliverables

- one narrow runtime-owned branch-reselection or residual-subgap surface
- focused tests
- one live script run showing the new exact result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not regress any already-frozen ingress exactness
- do not inflate branch reselection into closure or parity claims
