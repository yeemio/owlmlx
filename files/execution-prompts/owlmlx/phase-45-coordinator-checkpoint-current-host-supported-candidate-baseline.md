# owlmlx Phase 45 Coordinator Checkpoint: Current-Host Supported Candidate Baseline

## Goal

Close out current-host supported-candidate baseline establishment without
inflating heavy-weight or replacement claims.

Active goal contract:

- `files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`

## Why this checkpoint is needed now

The current host is no longer only at reentry verification.

It now has enough runtime-owned evidence to be treated as
`supported_host_candidate_baseline_established`, but the next step is still a
coordinator choice rather than an automatic jump into heavier validation.

## Current live truth

### Isolated validation registry truth

- `register_verified_mlx_baseline.py` can register
  `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/python` as
  `omlx-probe-venv`
- `runtime_mlx_environment_readiness.py` returns:
  - `readiness = ready`
  - `selected_label = omlx-probe-venv`

### Default `~/.owlmlx` registry truth

- `~/.owlmlx/mlx-verified-python.json` contains `omlx-probe-venv`
- `runtime_mlx_environment_readiness.py` returns:
  - `readiness = ready`
  - `selected_label = omlx-probe-venv`
- `runtime_host_stable_execution_status.py` returns:
  - `summary.status = host_ready_for_runtime_validation`
  - `summary.ready = true`
  - `summary.preferred_execution_mode = default_metal`

### Historical quarantine residue

- `~/.owlmlx/mlx-unsafe-python.json` still retains 6 unsafe entries
- host forensics still expose historical `NSRangeException` / `SIGABRT` /
  `mlx::core::metal::Device::Device()` crash reports
- that residue remains historical context, not the current blocked truth

### Candidate baseline smoke

- verified baseline imports `mlx.core` and `mlx_lm`
- minimal runtime-owned smoke succeeds:
  - `load_ok = true`
  - `generate_ok = true`
  - `model_id = fake-a`

### Higher-level runtime truth

- `runtime_customer_runtime_evidence.py`
  - `evidence_label = early_formal_runtime`
  - `dominant_next_gap = host_stable_execution`
  - `exact_external_blocker = null`
  - `recommended_next_step = current host candidate baseline is now established; proceed to stronger baseline validation / heavy-weight boundary check on this host and do not reopen cache widening or governance micro-rounds`
- `runtime_dominant_gap_reselection.py`
  - `selected_gap = host_stable_execution`
  - `rationale = supported-host baseline establishment remains dominant because the current host now has a supported candidate baseline while stronger baseline validation and heavy-weight boundary checks are still the next honest step, and cache remains intentionally frozen at the structural ingress seam`

## What completed

- the current host has moved beyond `reentry_admissible`
- baseline provenance is explicit
- isolated and default registry truth both select the same verified baseline
- the host-stable contract now says this host is ready for deeper runtime
  validation
- the runtime owns one minimal candidate-baseline smoke
- historical quarantine residue is preserved without being misreported as the
  current verdict

## What did not change

- `owlmlx` remains `early_formal_runtime`
- cache remains frozen at `structural_ingress_seam_introduced`
- governance remains below reference-grade parity even though the local policy
  branch is closed
- heavy-weight repeatability is not restored
- no replacement, parity, or customer-ready claim is authorized

## Decision required from coordinator

Choose one of these:

### Path C1: Authorize stronger baseline validation / heavy-weight boundary check on this host

Meaning:

- keep the current host as the supported candidate baseline
- start the next heavier runtime validation round on this machine
- do not reopen cache widening or governance micro-rounds

### Path C2: Hold at `supported_host_candidate_baseline_established`

Meaning:

- freeze current Phase 45 mainline at this checkpoint
- keep the candidate-baseline verdict
- stop before any heavier validation round begins

## Non-negotiable constraints

- Do not reopen cache beyond `structural_ingress_seam_introduced`
- Do not reopen governance micro-rounds
- Do not claim heavy-weight repeatability restored
- Do not upgrade `early_formal_runtime` to customer-ready or replacement-ready

## Recommendation

Take this checkpoint with:

- `Coordinator verdict = supported_host_candidate_baseline_established`

Reason:

- runtime-owned host truth, registry truth, and smoke truth now align on the
  current host
- remaining work is heavier validation, not candidate-baseline establishment
- the next step needs coordinator choice, not silent continuation
