# owlmlx Phase 45: Host-Stable Execution Status

> Status: authoritative
> Updated: 2026-04-13
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

Current result is:

- `summary.status = "host_blocked_move_validation"`
- `summary.ready = false`
- `summary.blocked_reason = "no verified-safe mlx baseline exists on this host"`
- `summary.recommended_next_step = "move replacement-grade runtime validation to another host or system image"`

Why:

- `default_metal` readiness remains blocked
- `force_cpu` readiness also remains blocked
- host forensics continue to show repeated:
  - `NSRangeException`
  - `SIGABRT`
  - `mlx::core::metal::Device::Device()`

## 5. What This Changes

Before this round, `owlmlx` already had:

- environment readiness
- blocker report
- host forensics
- first-smoke locality decision

But a reader still had to infer the host-level answer by combining those
surfaces.

Now `owlmlx` owns a direct host-level answer for the replacement-grade gap:

- is this host a candidate for deeper runtime validation
- or should the validation path move away from this machine

## 6. What This Does Not Claim

It does not claim:

- parity with `oMLX` or `vMLX`
- full runtime stability
- customer readiness

It only claims:

- `host_stable_execution` now has a runtime-owned contract
- the current host is not the right place to continue replacement-grade
  validation

