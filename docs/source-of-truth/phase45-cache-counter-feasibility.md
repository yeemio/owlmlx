# owlmlx Phase 45: Cache Counter Feasibility

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only ownership boundary for cache counters on the active path

## 1. Purpose

This document freezes a narrower question than `cache_counter_gap`:

**Which cache counters are actually runtime-owned on the current active path,
and which ones are not owned here at all?**

This matters because replacement-grade closure should not keep chasing fake
counter work once ownership has already been resolved.

## 2. Owned Contract

`owlmlx/cache_counter_feasibility.py` now owns:

- `build_cache_counter_feasibility(...)`
- `cache_counter_feasibility_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_counter_feasibility.py`

Contract:

- `surface = "owlmlx.cache_counter_feasibility"`
- `version = "phase45"`

Stable sections:

- `summary`
- `counter_ownership`
- `next_cache_subgap`

## 3. Current Honest Result

With the active runtime harness and one live `reuse_counter`, the current live
result is:

- `summary.feasibility_rung = "counter_ownership_exact"`

That means:

- `reuse_counter = "runtime_owned_visible"`
- `residency_counter = "not_runtime_owned_on_current_path"`
- `eviction_counter = "not_runtime_owned_on_current_path"`

The next cache closure step is therefore:

- `next_cache_subgap = "scheduler_depth"`

## 4. What This Changes

Before this round, cache still looked like an unresolved counter chase.

Now `owlmlx` owns a narrower answer:

- `reuse_counter` is already real on the current path
- `residency_counter` and `eviction_counter` should not keep being treated as
  locally missing implementation work on this path
- the remaining locally reducible cache work is now scheduler depth and
  TurboQuant preconditions

## 5. What This Does Not Claim

It does not claim:

- cache parity with `oMLX` / `vMLX`
- substrate-level residency truth
- substrate-level eviction truth
- stronger scheduler depth than `serial_single_worker`
- TurboQuant controlled validation

It only claims:

- counter ownership is now exact
- the next cache closure step has shifted away from fake counter work
