# owlmlx MLX-LM Generation Baseline Triage

> Status: authoritative static triage
> Updated: 2026-05-05
> Outcome label: `owlmlx_mlx_lm_generation_path_static_triage_closed`
> Scope: local installed `mlx_lm` API/source introspection only. No model load,
> external repository edit, or peer-runtime code vendoring occurred.

## 1. Purpose

This document closes a static triage lane for the current Model RC generation
gap. It explains which local `mlx_lm` generation knobs are visible in the
installed runtime, which parts belong in owlmlx-owned `ModelProfile` policy,
and which parts still need live proof before they can become supported
profile behavior.

The key boundary is:

- direct `mlx_lm.stream_generate` can be measured as the same-host baseline
- owlmlx can own profile policy around prompts, templates, stops, sampling,
  and timing evidence
- oMLX, vMLX, and vllm-mlx remain peer reference runtimes and design/test
  inputs, not code sources for this lane

## 2. Static Inspection Inputs

Local package inspected:

`/Users/yeemio/AI/gitrep/owlmlx/.venv/lib/python3.11/site-packages/mlx_lm`

Required import/signature probe result:

```text
mlx_lm /Users/yeemio/AI/gitrep/owlmlx/.venv/lib/python3.11/site-packages/mlx_lm/__init__.py
load (path_or_hf_repo: str, tokenizer_config: Optional[Dict[str, Any]] = None, model_config: Optional[Dict[str, Any]] = None, adapter_path: Optional[str] = None, lazy: bool = False, return_config: bool = False, revision: Optional[str] = None) -> Union[Tuple[mlx.nn.layers.base.Module, mlx_lm.tokenizer_utils.TokenizerWrapper], Tuple[mlx.nn.layers.base.Module, mlx_lm.tokenizer_utils.TokenizerWrapper, Dict[str, Any]]]
generate (model: mlx.nn.layers.base.Module, tokenizer: Union[transformers.tokenization_python.PythonBackend, mlx_lm.tokenizer_utils.TokenizerWrapper], prompt: Union[str, List[int]], verbose: bool = False, **kwargs) -> str
stream_generate (model: mlx.nn.layers.base.Module, tokenizer: Union[transformers.tokenization_python.PythonBackend, mlx_lm.tokenizer_utils.TokenizerWrapper], prompt: Union[str, mlx.core.array, List[int]], max_tokens: int = 256, draft_model: Optional[mlx.nn.layers.base.Module] = None, **kwargs) -> Generator[mlx_lm.generate.GenerationResponse, NoneType, NoneType]
```

Additional local functions inspected:

| Local file | Function / object | Relevance |
|---|---|---|
| `.venv/lib/python3.11/site-packages/mlx_lm/utils.py` | `load`, `load_model`, `load_tokenizer` | Model/config/tokenizer load path and `return_config` behavior. |
| `.venv/lib/python3.11/site-packages/mlx_lm/generate.py` | `generate`, `stream_generate`, `generate_step`, `GenerationResponse`, `BatchGenerator`, `BatchStats` | Single-stream generation, prefill/decode timing, EOS stop behavior, and batch stop machinery. |
| `.venv/lib/python3.11/site-packages/mlx_lm/sample_utils.py` | `make_sampler`, `make_logits_processors` | Local sampler and logits-processor knobs. |
| `.venv/lib/python3.11/site-packages/mlx_lm/tokenizer_utils.py` | `TokenizerWrapper.apply_chat_template`, `TokenizerWrapper.add_eos_token`, thinking helpers | Chat-template behavior, extra EOS registration, and thinking-token detection. |

## 3. Effective Call Shapes

### 3.1 `mlx_lm.load`

Local call shape:

```python
mlx_lm.load(
    path_or_hf_repo,
    tokenizer_config=None,
    model_config=None,
    adapter_path=None,
    lazy=False,
    return_config=False,
    revision=None,
)
```

Behavior observed from `mlx_lm/utils.py`:

- `path_or_hf_repo` is resolved through `_download`.
- `load_model` reads `config.json` and `generation_config.json`, merges
  optional `model_config`, builds the model class, loads safetensors, applies
  quantization config when present, and evaluates parameters unless `lazy=True`.
