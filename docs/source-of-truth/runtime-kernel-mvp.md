# Runtime Kernel MVP

> Status: authoritative
> Updated: 2026-04-11
> Milestone: Runtime-3

## 1. Purpose

Runtime-0 moved `owlmlx` from a truth derivation library into an executable
runtime kernel MVP. Runtime-3 extends that kernel into a persistent-child
runtime with explicit control surface, real streaming, and same-model benchmark
comparison against the old platform.

This milestone does not make `owlmlx` production-ready. It proves that owlmlx
now has its own runtime control object, backend adapter boundary, HTTP entry,
self-derived runtime status, and a persistent child session path for real MLX
models.

## 2. Runtime Deliverables

| Deliverable | Implementation |
|---|---|
| Runtime control object | `owlmlx/runtime/kernel.py` — `RuntimeKernel` |
| Backend adapter boundary | `owlmlx/runtime/backends.py` — `RuntimeBackend` protocol |
| Stable test backend | `FakeBackend` |
| MLX-family adapter | `owlmlx/runtime/mlx_lm_backend.py` — lazy `mlx_lm` adapter |
| MLX subprocess adapter | `owlmlx/runtime/mlx_lm_subprocess_backend.py` — parent-safe persistent child backend |
| HTTP entry | `owlmlx/runtime/server.py` |
| Runtime result contracts | `owlmlx/runtime/types.py` |

## 3. RuntimeKernel Responsibilities

`RuntimeKernel` owns:

- `load_model()`
- `generate()`
- `unload_model()`
- `status()`
- `status_dict()`
- active model tracking
- inventory construction from backend status
- memory-budget preflight before load
- GenerationGate discipline during generation
- runtime health snapshot derivation from self-owned state

This is executable runtime behavior, not schema extraction.

## 4. Truth Substrate Consumed

Runtime-0 consumes existing owlmlx truth modules directly:

| Module | RuntimeKernel use |
|---|---|
| `memory_budget.py` | load preflight and budget snapshot |
| `model_inventory.py` | loaded model inventory and health integration |
| `runtime_health.py` | runtime readiness/wait-tier/block reason |
| `serving.py` | `GenerationGate` serializes generation |
| `abort_recovery.py` | substrate state participates in health snapshot |

This closes the previous gap where owlmlx truth was mostly consumed by the
platform instead of owlmlx itself.

## 5. HTTP Surface

Runtime-0 exposes a minimal FastAPI app:

| Endpoint | Meaning |
|---|---|
| `GET /healthz` | Kernel-derived health snapshot |
| `POST /v1/load` | Load a model through RuntimeKernel |
| `POST /v1/generate` | Generate through RuntimeKernel and GenerationGate |
| `POST /v1/generate/stream` | Stream NDJSON events through RuntimeKernel |
| `GET /v1/models` | Inventory, budget, backend state |
| `GET /v1/runtime/status` | Full kernel-derived runtime snapshot |
| `POST /v1/runtime/restart` | Explicit restart of one loaded model |
| `POST /v1/unload` | Unload a model through RuntimeKernel |

The HTTP app does not own model state. It delegates to `RuntimeKernel`.

## 6. MLX-LM Adapter Boundary

`MlxLmBackend` is required in Runtime-0, but real model loading is not a
Runtime-0 blocker.

The adapter:

- lazily imports `mlx_lm`
- calls `mlx_lm.load(model_id)`
- calls `mlx_lm.generate(model, tokenizer, prompt=..., **kwargs)`
- reports loaded models through `BackendStatus.loaded_models`
- supports kernel load/generate/unload/status in mock tests

Direct `mlx_lm` import in the local venv can initialize MLX/Metal and
can crash in non-runtime test contexts. This is why the in-process adapter is
lazy and mock-tested only. Runtime-1 adds `MlxLmSubprocessBackend`, which keeps
the parent runtime safe by executing `mlx_lm` inside a child process.

Runtime-1 adds an explicit operator smoke script:

```bash
python scripts/runtime1_mlx_lm_smoke.py --model /path/to/small-mlx-model
```

This script is not part of pytest. It may initialize MLX/Metal and must remain
an explicit smoke until the local Metal import crash is resolved.

Runtime-2 changes the child behavior from one-shot execution to persistent
session lifecycle:

