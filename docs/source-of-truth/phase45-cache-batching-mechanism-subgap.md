# owlmlx Phase 45: Cache Batching Mechanism Subgap

> Status: authoritative
> Updated: 2026-04-15
> Scope: runtime-only cache scheduler exactness on the active path

## 1. Purpose

Freeze the next exact batching-mechanism subgap after continuous batching is
already proven to be structurally blocked on the active path.

## 2. Owned Contract

`owlmlx/cache_batching_mechanism_subgap.py` now owns:

- `build_cache_batching_mechanism_subgap(...)`
- `cache_batching_mechanism_subgap_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_batching_mechanism_subgap.py`

Contract:

- `surface = "owlmlx.cache_batching_mechanism_subgap"`
- `version = "phase45"`

Stable sections:

- `summary`
- `selected_mechanism`
- `mechanism_statuses`

## 3. Current Honest Result

The active path still has:

- whole-request ticketed FIFO generation gating
- one-request-per-child exchange
- full-session stream hold during streaming

Given that runtime truth, the next exact batching subgap is:

- `request_aggregation_window = locally_reducible_first_blocker`

The remaining mechanisms are explicitly secondary:

- `shared_prefill_batch_step = blocked_by_missing_request_aggregation_window`
- `interleaved_decode_scheduler = blocked_by_missing_request_aggregation_window_and_full_session_stream_hold`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- continuous batching is exact-feasibility-blocked
- three missing mechanisms are known

Now `owlmlx` can say something stronger:

- the first mechanism subgap is not shared prefill
- the first mechanism subgap is not decode interleaving
- the first mechanism subgap is aggregate request admission before the current
  serial gate and child exchange boundary claim the session

That keeps the loop from diffusing into three parallel scheduler narratives.

## 5. What This Does Not Claim

It does not claim:

- request aggregation already exists
- shared prefill exists
- interleaved decode exists
- continuous batching is now close to done

It only claims that the next exact local mechanism is now frozen honestly.

## 6. Next Closure Step

The next exact cache round should freeze whether `request_aggregation_window`
is runtime-owned and locally implementable on the active path without
violating the validated serial safety boundary.