- `load_tokenizer` wraps tokenizer loading and passes model-config EOS ids into
  `TokenizerWrapper`.
- `return_config=True` returns `(model, tokenizer, config)`.

owlmlx implication:

- live load timing is not emitted by `mlx_lm.load`; owlmlx must measure wall
  time around load requests.
- `lazy=True`, `return_config=True`, `tokenizer_config`, and `model_config`
  are policy levers, but changing them needs live proof per model family.

### 3.2 `mlx_lm.generate`

Local call shape:

```python
mlx_lm.generate(model, tokenizer, prompt, verbose=False, **kwargs)
```

Behavior observed from `mlx_lm/generate.py`:

- `generate` is a collector around `stream_generate`.
- it returns concatenated text.
- when `verbose=True`, it prints prompt token count, prompt tokens per second,
  generation token count, generation tokens per second, and peak memory.

owlmlx implication:

- `generate` is useful for CLI-style proof, but `stream_generate` is the better
  baseline for owlmlx HTTP streaming comparison because it exposes per-response
  timing fields.

### 3.3 `mlx_lm.stream_generate`

Local call shape:

```python
mlx_lm.stream_generate(
    model,
    tokenizer,
    prompt,
    max_tokens=256,
    draft_model=None,
    **kwargs,
)
```

Important forwarded kwargs come from `generate_step`:

```python
generate_step(
    prompt,
    model,
    max_tokens=256,
    sampler=None,
    logits_processors=None,
    max_kv_size=None,
    prompt_cache=None,
    prefill_step_size=2048,
    kv_bits=None,
    kv_group_size=64,
    quantized_kv_start=0,
    prompt_progress_callback=None,
    input_embeddings=None,
)
```

Behavior observed from `mlx_lm/generate.py`:

- string prompts are encoded with inferred special-token handling unless the
  caller passes token ids directly.
- `stream_generate` creates a `TokenizerWrapper` if needed.
- generation stops when the generated token is in `tokenizer.eos_token_ids` or
  `max_tokens` is reached.
- yielded `GenerationResponse` includes `text`, `token`, `logprobs`,
  `from_draft`, `prompt_tokens`, `prompt_tps`, `generation_tokens`,
  `generation_tps`, `peak_memory`, and `finish_reason`.

owlmlx implication:

- direct baseline runs can remove owlmlx wrapper variables by passing already
  templated token ids, a profile-derived sampler, and identical `max_tokens`.
- TTFT must still be measured by the caller around the first yielded response;
  `GenerationResponse` reports prompt throughput but not an explicit TTFT
  millisecond field.

## 4. Accepted Sampler And Logits Fields

Local sampler shape from `mlx_lm/sample_utils.py`:

```python
make_sampler(
    temp=0.0,
    top_p=0.0,
    min_p=0.0,
    min_tokens_to_keep=1,
    top_k=0,
    xtc_probability=0.0,
    xtc_threshold=0.0,
    xtc_special_tokens=[],
)
```

Local logits-processor shape:

```python
make_logits_processors(
    logit_bias=None,
    repetition_penalty=None,
    repetition_context_size=20,
    presence_penalty=None,
    presence_context_size=20,
    frequency_penalty=None,
    frequency_context_size=20,
)
```

CLI behavior from `mlx_lm/generate.py`:

- `--temp`, `--top-p`, `--min-p`, `--top-k`,
  `--xtc-probability`, `--xtc-threshold`,
  `--min-tokens-to-keep`, and `--seed` are accepted by the local command path.
- `seed` is applied in CLI `main` through `mx.random.seed(args.seed)`.
- `repetition_penalty`, `presence_penalty`, `frequency_penalty`, and
  `logit_bias` are available through `make_logits_processors`, but the local
  single-generate CLI path inspected here does not wire them from CLI flags.

owlmlx implication:

- `temperature`, `top_p`, `min_p`, `top_k`, `min_tokens_to_keep`, XTC fields,
  and deterministic seed handling are available locally.
- repetition, presence, frequency, and logit-bias behavior should be exposed as
  profile policy only after owlmlx wires an explicit logits-processor path and
  captures live output/latency proof.

