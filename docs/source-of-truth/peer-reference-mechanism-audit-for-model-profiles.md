# owlmlx Peer Reference Mechanism Audit For Model Profiles

> Status: authoritative audit
> Updated: 2026-05-05
> Scope: source/code audit only for `mlx-lm`, `oMLX`, `vMLX`, and
> `vllm-mlx` mechanisms that may inform owlmlx model-family profiles,
> scheduler/cache/runtime mechanisms, or license-reviewed vendor candidates.
> No runtime code, external repository, port, or model-load state was changed.

## 1. Status / Updated / Scope

Outcome label:
`owlmlx_peer_reference_mechanism_audit_surface_closed`.

This document answers one question: which peer-reference and ecosystem
mechanisms should become owlmlx-owned family profiles, owlmlx-owned runtime
mechanisms, direct ecosystem dependency usage, license-reviewed vendor
candidates, or non-adopted surface.

The audit is intentionally narrower than implementation. It does not move code
from any peer runtime into owlmlx, and it does not change the active
technical-preview server.

Current owlmlx model release-candidate facts used as input:

- Mainline models are `Qwen3.6-27B`, `Qwen3.6-35B-A3B`, and
  `gemma-4-31B-it`; the model program assigns these to the mainline lane
  (`docs/source-of-truth/model-release-candidate-program.md:67-75`).
- `DeepSeek-V4-Flash-2bit-DQ` is a pressure/adaptation lane only, not a
  mainline model (`docs/source-of-truth/model-release-candidate-program.md:83-114`).
- All three mainline v2 records remain `needs_optimization`; the measured
  blockers are Qwen27 slow decode, Qwen35 high TTFT plus
  `reasoning_trace_truncated`, and Gemma `repetitive_output`
  (`docs/source-of-truth/release-readiness-execution-plan.md:272-306`).
- Runtime/public truth is owned by owlmlx; OwlOps observes the record surface
  but must not invent runtime facts (`docs/source-of-truth/model-release-candidate-program.md:38-61`).

## 2. Executive Verdict

The next owlmlx closure round should be profile-first, not scheduler-first.

The strongest P0 signal is that all three mainline blockers map to
model-family profile behavior before they require deep scheduler adoption:

- Gemma: likely chat-template, stop-token, reasoning-channel cleanup,
  repetition/sampling, and unsafe prefix-cache interaction with mixed attention.
- Qwen35: likely thinking/template policy plus prefill and max-token behavior;
  decode speed is not the first visible blocker.
- Qwen27: likely runtime invocation overhead, sampler/logits path, or resident
  stream wrapper behavior, because output is valid while decode is slow.

DeepSeek V4 should stay P2 and experimental. The useful peer-reference material is
loader/cache/large-MoE pressure knowledge, especially from vMLX's DeepSeek V4
JANGTQ path, but it should not enter the mainline gate or be treated as a
generic owlmlx capability.

## 3. Sources Inspected

### 3.1 owlmlx source-of-truth

| Source | Inspection result |
|---|---|
| `AGENTS.md` | Project identity, honest label vocabulary, and adoption discipline read before audit. |
| `docs/source-of-truth/model-release-candidate-program.md` | Mainline and DeepSeek lane boundaries read; model ownership and evidence contract confirmed at lines 38-61 and 67-114. |
| `docs/source-of-truth/release-readiness-execution-plan.md` | Current v2 model blocker metrics and next-gap context read at lines 272-310. |
| `docs/source-of-truth/reference-runtime-comparison-matrix.md` | Existing reference-runtime gap framing read; owlmlx is still below oMLX/vMLX on scheduler/cache/lifecycle depth. |
| `docs/source-of-truth/runtime-capability-matrix.md` | Supported/partial/experimental labels read; current direct runtime and DeepSeek experimental rows are at lines 74-86 and 103-123. |
| `docs/source-of-truth/public-surface.md` | Public route and claim boundary read; supported HTTP surfaces include model RC routes at lines 45-123. |

### 3.2 peer-reference and ecosystem snapshots

