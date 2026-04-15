# owlmlx Phase 45 Round 28: Pre-Gate Admission Hook Exactness

## Goal

Advance `cache_scheduler_depth` after the pre-gate cohort window has already
been frozen as boundary-exact.

## Current frozen truth

- `owlmlx.cache_pre_gate_cohort_window_feasibility` is exact
- current cohort-window result:
  - `not_runtime_owned_before_gate_entry`
- current boundary result:
  - `generation_gate_has_no_pre_admission_hook`
- current safety result:
  - `serial_safety_validated_only_after_whole_request_gate_claim`

## This round must do

1. freeze whether a bounded pre-gate admission hook is locally expressible
   without breaking the validated serial safety boundary
2. distinguish:
   - exact hook absence
   - exact safety invariants that must remain after gate claim
3. keep aggregated child dispatch and stream release secondary unless runtime
   truth actually changes

## Minimum deliverables

- one narrow runtime-owned admission-hook surface or equivalent exact freeze
- focused tests
- one live script run showing the exact admission-hook result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim batching exists unless runtime-owned proof actually moves
- do not reopen multi-worker depth unless concurrency truth changes honestly
- do not drift back to shell/product work
