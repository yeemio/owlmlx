# owlmlx Phase 45 Coordinator Checkpoint: Child-Exchange Aggregated Dispatch Visible

## What completed

The supported-host branch remains frozen exact on the current host:

- `supported_host_repeatability_visible` remains established on
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- the original Kimi heavy boundary remains frozen exactly at:
  - `122.0G > 116.0G`
  - `memory_budget_exceeded`

The authorized child-exchange round has now completed:

- the old active cache seam:
  - `selected_seam = child_exchange_aggregated_dispatch_dependency`
  - `selected_seam.status = single_request_per_child_exchange_blocks_aggregated_dispatch`
- has now been advanced into visible non-stream aggregated child exchange

## Current active cache truth

The current live result is now:

- coordinator verdict:
  - `child_exchange_aggregated_dispatch_visible`
- request-aggregation window truth:
  - `owlmlx.cache_request_aggregation_window_exactness`
  - `ingress_window_status = bounded_pre_gate_admission_window_present`
  - `admission_boundary_status = cohort_forms_before_generation_gate_claim`
  - `child_dependency_status = aggregated_non_stream_child_exchange_visible`
- child-exchange exactness:
  - `owlmlx.cache_child_exchange_aggregated_dispatch_exactness`
  - `child_exchange_status = aggregated_non_stream_child_exchange_visible`
  - `exchange_shape = single_child_exchange_carries_multiple_non_stream_requests`
- active request-aggregation seam:
  - `owlmlx.cache_request_aggregation_active_seam`
  - `seam_rung = aggregation_active_seam_exact`
  - `selected_seam = cohort_to_child_exchange_handoff_dependency`
  - `selected_seam.status =
    pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange`

Preserved secondary truth remains:

- `stream_session_holds_gate_until_completion`
- `turboquant_preconditions = preconditions_exact`

## What did not change

This does **not** claim:

- mainline cohort handoff already exists
- stream rewrite or stream interleaving
- continuous batching
- cache parity
- replacement-ready runtime
- customer-ready runtime

The preserved post-claim invariants remain frozen:

- `max_concurrent_1_after_gate_claim`
- `ticketed_fifo_after_gate_claim`
- `serial_safety_validated_only_after_gate_claim`

## Why a new coordinator decision is needed

The authorized round was only:

- widen child exchange beyond one-request-per-exchange without touching stream
  or post-claim serial invariants

That work is now complete.

The next step would be a different dependency class:

- cohort-to-child handoff dependency work

That is outside the current authorization boundary and must not be auto-opened.

## Decision required

Choose one of:

1. Authorize one narrow runtime round on
   `cohort_to_child_exchange_handoff_dependency`, while keeping:
   - stream hold secondary
   - post-claim serial invariants frozen
   - no stream rewrite
   - no continuous batching / parity claims
2. Freeze cache at `child_exchange_aggregated_dispatch_visible` and stop here

## Recommendation

Take a fresh coordinator choice here.

The child-exchange question is no longer the active blocker. The next exact
question is whether the bounded pre-gate cohort may be handed off into the now
visible aggregated child exchange without breaking the frozen serial boundary.