## 5. Chat Template Behavior

Local behavior from `TokenizerWrapper.apply_chat_template`:

- if `enable_thinking` is absent, the wrapper injects
  `enable_thinking=self.has_thinking`.
- `has_thinking` is inferred from tokenizer vocabulary markers such as
  `<think>...</think>`, `<longcat_think>...</longcat_think>`, or
  channel-style thinking markers.
- if a custom `chat_template` callable exists, it is used and encoded when
  `tokenize=True`.
- otherwise the underlying Hugging Face tokenizer
  `apply_chat_template(..., tokenize=tokenize, return_dict=False, **kwargs)`
  is called.

Local CLI chat path:

- builds `messages` with optional system prompt and optional assistant prefill.
- calls `tokenizer.apply_chat_template(..., continue_final_message=has_prefill,
  add_generation_prompt=not has_prefill, **template_kwargs)`.
- accepts additional JSON kwargs through `--chat-template-config`.

owlmlx implication:

- a direct baseline can apply the same template path as owlmlx HTTP chat if it
  builds the same `messages`, passes the resolved profile
  `chat_template_kwargs`, and feeds the resulting token ids or prompt string
  into `stream_generate`.
- for Qwen profiles, `enable_thinking` must be explicit in evidence so a
  hidden tokenizer default does not explain a later gap.

## 6. Stop Tokens And Stop Strings

Local single-stream behavior:

- `stream_generate` stops on `token in tokenizer.eos_token_ids`.
- `TokenizerWrapper.add_eos_token(token)` can add an integer token id or token
  string to that EOS set.
- `finish_reason` is `"stop"` when the stop token is EOS and `"length"` when
  max tokens is reached.

Local batch behavior:

- `BatchGenerator(..., stop_tokens=...)` uses `SequenceStateMachine` over token
  sequences, so multi-token stop sequences exist in the batch-generation
  machinery.

Static limitation:

- the inspected single-stream `stream_generate` path does not expose generic
  stop-string matching.
- profile stop strings must either be converted into tokenizer EOS ids before
  generation, or implemented by owlmlx as a streaming post-token state machine
  with tests.

owlmlx implication:

- `stop_token_strings` belongs in `ModelProfile` now as policy metadata.
- treating arbitrary stop strings as supported runtime behavior requires live
  proof and explicit owlmlx stop matching or token-sequence machinery.

## 7. Timing Surfaces

Local single-stream surfaces:

- load wall clock: not built in; caller-owned measurement around `mlx_lm.load`.
- prompt/prefill throughput: `GenerationResponse.prompt_tokens` and
  `GenerationResponse.prompt_tps`.
- TTFT: caller-owned measurement from before `stream_generate` iteration to
  first yielded response.
- decode throughput: `GenerationResponse.generation_tokens` and
  `GenerationResponse.generation_tps`.
- total wall clock: caller-owned measurement around the full stream.
- peak memory: `GenerationResponse.peak_memory`.
- finish reason: `GenerationResponse.finish_reason`.

Local batch surfaces:

- `BatchStats` includes `prompt_tokens`, `prompt_tps`, `prompt_time`,
  `generation_tokens`, `generation_tps`, `generation_time`, and `peak_memory`.

owlmlx implication:

- Model RC evidence should continue to keep load time, TTFT, decode TPS, total
  wall clock, and peak memory as separate fields.
- direct `mlx_lm` baseline records should capture caller-side TTFT and total
  wall clock in addition to `GenerationResponse` fields.

## 8. ModelProfile Levers To Own Now

These levers can become owlmlx `ModelProfile` policy now as configuration or
evidence requirements:

