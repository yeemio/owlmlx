# owlmlx Phase 45: Stream-Hold Dependency Exactness

> Status: authoritative
> Updated: 2026-04-17
> Scope: runtime-only stream-hold seam after non-stream cohort handoff is visible

## 1. Purpose

Freeze the next exact stream dependency once:

- a bounded pre-gate request-aggregation/cohort window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the non-stream main path already hands that bounded cohort into one
  aggregated child exchange

The question is no longer whether stream work exists at all.

The question is:

- does `owlmlx` still hold the claimed gate through whole-session consumer
  completion, or has that dependency already narrowed to the backend stream
  iterator itself

## 2. Owned Contract

`owlmlx/cache_stream_hold_dependency_exactness.py` now owns:

- `build_cache_stream_hold_dependency_exactness(...)`
- `cache_stream_hold_dependency_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_stream_hold_dependency_exactness.py`

Contract:

- `surface = "owlmlx.cache_stream_hold_dependency_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `stream_hold`
- `next_active_dependency`
- `preserved_non_stream_handoff`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = stream_hold_dependency_exact`
- `summary.verdict = stream_hold_dependency_narrowed`
- `stream_hold.hold_status = stream_gate_release_decoupled_from_consumer_completion_visible`
- `stream_hold.gate_release_boundary = backend_stream_iterator_completion_before_consumer_drain`

The next active dependency is now:

- `next_active_dependency.dependency = stream_backend_iterator_completion_dependency`
- `next_active_dependency.status = stream_backend_iterator_holds_gate_until_completion`

Preserved non-stream truth remains:

- `preserved_non_stream_handoff.status = cohort_handed_off_to_aggregated_child_exchange_visible`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- the non-stream path already reached one aggregated child exchange
- but stream sessions still looked like they held the claimed gate through
  outer session completion

Now `owlmlx` can say something narrower:

- stream gate release no longer waits for the consumer to drain the whole
  session
- once the backend stream iterator completes, the claimed gate is released
- post-claim serial invariants remain intact:
  - `max_concurrent = 1`
  - `ticketed_fifo`
  - serial safety validated only after claim

## 5. What This Does Not Claim

It does not claim:

- stream interleaving exists
- continuous batching exists
- cache parity exists

It only claims that the stream seam is now narrower than whole-session
consumer completion and that the remaining exact hold sits at backend iterator
completion.

## 6. Next Closure Step

The next coordinator choice is no longer whether stream hold exists at all.

The next coordinator choice is whether `owlmlx` can narrow beyond:

- `stream_backend_iterator_completion_dependency`

without breaking:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
