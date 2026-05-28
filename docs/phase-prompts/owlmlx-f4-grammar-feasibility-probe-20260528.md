# Handoff · F-4 Sub-Round · Grammar Constrained Decoding Feasibility Probe

> **Grade**: feasibility-probe-grade (decision input for F-4.2; NOT a full design-grade round, NOT a code-grade promotion round)
> **Mission**: minimal probe to decide whether F-4.2 takes a grammar-constrained baseline path, falls back to prompt-strictness + JSON repair, or parks F-4 as a known limitation
> **Trigger**: F-4.1 smoke matrix landed 2026-05-28 (`deb2940f`) with 59/60 hard breaks; F-4 spec §12 next-step item #2 requires evidence-backed decision before F-4.2 starts
> **Plan-grade source**: [`../architect/design/F-4-structured-output-invariance-spec.md`](../architect/design/F-4-structured-output-invariance-spec.md) §12 next-step #2
> **Status of this handoff**: prepared 2026-05-28 immediately after F-4.1 spec update; should be picked up by a **fresh session** per [[feedback-fresh-session-grade-transitions]]
> **Language discipline**: probe writes one short evidence file + appends one decision subsection to F-4 spec; does NOT pre-commit F-4.2 direction; does NOT make any capability promotion claim; verdict labels use "probe-positive / probe-negative-with-fallback / probe-negative-stop" — NOT `supported` / `production_ready` / `partial_candidate`

---

## 0. 给新 session 的开场指令

**You are the post-F-4.1 grammar feasibility probe session.** F-4.0 and F-4.1 are both implemented and committed locally (NOT pushed):

| Stage | Verdict | Commit | Anchor |
|---|---|---|---|
| F-4.0 (validator fixtures) | passed 2026-05-28 (validator_contract=true, measurement_harness=false expected) | `24d94e7f bench: add f4 structured-output validator fixtures` | `files/evidence/owlmlx/bench/structured-output-invariance/20260528T025514Z-f4-validator-fixtures.jsonl` |
| F-4.1 (smoke matrix) | measurement-harness pass 2026-05-28 (NOT a reliability pass; 59/60 hard breaks) | `deb2940f bench: run f4 structured-output smoke matrix` | `files/evidence/owlmlx/bench/structured-output-invariance/20260528T030803Z-f4-smoke-matrix-rollup.jsonl` |

F-4.1 evidence summary (already written into F-4 spec §12):

- `sample_count=60`, `generation_error_count=0`, `hard_break_count=59`
- By model: Qwen27B 20/20 break; Qwen35B-A3B 19/20; Gemma31B 20/20
- By family: `json_schema_flat` 12/12; `function_call_arguments` 11/12 (one pass); `nested_object` 12/12; `enum_constrained` 12/12; `thinking_tag_closed` 12/12
- Dominant failures: `json_parse_failed=47`, `extra_prose_outside_envelope=8`, `thinking_tag_unclosed=4`
- Only pass: Qwen35B-A3B + `function_call_arguments` + temp=0.3

Your **only** deliverables this session:

1. **API-surface probe** (Step 1): determine whether mlx-lm 0.22.0+ (or the Blaizzy fork pin used in `deepseek-experimental` extras) exposes a logit-processor / sampler hook usable for grammar constraint.
2. **Library mount attempt** (Step 2): try the most-likely-compatible of {xgrammar, outlines, lm-format-enforcer} against that hook; record what worked / didn't.
3. **Control-vs-treatment mini run** (Step 3, only if Step 1 + 2 succeed): 10 samples each on one model + one family, prompt-only vs grammar-constrained.
4. **One evidence file** written into the F-4 evidence directory.
5. **One subsection appended** to F-4 spec §12 (or a new §13) recording the verdict and the recommended F-4.2 direction.
6. **One commit, no push.** (F-4.0 + F-4.1 + this probe commit will all push together after the design-grade follow-up round picks up.)

You will NOT:

- Write F-4.2 design-grade spec.
- Run F-4.2 stratified matrix.
- Add or modify any file under `owlmlx/` (per [[project-owlmlx-agents-module-as-spec-rule]] + F-4 spec §10).
- Add or modify any file under `tests/`.
- Modify F-4.0 / F-4.1 evidence files (frozen).
- Modify F-4 spec sections §1-§11 (frozen; only §12 append or §13 add).
- Modify `pyproject.toml` to add a grammar library as a dependency (probe is allowed to `pip install` locally for the probe run; commit-time dep addition is F-4.2 design-grade scope, not probe scope).
- Promote any capability label.
- Push to remote.
- Sweep unrelated dirty tree files (reference-runtime-comparison-matrix.md, suffix_decoding, canvas, competitor-capability-matrix, ds4-mtp-research, owl-lora-pipeline, 软件著作权目录) — they stay out of this commit.

