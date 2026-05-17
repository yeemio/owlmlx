# D2 · Design-Grade Spec

> **Gate**: Campaign D2 · DeepSeek V4 Flash isolated metrics ledger
> **Plan-grade source**: [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign D
> **Status**: design-grade + code-grade runner landed; real streaming smoke currently blocked · 2026-05-17
> **Prerequisite**: D1 passed under the adopted `messages` / chat-template prompt policy.
> **Non-goal**: this spec does not claim `owlmlx supports DeepSeek V4`.

## 1. Purpose

D2 turns the D1 lifecycle proof into a metrics ledger for the isolated
DeepSeek V4 lane:

```text
isolated runtime preflight
  -> load
  -> stream_generate_messages
  -> collect TTFT / wall time / decode TPS / RSS / health
  -> unload
  -> clean health
```

D2 remains experimental-only. It does not register DeepSeek V4 in the default
model surface and does not adopt `ds4.c`.

## 2. Scope

| Item | Requirement |
|---|---|
| Runtime environment | Existing isolated `.runtime-deepseek-v4-mlx` only |
| Prompt surface | adopted D1 `messages` / chat-template surface |
| Generation surface | streaming only, because TTFT and decode TPS require token events |
| Metrics | `load_time_s`, `ttft_ms`, `stream_wall_ms`, `decode_tps_after_first_token`, `wall_tps`, `peak_rss_gb`, backend health |
| Evidence | JSONL under `files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/` |
| Capability label | `experimental_only` |

## 3. Ledger Shape

Each row is a D2 metrics result:

```yaml
schema_version: d2.metrics.v1
record_type: metrics_result
gate: D2
model_id: DeepSeek-V4-Flash-2bit-DQ
prompt_surface: messages
generation_surface: stream_generate_messages
metrics:
  load_time_s: float
  ttft_ms: float
  stream_wall_ms: float
  prompt_tokens: int | null
  completion_tokens: int
  decode_tps_after_first_token: float
  wall_tps: float
  peak_rss_gb: float
backend_health:
  load_ok: true
  generate_ok: true
  unload_ok: true
  clean_health_after_unload: true
  child_restart_observed: false
verdict: passed | failed
```

`decode_tps_after_first_token` is computed as:

```text
(completion_tokens - 1) / ((stream_wall_ms - ttft_ms) / 1000)
```

`wall_tps` is computed as:

```text
completion_tokens / (stream_wall_ms / 1000)
```

## 4. Pass Criteria

```yaml
D2_deepseek_v4_metrics_ledger:
  preflight: passed
  prompt_surface: messages
  generation_surface: stream_generate_messages
  required_metrics_present:
    - load_time_s
    - ttft_ms
    - stream_wall_ms
    - completion_tokens
    - decode_tps_after_first_token
    - peak_rss_gb
  backend_health:
    load: passed
    generate: passed
    unload: passed
    clean_health_after_unload: passed
    child_restart_observed: false
  overall_conclusion: passed | blocked | failed
```

A missing required metric fails D2. A stream timeout or manual termination is a
`blocked` / `failed` diagnostic, not a pass.

## 5. Current Blocker

The first real D2 smoke attempt on 2026-05-17 used:

```bash
uv run python scripts/bench/deepseek_v4_d1_repeatability.py metrics \
  --run-id 20260517T-d2-p1-128-metrics-smoke \
  --prompt-id p1_short_cn \
  --max-tokens 128 \
  --timeout-s 900
```

It did not produce a D2 ledger row. The isolated runner child reached a loaded
RSS band but emitted no streaming token/done payload before manual cleanup:

```text
child command: python -m owlmlx.runtime.mlx_lm_runner
observed elapsed: >150s
observed rss: 17GB band
observed cpu: 0.0%
cleanup: own D2 attempt processes terminated; no residual D2 runner remains
```

This classifies D2 as **runner landed / real streaming smoke blocked**, not
metrics-pass.

## 6. Next Debug Slice

The next code-grade slice should isolate whether the blocker is:

1. `mlx_lm.stream_generate` for this DeepSeek adapter,
2. chat-template rendered prompt shape,
3. first-token latency far above D2 smoke assumptions, or
4. missing/late terminal payload semantics.

Do not weaken D2 into non-stream `generate_messages`: that would remove TTFT
and decode TPS, which are the reason D2 exists.
