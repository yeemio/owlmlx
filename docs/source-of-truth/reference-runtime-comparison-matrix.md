# owlmlx Reference Runtime Comparison Matrix

> Status: authoritative
> Updated: 2026-05-06
> Scope: honest runtime-only comparison between `owlmlx` and the current local reference runtimes `oMLX` / `vMLX`

## 0. Latest Live Evidence Addendum

The latest same-host live comparison notes are:

`docs/source-of-truth/reference-runtime-live-comparison-gemma-20260506.md`

`docs/source-of-truth/reference-runtime-live-comparison-qwen27-qwen35-20260506.md`

`docs/source-of-truth/reference-runtime-live-comparison-deepseek-20260506.md`

They cover only short-prompt, `max_tokens=64`, `temperature=0`, same-host runs
on `Mac17,6-arm64-macOS-26.4.1-128GB`.

Current live evidence:

- `oMLX`: `rejected`, because oMLX generated visible text in attempt 1 but the
  service disconnected/restarted around lifecycle/unload, so no clean
  two-repeat measured Gemma record exists.
- `oMLX`: `measured` for `Qwen3.6-27B`, with `owlmlx` TPS `5.4482` vs `oMLX`
  TPS `2.8127`.
- `oMLX`: `measured` for `Qwen3.6-35B-A3B`, with `owlmlx` TPS `3.5349` vs
  `oMLX` TPS `2.4400`.
- `vMLX`: `measured`, with `owlmlx` TPS `3.7468` vs `vMLX` TPS `3.8304` under
  a reasoning-aware stream consumer for Gemma.
- `vMLX`: `rejected` for both local Qwen directories because `vMLX serve`
  selects the multimodal loader and the local reference venv lacks `mlx-vlm`.
- `DeepSeek-V4-Flash-2bit-DQ`: `rejected` against both Homebrew `oMLX 0.3.4`
  sidecar and local `vMLX` probe because current stock loader paths do not
  support `model_type=deepseek_v4`.
- `DeepSeek-V4-Flash-2bit-DQ`: `owlmlx` also rejects before observable first
  token through the same missing `deepseek_v4` loader support, and the failed
  load originally dirtied 8066 backend health until restart.
- `DeepSeek-V4-Flash-2bit-DQ`: follow-up runtime evidence now shows
  `owlmlx` returns a clean pre-load `unsupported_model_family` response for
  missing `deepseek_v4` loader support without dirtying 8066 health or adding
  load-failure recovery noise.
- Final-answer profile follow-up now wires `chat_template_kwargs` through the
  OpenAI chat surface and child `mlx_lm` runner, and records parser replay
  evidence at
  `files/evidence/owlmlx/model-release-candidates/20260506T064509Z-final-answer-parser-replay/manifest.json`.
  The subsequent live Gemma proof at
  `files/evidence/owlmlx/model-release-candidates/20260506T-gemma-enable-thinking-false-live-proof/record.json`
  completed two repeats with clean final text and clean post-run health.
  The same profile control also produced clean short-prompt final text for
  Qwen35 at
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-enable-thinking-false-live-proof/record.json`.
  A later Gemma follow-up moved this from runner-only behavior into the
  runtime-owned OpenAI chat default path:
  `files/evidence/owlmlx/model-release-candidates/20260506T-gemma-runtime-profile-default-live-proof/record.json`.
  That direct request sent no client-side profile kwargs, stop strings, or
  parser `extra_body`, yet still returned clean final text and clean post-run
  health.
  This improves Gemma and Qwen35 short-prompt output quality but is still not a
  full parity or replacement claim.
- Qwen35 TTFT follow-up has narrowed the short-workload latency spike to child
  `mlx_lm.stream_generate` cold first-response behavior rather than OpenAI
  route framing or chat-template rendering. Evidence:
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-ttft-raw-template-decomposition/summary.json`
  and
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-child-stream-timing-live-proof/summary.json`.
  This is root-cause evidence only; no warmup/prefill/cache optimization or
  parity claim is made.
- Model RC timing-gate follow-up now appends runtime stream timing fields to
  the cumulative ledger for raw stream evidence. Qwen35 gate proof:
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-model-rc-timing-gate-live-proof/timing-gate-summary.json`.
  It classifies the short-workload Qwen35 latency as
  `cold_first_response_dominant`, not optimized.
