# owlmlx Phase 45 Round 49: Pre-Claim Admission-Carrier Construction

## Goal

Advance `cache_scheduler_depth` after pre-claim marker reclaim-reset exactness
is already frozen.

## Current frozen truth

- reclaim resets the adjacent marker slot back to a fully empty inert state
- no prior request history or reclaim reason remains visible after reclaim
- later staged requests may reuse that locality only after a clean inert reset

## This round must do

1. freeze whether any bounded admission-carrier can exist before gate claim
2. distinguish allowed inert carrier construction from forbidden ownership- or
   execution-bearing construction
3. keep any future carrier subordinate to the already-frozen post-claim safety
   invariants

## Minimum deliverables

- one narrow runtime-owned admission-carrier surface
- focused tests
- one live script run showing the exact admission-carrier result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not turn pre-claim carrier construction into queue ownership or execution
  entitlement
- do not reintroduce history-bearing state into a reclaimed marker slot
- do not drift back to shell/product work
