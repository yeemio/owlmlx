# owlmlx Phase 45: Cohort-To-Child Handoff Exactness

> Status: authoritative
> Updated: 2026-04-16
> Scope: runtime-only main-path cohort-to-child handoff after child exchange widening

## 1. Purpose

Freeze the next exact request-aggregation dependency once:

- a bounded pre-gate request-aggregation/cohort window is already visible
- one non-stream child exchange already supports aggregated dispatch
- the remaining question is whether the main serving path really hands that
  bounded cohort into the aggregated child exchange

## 2. Owned Contract

`owlmlx/cache_cohort_to_child_exchange_handoff_exactness.py` now owns:

- `build_cache_cohort_to_child_exchange_handoff_exactness(...)`
- `cache_cohort_to_child_exchange_handoff_exactness_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_cohort_to_child_exchange_handoff_exactness.py`

Contract:

- `surface = "owlmlx.cache_cohort_to_child_exchange_handoff_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `handoff`
- `next_active_dependency`
- `preserved_secondary_stream`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = cohort_to_child_handoff_exact`
- `handoff.handoff_status = cohort_handed_off_to_aggregated_child_exchange_visible`
- `handoff.main_path_shape = bounded_pre_gate_cohort_reaches_single_aggregated_non_stream_child_exchange`

The next active dependency is now:

- `next_active_dependency.dependency = stream_session_holds_gate_until_completion`
- `next_active_dependency.status = stream_session_holds_gate_until_completion`

Preserved secondary truth remains:

- `turboquant_preconditions = preconditions_exact`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- one non-stream child exchange can already carry multiple requests
- but the main serving path still does not hand off the bounded pre-gate cohort
  into that aggregated child exchange

Now `owlmlx` can say something narrower:

- the non-stream main serving path now hands a bounded pre-gate cohort into one
  aggregated child exchange
- post-claim serial invariants remain intact
- child exchange capability is no longer the active request-aggregation seam
- stream-session hold is now the next active dependency

## 5. What This Does Not Claim

It does not claim:

- stream release or stream interleaving exists
- continuous batching exists
- cache parity exists

It only freezes that the non-stream main path has crossed the cohort-to-child
handoff seam and that stream-session hold is now the next exact dependency.

## 6. Next Closure Step

The next coordinator choice is no longer whether cohort handoff may move.

The next coordinator choice is whether to authorize one narrower runtime round
on:

- `stream_session_holds_gate_until_completion`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
