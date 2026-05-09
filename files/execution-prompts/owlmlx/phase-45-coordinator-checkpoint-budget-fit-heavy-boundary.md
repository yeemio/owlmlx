# owlmlx Phase 45 Coordinator Checkpoint: Budget-Fit Heavy Boundary

## Goal

Close out the fit-within-budget heavy-boundary retarget round without
inflating repeatability, replacement, or customer-ready claims.

Active goal contract:

- `files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`

## Why this checkpoint is needed now

The current host is no longer only at candidate-baseline truth, and this round
is no longer about whether a heavier boundary can fit at all.

This round already selected one honest budget-fit heavier target and entered it
successfully once on the current host, so the remaining question is now:

- does the loop stop honestly at `budget_fit_heavy_boundary_entered`, or
- does the coordinator authorize true repeated heavy-weight validation next?

## Current live truth

### Registry and host truth

- isolated validation registry truth
  - verified baseline file:
    `/tmp/owlmlx-phase45-fit-verified.json`
  - quarantine file:
    `/tmp/owlmlx-phase45-fit-unsafe.json`
  - selects `omlx-probe-venv`
  - `runtime_mlx_environment_readiness.py` returns `readiness = ready`
- default `~/.owlmlx` registry truth
  - `mlx-verified-python.json` includes `omlx-probe-venv`
  - `runtime_host_stable_execution_status.py` returns:
    - `summary.status = host_ready_for_runtime_validation`
    - `summary.ready = true`
    - `summary.preferred_execution_mode = default_metal`
- historical quarantine residue
  - `mlx-unsafe-python.json` still retains earlier unsafe entries
  - this remains historical context, not the active baseline truth

### Original exact blocker truth

- the original heavy-boundary blocker remains frozen in:
  - `docs/source-of-truth/phase45-current-host-heavy-boundary-budget-blocker.md`
- original blocked target:
  - `/Users/yeemio/AI/Agent/models/Kimi-K2.5-3bit`
- exact blocker:
  - `122.0G > 116.0G`
  - `error_code = memory_budget_exceeded`

### Selected retarget candidate truth

- selected budget-fit heavier target:
  - `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- specimen gate truth:
  - `exists = true`
  - `has_config_json = true`
  - `has_index_json = true`
  - `expected_shard_count = 2`
  - `shard_count = 2`
  - `blocked_reason = null`
- boundary preconditions:
  - `required_memory_gb = 62.0`
  - `serving_budget_gb = 116.0`
  - `verdict = fits`
  - `reason = loading 62.0G fits within budget: 62.0G projected of 116.0G budget (54.0G headroom)`

### First budget-fit heavy boundary check

- `runtime_large_weight_first_smoke.py` on the selected Gemma target returns:
  - gate `smoke_ready = true`
  - load `ok = true`
  - generate `ok = true`
  - unload `ok = true`
  - generated text: `OK. OK. OK. OK.`

### Higher-level runtime truth

- `runtime_heavy_weight_repeatability_status.py --boundary-entered`
  returns:
  - `repeatability_rung = budget_fit_heavy_boundary_entered`
  - `boundary_entry.visible = true`
  - `recommended_next_step = stop here and require coordinator authorization before repeated heavy-weight validation`
- `runtime_customer_runtime_evidence.py --heavy-boundary-entered`
  returns:
  - `evidence_label = early_formal_runtime`
  - `dominant_next_gap = host_stable_execution`
  - `recommended_next_step = one budget-fit heavy boundary is now entered on this host; stop here and require coordinator authorization before repeated heavy-weight validation`
- `runtime_dominant_gap_reselection.py --heavy-boundary-entered`
  returns:
  - `selected_gap = host_stable_execution`
  - `heavy_weight_runtime_repeatability.repeatability_rung = budget_fit_heavy_boundary_entered`

## What completed

- the current host remains a supported candidate baseline
- the original Kimi blocker remains frozen exactly rather than being rewritten
- one honest budget-fit heavier boundary target was selected on the same host
- one real heavy boundary entry is now visible on the current host

## What did not change

- this round did not establish `host_ready_not_repeated`
- this round did not establish repeated heavy-weight proof
- this round did not move `customer_runtime_evidence` beyond `early_formal_runtime`
- cache remains frozen at `structural_ingress_seam_introduced`
- governance remains closed locally but below reference-grade parity
- no parity, replacement-ready, or customer-ready claim is authorized

## Decision required from coordinator

Choose one of these:

### Path H1: Authorize repeated heavy-weight validation on the selected budget-fit target

Meaning:

- keep the current host as the supported candidate baseline
- keep cache/governance frozen
- start an explicitly authorized repeated heavy-weight round on
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`

### Path H2: Hold at `budget_fit_heavy_boundary_entered`

Meaning:

- freeze current Phase 45 mainline exactly here
- do not start repeated heavy-weight validation
- do not pretend one successful entry already equals repeatability

## Non-negotiable constraints

- Do not reopen cache beyond `structural_ingress_seam_introduced`
- Do not reopen governance micro-rounds
- Do not rewrite one successful heavy boundary entry as repeatability restored
- Do not claim parity, replacement-ready, or customer-ready

## Recommendation

Take this checkpoint with:

- `Coordinator verdict = budget_fit_heavy_boundary_entered`

Reason:

- the current host and default baseline truth are both green
- one honest heavier boundary now fits and has entered on this host
- repeated heavy-weight validation still requires explicit authorization