All peer-reference / ecosystem repositories were cloned read-only into
`/tmp/owlmlx-peer-reference-audit-20260505`. No external repo was edited.

| Source | Commit inspected | License observed | Notes |
|---|---:|---|---|
| `mlx-lm` | `df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae` | MIT, `setup.py` says MIT and the license file is MIT (`setup.py:13-25`, `LICENSE:1-13`) | Direct ecosystem substrate for model loading, tokenizer/chat template wrapping, generation, cache classes, batch generation, and model-family implementations. |
| `oMLX` | `bac678ec72c97e497d05c3c6d637fa54f1b3d7e3` | Apache-2.0 (`pyproject.toml:5-11`, `LICENSE:1-35`) | Strongest reference for model profiles, thinking budget, sampler RNG safety, EnginePool, memory enforcement, and tiered cache. |
| `vMLX` | `3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69` | Apache-2.0 (`pyproject.toml:5-11`, `LICENSE:1-35`) | Strongest reference for Qwen3.6/Gemma4/DeepSeek V4 family registry, Gemma loop hazards, DSV4 loader/cache patches, and JANG/Smelt pressure mechanisms. Initial clone hit an HTTP/2 framing error; retrying clone with HTTP/1.1 succeeded. |
| `vllm-mlx` | `e69435608fa625b0dd4853cc118c968470a1b530` | Apache-2.0 (`pyproject.toml:5-11`, `LICENSE:1-45`) | Strong reference for prompt warm-up, continuous batching, lifecycle, metrics/cache endpoints, and reasoning parser surfaces. |

### 3.3 local probes

| Local source | Inspection result |
|---|---|
| `/Users/yeemio/AI/gitrep/runtime-probes/2026-04-16-mlx-omlx-vmlx-baseline-investigation.md` | Fresh `oMLX` and `vMLX` import/CLI probes passed; installed probe versions were `mlx = 0.31.1`, `mlx-lm = 0.31.2`, `omlx = 0.3.5`, and `vmlx = 1.3.35` (`:31-47`, `:83-113`, `:127-143`). |
| `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe` | Existing local probe inspected. `pyproject.toml` records Apache-2.0, `mlx>=0.31.1`, and a pinned `mlx-lm` git commit (`pyproject.toml:5-69`). |
| `/Users/yeemio/AI/gitrep/runtime-probes/vmlx-probe` | Existing local probe inspected. `pyproject.toml` records Apache-2.0, `mlx>=0.29.0`, and `mlx-lm>=0.31.2` for ArraysCache/LRUPromptCache/Gemma4 support (`pyproject.toml:5-58`). |

## 4. Mechanism Inventory

Each audited mechanism has exactly one adoption route and one priority.

