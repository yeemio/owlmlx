# owlmlx Replacement-Grade Stability Gaps

> Status: authoritative
> Updated: 2026-04-16

## 1. Purpose

This document freezes the current replacement-grade stability gap between
`owlmlx` and the local reference runtimes `oMLX` / `vMLX`.

Its purpose is not to claim parity. Its purpose is to keep the `owlmlx` loop
honest about:

- what is already real runtime substrate
- what is still below reference-grade stability
- which local branch should be worked next

## 2. Honest Top-Level Verdict

`owlmlx` is a real runtime with real serving seams, migration entrypoints,
status/evidence surfaces, and consumer cutover proof.

`owlmlx` is still:

**early formal runtime, below reference-grade stability**

That means:

- it is no longer honest to call `owlmlx` only a toy
- it is not honest to present it as customer-ready
- it is not honest to claim `oMLX` / `vMLX` replacement

## 3. Frozen Replacement-Grade Gaps

### 3.1 `host_stable_execution`

Reference systems prove:

- usable local execution baselines exist on real serving hosts
- deeper runtime validation does not stop at import-time crashes

`owlmlx` currently has:

- machine-owned blocker truth
- MLX environment readiness
- blocker report
- host forensics
- host-stable execution status

`owlmlx` still lacks:

- one verified-safe MLX baseline on a supported host/system image

### 3.2 `cache_scheduler_depth`

Reference systems prove:

- real cache reuse and scheduler depth in live runtime behavior
- batching/scheduler work goes beyond descriptive truth surfaces

`owlmlx` currently has:

- cache truth/evidence surfaces
- scheduler and TurboQuant exactness surfaces
- one bounded structural ingress seam before whole-request gate claim

`owlmlx` still lacks:

- replacement-grade scheduler/cache closure
- broader cohort/admission/batching work on the active runtime path
- request aggregation / continuous batching / parity

Current boundary:

- cache is intentionally frozen at
  `owlmlx.cache_structural_ingress_seam`
- `closure_level = structural_ingress_seam_introduced`

### 3.3 `multi_model_lifecycle_governance`

Reference systems prove:

- stronger lifecycle controls than active/default semantics alone
- governed multi-model residency, not just visibility

`owlmlx` currently has:

- load/unload/restart semantics
- inventory and budget truth
- governance status / controls / transition ledger
- governance policy-gap truth
- runtime-owned pinning control
- runtime-owned TTL policy control
- explicit TTL expiry sweep on the runtime-owned path
- runtime-owned eviction-history governance
- unload protection for pinned models
- pin retention across restart

`owlmlx` still lacks:

- reference-grade governed multi-model residency beyond the now-closed local
  policy branch

### 3.4 `heavy_weight_runtime_repeatability`

Reference systems prove:

- repeatable heavy-weight serving on a supported host

`owlmlx` currently has:

- specimen completeness gate
- first-smoke locality decision
- heavy-weight repeatability status

`owlmlx` still lacks:

- repeated heavy-weight proof on a supported host/system image

### 3.5 `customer_runtime_evidence`

Reference systems prove:

- enough operational/runtime evidence to support stronger promises

`owlmlx` currently has:

- runtime-owned evidence ledger
- exact external blockers
- dominant-gap reselection

`owlmlx` still lacks:

- enough evidence to move beyond `early_formal_runtime`

## 4. Mainline Reset

This document freezes two key resets:

- the main `owlmlx` goal is **not** specimen-first smoke
- the main `owlmlx` goal is **supported-host runtime substrate closure**

It also freezes the cache checkpoint boundary:

- Path A is complete
- cache widening must stop at `structural_ingress_seam_introduced`

## 5. Current Dominant Gap

`host_stable_execution` remains the gating program priority, and on the current
environment it is exact-blocked:

- no supported-host path is currently available here for deeper runtime
  validation

That means the current loop posture is now:

- the supported-host branch remains the real dominant gap
- the local governance fallback branch is policy-closed
- cache remains intentionally frozen at
  `structural_ingress_seam_introduced`
- no further local rounds are authorized
- the next move is no longer another locally reducible policy round
- the only legal restart condition is a real supported host / system image
- when that condition is met, reentry must start from
  `phase-45-supported-host-reentry-baseline-establishment.md`
