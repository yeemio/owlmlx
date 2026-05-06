# owlmlx Model RC Host Pressure Preflight Runner

## Goal

Implement the next Model RC admission-observability slice: before any
supervised large-model `load -> generate -> unload` run, the runtime and runner
must capture explicit host-pressure and model-load-admission evidence.

## Required Scope

- Add an explicit runtime action:
  - `POST /v1/runtime/host-pressure-sample`
  - updates cached `/v1/runtime/status.host_pressure`
  - does not load a model
  - does not sample private Metal allocator state
  - does not run eviction
- Keep `GET /v1/runtime/model-load-admission` as projection-only.
- Update `scripts/runtime_model_release_candidate.py` so every repeat writes:
  - `repeat-XX-host-pressure-sample.json`
  - `repeat-XX-model-load-admission-before.json`
- If pre-load admission is `blocked`, stop before `/v1/load`.
- If admission is `unknown`, preserve the blocker rather than claiming safety.

## Hard Rules

- Do not run heavy model loads in this round.
- Do not kill `8001` or `8009`.
- Do not make release-ready / parity / replacement / production-grade claims.
- Do not hide missing host-pressure truth behind budget projection.
- Do not make `/v1/runtime/status` shell out implicitly.

## Verification

```bash
pytest -q tests/test_model_release_candidate_surface.py
pytest -q tests/test_runtime_server.py
pytest -q tests/test_public_surface_contract.py tests/test_model_load_admission.py tests/test_host_pressure.py tests/test_memory_pressure_contract.py
python3 -m py_compile owlmlx/runtime/kernel.py owlmlx/runtime/server.py scripts/runtime_model_release_candidate.py
git diff --check -- owlmlx/runtime/kernel.py owlmlx/runtime/server.py scripts/runtime_model_release_candidate.py tests/test_runtime_kernel.py tests/test_runtime_server.py tests/test_model_release_candidate_surface.py docs/source-of-truth/model-load-admission.md docs/source-of-truth/runtime-status-schema.md docs/source-of-truth/public-surface.md files/execution-prompts/owlmlx/owlmlx-model-load-admission-projection-handoff.md files/execution-prompts/owlmlx/owlmlx-model-rc-admission-observability-goal-contract.md files/execution-prompts/owlmlx/owlmlx-model-rc-host-pressure-preflight-runner.md
```

## Live Probe

Restart only `8066` if needed. Do not touch legacy `8001` / `8009`.

Probe:

```bash
curl -sS -X POST http://127.0.0.1:8066/v1/runtime/host-pressure-sample
curl -sS 'http://127.0.0.1:8066/v1/runtime/model-load-admission?model_id=Qwen3.6-35B-A3B'
curl -sS 'http://127.0.0.1:8066/v1/runtime/model-load-admission?model_id=gemma-4-31B-it'
```

Expected honest result: after sample, admission should be concrete
(`admit`, `warn`, or `blocked`) when visibility and peak-RSS evidence exist.
If it remains `unknown`, the exact missing signal must be preserved.
