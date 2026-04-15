# owlmlx Phase 45: Cache Continuous-Batching Feasibility

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only continuous-batching feasibility on the active cache path

## 1. Purpose

This document freezes a narrower scheduler truth:

**Is continuous batching merely absent on the active cache path, or is there
already an exact feasibility blocker that explains why it is not a small
follow-up?**

It exists so the loop can stop treating continuous batching like a generic
backlog label once the scheduler branch itself is already exact.

## 2. Owned Contract

`owlmlx/cache_continuous_batching_feasibility.py` now owns:

- `build_cache_continuous_batching_feasibility(...)`
- `cache_continuous_batching_feasibility_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_continuous_batching_feasibility.py`

Contract:

- `surface = "owlmlx.cache_continuous_batching_feasibility"`
- `version = "phase45"`

Stable sections:

- `summary`
- `runtime_path`
- `missing_batching_mechanisms`

## 3. Current Honest Result

Current live harness result is:

- `summary.feasibility_rung = "feasibility_blocker_exact"`
- runtime path:
  - `generation_gate_mode = "serial_ticketed_fifo_whole_request"`
  - `child_exchange_mode = "single_request_per_child_exchange"`
  - `stream_holds_full_session = true`
- missing batching mechanisms:
  - `request_aggregation_window`
  - `shared_prefill_batch_step`
  - `interleaved_decode_scheduler`

## 4. Why This Is Stronger Than “Absent”

The active path is now exact enough to say more than “continuous batching has
not been implemented.”

The blocker is structural on the current path:

- the gate still serializes whole requests
- the subprocess child protocol still serves one request per exchange
- streaming still occupies the full gate session for the lifetime of the stream

That means continuous batching is not a small flag flip or a shallow follow-up
to queue-policy truth. It needs an explicit batching mechanism.

## 5. What This Does Not Claim

It does not claim:

- continuous batching exists
- continuous batching is close to shipping
- multi-worker depth is safe

It only claims:

- the next scheduler branch has been narrowed beyond branch selection
- the active path now has an exact feasibility blocker for continuous batching
- multi-worker depth remains secondary until concurrency safety is revalidated
