# owlmlx Phase 45 Round 21: TurboQuant Preconditions Exactness

## Goal

Advance `cache_scheduler_depth` after the scheduler implementation backlog has
already been frozen exact on the active path.

## Dominant gap

`cache_scheduler_depth`

## Current frozen truth

- `owlmlx.cache_scheduler_implementation_backlog` is exact
- the remaining scheduler-grade work is explicit:
  - `continuous_batching`
  - `multi_worker_scheduler_depth`
  - `deeper_queue_policy`
- TurboQuant still remains secondary but exact on this branch:
  - current status is still `safety_blocked`

## This round must do

1. freeze TurboQuant preconditions as an exact remaining blocker on the cache branch
2. keep scheduler implementation backlog and TurboQuant exactness separate
3. avoid any readiness inflation beyond runtime-owned proof

## Minimum deliverables

- one runtime-owned TurboQuant preconditions exactness surface or equivalent narrowing of the existing readiness surface
- one operator script
- focused tests
- source-of-truth update

## Verification

- focused pytest for TurboQuant/cache/customer-ledger composition
- one live script run showing the exact TurboQuant-preconditions truth

## Hard rules

- work only in `owlmlx`
- do not regress scheduler backlog exactness
- do not claim TurboQuant is ready for controlled validation unless runtime-owned proof actually moves
- do not drift back to specimen-first work
