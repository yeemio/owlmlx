# Phase 45: Scheduler-vs-TurboQuant Branch Reselection

> Status: frozen runtime truth
> Updated: 2026-04-16

## Surface

- `owlmlx.cache_scheduler_turboquant_branch_reselection`

## Frozen Truth

Once the admission-carrier exactness chain is complete, the next non-carrier
cache branch can be reselected honestly:

- scheduler depth is the selected next branch on the current path
- the selected scheduler sub-branch remains `continuous_batching`
- TurboQuant stays exact-but-secondary on the same path

This does not claim scheduler closure. It only freezes which non-carrier cache
branch is now the next honest reduction target.

## Operator Entry

- `python3 scripts/runtime_cache_scheduler_turboquant_branch_reselection.py --run-harness`

## Next Exact Question

After scheduler-vs-TurboQuant branch reselection is frozen, the next local
cache question is:

- how the selected scheduler-depth branch should be reduced next without
  regressing already-frozen ingress invariants or inflating TurboQuant
