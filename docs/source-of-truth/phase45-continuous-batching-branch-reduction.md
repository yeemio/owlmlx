# Phase 45: Continuous-Batching Branch Reduction

> Status: frozen runtime truth
> Updated: 2026-04-16

## Surface

- `owlmlx.cache_continuous_batching_branch_reduction`

## Frozen Truth

Once scheduler depth is reselected as the active non-carrier cache branch, the
next honest scheduler reduction on the current path is:

- `continuous_batching`

Inside that branch, the next exact reduction target is:

- `request_aggregation_window`

The remaining scheduler mechanisms stay secondary:

- `shared_prefill_batch_step`
- `interleaved_decode_scheduler`

TurboQuant stays exact-but-secondary on the same path.

## Operator Entry

- `python3 scripts/runtime_cache_continuous_batching_branch_reduction.py --run-harness`

## Next Exact Question

After continuous-batching branch reduction is frozen, the next local cache
question is:

- how request-aggregation-window work re-enters the cache chain on the current
  path without reopening carrier-local exactness
