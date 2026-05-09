# owlmlx Phase 45: Heavy-Weight Runtime Repeatability Status

> Status: authoritative
> Updated: 2026-04-16
> Scope: runtime-only heavy-weight repeatability for replacement-grade alignment

## 1. Purpose

This document advances `heavy_weight_runtime_repeatability` from a specimen
staging narrative into a runtime-owned status contract.

The question it answers is:

**Is heavy-weight repeatability locally blocked, merely entered once on a
supported host, merely host-ready, or actually visible as repeated proof?**

## 2. Owned Contract

`owlmlx/heavy_weight_repeatability_status.py` now owns:

- `build_heavy_weight_runtime_repeatability_status(...)`
- `heavy_weight_repeatability_status_to_dict(...)`

Operator entry:

- `scripts/runtime_heavy_weight_repeatability_status.py`

Contract:

- `surface = "owlmlx.heavy_weight_runtime_repeatability"`
- `version = "phase45"`

Stable sections:

- `summary`
- `host_stability`
- `first_smoke_decision`
- `supported_host_proof`
- `boundary_preconditions`
- `boundary_entry`

## 3. Repeatability Rungs

Current `summary.repeatability_rung` values:

- `local_blocked`
- `local_preconditions_incomplete`
- `budget_fit_heavy_boundary_entered`
- `host_ready_not_repeated`
- `supported_host_repeatability_visible`

Interpretation:

- `local_blocked`
  - the current host is not a valid heavy-weight repeatability candidate
- `local_preconditions_incomplete`
  - specimen prerequisites are incomplete before repeatability validation can begin
- `budget_fit_heavy_boundary_entered`
  - one budget-fit heavy boundary has been entered on the current host
  - repeated proof is not yet established and remains pending a narrow
    repeated-validation result
- `host_ready_not_repeated`
  - a supported host/runtime path is ready
  - repeated heavy-weight proof has not yet been established
- `supported_host_repeatability_visible`
  - repeated proof on a supported host is visible
  - broader customer-runtime evidence still remains open

## 4. Current Honest Result

On the current host, the honest result is now:

- `summary.repeatability_rung = "supported_host_repeatability_visible"`
- `first_smoke_decision.decision = "local_smoke_ready"`
- `supported_host_proof.visible = true`
- `supported_host_proof.repeat_runs = 2`
- `boundary_preconditions.required_memory_gb = 62.0`
- `boundary_preconditions.verdict = "fits"`
- `boundary_entry.visible = true`

because `owlmlx` now has:

- one supported candidate baseline on this host
- one original exact heavy-boundary blocker still frozen for:
  `/Users/yeemio/AI/Agent/models/Kimi-K2.5-3bit`
  at `122.0G > 116.0G`
- one selected budget-fit retarget specimen path:
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- two real repeat runs on the same selected path whose runtime-owned flows both
  complete:
  `gate -> load -> generate -> unload`
- default `~/.owlmlx` truth still selects `omlx-probe-venv`
- supported-host repeated heavy-weight proof is now visible on this exact path

## 5. What This Changes

Before this round, `owlmlx` had:

- specimen completeness gate
- first-smoke locality decision
- host-stable execution status

But it still lacked one runtime-owned answer to:

- whether heavy-weight repeatability is merely blocked locally
- whether one honest heavier boundary has entered on a supported host
- or whether repeated proof is actually visible

Now `owlmlx` owns that answer directly, and the current host is no longer
misreported as only `local_preconditions_incomplete` once one honest
budget-fit heavier boundary has already entered on the active retarget path.

The original Kimi blocker also remains more exact than the old broad-path
narrative:

- the root models directory may still contain unrelated `.aria2` residue
- the Kimi specimen path itself is complete
- the Kimi blocker is the selected heavy boundary budget mismatch, not stale
  download metadata

The current retarget result is now also exact:

- `gemma-4-31B-it` fits the current `116.0G` serving budget at `62.0G`
- one first heavy boundary entry is visible on the current host
- two repeat runs on the same selected path now also succeed on default
  `~/.owlmlx` truth
- repeated heavy-weight proof is now visible on the current host
- this still does not promote `owlmlx` beyond `early_formal_runtime`

## 6. What This Does Not Claim

It does not claim:

- customer-grade heavy-weight serving parity exists
- cache depth closure exists
- governance reached reference-grade residency parity

It only claims:

- `owlmlx` now has a runtime-owned heavy-weight repeatability status
- the current host now has a supported candidate baseline for heavier runtime
  validation
- the original Kimi over-budget blocker remains frozen exactly at
  `122.0G > 116.0G`
- one budget-fit heavy boundary is now entered on the current host through
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- supported-host repeated heavy-weight proof is now visible on that same
  selected path
- customer-runtime evidence and dominant-gap reselection can now carry this
  repeatability state exactly without inflating readiness claims
