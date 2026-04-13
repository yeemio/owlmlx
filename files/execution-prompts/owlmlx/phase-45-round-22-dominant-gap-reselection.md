# owlmlx Phase 45 Round 22: Dominant-Gap Reselection

## Goal

Re-evaluate the next locally reducible dominant gap after the cache branch now
has both:

- exact scheduler implementation backlog
- exact TurboQuant preconditions gap

## Current frozen truth

- `owlmlx.cache_scheduler_implementation_backlog` is exact
- `owlmlx.cache_turboquant_preconditions_gap` is exact
- `multi_model_lifecycle_governance` is already frozen to `policy_gap_exact`
- `host_stable_execution` and `heavy_weight_runtime_repeatability` remain exact external blockers on this host

## This round must do

1. compare the remaining locally reducible gaps without drifting back into narrative comparison
2. decide whether the next dominant gap remains:
   - `cache_scheduler_depth`
   - or shifts to `multi_model_lifecycle_governance`
   - or shifts to `customer_runtime_evidence`
3. freeze that reselection as runtime-owned truth or goal truth

## Minimum deliverables

- one narrow decision surface or equivalent exact reselection freeze
- focused tests
- source-of-truth update

## Hard rules

- work only in `owlmlx`
- do not reopen already exact cache sub-branches without new runtime-owned evidence
- do not inflate customer readiness
- do not drift back to specimen-first work
