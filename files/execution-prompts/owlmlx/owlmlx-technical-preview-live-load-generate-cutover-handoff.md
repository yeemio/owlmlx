# owlmlx Technical Preview Live Load/Generate Cutover Handoff

> Date: 2026-04-30
> Outcome: `owlmlx_technical_preview_live_load_generate_gate_passed`
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`

## 1. Verdict

The side-by-side `owlmlx` technical-preview serving gate passed on this host.

The preview server was started on `127.0.0.1:8066`, loaded
`gemma-4-31B-it`, generated a short response through the real
`mlx-lm-subprocess` child, unloaded the model, and released the port.

This does not stop or replace the legacy services yet. It proves the next
cutover step can move from "does owlmlx start?" to "can external clients be
retargeted to owlmlx and pass their probes?"

## 2. Narrow Fix Applied

The first live gate in this round loaded and unloaded successfully but failed
generation because this installed `mlx_lm` version does not accept
`temperature` as a direct `generate_step(...)` keyword.

Failed evidence:

- `files/evidence/owlmlx/technical-preview-cutover/20260430T025744Z/`
- failure message:
  `TypeError: generate_step() got an unexpected keyword argument 'temperature'`

Fix:

- `owlmlx/runtime/mlx_lm_runner.py`
  - added `_prepare_generation_params(...)`
  - converts API-facing sampling params such as `temperature`, `temp`,
    `top_p`, and `top_k` into `sampler=mlx_lm.sample_utils.make_sampler(...)`
  - applies the same adapter to non-stream, batch, message, and stream
    generation paths

Regression coverage:

- `tests/test_mlx_lm_runner_params.py`
  - verifies non-sampling params stay unchanged
  - verifies `temperature` no longer leaks into `generate_step`
  - verifies sampler-family params are consumed into a callable sampler

## 3. Passing Live Evidence

Fresh evidence directory:

- `files/evidence/owlmlx/technical-preview-cutover/20260430T030415Z/`

Command shape:

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
.venv/bin/python scripts/runtime_technical_preview_server.py \
  --host 127.0.0.1 \
  --port 8066 \
  --models-root /Users/yeemio/AI/Agent/models \
  --backend-timeout-s 900 \
  --log-level warning
```

Observed live result:

- `GET /healthz` returned HTTP 200
  - `backend_name = "mlx-lm-subprocess"`
  - `persistent_child = true`
  - `readiness = "degraded"` before model load
- `GET /v1/runtime/model-visibility` returned HTTP 200
  - visible models:
    - `Qwen3.6-27B`
    - `Qwen3.6-35B-A3B`
    - `gemma-4-31B-it`
    - `gpt-oss-120b-MXFP4-Q4`
- `POST /v1/load`
  - model: `gemma-4-31B-it`
  - status: HTTP 200
  - `ok = true`
  - duration: `7.5173s`
  - child pid: `34917`
  - runner path:
    `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- `POST /v1/generate`
  - prompt: `Reply with exactly OK.`
  - params: `{"max_tokens": 2, "temperature": 0.0}`
  - status: HTTP 200
  - `ok = true`
  - text: ` OK.`
  - duration: `3.1895s`
  - execution time: `3.1631s`
- `POST /v1/unload`
  - status: HTTP 200
  - `ok = true`

Cleanup:

- preview server was terminated
- `lsof -n -iTCP:8066 -sTCP:LISTEN` returned no listener

## 4. Legacy Services

Legacy services were intentionally left running:

- legacy `oMLX` service on `127.0.0.1:8001`
- legacy router on `:8009`

No `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent` files were edited.

## 5. Verification

```text
.venv/bin/python -m pytest -q \
  tests/test_mlx_lm_runner_params.py \
  tests/test_runtime_technical_preview_server.py
```

Result:

```text
6 passed, 2 warnings
```

```text
.venv/bin/python -m pytest -q \
  tests/test_mlx_lm_runner_params.py \
  tests/test_mlx_lm_subprocess_backend.py \
  tests/test_runtime_technical_preview_server.py
```

Result:

```text
56 passed, 2 warnings
```

```text
.venv/bin/python -m pytest -q \
  tests/test_public_surface_contract.py \
  tests/test_runtime_model_visibility.py \
  tests/test_runtime_server.py \
  -k "model_visibility or runtime_status or healthz or generate"
```

Result:

```text
10 passed, 47 deselected
```

`py_compile` passed for:

- `owlmlx/runtime/mlx_lm_runner.py`
- `owlmlx/runtime/mlx_lm_subprocess_backend.py`
- `owlmlx/runtime/technical_preview.py`
- `scripts/runtime_technical_preview_server.py`

## 6. Next Cutover Step

Do not stop `oMLX :8001` yet.

The next executable step is an external-client retarget probe:

- start `owlmlx` technical preview on `127.0.0.1:8066`
- point one consumer boundary at `8066` instead of the legacy service
- run that consumer's existing health/model/generate probe
- archive the result under `files/evidence/owlmlx/technical-preview-cutover/`

Only after that external-client probe passes should the coordinator schedule a
controlled shutdown of legacy `oMLX :8001`.

This handoff makes no release-ready, parity, replacement-grade performance, or
superiority claim against `oMLX` / `vMLX`.
