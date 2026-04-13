# owlmlx Stabilization-2: Machine-Level MLX Import Blocker

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only blocker truth for this machine's MLX import path

## 1. Purpose

This document freezes the current blocker truth after multiple clean-baseline
attempts:

**The current machine can hold a complete large-weight specimen locally, but
its default MLX/Metal path still cannot provide a usable `mlx_lm` subprocess
environment.**

This is not a model-directory blocker anymore. It is a machine-level
MLX/Metal import blocker.

## 2. Verified Facts

Current specimen truth:

- local specimen: `/Users/yeemio/AI/Agent/models/MiniMax-M2.7`
- indexed shard count: `125`
- present shard count: `125`
- specimen path blocker: `null`

Current environment truth:

- current interpreter: `ModuleNotFoundError` for `mlx_lm`
- `.runtime1-mlx` in `default_metal`: quarantined after `returncode = -6`
- `.runtime2-mlx` in `default_metal`: quarantined after `returncode = -6`
- `force_cpu` is tracked as a distinct execution mode
- historical top-level shell checks suggested that `MLX_FORCE_CPU=1` could
  import `mlx.core`, `mlx_lm`, and `from mlx_lm import load` on `.runtime2-mlx`
- current runtime-owned probe matrix now shows that the same interpreter still
  returns `-6` under both:
  - `launch_mode = direct_exec`
  - `launch_mode = env_wrapper`
  for:
  - `mlx_core_import`
  - `mlx_lm_import`
  - `mlx_lm_load_symbol`
- therefore the earlier shell-success observation is no longer sufficient as a
  current verified truth; the large-weight specimen gate remains blocked

Persisted quarantine file:

- `~/.owlmlx/mlx-unsafe-python.json`

Current shared crash signature:

- Objective-C `NSRangeException`
- `libmlx.dylib`
- `mlx::core::metal::Device::Device()`
- subprocess return code `-6`

## 3. Architectural Consequence

The next blocker is no longer inside runtime contracts, specimen gates, or
download completeness.

The blocker is:

- this machine currently cannot import `mlx_lm` safely through the default
  Metal path in any verified clean baseline we have created
- and the current runtime-owned automated `force_cpu` probe path has not yet
  produced a usable registered baseline either

That means there is now a second-order blocker as well:

- `owlmlx` still lacks a trustworthy, runtime-owned way to promote that
  operator-observed `force_cpu` success into a verified baseline contract

That means `owlmlx` must not pretend default-Metal MiniMax first smoke is the
next immediate step on this host.

## 4. Runtime-Owned Response

`owlmlx` now responds honestly by:

- quarantining any interpreter that aborts during import probe
- refusing to auto-prefer a stale baseline path
- exposing the blocked state through:
- `scripts/runtime_mlx_environment_readiness.py`
- `scripts/runtime_large_weight_specimen_gate.py`
- `scripts/runtime_mlx_blocker_report.py`

These contracts are now mode-aware:

- `default_metal`
- `force_cpu`

The blocker report itself is now a stable runtime-owned contract:

- `contract.surface = "owlmlx.mlx_blocker_report"`
- `contract.version = "stabilization2"`
- stable sections:
  - `summary`
  - `readiness`
  - `quarantine`
- diagnostic sections:
  - `readiness.probes`

## 5. What This Does Not Mean

This does **not** prove:

- MiniMax-M2.7 is incompatible with owlmlx
- MLX conversion is impossible
- another machine or another OS/runtime state would fail the same way

It proves only this:

**this machine is currently blocked at the default MLX/Metal import layer.**

It also proves this narrower operational fact:

**manual shell success on `force_cpu` is not yet the same thing as a
runtime-owned usable baseline.**

## 6. Next Rational Step

The next rational step is not another ad-hoc local venv attempt that still
assumes one interpreter equals one baseline.

It is one of:

- mode-aware baseline registration
- CPU-forced first smoke for MiniMax-M2.7
- force_cpu discrepancy forensics: explain why top-level shell success and
  runtime-owned subprocess probes diverge
- machine-level MLX/Metal crash forensics
- trying a distinct host or system image
- waiting for an upstream MLX/Metal fix and re-validating through the same gate

## 7. Runtime-Owned Forensics Harness

`owlmlx` now includes a dedicated discrepancy harness:

- `scripts/runtime_mlx_probe_matrix.py`

It compares:

- `execution_mode = default_metal | force_cpu`
- `launch_mode = direct_exec | env_wrapper`
- probe cases:
  - `mlx_core_import`
  - `mlx_lm_import`
  - `mlx_lm_load_symbol`

This exists specifically to explain or collapse the gap between:

- operator-observed top-level shell success
- runtime-owned subprocess probe failure

Current verified result on this host:

- `.runtime2-mlx`
- `execution_mode = force_cpu`
- `launch_mode = direct_exec` => all three import probes fail with `-6`
- `launch_mode = env_wrapper` => all three import probes fail with `-6`

So the discrepancy has narrowed materially:

- the runtime-owned matrix no longer supports promoting `force_cpu`
- and the prior shell-success observation must be treated as stale, divergent,
  or not yet reproducible under the current verified command set

Until that changes, `force_cpu` must not be promoted to a verified baseline.

## 8. Host-Level Crash Forensics

`owlmlx` now also exposes:

- `scripts/runtime_mlx_host_forensics.py`

This contract summarizes:

- recent MLX-related `Python-*.ips` crash reports
- the shared `NSRangeException` signature
- `mlx::core::metal::Device::Device()` presence
- machine and OS context

This is not a replacement for upstream debugging, but it makes the local
handoff boundary explicit:

- if readiness is blocked
- and crash forensics still show the same MLX/Metal signature

then the next rational step may be another host or an upstream-correlated fix,
not another blind local specimen smoke attempt.