- Qwen35 experimental prefill-warmup follow-up produced a bounded Model
  RC-only mitigation proof:
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-experimental-prefill-warmup-live-proof/timing-gate-summary.json`.
  Warmup first response was `3198.552ms`; the measured post-warmup first
  response was `210.355ms`; the row stayed `needs_optimization` and does not
  make warmup a default serving behavior.
- Model RC now consumes comparative-evidence rows directly. Qwen27 and Qwen35
  both read their same-model oMLX `measured` records and removed
  `reference_runtime_comparison_missing` from the latest Model RC rows:
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen27-reference-comparison-consumption-live-proof/record.json`
  and
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-reference-comparison-consumption-live-proof/record.json`.
- Gemma now also consumes its same-model vMLX reasoning-aware `measured`
  record from the cumulative comparative ledger. Latest Model RC proof:
  `files/evidence/owlmlx/model-release-candidates/20260506T-gemma-reference-comparison-consumption-live-proof/record.json`.
  It clears `reference_runtime_comparison_missing` for Gemma while keeping the
  broader claim narrow.

This improves the Gemma, Qwen27, and Qwen35 reference evidence floor, but it is
still not a parity claim and does not cover measured DeepSeek generation,
longer prompts, multi-turn behavior, concurrent workloads, cache reuse, or
final-answer quality across all mainline model families.

## 1. Purpose

This document exists to answer one narrow question honestly:

**Relative to `oMLX` and `vMLX`, where is `owlmlx` already close, where is it still behind, and which parts are intentionally not owned by each system?**

It is **not** a parity claim.

It is a truth document for:

- relative runtime maturity
- adoption/borrowing direction
- intentionally absent or shell-hosted capability
- mutual learning without identity collapse

## 2. Comparison Inputs

This matrix is based on four inputs:

1. `owlmlx` current authoritative truth:
   - `replacement-grade-stability-gaps.md`
   - `phase45-customer-runtime-evidence-ledger.md`
   - `phase45-dominant-gap-reselection.md`
2. `owlmlx` product/adoption boundary:
   - `product-definition.md`
   - `master-outline.md`
3. local probe verification:
   - `<runtime-probes repo>/2026-04-16-mlx-omlx-vmlx-baseline-investigation.md`
4. current `oMLX` / `vMLX` public repo surfaces:
   - `<runtime-probes repo>/omlx-probe/README.md`
   - `<runtime-probes repo>/vmlx-probe/README.md`

## 3. Current Honest Top-Level Verdict

### owlmlx

Current honest label remains:

- `early_formal_runtime`
- `below reference-grade stability`

### Relative to oMLX

`owlmlx` is no longer a toy relative to `oMLX`.

Current honest posture:

- **one tier behind in runtime maturity**
- closest gaps now concentrate in:
  - host-stable execution confidence
  - heavy-weight repeatability
  - deeper cache/scheduler closure

### Relative to vMLX

`owlmlx` is materially closer on substrate identity than before, but still
clearly behind `vMLX` on engine depth and broader serving maturity.

Current honest posture:

- **one to two tiers behind**
- biggest deficits concentrate in:
  - scheduler / batching depth
  - broader cache path maturity
  - packaging / runtime-product operationalization

## 4. Runtime Comparison Matrix

Legend:

- `ahead` = stronger in this dimension right now
- `close` = in the same tier or one small gap away
- `behind` = meaningfully weaker
- `not-owned` = intentionally outside current project boundary
- `unknown` = not enough current evidence

| Dimension | owlmlx | oMLX | vMLX | Honest read |
|---|---|---|---|---|
| Runtime identity / owned truth | runtime-owned identity, contracts, evidence, goal discipline | mature runtime/product, but not centered on runtime-owned truth ledgers | mature engine/product, but not centered on runtime-owned truth ledgers | `owlmlx` is **ahead** on truth discipline |
| Fresh MLX baseline | current re-validation shows fresh baseline can work locally | fresh clone/venv works | fresh clone/venv works | currently **close**, not a major gap |
| Core local serving path | real runtime kernel exists | mature multi-model local serving | mature multi-model serving engine | `owlmlx` still **behind** |
| OpenAI-compatible serving | yes | yes | yes | **close** |
| Anthropic-compatible serving/messages | yes | not the primary public identity | yes in product messaging | `owlmlx` is **close** |
| Cache evidence / truth surfaces | strong runtime-owned truth and exactness docs | mature practical cache behavior | mature practical cache behavior | `owlmlx` is **ahead on truth**, **behind on runtime closure** |
| Continuous batching / deeper scheduler work | frozen at structural ingress seam only | present publicly as continuous batching | present publicly as continuous batching and broader engine controls | `owlmlx` is **behind**, especially vs `vMLX` |
| Multi-model lifecycle governance | policy branch locally closed, but still below reference-grade residency parity | mature multi-model serving/ops behavior | mature runtime engine posture with broad feature surface | `owlmlx` is **behind** |
| Heavy-weight repeatability | not yet restored to reference-grade confidence | stronger historical proof on local platform | stronger engine-oriented confidence signals | `owlmlx` is **behind** |
| Packaging / app distribution | not-owned by runtime repo | app + Homebrew + CLI + admin shell | app/panel + PyPI/uv/pipx + engine CLI | `owlmlx` intentionally **not-owned** |
| Operator/admin surface | not-owned by runtime repo | built-in admin/dashboard surfaces | engine + panel/desktop workflow | `owlmlx` intentionally **not-owned** |
| Installation ergonomics | runtime repo only | strong end-user install story | strong end-user install story | `owlmlx` intentionally **not-owned** |
| Broad model-family productization | selective runtime substrate focus | broad productized family surface | very broad model-family surface | `owlmlx` is **behind** by choice |
| Runtime evidence honesty | strong | weaker as an explicit repo-level contract discipline | weaker as an explicit repo-level contract discipline | `owlmlx` is **ahead** |

## 5. “Deleted / Not-Owned” Comparison

The user asked for the comparison to include “各自删除的部分”.

For truth purposes, the useful version of that is:

- what each system **intentionally does not own**
- what each system currently leaves to another layer
- what should **not** be misread as a missing feature when it is actually a boundary choice

### 5.0 Side-by-side deletion / non-ownership matrix

| System | Explicitly deleted / not owned / not first-class | Why it matters |
|---|---|---|
| `owlmlx` | desktop shell, packaged app distribution, operator/admin UI, end-user installer ergonomics, control-plane product shell | prevents runtime repo from collapsing back into product-shell monolith |
| `oMLX` | not observed as first-class runtime-owned evidence ledgers, dominant-gap reselection truth, hard shell/runtime repo split | shows `oMLX` is optimized around practical runtime productization rather than truth-ledger formalism |
| `vMLX` | not observed as first-class runtime-owned evidence ledgers, dominant-gap reselection truth, hard shell/runtime split as primary identity | shows `vMLX` is optimized around engine breadth, packaging, and productized serving rather than runtime-truth formalism |

This table is intentionally asymmetric:

- `owlmlx` lists what is **deliberately removed from scope**
- `oMLX` / `vMLX` list what is **not currently observed as first-class repo identity**

That asymmetry is honest, because the systems are solving different primary
problems.

### 5.1 owlmlx - intentionally not owned

`owlmlx` intentionally does **not** own:

- desktop shell
- packaged macOS app distribution
- admin dashboard / operator UI
- end-user onboarding and installer ergonomics
- control-plane product shell

Those are above the runtime and belong to shell/operator layers such as
`owlops`, not to `owlmlx` itself.

This is a **boundary choice**, not a runtime defect.

### 5.2 oMLX - not observed as first-class runtime-owned truth

In the current public repo/product surface, `oMLX` is very strong on runtime
productization, but the following are **not observed as first-class owned truth
layers in the way `owlmlx` models them**:

- replacement-grade gap ledgers
- runtime-owned customer evidence ledgers
- dominant-gap reselection as a machine-readable surface
- shell/runtime separation as a hard repository boundary

This is **not a criticism**. It simply means `oMLX` optimizes for a different
center of gravity:

- practical serving product
- admin/product shell
- operational UX

rather than truth-ledger formalism.

### 5.3 vMLX - not observed as first-class truth-ledger runtime

In the current public repo/product surface, `vMLX` is very strong on serving
engine breadth and packaging ergonomics, but the following are **not observed as
the repo’s first-class identity layer** in the way `owlmlx` models them:

- replacement-grade runtime evidence ledgers
- exact dominant-gap reselection truth
- shell/runtime truth separation as the primary architectural story

Again, this is **not a defect report**. It reflects a different priority:

- engine/product capability breadth
- packaging and operator usability
- broad model-family support

## 6. Mutual Learning Matrix

This section exists so the comparison becomes useful rather than tribal.

| Learn from | Worth borrowing / studying | Should not be blindly copied |
|---|---|---|
| oMLX | tiered KV cache, practical multi-model operations, app/admin ergonomics, local service distribution | runtime identity, shell coupling, product-shell assumptions |
| vMLX | packaging patterns, install ergonomics, broader engine flag surface, distributed/engine posture, benchmark/product messaging | product identity, engine breadth claims before truth closure, shell/engine blending |
| owlmlx | runtime-owned truth, evidence discipline, governance semantics, explicit capability honesty, shell/runtime separation | over-freezing, narrative over-precision when fresh re-validation has not been rerun |

## 7. What This Means Operationally

### 7.1 What owlmlx should stop saying

`owlmlx` should **not** say:

- “we are far behind because our MLX baseline cannot even start”
- “we are basically at parity with oMLX”
- “we are basically at parity with vMLX”

All three are now too crude.

### 7.2 What owlmlx should say instead

More accurate statements are:

- `owlmlx` is now a real runtime, not a toy.
- Relative to `oMLX`, it is in the same broad arena but still one tier behind in replacement-grade runtime maturity.
- Relative to `vMLX`, it is closer on substrate than before, but still behind on broader engine/scheduler/productized serving depth.
- `owlmlx` is ahead on runtime-owned truth and evidence discipline.
- `owlmlx` intentionally does not own desktop shell, packaging, and operator UI.

## 8. Current Strategic Read

As of 2026-04-16:

- the old “current dev host baseline is definitely blocked” story has been weakened by re-validation
- this improves `owlmlx`'s relative position somewhat
- but it does **not** close the real remaining gaps:
  - host-stable execution confidence
  - heavy-weight repeatability
  - deeper cache/scheduler closure

So the honest strategic read is:

- **closer than before**
- **not close enough to claim replacement**
- **better than a toy**
- **still below reference-grade stability**

## 9. Update Rule

This document should be updated only when one of these changes:

1. `owlmlx` upgrades or downgrades its honest label
2. `owlmlx` materially re-enters or loses host-stable execution
3. one of the major comparison dimensions changes:
   - heavy-weight repeatability
   - scheduler/cache depth
   - shell/runtime boundary
4. public `oMLX` or `vMLX` reference surfaces materially change
