# owlmlx Phase 45 Round 15: Cache Evidence Refresh Against Active Runtime Observations

## Goal

Advance `cache_scheduler_depth` by refreshing the cache closure surfaces against
the stronger active-runtime observation harness that already exists.

## Dominant Gap

`cache_scheduler_depth`

## Why This Round

`owlmlx` now has:

- cache scheduler status
- cache residency evidence
- cache repeatability evidence
- TurboQuant readiness
- cache closure rung
- active runtime-path cache observations through persistent-child reuse

The current customer/runtime truth still underweights that stronger cache path.
The next reduction step is to absorb the active runtime observations more
directly and keep the remaining cache blocker exact.

## Required Work

1. refresh the cache closure/evidence path against the runtime observation harness
2. keep direct counter absence explicit
3. only move the dominant gap again if the refreshed cache truth really justifies it

## Verification

- focused pytest for refreshed cache evidence/closure contracts
- adjacent cache and customer-ledger tests
- script smokes for the refreshed cache closure path and customer ledger
- source-of-truth update reflecting the refreshed cache dominant gap

## Hard Rules

- work only inside `owlmlx`
- do not invent reuse/eviction counters that do not exist
- do not inflate TurboQuant readiness
- keep supported-host heavy-weight blocker unchanged unless runtime truth really moved
