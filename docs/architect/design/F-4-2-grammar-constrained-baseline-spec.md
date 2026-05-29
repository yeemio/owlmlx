# F-4.2 · Grammar-Constrained Baseline · Design-Grade Spec

> **Grade**: design-grade (defines code-grade + bench-grade phases; this document
> implements no code and runs no matrix).
> **Supersedes**: the prompt-only stratified-matrix definition of F-4.2 in
> [`F-4-structured-output-invariance-spec.md`](F-4-structured-output-invariance-spec.md) §4.3.
> That definition asked for `hard_break_count=0` at N≥1000 from prompt-only
> generation; the F-4.1 smoke matrix (59/60 hard breaks) and the grammar
> feasibility probe (control 10/10 break) make a prompt-only path a dead end.
> **Origin**: F-4 spec §12.1 `verdict=probe-positive`; recommended direction
> "grammar-constrained baseline".
> **Status**: drafted 2026-05-28. Authored in the same session as the F-4.1
> closeout and the grammar feasibility probe, NOT in a fresh session as
> `feedback-fresh-session-grade-transitions` prefers. This is a known
> capability-honesty risk; the spec compensates by (a) grounding every claim in
> the committed probe evidence `20260528T063524Z-f4-grammar-feasibility-probe*`
> and the read mlx-lm/xgrammar source, and (b) marking every not-yet-verified
> assertion as a code-grade verification step rather than a settled fact.
> **Honesty ceiling**: F-4 capability label stays `experimental`. Nothing in
> this spec promotes a label. A `partial_candidate` discussion is gated on
> F-4.2b passing on the full matrix and is explicitly out of this spec's scope.

---

## 1. Purpose

Build the first structured-output path on owlmlx that produces parseable JSON at
a usable rate, by constraining decoding with a grammar instead of relying on
prompt instructions. The probe established that:

- mlx-lm 0.31.3 (mainline PyPI) exposes `logits_processors` on
  `generate_step` / `stream_generate` with signature
  `(tokens, logits) -> logits`, `logits` shape `[1, vocab_size]`.
- xgrammar 0.2.1 compiles a JSON schema to a `GrammarMatcher` whose per-step
  bitmask can be applied to mlx logits via a numpy `unpackbits` bridge
  (`apply_token_bitmask_inplace` is torch-only and is deliberately avoided).
- On `json_schema_flat` / Qwen 35B-A3B 4bit / temp 0.3, grammar lifted
  `json_parse_failed_rate` from 1.00 (control) to 0.00 (treatment) at a
  1.125× tokens/sec cost — all in-process.

F-4.2 turns that in-process probe into a production path through the
subprocess backend, then re-validates it across the full F-4 family/model
matrix.

## 2. Prerequisites

F-4.2 code-grade may start when all are true:

- F-4.0 + F-4.1 committed (`24d94e7f`, `deb2940f`) and pushed.
- Grammar probe committed (`d3d8273e`) with `verdict=probe-positive`.
- `mlx_lm.stream_generate` still exposes `logits_processors` passthrough on the
  installed version (re-confirm at code-grade; do not assume across upgrades).

## 3. Architecture Decision: Grammar Runs Child-Side

This is the resolution of F-4 spec §12.1 unresolved problem #1.

`MlxLmSubprocessBackend` ([`mlx_lm_subprocess_backend.py`](../../owlmlx/runtime/mlx_lm_subprocess_backend.py))
never imports mlx-lm in the owlmlx parent. Each loaded model owns a persistent
child runner (`owlmlx.runtime.mlx_lm_runner`, launched `python -m`). Parent and
child speak newline-delimited JSON over the child's stdin/stdout
(`proc.stdin.write(json.dumps(request) + "\n")`).

A live `xgrammar.GrammarMatcher` is a C++-backed object holding a Python
closure; it is **not** JSON-serializable and cannot cross that boundary.
Therefore:

```text
PARENT                              CHILD (mlx_lm_runner)
------                              ---------------------
stream_generate request            receives request
  + grammar spec (JSON schema,  →   builds xgrammar TokenizerInfo from the
    serializable)                     loaded tokenizer + model vocab_size
                                    compiles GrammarMatcher from the schema
                                    constructs an mlx logits_processor
                                    threads it into mlx_lm.stream_generate
  ← stream_event tokens             emits tokens as today
```

