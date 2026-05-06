# owlmlx Metal OOM Memory-Pressure Cooldown Admission Handoff

> Date: 2026-05-05
> Outcome label: `owlmlx_metal_oom_memory_pressure_cooldown_admission_introduced`
> Scope: block new model loads for a bounded cooldown window after
> runtime-owned Metal insufficient-memory child-loss evidence.

## 1. Triggering Gap

The ghost-state fix clears stale subprocess registrations after child loss, but
it does not prevent an immediate reload after a Metal high-watermark failure.
The Qwen3.6-35B-A3B incident showed the missing second layer:

- large direct baselines pushed macOS/Metal memory into a high-watermark state
- owlmlx HTTP Qwen35 then hit Metal insufficient-memory child loss
- without a cooldown admission barrier, the next heavy load could repeat the
  same failure immediately after cleanup

## 2. Runtime Change

`MlxLmSubprocessBackend.status()` now classifies the last subprocess failure:

- `metal_oom`
- `broken_pipe_child_lost`
- `child_lost_no_output`
- `child_lost`
- `backend_error`

`RuntimeKernel.load_model()` now performs two preflight checks before budget
preflight:

1. `dead_registered_models` recovery barrier
   - rejects new loads until stale subprocess registrations are unloaded
2. Metal-OOM cooldown barrier
   - if backend status carries `last_failure_class = "metal_oom"`, the kernel
     starts a bounded cooldown window
   - new loads return `RuntimeErrorCode.backend_error` with
     `detail.memory_pressure_cooldown`
   - the same failure fingerprint does not extend the cooldown repeatedly

Current cooldown policy:

- `policy = "metal_oom_child_loss_cooldown"`
- duration: `120s`

## 3. Observable Status

`/v1/runtime/status` now includes diagnostic section:

- `memory_pressure_cooldown.active`
- `memory_pressure_cooldown.reason_code`
- `memory_pressure_cooldown.reason_message`
- `memory_pressure_cooldown.remaining_s`
- `memory_pressure_cooldown.cooldown_until_s`
- `memory_pressure_cooldown.policy`

`memory_pressure_contract` now recognizes:

- `pressure_classification = "cooldown_barrier"`
- `reason.code = "metal_oom_cooldown_active"`
- `policy_boundaries.runtime_owned_metal_oom_cooldown = true`

## 4. What This Does Not Claim

- It does not predict Metal OOM before the first failure.
- It does not read private Metal driver pressure counters.
- It does not rank eviction victims.
- It does not implement automatic restart loops.
- It does not change legacy `8001` / `8009` services.

## 5. Verification

```bash
.venv/bin/python -m pytest -q tests/test_mlx_lm_subprocess_backend.py -k "metal_oom or cooldown or stale_registration"
.venv/bin/python -m pytest -q tests/test_memory_pressure_contract.py
.venv/bin/python -m pytest -q tests/test_runtime_kernel.py -k "unload or restart or status_dict"
.venv/bin/python -m pytest -q tests/test_runtime_server.py -k "unload or runtime_status or healthz or memory_pressure_contract"
.venv/bin/python -m py_compile owlmlx/runtime/mlx_lm_subprocess_backend.py owlmlx/runtime/kernel.py owlmlx/memory_pressure_contract.py
```

Observed results:

- Metal-OOM/cooldown targeted subprocess tests: `3 passed, 51 deselected`
- full subprocess backend: `54 passed`
- memory pressure + recovery/admission contracts: `30 passed`
- runtime kernel focused: `12 passed, 13 deselected`
- runtime server focused: `4 passed, 37 deselected`
- py_compile: passed

## 6. Remaining Gap

The next possible improvement is live host-pressure sampling before the first
Metal OOM. This handoff only adds post-failure cooldown admission based on
runtime-owned evidence.