---

## 1. Mission · Feasibility Probe

### 1.1 Scope

- **Model**: Qwen35B-A3B (the only F-4.1 model with any non-break sample; signal is strongest there).
- **Family**: `json_schema_flat` (highest uniform failure rate at 12/12; simplest grammar to encode; clearest signal of any treatment effect). A fresh-session reader may justify picking `function_call_arguments` instead if they want to test the one family that already had a 1/12 pass — but document the rationale in the evidence file's `notes` field.
- **Sample size**: 10 control + 10 treatment (probe, not gate).
- **Temperatures**: pick one (e.g. temp=0.3, since that is where the F-4.1 single-pass occurred). Do not mix temperatures in the probe.

### 1.2 Three-step probe

**Step 1 — API surface check (no library install yet)**

- Read mlx-lm 0.22.0+ source (`mlx_lm/sample_utils.py`, `mlx_lm/generate.py`, or equivalent) and confirm whether a `logits_processor` / `sampler` kwarg is exposed on the generation entry point.
- Read the Blaizzy fork pin `5c10538136b9038b9626c134612b08afc18d697a` (used by `deepseek-experimental` extras) — has it diverged from mainline on the sampler interface? If yes, document.
- Write findings into the probe evidence file under `api_surface`.

**Step 2 — Library mount attempt (one library at a time)**

Try in this preferred order (mount the first one that succeeds; do not try all three if one works):

