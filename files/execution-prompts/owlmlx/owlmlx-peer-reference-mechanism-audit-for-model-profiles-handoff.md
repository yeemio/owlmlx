# owlmlx Peer Reference Mechanism Audit For Model Profiles Handoff

> Status: handoff
> Updated: 2026-05-05
> Outcome label: `owlmlx_peer_reference_mechanism_audit_surface_closed`
> Scope: audit-only closeout for peer-reference and ecosystem mechanisms informing model-family
> profile work. No runtime code or external repository was changed.

## Result

The audit document is now archived at:

`docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md`

The source-of-truth index was updated in:

`docs/source-of-truth/master-outline.md`

## Sources Inspected

Required owlmlx documents were read first:

- `AGENTS.md`
- `docs/source-of-truth/model-release-candidate-program.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/reference-runtime-comparison-matrix.md`
- `docs/source-of-truth/runtime-capability-matrix.md`
- `docs/source-of-truth/public-surface.md`

Peer-reference / ecosystem read-only snapshots inspected under
`/tmp/owlmlx-peer-reference-audit-20260505`:

- `mlx-lm` at `df1d3f3c9a7aae402dcbb8f41d4c36bcc13a50ae`
- `oMLX` at `bac678ec72c97e497d05c3c6d637fa54f1b3d7e3`
- `vMLX` at `3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69`
- `vllm-mlx` at `e69435608fa625b0dd4853cc118c968470a1b530`

Local probes inspected:

- `/Users/yeemio/AI/gitrep/runtime-probes/2026-04-16-mlx-omlx-vmlx-baseline-investigation.md`
- `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe`
- `/Users/yeemio/AI/gitrep/runtime-probes/vmlx-probe`

Note: the first vMLX clone failed with an HTTP/2 framing error, then succeeded
with `git -c http.version=HTTP/1.1 clone --depth 1`.

## Top Recommendations

P0:

1. Implement an owlmlx-owned `ModelProfile` resolver before scheduler/cache
   adoption. Profiles should cover Qwen3.6 text, Qwen3.6 MoE, Gemma4 text, and
   DeepSeek V4 experimental.
2. Use profiles to drive chat-template kwargs, stop tokens, sampler defaults,
   reasoning parser selection, thinking budget/max-token policy, and cache
   caution flags.
3. Run focused evidence:
   - Gemma: stop tokens, channel cleanup, repetition policy, cache caution.
   - Qwen35: `enable_thinking`, thinking budget, max-token, prefill step size.
   - Qwen27: direct MLX-LM stream versus owlmlx HTTP stream with identical
     prompt/profile/sampler.

P1:

1. Add runtime-owned cache/prefix counters before deeper cache adoption.
2. Add one bounded prefill or warm-prefix experiment only after P0 profiles
   explain current blockers.
3. Design continuous batching from owlmlx gate/admission truth rather than by
   copying a peer-reference scheduler.

P2:

1. Keep DeepSeek V4 as a pressure/adaptation lane.
2. Review JANG/JANGTQ/DSV4 dependency and model-asset provenance before any
   vendor import.
3. Isolate any DSV4 adapter behind an experimental namespace and separate
   evidence label.

## License / Provenance Warnings

Vendor candidates only:

- `oMLX/omlx/utils/sampling.py`, Apache-2.0, narrow sampler/RNG safety
  primitive candidate after local reproduction.
- `vMLX/vmlx_engine/loaders/load_jangtq_dsv4.py` plus minimal related DSV4
  routing/cache references, Apache-2.0, blocked on JANG/JANGQ/JANGTQ and model
  asset provenance review.

No code is approved for vendoring by the audit itself.

## Must-Not-Claim Check

The audit must not be summarized as any of:

- `release-ready`
- `production-grade`
- `parity`
- `equivalent`
- `replacement`
- `beats`
- `wins`

Those words are allowed only in explicit forbidden-claim checks.

## Exact Next Execution Prompt Recommendation

Archive and run a focused implementation prompt named:

`files/execution-prompts/owlmlx/owlmlx-model-profile-resolver-p0-gemma-qwen-mainline.md`

Prompt:

```markdown
# owlmlx Model Profile Resolver P0 For Gemma And Qwen Mainline

You are working in `/Users/yeemio/AI/gitrep/owlmlx`.

Read first:

1. `AGENTS.md`
2. `docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md`
3. `docs/source-of-truth/model-release-candidate-program.md`
4. `docs/source-of-truth/release-readiness-execution-plan.md`
5. current diffs for `owlmlx/runtime/server.py`, `owlmlx/runtime/technical_preview.py`,
   `owlmlx/serving.py`, and model release-candidate runner files

Goal:

Implement a narrow owlmlx-owned `ModelProfile` resolver and wire it only where
needed to reduce the current mainline model blockers:

- `gemma-4-31B-it`: `repetitive_output`
- `Qwen3.6-35B-A3B`: high TTFT plus `reasoning_trace_truncated`
- `Qwen3.6-27B`: slow decode despite valid output

Hard boundaries:

- Do not vendor peer-runtime code.
- Do not modify external repos.
- Do not stop or kill ports `8001`, `8009`, or the active owlmlx preview
  server unless the coordinator explicitly authorizes a live rerun.
- Do not broaden into DSV4 implementation; DeepSeek remains experimental-only.
- Preserve existing dirty/staged work. Do not revert unrelated changes.

Implementation target:

1. Add typed profile data for:
   - `qwen3_6_text`
   - `qwen3_6_moe`
   - `gemma4_text`
   - `deepseek_v4_experimental`
2. Resolve profile from model id and local config fields when available.
3. Expose resolved profile fields for:
   - chat template kwargs
   - stop/eos token strings
   - sampler defaults
   - reasoning parser family
   - thinking enabled/default/budget policy
   - cache caution flags
4. Add focused tests for profile resolution and serialization.
5. If wiring into runtime surfaces is safe in this round, add only the smallest
   consumer link needed to record profile id and selected caveats in model RC
   records. Otherwise, archive the wiring handoff separately.

Verification:

- focused pytest for new profile tests
- existing model release-candidate surface tests
- `git diff --check`
- forbidden-claim grep over touched docs/prompts if any

Final report:

- outcome label
- files changed
- profile ids added
- runtime wiring completed or deferred
- tests run and results
- next recommended live evidence lane
```
