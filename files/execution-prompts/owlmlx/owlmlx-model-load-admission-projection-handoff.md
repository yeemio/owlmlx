# owlmlx Model Load Admission Projection Handoff

> Date: 2026-05-05
> Outcome: `owlmlx_model_load_admission_projection_introduced`
> Scope: model-specific load-admission projection for OwlOps optimization
> observability; no live model load, no private Metal oracle, no eviction.

## 1. What Landed

- New `owlmlx.model_load_admission` runtime-owned surface.
- New HTTP route: `GET /v1/runtime/model-load-admission`.
- Optional query: `model_id=<id>`.
- New explicit sampling route: `POST /v1/runtime/host-pressure-sample`.
- The surface combines:
  - runtime budget headroom
  - runtime model visibility
  - cached host-pressure sample
  - Metal-OOM cooldown / stale registration barriers
  - latest Model RC `peak_resident_set_bytes`
  - resolved model profile id / family

## 2. Decision Vocabulary

Admission decisions:

- `admit`
- `warn`
- `blocked`
- `already_loaded`
- `unknown`

Budget projections:

- `fits`
- `fits_warning`
- `exceeds`
- `already_loaded`
- `unknown`

## 3. Honest Boundary

This is a projection surface. It does not:

- load a model
- sample private Metal allocator or command-queue pressure
- run pressure-ranked eviction
- restart or quarantine workers
- claim application readiness

If host pressure has not been sampled, `admission_decision` remains `unknown`
even when `budget_projection` is `fits` or `fits_warning`.

The Model RC runner now calls the explicit sampler before each repeat load and
archives:

- `repeat-XX-host-pressure-sample.json`
- `repeat-XX-model-load-admission-before.json`

If model-load admission is `blocked`, the runner stops before `/v1/load`.

## 4. Verification

```bash
pytest -q tests/test_model_load_admission.py
pytest -q tests/test_runtime_server.py -k "model_load_admission or model_release_candidate or runtime_status"
pytest -q tests/test_public_surface_contract.py
python3 -m py_compile owlmlx/model_load_admission.py owlmlx/runtime/server.py
git diff --check -- owlmlx/model_load_admission.py owlmlx/runtime/server.py tests/test_model_load_admission.py tests/test_runtime_server.py docs/source-of-truth/model-load-admission.md docs/source-of-truth/master-outline.md docs/source-of-truth/public-surface.md docs/source-of-truth/runtime-status-schema.md files/execution-prompts/owlmlx/owlmlx-model-load-admission-projection-handoff.md
```

## 5. Next Gap

OwlOps can now consume `model-load-admission` alongside Model RC v2 records.
The next runtime-side gap is improving the admission inputs: per-model peak RSS
should be refreshed after optimization runs, and host-pressure samples should
be captured immediately before supervised large-model load attempts.
