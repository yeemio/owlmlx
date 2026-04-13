# owlmlx Stabilization-3: Verified Baseline Resolution

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only locality decision for large-weight first smoke

## 1. Purpose

Stabilization-3 closes the current dominant question from `master-outline.md`:

**Can this host provide one verified-safe MLX baseline for large-weight first
smoke, or must first smoke move to another host/system image?**

This round does not fix MLX on this machine. It freezes the honest runtime
decision about what happens next.

## 2. Owned Contract

`owlmlx/runtime/first_smoke_decision.py` now owns:

- `build_large_weight_first_smoke_decision(...)`
- `first_smoke_decision_to_dict(...)`

Operator entry:

- `scripts/runtime_large_weight_first_smoke_decision.py`

Contract:

- `surface = "owlmlx.large_weight_first_smoke_decision"`
- `version = "stabilization3"`

Stable sections:

- `summary`
- `default_metal_gate`
- `force_cpu_gate`
- `host_forensics`

## 3. Decision Semantics

Possible `summary.decision` values:

- `local_smoke_ready`
- `local_preconditions_incomplete`
- `move_host_recommended`
- `local_blocked_continue_forensics`

Interpretation:

- `local_smoke_ready`
  - one execution mode has a runtime-owned usable baseline
  - first smoke may proceed locally for that same mode
- `local_preconditions_incomplete`
  - specimen path or other local prerequisites are incomplete
  - fix local preparation before deciding anything about host handoff
- `move_host_recommended`
  - specimen is locally complete
  - no local verified-safe MLX baseline exists
  - current host forensics continue to show the machine-level MLX crash path
- `local_blocked_continue_forensics`
  - local readiness is still blocked
  - but the evidence is not yet strong enough to freeze a move-host handoff

## 4. Current Verified Result

Current result on this host for:

- specimen: `/Users/yeemio/AI/Agent/models/MiniMax-M2.7`
- known candidates included

is now:

- `summary.decision = "move_host_recommended"`
- `summary.smoke_ready = false`
- `summary.blocked_reason = "no verified-safe mlx baseline exists on this host"`
- `summary.recommended_next_step = "move large-weight first smoke to another host or system image"`

The evidence chain is:

- specimen path is complete:
  - indexed shards: `125`
  - present shards: `125`
  - specimen blocker: `null`
- `default_metal` gate remains blocked
- `force_cpu` gate also remains blocked
- host forensics continue to show repeated:
  - `NSRangeException`
  - `SIGABRT`
  - `mlx::core::metal::Device::Device()`

This closes the prior ambiguity. `owlmlx` no longer needs to keep asking
whether this host is probably close to local first smoke.

## 5. What This Proves

It proves:

- the blocker is no longer inside specimen completeness
- the blocker is no longer unresolved baseline bookkeeping
- the current host should not be treated as the immediate next place to run
  MiniMax first smoke

It does not prove:

- MiniMax-M2.7 is incompatible with `owlmlx`
- another host would fail the same way
- MLX conversion should be abandoned

## 6. Architectural Consequence

The next rational step is now off-host:

- select another host or system image
- establish one verified-safe MLX baseline there
- re-run the same runtime-owned specimen gate and first-smoke decision

The local machine remains useful for:

- blocker truth
- crash forensics
- runtime contract hardening

It is not the current candidate for first large-weight smoke.

