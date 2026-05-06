# owlmlx Metal OOM Subprocess Ghost-State Recovery Handoff

> Date: 2026-05-05
> Outcome label: `owlmlx_metal_oom_subprocess_ghost_state_recovery_introduced`
> Scope: clear stale subprocess registrations after child-loss failures so
> `active_model_id` does not remain stuck on a dead model.

## 1. Triggering Evidence

The Qwen3.6-35B-A3B HTTP Model RC baseline left `8066` in a blocked ghost state:

- `backend.detail.last_subprocess.stderr` contained a Metal command-buffer
  insufficient-memory failure.
- `backend.detail.children` was empty.
- `backend.loaded_models` still included `Qwen3.6-35B-A3B`.
- `active_model_id` still pointed at `Qwen3.6-35B-A3B`.
- `/v1/unload` returned `model_not_loaded`, so the kernel could not clear the
  active model.

## 2. Runtime Change

`MlxLmSubprocessBackend.unload()` now treats `session missing but registration
exists` as a stale subprocess registration cleanup:

- removes the stale registration
- removes restart accounting for that model
- returns `UnloadResult(ok=True)`
- exposes `detail.stale_registration_cleared = true`
- clears backend `last_error` once no dead registrations remain

`MlxLmSubprocessBackend.status()` now exposes:

- `backend.detail.dead_registered_models`
- `healthy = false` whenever a registered model has no live child session

## 3. Kernel Effect

Because stale cleanup returns `ok=True`, `RuntimeKernel.unload_model()` follows
the existing successful-unload path and clears `active_model_id` when the ghost
model was active.

## 4. What This Does Not Claim

- It does not prevent Metal OOM.
- It does not add memory/Metal cooldown admission.
- It does not restart or kill legacy listeners.
- It does not claim a model is ready for user-facing release.

## 5. Verification

```bash
.venv/bin/python -m pytest -q tests/test_mlx_lm_subprocess_backend.py -k "dead_child or stale_registration or dead_subprocess_registration"
.venv/bin/python -m pytest -q tests/test_mlx_lm_subprocess_backend.py
.venv/bin/python -m pytest -q tests/test_runtime_kernel.py -k "unload or restart or status_dict"
.venv/bin/python -m pytest -q tests/test_runtime_server.py -k "unload or runtime_status or healthz"
.venv/bin/python -m py_compile owlmlx/runtime/mlx_lm_subprocess_backend.py
```

Observed results:

- targeted subprocess recovery: `5 passed, 47 deselected`
- full subprocess backend: `54 passed` after the follow-up cooldown tests were added
- runtime kernel focused: `12 passed, 13 deselected`
- runtime server focused: `4 passed, 37 deselected`
- py_compile: passed

## 6. Remaining Gap

The next narrow gap is a memory/Metal cooldown admission contract. This handoff
only closes the ghost-state recovery defect after a child-loss failure; it does
not prevent the next large-model load from hitting Metal high-watermark
pressure.
