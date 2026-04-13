# owlmlx Phase 45 Round 17: Cache Residency/Eviction Feasibility Freeze

## Goal

Advance `cache_scheduler_depth` after one real runtime-owned `reuse_counter`
has become visible on the active runtime path.

## Dominant Gap

`cache_scheduler_depth`

## Why This Round

`owlmlx` now has:

- active runtime-path repeated-serving observations
- one real runtime-owned `reuse_counter`
- a frozen exact cache counter gap

The remaining cache blocker is narrower now:

- `residency_counter` is still absent
- `eviction_counter` is still absent
- scheduler depth remains `serial_single_worker`
- TurboQuant is still below controlled validation

The next honest step is not another evidence refresh. It is to decide whether
`residency_counter` and `eviction_counter` are locally implementable on the
current runtime path, or whether they must be frozen as not-runtime-owned on
this substrate boundary.

## Required Work

1. inspect the active runtime path and decide whether `residency_counter` can
   be added honestly without inventing substrate internals
2. inspect whether `eviction_counter` is locally implementable on the current
   runtime path or must be frozen as absent
3. if one of them is honestly implementable, land it with tests and scripts
4. otherwise freeze the exact non-owned boundary and narrow the next closure
   step to scheduler depth or TurboQuant preconditions

## Verification

- focused pytest for the updated cache counter gap / repeatability / closure
- adjacent subprocess backend tests if runtime observations change
- script smokes for cache counter gap and customer ledger
- truth docs updated to reflect the narrower remaining cache blocker

## Hard Rules

- work only inside `owlmlx`
- do not invent cache residency/eviction semantics that the runtime does not actually own
- do not conflate process reuse with substrate KV eviction
- do not change the supported-host heavy-weight blocker
