# owlmlx Phase 45 Round 31: Pre-Claim Staging Seam Exactness

## Goal

Advance `cache_scheduler_depth` after the pre-claim admission contract is
already exact.

## Current frozen truth

- `owlmlx.cache_pre_claim_admission_contract` is exact
- the only allowable future pre-claim seam is bounded metadata/ticket staging
  before whole-request gate claim
- forbidden pre-claim actions:
  - `no_gate_claim_from_pre_claim_seam`
  - `no_child_exchange_from_pre_claim_seam`
  - `no_stream_start_from_pre_claim_seam`
  - `no_model_execution_from_pre_claim_seam`

## This round must do

1. freeze the exact bounded staging seam, if any, that can exist before
   whole-request gate claim
2. distinguish:
   - exact metadata/ticket work that may be staged pre-claim
   - exact work that must remain outside pre-claim staging
3. keep child exchange, stream start, and model execution outside the seam
   unless runtime truth actually changes

## Minimum deliverables

- one narrow runtime-owned pre-claim staging-seam surface or equivalent exact
  freeze
- focused tests
- one live script run showing the exact staging-seam result
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not claim request aggregation exists unless runtime-owned proof actually
  moves
- do not reopen multi-worker depth unless concurrency truth changes honestly
- do not drift back to shell/product work
