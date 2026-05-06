# owlmlx Model RC Supervised Admission Rerun And Post-Run Health Gate Handoff

> Status: handoff
> Updated: 2026-05-06
> Scope: one goal-driven loop slice after host-pressure / model-load-admission
> preflight became available

## 1. Outcome

`owlmlx_model_rc_supervised_admission_rerun_post_run_health_gate_introduced`

The loop advanced from static admission preflight to two serial live Model RC
runs, then narrowed the next runtime-owned gap: a Model RC row cannot be
considered clean when the load / generate / unload repeat loop succeeds but the
runtime is left with unhealthy backend state.

## 2. Live Runs

All heavy runs were serial. `8001` and `8009` were not killed.

### Qwen3.6-35B-A3B

Evidence directory:

`files/evidence/owlmlx/model-release-candidates/20260505T162118Z-qwen36-35b-a3b-supervised-admission-rerun`

Observed result:

- `verdict = needs_optimization`
- `failure_count = 0`
- `repeat_count = 2`
- `output_sanity_label = valid_text`
- `ttft_ms = 1763.931`
- `decode_tokens_per_second = 31.1`
- `peak_resident_set_bytes = 62626299904`
- post-run health clean: `active_model_id = null`, `backend_error = null`

### gemma-4-31B-it

Evidence directory:

`files/evidence/owlmlx/model-release-candidates/20260505T162236Z-gemma-4-31b-it-supervised-admission-rerun`

Observed result:

- `verdict = needs_optimization` in the generated record before this fix
- `failure_count = 0` in the generated record before this fix
- `repeat_count = 2`
- `output_sanity_label = reasoning_trace_truncated`
- `ttft_ms = 1906.926`
- `decode_tokens_per_second = 2.757`
- `peak_resident_set_bytes = 59347599360`
- post-run health not clean:
  `backend_error = "Expecting ':' delimiter: line 1 column 37 (char 36)"`

The Gemma row proves the runner needed a post-run health gate. The HTTP stream
artifacts are valid JSON and the unload responses are structured success, so
the saved evidence does not prove the raw offending child-transport line. The
honest conclusion is therefore `post_run_backend_unhealthy`, not a claimed root
cause.

## 3. Code Changes

- `scripts/runtime_model_release_candidate.py`
  - writes `post-run-healthz.json`
  - writes `post-run-runtime-status.json`
  - records `post_run_backend_unhealthy` when post-run health is not clean
  - increments `failure_count` and moves verdict to `blocked` when this happens
  - handles URL-level health probe failures as structured evidence instead of
    crashing without a record
- `owlmlx/runtime/mlx_lm_subprocess_backend.py`
  - records the shutdown exchange as the latest subprocess result
  - clears prior latched transport error after a normal successful unload when
    no models remain registered
  - does not clear force-unload / failed child cleanup failures

## 4. Verification

- `pytest -q tests/test_model_release_candidate_surface.py -q`:
  `30 passed`
- `pytest -q tests/test_mlx_lm_subprocess_backend.py -k 'successful_unload_clears_prior_latched_error or unload_stops_persistent_child or unload_clears_stale_registration_after_dead_child or classifies_metal_oom_child_loss'`:
  `4 passed, 51 deselected`
- `pytest -q tests/test_runtime_server.py -k 'healthz or model_release_candidate'`:
  `1 passed, 42 deselected`
- `python3 -m py_compile scripts/runtime_model_release_candidate.py owlmlx/runtime/mlx_lm_subprocess_backend.py`:
  success
- `git diff --check -- scripts/runtime_model_release_candidate.py owlmlx/runtime/mlx_lm_subprocess_backend.py tests/test_model_release_candidate_surface.py tests/test_mlx_lm_subprocess_backend.py`:
  clean

## 5. Live Service State

`8066` was restarted to pick up the new code. `8001` and `8009` were only
observed before / after and were not stopped.

Restart evidence:

`files/evidence/owlmlx/model-release-candidates/20260505T162923Z-post-run-health-gate-and-8066-restart`

Post-restart state:

- `healthz.ok = true`
- `backend_error = null`
- `active_model_id = null`
- `model_count = 0`
- `summary.backend_healthy = true`

The clean Qwen35 supervised record was appended to
`files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`.
The mounted 8066 history returned `9` records with the Qwen35 supervised row as
the latest record. The Gemma supervised row was not appended because it was
generated before the post-run health gate and left the backend unhealthy.

## 6. Next Dominant Gap

Do not run another large model until the next runner record proves that a dirty
post-run backend is recorded as `blocked / post_run_backend_unhealthy`.

Recommended next round:

1. Run a lightweight fake-server operator proof for the post-run health gate if
   a reviewer wants command-level evidence beyond pytest.
2. Re-run Gemma once under the updated runner only if 8066 remains clean and
   host pressure is normal.
3. If Gemma still leaves post-run backend unhealthy, inspect the child transport
   protocol around stream terminal records and shutdown exchange with raw-line
   capture; do not keep optimizing prompt/template while the backend health
   latch is dirty.

## 7. Non-Claims

- No release-ready claim.
- No parity / equivalent / replacement claim against `oMLX` or `vMLX`.
- No DeepSeek heavy run.
- No OwlOps UI work.
- No OwlCoda release entry work.
- No legacy `8001` / `8009` shutdown.
