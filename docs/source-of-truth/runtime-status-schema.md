# owlmlx Runtime Status Schema

> Status: authoritative
> Updated: 2026-04-09

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