The serializable artifact that crosses the boundary is the **grammar
specification** (a JSON schema object, or a tagged variant — see §5), never the
matcher. The matcher is reconstructed child-side, fresh per generation request.

### 3.1 Concrete injection points (read 2026-05-28)

- [`mlx_lm_runner.py`](../../owlmlx/runtime/mlx_lm_runner.py) `_prepare_generation_params`
  (line ~124) already converts OpenAI-style sampling params into a `sampler`
  callable. Grammar construction belongs adjacent to this, but it additionally
  needs the `model`/`tokenizer`, which are only in scope at the action handler.
- The `stream_generate` action handler (line ~488) binds `model` and
  `tokenizer`, calls `generation_params = _prepare_generation_params(params)`,
  then `mlx_lm.stream_generate(model, tokenizer, prompt, **generation_params)`
  (line ~538). The grammar `logits_processor` must be appended to
  `generation_params["logits_processors"]` here, after the model/tokenizer are
  known.
- `MlxLmSubprocessBackend.stream_generate` (line ~2163) and
  `stream_generate_messages` (line ~2263) build the request payload sent to the
  child. They must forward a new optional `grammar` field unchanged.

### 3.2 Per-step processor contract (verified by probe)

The processor closure MUST:

1. On its first call, record `tokens.shape[0]` and accept nothing — the first
   call carries the prompt-tail token, not a generation (verified: mlx-lm runs
   the bulk of the prompt through `_model_call` outside the processor, then
   hands the final prompt token to `_step` once; `tokens` then accumulates that
   token plus each sampled token).
2. On later calls, accept the newly-arrived token(s) into the matcher.
3. Use the **model's** logits vocab_size (e.g. Qwen3.6 nests it at
   `text_config.vocab_size = 248320`), not the tokenizer-native size (248077),
   for the bitmask, or the bitmask will not broadcast against logits.
4. Set disallowed logits to `-inf` (probe used `mx.where(allowed, logits, -inf)`).

These four are encoded as the probe's working processor; F-4.2 lifts that logic
into the child runner. The off-by-prompt-tail and vocab-padding mistakes are
documented in the probe commit `d3d8273e` so code-grade does not repeat them.

## 4. Per-Family Grammar Strategy

**Critical design point.** The five F-4 families (F-4 spec §5) do NOT all want
the same grammar. A pure-JSON grammar would *break* the family that requires a
reasoning envelope.

| Family | Target shape | Grammar construction | Risk |
|---|---|---|---|
| `json_schema_flat` (§5.1) | bare JSON object | `compile_json_schema` | low — proven by probe |
| `nested_object` (§5.3) | nested JSON | `compile_json_schema` | low |
| `enum_constrained` (§5.4) | JSON w/ enums | `compile_json_schema` (enums map to grammar alternation) | low |
| `function_call_arguments` (§5.2) | tool-call arg object | `compile_json_schema`; consider xgrammar `openai_tool_call_schema` module | medium — verify the module shape matches the F-4 case |
| `thinking_tag_closed` (§5.5) | `<thinking>…</thinking>{json}` | xgrammar structural tag: `StructuralTagItem(begin="</thinking>", schema, end="")` triggered on `</thinking>` | resolved — see §4.1 |

F-4.2a MUST verify, with a 1-sample probe per family, that the chosen grammar
construction compiles and constrains correctly BEFORE the full matrix run.

### 4.1 Per-family construction verification (done 2026-05-29, model-free)

This verification was run ahead of code-grade as a model-free grammar
compile + `accept_string` check (no 35B load, no generation): for each family,
compile the grammar, then confirm a known-good exemplar is accepted and a
known-bad exemplar is rejected.

- Probe: [`../../scripts/probe/f4_grammar_per_family_verify.py`](../../scripts/probe/f4_grammar_per_family_verify.py)
- Evidence: `files/evidence/owlmlx/bench/structured-output-invariance/20260529T024253Z-f4-2-per-family-grammar-verify.json`

Result: `all_families_pass=true`.

| Family | Construction | good accepted | bad rejected |
|---|---|---|---|
| `json_schema_flat` | `compile_json_schema` | ✓ | ✓ |
| `function_call_arguments` | `compile_json_schema` | ✓ | ✓ |
| `nested_object` | `compile_json_schema` | ✓ | ✓ |
| `enum_constrained` | `compile_json_schema` | ✓ | ✓ |
| `thinking_tag_closed` | `compile_structural_tag([StructuralTagItem(begin="</thinking>")], ["</thinking>"])` | ✓ | ✓ |

