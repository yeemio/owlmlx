# owlmlx Model RC Parallel Profile / Baseline / Provenance Coordinator Packet

> Coordinator: owlmlx
> Date: 2026-05-05
> Goal: continue Model RC progress after peer-reference mechanism audit
> Outcome label: `owlmlx_model_rc_parallel_profile_baseline_provenance_packet_ready`

## 1. Current Truth

The peer-reference mechanism audit is closed and should be treated as sufficient
for the next implementation slice:

- Source of truth:
  `docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md`
- Handoff:
  `files/execution-prompts/owlmlx/owlmlx-peer-reference-mechanism-audit-for-model-profiles-handoff.md`

Do not continue broad mechanism research. The next work should reduce the
current Model RC blockers:

- `gemma-4-31B-it`: no longer primarily raw-prompt repetition; current latest
  record is chat-template `reasoning_trace_truncated` with high TTFT.
- `Qwen3.6-35B-A3B`: high TTFT plus `reasoning_trace_truncated`.
- `Qwen3.6-27B`: valid output but slow decode.
- `DeepSeek-V4-Flash-2bit-DQ`: pressure/adaptation lane only.

`oMLX`, `vMLX`, and `vllm-mlx` are peer reference runtimes, not upstreams.
`mlx-lm` is the shared ecosystem dependency/substrate.

## 2. Parallel Allocation

Run three lanes in parallel only because their write sets and memory profiles
are separated.

### Lane A: ModelProfile Resolver P0

Prompt:

`files/execution-prompts/owlmlx/owlmlx-model-profile-resolver-p0-gemma-qwen-mainline.md`

Executor type: code implementation executor.

Memory rule: no heavy model load. Unit tests and py_compile only unless the
coordinator explicitly asks for live validation.

Write ownership:

- `owlmlx/model_profile.py` or equivalent new profile module
- `tests/test_model_profile.py`
- optional narrow docs for the profile contract
- optional minimal Model RC schema/runner wiring only if safe

Primary output:

- owlmlx-owned typed `ModelProfile` resolver for Qwen3.6 text, Qwen3.6 MoE,
  Gemma4 text, and DeepSeek V4 experimental.

### Lane B: Vendor Provenance Audit

Prompt:

`files/execution-prompts/owlmlx/owlmlx-peer-reference-vendor-provenance-audit.md`

Executor type: audit/documentation executor.

Memory rule: no model loads.

Write ownership:

- `docs/source-of-truth/peer-reference-vendor-provenance-audit.md`
- `files/execution-prompts/owlmlx/owlmlx-peer-reference-vendor-provenance-audit-handoff.md`
- `docs/source-of-truth/master-outline.md` only if adding the truth document

Primary output:

- final legal/provenance boundary for the two candidate code-reuse areas:
  oMLX sampler/RNG safety and vMLX DeepSeek V4 JANGTQ/DSV4 loader references.

### Lane C: Qwen27 Direct MLX-LM Baseline

Prompt:

`files/execution-prompts/owlmlx/owlmlx-qwen27-direct-mlx-lm-baseline.md`

Executor type: live evidence executor, preferably Codex with desktop/computer
monitoring if available.

Memory rule: this is the only heavy model lane. It may run while A/B work, but
must not overlap with any other heavy model load.

Write ownership:

- one new evidence directory under
  `files/evidence/owlmlx/model-release-candidates/`
- one handoff under `files/execution-prompts/owlmlx/`
- optional short execution-plan note only if the evidence is complete

Primary output:

- same prompt / same model direct `mlx_lm.stream_generate` vs owlmlx HTTP
  streaming comparison for `Qwen3.6-27B`, to determine whether slow decode is
  in the MLX-LM substrate/profile or in owlmlx wrapper/runtime path.

## 3. Cross-Lane Rules

- Do not modify OwlOps, OwlCoda, `/Users/yeemio/AI/Agent`, or legacy platform
  repos.
- Do not stop or kill `8001` or `8009`.
- Do not claim release-ready, parity, replacement, production-grade,
  equivalent, beats, wins, or matches.
- Do not vendor peer-runtime code in this parallel slice.
- Do not let OwlOps infer runtime truth locally.
- Do not merge DeepSeek into the mainline Model RC pass/fail gate.
- Preserve existing staged and dirty work; do not revert unrelated Phase45
  residue.

## 4. Coordination Decision After Return

When all lanes return:

1. If A succeeds, use `ModelProfile` as the next shared substrate for Gemma and
   Qwen35 live experiments.
2. If B finds license/provenance blockers, keep vendor candidates as
   documentation-only and implement rewrites instead.
3. If C shows direct MLX-LM is fast but owlmlx HTTP is slow, prioritize
   wrapper/stream path profiling for Qwen27.
4. If C shows direct MLX-LM is also slow, keep Qwen27 as profile/model
   baseline issue and avoid blaming owlmlx wrapper without evidence.
