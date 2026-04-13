# owlmlx Phase 45 Round 19: Cache Scheduler/TurboQuant Split

## Goal

Advance `cache_scheduler_depth` after cache counter ownership has already been
frozen exact on the active runtime path.

## Dominant Gap

`cache_scheduler_depth`

## Why This Round

`owlmlx` now has:

- one runtime-owned `reuse_counter`
- a frozen cache counter gap
- a frozen cache counter-feasibility boundary

That means the remaining cache work is no longer about counter ownership on
this path. The remaining cache closure work is now:

- scheduler depth beyond `serial_single_worker`
- TurboQuant preconditions above `safety_blocked`

## Required Work

1. inspect whether scheduler depth can move honestly on the current runtime
   path without inventing batching semantics
2. inspect whether TurboQuant can move above `safety_blocked` using current
   runtime-owned truth only
3. if neither can move honestly, freeze the exact split and narrow the next
   closure step again
4. if one can move honestly, land it with tests, scripts, and updated truth

## Verification

- focused pytest for updated cache scheduler / TurboQuant / customer-ledger
  surfaces
- adjacent cache tests if runtime truths move
- script smokes for cache counter feasibility and customer ledger
- truth docs updated so the next cache blocker is narrower than today

## Hard Rules

- work only inside `owlmlx`
- do not invent batching depth that the runtime does not own
- do not inflate TurboQuant readiness beyond runtime-owned proof
- do not change the supported-host heavy-weight blocker
