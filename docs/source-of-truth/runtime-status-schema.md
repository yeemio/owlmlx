# owlmlx Runtime Status Schema

> Status: authoritative
> Updated: 2026-04-13

## 1. Purpose

This document defines the runtime-owned schema boundary for the status surfaces
that `owlmlx` expects upper layers to consume.

## 2. Core Runtime Status Schema

The core runtime status schema is the owned shape for general runtime truth.

### 2.1 Required Semantic Fields

| Field | Meaning |
|---|---|
| `runtime` | runtime identity |
| `status` | current health or availability state |
| `load_state` | whether runtime or model is loaded, loading, idle, or unavailable |
| `memory_active` | active memory footprint |
| `memory_budget_gb` | runtime memory budget when defined |
| `model_memory_utilization` | budget-relative utilization when computable |
| `queue_state` | active or waiting work when applicable |
| `truth_level` | how direct the runtime truth is |

### 2.2 Optional Semantic Fields

| Field | Meaning |
|---|---|
| `memory_peak` | peak memory usage |
| `cache_truth` | owned cache visibility or reuse state |
| `restart_requested` | runtime-level restart request |
| `loaded_model_count` | number of loaded models when the runtime is multi-model |
| `loaded_model_details` | per-model runtime detail when available |

## 3. Large-Weight Runtime Path Status Schema

This schema is owned by `owlmlx` as a path-level status contract.

### 3.1 Required Semantic Fields

| Field | Meaning |
|---|---|
| `runtime` | runtime identity for the path |
| `path_variant` | owned runtime-path variant name |
| `status` | current runtime state |
| `model` | current specimen or model identity |
| `tier` | serving tier, currently background |
| `interactive_status` | honest interaction posture |
| `lifecycle_mode` | manual, managed, or other lifecycle posture |
| `memory_active` | active memory footprint |
| `memory_budget_gb` | path-specific memory budget |

### 3.2 Optional Semantic Fields

| Field | Meaning |
|---|---|
| `memory_peak` | peak memory usage |
| `layers` | structural layer count |
| `layout` | path-specific artifact layout |
| `fuse_eval` | runtime optimization flag |
| `cache_entries` | cache occupancy |
| `cache_size_gb` | cache size |
| `cache_pinned` | pinned cache count |
| `prefill_baseline` | prefill baseline evidence |
| `decode_baseline` | decode baseline evidence |
| `uptime_s` | runtime uptime |

## 4. Contract Interpretation Rules

- `interactive_status` is an honesty field, not a marketing field.
- `path_variant` belongs to runtime truth, not only to shell labeling.
- `memory_*` fields are runtime facts, not UI estimates, when sourced directly.
- A missing optional field must not be misread as capability support.

## 5. Extraction Direction

The platform shell can keep transport and presentation endpoints, but the schema
definitions above should become the reference point for:

- router proxy responses
- dashboard proxy responses
- snapshot embedding
- contract tests

## 6. Stabilization-1 Contract Freeze

From Stabilization-1 onward, `/v1/runtime/status` is split into:

- stable contract sections:
  - `contract`
  - `summary`
  - `health`
  - `inventory`
  - `budget`
  - `restart`
- diagnostic sections:
  - `backend.detail`
  - `governance_observations`
  - `generation_gate`

The stable sections are intended for long-lived `owlcoda` / `owlops` consumption.
The diagnostic sections remain useful, but upper layers must treat them as best-effort detail rather than field-stable compatibility promises.

`GET /healthz` is also frozen as a smaller liveness contract in Stabilization-1:

- `contract.surface`
- `contract.version`
- `runtime`
- `backend_name`
- `ok`
- `readiness`
- `active_model_id`
- `model_count`

## 7. Stabilization-2 Runtime-Owned Readiness Surfaces

Stabilization-2 introduces two additional runtime-owned machine/operator
surfaces that sit alongside runtime status:

- `owlmlx.mlx_environment`
  - readiness for safe `mlx_lm` subprocess use on the current machine
- `owlmlx.mlx_blocker_report`
  - machine-level summary when no usable MLX baseline exists

These are not replacements for `/v1/runtime/status`. They are narrower,
runtime-only preparation contracts for large-weight specimen work.

## 8. Stabilization-3 Runtime-Owned First-Smoke Decision Surface

Stabilization-3 adds one further runtime-owned machine/operator surface:

- `owlmlx.large_weight_first_smoke_decision`
  - a locality decision for large-weight first smoke
  - combines:
    - `default_metal` specimen gate
    - `force_cpu` specimen gate
    - host-level crash forensics

This surface exists so `owlmlx` can answer one narrow question honestly:

- should first smoke proceed on this host
- or should first smoke move to another host/system image

This is still not a replacement verdict. It is a runtime-only handoff
decision for large-weight validation.

## 9. Phase 45 Replacement-Grade Stability Surfaces

Phase 45 adds two narrower runtime-owned surfaces that support
replacement-grade stability alignment without claiming parity:

- `owlmlx.host_stable_execution`
  - direct host-level answer for whether this machine is a valid candidate for
    deeper runtime validation
- `owlmlx.cache_scheduler_status`
  - direct runtime-owned answer for current cache/scheduler closure depth
- `owlmlx.cache_residency_evidence`
  - direct runtime-owned answer for current cache residency/reuse evidence rung
- `owlmlx.cache_repeatability_evidence`
  - direct runtime-owned answer for repeated-serving cache evidence rung
