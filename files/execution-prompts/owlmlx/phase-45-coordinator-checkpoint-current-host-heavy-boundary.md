# owlmlx Phase 45 Coordinator Checkpoint: Current-Host Heavy Boundary

## Goal

Close out one stronger baseline validation / heavy-weight boundary round on the
current host without inflating repeatability or replacement claims.

Active goal contract:

- `files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`

## Why this checkpoint is needed now

The current host is no longer only at candidate-baseline truth.

This round already tested one exact heavy boundary on the selected specimen
path, so the remaining question is no longer "can this host reenter?" It is:

- does the current host reach `host_ready_not_repeated`, or
- does the selected heavy boundary remain exact-blocked?

## Current live truth

### Host and baseline truth

- `runtime_host_stable_execution_status.py`
  - `summary.status = host_ready_for_runtime_validation`
  - `summary.ready = true`
  - `summary.preferred_execution_mode = default_metal`
- default `~/.owlmlx` registry still selects:
  - `omlx-probe-venv`

### Selected heavy specimen truth

- active specimen path:
  - `/Users/yeemio/AI/Agent/models/Kimi-K2.5-3bit`
- specimen gate truth:
  - `exists = true`
  - `has_config_json = true`
  - `expected_shard_count = 91`
  - `shard_count = 91`
  - `blocked_reason = null`
- note:
  - the broad root path `/Users/yeemio/AI/Agent/models` still carries unrelated
    `.aria2` residue
  - that root-path residue is not the active selected specimen truth for this
    round

### Stronger baseline / heavy-boundary truth

- `runtime_heavy_weight_repeatability_status.py --specimen-path /Users/yeemio/AI/Agent/models/Kimi-K2.5-3bit --boundary-memory-gb 122`
  returns:
  - `repeatability_rung = local_preconditions_incomplete`
  - `first_smoke_decision.decision = local_smoke_ready`
  - `boundary_preconditions.required_memory_gb = 122.0`
  - `boundary_preconditions.verdict = exceeds`
  - `boundary_preconditions.reason = loading 122.0G would exceed serving budget: 0.0G loaded + 122.0G requested = 122.0G > 116.0G limit`

### First heavy boundary check

- `runtime_large_weight_first_smoke.py` on the same specimen and `--memory-gb 122`
  returns:
  - gate `smoke_ready = true`
  - load `ok = false`
  - `error_code = memory_budget_exceeded`
  - exact blocker matches the repeatability surface:
    `122.0G > 116.0G`

### Higher-level runtime truth

- `runtime_customer_runtime_evidence.py`
  - `evidence_label = early_formal_runtime`
  - `dominant_next_gap = host_stable_execution`
  - `exact_external_blocker = null`
  - `recommended_next_step = freeze the selected heavy-weight boundary blocker exact on this host and do not reopen cache widening or governance micro-rounds`
- `runtime_dominant_gap_reselection.py`
  - `selected_gap = host_stable_execution`
  - `heavy_weight_runtime_repeatability.repeatability_rung = local_preconditions_incomplete`

## What completed

- the current host remains a supported candidate baseline
- the selected Kimi specimen path is no longer falsely blocked by stale root
  download metadata
- one real heavy boundary check was attempted on the current host
- the remaining blocker is now runtime-owned and exact:
  `memory_budget_exceeded`

## What did not change

- this round did not establish `host_ready_not_repeated`
- this round did not establish repeated heavy-weight proof
- cache remains frozen at `structural_ingress_seam_introduced`
- governance remains closed locally but below reference-grade parity
- no parity, replacement-ready, or customer-ready claim is authorized

## Decision required from coordinator

Choose one of these:

### Path H1: Authorize a fitting heavy-boundary target or precondition set on this host

Meaning:

- keep the current host as the supported candidate baseline
- do not reopen cache/governance
- rerun the heavy-boundary round only with a specimen / memory target that can
  fit inside the current host serving budget

### Path H2: Hold at `boundary_check_still_preconditions_blocked`

Meaning:

- freeze current Phase 45 mainline exactly here
- do not start repeated heavy-weight validation
- do not pretend the current Kimi heavy boundary already entered

## Non-negotiable constraints

- Do not reopen cache beyond `structural_ingress_seam_introduced`
- Do not reopen governance micro-rounds
- Do not rewrite one failed heavy boundary check as repeatability restored
- Do not claim parity, replacement-ready, or customer-ready

## Recommendation

Take this checkpoint with:

- `Coordinator verdict = boundary_check_still_preconditions_blocked`

Reason:

- host truth and specimen-gate truth are both green
- the first real heavy boundary now fails for one exact runtime-owned reason:
  serving budget
- repeated heavy-weight validation is not honest until that blocker changes
