# owlmlx Phase 45 Round 25: Batching Mechanism Subgap

## Goal

Advance `cache_scheduler_depth` after continuous batching is already frozen as
an exact feasibility blocker on the active path.

## Current frozen truth

- `owlmlx.cache_continuous_batching_feasibility` is exact
- the active path still has:
  - `generation_gate_mode = serial_ticketed_fifo_whole_request`
  - `child_exchange_mode = single_request_per_child_exchange`
  - `stream_holds_full_session = true`
- missing batching mechanisms are explicit:
  - `request_aggregation_window`
  - `shared_prefill_batch_step`
  - `interleaved_decode_scheduler`
- `multi_worker_scheduler_depth` remains secondary and safety-bound

## This round must do

1. split the continuous-batching blocker into the next exact mechanism subgap
2. decide which missing batching mechanism is the next locally reducible one
3. keep multi-worker depth secondary unless concurrency truth actually changes

## Minimum deliverables

- one narrow runtime-owned batching-mechanism selection surface or equivalent exact freeze
- focused tests
- one live script run showing the selected mechanism subgap
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim batching exists unless runtime-owned proof actually moves
- do not reopen multi-worker depth unless concurrency safety is revalidated honestly
- do not drift back to shell/product work
