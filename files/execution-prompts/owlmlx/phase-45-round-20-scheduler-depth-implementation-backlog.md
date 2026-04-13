# owlmlx Phase 45 Round 20: Scheduler-Depth Implementation Backlog

## Goal

Advance `cache_scheduler_depth` after the active-path scheduler floor has
already been frozen exact.

## Dominant gap

`cache_scheduler_depth`

## Current frozen truth

- `owlmlx.cache_counter_feasibility` is exact
- `owlmlx.cache_scheduler_turboquant_split` is exact
- `owlmlx.cache_scheduler_floor_gap` is exact
- the remaining cache branch is scheduler-grade first:
  - `queue_discipline = serial`
  - `max_concurrent = 1`
  - `scheduler_depth = serial_single_worker`
- TurboQuant remains exact but secondary on this branch

## This round must do

1. freeze the scheduler implementation backlog as a runtime-owned surface
2. separate:
   - already-owned scheduler truth
   - not-yet-implemented scheduler depth
3. keep the result conservative:
   - no fake continuous batching
   - no fake multi-worker scheduler
   - no parity inflation

## Minimum deliverables

- one new runtime-owned scheduler backlog/implementation-gap surface
- one operator script
- focused tests
- source-of-truth update

## Verification

- focused pytest for scheduler-floor / scheduler-backlog / customer-ledger composition
- one live script run showing the new scheduler backlog truth

## Hard rules

- work only in `owlmlx`
- do not drift back to specimen-first work
- do not inflate TurboQuant readiness
- do not claim scheduler implementation that does not exist
