# owlmlx Phase 45: Host-Stable Execution Status

> Status: authoritative
> Updated: 2026-04-16
> Scope: runtime-only host-level execution readiness for replacement-grade validation

## 1. Purpose

This document turns `host_stable_execution` from a narrative replacement gap
into a runtime-owned contract.

The question it answers is narrower than full runtime parity:

**Is this host even a valid candidate for replacement-grade runtime
validation?**

That is more fundamental than:

- specimen-first smoke
- benchmark work
- optimization work

because if the host cannot sustain one verified-safe execution baseline, those
later steps do not belong on this machine yet.

## 2. Owned Contract

`owlmlx/runtime/host_stability.py` now owns:

- `build_host_stable_execution_status(...)`
- `host_stability_to_dict(...)`

Operator entry:

- `scripts/runtime_host_stable_execution_status.py`

Contract:

- `surface = "owlmlx.host_stable_execution"`
- `version = "phase45"`

Stable sections:

- `summary`
- `default_metal_readiness`
- `force_cpu_readiness`
- `host_forensics`

## 3. Status Semantics

Possible `summary.status` values:

- `host_ready_for_runtime_validation`
- `host_blocked_move_validation`
- `host_blocked_continue_forensics`

Interpretation:

- `host_ready_for_runtime_validation`
  - at least one execution mode has a runtime-owned verified-safe baseline
  - this host may proceed into deeper runtime validation
- `host_blocked_move_validation`
  - no verified-safe baseline exists
  - host forensics still show repeated MLX crash evidence
  - runtime validation should move to another host/system image
- `host_blocked_continue_forensics`
  - no verified-safe baseline exists
  - but the host does not yet have strong enough forensics to justify hard
    move-host recommendation

## 4. Current Verified Result On This Host

Current live result is:

- `summary.status = "host_ready_for_runtime_validation"`
- `summary.ready = true`
- `summary.preferred_execution_mode = "default_metal"`
- `summary.blocked_reason = null`
- `summary.recommended_next_step = "run repeated runtime validation on this host with default_metal"`

Why:

- isolated validation registry truth
  - `register_verified_mlx_baseline.py` can register
    `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/python`
    as `omlx-probe-venv`
  - `runtime_mlx_environment_readiness.py` then returns:
    - `readiness = ready`
    - `selected_label = omlx-probe-venv`
- default `~/.owlmlx` registry truth
  - `~/.owlmlx/mlx-verified-python.json` contains `omlx-probe-venv`
  - `runtime_mlx_environment_readiness.py` returns:
    - `readiness = ready`
    - `selected_label = omlx-probe-venv`
  - `runtime_host_stable_execution_status.py` returns:
    - `summary.status = host_ready_for_runtime_validation`
    - `summary.ready = true`
- historical quarantine residue
  - `~/.owlmlx/mlx-unsafe-python.json` still retains 6 unsafe entries
  - host forensics still show historical:
    - `NSRangeException`
    - `SIGABRT`
    - `mlx::core::metal::Device::Device()`
  - that residue remains historical context, not the current blocked truth,
    because one verified-safe baseline now exists and is selected by the
    default registry

## 5. What This Changes

Before this round, `owlmlx` already had:

- environment readiness
- blocker report
- host forensics
- first-smoke locality decision

But a reader still had to infer the host-level answer by combining those
surfaces.

Now `owlmlx` owns a direct host-level answer for the replacement-grade gap:

- this host now has one supported candidate baseline for deeper runtime
  validation
- historical crash residue can stay visible without being misreported as the
  current blocking verdict

## 6. What This Does Not Claim

It does not claim:

- parity with `oMLX` or `vMLX`
- full runtime stability
- heavy-weight repeatability restored
- customer readiness

It only claims:

- `host_stable_execution` now has a runtime-owned contract
- the current host is a valid candidate for stronger runtime validation
- the current verdict must distinguish isolated validation truth, default
  registry truth, and historical quarantine residue
