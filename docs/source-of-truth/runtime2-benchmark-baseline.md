# Runtime-2 Benchmark Baseline

> Status: authoritative
> Updated: 2026-04-11
> Scope: Runtime-2 steady-state benchmark truth

## 1. Purpose

This document freezes the first fair Runtime-2 steady-state benchmark shape.

The goal is not to claim production performance parity. The goal is to record
the first persistent-child baseline where `load` and warm `generate` are
measured separately.

## 2. Benchmark Method

Script:

`scripts/runtime2_steady_state_benchmark.py`

Environment:

- Python: `/Users/yeemio/AI/gitrep/owlmlx/.runtime1-mlx/bin/python`
- `mlx_lm`: `0.31.2`
- parent process never imports `mlx_lm`
- backend: `MlxLmSubprocessBackend`

Discipline:

- select one safe environment explicitly
- `load` once
- run repeated `generate` calls against the same persistent child
- `unload` explicitly
- record load time and warm generate latencies separately

## 3. First Baseline

Model:

- `/Users/yeemio/AI/Agent/models/gpt-oss-20b-MXFP4-Q4`

Command shape:

```bash
env PYTHONPATH=/Users/yeemio/AI/gitrep/owlmlx \
  /Users/yeemio/AI/gitrep/owlmlx/.runtime1-mlx/bin/python \
  scripts/runtime2_steady_state_benchmark.py \
  --python /Users/yeemio/AI/gitrep/owlmlx/.runtime1-mlx/bin/python \
  --model /Users/yeemio/AI/Agent/models/gpt-oss-20b-MXFP4-Q4 \
  --memory-gb 16 \
  --prompt "Reply with exactly OK." \
  --max-tokens 8 \
  --repeat 5
```

Result:

| Metric | Value |
|---|---|
| `load_time_s` | `1.4891` |
| `warm_generate_mean_s` | `0.1677` |
| `warm_generate_median_s` | `0.1571` |
| `warm_generate_min_s` | `0.1341` |
| `warm_generate_max_s` | `0.2448` |

## 4. Interpretation

This baseline proves three things:

- Runtime-2 has removed the Runtime-1 cold-start-per-request bottleneck.
- The persistent child session is stable across repeated warm generations.
- `owlmlx` now has a repeatable benchmark tool for future comparison against
  the old platform.

This baseline does **not** prove:

- production latency under concurrent traffic
- TTFT parity with the old platform
- streaming readiness
- multi-model steady-state fairness
- restart behavior under repeated child faults

## 5. Next Benchmark Expansions

The next honest benchmark set should add:

- one more model family beyond `gpt-oss-20b`
- comparison with old-platform warm serving on the same machine
- repeated restart/recovery benchmark
- queue behavior under serialized concurrent requests
