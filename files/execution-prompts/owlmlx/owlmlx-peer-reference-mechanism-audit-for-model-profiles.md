# owlmlx Peer Reference Mechanism Audit For Model Profiles

> Coordinator: owlmlx
> Date: 2026-05-05
> Executor type: single audit executor
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Outcome label: choose one of
> `owlmlx_peer_reference_mechanism_audit_surface_closed` or
> `owlmlx_peer_reference_mechanism_audit_still_blocked`

## 0. Why This Round Exists

`owlmlx` has entered the Model Release Candidate gate. The current mainline
records are live but not passable:

- `Qwen3.6-27B`: valid output, but decode is slow.
- `Qwen3.6-35B-A3B`: decode is better, but TTFT is high and output is
  `reasoning_trace_truncated`.
- `gemma-4-31B-it`: output is `repetitive_output`, so profile/template quality
  is the first blocker.
- `DeepSeek-V4-Flash-2bit-DQ`: pressure/adaptation lane only, not mainline.

The open question is not "can we copy oMLX/vMLX wholesale?" The question is:

**Which peer-reference mechanisms should become owlmlx-owned family profiles,
scheduler/cache/runtime mechanisms, or license-reviewed vendor candidates?**

This round is an audit and adoption-design round. Do not implement runtime
optimization code in this round.

## 1. Hard Boundaries

You are working in `/Users/yeemio/AI/gitrep/owlmlx`.

Do not modify external repos.
Do not touch OwlOps, OwlCoda, `/Users/yeemio/AI/Agent`, or old platform code.
Do not stop or kill `8001`, `8009`, or the owlmlx preview server.
Do not run heavy model loads unless you explicitly find this prompt is stale
and the coordinator has asked for live validation. This round is source/code
audit, not model execution.
Do not copy peer-runtime code into owlmlx.
Do not create release-ready, parity, replacement, production-grade, wins,
beats, or equivalent claims.

Allowed changes:

- add one new source-of-truth audit document
- update `docs/source-of-truth/master-outline.md` if you add the document
- add one handoff under `files/execution-prompts/owlmlx/`
- optionally update `docs/source-of-truth/release-readiness-execution-plan.md`
  with a short "audit completed / next lanes" note, but only if the audit is
  actually complete

## 2. Required Read Order

Read these owlmlx files first:

1. `AGENTS.md`
2. `docs/source-of-truth/model-release-candidate-program.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/reference-runtime-comparison-matrix.md`
5. `docs/source-of-truth/runtime-capability-matrix.md`
6. `docs/source-of-truth/public-surface.md`

Then inspect peer-reference and ecosystem sources. Prefer primary sources:

- `https://github.com/ml-explore/mlx-lm`
- `https://github.com/jundot/omlx`
- `https://github.com/jjang-ai/vmlx`
- `https://github.com/waybarrios/vllm-mlx`

If local probes exist, inspect them too:

- `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe`
- `/Users/yeemio/AI/gitrep/runtime-probes/vmlx-probe`
- `/Users/yeemio/AI/gitrep/runtime-probes/2026-04-16-mlx-omlx-vmlx-baseline-investigation.md`

If a source is unavailable, record that explicitly. Do not infer unavailable
source truth from memory.

## 3. Audit Scope

Build a mechanism inventory across `mlx-lm`, `oMLX`, `vMLX`, and `vllm-mlx`.
At minimum cover:

- chat template / model-family defaults
- tokenizer and stop-token handling
- thinking / reasoning trace controls
- sampler and RNG safety
- prefill and TTFT controls
- decode loop / streaming path
- prompt cache / prefix cache
- KV cache policy, paged KV, cache quantization, or rotating KV
- continuous batching and request scheduler
- model residency and multi-model lifecycle
- memory pressure, reclaim, unload, restart, or tiered/SSD cache behavior
- MoE / top-k / large-model pressure handling
- model acquisition / conversion / artifact manifest
- benchmark runner and metrics surfaces
- OpenAI / Anthropic compatibility surfaces that influence runtime behavior
- features that belong above owlmlx and should remain OwlOps/OwlCoda-owned

## 4. Required Classification

For every audited mechanism, classify it into exactly one adoption route:

- `use_directly_from_ecosystem`
- `rewrite_as_owlmlx_mechanism`
- `profile_config_only`
- `vendor_candidate_requires_license_review`
- `do_not_adopt_now`

Also assign one priority:

- `P0_current_rc_blocker`
- `P1_next_rc_accelerator`
- `P2_deepseek_pressure_lane`
- `P3_future_engine_depth`
- `not_now`

