# owlmlx Phase 45 Round 58: Scheduler-vs-TurboQuant Branch Reselection

## Goal

Advance `cache_scheduler_depth` after the admission-carrier branch has been
frozen as complete enough for honest reselection.

## Current frozen truth

- the admission-carrier exactness chain is complete on the current path
- no narrower residual carrier subgap remains open
- the next cache sub-branch moves back to scheduler-vs-TurboQuant reselection

## This round must do

1. decide which non-carrier cache branch is now the next honest reduction
   target
2. keep all already-frozen ingress invariants intact
3. avoid inflating reselection into cache closure or parity claims

## Minimum deliverables

- one narrow runtime-owned branch-reselection surface
- focused tests
- one live script run showing the exact result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not reopen carrier-local exactness questions unless the runtime truth
  forces it
- do not weaken post-claim serial safety invariants
