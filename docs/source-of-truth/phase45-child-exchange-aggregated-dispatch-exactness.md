# owlmlx Phase 45: Child-Exchange Aggregated-Dispatch Exactness

> Status: authoritative
> Updated: 2026-04-16
> Scope: runtime-only child-exchange dependency after pre-gate window entry

## 1. Purpose

Freeze the next exact request-aggregation dependency once:

- a bounded pre-gate request-aggregation/cohort window is already visible
- ingress is no longer the active blocker
- `owlmlx` still must not widen into stream rewrite or continuous batching

## 2. Owned Contract

`owlmlx/cache_child_exchange_aggregated_dispatch_exactness.py` now owns:

- `build_cache_child_exchange_aggregated_dispatch_exactness(...)`
- `cache_child_exchange_aggregated_dispatch_exactness_to_dict(...)`

Operator entries:

- `scripts/runtime_cache_child_exchange_aggregated_dispatch_exactness.py`
- `owlmlx/cache_child_exchange_aggregated_dispatch_harness.py`

Contract:

- `surface = "owlmlx.cache_child_exchange_aggregated_dispatch_exactness"`
- `version = "phase45"`

Stable sections:

- `summary`
- `child_exchange`
- `next_active_dependency`
- `preserved_secondary_stream`

## 3. Current Honest Result

The current live result is:

- `summary.exactness_rung = child_exchange_dependency_exact`
- `child_exchange.child_exchange_status = aggregated_non_stream_child_exchange_visible`
- `child_exchange.exchange_shape = single_child_exchange_carries_multiple_non_stream_requests`

The next active dependency is now:

- `next_active_dependency.dependency = cohort_to_child_exchange_handoff_dependency`
- `next_active_dependency.status = pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange`

Preserved secondary truth remains:

- `stream_session_holds_gate_until_completion`

## 4. What This Changes

Before this round, `owlmlx` could only say:

- child exchange remained one-request-per-exchange
- aggregated dispatch was blocked directly at the child protocol seam

Now `owlmlx` can say something narrower:

- one non-stream child exchange can already carry multiple requests
- child exchange itself is no longer the exact one-request-per-exchange blocker
- the next active blocker is the missing handoff from the bounded pre-gate
  cohort into that aggregated child exchange on the main serving path
- stream hold remains real, but secondary

## 5. What This Does Not Claim

It does not claim:

- the main serving path already hands off cohorts into aggregated child exchange
- stream release or stream interleaving exists
- continuous batching exists
- cache parity exists

It only freezes that child exchange has widened one layer, while the next exact
blocker is now the cohort-to-child handoff seam.

## 6. Next Closure Step

The next coordinator choice is no longer whether child exchange may widen.

The next coordinator choice is whether to authorize one narrower runtime round
on:

- `cohort_to_child_exchange_handoff_dependency`

while preserving:

- `max_concurrent = 1` after whole-request gate claim
- ticketed FIFO after claim
- serial safety validated only after gate claim
- stream hold as secondary truth
