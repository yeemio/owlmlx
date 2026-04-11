# Runtime-1/2 Environment Diagnostics

> Status: authoritative
> Updated: 2026-04-11
> Scope: local Runtime-1/2 MLX environment truth

## 1. Purpose

This document freezes the current Runtime-1/2 environment situation, including
the clean-room environment result that unblocked the first real local smoke.

The question is not whether `owlmlx` has a safe subprocess boundary anymore.
It does. The remaining question is which local Python environment, if any, can
import `mlx_lm` without aborting inside MLX/Metal initialization.

## 2. Verified Probe Results

Using `runtime1_mlx_lm_smoke.py` and the structured selection helpers in
`owlmlx/runtime/mlx_environment.py`, the current machine-level truth is:

| Environment | Executable | Result | Meaning |
|---|---|---|---|
| current | `/opt/homebrew/opt/python@3.14/bin/python3.14` | `ModuleNotFoundError` | no `mlx_lm` installed |
| llm-infra | `/Users/yeemio/AI/llm-infra/.venv/bin/python` | returncode `-6` | child process aborts during MLX/Metal init |
| owlmlx-venv | `/Users/yeemio/AI/gitrep/owlmlx/.venv/bin/python` | returncode `-6` | child process aborts during MLX/Metal init |
| homebrew-python3 | `/opt/homebrew/bin/python3` | `ModuleNotFoundError` | no `mlx_lm` installed |

Observed failure signature in the aborting environments:

- Objective-C `NSRangeException`
- crash during `libmlx.dylib` device / Metal allocator initialization
- Python cannot catch it in-process
- subprocess isolation converts it into a structured failure for the parent

## 3. Architecture Consequence

The current blocker is environment-level, not runtime-kernel-level.

What is already proven:

- parent process never needs to import `mlx_lm`
- dangerous child aborts are isolated from `owlmlx` parent runtime
- default probing no longer walks known-dangerous virtualenvs automatically
- explicit diagnostic probing still captures real return code and stderr

What is now proven:

- a clean local Python environment can import `mlx_lm` safely
- a small local MLX-compatible model can complete the first real
  `load -> generate` path through `owlmlx`

Verified successful clean-room environment:

| Environment | Executable | Result | Meaning |
|---|---|---|---|
| runtime1-mlx | `/Users/yeemio/AI/gitrep/owlmlx/.runtime1-mlx/bin/python` | import probe passed | clean environment can safely import `mlx_lm 0.31.2` |

Verified real local smoke coverage:

| Model | Path | Result | Detail |
|---|---|---|---|
| gpt-oss-20b-MXFP4-Q4 | `/Users/yeemio/AI/Agent/models/gpt-oss-20b-MXFP4-Q4` | PASS | Runtime-1 one-shot `generate` succeeded in about 12.07s |
| Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit | `/Users/yeemio/AI/Agent/models/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit` | PASS | Runtime-1 one-shot `generate` succeeded in about 12.66s |
| Qwen3.5-35B-A3B-4bit | `/Users/yeemio/AI/Agent/models/Qwen3.5-35B-A3B-4bit` | PASS | Runtime-1 one-shot `generate` succeeded in about 13.41s |

## 4. Operational Discipline

Until the clean environment becomes the standard Runtime-1 baseline:

- do not run direct parent-process `import mlx_lm`
- do not use the old `llm-infra` or `owlmlx/.venv` as Runtime-1 validation
  baselines
- only probe known-dangerous environments through explicit opt-in flags
- treat returncode `-6` as an environment failure, not a kernel failure

## 5. Decision

Runtime-1 should proceed with a clean-room environment instead of repairing the
two existing MLX-oriented virtualenvs.

Rationale:

- both existing MLX-oriented environments already fail at import time
- repairing them in place risks mixing old state with new installs
- a new environment is the fastest way to answer the only remaining question:
  can this machine import `mlx_lm` safely at all?

## 6. Next Step

The clean-room Runtime-1 environment has now been created and verified:

```bash
python3 -m venv .runtime1-mlx
.runtime1-mlx/bin/pip install --upgrade pip
.runtime1-mlx/bin/pip install "mlx>=0.22.0" "mlx-lm>=0.22.0" "fastapi>=0.115.0"
env PYTHONPATH=/Users/yeemio/AI/gitrep/owlmlx \
  .runtime1-mlx/bin/python scripts/runtime1_mlx_lm_smoke.py \
  --model /Users/yeemio/AI/Agent/models/gpt-oss-20b-MXFP4-Q4 \
  --memory-gb 16 \
  --prompt "Reply with exactly OK." \
  --max-tokens 8
```

## 7. Runtime-2 Persistent Child Validation

Runtime-2 has now validated persistent child reuse in the clean
`.runtime1-mlx` environment:

| Model | Load result | Generate #1 | Generate #2 | Proof |
|---|---|---|---|---|
| gpt-oss-20b-MXFP4-Q4 | PASS, one persistent child | PASS, `0.2438s` | PASS, `0.1479s` | same `pid`, `generation_count=1 -> 2` |
| Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit | PASS, one persistent child | PASS, `0.5539s` | PASS, `0.4322s` | same `pid`, `generation_count=1 -> 2` |

This proves Runtime-2 is no longer doing one-shot `load + generate + exit` on
every request. The model stays resident inside one child process until explicit
`unload`.

Current answer on `unload`:

- in Runtime-1 one-shot mode, `unload` was only a registration boundary
- in Runtime-2 persistent mode, `unload` is a real child teardown boundary
- Runtime-2 `generate` reuses the already-loaded child process

First Runtime-2 steady-state benchmark on the clean environment:

| Model | Load | Warm mean | Warm median | Warm min | Warm max |
|---|---|---|---|---|---|
| gpt-oss-20b-MXFP4-Q4 | `1.4891s` | `0.1677s` | `0.1571s` | `0.1341s` | `0.2448s` |