- `owlmlx.turboquant_readiness`
  - direct runtime-owned answer for whether TurboQuant is still safety-blocked,
    evidence-blocked, or ready for controlled validation
- `owlmlx.cache_closure_rung`
  - direct runtime-owned answer for the current conservative cache closure rung
- `owlmlx.cache_counter_gap`
  - direct runtime-owned answer for whether the remaining cache blocker has narrowed to an exact counter-grade gap
- `owlmlx.cache_counter_feasibility`
  - direct runtime-owned answer for which cache counters are actually owned on the current path and which remaining cache work has shifted to scheduler/TurboQuant closure
- `owlmlx.cache_scheduler_turboquant_split`
  - direct runtime-owned answer for whether the remaining cache closure has now split cleanly between scheduler depth and TurboQuant preconditions
- `owlmlx.cache_scheduler_floor_gap`
  - direct runtime-owned answer for the exact scheduler-grade floor on the active cache path once the split is already exact
- `owlmlx.cache_scheduler_implementation_backlog`
  - direct runtime-owned answer for the exact scheduler implementation work that remains once the serial floor is already exact
- `owlmlx.cache_scheduler_branch_selection`
  - direct runtime-owned answer for which scheduler branch should be worked next once the backlog is already exact
- `owlmlx.cache_continuous_batching_feasibility`
  - direct runtime-owned answer for whether continuous batching is merely absent or is exact-feasibility-blocked on the active path
- `owlmlx.cache_batching_mechanism_subgap`
  - direct runtime-owned answer for which missing batching mechanism is the next exact local subgap once continuous batching is already proven structurally blocked
- `owlmlx.cache_request_aggregation_window_exactness`
  - direct runtime-owned answer for the exact ingress and dependency blockers underneath request aggregation once that mechanism is already selected
- `owlmlx.cache_pre_gate_cohort_window_feasibility`
  - direct runtime-owned answer for whether owlmlx owns any cohort/admission seam before whole-request gate claim on the active path
- `owlmlx.cache_turboquant_preconditions_gap`
  - direct runtime-owned answer for the exact TurboQuant safe-activation requirements still missing on the active cache path
- `owlmlx.dominant_gap_reselection`
  - direct runtime-owned answer for which locally reducible gap should be worked next once cache, governance, and heavy-weight branches are already frozen strongly enough to compare honestly
- `owlmlx.multi_model_governance_status`
  - direct runtime-owned answer for current multi-model lifecycle governance depth
- `owlmlx.multi_model_governance_controls`
  - direct runtime-owned answer for which governance controls are present today and what repeated transition evidence exists without inventing absent controls
- `owlmlx.multi_model_governance_transition_ledger`
  - direct runtime-owned answer for whether recent governance transitions and repeated transition signals are visible as first-class lifecycle truth
- `owlmlx.multi_model_governance_policy_gap`
  - direct runtime-owned answer for whether the remaining governance blocker is still observation-grade or is now policy-grade only
- `owlmlx.heavy_weight_runtime_repeatability`
  - direct runtime-owned answer for whether heavy-weight repeatability is locally blocked, host-ready, or visible on a supported host
- `owlmlx.customer_runtime_evidence`
  - direct runtime-owned answer for how much cumulative replacement-grade evidence now exists, which gaps remain externally blocked, and which locally reducible gap should be worked next

These surfaces are still narrower than `/v1/runtime/status`. They exist so
`owlmlx` can answer two replacement-grade questions honestly:

- should deeper runtime validation continue on this host
- how much cache/scheduler depth does the runtime actually own today
- what level of cache residency/reuse evidence does the runtime actually own today
- what level of repeated-serving cache evidence does the runtime actually own today
- whether TurboQuant remains blocked by cache safety/evidence or has reached a
  runtime-owned controlled-validation rung
- what the current conservative cache closure rung actually is
- whether the remaining cache blocker is still observation-grade or has narrowed to exact missing counters plus serial-only scheduler depth
- whether cache counter ownership itself is already exact, so the next cache step is scheduler-depth / TurboQuant rather than more fake counter work
- whether the remaining cache closure has already split exactly into scheduler-depth versus TurboQuant work
- whether the scheduler branch itself is now frozen as a serial single-worker floor
- whether the scheduler branch has now narrowed further into an implementation backlog rather than a truth-gap
- whether the next scheduler branch is `continuous_batching` or a different exact path once the backlog is already frozen
- whether `continuous_batching` is merely absent or structurally blocked once it is already the selected scheduler branch
- whether the TurboQuant branch itself is now frozen as an exact set of missing preconditions rather than a generic safety posture
- whether cache remains the next locally reducible dominant gap once governance is policy-gap exact and heavy-weight repeatability is externally blocked
- what multi-model lifecycle behavior the runtime actually owns today
- which multi-model governance controls and transition evidence the runtime actually owns today
- whether recent governance transitions are visible strongly enough to freeze the remaining lifecycle gap exactly
- whether the remaining governance blocker is still observation-grade or has narrowed to policy-grade absent controls
- whether heavy-weight repeatability is blocked locally or only awaits supported-host repeated proof
- how much cumulative customer-runtime evidence now exists without inflating readiness claims

Phase 45 also adds one narrower diagnostic section inside the core runtime
status payload:

- `governance_observations`
  - lightweight active-kernel observations for:
    - transition count
    - recent explicit-targeting/restart activity
    - active-model reassignment visibility
    - restart-restore visibility

This section is diagnostic rather than field-stable policy truth. It exists so
the governance controls and transition ledger can consume runtime-owned
observations instead of harness-only synthetic evidence.
