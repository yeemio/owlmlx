# owlmlx Technical Preview Serving Launcher Handoff

> Date: 2026-04-28
> Outcome: `owlmlx_technical_preview_serving_launcher_introduced`
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`

## 1. What Landed

This round introduced the first official side-by-side technical-preview
serving launcher for `owlmlx`.

New runtime factory:

- `owlmlx/runtime/technical_preview.py`
  - creates a real `RuntimeKernel(MlxLmSubprocessBackend(...))`
  - defaults child execution to the repo `.venv/bin/python`
  - resolves stable public `model_id` values to local paths under
    `OWLMLX_MODELS_ROOT`
  - preserves public `model_id` at the HTTP/runtime API boundary
  - mounts the existing `create_app(...)` public surface

New operator CLI:

- `scripts/runtime_technical_preview_server.py`
  - starts the technical-preview app through `uvicorn`
  - defaults to `127.0.0.1:8066`
  - defaults models root to `/Users/yeemio/AI/Agent/models`
  - does **not** stop or mutate legacy `oMLX` / router services

Backend extension:

- `MlxLmSubprocessBackend` now accepts optional `model_path_resolver`
  - default behavior is unchanged
  - the resolver is used only for child-runner `mlx_lm.load(...)` path
  - backend status and API results keep the public logical `model_id`

Public surface:

- `docs/source-of-truth/public-surface.md` now lists
  `owlmlx.runtime.technical_preview` and
  `scripts/runtime_technical_preview_server.py` as supported
  technical-preview serving surfaces.

## 2. Operator Command

Side-by-side startup command:

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
.venv/bin/python scripts/runtime_technical_preview_server.py \
  --host 127.0.0.1 \
  --port 8066 \
  --models-root /Users/yeemio/AI/Agent/models
```

Equivalent uvicorn factory form:

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
OWLMLX_MODELS_ROOT=/Users/yeemio/AI/Agent/models \
.venv/bin/python -m uvicorn \
  owlmlx.runtime.technical_preview:create_technical_preview_app \
  --factory \
  --host 127.0.0.1 \
  --port 8066
```

Do not use bare `python3`; on this host it resolves to Homebrew Python 3.14
without `mlx` / `mlx_lm`.

## 3. Live Probe Result

The launcher was run side-by-side on `127.0.0.1:8066`.

Observed:

- `GET /healthz` returned HTTP 200
  - `backend_name = "mlx-lm-subprocess"`
  - `ok = true`
  - `readiness = "degraded"` because no model was loaded yet
- `GET /v1/runtime/status` returned HTTP 200
  - `surface = "owlmlx.runtime.status"`
  - `backend.backend_name = "mlx-lm-subprocess"`
- `GET /v1/runtime/model-visibility` returned HTTP 200
  - `surface = "owlmlx.runtime.model_visibility"`
  - visible models on this host:
    - `Qwen3.6-27B`
    - `Qwen3.6-35B-A3B`
    - `gemma-4-31B-it`
    - `gpt-oss-120b-MXFP4-Q4`
- `GET /v1/models` returned HTTP 200

Cleanup:

- the preview server process was terminated
- `lsof -nP -iTCP:8066 -sTCP:LISTEN` showed no remaining listener

No model load or generation was executed in this round.

## 4. Tests Run

```text
.venv/bin/python -m pytest -q \
  tests/test_runtime_technical_preview_server.py \
  tests/test_public_surface_contract.py \
  tests/test_runtime_model_visibility.py
```

Result:

```text
19 passed
```

```text
.venv/bin/python -m pytest -q \
  tests/test_mlx_lm_subprocess_backend.py \
  tests/test_runtime_technical_preview_server.py
```

Result:

```text
53 passed
```

```text
.venv/bin/python -m pytest -q \
  tests/test_runtime_technical_preview_server.py \
  tests/test_public_surface_contract.py \
  tests/test_runtime_model_visibility.py \
  tests/test_runtime_server.py -k "model_visibility or runtime_status or healthz"
```

Result:

```text
6 passed, 54 deselected
```

`py_compile` passed for:

- `owlmlx/runtime/technical_preview.py`
- `owlmlx/runtime/mlx_lm_subprocess_backend.py`
- `owlmlx/runtime/server.py`
- `scripts/runtime_technical_preview_server.py`

`git diff --check` was clean.

## 5. Legacy Service State

Before this round, the local machine still had:

- legacy `oMLX serve` on `127.0.0.1:8001` (`python -m omlx.cli serve`)
- legacy `llm_router` on `:8009`

This round intentionally did not stop either process.

## 6. Next Cutover Gate

The next round may start owlmlx on `8066`, then run:

- `GET /healthz`
- `GET /v1/runtime/status`
- `GET /v1/runtime/model-visibility`
- `GET /v1/models`
- `POST /v1/load` for one visible model with an explicit `memory_gb`
- `POST /v1/generate` with `max_tokens` kept small

Only after that succeeds should the coordinator consider stopping legacy
`oMLX :8001` or retargeting OwlCoda / OwlOps / router clients.

This round does not claim production readiness, parity, replacement-grade
performance, or superiority over `oMLX` / `vMLX`.
