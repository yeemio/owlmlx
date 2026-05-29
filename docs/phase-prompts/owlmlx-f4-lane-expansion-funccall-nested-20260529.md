# Phase F-4 · Round: Grammar Lane Expansion (function_call + nested → N≥1000)

> **Grade**: bench-grade measurement + conditional doc-grade promotion (NO new
> production runtime code expected; the grammar path already exists).
> **Mission**: take `function_call_arguments` + `nested_object` — fixed at small
> N by the #3 bounds — to N≥1000 on the two Qwen models, and IF clean, fold them
> into the source-of-truth `partial` grammar lane. If not clean, document the
> residual honestly and promote nothing.
> **Trigger**: F-4 #3 (`810f2efd`) bounded both families to 0/16 across all three
> models; that is small-N only and explicitly NOT in the `partial` lane yet
> (source-of-truth doc §4, F-4.2 spec §8.6).
> **Status**: prepared 2026-05-29 after the F-4 grammar arc (`d3d8273e` →
> `991cb391`). Pick up in a **fresh session** per
> [[feedback-fresh-session-grade-transitions]] — the entire prior arc ran in one
> session, so a fresh executor is the honesty control this round needs.
> **Language discipline**: a clean N≥1000 result licenses ONLY a lane-scoped
> `partial` expansion, never F-4-wide `partial`, never `supported`. Any non-zero
> hard break or generation error fails the expansion and forbids the wording.

---

## 1. Identity and mission

You are the F-4 grammar **lane-expansion** executor. The structured-output
grammar lane is already source-of-truth `partial` for a narrow set; your job is
to test whether two more families earn the same label at scale, and to either
expand the lane (clean) or document why not (dirty). One dominant deliverable:
a defensible N≥1000 verdict for `function_call_arguments` + `nested_object`.

## 2. First principles

- **Pre-register the gate before running.** This doc fixes the gate (§7). Do not
  move it after seeing numbers.
- **Small-N clean ≠ reliable.** #3 proved the *fix mechanism* works (0/16); only
  an N≥1000 run earns a `partial` label, exactly as F-4.3 did for json+enum.
- **Promotion is a human verdict, never automatic.** The bench rollup
  `structured_output_invariance_promotion_candidate` is hardcoded `False`; the
  label lives in a source-of-truth doc you edit only on a clean pass.
- **Honest negatives are valid deliverables.** If a break appears at N≥1000, the
  round still succeeds — as a measurement that keeps these families out of the
  lane.

## 3. Current real state (verified, 2026-05-29)