| Lever | Recommended profile status | Reason |
|---|---|---|
| `chat_template_kwargs.enable_thinking` | `partial` | Local tokenizer may inject it implicitly; owlmlx should make it explicit per profile and record it in evidence. |
| `stop_token_strings` | `partial` | Strings can guide EOS augmentation or owlmlx-owned matching, but runtime matching still needs proof per path. |
| deterministic sampler defaults: `temperature=0.0`, `top_p=1.0` or explicit direct-baseline values | `supported` as profile metadata | These are stable config defaults and keep comparison runs controlled. |
| `min_p`, `top_k`, `min_tokens_to_keep` | `partial` | Locally accepted by `make_sampler`; profile use should start as experiment knobs until output and timing are measured. |
| repetition / presence / frequency penalties | `partial` | Local logits processors exist, but owlmlx must wire and verify them before treating behavior as supported. |
| `prefill_step_size` | `partial` | Locally accepted by `generate_step`; useful for Qwen35 TTFT experiments but not proven as a profile default. |
| `max_kv_size`, `kv_bits`, `kv_group_size`, `quantized_kv_start` | `experimental` | Locally accepted cache knobs; model-family safety needs dedicated live evidence. |
| `prompt_template_id` and same-template direct baseline marker | `supported` as evidence metadata | This is owlmlx-owned provenance, not a model behavior claim. |
| `reasoning_parser_family` and `thinking_policy` | `partial` | Profile metadata is safe now; streaming parser behavior needs separate tests. |
| `cache_policy` caution/bypass flags | `partial` | Safe as conservative policy metadata; acceleration claims require live proof. |

Concrete per-model recommendations:

- `qwen3_6_text`: keep `enable_thinking=True`, `<|im_end|>` as the first stop
  marker, deterministic sampler defaults, and require direct
  `stream_generate` versus owlmlx HTTP same-prompt timing.
- `qwen3_6_moe`: keep `enable_thinking=True`, `<|im_end|>`, explicit
  max-token/thinking-budget experiment metadata, and a `prefill_step_size`
  experiment lane for TTFT.
- `gemma4_text`: keep Gemma stop markers, channel cleanup metadata,
  deterministic sampler defaults, a repetition-penalty experiment knob, and a
  cache-caution flag until mixed-attention cache reuse has owlmlx proof.
- `deepseek_v4_experimental`: keep stop markers and thinking metadata in the
  experimental lane only; do not infer mainline behavior from this profile.

## 9. Levers Requiring Live Proof Before Support

These must not be promoted beyond `partial` or `experimental` without live
evidence:

- any claim that owlmlx HTTP decode overhead is or is not the Qwen27 blocker
- `prefill_step_size` improving Qwen35 TTFT without quality regression
- bounded thinking policy producing complete Qwen35 answers under selected
  `max_tokens`
- repetition / presence / frequency penalties fixing Gemma output without
  hiding template or stop-token bugs
- generic stop-string support on single-stream HTTP
- prefix-cache reuse, cache bypass, `max_kv_size`, KV quantization, or prompt
  cache acceleration per model family
- speculative decoding or draft-model behavior
- XTC sampler behavior under owlmlx serving

## 10. Peer Reference Boundary

Peer-reference mechanisms remain useful as test/design inputs only:

- oMLX sampler/RNG behavior remains a test hypothesis if owlmlx reproduces a
  local RNG or sampler drift issue.
- vMLX model-family profiles remain useful as profile-shape evidence for
  Qwen, Gemma, and DeepSeek experimental lanes.
- vllm-mlx reasoning parsers, stop-sequence handling, and request-surface
  fields remain useful as contract examples.
- MLX-LM is the local ecosystem dependency for loader, tokenizer, cache, and
  generation APIs inspected here.

No peer-runtime code is approved for vendoring by this triage.

## 11. Next Runtime-Owned Closure Round

Recommended next live proof:

1. Build one direct `mlx_lm.stream_generate` harness that uses the resolved
   owlmlx `ModelProfile` to apply chat template kwargs, sampler defaults,
   max tokens, and stop metadata.
2. For `Qwen3.6-27B`, run same prompt / same profile / same sampler through
   direct `mlx_lm.stream_generate` and owlmlx HTTP streaming, recording TTFT,
   decode TPS, total wall clock, output sanity, and profile id.
3. For `Qwen3.6-35B-A3B`, add a bounded thinking and prefill-step experiment
   only after the same-template baseline is recorded.
4. For `gemma-4-31B-it`, test stop markers, channel cleanup, and one
   repetition-policy variant before changing cache behavior.

This lane remains static closed. The live round must be separately authorized
because it will load heavy models.
