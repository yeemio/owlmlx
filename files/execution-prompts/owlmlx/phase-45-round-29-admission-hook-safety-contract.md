# owlmlx Phase 45 Round 29: Admission Hook Safety Contract

## Goal

Advance `cache_scheduler_depth` after the admission-hook blocker is already
frozen exact.

## Current frozen truth

- `owlmlx.cache_pre_gate_admission_hook_exactness` is exact
- current hook result:
  - `no_bounded_hook_before_gate_claim`
- current owned boundary:
  - `whole_request_gate_claim_is_first_runtime_owned_boundary`
- preserved safety invariants:
  - `max_concurrent_1_after_gate_claim`
  - `ticketed_fifo_after_gate_claim`
  - `serial_safety_validated_only_after_gate_claim`

## This round must do

1. freeze the exact safety contract any future pre-gate admission hook must
   preserve
2. distinguish:
   - invariants that must remain post-claim
   - boundaries that a hook is not allowed to bypass
3. keep child dispatch and stream release secondary unless runtime truth
   actually changes

## Minimum deliverables

- one narrow runtime-owned admission-hook safety surface or equivalent exact
  freeze
- focused tests
- one live script run showing the exact safety-contract result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim batching exists unless runtime-owned proof actually moves
- do not reopen multi-worker depth unless concurrency truth changes honestly
- do not drift back to shell/product work
