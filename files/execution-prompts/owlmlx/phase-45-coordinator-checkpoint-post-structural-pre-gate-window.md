# owlmlx Phase 45 Coordinator Checkpoint: Post-Structural Pre-Gate Window

## What completed

The supported-host branch remains frozen exact on the current host:

- `supported_host_repeatability_visible` remains established on
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- the original Kimi heavy boundary remains frozen exactly at:
  - `122.0G > 116.0G`
  - `memory_budget_exceeded`

The cache branch has now been reopened honestly beyond the old structural
checkpoint:

- old preserved checkpoint:
  - `owlmlx.cache_structural_ingress_seam`
  - `seam_rung = structural_ingress_seam_introduced`
- new active cache surface:
  - `owlmlx.cache_pre_gate_admission_window_seam`
  - `closure_level = pre_gate_admission_window_seam_exact`

## Current active cache truth

The current exact blocker is now:

- `selected_seam = bounded_pre_gate_admission_hook`
- `selected_seam.status = bounded_hook_present_but_no_request_aggregation_window`

Meaning:

- one bounded pre-gate hook already exists before whole-request gate claim
- that hook is runtime-owned
- it remains bounded to immutable metadata, observational ticket reservation,
  and bounded pre-claim bookkeeping
- it still does **not** form a request-aggregation/cohort window

Frozen secondary truth remains:

- `single_request_per_child_exchange_blocks_aggregated_dispatch`
- `stream_session_holds_gate_until_completion`
- `turboquant_preconditions = preconditions_exact`

## What did not change

This does **not** claim:

- request aggregation support
- continuous batching support
- cache parity
- child exchange parallelism
- stream-path rewrite
- customer-ready runtime
- replacement-ready runtime

## Why a new coordinator decision is needed

The next step is no longer another useful truth-only cache decomposition round.

The next step is implementation-class:

- either authorize work that turns the existing bounded hook into a real
  request-aggregation/cohort window
- or freeze cache at this post-structural exact blocker and stop here

## Decision required

Choose one of:

1. Authorize one narrow runtime round to turn the existing bounded pre-gate
   hook into a true cohort/request-aggregation window while preserving:
   - `max_concurrent_1_after_gate_claim`
   - `ticketed_fifo_after_gate_claim`
   - `serial_safety_validated_only_after_gate_claim`
2. Freeze cache at `pre_gate_admission_window_seam_exact` and hand control
   back to a different dominant branch later

## Recommendation

Take a fresh coordinator choice here.

The blocker is now exact enough that the next move is no longer "find the
blocker"; it is "authorize or defer the next structural runtime widening."