So the §4 central risk is resolved: `thinking_tag_closed` IS expressible as a
structural tag, no post-envelope-fallback needed. Caveat for code-grade: the
2-arg `compile_structural_tag(tags, triggers)` form is documented as
deprecated in xgrammar 0.2.1 (the non-deprecated path is the `StructuralTag`
pydantic class, which in 0.2.1 exposes only `{type, format}`). F-4.2a should
prefer the `StructuralTag`-class form if the begin/end envelope can be
expressed there, and pin xgrammar in the `grammar-experimental` extras so the
legacy form does not vanish under an upgrade without notice. This verification
is model-free; it proves grammar *shape* correctness, not end-to-end generation
(that is F-4.2b's job, and is already proven for `json_schema_flat`).

## 5. Request / Response Contract

### 5.1 New optional request field

```jsonc
{
  "action": "stream_generate",
  "model_id": "...",
  "prompt": "...",
  "params": {
    "temperature": 0.3,
    "max_tokens": 128,
    // NEW (all optional; absent = today's behavior, byte-for-byte):
    "grammar": {
      "kind": "json_schema" | "structural_tag",
      "schema": { /* JSON schema object */ },
      "structural_tag": { /* xgrammar structural-tag spec, when kind=structural_tag */ }
    }
  }
}
```

### 5.2 Backward compatibility (hard requirement)

- A request with no `grammar` field MUST produce byte-identical behavior to the
  current runner. The grammar code path is entered only when `grammar` is
  present and non-null.
- This MUST be covered by a runner test asserting that the `generation_params`
  dict gains no `logits_processors` entry when `grammar` is absent.

### 5.3 Failure surfacing

When grammar construction fails (invalid schema, unsupported structural tag,
xgrammar import error), the child MUST emit a structured error
(`ok=False, error="grammar_compile_failed: <detail>"`) and MUST NOT fall back to
unconstrained generation silently — a silent fallback would let an invalid
grammar masquerade as a passing run.

## 6. Code Surfaces (design-level; code-grade implements)

Per [`project-owlmlx-agents-module-as-spec-rule`], grammar helpers live where a
runtime consumer needs them — the child runner — not in a new free-floating
`owlmlx/` module without a consumer.

| File | Change |
|---|---|
| `owlmlx/runtime/mlx_lm_runner.py` | child-side grammar matcher + logits_processor builder; wire into `stream_generate` / `generate` / `generate_messages` action handlers |
| `owlmlx/runtime/mlx_lm_subprocess_backend.py` | forward optional `grammar` field into the child request payload (stream + non-stream) |
| `pyproject.toml` | add `grammar-experimental` optional-dependencies group pinning `xgrammar` (resolves §12.1 unresolved problem #3) |
| `tests/test_mlx_lm_runner_grammar.py` (new) | unit-test grammar param handling: absent → no processor; present+valid → processor appended; present+invalid → structured error. Tokenizer/matcher construction can be tested without loading a 35B model by using a tiny local tokenizer fixture or by mocking. |
| `scripts/bench/structured_output_invariance.py` | add a `--grammar` switch so the F-4.2b matrix can run grammar-on and reuse the F-4.1 rollup schema for an apples-to-apples diff |

This spec does NOT prescribe the line-level diff; code-grade owns that.

## 7. Resolution of F-4 §12.1 Unresolved Problems

1. **Subprocess boundary** → resolved by §3: pass the serializable schema, build
   the matcher child-side.
2. **numpy hot-loop cost** → design decision: accept the numpy `unpackbits`
   bridge for F-4.2 (the probe measured 1.125× on 35B-A3B). F-4.2b MUST record
   per-model tokens/sec degradation in the matrix rollup. A native mlx mask op
   is explicitly deferred to a future round and only justified if a small model
   shows degradation > 2× (threshold recorded here, not enforced as a gate).
3. **pyproject extras** → resolved by §6: add `grammar-experimental` extras.
   xgrammar pulls torch transitively (~84MB); this is acceptable for an
   experimental extras group and MUST NOT be added to the default install.

## 8. Phase Breakdown

### 8.1 F-4.2a — Child-Side Grammar Plumbing (code-grade)

- Implement §6 surfaces.
- Add the `grammar-experimental` extras.
- Per-family 1-sample compile+constrain verification (§4) — written as a small
  bench/probe invocation, NOT committed as a matrix.
- Tests green: new runner grammar test + nearest existing subprocess backend
  tests.
- Commit; do not push unless requested.

#### 8.1.1 F-4.2a implementation status (landed 2026-05-29)

Implemented in `mlx_lm_runner.py`: `_build_grammar_logits_processor`
(child-side, lazy-compiles the matcher using `logits.shape[-1]` as the
authoritative vocab size), `_resolve_hf_tokenizer_for_xgrammar` (picks the
`PreTrainedTokenizerBase` xgrammar wants — uses a raw HF tokenizer directly,
unwraps mlx-lm's `TokenizerWrapper._tokenizer`), `_maybe_add_grammar_processor`
(wiring), and `_prepare_generation_params` now strips `grammar`. Wired into all
four generation action handlers (generate / generate_messages / stream_generate
/ stream_generate_messages).

**Backend needed no change.** The §6 table anticipated a backend edit, but
`MlxLmSubprocessBackend` already forwards every kwarg into the request `params`
(`"params": dict(kwargs)`), so a `grammar` kwarg reaches the child unchanged. A
regression test guards that contract.

Verification:
- `tests/test_mlx_lm_runner_grammar.py` — 7 tests (param strip, wiring, real
  xgrammar masking, backend forwarding). The masking test caught a real
  tokenizer-unwrap bug before it shipped (the fix is `_resolve_hf_tokenizer_for_xgrammar`).
- `scripts/probe/f4_2_backend_grammar_smoke.py` — end-to-end through the real
  subprocess IPC: control (no grammar) returns a `<think>`-prefixed string that
  fails JSON parse; treatment (grammar) returns valid JSON. Evidence
  `files/evidence/owlmlx/bench/structured-output-invariance/20260529T054051Z-f4-2-backend-grammar-smoke.json`.
- 108 passed across grammar + params + subprocess-backend + structured-output
  suites.

Not done in F-4.2a: the full family/model matrix (that is F-4.2b), and the
`StructuralTag`-class form preference (the legacy 2-arg structural-tag form is
in use; see §4.1 caveat).

### 8.2 F-4.2b — Grammar-On Stratified Matrix (bench-grade)

- Reuse the F-4.1 runner with `--grammar` on.
- Matrix: 5 families × 3 models (Qwen 27B, Qwen 35B-A3B, Gemma 31B) × 2
  temperatures; sample count per cell ≥ the F-4.1 cell count so the rollup is
  diffable against `20260528T030803Z-f4-smoke-matrix-rollup.jsonl`.
- Evidence: `files/evidence/owlmlx/bench/structured-output-invariance/<ts>-f4-2-grammar-matrix.{jsonl,rollup.jsonl}`.

**Pass thresholds** (revised from §4.3's prompt-only thresholds):

| Metric | Threshold |
|---|---|
| `generation_error_count` | `0` (grammar must not crash generation) |
| `json_parse_failed_rate` per family | record per family; the gate is a *substantial* drop vs the F-4.1 baseline, not necessarily 0 |
| `hard_break_rate` overall | record; promotion-candidate discussion requires a separate, larger N≥1000 run — NOT this matrix |
| tokens/sec degradation per model | recorded, not gated |

F-4.2b is a measurement-and-comparison gate, not a promotion gate. It answers
"does child-side grammar reproduce the probe's effect across families/models?"
Any family where grammar does NOT help (e.g. `thinking_tag_closed` if the
structural tag is unavailable) is reported as a per-family limitation, not a
campaign failure.

### 8.3 F-4.2c — Fresh Repeat (bench-grade, conditional)

Only if F-4.2b shows a clean per-family pass: rerun with a different seed,
same models/temperatures, to confirm stability before any source-of-truth
promotion review. Promotion review itself is a later, separate round.

## 9. Validator Contract Additions

The F-4 validator (`scripts/bench/structured_output_invariance.py`) gains
grammar-aware diagnostic codes (additive; existing codes unchanged):

- `grammar_unterminated_at_max_tokens` — matcher not terminated when generation
  hit `max_tokens` (the probe already emits this).
- `grammar_compile_failed` — schema/structural-tag did not compile (surfaced
  from the child error).
- `grammar_rejected_token` — matcher rejected a sampled token (should be near-zero
  if masking works; non-zero indicates a masking/vocab bug).

These are diagnostics, not new hard-break categories, unless code-grade finds a
reason to gate on them.

## 10. Capability Label

- F-4 stays `experimental` throughout F-4.2.
- F-4.2b passing does NOT auto-promote. It enables a *discussion* of
  `partial_candidate` for the families that pass, which is a separate
  source-of-truth round with its own evidence bar (N≥1000, fresh repeat).
- Banned public-claim vocabulary (`parity` / `equivalent` / `production_ready`
  / `beats` / `matches` per [`public-claim-matrix.md`](../../docs/source-of-truth/public-claim-matrix.md) §3)
  appears nowhere in F-4.2 evidence strings or labels.

## 11. Out of Scope / Future

- xgrammar `openai_tool_call_schema` integration beyond the single
  `function_call_arguments` family (full OpenAI tool-calling is a separate
  campaign).
- A native mlx logits-mask op to replace the numpy bridge (deferred per §7.2).
- Speculative decoding interaction with grammar (F-1/F-2 territory).
- Promotion of any model to `partial_candidate` or `supported`.
- Grammar for non-JSON structured formats (XML, YAML).

## 12. Honesty Caveats

- The probe covered ONE family on ONE model. This spec generalizes a *design*
  from that point, not a *result*. F-4.2b is precisely the step that tests
  whether the generalization holds; until it runs, "grammar fixes structured
  output across families" is `plausible`, not demonstrated
  (per `feedback-evidence-language-calibration`).
- This spec was written in the same session as the probe and F-4.1 closeout.
  A fresh session would carry less narrative bias; the compensating controls
  are the per-claim grounding in committed evidence and the explicit
  verification-step framing of unproven assertions.

## 13. References

- [`F-4-structured-output-invariance-spec.md`](F-4-structured-output-invariance-spec.md) §4.3 (superseded F-4.2 definition), §5 (families), §12.1 (probe outcome)
- [`../../scripts/probe/f4_grammar_feasibility.py`](../../scripts/probe/f4_grammar_feasibility.py) (probe; reference processor logic)
- [`../../files/evidence/owlmlx/bench/structured-output-invariance/20260528T063524Z-f4-grammar-feasibility-probe-summary.json`](../../files/evidence/owlmlx/bench/structured-output-invariance/20260528T063524Z-f4-grammar-feasibility-probe-summary.json)
- [`../../owlmlx/runtime/mlx_lm_runner.py`](../../owlmlx/runtime/mlx_lm_runner.py) `_prepare_generation_params`, `stream_generate` action
- [`../../owlmlx/runtime/mlx_lm_subprocess_backend.py`](../../owlmlx/runtime/mlx_lm_subprocess_backend.py) child IPC

## 14. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-28 | Initial F-4.2 design-grade spec. Pivots F-4.2 from the prompt-only stratified matrix (F-4 spec §4.3) to a grammar-constrained baseline, justified by the `probe-positive` verdict. Resolves the three §12.1 unresolved problems at design level (child-side matcher; accept numpy bridge + record degradation; add `grammar-experimental` extras). Flags the per-family grammar strategy as the central design risk (thinking_tag_closed needs a structural tag). Authored in the same session as the probe per user direction; honesty caveat recorded in the header and §12. | Post-probe session (with user direction) |
| 2026-05-29 | Added §4.1: model-free per-family grammar construction verification (`all_families_pass=true`). Resolves the §4 central risk — `thinking_tag_closed` is expressible via `compile_structural_tag([StructuralTagItem(begin="</thinking>")], ["</thinking>"])`; no post-envelope fallback needed. Downgraded the family-table risk column accordingly. Recorded the deprecated-2arg-form caveat for code-grade. Evidence `20260529T024253Z-f4-2-per-family-grammar-verify.json`. | Post-probe session (with user direction) |
| 2026-05-29 | F-4.2a code-grade landed (§8.1.1): child-side grammar builder + tokenizer resolver + wiring in `mlx_lm_runner.py`, `grammar-experimental` extras, TDD test (7 tests, caught a real tokenizer-unwrap bug), and an end-to-end backend-IPC smoke (control breaks, grammar yields valid JSON). Backend needed no change — kwargs already forward into params. Authored same-session per user direction. | Post-probe session (with user direction) |
