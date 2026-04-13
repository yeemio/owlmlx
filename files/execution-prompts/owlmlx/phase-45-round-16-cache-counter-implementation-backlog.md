# owlmlx Phase 45 Round 16: Cache Counter Implementation Backlog

## Goal

Advance `cache_scheduler_depth` now that the remaining blocker has been frozen
as an exact counter-grade gap.

## Dominant Gap

`cache_scheduler_depth`

## Why This Round

`owlmlx` now has:

- active runtime-path cache observations
- a conservative cache closure rung
- a customer ledger that already points at `owlmlx.cache_counter_gap`

The remaining blocker is no longer "refresh cache evidence". It is exact:

- no runtime-owned `residency_counter`
- no runtime-owned `reuse_counter`
- no runtime-owned `eviction_counter`
- scheduler remains `serial_single_worker`
- TurboQuant is still below controlled validation

## Required Work

1. choose the lightest honest next closure step inside the active runtime path
2. prefer one real counter over fake substrate internals
3. keep scheduler depth and TurboQuant truth conservative
4. only move the dominant gap if a real cache counter or scheduler closure step lands

## Verification

- focused pytest for the new counter/scheduler closure step
- adjacent cache closure and customer-ledger tests
- script smokes for the updated cache counter gap and customer ledger
- source-of-truth update reflecting the new exact cache closure step

## Hard Rules

- work only inside `owlmlx`
- do not invent cache counters the runtime does not actually own
- do not inflate TurboQuant readiness
- do not change the supported-host heavy-weight blocker
