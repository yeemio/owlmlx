# owlmlx Phase 45 Coordinator Checkpoint: Request Aggregation Window Visible

## What completed

The supported-host branch remains frozen exact on the current host:

- `supported_host_repeatability_visible` remains established on
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- the original Kimi heavy boundary remains frozen exactly at:
  - `122.0G > 116.0G`
  - `memory_budget_exceeded`

The authorized pre-gate widening round has now completed:

- the old preserved cache checkpoint:
  - `owlmlx.cache_pre_gate_admission_window_seam`
  - `selected_seam.status = bounded_hook_present_but_no_request_aggregation_window`
- has now been advanced into a live runtime-owned cohort window

## Current active cache truth

The current live result is now:

- coordinator verdict:
  - `request_aggregation_window_visible`
- direct ingress/window truth:
  - `owlmlx.cache_request_aggregation_window_exactness`
  - `ingress_window_status = bounded_pre_gate_admission_window_present`
  - `admission_boundary_status = cohort_forms_before_generation_gate_claim`
- active request-aggregation seam:
  - `owlmlx.cache_request_aggregation_active_seam`
  - `seam_rung = aggregation_active_seam_exact`
  - `selected_seam = child_exchange_aggregated_dispatch_dependency`
  - `selected_seam.status = single_request_per_child_exchange_blocks_aggregated_dispatch`

Preserved secondary truth remains:

- `stream_session_holds_gate_until_completion`
- `turboquant_preconditions = preconditions_exact`

## What did not change

This does **not** claim:

- aggregated child dispatch
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

- make the existing bounded pre-gate hook into a real request-aggregation /
  cohort window

That work is now complete.

The next step would be a different dependency class:

- child exchange aggregated-dispatch dependency work

That is outside the current authorization boundary and must not be auto-opened.

## Decision required

Choose one of:

1. Authorize one narrow runtime round on
   `child_exchange_aggregated_dispatch_dependency`, while keeping:
   - stream hold secondary
   - post-claim serial invariants frozen
   - no stream rewrite
   - no continuous batching / parity claims
2. Freeze cache at `request_aggregation_window_visible` and stop here

## Recommendation

Take a fresh coordinator choice here.

The ingress/window question is no longer the active blocker. The next exact
question is whether child exchange may be widened beyond one-request-per-
exchange without breaking the frozen serial boundary.