1. **xgrammar** (https://github.com/mlc-ai/xgrammar): check for mlx backend support or generic logit-processor wrapper.
2. **outlines** (https://github.com/dottxt-ai/outlines): check for mlx backend (recent versions added one) or generic adapter path.
3. **lm-format-enforcer** (https://github.com/noamgat/lm-format-enforcer): check for mlx adapter.

For the mounted library: write a ≤80-line probe script under `scripts/probe/f4_grammar_feasibility.py` (or similar path under `scripts/probe/`). Script may `pip install` the library locally but does NOT add it to `pyproject.toml`. Script exit code 0 = mount succeeded; non-zero = mount failed.

If all three libraries fail Step 2: verdict is `probe-negative-stop` (no library mounts; grammar path infeasible on current mlx-lm stack); skip Step 3.

**Step 3 — Control-vs-treatment run (only if Step 2 succeeded)**

- Reuse the existing F-4.1 runner where possible; if the runner needs a `--backend grammar` flag to thread the logit processor through, add it minimally in the runner script (NOT in `owlmlx/`).
- 10 control samples: prompt-only on Qwen35B-A3B / `json_schema_flat` / chosen temperature.
- 10 treatment samples: grammar-constrained, same model / family / temperature.
- Measure for each sample: `json_parse_failed` (boolean), token count, wall-clock duration, `generation_error` (boolean).
- Roll up: control hard-break rate vs treatment hard-break rate; control tokens/sec vs treatment tokens/sec.

### 1.3 Three verdict outcomes

| Verdict | Trigger | Implication for F-4.2 |
|---|---|---|
| **probe-positive** | Step 3 ran AND treatment hard-break-rate ≤ 20% (i.e. ≤ 2/10) AND tokens/sec degradation ≤ 5× | F-4.2 design-grade spec walks the grammar-constrained baseline path |
| **probe-negative-with-fallback** | Step 2 succeeded but Step 3 treatment hard-break-rate > 20% OR tokens/sec degradation > 5×; OR Step 2 mounted only with infeasible-for-production cost | F-4.2 design-grade spec walks the prompt-strictness + JSON-repair fallback path; grammar parked as future work |
| **probe-negative-stop** | All three libraries failed Step 2 | F-4 parks; F-4 spec §1 amended with known-limitation note "no reliable structured-output on current mlx-lm stack at this revision" |

Thresholds (20% / 5×) are heuristics, not gates — the probe writeup may argue a different verdict with justification recorded in the evidence file's `verdict_rationale` field.

---

## 2. Probe Outputs

### 2.1 Evidence file

```
files/evidence/owlmlx/bench/structured-output-invariance/
  <ts>-f4-grammar-feasibility-probe.jsonl
  <ts>-f4-grammar-feasibility-probe-summary.json
```

Required summary fields (JSON):

```json
{
  "phase": "f4-grammar-feasibility-probe",
  "verdict": "probe-positive | probe-negative-with-fallback | probe-negative-stop",
  "mlx_lm_version": "<actual installed version>",
  "mlx_lm_fork": "blaizzy-pin-5c10538 | mainline",
  "api_surface": {
    "logits_processor_exposed": true,
    "sampler_hook_exposed": false,
    "notes": "<free text>"
  },
  "library_attempted": "xgrammar | outlines | lm-format-enforcer | none",
  "library_mount_succeeded": true,
  "step3_ran": true,
  "control": { "hard_break_count": 8, "tokens_per_sec_median": 12.3 },
  "treatment": { "hard_break_count": 1, "tokens_per_sec_median": 9.8 },
  "verdict_rationale": "<2-4 sentences>"
}
```

JSONL rows (one per sample, if Step 3 ran) follow the F-4.1 sample schema where possible; use the existing runner's schema so the rollup can be diffed against the F-4.1 baseline.

### 2.2 F-4 spec append

Append a subsection (suggested title: **§12.1 Grammar Feasibility Probe Outcome**, or new top-level **§13 Grammar Feasibility Probe**) to `docs/architect/design/F-4-structured-output-invariance-spec.md`. Target length: 20-40 lines. Required content:

- Verdict label (one of the three §1.3 labels).
- Evidence pointer (path to the two probe files).
- Recommended F-4.2 direction (1-2 sentences, framed as "by this evidence, F-4.2 should …", NOT "F-4.2 will …").
- If `probe-negative-stop`: also amend §1 (Purpose) with a known-limitation note and link to this probe section.

Do NOT rewrite §1-§11 invariants. Do NOT touch F-4.0 / F-4.1 evidence rows.

---

## 3. Acceptance

The fresh session closes when:

1. Probe script exists under `scripts/probe/f4_grammar_feasibility.py` (or equivalent).
2. Step 1 (API surface check) ran and findings written into the evidence summary.
3. Step 2 (library mount) attempted and result recorded.
4. Step 3 (control-vs-treatment) ran if-and-only-if Step 2 succeeded; results in evidence file.
5. Evidence file pair written into the path in §2.1.
6. F-4 spec append landed per §2.2.
7. No `owlmlx/` package source change.
8. No `tests/` change.
9. No `pyproject.toml` change.
10. One commit. Suggested commit message: `bench: run f4 grammar feasibility probe`.
11. **NO push.** F-4.0 (`24d94e7f`) + F-4.1 (`deb2940f`) + this probe commit will all push together after the next design-grade round picks up the verdict.

### 3.1 Hard Rules (every one of these is a probe-session review checkbox)

- [ ] No file under `owlmlx/` created or modified.
- [ ] No file under `tests/` created or modified.
- [ ] No file under `docs/architect/design/` modified except F-4 spec §12.1 / §13 append.
- [ ] No file under `docs/phase-prompts/` modified except possibly amending this handoff's Change Log on completion (optional).
- [ ] `pyproject.toml` unchanged.
- [ ] F-4.0 and F-4.1 evidence files byte-identical to pre-probe state.
- [ ] F-4 spec §1-§11 byte-identical to pre-probe state.
- [ ] DSV4 / Campaign D state in any other doc: untouched.
- [ ] Banned vocabulary (`parity` / `replacement` / `equivalent` / `production_ready` / `production-ready` / `beats` / `wins` / `matches` per [`public-claim-matrix.md`](../source-of-truth/public-claim-matrix.md) §3 + [`owlmlx/model_release_candidate_schema.py`](../../owlmlx/model_release_candidate_schema.py) `BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY`) appears nowhere in the new strings.
- [ ] Verdict labels used are the three in §1.3, NOT `supported` / `partial_candidate` / `promotion_candidate`.
- [ ] Other dirty/untracked tree files (suffix_decoding C2 残留, canvas, competitor-capability-matrix-20260527, ds4-mtp-research, owl-lora-pipeline, 软件著作权申请资料) stay OUT of the commit.
- [ ] `git push` NOT run.

### 3.2 Acceptance verification commands

```bash
# 1. Confirm changed files match scope:
git status --short
git diff --cached --stat HEAD

# 2. owlmlx/ untouched:
git diff HEAD -- owlmlx/ | wc -l   # expect 0

# 3. tests/ untouched:
git diff HEAD -- tests/ | wc -l    # expect 0

# 4. pyproject.toml untouched:
git diff HEAD -- pyproject.toml | wc -l   # expect 0

# 5. F-4 spec only-append check (only insertions, no deletions in §1-§11 region):
git diff HEAD -- docs/architect/design/F-4-structured-output-invariance-spec.md | grep -E "^-[^-]" | head   # expect empty (no removals)

# 6. Evidence file pair exists:
ls -la files/evidence/owlmlx/bench/structured-output-invariance/*grammar-feasibility-probe*

# 7. Banned vocabulary scan on probe diff:
git diff HEAD -- docs/ scripts/ files/evidence/ | grep -E "^\+" | grep -iE "parity with|matches oMLX|matches vMLX|beats|equivalent to oMLX|equivalent to vMLX|replaces|production[ _-]ready"

# 8. Local ahead count is now 3, not 2, and origin still at 87d6721b:
git log --oneline origin/main..HEAD
```

Commands 2 / 3 / 4 / 5 / 7 must return empty / 0. Command 6 must show the file pair. Command 8 must show exactly 3 commits.

---

## 4. Next Round After This Probe

After probe commit landed (still NOT pushed):

1. **probe-positive** → new fresh session writes F-4.2 design-grade spec on the grammar-constrained baseline path. That spec may then add the chosen library to `pyproject.toml` `[project.optional-dependencies]` as e.g. `grammar-experimental` extras. Code-grade F-4.2 follows in another fresh session. Push happens after F-4.2 closes (or sooner if user requests).

2. **probe-negative-with-fallback** → new fresh session writes F-4.2 design-grade spec on the prompt-strictness + JSON-repair fallback path. Grammar is recorded as future work in F-4 spec §12.x / §13. Push happens after F-4.2 design-grade lands.

3. **probe-negative-stop** → F-4 parks. F-4 spec §1 carries the known-limitation note. Push happens immediately (no point holding the F-4.0/4.1/probe commits if F-4 is parked). The next-dominant-gap discovery session (parked from Campaign D closeout) takes over the main thread.

Do NOT pre-stage any of these design-grade artifacts in this probe session.

---

## 5. Reading List (self-contained for the probe session)

### 5.1 Authoritative state to read in full

- [`docs/architect/design/F-4-structured-output-invariance-spec.md`](../architect/design/F-4-structured-output-invariance-spec.md) — entire file; §10 + §12 are the most relevant
- [`files/evidence/owlmlx/bench/structured-output-invariance/20260528T030803Z-f4-smoke-matrix-rollup.jsonl`](../../files/evidence/owlmlx/bench/structured-output-invariance/20260528T030803Z-f4-smoke-matrix-rollup.jsonl) — F-4.1 rollup; informs which family / model is the strongest probe target

### 5.2 Section-only reads

- [`pyproject.toml`](../../pyproject.toml) — the `mlx-lm` baseline line and the `[project.optional-dependencies] deepseek-experimental` block (do NOT modify)
- F-4.1 runner script (find via `git log --oneline --all -- 'bench/**/*structured*'` or via the F-4.1 commit `deb2940f`) — the probe's Step 3 reuses this runner

### 5.3 Code/data references (read-only)

- mlx-lm upstream: https://github.com/ml-explore/mlx-lm — `sample_utils.py`, `generate.py` for sampler/logit-processor surface
- Blaizzy fork at pinned commit `5c10538136b9038b9626c134612b08afc18d697a` — compare sampler interface against mainline

### 5.4 Library candidate links (Step 2 reading)

- xgrammar: https://github.com/mlc-ai/xgrammar
- outlines: https://github.com/dottxt-ai/outlines
- lm-format-enforcer: https://github.com/noamgat/lm-format-enforcer

### 5.5 Memory anchors

- [[feedback-fresh-session-grade-transitions]] — why this is a fresh session
- [[feedback-staging-discipline]] — only stage probe-scope files; leave unrelated dirty tree files alone
- [[feedback-plan-grade-feasibility-probe]] — this handoff is a direct instance of that rule
- [[project-owlmlx-agents-module-as-spec-rule]] — probe code lives under `scripts/`, not `owlmlx/`
- [[feedback-evidence-language-calibration]] — verdict uses "compatible" / "viable" / "infeasible", NOT `supported`

---

## 6. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-28 | Initial F-4 grammar feasibility probe handoff. Trigger: F-4.1 smoke matrix landed locally (`deb2940f`) with 59/60 hard breaks; F-4 spec §12 next-step item #2 requires evidence-backed F-4.2 direction. Scope: minimal probe (1 model / 1 family / ~10 samples per arm) producing one of three verdicts that determines F-4.2's design-grade path. Routed to a fresh session per [[feedback-fresh-session-grade-transitions]]. Push deferred per user direction — F-4.0 + F-4.1 + probe commits will push together after the design-grade follow-up picks up. | Post-F-4.1 closeout session (with user direction) |
