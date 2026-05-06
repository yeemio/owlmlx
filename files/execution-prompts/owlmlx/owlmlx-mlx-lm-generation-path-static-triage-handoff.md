# owlmlx MLX-LM Generation Path Static Triage Handoff

> Status: handoff
> Updated: 2026-05-05
> Outcome label: `owlmlx_mlx_lm_generation_path_static_triage_closed`
> Scope: docs/static-introspection closeout. No heavy model load, external
> repository edit, or peer-runtime code vendoring occurred.

## Result

The static triage document is archived at:

`docs/source-of-truth/mlx-lm-generation-baseline-triage.md`

The source-of-truth index was updated in:

`docs/source-of-truth/master-outline.md`

## Local API Facts Captured

Required `mlx_lm` import/signature probe passed:

- `mlx_lm.__file__`:
  `/Users/yeemio/AI/gitrep/owlmlx/.venv/lib/python3.11/site-packages/mlx_lm/__init__.py`
- `mlx_lm.load(path_or_hf_repo, tokenizer_config=None, model_config=None,
  adapter_path=None, lazy=False, return_config=False, revision=None)`
- `mlx_lm.generate(model, tokenizer, prompt, verbose=False, **kwargs)`
- `mlx_lm.stream_generate(model, tokenizer, prompt, max_tokens=256,
  draft_model=None, **kwargs)`

Additional local functions inspected:

- `mlx_lm.generate.generate_step`
- `mlx_lm.generate.GenerationResponse`
- `mlx_lm.generate.BatchGenerator`
- `mlx_lm.generate.BatchStats`
- `mlx_lm.sample_utils.make_sampler`
- `mlx_lm.sample_utils.make_logits_processors`
- `mlx_lm.tokenizer_utils.TokenizerWrapper.apply_chat_template`
- `mlx_lm.tokenizer_utils.TokenizerWrapper.add_eos_token`

## Concrete ModelProfile Levers Recommended

Recommended now as profile metadata or controlled experiment fields:

- `chat_template_kwargs.enable_thinking`
- `stop_token_strings`
- deterministic sampler defaults such as `temperature=0.0` and explicit
  `top_p`
- optional sampler experiment fields: `min_p`, `top_k`,
  `min_tokens_to_keep`
- logits-processor experiment fields: repetition, presence, and frequency
  penalties
- `prefill_step_size` for Qwen35 TTFT experiments
- `prompt_template_id` and same-template direct-baseline provenance
- `reasoning_parser_family`, `thinking_policy`, and conservative
  `cache_policy` caveats

Per-model recommendations:

- `qwen3_6_text`: explicit `enable_thinking=True`, `<|im_end|>`, deterministic
  sampler defaults, and same-prompt direct-vs-HTTP decode timing proof.
- `qwen3_6_moe`: explicit thinking policy, max-token/thinking-budget
  experiment metadata, and `prefill_step_size` TTFT proof.
- `gemma4_text`: Gemma stop markers, channel cleanup metadata,
  repetition-policy experiment knob, and cache caution until model-family cache
  proof exists.
- `deepseek_v4_experimental`: keep stop/thinking metadata experimental only.

## Deferred Live Proof

Requires a later heavy-model lane:

- Qwen27 direct `mlx_lm.stream_generate` versus owlmlx HTTP streaming with the
  same prompt, template, sampler, and max tokens.
- Qwen35 bounded-thinking and prefill-step experiments.
- Gemma stop-marker, channel-cleanup, and repetition-policy experiments.
- Generic stop-string matching on owlmlx HTTP single-stream output.
- Prefix-cache reuse/bypass, KV quantization, prompt-cache acceleration, XTC,
  and speculative decoding behavior.

## Must-Not-Claim Check

Do not summarize this handoff as any of:

- `release-ready`
- `production-grade`
- `parity`
- `equivalent`
- `superior`

Those words are present here only as forbidden-claim text.

## Suggested Next Prompt

Run only when a heavy-model lane is authorized:

```markdown
# owlmlx Direct MLX-LM Versus HTTP Same-Profile Live Baseline

Work in `/Users/yeemio/AI/gitrep/owlmlx`.

Read first:

1. `AGENTS.md`
2. `docs/source-of-truth/mlx-lm-generation-baseline-triage.md`
3. `docs/source-of-truth/model-release-candidate-program.md`
4. `owlmlx/model_profile.py`

Goal:

Create a runtime-owned live evidence harness that compares direct
`mlx_lm.stream_generate` against owlmlx HTTP streaming using the same model id,
same prompt, same resolved `ModelProfile`, same chat-template kwargs, same
sampler defaults, same max tokens, and same stop metadata.

Start with `Qwen3.6-27B` only.

Hard rules:

- This is a heavy-model lane; run only after coordinator authorization.
- Preserve existing dirty/staged work.
- Do not vendor peer-runtime code.
- Do not edit external repositories.
- Keep labels honest: `supported`, `partial`, `experimental`, or
  `not in scope`.

Evidence to record:

- model id and profile id
- exact prompt/template provenance
- direct `mlx_lm` load wall clock, TTFT, decode TPS, total wall clock, output
  sanity, peak memory if available
- owlmlx HTTP load/generate/unload timing, TTFT, decode TPS, total wall clock,
  output sanity, and process-tree RSS
- verdict: wrapper overhead indicated, shared `mlx_lm`/model behavior
  indicated, or inconclusive

Final response:

- outcome label
- files changed
- evidence path
- exact commands run
- blockers/deferred proof
- whether staged
```
