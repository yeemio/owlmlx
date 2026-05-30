# owlmlx Replacement-Grade Stability Gaps

> Status: authoritative
> Updated: 2026-04-22

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
- one verified candidate baseline selected by both the isolated validation
  registry and the default `~/.owlmlx` registry
- one selected heavy-weight retarget target that fits the current host serving
  budget and now has repeated proof visible on this host

`owlmlx` still lacks:

- broader long-run host confidence beyond the current exact selected path

### 3.2 `cache_scheduler_depth`

Reference systems prove:

- real cache reuse and scheduler depth in live runtime behavior
- batching/scheduler work goes beyond descriptive truth surfaces

`owlmlx` currently has:

- cache truth/evidence surfaces
- scheduler and TurboQuant exactness surfaces
- one bounded structural ingress seam before whole-request gate claim
- one bounded pre-gate request-aggregation/cohort window visible before
  whole-request gate claim
- one active request-aggregation seam frozen at
  `owlmlx.cache_request_aggregation_active_seam`
- repeated-load aggregated-dispatch proof on the non-stream main runtime path
  recorded in
  `tests/test_runtime_kernel.py::test_repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load`
  (release floor `3.1` closed 2026-04-25; this is release-floor language and
  does not yet imply replacement-grade scheduler/cache closure)

`owlmlx` still lacks:

- replacement-grade scheduler/cache closure
- broader request-aggregation dependency closure on the active runtime path
- request aggregation / continuous batching / parity

Current boundary:

- cache currently points at `owlmlx.cache_request_aggregation_active_seam`
- `closure_level = aggregation_active_seam_exact`
- exact blocker:
  `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection`
- subprocess-transport sentinel narrowing is closed in the current paradigm;
  further cache-scheduler progress redirects to native MLX backend feasibility
  rather than another sentinel rung

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
- one successful budget-fit heavy boundary entry on the selected retarget path:
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- two successful repeat runs on that same selected path under default
  `~/.owlmlx` truth
- one original exact heavy-boundary blocker still frozen for the Kimi target:
  `loading 122.0G would exceed serving budget: 0.0G loaded + 122.0G requested = 122.0G > 116.0G limit`

`owlmlx` still lacks:

- broader long-run heavy-weight confidence beyond the current narrow supported-
  host repeated-proof checkpoint

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

- Path A remains preserved as a completed structural checkpoint
- the active cache blocker is no longer raw structural hook existence
- cache is now narrowed beyond ingress onto the request-aggregation active seam

## 5. Current Dominant Gap

> **⚠️ Point-in-time / superseded (flagged 2026-05-30 audit).** This section's
> "dominant gap = `cache_scheduler_depth`" and "next executable mainline = native
> MLX backend feasibility" are STALE. Native MLX backend feasibility (B-1 →
> B-1.3) is complete; `native-mlx-backend-capability-matrix.md` §7 redirects
> beyond it. Current active campaigns are F-1 / F-4 / B-1c (see
> `runtime-capability-matrix.md` + `master-outline.md` §8.5). The terminal-notice
> sentinel-chain decomposition below is historical phase-45 detail, not the live
> selector. Do not use this section to pick the next mainline.

`cache_scheduler_depth` now becomes the dominant locally reducible gap on the
current environment:

- both the isolated validation registry and the default `~/.owlmlx` registry
  now select `omlx-probe-venv` as a verified baseline
- historical quarantine residue and crash reports remain visible as historical
  context
- the original Kimi heavy-boundary blocker remains frozen exactly at
  `122.0G > 116.0G`
