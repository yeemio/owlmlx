# owlmlx Phase 45: Cache Scheduler Branch Selection

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only selection of the next scheduler branch on the active cache path

## 1. Purpose

This document freezes the next exact scheduler branch once the active cache
path already has:

- exact scheduler implementation backlog
- explicit serial ticketed FIFO queue policy
- exact-but-secondary TurboQuant preconditions

The question it answers is:

**Which scheduler branch should `owlmlx` work next on the active path, and
which branch must stay secondary until safety is revalidated?**

## 2. Owned Contract

`owlmlx/cache_scheduler_branch_selection.py` now owns:

- `build_cache_scheduler_branch_selection(...)`
- `cache_scheduler_branch_selection_to_dict(...)`

Operator entry:

- `scripts/runtime_cache_scheduler_branch_selection.py`

Contract:

- `surface = "owlmlx.cache_scheduler_branch_selection"`
- `version = "phase45"`

Stable sections:

- `summary`
- `selected_branch`
- `secondary_branch`

## 3. Current Honest Result

Current live harness result is:

- `summary.selection_rung = "branch_selection_exact"`
- selected branch:
  - `continuous_batching`
  - `status = "locally_reducible_on_current_path"`
- secondary branch:
  - `multi_worker_scheduler_depth`
  - `status = "safety_revalidation_required"`

## 4. Why Continuous Batching Wins First

The current path still has:

- validated concurrency boundary = `1`
- explicit serial ticketed FIFO queue policy
- no runtime proof that multi-worker serving is safe on this substrate

That means:

- `multi_worker_scheduler_depth` is not the next honest implementation branch
- it stays secondary until the concurrency boundary is revalidated
- `continuous_batching` is the next locally reducible scheduler branch on the
  current path

## 5. What This Does Not Claim

It does not claim:

- continuous batching already exists
- multi-worker scheduler depth is safe
- scheduler parity with `oMLX` / `vMLX`

It only claims:

- the scheduler backlog is now narrowed beyond a generic implementation list
- the next branch is `continuous_batching`
- `multi_worker_scheduler_depth` remains secondary because it still depends on
  concurrency-safety revalidation