| Mechanism | Most relevant evidence | Adoption route | Priority | owlmlx interpretation |
|---|---|---|---|---|
| MLX-LM model loading, tokenizer wrapper, and base generation API | `mlx-lm` exposes `load`, `generate`, `stream_generate`, conversion/quantization helpers, and sampler/logits extension points ([README lines 65-78](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/README.md#L65-L78), [92-108](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/README.md#L92-L108), [118-151](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/README.md#L118-L151)). | `use_directly_from_ecosystem` | `P0_current_rc_blocker` | Use the ecosystem substrate directly and test owlmlx's wrapper against it. Do not vendor broad MLX-LM code. |
| Model-family profile registry | oMLX has universal and model-specific profile fields for sampling, context, thinking, dflash/specprefill/cache flags ([model_profiles.py lines 19-66](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/model_profiles.py#L19-L66)); vMLX resolves model configs and stamped JANG metadata ([model_config_registry.py lines 31-68](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/model_config_registry.py#L31-L68), [115-139](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/model_config_registry.py#L115-L139)). | `rewrite_as_owlmlx_mechanism` | `P0_current_rc_blocker` | Implement an owlmlx-owned `ModelProfile` resolver from local model metadata and explicit overrides. Borrow the mechanism shape, not the peer-runtime identity layer. |
| Chat template kwargs and `enable_thinking` defaults | MLX-LM `TokenizerWrapper.apply_chat_template` injects `enable_thinking` when absent based on model thinking detection ([tokenizer_utils.py lines 256-346](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/mlx_lm/tokenizer_utils.py#L256-L346)); vLLM-MLX exposes default chat-template kwargs ([server.py lines 6270-6283](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/server.py#L6270-L6283)). | `profile_config_only` | `P0_current_rc_blocker` | Treat template kwargs as profile fields first. Runtime code should consume a resolved profile rather than hard-code per endpoint. |
| Qwen3.6 profile defaults | vMLX registers `qwen3_5` and `qwen3_5_moe_text` with qwen parser, `<|im_end|>`, and `think_in_template=True` ([model_configs.py lines 88-123](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/model_configs.py#L88-L123)). | `profile_config_only` | `P0_current_rc_blocker` | Qwen27 and Qwen35 should get explicit qwen profile defaults before deeper runtime work. |
| Gemma4 profile defaults | vMLX registers Gemma4/Gemma4 text with gemma4 parser, `<eos>` plus `<turn|>`, and channel-token cleanup ([model_configs.py lines 652-680](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/model_configs.py#L652-L680)); MLX-LM Gemma4 text cache mixes full attention with rotating cache ([gemma4_text.py lines 675-688](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/mlx_lm/models/gemma4_text.py#L675-L688)). | `profile_config_only` | `P0_current_rc_blocker` | Gemma's first fix should be a profile: template, stop set, channel cleanup, repetition policy, and cache caution flags. |
| Stop-token augmentation | vMLX adds extra EOS tokens from the model config registry when computing stop tokens ([scheduler.py lines 1326-1360](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/scheduler.py#L1326-L1360)); DeepSeek V4 adds user/assistant turn markers to stop runaway turns ([model_configs.py lines 498-561](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/model_configs.py#L498-L561)). | `profile_config_only` | `P0_current_rc_blocker` | Stop tokens belong in model profile resolution and should be surfaced in runtime evidence. |
| Thinking/reasoning parsing | oMLX has `extract_thinking`, streaming parser, and thinking budget processor ([thinking.py lines 29-156](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/api/thinking.py#L29-L156), [201-240](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/api/thinking.py#L201-L240)); vLLM-MLX has Qwen3, DeepSeek-R1, and Gemma4 parsers ([qwen3_parser.py lines 1-64](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/reasoning/qwen3_parser.py#L1-L64), [deepseek_r1_parser.py lines 1-110](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/reasoning/deepseek_r1_parser.py#L1-L110), [gemma4_parser.py lines 1-130](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/reasoning/gemma4_parser.py#L1-L130)). | `rewrite_as_owlmlx_mechanism` | `P0_current_rc_blocker` | owlmlx should own a small reasoning router and streaming parser contract so OpenAI/Anthropic surfaces expose the same runtime truth. |
| Thinking token budget / forced close | vLLM-MLX implements a thinking-aware logits processor with lifecycle phases, budget counting, rollback snapshots, and forced transition ([thinking_processor.py lines 1-110](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/constrained/thinking_processor.py#L1-L110), [200-269](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/constrained/thinking_processor.py#L200-L269)). | `rewrite_as_owlmlx_mechanism` | `P0_current_rc_blocker` | For Qwen35, a bounded thinking policy is a smaller experiment than adopting a scheduler. |
| Sampler and RNG safety | MLX-LM supports temperature/top-p/min-p/top-k and logits processors ([sample_utils.py lines 10-68](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/mlx_lm/sample_utils.py#L10-L68), [72-126](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/mlx_lm/sample_utils.py#L72-L126)); oMLX keeps a reimplementation because compiled MLX-LM samplers stopped advancing RNG in server use ([utils/sampling.py lines 2-14](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/utils/sampling.py#L2-L14), [132-167](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/utils/sampling.py#L132-L167)). | `vendor_candidate_requires_license_review` | `P0_current_rc_blocker` | Candidate for narrow license review only if owlmlx reproduces RNG/sampler drift. Until then, prefer direct MLX-LM plus tests. |
| Single-request streaming path | MLX-LM `stream_generate` reports prompt/generation throughput, peak memory, stop reason, and supports speculative draft model input ([generate.py lines 657-753](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/mlx_lm/generate.py#L657-L753)). | `use_directly_from_ecosystem` | `P0_current_rc_blocker` | Qwen27 should first compare owlmlx HTTP streaming against direct MLX-LM streaming with identical prompt/profile. |
| Prefill chunking and TTFT control | MLX-LM supports `prefill_step_size` in `generate_step` ([generate.py lines 307-345](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/mlx_lm/generate.py#L307-L345)); oMLX adds external/chunked prefill ([scheduler.py lines 1345-1568](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/scheduler.py#L1345-L1568)); vLLM-MLX has prompt warm-up via strict-prefix paths ([prompt_warmup.py lines 1-27](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/prompt_warmup.py#L1-L27), [179-275](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/prompt_warmup.py#L179-L275)). | `rewrite_as_owlmlx_mechanism` | `P0_current_rc_blocker` | For Qwen35, test prefill step size and warm-prefix ideas as owlmlx-owned knobs with evidence, not blind code adoption. |
| Prompt cache / prefix cache policy | MLX-LM has `LRUPromptCache`, save/load cache, rotating and quantized cache classes ([cache.py lines 15-85](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/mlx_lm/models/cache.py#L15-L85), [1623-1738](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/mlx_lm/models/cache.py#L1623-L1738)); oMLX cache factory builds prefix/paged/SSD stacks ([cache/factory.py lines 50-159](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/cache/factory.py#L50-L159)); vMLX documents a Gemma4 cache corruption hazard from bad rotating meta handling ([scheduler.py lines 72-117](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/scheduler.py#L72-L117)). | `rewrite_as_owlmlx_mechanism` | `P1_next_rc_accelerator` | Use MLX-LM classes directly, but owlmlx cache admission, counters, invalidation, and profile bypasses must be owned. |
| Gemma mixed-attention prefix-cache bypass | vMLX auto-bypasses prefix cache for mixed attention models because Gemma4 sliding+full attention produced generation loops after reconstructed cache reuse ([scheduler.py lines 352-369](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/scheduler.py#L352-L369)). | `profile_config_only` | `P0_current_rc_blocker` | Gemma profile should start with cache caution or bypass until owlmlx has model-specific cache proof. |
| Continuous batching scheduler | MLX-LM has `BatchGenerator` and `batch_generate` ([generate.py lines 1488-1527](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/mlx_lm/generate.py#L1488-L1527), [1887-1958](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/mlx_lm/generate.py#L1887-L1958)); oMLX and vLLM-MLX both drive continuous batching through BatchGenerator ([oMLX scheduler.py lines 1-12](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/scheduler.py#L1-L12), [vLLM-MLX scheduler.py lines 1-12](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/scheduler.py#L1-L12)). | `rewrite_as_owlmlx_mechanism` | `P1_next_rc_accelerator` | Adopt the mechanism shape only after profile P0. It must preserve owlmlx's serial gate and request truth semantics until proven safe. |
| Model residency and lifecycle | oMLX EnginePool supports preload, LRU eviction, pinning, manual load/unload, TTL, and memory checks ([README lines 157-165](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/README.md#L157-L165), [engine_pool.py lines 360-460](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/engine_pool.py#L360-L460)); vLLM-MLX has a single-flight residency manager and registry-backed memory-budget eviction ([lifecycle.py lines 17-252](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/lifecycle.py#L17-L252), [model_registry.py lines 361-530](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/model_registry.py#L361-L530)). | `rewrite_as_owlmlx_mechanism` | `P1_next_rc_accelerator` | owlmlx already owns load/unload/restart truth; peer-runtime lifecycle patterns should inform policy tests, not be copied wholesale. |
| Memory pressure and reclaim | oMLX polls Metal active memory, unloads LRU non-pinned engines, and propagates limits into schedulers ([process_memory_enforcer.py lines 3-12](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/process_memory_enforcer.py#L3-L12), [151-200](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/process_memory_enforcer.py#L151-L200)); vLLM-MLX can evict idle loaded models by memory budget ([model_registry.py lines 675-770](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/model_registry.py#L675-L770)). | `rewrite_as_owlmlx_mechanism` | `P1_next_rc_accelerator` | Keep owlmlx reclaim policy runtime-owned; use peer references as acceptance-case inspiration. |
| SSD/tiered cache | oMLX README and paged SSD cache document prefix sharing, safetensors restore, async writes, LRU, startup scan, and cache format versioning ([README lines 138-151](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/README.md#L138-L151), [paged_ssd_cache.py lines 3-14](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/cache/paged_ssd_cache.py#L3-L14), [53-81](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/cache/paged_ssd_cache.py#L53-L81)). | `rewrite_as_owlmlx_mechanism` | `P3_future_engine_depth` | Not a mainline P0; useful after owlmlx has profile and basic cache counters closed. |
| DeepSeek V4 JANGTQ / DSV4 adapter path | vMLX describes DeepSeek V4 architecture, stop markers, reasoning mode, and custom cache in model configs ([model_configs.py lines 498-561](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/model_configs.py#L498-L561)); tokenizer code registers DSV4 and routes bundles to a dedicated loader ([utils/tokenizer.py lines 709-729](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/utils/tokenizer.py#L709-L729), [816-845](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/utils/tokenizer.py#L816-L845)); the loader wraps a DSV4 prefill patch ([load_jangtq_dsv4.py lines 1-40](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/loaders/load_jangtq_dsv4.py#L1-L40), [60-180](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/loaders/load_jangtq_dsv4.py#L60-L180)). | `vendor_candidate_requires_license_review` | `P2_deepseek_pressure_lane` | Candidate only for isolated DeepSeek adapter work. It must not be generalized into mainline support or copied before license/provenance/dependency review. |
| MoE expert reduction / Smelt / TurboQuant | vMLX README lists JANG profiles and Smelt partial expert loading ([README lines 575-635](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/README.md#L575-L635)); scheduler surfaces TurboQuant precedence and DSV4 cache schema details ([scheduler.py lines 336-350](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/scheduler.py#L336-L350), [559-593](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/vmlx_engine/scheduler.py#L559-L593)). | `do_not_adopt_now` | `P2_deepseek_pressure_lane` | Keep as DeepSeek/Gemma pressure research until owlmlx has a tested profile layer and a legal path for any borrowed pieces. |
| Model acquisition, conversion, and artifact manifest | MLX-LM has conversion/quantization/upload APIs ([README lines 92-108](https://github.com/ml-explore/mlx-lm/blob/df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae/README.md#L92-L108)); vLLM-MLX provides model inspect/acquire/convert commands with artifact manifest language ([README lines 199-210](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/README.md#L199-L210)). | `use_directly_from_ecosystem` | `P3_future_engine_depth` | Use MLX/HF tooling and record provenance in owlmlx metadata; do not build a broad acquisition product inside this audit line. |
| Benchmarks and metrics | oMLX has admin benchmark metrics including TTFT/TPOT/TPS/peak/cached ([admin/benchmark.py lines 1-6](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/admin/benchmark.py#L1-L6), [138-169](https://github.com/jundot/omlx/blob/bac678ec72c97e497d05c3c6d637fa54f1b3d7e3/omlx/admin/benchmark.py#L138-L169)); vLLM-MLX exposes status/cache stats and cache clear/rewarm endpoints ([server.py lines 3070-3208](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/server.py#L3070-L3208)). | `rewrite_as_owlmlx_mechanism` | `P1_next_rc_accelerator` | Expand owlmlx's model RC evidence rather than importing peer-runtime admin surfaces. OwlOps should consume owlmlx history records. |
| OpenAI/Anthropic compatibility behavior that affects runtime profiles | vLLM-MLX request schema includes `enable_thinking` and `thinking_token_budget` ([api/models.py lines 180-193](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/api/models.py#L180-L193)); server reasoning code maps reasoning into OpenAI/Anthropic stream behavior ([server.py lines 5210-5358](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/server.py#L5210-L5358), [5539-5745](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/vllm_mlx/server.py#L5539-L5745)). | `profile_config_only` | `P0_current_rc_blocker` | Endpoint defaults should route into the same resolved profile and reasoning policy. |
| Multimodal, audio/TTS/STT, MCP, broad tool parsers, UI/panel features | vLLM-MLX and vMLX README files advertise broad multimodal/audio/tool/API surfaces ([vLLM-MLX README lines 46-74](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/README.md#L46-L74), [vMLX README lines 174-225](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/README.md#L174-L225)). | `do_not_adopt_now` | `not_now` | These belong above owlmlx or outside the current model RC closure. Do not broaden the runtime line around them. |
| Distributed serving, speculative/MTP, PLD, JIT, and advanced engine experiments | vLLM-MLX and vMLX expose distributed/speculative/MTP/sparse-prefill/JIT style features ([vLLM-MLX README lines 66-70](https://github.com/waybarrios/vllm-mlx/blob/e69435608fa625b0dd4853cc118c968470a1b530/README.md#L66-L70), [vMLX README lines 188-209](https://github.com/jjang-ai/vmlx/blob/3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69/README.md#L188-L209)). | `do_not_adopt_now` | `P3_future_engine_depth` | Keep as future engine research; not needed to close current profile blockers. |

## 5. License And Provenance Boundary

Direct ecosystem use is not vendoring. Using `mlx-lm` as a dependency remains
the preferred route for model loading, tokenization, cache classes, and
single-request generation because `mlx-lm` is the primary MLX ecosystem layer
and is MIT-licensed in the inspected snapshot.

Vendor candidates require explicit legal/provenance review before code reuse.
None are approved for import by this audit alone.

| Candidate | Peer/reference repo | License observed | Exact file/module candidate | Why direct code reuse might be better than rewrite | Required attribution/provenance work | Why this does not turn owlmlx into a peer-runtime fork |
|---|---|---|---|---|---|---|
| Uncompiled sampler/RNG safety primitive | `oMLX` | Apache-2.0 (`pyproject.toml:5-11`, `LICENSE:1-35`) | `omlx/utils/sampling.py` | It is a narrow patch around a concrete server RNG hazard; if owlmlx reproduces the issue, copying the tested primitive may be safer than re-deriving subtle MLX RNG behavior. | Preserve Apache-2.0 license/NOTICE requirements, source commit `bac678e...`, file-level attribution, local tests proving need, and a diff-minimized vendor note. | The candidate is a single primitive behind owlmlx's profile/runtime contract, not the oMLX engine, scheduler, admin app, or identity. |
| DeepSeek V4 JANGTQ / DSV4 loader shim and cache patch references | `vMLX` | Apache-2.0 (`pyproject.toml:5-11`, `LICENSE:1-35`) | `vmlx_engine/loaders/load_jangtq_dsv4.py`, relevant routing in `vmlx_engine/utils/tokenizer.py`, and only the minimal DSV4 cache/batch patches needed after live reproduction | The path encodes specific DSV4 bundle layout, registration, mask/cache bugs, and JANGTQ sidecar behavior that would be expensive and risky to rediscover from scratch. | Review Apache-2.0 obligations, JANG/JANGQ dependency licenses, model-asset terms, sidecar provenance, source commit `3ae0b...`, and isolate the code behind an experimental DeepSeek adapter namespace. | It is limited to the DeepSeek experimental lane and would not replace owlmlx's scheduler, cache policy, model profile resolver, or public runtime identity. |

Everything else in this audit is either direct ecosystem use, owlmlx-owned
rewrite, profile configuration, or not adopted now.

## 6. Adoption Route Matrix

| Adoption route | Mechanisms |
|---|---|
| `use_directly_from_ecosystem` | MLX-LM loading/tokenizer/generation API; MLX-LM single-request `stream_generate`; MLX/HF model acquisition and conversion tools. |
| `rewrite_as_owlmlx_mechanism` | Model profile resolver; owlmlx reasoning router/parser; thinking budget policy; prefill/TTFT control; prompt/prefix cache policy; continuous batching scheduler; model lifecycle; memory pressure/reclaim; SSD/tiered cache policy; benchmark/metrics evidence surfaces. |
| `profile_config_only` | Chat-template kwargs; Qwen3.6 defaults; Gemma4 defaults; stop-token augmentation; Gemma mixed-attention cache caution; OpenAI/Anthropic profile-affecting defaults. |
| `vendor_candidate_requires_license_review` | oMLX sampler/RNG safety primitive; vMLX DeepSeek V4 JANGTQ/DSV4 adapter references. |
| `do_not_adopt_now` | Broad multimodal/audio/MCP/panel/tool-parser surfaces; broad MoE/Smelt/TurboQuant adoption; distributed/speculative/MTP/PLD/JIT engine experiments. |

## 7. Mapping To Current Model RC Blockers

### 7.1 Gemma line: `gemma-4-31B-it`

Current blocker: `repetitive_output`.

Likely causes, in priority order:

1. Chat template or prompt wrapping: Gemma4 uses channel markers and needs
   model-specific cleanup; both vMLX and vLLM-MLX have Gemma4 parser/profile
   logic.
2. Stop-token handling: vMLX adds `<turn|>` alongside `<eos>` for Gemma4.
3. Repetition/sampling policy: repetitive output should be measured with
   deterministic and repetition-penalty variants before scheduler changes.
4. Prefix-cache hazard: vMLX explicitly bypasses mixed-attention prefix cache
   for Gemma4 because reconstructed cache can create loops.

Most relevant peer-reference and ecosystem mechanisms:

- vMLX Gemma4 profile defaults and stop-token cleanup.
- vLLM-MLX Gemma4 channel parser.
- MLX-LM Gemma4 cache construction and tokenizer/template behavior.

Next owlmlx solution shape:

- Start as `Gemma profile` plus the generic owlmlx profile resolver.
- Add `gemma4` stop tokens, channel cleanup, `enable_thinking`/reasoning
  policy, repetition policy, and a cache-bypass/caution flag.
- Do not start with a backend decode overhaul unless direct MLX-LM baseline
  reproduces the same repetition under the same prompt/profile.

### 7.2 Qwen3.6-35B-A3B line

Current blockers: high TTFT and `reasoning_trace_truncated`.

Likely causes, in priority order:

1. Thinking/template policy: Qwen3.6 MoE needs qwen profile defaults,
   `think_in_template`, and explicit `enable_thinking` behavior.
2. Max token and thinking budget behavior: a short generation can be consumed
   by reasoning before content appears.
3. Prefill configuration: TTFT is visibly higher than decode speed in the v2
   record, so prefill/warm-prefix experiments are relevant.
4. Decode loop: lower priority for Qwen35 because decode speed is not the
   dominant metric in the v2 record.

Most relevant peer-reference and ecosystem mechanisms:

- vMLX `qwen3_5_moe_text` registration with qwen parser and `think_in_template`.
- MLX-LM tokenizer thinking inference and `apply_chat_template`.
- oMLX/vLLM-MLX thinking budget parsers and vLLM-MLX prompt warm-up design.

Smallest runtime-owned experiment:

- Add a Qwen35 profile with explicit `enable_thinking` modes, reasoning parser,
  max-token/budget settings, and prefill step size evidence.
- Run one same-prompt comparison through owlmlx HTTP and direct MLX-LM
  `stream_generate`, recording TTFT, decode speed, and whether content appears
  before max tokens.

### 7.3 Qwen3.6-27B line

Current blocker: slow decode despite valid output.

Likely first gap:

1. owlmlx wrapper overhead or stream event path.
2. Sampler/logits path differences.
3. Resident model path behavior or extra evaluation/synchronization.
4. Cache policy only after direct stream baseline is measured.

Most relevant peer-reference and ecosystem mechanisms:

- MLX-LM direct `stream_generate`.
- oMLX sampler/RNG safety candidate only if owlmlx reproduces sampler drift.
- BatchGenerator/continuous batching is not the first test; it changes too many
  variables for a P0 decode diagnosis.

Smallest runtime-owned experiment:

- Same model, same prompt, same sampler, same max tokens: compare direct
  MLX-LM `stream_generate` against owlmlx HTTP streaming and record per-token
  decode timing. If direct MLX-LM is also slow, profile/model settings are the
  cause; if only owlmlx is slow, inspect wrapper/event overhead.

### 7.4 DeepSeek-V4-Flash-2bit-DQ line

Current lane: pressure/adaptation only.

Relevant mechanisms:

- vMLX DeepSeek V4 model config, stop markers, reasoning mode, and DSV4 cache
  contract.
- vMLX DSV4 registration and JANGTQ loader routing.
- DSV4 cache/prefill patch references, but only behind license/provenance
  review and live owlmlx reproduction.

Priority boundary:

- `P2_deepseek_pressure_lane`: DSV4 loader/adaptor proof, stop markers,
  reasoning parser, memory-headroom evidence, unload/restart evidence.
- Not mainline: Smelt/TurboQuant broad adoption, JANG conversion pipeline,
  DSV4 long-context ambitions, and any DeepSeek label stronger than
  `experimental`.

What must remain experimental-only:

- DeepSeek V4 HTTP adapter exposure until a runtime-owned adapter path exists.
- JANG/JANGTQ/DSV4 vendor code until license/provenance review is complete.
- Any claim that the 2bit-DQ pressure lane proves the mainline matrix.

## 8. What owlmlx Should Implement Next

P0 next round:

1. Add an owlmlx-owned `ModelProfile` resolver and typed profile contract for
   Qwen3.6 text, Qwen3.6 MoE, Gemma4 text, and DeepSeek V4 experimental.
2. Feed the resolved profile into chat template kwargs, stop tokens, sampler
   parameters, reasoning parser selection, thinking budget/max-token policy,
   and cache caution flags.
3. Run focused live evidence:
   - Gemma: profile variants for stop tokens, channel cleanup, repetition
     policy, and cache bypass.
   - Qwen35: `enable_thinking`/budget/max-token and prefill-step variants.
   - Qwen27: direct MLX-LM stream vs owlmlx HTTP stream with identical prompt.
4. Record each result through the existing model RC history surface, not a
   sidecar-only local note.

P1 next round after P0 evidence:

1. Add cache/prefix counters that distinguish prompt cache, prefix cache,
   cache bypass, and cache miss.
2. Add a minimal prefill/warm-prefix experiment only for a selected model and
   one prompt shape.
3. Start continuous-batching design from owlmlx's bounded admission/gate truth,
   not by copying a reference scheduler.

P2 DeepSeek-only round:

1. Audit JANG/JANGTQ/DSV4 dependency licenses and model-asset terms.
2. If legal/provenance passes, prototype an isolated experimental adapter
   namespace and keep it out of the mainline model gate.
3. Preserve memory peak source discrepancies instead of normalizing them.

## 9. What owlmlx Must Not Claim

The following words may appear only in this section or other explicit
forbidden-claim text, never as a positive current-state statement:

- `release-ready`
- `production-grade`
- `parity`
- `equivalent`
- `replacement`
- `beats`
- `wins`

This audit does not say owlmlx has matched oMLX, vMLX, vllm-mlx, or MLX-LM.
It only classifies mechanisms and proposes the next runtime-owned closure
round.

## 10. Open Questions / Blockers

- The exact owlmlx runtime code path for current chat-template kwargs, stop
  token propagation, and sampler invocation still needs a follow-up
  implementation round. This audit intentionally did not edit code.
- The vMLX DSV4 path depends on JANG/JANGQ/JANGTQ pieces whose licensing and
  model-asset terms were not fully reviewed in this audit. Treat DSV4 vendor
  work as blocked pending provenance review.
- The vMLX peer-reference clone initially failed over HTTP/2 and succeeded over
  HTTP/1.1. The inspected commit is recorded above; future audits should
  refresh the snapshot before implementation.
- Peer-reference and ecosystem repos are moving targets. Any future vendor decision must re-check
  the exact source commit, package metadata, and license file at the time of
  adoption.
