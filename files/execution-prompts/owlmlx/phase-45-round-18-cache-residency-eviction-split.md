# owlmlx Phase 45 Round 18: Cache Residency/Eviction Split

## Goal

Advance `cache_scheduler_depth` after the active runtime path has already
landed one honest `reuse_counter`.

## Dominant Gap

`cache_scheduler_depth`

## Why This Round

`owlmlx` now has:

- active runtime-path repeated-serving observations
- one real runtime-owned `reuse_counter`
- an exact cache counter gap that is no longer observation-grade

The remaining cache blocker is now narrower and cleaner:

- `residency_counter` is still absent
- `eviction_counter` is still absent
- scheduler depth remains `serial_single_worker`
- TurboQuant is still below controlled validation

This means the next honest question is:

- can `residency_counter` or `eviction_counter` be owned by the current
  runtime path without faking substrate internals
- or should cache now split into
  - remaining counter boundary
  - scheduler-depth boundary

## Required Work

1. inspect the active runtime path for an honest `residency_counter`
2. inspect whether `eviction_counter` is non-owned on the current substrate
3. if neither can be added honestly, freeze that exact boundary
4. if that boundary is exact, split the next closure step toward scheduler
   depth or TurboQuant preconditions

## Verification

- focused pytest for updated cache counter gap / closure / customer ledger
- adjacent subprocess backend tests if observations change
- script smokes for cache counter gap and customer ledger
- truth docs updated so the remaining cache blocker is narrower than today

## Hard Rules

- work only inside `owlmlx`
- do not invent cache residency or eviction semantics that the runtime does not own
- do not conflate persistent-child reuse with substrate cache residency
- do not change the supported-host heavy-weight blocker