- `load` starts one child per loaded model
- `generate` reuses that child
- `unload` explicitly shuts that child down
- parent process still never imports `mlx_lm`

## 7. Verified Behavior

Runtime-0 tests prove:

- kernel can load a fake model
- kernel rejects over-budget load
- kernel counts already loaded memory
- generation before load fails with runtime error
- loaded fake model can generate completion
- generation is serialized by `GenerationGate`
- unload clears active model
- backend unhealthy state blocks readiness
- HTTP load/generate/models/unload roundtrip works
- HTTP load respects memory budget
- `MlxLmBackend` calls mlx-lm load/generate paths under mock
- `MlxLmSubprocessBackend` runs child-process generation through a JSON runner
- `MlxLmSubprocessBackend` can keep one persistent child alive across multiple
  generation requests
- `RuntimeKernel` can use `MlxLmBackend` under mock
- `MlxLmBackend` import preflight returns structured failure instead of
  importing `mlx_lm` in the parent process

## 8. Non-Claims

Runtime-0 does not claim:

- real local model load is verified
- real token generation is verified
- production HTTP serving is ready
- process lifecycle is implemented
- eviction/reclaim is implemented
- oMLX is fully replaced
- Kimi/Gemma/120B serving is migrated

## 9. Runtime-1 Baseline

- clean-room environment `.runtime1-mlx` can import `mlx_lm 0.31.2`
- one-shot real local smoke passed on:
  - `gpt-oss-20b-MXFP4-Q4` in about `12.07s`
  - `Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit` in about `12.66s`
  - `Qwen3.5-35B-A3B-4bit` in about `13.41s`

Runtime-1 also established explicit environment selection discipline:

- default smoke probing only checks the current Python executable
- known MLX-oriented virtualenvs require explicit opt-in
- this avoids default diagnostics triggering repeated child-process aborts on
  environments already known to crash during `import mlx_lm`

## 10. Runtime-2 Verified State

Runtime-2 is now the active kernel milestone. It has verified:

- persistent child lifecycle through `MlxLmSubprocessBackend`
- `load once -> generate many -> explicit unload`
- real local model reuse in the clean `.runtime1-mlx` environment
- child health probe through runner `ping`
- dead child restart on the next generation request when registration remains

Runtime-2 real local smoke results:

- `gpt-oss-20b-MXFP4-Q4`
  - `load` started one persistent child
  - `generate #1` reused that child in about `0.2438s`
  - `generate #2` reused the same child in about `0.1479s`
- `Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit`
  - `load` started one persistent child
  - `generate #1` reused that child in about `0.5539s`
  - `generate #2` reused the same child in about `0.4322s`

This closes the Runtime-1 one-shot performance bottleneck. The dominant gap is
no longer cold-start-per-request.

Runtime-2 hardening is now partially complete:

- child health probe is exposed through backend `status()`
- dead child restart policy exists at the backend layer
- steady-state benchmark tooling exists in `scripts/runtime2_steady_state_benchmark.py`

First steady-state benchmark baseline:

- `gpt-oss-20b-MXFP4-Q4`
  - `load_time_s`: about `1.4891s`
  - `warm_generate_mean_s`: about `0.1677s`
  - `warm_generate_median_s`: about `0.1571s`
  - `warm_generate_min_s`: about `0.1341s`
  - `warm_generate_max_s`: about `0.2448s`

The next dominant gap is Runtime-2 reliability hardening beyond the backend:
explicit restart semantics in the HTTP/runtime surface, persistent child SLOs,
and fair comparison benchmarks against the old platform.

The benchmark truth is frozen separately in
`runtime2-benchmark-baseline.md`.

Runtime-3 is now complete above that backend baseline:

- explicit restart is exposed at `POST /v1/runtime/restart`
- full runtime snapshot is exposed at `GET /v1/runtime/status`
- serialized concurrent serving truth is frozen in
  `runtime3-serving-surface.md`
- streamed generation is exposed at `POST /v1/generate/stream`
- real streamed token delivery is frozen in `runtime3-benchmark-and-streaming.md`
- same-model benchmark comparison against the old platform is frozen in
  `runtime3-benchmark-and-streaming.md`

The current environment truth is frozen separately in
`runtime1-environment-diagnostics.md`.
