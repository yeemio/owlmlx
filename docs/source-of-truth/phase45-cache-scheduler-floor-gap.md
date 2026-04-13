# owlmlx Phase 45: Cache Scheduler Floor Gap

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only scheduler-floor truth inside the cache closure line

## 1. Purpose

This document freezes the current scheduler branch of `cache_scheduler_depth`
after cache counter ownership and the scheduler/TurboQuant split are already exact.

The question it answers is:

**What is the exact scheduler-grade floor on the current active path, and what
cache work remains after the split is clean?**

## 2. Owned Contract

`owlmlx/cache_scheduler_floor_gap.py` now owns:

- `build_cache_scheduler_floor_gap(...)`
- `cache_scheduler_floor_gap_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_scheduler_floor_gap.py`

Contract:

- `surface = "owlmlx.cache_scheduler_floor_gap"`
- `version = "phase45"`

Stable sections:

- `summary`
- `scheduler_floor`
- `next_step`

## 3. Current Honest Result

Current live result from the runtime-owned harness is:

- `summary.floor_rung = "serial_floor_exact"`
- `scheduler_floor.queue_discipline = "serial"`
- `scheduler_floor.max_concurrent = 1`
- `scheduler_floor.continuous_batching = false`
- `scheduler_floor.scheduler_depth = "serial_single_worker"`

The remaining scheduler blocker is now exact:

- queue discipline stays serial
- `max_concurrent` stays `1`
- no deeper scheduler behavior is runtime-owned on this path yet

## 4. What This Changes

Before this round, the remaining cache closure was already split cleanly between:

- `scheduler_depth`
- `TurboQuant preconditions`

But the scheduler branch was still mixed into the split surface.

Now `owlmlx` owns one narrower answer:

- the active cache path is no longer blocked by counter ownership
- it is no longer blocked by split ambiguity
- it is now blocked by a scheduler-grade floor that is exact

## 5. What This Does Not Claim

It does not claim:

- deeper scheduler implementation exists
- continuous batching exists
- parity with `oMLX` / `vMLX`

It only claims:

- the active runtime path has a frozen serial scheduler floor
- further cache closure on this path is now scheduler-implementation work first
- TurboQuant remains exact but secondary on this branch
