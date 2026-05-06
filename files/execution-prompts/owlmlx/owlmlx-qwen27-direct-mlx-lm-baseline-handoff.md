# owlmlx Qwen27 Direct MLX-LM Baseline Handoff

> Executor: C
> Date: 2026-05-05
> Outcome label: `owlmlx_qwen27_direct_mlx_lm_baseline_completed`
> Evidence dir:
> `files/evidence/owlmlx/model-release-candidates/20260505T140449Z-qwen36-27b-direct-mlx-lm-baseline`

## Scope

This lane compared only `Qwen3.6-27B` direct `mlx_lm.stream_generate` versus
owlmlx HTTP streaming on the same host.

No runtime code was modified. No external repository was edited. Legacy
listeners on `8001` and `8009` were observed only and were not stopped or
killed.

## Commands

Preflight and lock:

```bash
pwd
.venv/bin/python - <<'PY'
import importlib.util, sys
print(sys.executable)
print("mlx", importlib.util.find_spec("mlx") is not None)
print("mlx_lm", importlib.util.find_spec("mlx_lm") is not None)
PY
curl -s http://127.0.0.1:8066/healthz
curl -s http://127.0.0.1:8066/v1/openai/models
lsof -n -iTCP:8066 -sTCP:LISTEN
test ! -e /tmp/owlmlx-model-rc-heavy.lock
mkdir /tmp/owlmlx-model-rc-heavy.lock
```

Direct baseline:

```bash
.venv/bin/python <inline direct mlx_lm.stream_generate harness>
```

The inline harness used:

- model path: `/Users/yeemio/AI/Agent/models/Qwen3.6-27B`
- prompt: `In one short sentence, define local AI.`
- max tokens: `32`
- temperature: `0`
- repeats: `2`
- API: `mlx_lm.load` plus `mlx_lm.stream_generate`

owlmlx HTTP baseline:

```bash
.venv/bin/python scripts/runtime_model_release_candidate.py \
  --ledger-path files/evidence/owlmlx/model-release-candidates/20260505T140449Z-qwen36-27b-direct-mlx-lm-baseline/http-ledger.jsonl \
  run-live-http-mainline \
  --runtime-url http://127.0.0.1:8066 \
  --host-class Mac17,6-arm64-macOS-26.4.1-128GB \
  --model-id Qwen3.6-27B \
  --artifact-path /Users/yeemio/AI/Agent/models/Qwen3.6-27B \
  --prompt 'In one short sentence, define local AI.' \
  --max-tokens 32 \
  --temperature 0 \
  --request-mode raw_generate_stream \
  --prompt-template-id operator_prompt_raw \
  --repeats 2 \
  --memory-gb 56 \
  --evidence-dir files/evidence/owlmlx/model-release-candidates/20260505T140449Z-qwen36-27b-direct-mlx-lm-baseline \
  --http-timeout-s 900 \
  --rss-sample-interval-s 0.5
```

## Results

Direct `mlx_lm.stream_generate`:

- load wall time: `7150.766 ms`
- mean TTFT: `2151.716 ms`
- mean decode throughput: `2.458 tokens/s`
- mean generation wall time: `14789.108 ms`
- sampled peak process-tree RSS: `53353775104 bytes`
- repeat 1: TTFT `2889.905 ms`, decode `2.339 tokens/s`, wall `16141.611 ms`
- repeat 2: TTFT `1413.528 ms`, decode `2.578 tokens/s`, wall `13436.604 ms`

owlmlx HTTP streaming:

- load time: `6395.317 ms`
- reload time: `6054.338 ms`
- unload mean: `540.469 ms`
- mean TTFT: `2180.629 ms`
- mean decode throughput: `4.028 tokens/s`
- mean generation wall time: `9877.296 ms`
- sampled peak process-tree RSS: `49523113984 bytes`
- repeat count: `2`
- failure count: `0`
- output sanity label: `reasoning_trace_truncated`

Deltas:

- HTTP minus direct TTFT: `+28.913 ms`
- HTTP minus direct decode throughput: `+1.570 tokens/s`
- HTTP decode throughput ratio versus direct: `1.639`
- HTTP minus direct generation wall time: `-4911.812 ms`
- HTTP minus direct sampled peak RSS: `-3830661120 bytes`

## Classification

Blocker classification:
`model_profile_or_mlx_lm_baseline_decode`

Reason: direct `mlx_lm.stream_generate` was also slow for the same
`Qwen3.6-27B` prompt and settings. The owlmlx HTTP path was not materially
slower in decode throughput in this run, so this evidence does not support
classifying the next gap as owlmlx wrapper stream overhead.

## Cleanup

Post-run checks showed:

- `http://127.0.0.1:8066/healthz` returned `ok: true`, `readiness: degraded`,
  and `active_model_id: null`
- `8066` still had the pre-existing listener PID `4348`
- no lane-owned direct `mlx_lm`, `runtime_model_release_candidate`, or
  `Qwen3.6-27B` process remained
- legacy `8001` and `8009` listeners remained present and were not touched

The lane-local HTTP ledger was written only inside the evidence directory. The
cumulative Model RC ledger was not updated.
