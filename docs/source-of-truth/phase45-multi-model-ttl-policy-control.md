# owlmlx Phase 45: Multi-Model TTL Policy Control

> Status: authoritative
> Updated: 2026-04-16
> Scope: runtime-only TTL policy control for multi-model governance

## 1. Purpose

This document advances the governance fallback branch by adding one more real
runtime-owned policy control.

The question it answers is:

**Does `owlmlx` now own a real TTL policy on the runtime path, or is TTL still
only a narrative gap?**

## 2. Owned Contract

`owlmlx/multi_model_ttl_policy_control.py` now owns:

- `build_multi_model_ttl_policy_control(...)`
- `multi_model_ttl_policy_control_to_dict(...)`

Operator entry:

- `scripts/runtime_multi_model_ttl_policy_control.py`

Contract:

- `surface = "owlmlx.multi_model_ttl_policy_control"`
- `version = "phase45"`

Stable sections:

- `summary`
- `ttl_policy`
- `policy_progress`

## 3. What RuntimeKernel Now Owns

`RuntimeKernel` now owns:

- `set_model_ttl(model_id, ttl_seconds)`
- `clear_model_ttl(model_id)`
- `sweep_expired_models()`

It also owns the required bookkeeping for:

- per-model TTL configuration
- last-touch activity updates on load/generate/restart
- explicit expired-model sweep on the runtime-owned path
- pinned-expiry skip semantics

## 4. Current Honest Result

The current honest result is:

- `summary.control_rung = "control_implemented"`

because:

- TTL policy is present on the runtime-owned path
- explicit expiry sweep is visible
- expired pinned models remain blocked rather than silently unloaded

The remaining governance policy blocker is now:

- `eviction-history governance`

## 5. What This Does Not Claim

It does not claim:

- background TTL daemon behavior
- backend-native TTL
- eviction-history governance
- multi-model governance parity with `oMLX` / `vMLX`

It only claims:

- `owlmlx` now owns one more real lifecycle policy control locally
- the governance fallback branch has shrunk from `pinning + TTL + eviction`
  to `eviction-history governance only`
