# owlmlx Model RC Profile-Aware Parallel Coordinator Packet

> Date: 2026-05-05
> Coordinator: Codex
> Goal: narrow the current Model RC gap from generic slow/odd output into
> runtime-owned profile, baseline, and observability facts.

## 1. Current Frozen Truth

- `owlmlx.model_profile` P0 exists and resolves:
  - `qwen3_6_text`
  - `qwen3_6_moe`
  - `gemma4_text`
  - `deepseek_v4_experimental`
  - `unknown`
- The current Model RC runner serializes `model_profile` into
  `runner-config.json`, but the profile is not yet fully operational for live
  generation decisions.
- Qwen3.6-27B direct `mlx_lm.stream_generate` baseline is also slow. The
  latest evidence does not support treating owlmlx HTTP wrapper overhead as the
  dominant Qwen27 blocker.
- Qwen3.6-35B-A3B still needs TTFT/template/thinking-budget isolation.
- Gemma still needs profile-aware output-shape isolation after chat-template
  routing moved the blocker from raw repetition into reasoning/channel output.
- OwlOps can consume Model RC v2 history, but should not infer missing
  runtime facts locally.

## 2. Parallel Allocation

### Executor A: Profile-Aware Runner Wiring

Prompt:
`files/execution-prompts/owlmlx/owlmlx-model-profile-operational-wiring.md`

Type: lightweight code lane.

Purpose: make P0 `ModelProfile` operational in the Model RC live runner without
running heavy models.

### Executor B: MLX-LM Generation Path Static Triage

Prompt:
`files/execution-prompts/owlmlx/owlmlx-mlx-lm-generation-path-static-triage.md`

Type: lightweight audit lane.

Purpose: inspect local `mlx_lm` generation/sampler/template APIs and identify
which knobs are safe to express as owlmlx profile policy.

### Executor C: Qwen35/Gemma Direct Baseline

Prompt:
`files/execution-prompts/owlmlx/owlmlx-qwen35-gemma-direct-mlx-lm-baseline.md`

Type: only heavy live lane.

Purpose: compare direct `mlx_lm` versus owlmlx HTTP for Qwen3.6-35B-A3B and
Gemma-4-31B-it, one model at a time under `/tmp/owlmlx-model-rc-heavy.lock`.

### OwlOps External Assistance

Prompt:
`files/execution-prompts/owlmlx/owlops-model-rc-profile-aware-observability-r167.md`

Type: external consumer prompt, do not run until owlmlx exposes profile-aware
records or explicit `runtime_missing` equivalent fields.

Purpose: prepare OwlOps to render profile-aware evidence without local runtime
inference.

## 3. Hard Rules

- `oMLX`, `vMLX`, and `vllm-mlx` are peer reference runtimes, not upstreams.
- Do not edit OwlOps/OwlCoda/AI/Agent from owlmlx executor lanes.
- Do not kill legacy `8001` or `8009`.
- Only Executor C may load heavy models.
- Executor C must use `/tmp/owlmlx-model-rc-heavy.lock` before any model load.
- Do not make current release-ready, parity, production-grade, superior, or
  equivalent claims.
- Preserve unrelated dirty and staged work.
- Stage only lane-owned files.

## 4. Completion Order

1. A and B may run immediately.
2. C may run immediately only if it can acquire the heavy lock.
3. OwlOps should wait until A returns the exact field contract and at least one
   fresh profile-aware record exists, unless it is only preparing fallback UI.

## 5. Coordinator Decision After Return

- If A succeeds and C confirms Qwen35/Gemma issues are also direct-baseline
  visible, the dominant next gap is model profile/generation policy.
- If C finds owlmlx HTTP materially worse than direct `mlx_lm`, the dominant
  next gap becomes owlmlx runtime stream/generation path overhead for that
  model family.
- If B finds a clear `mlx_lm` profile knob that A did not wire, run a narrow
  A-fix lane before more live records.
- OwlOps should only be activated after owlmlx has a stable wire contract or an
  explicit `runtime_missing` missing-field contract.
