# owlmlx Runtime Monitor And Test Launch Contract Prompt

> Status: ready-to-run executor prompt
> Updated: 2026-05-06
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Scope: runtime-owned monitor snapshot, test-run preflight/launch contract,
> and OwlOps consumption boundary

## Copy-Paste Prompt

```text
You are in /Users/yeemio/AI/gitrep/owlmlx.

Read these first:

1. AGENTS.md
2. docs/source-of-truth/runtime-monitor-test-console-contract.md
3. docs/source-of-truth/runtime-status-schema.md
4. docs/source-of-truth/public-surface.md
5. docs/source-of-truth/model-release-candidate-program.md
6. docs/handoff/owlmlx-model-rc-post-run-health-handoff-20260506.md

Goal:

Implement the first runtime-owned slice for the OwlOps Runtime Monitor + Test Console:

- normalized monitor snapshot contract
- read-only test-run preflight contract
- explicit run/audit/status shapes
- route scaffolding that returns honest `unsupported` or `unknown` where live launch/event streaming is not implemented yet
- fake-runtime tests that prove the shape and boundary behavior

Hard boundaries:

- Do not work in OwlOps UI.
- Do not kill or mutate listeners on 8001 or 8009.
- Do not run Qwen35, Gemma, DeepSeek, or other heavy models in parallel.
- For this first slice, do not run any heavy model unless the user explicitly asks for a live proof.
- Do not mark any mainline model as pass.
- Do not claim release-ready, production-ready, parity, replacement, equivalent, wins, beats, or matches.
- Do not use `git add .`.
- Preserve existing staged/dirty work. Inspect `git status --short` first and only touch files needed for this slice.
- Use `.venv/bin/python` for tests in this repo unless the repo-local environment proves otherwise.

Implementation target:

1. Add pure runtime-owned schemas/builders, naming can follow the existing repo style:
   - monitor snapshot envelope
   - monitor event envelope
   - test-run preflight request/result
   - test-run status/index row
   - test-run audit row

2. Add HTTP route scaffolding in the runtime server:
   - `GET /v1/runtime/monitor/snapshot`
   - `POST /v1/runtime/test-runs/preflight`
   - `GET /v1/runtime/test-runs`
   - `GET /v1/runtime/test-runs/{run_id}`
   - `POST /v1/runtime/test-runs`
   - `GET /v1/runtime/monitor/events`
   - `GET /v1/runtime/test-runs/{run_id}/events`
   - `POST /v1/runtime/test-runs/{run_id}/abort`

   In this first slice, it is acceptable for live launch, SSE, and abort to return structured `unsupported` payloads. Do not fake execution. The key is to freeze the runtime-owned shape and make OwlOps able to render honest unsupported/unknown states.

3. Snapshot composition must consume existing runtime truth, not invent it:
   - health/readiness
   - runtime status summary
   - backend detail
   - inventory
   - budget
   - generation gate
   - load failure
   - cooldown
   - host pressure cached sample
   - Model RC latest/history where configured

4. Preflight must be read-only and should include:
   - decision: `admit`, `defer`, `reject`, or `unknown`
   - reason
   - service_readiness
   - active_run_state
   - model_visibility
   - model_load_admission
   - host_pressure
   - serving_budget
   - generation_gate
   - estimated_memory_gb
   - selected_profile
   - would_write_evidence_to
   - required_operator_confirmation

5. Preserve clean-idle degraded semantics:
   - `readiness=degraded` can still be healthy when `ok=true`, `backend_error=null`, `active_model_id=null`, and `model_count=0`.
   - Tests must cover this so OwlOps does not render clean idle as unhealthy.

6. Test profiles to include in schema/config:
   - `qwen36-27b-decode`
   - `qwen36-35b-ttft-template`
   - `gemma-repetitive-output-template`
   - `post-run-health-gate`

7. Add tests:
   - fake app returns `/v1/runtime/monitor/snapshot` with contract/version, source metadata, clean-idle degraded semantics, and Model RC history summary when a ledger is configured
   - preflight rejects or defers when a run is active or generation gate is busy
   - preflight returns unknown/unsupported rather than guessing when a truth source is absent
   - live launch route returns structured `unsupported` until the launch worker is implemented
   - abort route returns structured `unsupported` or `not_found` without killing anything
   - route paths and payloads are covered in `tests/test_runtime_server.py` or a focused new test file

Verification:

Run the narrowest meaningful tests, for example:

`.venv/bin/python -m pytest -q tests/test_runtime_server.py -k 'monitor or test_run or model_release_candidate or healthz'`

If new pure schema modules are added, also run their focused tests and:

`.venv/bin/python -m py_compile <changed python files>`

Finally run:

`git diff --check -- <changed files>`

Deliverable summary:

- changed files
- route behavior implemented
- tests run and results
- any routes intentionally still `unsupported`
- whether 8066 live proof was skipped or run
- next slice recommendation: SSE/events worker, audited live launch worker, or first model optimization lane
```

## Coordinator Note

This prompt is intentionally contract-first. It should unblock OwlOps frontend
work without making the UI invent runtime state, while leaving heavy live model
runs for a later explicitly selected optimization lane.
