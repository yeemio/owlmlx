# owlmlx Goal Contract: Replacement-Grade Stability Alignment

> Status: active goal contract
> Updated: 2026-04-13

## Goal ID

`owlmlx-replacement-grade-stability-alignment`

## Title

Close the replacement-grade stability gap between `owlmlx` and the local
reference runtimes `oMLX` / `vMLX`.

## Success Definition

This goal succeeds only when `owlmlx` can honestly be described as approaching
the same class of local runtime stability that makes `oMLX` and `vMLX`
serious customer-facing systems rather than experimental runtimes.

At minimum, that requires:

1. one host-stable execution baseline for supported local serving
2. owned cache / scheduler depth that is no longer only narrative or truth
   surface
3. owned multi-model lifecycle governance beyond minimal load/unload semantics
4. repeated heavy-weight runtime proof on a supported host, not just specimen
   staging contracts
5. customer-runtime evidence strong enough to move beyond "early runtime
   prototype"

This goal does **not** require matching every feature breadth of `oMLX` or
`vMLX` before progress counts. It does require closing the stability-class gap
that currently prevents honest customer-facing claims.

## Blocked Definition

The goal is blocked only if:

- a core stability gap cannot be reduced without an external dependency and
  that dependency is the exact blocker, or
- the current runtime truth is too thin to select the next dominant gap
  honestly

## Hard Rules

1. Work only inside `owlmlx`.
2. Do not let specimen-specific work redefine the top-level goal.
3. Do not claim customer readiness before `oMLX` / `vMLX`-class stability is
   evidenced.
4. Do not treat control-plane or UI work from the shell repo as `owlmlx`
   closure.
5. Prefer closing runtime truth drift and stability blockers before adding new
   runtime surface area.

## Out of Scope

- desktop UI or dashboard work
- product-shell replacement storytelling
- MiniMax quantization or optimization as a top-level goal
- modality expansion for its own sake
- replacement verdict inflation

## Current Truth

- `owlmlx` already has a real executable runtime kernel and migration seams.
- `owlmlx` already has structured blocker truth, specimen gates, and
  host-forensics contracts.
- `owlmlx` is **not** yet at `oMLX` / `vMLX` stability class.
- current host MLX execution remains blocked at the import layer.
- current replacement posture is still closer to an early formal runtime than a
  customer-ready one.

## Remaining Gaps

1. `host_stable_execution`
2. `cache_scheduler_depth`
3. `multi_model_lifecycle_governance`
4. `heavy_weight_runtime_repeatability`
5. `customer_runtime_evidence`

## Dominant Next Gap

The current dominant next gap is:

`cache_scheduler_depth`

Reason:

- `multi_model_lifecycle_governance` now has a runtime-owned status surface,
  governance-controls surface, governance-transition ledger, active-kernel
  governance observations, and a governance policy-gap freeze
- its remaining absent controls are now frozen more narrowly as policy-grade
  gaps (`pinning`, `TTL`, `eviction-history governance`) rather than the next
  dominant observation/integration gap
- `host_stable_execution` remains exact but externally constrained on this host
- `heavy_weight_runtime_repeatability` still has a frozen exact external
  blocker: a supported host/system image is required for repeated heavy-weight
  proof
- `customer_runtime_evidence` can now move its dominant next gap away from
  governance once the policy gap is exact
- `cache_scheduler_depth` remains the clearest remaining locally reducible gap:
  its counter ownership is now exact on the active path
  (`reuse_counter` visible; `residency_counter` / `eviction_counter`
  not-runtime-owned here), so the remaining locally reducible cache work is
  an exact scheduler implementation backlog on top of a serial ticketed FIFO floor,
  plus an exact TurboQuant preconditions branch that still lacks safe-activation requirements
 - within that scheduler backlog, the next exact implementation branch is now
   `continuous_batching`; `multi_worker_scheduler_depth` remains secondary
   until the concurrency boundary is revalidated honestly
 - `owlmlx.dominant_gap_reselection` now freezes that cache choice directly,
   so the loop no longer needs to infer it from narrative comparison once
   governance and heavy-weight truth are already exact
