# owlmlx Phase 45 Round 30: Pre-Claim Admission Contract

## Goal

Advance `cache_scheduler_depth` after the admission-hook safety contract is
already exact.

## Current frozen truth

- `owlmlx.cache_admission_hook_safety_contract` is exact
- preserved post-claim invariants:
  - `max_concurrent_1_after_gate_claim`
  - `ticketed_fifo_after_gate_claim`
  - `serial_safety_validated_only_after_gate_claim`
- forbidden bypasses:
  - `no_bypass_of_whole_request_gate_claim`
  - `no_reordering_after_gate_claim`
  - `no_post_claim_parallel_generation`

## This round must do

1. freeze whether `owlmlx` can define any bounded pre-claim admission contract
   without violating the exact post-claim safety contract
2. distinguish:
   - exact pre-claim admission seam that might exist
   - exact post-claim boundaries it may not bypass
3. keep child dispatch and stream release secondary unless runtime truth
   actually changes

## Minimum deliverables

- one narrow runtime-owned pre-claim admission-contract surface or equivalent
  exact freeze
- focused tests
- one live script run showing the exact pre-claim contract result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim batching exists unless runtime-owned proof actually moves
- do not reopen multi-worker depth unless concurrency truth changes honestly
- do not drift back to shell/product work
