# Structured-Output Grammar Lane Status

> Status: authoritative
> Created: 2026-05-29 (F-4 grammar-constrained structured output)
> Scope: the honest capability status of grammar-constrained structured-output
> decoding in owlmlx. Complements the design spec
> `docs/architect/design/F-4-2-grammar-constrained-baseline-spec.md`.

## 1. Capability label

**`partial`** — for a deliberately narrow lane, defined precisely in §2. This is
a *feature-lane* label, not a model capability label; it does not change any
model's `model_release_candidate_record` entry. F-4 structured output **overall
remains `experimental`** (§4).

This label was promoted from `partial_candidate` after both prerequisites of the
F-4 §8.4 / #1 promotion review passed (§3).

The lane **scope was expanded 2026-05-30** (F-4.4) to add
`function_call_arguments` + `nested_object` on the two Qwen models; the label
itself is unchanged (still `partial`, still feature-lane-scoped).

## 2. What `partial` covers (and only this)

| Dimension | In the lane |
|---|---|
| Families | `json_schema_flat`, `enum_constrained`, `function_call_arguments`, `nested_object` |
| Models | `qwen3.6-27b-4bit`, `qwen3.6-35b-a3b-4bit` |
| Mechanism | child-side xgrammar JSON-schema constraint (see F-4.2a) |
| Grammar bounds | `function_call_arguments` + `nested_object` additionally carry `maxLength=120` on free-text strings and `max_whitespace_cnt=4` (the F-4.2 §8.6 bounds); `json_schema_flat` / `enum_constrained` are unbounded |
| Temperatures | 0.0 and 0.3 |
| Surface | direct backend `stream_generate`/`generate` **and** the OpenAI
  `/v1/chat/completions` route via `response_format` json_schema |

Within this lane, grammar-constrained decoding produces parseable,
schema-conformant JSON reliably (§3 evidence).

## 3. Evidence

- **F-4.3 lane (N=1024):** `files/evidence/owlmlx/bench/structured-output-invariance/20260529T070431Z-f4-3-grammar-lane.{jsonl,rollup.jsonl}` + `-narrow-lane-verdict.json` — `hard_break_count=0`, `generation_error_count=0`, all 8 cells uniformly clean.
- **Fresh repeat (N=1024):** `…20260529T105156Z-f4-3-grammar-lane-freshrepeat.jsonl` — 0 hard breaks again (temp=0.3 cells re-sampled), confirming stochastic stability.
- **F-4.4 lane expansion (N=1024):** `…20260530T064353Z-f4-4-lane-expansion.{jsonl,rollup.jsonl}` + `-verdict.json` — `function_call_arguments` + `nested_object` on both Qwen models, all 8 cells 128/0, `hard_break_count=0`, `generation_error_count=0` (spec §8.8).
- **OpenAI surface:** `tests/test_server_routes_openai.py` (plumbing: `response_format` → `params['grammar']` → kernel → backend) + `scripts/probe/f4_openai_surface_grammar_smoke.py` (real Qwen 27B through `/v1/chat/completions` → valid schema-conformant JSON).
- **Promotion-review verdict:** `…20260529T105156Z-f4-1-promotion-review-verdict.json` (both prerequisites pass).
- **Baseline contrast:** prompt-only on the same matrix broke 59/60 (F-4.1 `20260528T030803Z-f4-smoke-matrix`); grammar took the full matrix to 20/60 and this lane to 0.

## 4. What `partial` does NOT cover

- **F-4 overall** — stays `experimental`. This label is lane-scoped only.
- **`supported`** — not claimed for any model or for F-4 structured output. The
  word is not used as a capability claim here (the `enum_constrained` schema
  contains `"supported"` only as a fixture enum *value*).
- **`thinking_tag_closed`** — residual. Reasoning models do not reliably close
  their native `<think>` channel within the token budget; grammar backfires on
  it (F-4.2 spec §8.5). Out of the lane.
- **`gemma-4-31b-it-4bit`** — excluded from the `partial` lane on **every**
  family (including `function_call_arguments` / `nested_object`). Its degeneracy
  is only small-N fixed (0/16, F-4.2 spec §8.6), **not** validated at N≥1000.
- Any model, family, temperature, or surface not listed in §2.

## 5. Banned-vocabulary compliance

No `parity` / `production-ready` / `production-grade` / `equivalent` / `beats` /
`matches` claim appears in this lane's status or evidence (per
`public-claim-matrix.md` §3). The lane claim is the measured fact: zero hard
breaks at N=1024 for the §2 scope (json_schema_flat/enum_constrained: 2 runs;
function_call_arguments/nested_object: 1 run, F-4.4).

## 6. Expansion path (not yet done)

- ~~N≥1000 run for `function_call_arguments` + `nested_object`~~ — **done
  2026-05-30** (F-4.4, N=1024, 0 breaks); folded into §2 for the two Qwen models.
  gemma at N≥1000 on these families is still open (optional follow-up probe).
- A reasoning-aware redesign of `thinking_tag_closed` (trigger on the model's
  actual reasoning close, larger/var token budget) before it can rejoin.
- Additional models beyond the two Qwen variants.

## 7. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-29 | Lane promoted `partial_candidate` → `partial` after the §8.4/#1 review: fresh-seed repeat (N=1024 ×2, 0 breaks) + OpenAI-surface coverage both passed. Feature-lane label; F-4 overall stays experimental. | Post-probe session (with user direction) |
| 2026-05-30 | Lane **scope expanded** (F-4.4): `function_call_arguments` + `nested_object` added on qwen3.6-27b-4bit + qwen3.6-35b-a3b-4bit after an N=1024 run (8 cells 128/0, `hard_break_count=0`, `generation_error_count=0`; bounded grammar maxLength=120 + max_whitespace_cnt=4). gemma stays excluded (small-N only). Label unchanged (`partial`, feature-lane). Run in a session separate from the F-4 arc, fully detached (os.setsid) to survive session idle. | Fresh-session executor (with user direction) |
