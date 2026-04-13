# owlmlx Phase 45 Round 1: Replacement-Grade Gap Freeze

> Status: archived execution prompt
> Updated: 2026-04-13

## Goal

Execute the first round of
`owlmlx-replacement-grade-stability-alignment`.

This round does **not** try to close the full stability gap. It freezes the
top-level gap contract so future rounds cannot drift back into specimen-first
or shell-first goals.

## Dominant Gap

`goal_drift_and_gap_freeze`

The repo's dominant question drifted into:

- whether MiniMax first smoke should continue locally or move hosts

That is a real runtime question, but it is **not** the main `owlmlx` goal.
The main goal is replacement-grade stability alignment versus `oMLX` and
`vMLX`.

## Required Outcome

This round must leave behind:

1. one formal goal contract for replacement-grade stability alignment
2. one authoritative `owlmlx` source-of-truth document that lists the current
   replacement-grade stability gaps
3. one corrected top-level dominant question in `master-outline.md`

## Hard Rules

1. Stay inside `owlmlx`.
2. Do not reopen shell/UI/platform work.
3. Do not claim parity with `oMLX` or `vMLX`.
4. Do not let specimen-specific work define the current top-level goal.
5. Keep this round focused on truth freeze and gap formalization.

## Required Gap Inventory

The new source-of-truth must freeze at least these gaps:

1. `host_stable_execution`
2. `cache_scheduler_depth`
3. `multi_model_lifecycle_governance`
4. `heavy_weight_runtime_repeatability`
5. `customer_runtime_evidence`

For each gap, include:

- what `oMLX` / `vMLX` currently demonstrate
- what `owlmlx` currently has
- why the gap still blocks customer-grade runtime claims

## Verification

At minimum:

- ensure touched docs are internally consistent
- update `master-outline.md`
- update `runtime-capability-matrix.md` only if a capability claim changed

## Honest End State

Good:

- `owlmlx` now has a frozen replacement-grade stability goal contract
- the next dominant gap can be selected from one stable inventory

Bad:

- keep using MiniMax/local-host first smoke as the implicit top-level goal
- claim parity based on runtime surface breadth alone