For any `vendor_candidate_requires_license_review`, record:

- peer/reference repo
- observed license
- exact file or module candidate
- why direct code reuse might be better than a rewrite
- required attribution/provenance work
- why this does not turn owlmlx into a peer-runtime fork

Do not mark any code as safe to vendor unless you have inspected the license
file or package metadata from a primary source.

## 5. Map To Current Model RC Blockers

The audit must end with concrete next recommendations for the current owlmlx
optimization lines:

### Gemma line

Current blocker: `repetitive_output`.

Answer:

- is this likely chat template, prompt wrapping, stop token, repetition penalty,
  tokenizer, sampler, or decode-loop behavior?
- which peer-reference or ecosystem mechanism is most relevant?
- should owlmlx solve it as `Gemma profile`, generic chat-template resolver, or
  backend decode change?

### Qwen3.6-35B-A3B line

Current blockers: high TTFT and `reasoning_trace_truncated`.

Answer:

- is this likely template/thinking control, prefill, prompt formatting, max
  token policy, or decode issue?
- which peer-reference or ecosystem mechanisms should be studied first?
- what would be the smallest runtime-owned experiment after this audit?

### Qwen3.6-27B line

Current blocker: slow decode despite valid output.

Answer:

- is the first likely gap sampler, stream wrapper overhead, cache policy,
  MLX-LM invocation mode, model residency, or reference-runtime fast path?
- which peer-reference or ecosystem mechanism should be tested first?

### DeepSeek-V4-Flash-2bit-DQ line

Current lane: pressure/adaptation only.

Answer:

- which mechanisms are relevant to a 96GB-class 2bit-DQ / large MoE pressure
  lane?
- which should be `P2_deepseek_pressure_lane`, not mainline release gate?
- what must remain experimental-only?

## 6. Deliverables

Create:

1. `docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md`
2. `files/execution-prompts/owlmlx/owlmlx-peer-reference-mechanism-audit-for-model-profiles-handoff.md`

If you add the source-of-truth document, update:

- `docs/source-of-truth/master-outline.md`

Optional, only if the audit is complete and internally consistent:

- append a short note to
  `docs/source-of-truth/release-readiness-execution-plan.md`

## 7. Audit Document Required Shape

The source-of-truth document must include:

1. `Status / Updated / Scope`
2. `Executive Verdict`
3. `Sources Inspected`
4. `Mechanism Inventory`
5. `License And Provenance Boundary`
6. `Adoption Route Matrix`
7. `Mapping To Current Model RC Blockers`
8. `What owlmlx Should Implement Next`
9. `What owlmlx Must Not Claim`
10. `Open Questions / Blockers`

The mechanism inventory must be evidence-backed. Every material claim should
have either:

- local file path + line number
- peer-reference or ecosystem URL + exact section / line when available
- explicit note that source was unavailable and the row is blocked

Do not paste long peer-runtime code. Quote only tiny identifiers or short
phrases when needed.

## 8. Acceptance Criteria

This round can return `owlmlx_peer_reference_mechanism_audit_surface_closed` only if:

- all required owlmlx docs were read
- all available peer-reference / ecosystem / local probe sources were inspected or explicitly
  recorded as unavailable
- every audited mechanism has exactly one adoption route
- current RC blockers are mapped to concrete next owlmlx actions
- license/provenance boundaries are explicit
- no runtime code was changed
- no external repo was changed
- no banned readiness/parity/replacement claim was introduced
- `git diff --check` passes

Return `owlmlx_peer_reference_mechanism_audit_still_blocked` if source access,
license ambiguity, or stale repo state prevents an honest audit.

## 9. Verification Commands

Run at minimum:

```bash
git diff --check
rg -n "release-ready|production-grade|parity|equivalent|replacement|beats|wins" \
  docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md \
  files/execution-prompts/owlmlx/owlmlx-peer-reference-mechanism-audit-for-model-profiles-handoff.md
```

If you update `master-outline.md`, verify that the referenced document path
exists.

If the grep hits are only in forbidden-claim or "must not claim" sections,
record that as non-blocking. If any hit is a positive current claim, fix it
before returning.

## 10. Final Report Required

Return a concise final report with:

- outcome label
- files changed
- sources inspected
- top P0/P1 adoption recommendations
- license/provenance warnings
- verification commands and results
- exact next execution prompt recommendation

Do not say owlmlx is ready to publish.
Do not say owlmlx has matched oMLX or vMLX.
Do not tell OwlOps to infer runtime truth locally.
