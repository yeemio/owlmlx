# owlmlx Stabilization-3: Verified Baseline Resolution

> Status: active round prompt
> Updated: 2026-04-13
> Scope: runtime-only baseline resolution for local large-weight first smoke

## 1. Goal Contract

- `goal_id`: `owlmlx-stabilization-3-verified-baseline-resolution`
- `title`: Resolve whether this host can provide one runtime-owned verified MLX baseline

### Success Definition

This round succeeds only if one of these outcomes is reached honestly:

1. `owlmlx` establishes one verified-safe MLX baseline on this host:
   - registered through the runtime-owned baseline registry
   - reproducible through runtime-owned probe paths
   - sufficient to unblock large-weight first smoke gate for the same execution mode
2. `owlmlx` proves that this host currently cannot provide such a baseline and
   freezes a formal handoff decision:
   - local first smoke remains blocked
   - the next required step is another host or system image
   - the blocker is captured through runtime-owned evidence rather than ad-hoc shell claims

### Blocked Definition

This round is blocked only if:

- the current host evidence is internally contradictory and cannot be reduced by
  runtime-owned probes, or
- a required external dependency is needed to continue honestly

### Hard Rules

1. Stay inside `owlmlx`; do not modify `/Users/yeemio/AI/Agent`.
2. Do not claim MiniMax-M2.7 is incompatible unless the blocker is shown to be
   model-specific rather than host/import specific.
3. Do not promote manual shell success to verified truth unless `owlmlx` owns
   the same success through its runtime probes or baseline registry.
4. Do not add control-plane, dashboard, or product-shell work in this round.
5. Do not start performance or optimization work; this round is only about
   baseline resolution and first-smoke eligibility.

### Out of Scope

- operator UI
- release/readiness presentation above runtime layer
- benchmark work
- MiniMax quantization or optimization
- replacement verdict changes

## 2. Frozen Current Truth

- `MiniMax-M2.7` specimen path is complete:
  - `/Users/yeemio/AI/Agent/models/MiniMax-M2.7`
  - indexed shards: `125`
  - present shards: `125`
- `default_metal` is blocked on this host for known clean baselines
- `force_cpu` is tracked as a distinct execution mode
- current runtime-owned probe matrix still returns `-6` for `.runtime2-mlx`
  under `force_cpu`
- current repeated crash signature remains:
  - `NSRangeException`
  - `libmlx.dylib`
  - `mlx::core::metal::Device::Device()`
- current dominant question is frozen in `master-outline.md`:
  - can this host produce one verified-safe MLX baseline,
  - or must first smoke move to another host/system image

## 3. Dominant Gap

`owlmlx` still lacks a trustworthy runtime-owned decision about the local
baseline question.

More specifically:

- the host-level MLX blocker is well evidenced
- the specimen gate is already honest
- but the system still has not closed the final decision:
  - verified baseline on this host
  - or formal local-blocked / move-host handoff

## 4. Required Waves

### Wave 0 — Freeze

- restate the goal contract and frozen truth
- confirm the round stays inside `owlmlx`

### Wave 1 — Assess

- inspect the current mode-aware baseline registry and quarantine flow
- inspect current probe matrix and forensics contracts
- identify the smallest remaining ambiguity in local baseline promotion

### Wave 2 — Execute

Choose exactly one dominant objective:

- either make runtime-owned baseline promotion honest and reproducible for one
  usable mode
- or make the local-blocked / move-host decision explicit as a formal runtime
  contract and first-smoke handoff rule

### Wave 3 — Verify

Run targeted verification for all touched runtime assets.

Minimum expected checks:

- `tests/test_mlx_environment.py`
- any new or updated runtime-specific tests
- the relevant operator script(s) for:
  - environment readiness
  - blocker report
  - host forensics
  - first-smoke gate

### Wave 4 — Freeze Truth

- update source-of-truth docs that changed materially
- update `runtime-capability-matrix.md` if any capability claim changed
- update `master-outline.md` only if the dominant question or next step changed

## 5. Required Delivery Summary

The round summary must include:

- goal status
- dominant gap addressed
- decision: `continue | blocked | success`
- modified files
- checks run
- new or corrected runtime truth
- remaining truth gap
- next dominant gap
- why this round materially advances `owlmlx`

## 6. Honest Outcome Rules

Good outcomes:

- `verified baseline established for execution_mode = X`
- `local first smoke still blocked; move-host handoff frozen`

Bad outcomes:

- `probably still blocked`
- `manual shell success seems enough`
- `try another venv later`

