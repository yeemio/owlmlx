# Runtime Kernel MVP

> Status: authoritative
> Updated: 2026-04-11
> Milestone: Runtime-0

## 1. Purpose

Runtime-0 moves `owlmlx` from a truth derivation library into an executable
runtime kernel MVP.

This milestone does not make `owlmlx` production-ready. It proves that owlmlx
now has its own runtime control object, backend adapter boundary, HTTP entry,
and self-derived runtime status.

## 2. Runtime-0 Deliverables

| Deliverable | Implementation |
|---|---|
| Runtime control object | `owlmlx/runtime/kernel.py` — `RuntimeKernel` |
| Backend adapter boundary | `owlmlx/runtime/backends.py` — `RuntimeBackend` protocol |
| Stable test backend | `FakeBackend` |
| MLX-family adapter | `owlmlx/runtime/mlx_lm_backend.py` — lazy `mlx_lm` adapter |
| MLX subprocess adapter | `owlmlx/runtime/mlx_lm_subprocess_backend.py` — parent-safe child-process runner |
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
| `GET /v1/models` | Inventory, budget, backend state |
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

Direct `mlx_lm` import in the local venv currently initializes MLX/Metal and
can crash in non-runtime test contexts. This is why the in-process adapter is
lazy and mock-tested only. Runtime-1 adds `MlxLmSubprocessBackend`, which keeps
the parent runtime safe by executing `mlx_lm.load + mlx_lm.generate` inside a
child process.

Runtime-1 adds an explicit operator smoke script:

```bash
python scripts/runtime1_mlx_lm_smoke.py --model /path/to/small-mlx-model
```

This script is not part of pytest. It may initialize MLX/Metal and must remain
an explicit smoke until the local Metal import crash is resolved.

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
- `RuntimeKernel` can use `MlxLmBackend` under mock
- `MlxLmBackend` import preflight returns structured failure instead of
  importing `mlx_lm` in the parent process

## 8. Non-Claims

Runtime-0 does not claim:

- real local model load is verified
- real token generation is verified
- streaming output exists
- production HTTP serving is ready
- process lifecycle is implemented
- eviction/reclaim is implemented
- oMLX is fully replaced
- Kimi/Gemma/120B serving is migrated

## 9. Next Dominant Gap

Runtime-1 should verify a real MLX model load/generate path through
`MlxLmBackend` using a local model small enough for safe smoke testing.

Current Runtime-1 state:

- parent-safe subprocess runner exists
- clean-room environment `.runtime1-mlx` can import `mlx_lm 0.31.2`
- first real local smoke has passed on
  `/Users/yeemio/AI/Agent/models/gpt-oss-20b-MXFP4-Q4`
- real subprocess generate completed successfully in about `12.07s`

Runtime-1 now also has explicit environment selection discipline:

- default smoke probing only checks the current Python executable
- known MLX-oriented virtualenvs require explicit opt-in
- this avoids default diagnostics triggering repeated child-process aborts on
  environments already known to crash during `import mlx_lm`

Runtime-1 should not jump straight to Kimi 1T, 120B, or Gemma 31B. The next gap
is widening real-model coverage and turning subprocess success from one proven
path into a stable baseline.

The current environment truth is frozen separately in
`runtime1-environment-diagnostics.md`.
