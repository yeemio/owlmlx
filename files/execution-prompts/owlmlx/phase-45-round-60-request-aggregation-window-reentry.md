# owlmlx Phase 45 Round 60: Request-Aggregation-Window Reentry

## Goal

Advance `cache_scheduler_depth` after continuous-batching branch reduction is
already frozen.

## Current frozen truth

- scheduler depth remains the active cache branch
- `continuous_batching` remains the selected scheduler sub-branch
- `request_aggregation_window` is now the selected exact reduction target
- TurboQuant stays exact-but-secondary

## This round must do

1. re-enter the request-aggregation-window chain honestly
2. keep shared-prefill and interleaved-decode secondary
3. preserve already-frozen carrier-local and post-claim safety truth

## Minimum deliverables

- one narrow runtime-owned request-aggregation reentry surface
- focused tests
- one live script run showing the exact result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not reopen carrier-local exactness
- do not inflate request-aggregation reentry into continuous-batching closure or parity
