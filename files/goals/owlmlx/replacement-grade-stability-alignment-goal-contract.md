# owlmlx Goal Contract: Supported-Host Runtime Substrate Closure

> Status: active goal contract
> Updated: 2026-04-15

## Goal ID

`owlmlx-supported-host-runtime-substrate-closure`

## Title

Make `owlmlx` a supported-host runtime substrate that upper layers can rely on
without inflating platform-level replacement claims.

## Success Definition

This goal succeeds only when `owlmlx` can honestly be described as a runtime
substrate with one supported-host execution baseline, stable runtime-owned
contracts, and enough runtime depth that upper layers do not need to guess,
compensate, or redefine runtime truth.

At minimum, that requires:

1. one verified supported-host execution baseline for local serving
2. owned cache / scheduler depth that moves beyond narrative/status-only truth
3. owned multi-model lifecycle governance beyond minimal load/unload semantics
4. repeated heavy-weight runtime proof on a supported host, not just specimen
   staging contracts
5. customer-runtime evidence strong enough to move beyond "early formal
   runtime"

This goal still uses `oMLX` / `vMLX` as reference systems for stability class,
but day-to-day work should optimize for substrate closure, not for broad
platform-replacement storytelling.

## Blocked Definition

The goal is blocked only if:

- no supported host or system image is available for runtime-baseline
  establishment and that is the exact blocker, or
- the current runtime truth is too thin to select the next dominant gap
  honestly

## Hard Rules

1. Work only inside `owlmlx`.
2. Treat `oMLX` / `vMLX` as reference class, not as feature-clone scope.
3. Do not let specimen-specific work or current blocked-host forensics redefine
   the top-level goal once the blocker is already exact.
4. Do not claim customer readiness or platform replacement from `owlmlx`
   progress alone.
5. Do not treat control-plane, UI, or operator workflow work from shell repos
   as `owlmlx` closure.
6. Prefer supported-host baseline establishment and runtime contract depth over
   adding new runtime surface area.

## Out of Scope

- desktop UI or dashboard work
- product-shell replacement storytelling
- control-plane operability work that belongs in `owlops`
- MiniMax quantization or optimization as a top-level goal
- modality expansion for its own sake
- replacement verdict inflation

## Current Truth

- `owlmlx` already has a real executable runtime kernel and migration seams.
- `owlmlx` already has structured blocker truth, specimen gates, and
  host-forensics contracts.
- `owlmlx` already exposes runtime-owned status, evidence, and dominant-gap
  surfaces that upper layers can consume honestly.
- `owlmlx` is **not** yet at `oMLX` / `vMLX` stability class.
- the current host MLX execution remains blocked at the import layer.
- the current honest posture is still closer to an early formal runtime than a
  supported runtime substrate.

## Active Workstreams

1. `supported_host_baseline_establishment`
   - resolve the exact external blocker by moving runtime validation onto one
     supported host/system image
2. `cache_scheduler_depth`
3. `multi_model_lifecycle_governance`
4. `heavy_weight_runtime_repeatability`
5. `customer_runtime_evidence`

## Current Priority Order

### Priority 1: Supported-Host Baseline Establishment

This is the gating program priority.

Reason:

- the current host is already frozen as unsuitable for deeper replacement-grade
  validation
- without one supported host/image, `owlmlx` cannot honestly graduate from
  exact blocker reporting into supported runtime substrate claims
- continuing to spend the mainline on the blocked host would blur runtime
  closure with environment forensics

### Priority 2: `cache_scheduler_depth`

This remains the current locally reducible dominant gap.

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
 - that selected branch is now narrowed further: continuous batching is not
   just absent on the active path, it is exact-feasibility-blocked until one
   request-aggregation or interleaved scheduling mechanism exists
 - that continuous-batching blocker is now narrowed again: the first exact
   local mechanism subgap is `request_aggregation_window`;
   `shared_prefill_batch_step` and `interleaved_decode_scheduler` remain
   secondary behind aggregate admission
 - that request-aggregation mechanism is now narrowed again: the missing piece
   is a pre-gate admission window before whole-request session claim;
   aggregated child dispatch and stream release remain downstream
   dependencies
 - that ingress blocker is now narrowed again: no runtime-owned cohort window
   exists before gate claim, because owlmlx only owns queueing after
   whole-request gate entry and the validated serial safety boundary still
   begins there
 - `owlmlx.dominant_gap_reselection` now freezes that cache choice directly,
   so the loop no longer needs to infer it from narrative comparison once
   governance and heavy-weight truth are already exact
