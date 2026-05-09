# owlmlx Phase 45 Coordinator Checkpoint: Narrow Repeated Heavy-Weight Validation

## Goal

Close out the authorized narrow repeated heavy-weight validation round without
inflating parity, replacement, or customer-ready claims.

Active goal contract:

- `files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`

## Why this checkpoint is needed now

The loop is no longer waiting on authorization to try repeated validation.

That round has now actually been run on the selected budget-fit path under the
default `~/.owlmlx` registry truth, so the remaining question is no longer:

- can the current host reach a repeated-proof attempt?

It is now:

- has supported-host repeated heavy-weight proof become visible on this exact
  selected path, and
- which frozen branch should coordinator reopen next, if any?

## Current live truth

### Default baseline truth

- default `~/.owlmlx` registry still selects:
  - `omlx-probe-venv`
- `runtime_mlx_environment_readiness.py --include-known-venvs` returns:
  - `readiness = ready`
  - `selected_label = omlx-probe-venv`
- `runtime_host_stable_execution_status.py --include-known-venvs` returns:
  - `summary.status = host_ready_for_runtime_validation`
  - `summary.ready = true`
  - `summary.preferred_execution_mode = default_metal`

### Historical quarantine residue

- `~/.owlmlx/mlx-unsafe-python.json` still retains 6 unsafe entries
- host forensics still show historical `NSRangeException` / `SIGABRT`
  Metal-init crashes
- those remain historical context, not the active baseline blocker truth

### Original exact blocker truth

- the original Kimi heavy-boundary blocker remains frozen in:
  - `docs/source-of-truth/phase45-current-host-heavy-boundary-budget-blocker.md`
- original blocked target:
  - `/Users/yeemio/AI/Agent/models/Kimi-K2.5-3bit`
- exact blocker:
  - `122.0G > 116.0G`
  - `error_code = memory_budget_exceeded`

### Selected repeated-validation target truth

- selected path:
  - `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- selected boundary:
  - `62.0G <= 116.0G`
- specimen gate remains green:
  - `exists = true`
  - `has_config_json = true`
  - `has_index_json = true`
  - `expected_shard_count = 2`
  - `shard_count = 2`
  - `blocked_reason = null`

### Repeat run outcomes

- repeat run 1 on default `~/.owlmlx` truth:
  - gate `smoke_ready = true`
  - load `ok = true`
  - generate `ok = true`
  - unload `ok = true`
  - generated text: `OK. OK. OK. OK.`
- repeat run 2 on default `~/.owlmlx` truth:
  - gate `smoke_ready = true`
  - load `ok = true`
  - generate `ok = true`
  - unload `ok = true`
  - generated text: `OK. OK. OK. OK.`

### Higher-level runtime truth

- `runtime_heavy_weight_repeatability_status.py` returns:
  - `repeatability_rung = supported_host_repeatability_visible`
  - `supported_host_proof.visible = true`
  - `supported_host_proof.repeat_runs = 2`
- `runtime_customer_runtime_evidence.py` returns:
  - `evidence_label = early_formal_runtime`
  - `dominant_next_gap = cache_scheduler_depth`
  - `exact_external_blocker = null`
  - `recommended_next_step = freeze supported-host repeated heavy-weight proof exact and take a fresh coordinator checkpoint before reopening cache/governance`
- `runtime_dominant_gap_reselection.py` returns:
  - `selected_gap = cache_scheduler_depth`
  - `heavy_weight_runtime_repeatability.repeatability_rung = supported_host_repeatability_visible`

## What completed

- the current host remains a supported candidate baseline
- the selected budget-fit Gemma path now has supported-host repeated
  heavy-weight proof visible under default `~/.owlmlx` truth
- the original Kimi over-budget blocker remains frozen exactly rather than
  being rewritten
- the active dominant gap has now moved from `host_stable_execution` to
  `cache_scheduler_depth`

## What did not change

- this round did not reopen cache beyond `structural_ingress_seam_introduced`
- this round did not reopen governance micro-rounds
- this round did not move `customer_runtime_evidence` beyond
  `early_formal_runtime`
- this round did not authorize parity, replacement-ready, or customer-ready
  claims

## Decision required from coordinator

Choose one of these:

### Path C1: Reopen `cache_scheduler_depth` as the next exact branch

Meaning:

- keep supported-host repeated proof frozen exact
- do not reopen governance
- start from the existing structural ingress seam and scheduler backlog truth

### Path C2: Hold at `supported_host_repeatability_visible`

Meaning:

- freeze current Phase 45 mainline exactly here
- do not reopen cache/governance yet
- preserve this as the current strongest supported-host proof checkpoint

## Non-negotiable constraints

- Do not reopen governance micro-rounds
- Do not rewrite repeated proof visible into parity or replacement-ready
- Do not substitute isolated `/tmp` registry truth for the default
  `~/.owlmlx` registry verdict
- Do not claim customer-ready posture from this checkpoint

## Recommendation

Take this checkpoint with:

- `Coordinator verdict = supported_host_repeatability_visible`

Reason:

- repeated proof is now visible on the selected default-registry path
- the current host branch is no longer the active governing blocker
- the next exact local branch is now `cache_scheduler_depth`
