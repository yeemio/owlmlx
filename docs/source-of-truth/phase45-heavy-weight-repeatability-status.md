# owlmlx Phase 45: Heavy-Weight Runtime Repeatability Status

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only heavy-weight repeatability for replacement-grade alignment

## 1. Purpose

This document advances `heavy_weight_runtime_repeatability` from a specimen
staging narrative into a runtime-owned status contract.

The question it answers is:

**Is heavy-weight repeatability locally blocked, merely host-ready, or actually
visible on a supported host?**

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

## 3. Repeatability Rungs

Current `summary.repeatability_rung` values:

- `local_blocked`
- `local_preconditions_incomplete`
- `host_ready_not_repeated`
- `supported_host_repeatability_visible`

Interpretation:

- `local_blocked`
  - the current host is not a valid heavy-weight repeatability candidate
- `local_preconditions_incomplete`
  - specimen prerequisites are incomplete before repeatability validation can begin
- `host_ready_not_repeated`
  - a supported host/runtime path is ready
  - repeated heavy-weight proof has not yet been established
- `supported_host_repeatability_visible`
  - repeated proof on a supported host is visible
  - broader customer-runtime evidence still remains open

## 4. Current Honest Result

On the current host, the honest result remains:

- `summary.repeatability_rung = "local_blocked"`

because `owlmlx` still has:

- a frozen host-level blocker on this machine
- no supported-host repeated heavy-weight proof yet

## 5. What This Changes

Before this round, `owlmlx` had:

- specimen completeness gate
- first-smoke locality decision
- host-stable execution status

But it still lacked one runtime-owned answer to:

- whether heavy-weight repeatability is merely blocked locally
- or actually visible on a supported host

Now `owlmlx` owns that answer directly.

## 6. What This Does Not Claim

It does not claim:

- heavy-weight repeatability is proven on the current host
- a supported host has already been supplied
- customer-grade heavy-weight serving parity exists

It only claims:

- `owlmlx` now has a runtime-owned heavy-weight repeatability status
- the current external blocker can be frozen exactly
- the next locally reducible gap can move to broader customer runtime evidence
