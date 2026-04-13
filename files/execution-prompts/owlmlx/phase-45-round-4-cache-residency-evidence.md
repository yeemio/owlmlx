# owlmlx Phase 45 Round 4: Cache Residency/Reuse Evidence

> Status: archived execution prompt
> Updated: 2026-04-13

## Goal

Advance `cache_scheduler_depth` beyond pure status truth by adding one
runtime-owned evidence surface for current cache residency/reuse behavior.

## Dominant Gap

`cache_scheduler_depth`

`owlmlx` now already has:

- cache truth contract
- serialized scheduler truth
- runtime-owned cache/scheduler status

But it still lacks runtime-owned evidence for:

- whether cache state actually persists across runtime activity
- whether the runtime can expose any honest reuse/residency signal today

## Required Outcome

Create one runtime-owned evidence surface that:

1. stays inside `owlmlx`
2. exposes current cache residency/reuse evidence honestly
3. does not pretend paged cache or deep scheduler closure already exist
4. gives the next blocked reason if evidence is still too shallow

## Hard Rules

1. Stay inside `owlmlx`.
2. Do not claim cache parity from config visibility alone.
3. Do not move into shell/dashboard/operator UX work.
4. Prefer narrow honest evidence over ambitious fake cache depth.
