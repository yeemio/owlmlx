# Runtime-3 Benchmark And Streaming Truth

> Status: authoritative
> Updated: 2026-04-11
> Scope: Runtime-3 real streaming proof and same-model comparison against the old platform

## 1. Purpose

This document closes the remaining Runtime-3 proof points:

- real streamed token delivery through the RuntimeKernel path
- same-model comparison against old-platform benchmark truth using the same
  benchmark prompt set

## 2. Real Streaming Smoke

Script:

`scripts/runtime3_streaming_smoke.py`

Environment:

- `/Users/yeemio/AI/gitrep/owlmlx/.runtime1-mlx/bin/python`

Model:

- `/Users/yeemio/AI/Agent/models/gpt-oss-20b-MXFP4-Q4`

Observed result:

| Metric | Value |
|---|---|
| `load_time_s` | `1.4815` |
| `ttft_s` | `0.2182` |
| `total_s` | `0.2672` |
| token events | `8` |
| done event | `1` |

Key proof:

- RuntimeKernel emitted real token events before final completion
- the stream ran through `MlxLmSubprocessBackend`, not the in-process probe adapter
- parent process still never imported `mlx_lm`

## 3. Same-Model Benchmark Comparison

Script:

`scripts/runtime3_platform_benchmark_compare.py`

Old-platform truth source:

- `/Users/yeemio/AI/Agent/model_fleet/benchmark_gate.json`

Benchmark prompt set:

- `short_qa`
- `structured_json`
- `coding`

These prompts match the old platform's dedicated benchmark cases as defined in
`AI/Agent/model_fleet/benchmark_runner.py` on 2026-04-11.

Comparison model:

- `/Users/yeemio/AI/Agent/models/Qwen3.5-35B-A3B-4bit`

Runtime-3 result:

| Metric | owlmlx Runtime-3 | old platform |
|---|---:|---:|
| avg TTFT seconds | `0.779` | `0.431` |
| avg total seconds | `3.937` | `3.093` |
| avg tokens/sec | `143.1` | `61.7` |

Delta (`owlmlx - old platform`):

| Metric | Delta |
|---|---:|
| TTFT seconds | `+0.348` |
| total seconds | `+0.844` |
| tokens/sec | `+81.4` |

## 4. Interpretation

Runtime-3 comparison truth:

- `owlmlx` is still slower on TTFT than the old platform for this same-model
  benchmark shape
- `owlmlx` is also slower on end-to-end total latency
- persistent child sessions removed the Runtime-1 cold-start cliff, but the
  serving stack still has orchestration overhead relative to the mature old
  platform

The tokens/sec comparison should be treated as indicative, not absolute:

- both paths use the same model and same benchmark prompts
- but output length and formatting can still differ between the old platform's
  OpenAI-style HTTP serving path and `owlmlx` direct RuntimeKernel streaming

The most trustworthy comparison fields are:

- TTFT
- total latency

## 5. Runtime-3 Closure

Runtime-3 is now considered complete because it has all four planned proof
points:

1. explicit runtime/control surface
2. serialized concurrent serving proof
3. real streaming response path
4. same-model comparison against old-platform benchmark truth

## 6. Non-Claims

This document does not claim:

- production SLOs are defined
- streaming transport is finalized as SSE vs NDJSON
- multi-child per-model pools exist
- platform migration is complete
- old-platform parity is achieved
