# owlmlx Phase 45 Round 27: Pre-Gate Cohort Window Feasibility

## Goal

Advance `cache_scheduler_depth` after request aggregation is already frozen as
an exact ingress/runtime blocker.

## Current frozen truth

- `owlmlx.cache_request_aggregation_window_exactness` is exact
- current ingress blocker:
  - `missing_pre_gate_admission_window`
- current boundary blocker:
  - `generation_gate_claims_session_before_cohort_formation`
- downstream dependencies remain secondary:
  - `single_request_per_child_exchange_blocks_aggregated_dispatch`
  - `stream_session_holds_gate_until_completion`

## This round must do

1. freeze whether a pre-gate cohort window is locally expressible as a
   runtime-owned mechanism on the active path
2. distinguish:
   - exact admission-window feasibility
   - exact serial-safety constraint that still limits it
3. keep aggregated child dispatch and stream release secondary unless runtime
   truth actually changes

## Minimum deliverables

- one narrow runtime-owned pre-gate cohort-window surface or equivalent exact
  freeze
- focused tests
- one live script run showing the exact cohort-window result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim batching exists unless runtime-owned proof actually moves
- do not reopen multi-worker depth unless concurrency truth changes honestly
- do not drift back to shell/product work
