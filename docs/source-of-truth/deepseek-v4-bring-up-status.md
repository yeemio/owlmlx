# DeepSeek-V4 Family Bring-Up Status

> Status: authoritative
> Created: 2026-05-10
> Scope: honest current state and bring-up path for DeepSeek-V4-Flash in owlmlx;
> complements `deepseek-v4-flash-adapter-optimization-candidate.md`

## 1. Current Status

`owlmlx` returns a clean pre-load `unsupported_model_family` rejection for
DeepSeek-V4-Flash-2bit-DQ. This is correct defensive behavior: the runtime
probes for `mlx_lm.models.{model_type}` before attempting load, and the
stock `mlx-lm >= 0.22.0` (current pyproject.toml constraint) does not include
`mlx_lm.models.deepseek_v4`. The rejection does not dirty runtime health or
add load-failure recovery noise.

The bring-up target is: **load → generate → unload → clean health**, with a
measured `model_release_candidate_record` row.

## 2. Upstream Dependency

DeepSeek-V4 support requires `mlx_lm.models.deepseek_v4`. This module exists
in:

- **PR branch:** `machiabeli/mlx-lm-1`, commit `7d20c1d`
- **Status:** not merged into any `mlx-lm` release as of 2026-05-10
- **Isolated proof:** a first short smoke through the PR branch produced
  visible text; full lifecycle was not completed (memory pressure at 4-bit)
- **Stock release:** `mlx-lm 0.31.3` does not include `deepseek_v4.py`

owlmlx has **no local allowlist** blocking DeepSeek. The check is a pure
`importlib.util.find_spec(f"mlx_lm.models.{model_type}")` probe. When the
module is available, the load path proceeds normally.

## 3. Bring-Up Path

### 3.1 When Upstream Merges

Once `mlx_lm.models.deepseek_v4` is available in a released `mlx-lm` version:

1. Bump `mlx-lm` lower bound in `pyproject.toml` to the release that includes it
2. Run the Model RC harness against `DeepSeek-V4-Flash-2bit-DQ` with the
   `flagship_experimental` lane
3. Collect a clean `load → generate → unload → clean health` record
4. If memory pressure causes OOM (exit 137), classify as
   `memory_budget_exceeded` and record the exact RSS at point of failure
5. Update `native-mlx-backend-capability-matrix.md` and add a measured
   `model_release_candidate_record` row

### 3.2 Intermediate Path (PR Branch)

If owlmlx needs DeepSeek evidence before upstream merges:

1. Create a separate `pyproject.toml` extras group: `[project.optional-dependencies]`
   `deepseek-experimental = ["mlx-lm @ git+https://github.com/machiabeli/mlx-lm@7d20c1d"]`
2. Run the Model RC harness under this extras group in a dedicated venv
3. Record evidence under `files/evidence/owlmlx/model-release-candidates/` with
   `lane=flagship_experimental` and `visibility_status=not_registered`
4. Do **not** merge the PR-branch dependency into the mainline `runtime` extra

This path is optional. The main bring-up gate is upstream merge.

### 3.3 Memory Budget Constraint

The 2-bit-DQ variant requires approximately 14–16 GB peak RSS on a 128 GB host.
The 4-bit variant required >40 GB and caused OOM on the test host. Bring-up
should target only the 2-bit-DQ variant initially.

## 4. Blocked Scope

Until upstream merges, the following are explicitly deferred:

- Any measured TPS comparison against reference runtimes for DeepSeek
- Any visibility registration on `GET /v1/openai/models`
- Any claim of DeepSeek support in external communication

The `BANNED_VERDICT_VOCABULARY` enforcement in `owlmlx.comparative_evidence_schema`
ensures no premature parity or replacement claim can pass schema validation.

## 5. Test Contract

`tests/test_mlx_native_backend.py` includes a test verifying the current clean
rejection behavior: loading `DeepSeek-V4-Flash-2bit-DQ` returns an error event
with `error_code=unsupported_model_family` without dirtying the backend's
health state.

When the bring-up is complete, a new test in
`tests/test_mlx_native_backend_real_smoke.py` (env-gated) should verify the
full lifecycle.

## 6. Update Rule

This document is updated when:

- `mlx_lm.models.deepseek_v4` is available in a released version
- A full-lifecycle Model RC record exists for any DeepSeek variant
- The memory budget constraint changes (larger or smaller variant available)
