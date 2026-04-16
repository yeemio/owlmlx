# owlmlx Phase 45 Round 48: Marker Reclaim-Reset Exactness

## Goal

Advance `cache_scheduler_depth` after pre-claim marker locality-lifetime
coupling is already exact.

## Current frozen truth

- the isolated adjacent marker slot is coupled only to its own staged-request
  lifetime before whole-request gate claim
- reclaim may occur only by same-request pre-claim discard or same-request
  gate-claim expiry transition
- no cross-request slot reuse or retained ownership may emerge from that
  coupling

## This round must do

1. freeze the exact clean-state reset left in the adjacent inert slot after
   reclaim
2. distinguish allowed reset semantics from forbidden history-carrying reuse
3. keep reclaim/reset free of hidden queue ownership or execution-bearing
   transfer

## Minimum deliverables

- one narrow runtime-owned reclaim-reset surface
- focused tests
- one live script run showing the exact reclaim-reset result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not let reclaimed marker state carry queue ownership or execution history
- do not introduce cross-request reuse before exact inert reset is frozen
- do not drift back to shell/product work