- the selected retarget heavy boundary on
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it` now fits and now has repeated
  proof visible on this host at `62.0G <= 116.0G`

That means the current loop posture is now:

- the supported-host branch is no longer the active dominant gap on this host
- the current host now has `supported_host_candidate_baseline_established`
- supported-host repeated heavy-weight proof is now visible on the selected
  budget-fit path
- the local governance fallback branch is policy-closed
- cache now reopens beyond ingress onto the active request-aggregation seam
- the bounded pre-gate window already forms cohorts before whole-request gate
  claim
- one non-stream child exchange can already carry multiple requests in one
  exchange
- the non-stream main serving path now hands that bounded cohort into the
  aggregated child exchange
- stream gate release is now decoupled from outer consumer completion
- a second backend stream can now start before the first iterator consumer
  receives the first stream's terminal event
- a second backend stream can now also start before the first terminal payload
  is committed to the first stream queue
- a second backend stream can now also start before the first terminal payload
  is decoded and captured
- a second backend stream request can now also enter the live backend exchange
  before the first terminal record is fully captured
- a second backend stream request can now also enter the live backend exchange
  before the first stream fully matches its terminal-record prefix on child
  stdout
- a second backend stream request can now also enter the live backend exchange
  before the first terminal done payload reaches its action discriminant on
  child stdout
- a second backend stream request can now also enter the live backend exchange
  before the first terminal-notice record is fully captured
- a second backend stream request can now also enter the live backend exchange
  before child stdout fully matches the first terminal-notice prefix
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first terminal-notice action discriminant
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first terminal-notice action stem
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first explicit terminal-notice marker field
- a second backend stream request can now also enter the live backend exchange
  before child stdout fully matches the first terminal-notice marker key
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first terminal-notice marker stem
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first terminal-notice marker discriminant
- owlmlx now also owns one runtime-owned terminal-notice leading-discriminator
  record ahead of the old marker-key-lead seam
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the first terminal-notice marker-key lead on the
  old notice record
- a second backend stream request can now also enter the live backend exchange
  before child stdout fully matches that runtime-owned leading-discriminator
  action
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned leading-discriminator prefix
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned leading-discriminator stem
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned leading-discriminator
  discriminant
- owlmlx now also owns one earlier runtime-owned `terminal_notice_lead` marker
  on that same leading-discriminator record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned `terminal_notice_lead`
  marker-prefix on the leading-discriminator record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches that runtime-owned `terminal_notice_l`
  marker-stem on the leading-discriminator record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the fuller earlier runtime-owned discriminator
  prefix on the newer discriminator record
- a second backend stream request can now also enter the live backend exchange
  before child stdout reaches the earlier runtime-owned discriminator stem on
  that newer discriminator record
- one new earlier runtime-owned boundary record now also exists ahead of that
  newer runtime-owned leading-discriminator record
- a second backend stream request can now also enter the live backend exchange
  once child stdout reaches that new earlier runtime-owned boundary stem and
  before child stdout reaches fuller earlier-runtime-owned-boundary prefix
  detection on that same internal record
- the literal prefix before `runtime_owned_terminal_b` is not yet an honest
  runtime-owned transport boundary on this path
- earlier-runtime-owned boundary stem detection is now frozen as the first
  honest unique boundary on that newer runtime-owned boundary record
- one distinct earlier runtime-owned terminal record now exists ahead of that
  current stem seam
- a second backend stream request can now also enter the live backend exchange
  after child stdout reaches `runtime_owned_terminal_earlier_boundary` and
  before child stdout reaches `runtime_owned_terminal_b`
- earlier-runtime-owned-boundary earlier-boundary detection is also frozen as
  the first honest unique boundary on the newer earlier-boundary record
- one distinct earlier-earlier runtime-owned terminal record now exists ahead
  of that existing earlier-boundary record:
  `runtime_owned_terminal_earlier_earlier_boundary`
- a second backend stream request can now also enter the live backend exchange
  after child stdout reaches `runtime_owned_terminal_earlier_earlier_boundary`
  and before child stdout reaches `runtime_owned_terminal_earlier_boundary`
- the remaining exact blocker is now
  `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_detection`
- the newer earlier-runtime-owned discriminator discriminant remains frozen as
  the first honest unique boundary on the newer earlier-runtime-owned
  discriminator record
- the newer earlier-runtime-owned leading-discriminator discriminant also
  remains frozen as the first honest unique boundary on the newer earlier-
  runtime-owned leading-discriminator record
- current marker-discriminant detection remains frozen as the first honest
  unique boundary on the current runtime-owned marker-first record
- one new earlier runtime-owned terminal-notice discriminator record now
  exists ahead of that current marker-discriminant seam
- one new earlier runtime-owned leading-discriminator record now also exists
  ahead of that newer discriminator record
- marker-key lead remains preserved as the first unique boundary on the old
  terminal-notice record
- cache is now the next dominant locally reducible gap
- governance micro-rounds must not reopen
- the next coordinator choice is no longer whether to authorize one new
  earlier runtime-owned boundary ahead of the current stem seam
- the next coordinator choice is no longer whether to narrow inside
  `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`
- the subprocess-transport sentinel chain is now a baseline contract that a
  native backend must preserve or replace explicitly
- the next executable mainline is native MLX backend feasibility while
  preserving post-claim serial invariants and non-stream handoff truth; this
  still does not claim batching, prefix-cache reuse, parity, or interleaving
