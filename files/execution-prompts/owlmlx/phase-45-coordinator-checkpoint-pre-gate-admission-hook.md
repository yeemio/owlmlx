# owlmlx Phase 45 Coordinator Checkpoint: Pre-Gate Admission Hook Decision

## Goal

Continue `owlmlx` toward supported-host runtime substrate closure without
inflating replacement claims.

Active goal contract:

- `files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`

## Why this checkpoint is needed now

The local exactness chain for `cache_scheduler_depth` has been reduced far
enough that the next step is no longer another useful runtime-owned
decomposition round.

The remaining cache blocker is now implementation-class:

- `cache_scheduler_depth -> cache_pre_gate_admission_window_seam`
- live closure level:
  - `pre_gate_admission_window_seam_exact`
- live contract surface:
  - `owlmlx.cache_pre_gate_admission_window_seam`

Current honest result:

- request aggregation remains the active cache subchain
- the active seam is now the missing bounded pre-gate admission hook before
  whole-request gate claim
- child exchange and stream hold remain secondary
- TurboQuant remains exact-but-secondary

This is the point where continued exactness slicing has diminishing value.
The next meaningful move is a structural runtime decision.

## Current frozen truth

Live customer ledger still says:

- `dominant_next_gap = cache_scheduler_depth`
- `evidence_label = early_formal_runtime`

Heavy-weight runtime remains externally blocked:

- supported host / system image
- one verified-safe MLX baseline

Governance remains policy-grade exact:

- `pinning`
- `ttl_policy`
- `eviction_history_governance`

So the local decision is specifically about cache/scheduler direction, not
about replacement verdict inflation.

## Decision required from coordinator

Choose one of these two paths.

### Path A: Authorize real pre-gate admission-hook implementation

Meaning:

- start actual runtime work to introduce one bounded pre-gate admission
  hook/buffer before whole-request gate claim
- keep all already-frozen post-claim serial safety invariants intact
- do not treat this as parity; treat it as a structural runtime experiment

This path is justified if the team wants `cache_scheduler_depth` to remain the
dominant local gap.

### Path B: Stop cache exactness here and switch dominant gap

Meaning:

- freeze the current cache branch at `pre_gate_admission_window_seam_exact`
- stop further cache micro-decomposition
- switch active loop priority to one of:
  - `supported_host_baseline_establishment`
  - `multi_model_lifecycle_governance`
  - `heavy_weight_runtime_repeatability`

This path is justified if the team judges pre-gate admission-hook work too
structural or too risky for the current loop.

## Non-negotiable constraints if Path A is chosen

Any implementation round must preserve:

- no bypass of whole-request gate claim
- no post-claim request reordering
- no weakening of:
  - `max_concurrent_1_after_gate_claim`
  - `ticketed_fifo_after_gate_claim`
  - `serial_safety_validated_only_after_gate_claim`

And it must still keep:

- child exchange one-request-at-a-time truth honest
- stream hold truth honest
- TurboQuant secondary on this branch

## Recommendation

My recommendation is:

- take this checkpoint now
- do not continue cache exactness micro-rounds without coordinator choice

Reason:

- the next step is no longer “discover the blocker”
- the blocker is already exact
- the next step is “authorize or defer a structural runtime implementation”

## Minimal review entrypoints

- `docs/source-of-truth/master-outline.md`
- `files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`
- `owlmlx/customer_runtime_evidence.py`
- `owlmlx/cache_pre_gate_admission_window_seam.py`
- `scripts/runtime_customer_runtime_evidence.py`
- `scripts/runtime_cache_pre_gate_admission_window_seam.py`