| Fact | State | Anchor |
|---|---|---|
| Grammar lane label | source-of-truth `partial` | `docs/source-of-truth/structured-output-grammar-lane.md` |
| Lane scope (current) | {json_schema_flat, enum_constrained} × {qwen3.6-27b-4bit, qwen3.6-35b-a3b-4bit} × grammar | lane doc §2 |
| Lane evidence | 2× N=1024 @ 0 breaks | `…20260529T070431Z-f4-3-grammar-lane*`, `…20260529T105156Z-f4-3-grammar-lane-freshrepeat*` |
| function_call + nested | bounded (maxLength=120 + max_whitespace_cnt=4), **0/16 small-N on all 3 models** | F-4.2 spec §8.6, `…20260529T104334Z-f4-3-gemma-bounded-*` |
| function_call + nested at N≥1000 | **NOT run** ← this round | — |
| thinking_tag_closed | residual (reasoning models don't close `<think>` in budget); out of scope | F-4.2 spec §8.5 |
| OpenAI surface | `response_format` json_schema → grammar wired + verified | `server_routes_openai.py`, `test_server_routes_openai.py` |
| Bench CLI | has `--grammar`, `--families`, `--models`, `--temperatures`, `--samples-per-family`, `--max-tokens`, `--run-id` | `scripts/bench/structured_output_invariance.py` |
| `F4_FAMILY_GRAMMARS` | json_schema_flat, function_call_arguments, nested_object, enum_constrained (thinking_tag absent by design) | same file |
| All 3 models cached | qwen 27B / qwen 35B-A3B / gemma-4-31b-it-4bit all present | `/Users/yeemio/AI/Agent/models/` |
| Tests green | bench + grammar-runner + openai-route suites pass | `pytest` |

## 4. Key gaps this round closes

1. The `partial` lane covers only 2 of the 4 grammar families. function_call +
   nested are clean at small N but unproven at scale.
2. Whether gemma can ever join the lane is unknown (it was excluded from the
   original lane; #3 fixed its degeneracy small-N only). This round may answer
   it as a secondary wave, or defer it — your call per §8.

## 5. Must-read files (load these, in order)

1. `docs/source-of-truth/structured-output-grammar-lane.md` — the label you may edit.
2. `docs/architect/design/F-4-2-grammar-constrained-baseline-spec.md` §8.4 (F-4.3 lane), §8.6 (gemma fix), §8.7 (promotion review) — the pattern to mirror.
3. `scripts/bench/structured_output_invariance.py` — `F4_FAMILY_GRAMMARS`, `f4_family_grammar`, `run_smoke_matrix`, `_run_generation_cell`, `rollup_records`. Read, do not rewrite.
4. `files/evidence/owlmlx/bench/structured-output-invariance/20260529T070431Z-f4-3-narrow-lane-verdict.json` — the verdict shape to reproduce.
5. `files/evidence/owlmlx/bench/structured-output-invariance/20260529T104334Z-f4-3-gemma-bounded-verdict.json` — the small-N result you are scaling up.

## 6. Hard rules

- [ ] Pre-registered gate (§7) is fixed; do not relax it after seeing numbers.
- [ ] A `partial` lane expansion requires `hard_break_count==0` AND
      `generation_error_count==0` at `sample_count>=1000`. Anything else →
      no promotion, document and stop.
- [ ] Edit the lane label ONLY in `structured-output-grammar-lane.md`. Do NOT
      touch any `owlmlx/model_release_candidate_record.py` entry (that governs
      model labels, not this feature lane).
- [ ] F-4 overall stays `experimental`. The word `supported` is claimed nowhere
      (the `enum_constrained` fixture's `"supported"` enum value is not in this
      round's families anyway).
- [ ] Banned vocabulary (`parity` / `equivalent` / `production_ready` /
      `production-grade` / `beats` / `matches` per
      `docs/source-of-truth/public-claim-matrix.md` §3) appears in no new string.
- [ ] No production runtime code change is expected. If you find yourself editing
      `owlmlx/runtime/*.py`, stop and reconsider — the grammar path already works.
- [ ] Staging discipline: these 7 pre-existing dirty/untracked tree files stay
      OUT of every commit — `reference-runtime-comparison-matrix.md`,
      `owlmlx/speculative/suffix_decoding/{__init__.py,runtime.py}`,
      `docs/architect/04-architecture-canvas.html`,
      `competitor-capability-matrix-20260527.md`,
      `ds4-mtp-local-llm-stack-research.zh-20260514.md`, `owl-lora-pipeline/`,
      `软件著作权申请资料/`.
- [ ] thinking_tag_closed is NOT in this round.

## 7. Pre-registered gate

| Metric | Threshold |
|---|---|
| `sample_count` (per family, summed over models+temps) | ≥ 1000 |
| `hard_break_count` | **0** |
| `generation_error_count` | **0** |

Lane-expansion claim ceiling on pass: "the grammar lane `partial` now also
covers `function_call_arguments` + `nested_object` on qwen3.6-27b-4bit +
qwen3.6-35b-a3b-4bit." Nothing wider.

## 8. Wave plan (~2–3h, branch at Wave 4)

### Wave 1 — Pre-flight (≈15 min)
- Confirm `f4_family_grammar("function_call_arguments")` and `"nested_object")`
  carry `maxLength` on free-text strings and `max_whitespace_cnt<=4` (the #3
  bounds). Confirm `thinking_tag_closed` returns `None`.
- Run the existing suites green: `pytest tests/test_structured_output_invariance.py tests/test_mlx_lm_runner_grammar.py -q`.
- Confirm the 3 model paths resolve.
- **Acceptance**: bounds present, tests green, models resolve.

### Wave 2 — Primary N≥1000 run (≈60–90 min)
- Run, with an explicit `--run-id "<UTC>-f4-4-lane-expansion"`:
  ```
  --phase smoke --grammar \
    --families function_call_arguments nested_object \
    --models qwen3.6-27b-4bit qwen3.6-35b-a3b-4bit \
    --temperatures 0.0 0.3 --samples-per-family 128 --max-tokens 256
  ```
  (2 families × 2 models × 2 temps × 128 = 1024 rows; max_tokens 256 is the same
  value as the #3 run that produced 0/96.)
- **Acceptance**: run completes, evidence jsonl + rollup written.

### Wave 3 — Per-cell analysis (≈15 min)
- Break down by (family, model, temp). Confirm whether ALL 8 cells are clean, not
  just the aggregate. Inspect any break's `output_text` + `failure_codes` +
  `finish_reason`.
- **Acceptance**: a per-cell table + a clear pass/fail call against §7.

### Wave 4 — BRANCH on the Wave 3 result
- **4-PASS (0 breaks, 0 gen-err, N≥1000):** write a lane-expansion verdict
  evidence (mirror `…-narrow-lane-verdict.json`), then edit
  `structured-output-grammar-lane.md` §2 to add the two families (Qwen models
  only) and §3 to cite the new evidence; move them out of §4 exclusions. Update
  F-4.2 spec with an §8.8 results note + change-log row.
- **4-FAIL (any break / gen-err):** write the verdict as `lane-fail`, record the
  dominant failure taxonomy, do NOT edit the lane label, and add a spec note
  explaining what blocks these families at scale. The round still succeeds.

### Wave 5 — (Secondary, optional) gemma-at-scale probe (≈45 min)
- Only if Wave 4 passed and time remains. Run the SAME matrix with
  `--models gemma-4-31b-it-4bit` for all four grammar families
  (json_schema_flat, enum_constrained, function_call_arguments, nested_object)
  at N≥1000. This decides whether gemma can ever join the lane.
- **Branch**: clean → note gemma as a candidate (do NOT auto-admit; admitting a
  third model is its own review). dirty → record gemma stays excluded with the
  failure taxonomy.
- If out of time, explicitly `log` that this was skipped — no silent omission.

### Wave 6 — Evidence, commit, push (≈15 min)
- Stage ONLY round-scope files. One commit. Push only if the user has said so in
  this round; otherwise leave it local and report the ahead count.

## 9. Required tests / checks

- `pytest tests/test_structured_output_invariance.py tests/test_mlx_lm_runner_grammar.py -q` green before and after.
- `git diff --check` clean.
- Banned-vocab grep on the diff returns empty.
- `grep -rn "supported" <new evidence/docs>` shows only disclaimers, never a model/feature `supported` claim.

## 10. Verification assets to produce

- `files/evidence/owlmlx/bench/structured-output-invariance/<ts>-f4-4-lane-expansion.{jsonl,rollup.jsonl}`
- `…<ts>-f4-4-lane-expansion-verdict.json` (gate, per-cell, verdict, claim ceiling, exclusions)
- (Wave 5, if run) `…<ts>-f4-4-gemma-allfamilies.{jsonl,rollup.jsonl}` + verdict

## 11. Out of scope

- thinking_tag_closed (residual; needs reasoning-aware redesign, not this round).
- Any model_release_candidate_record / model-level label change.
- New production runtime code.
- The OpenAI surface (already done in #1).
- Admitting a 3rd model (gemma) to the lane — Wave 5 only *measures*; admission is a later review.

## 12. Final report format (required)

- Modified files
- Wave-by-wave outcomes
- New user-visible capability (if any): exact lane scope after this round
- Tests run + results
- `git diff --check` + banned-vocab + supported-claim scan results
- Capability-honesty delta: what label changed, scoped how, what stayed out
- Remaining blockers / next candidates
- Why this round materially advanced delivery

## 13. Suggested commit message

- PASS: `bench: expand grammar partial lane to function_call + nested (N=1024, 0 breaks)`
- FAIL: `bench: f4 lane-expansion measurement — function_call/nested not clean at N≥1000`

## 14. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-29 | Initial lane-expansion round prompt. Routes the N≥1000 test of function_call_arguments + nested_object (bounded by #3) to a fresh session, with a pre-registered gate, a pass→promote / fail→document branch, and an optional gemma-at-scale secondary wave. Authored after the F-4 grammar arc (`d3d8273e`→`991cb391`) to finally return grade transitions to a fresh session. | F-4 arc session (with user direction) |
