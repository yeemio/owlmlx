# owlmlx Phase 45 Round 23: Scheduler Backlog Branch Selection

## Goal

Select the next exact scheduler-implementation branch after the serial
ticketed FIFO queue policy is already frozen on the active cache path.

## Current frozen truth

- `owlmlx.cache_scheduler_implementation_backlog` is exact
- owned scheduler truth now includes:
  - `queue_discipline_serial`
  - `max_concurrent_1`
  - `generation_gate_wait_counters_visible`
  - `ticketed_fifo_queue_policy_visible`
- remaining scheduler backlog has narrowed to:
  - `continuous_batching`
  - `multi_worker_scheduler_depth`
- `owlmlx.dominant_gap_reselection` keeps the dominant gap on
  `cache_scheduler_depth`
- governance remains `policy_gap_exact`
- heavy-weight repeatability remains externally blocked on this host

## This round must do

1. split the remaining scheduler implementation backlog into the next exact
   locally reducible branch
2. decide whether the next scheduler work is:
   - `continuous_batching`
   - `multi_worker_scheduler_depth`
   - or an exact safety/feasibility blocker that keeps one branch secondary
3. freeze that decision as runtime-owned truth

## Minimum deliverables

- one narrow scheduler-branch selection surface or equivalent exact freeze
- focused tests
- one live script run showing the selected scheduler subgap
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim continuous batching exists unless runtime-owned proof actually moves
- do not claim multi-worker serving is safe on the current path unless the concurrency boundary is honestly revalidated
- do not reopen governance or specimen-first work unless the new scheduler branch proves blocked by an exact external dependency
