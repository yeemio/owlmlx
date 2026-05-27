# Handoff · Campaign D Closeout · Sweep + Upstream Watch

> **Grade**: doc-grade (file edits + one new short source-of-truth doc; NO code, NO new spec rounds, NO new design-grade work)
> **Mission**: apply plan-grade §13 stale-language sweep AND create the plan-grade §9.3 mlx-lm upstream watch ledger, both deferred during D5/D6/D7 by [[feedback-staging-discipline]]
> **Trigger**: Campaign D fully closed 2026-05-27 (D5 + D6 + D7 all passed and pushed); DSV4-Flash 2bit-DQ now at `lane=technical_preview`, `verdict=partial`, registered on `/v1/runtime/model-visibility` only
> **Plan-grade source**: [`../architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`](../architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md) §13
> **Status of this handoff**: prepared 2026-05-27 immediately after Campaign D closeout; should be picked up by a **fresh session** per [[feedback-fresh-session-grade-transitions]]
> **Language discipline**: this handoff edits documents that describe completed evidence. It does NOT claim new evidence, does NOT promote any capability label beyond what D7 already promoted, and does NOT touch `owlmlx/` package source.

---

## 0. 给新 session 的开场指令

**You are the post-Campaign-D closeout session.** D1-D7 are all passed and pushed:

| Stage | Verdict | Anchor |
|---|---|---|
| D1 (isolated repeatability ladder) | passed 2026-05-17 | `files/evidence/owlmlx/deepseek-v4/d1-isolated-repeatability/20260517T-d1-full-ladder-adopted-messages-policy.jsonl` |
| D2 (metrics ledger) | passed 2026-05-17 | `files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl` |
| D3 (MTP checkpoint inspection) | closed 2026-05-17 | `files/evidence/owlmlx/deepseek-v4/d3-checkpoint-inspection/20260517T-d3-mtp-checkpoint-inspection.jsonl` |
| D4 (clean pre-load reject) | closed 2026-05-17 | `files/evidence/owlmlx/deepseek-v4/d4-preload-reject/20260517T-d4-mtp-clean-preload-reject.jsonl` |
| D5 (sustained-load N≥20) | passed 2026-05-27 | `files/evidence/owlmlx/deepseek-v4/d5-sustained-load/20260527T084115Z-d5-sustained-load.{jsonl,summary.json}` |
| D6 (mainline backend integration) | passed 2026-05-27 under amended §7.1 item 7 | `files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/20260527T072206Z-d6-mainline-backend-lifecycle.{jsonl,summary.json}` |
| D7 (technical_preview visibility) | passed 2026-05-27 | `files/evidence/owlmlx/deepseek-v4/d7-technical-preview-visibility/20260527T093211Z-d7-technical-preview-visibility.jsonl` |

Your **only** deliverables this session:

1. **Sweep**: apply the plan-grade §13 stale-language updates to 2 source-of-truth docs (specific line anchors below).
2. **Watch ledger**: create one new short source-of-truth file `docs/source-of-truth/mlx-lm-upstream-watch.md` per plan §9.3.

You will NOT:

- Write a new design-spec or code-grade artifact (Campaign D is closed).
- Touch `owlmlx/` package source (D7 already locked the relevant code surfaces).
- Touch any `tests/` file.
- Promote any capability label further (`partial` is the ceiling until upstream `mlx-lm` mainline merges DSV4).
- Make claims about oMLX / vMLX measured TPS comparison (banned per [[public-claim-matrix.md]] §3).
- Reorganize files / move files / rename files.
- Re-run any D evidence (every D row is frozen).

---

## 1. Mission Detail · Sweep

Plan-grade §13 lists 5 stale-language locations. D7 code-grade already covered the 2 that are runtime/data state (capability matrix DSV4 row, bring-up-status §4). The remaining 3 sweep items belong to this closeout session.

### 1.1 [`docs/architect/02-state-vs-market-gap.md`](../architect/02-state-vs-market-gap.md) §3.5 (DSV4 row)

**Current wording context**: §3.5 (Quantization & MoE) likely contains a row that classifies DSV4 as "刻意不追" or equivalent older language predating Campaign D upgrade. Use `grep -n "DSV4\|DeepSeek V4\|DeepSeek-V4" docs/architect/02-state-vs-market-gap.md` to locate; then update the wording to reflect:

- "刻意不追" / "deferred" framing → **REPLACED** by "Campaign D upgrade 已闭环 (2026-05-27)"
- Add evidence pointers: D5 + D6 + D7 in `files/evidence/owlmlx/deepseek-v4/d{5,6,7}-...`
- State current capability label: `partial` (NOT `supported`)
- State current visibility: `/v1/runtime/model-visibility` `technical_preview` tier only
- Honor the §1 hard rule: do NOT claim DSV4 reaches `supported` until upstream mlx-lm merges

The exact wording is your call — match the surrounding row style. The hard constraint is honesty: every claim must be backed by a frozen evidence row.

### 1.2 [`docs/source-of-truth/reference-runtime-comparison-matrix.md`](../source-of-truth/reference-runtime-comparison-matrix.md) §8 (新出现的硬差距 block)

**Current state**: This file already has uncommitted modifications in the working tree (~227 lines changed, +201/-32). Run `git diff -- docs/source-of-truth/reference-runtime-comparison-matrix.md` first to see what's already drafted. If the diff already represents the §8 sweep, **review it for correctness** and stage it as part of this round; do NOT discard it.

If the diff does NOT cover §8, then add a wording change to mark the DSV4 hard-gap entry as "resolved at `technical_preview` tier on 2026-05-27; capability label `partial`; NOT on `/v1/models` default surface". The exact phrasing matches the surrounding §8 entry style.

**Important**: this file was identified as "out of D5/D6/D7 round scope" in earlier turns per [[feedback-staging-discipline]]. This closeout round is the correct place to stage it. Other dirty files in the tree (`owlmlx/speculative/suffix_decoding/__init__.py`, `owlmlx/speculative/suffix_decoding/runtime.py`, `docs/architect/04-architecture-canvas.html`, `docs/source-of-truth/competitor-capability-matrix-20260527.md`, `docs/source-of-truth/ds4-mtp-local-llm-stack-research.zh-20260514.md`, `软件著作权申请资料/`) are **NOT** part of this sweep — they belong to unrelated work streams and must stay out of this commit.

### 1.3 [`docs/architect/01-mainline-roadmap.md`](../architect/01-mainline-roadmap.md) DSV4 references (optional, low priority)

If grep shows any stale DSV4 wording in `01-mainline-roadmap.md` Campaign D section (lines 35-38 / 320 / 455 area mentioned in plan §14 references), update the brief mentions to "Campaign D closed 2026-05-27 → DSV4 at `partial` + `technical_preview`". Keep edits **minimal** — this file is a high-traffic doc and most of its text is still accurate; only the explicit Campaign D status line needs touching.

If the file already reflects the post-D7 state, skip this item — do NOT make cosmetic changes.

---

## 2. Mission Detail · Upstream Watch Ledger

Plan-grade §9.3 specifies a new source-of-truth file at `docs/source-of-truth/mlx-lm-upstream-watch.md`. The file does not yet exist. Your task: create it with the following shape.

### 2.1 File location and shape

```text
docs/source-of-truth/mlx-lm-upstream-watch.md
```

Suggested structure (you may adjust subsection ordering to match existing source-of-truth files like [`deepseek-v4-bring-up-status.md`](../source-of-truth/deepseek-v4-bring-up-status.md)):

```text
# mlx-lm Upstream Watch Ledger

> Status: authoritative
> Created: 2026-05-27 (Campaign D closeout)
> Scope: track upstream mlx-lm activity that affects owlmlx's DSV4 (and future model) integration paths; each watched item has a defined trigger condition that re-opens the relevant campaign

## 1. Purpose

owlmlx pins mlx-lm to specific commits in optional dependency groups
(see `pyproject.toml` extras `deepseek-experimental`). When upstream
state changes, the pinned commit can become inadequate (mainline merge
finally lands → consider pin removal) or unsafe (fork abandoned →
switch candidate). This ledger lists the watched items, the trigger
condition for each, and what owlmlx-side action results.

## 2. Currently Pinned Upstream Dependencies

| Optional extras group | Upstream | Commit / branch | Reason for pin |
|---|---|---|---|
| `deepseek-experimental` | https://github.com/Blaizzy/mlx-lm | `5c10538136b9038b9626c134612b08afc18d697a` (on branch `pc/add-deepseekv4flash-model`) | Adds `mlx_lm.models.deepseek_v4` not yet in mainline; sole path enabling D1-D7 evidence |

## 3. Watched Items

### 3.1 ml-explore/mlx-lm#1233 — "Add model support for DeepSeek-V4 (deepseek_v4)" (issue)

- **State at watch creation**: open
- **Trigger**: closed (with merge of any DSV4-adding PR) OR closed (without merge, e.g., upstream rejection)
- **owlmlx action on merge**: re-evaluate whether `deepseek-experimental` extras can switch to a tagged mlx-lm release; if yes, a new campaign-D-follow-up round decides `supported` promotion candidacy (NOT automatic).
- **owlmlx action on close-without-merge**: confirm `deepseek-experimental` extras keep working against Blaizzy fork; if Blaizzy fork goes stale, evaluate candidate switch to #1195 / #1189 / #1201.

### 3.2 ml-explore/mlx-lm#1192 — Blaizzy "Add DeepSeek-v4 (Flash/Pro)" (PR; current primary)

- **State at watch creation**: open (commit `5c10538136b9038b9626c134612b08afc18d697a`)
- **Trigger**: any of {merged into mlx-lm mainline, abandoned by author, force-pushed in a way that invalidates `5c10538136b9038b9626c134612b08afc18d697a`}
- **owlmlx action on merge**: pin removal candidate (see 3.1).
- **owlmlx action on abandon/invalidate**: switch `deepseek-experimental` extras to a candidate PR (3.3 / 3.4 / 3.5) by editing `pyproject.toml`; trigger a fresh D6 lifecycle re-validation under the new pin.

### 3.3 ml-explore/mlx-lm#1195 (candidate switch target)

- **State at watch creation**: open / draft (depending on observation date)
- **Trigger**: draft → ready / merged
- **owlmlx action**: candidate evaluation; not auto-switched.

### 3.4 ml-explore/mlx-lm#1189 (candidate switch target)

- Same shape as 3.3.

### 3.5 ml-explore/mlx-lm#1201 (candidate switch target)

- Same shape as 3.3.

## 4. Review Cadence

This ledger is reviewed every 4 weeks (suggested cadence; not enforced
automatically). A review consists of:

1. `gh issue view ml-explore/mlx-lm 1233` (or web equivalent)
2. `gh pr view ml-explore/mlx-lm 1192 1195 1189 1201` (or web)
3. If any state change matches a trigger above, open a fresh
   campaign-D-follow-up round; this ledger is updated in that round.

## 5. Update Rule

This ledger is updated when:

- A watched item changes state and triggers an owlmlx-side action.
- A new mlx-lm release impacts the optional dependency groups in `pyproject.toml`.
- A new optional dependency group is added in `pyproject.toml` (extends the watch table in §2).

## 6. References

- [`docs/architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`](../architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md) §9.3 (origin of this ledger)
- [`docs/source-of-truth/deepseek-v4-bring-up-status.md`](deepseek-v4-bring-up-status.md) §2 (upstream dependency notes)
- [`pyproject.toml`](../../pyproject.toml) `[project.optional-dependencies]` (currently pinned commits)
- [`docs/architect/design/D6-mainline-backend-integration-spec.md`](../architect/design/D6-mainline-backend-integration-spec.md) §3.1 (Blaizzy fork pin rationale)
```

The above template is **prescriptive on structure**, **suggestive on prose** — you may tighten or expand prose, but do NOT remove any section heading and do NOT remove any of the 5 watched-item entries (3.1-3.5).

### 2.2 What this ledger does NOT do

- Does NOT promise any owlmlx action will be taken automatically.
- Does NOT claim parity / replacement / equivalence with upstream-merged behavior (banned vocabulary).
- Does NOT supersede the D6 spec's §3.1 invariants — pin changes still require a campaign-D-follow-up round.
- Does NOT include any non-public information about upstream contributors.

---

## 3. Acceptance for This Handoff

The fresh session closes when:

1. Sweep changes landed in [`docs/architect/02-state-vs-market-gap.md`](../architect/02-state-vs-market-gap.md) §3.5 (DSV4 wording updated).
2. Sweep changes landed in [`docs/source-of-truth/reference-runtime-comparison-matrix.md`](../source-of-truth/reference-runtime-comparison-matrix.md) §8 (DSV4 hard-gap entry marked resolved; the pre-existing working-tree diff reviewed and either kept or replaced with a tighter version).
3. (Optional) Minor wording adjustment landed in [`docs/architect/01-mainline-roadmap.md`](../architect/01-mainline-roadmap.md) Campaign D section if any post-D7 stale language is found; skip if already current.
4. New file `docs/source-of-truth/mlx-lm-upstream-watch.md` created per §2.
5. No `owlmlx/` package source change.
6. No `tests/` change.
7. No new design-spec / plan-grade / phase-prompt file.
8. One commit, one push. Suggested commit message: `docs: campaign-d closeout sweep + mlx-lm upstream watch ledger`.

### 3.1 Hard Rules (every one of these is a closeout-session review checkbox)

- [ ] DSV4 capability label remains `partial` everywhere; nowhere does the word `supported` appear in association with DSV4 in any edited file.
- [ ] `/v1/runtime/model-visibility` is the only visibility surface mentioned for DSV4 in any edited file; `/v1/models` and `/v1/openai/models` are explicitly excluded from any DSV4 visibility claim.
- [ ] Banned vocabulary (`parity` / `replacement` / `equivalent` / `production_ready` / `production-ready` / `beats` / `wins` / `matches` per [`public-claim-matrix.md`](../source-of-truth/public-claim-matrix.md) §3 + [`owlmlx/model_release_candidate_schema.py`](../../owlmlx/model_release_candidate_schema.py) `BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY`) appears nowhere in the new strings.
- [ ] The upstream watch ledger does NOT make promises owlmlx is not committed to; trigger actions are stated as "evaluate" / "consider", not "will switch".
- [ ] No file under `owlmlx/` is created or modified.
- [ ] No file under `tests/` is created or modified.
- [ ] No file under `docs/architect/design/` is created or modified (Campaign D specs are frozen).
- [ ] No file under `docs/phase-prompts/` is created or modified except possibly this handoff itself (you may amend its Change Log on completion; do not need to).
- [ ] Other dirty/untracked tree files (suffix_decoding C2 残留, canvas, competitor-capability-matrix-20260527, ds4-mtp-research, 软件著作权申请资料) stay OUT of the commit.

### 3.2 Acceptance verification commands

```bash
# 1. Confirm changed files match scope:
git status --short
git diff --stat HEAD

# 2. Banned vocabulary scan on the closeout diff:
git diff HEAD -- docs/ | grep -E "^\+" | grep -iE "parity with|matches oMLX|matches vMLX|beats oMLX|beats vMLX|equivalent to oMLX|equivalent to vMLX|replaces oMLX|replaces vMLX|production[ _-]ready"

# 3. DSV4 supported-claim regression scan:
grep -rn "DeepSeek-V4-Flash-2bit-DQ" docs/ | grep -iE "supported" | grep -v "not_supported\|NOT supported\|not be supported\|until upstream"

# 4. Watch ledger exists and is valid markdown:
ls -la docs/source-of-truth/mlx-lm-upstream-watch.md
head -10 docs/source-of-truth/mlx-lm-upstream-watch.md
```

All four commands MUST return clean output (no banned phrases; no spurious supported-claim).

---

## 4. Next Round After This Handoff

After closeout commit landed:

1. **mlx-lm watch review** (independent cadence, ~4 weeks): walk the new `mlx-lm-upstream-watch.md` ledger. If a trigger fires, that opens a new campaign-D-follow-up round (NOT this closeout's concern).

2. **Next-dominant-gap discovery** (separate fresh session): re-read [[01-mainline-roadmap.md]] and [[02-state-vs-market-gap.md]] to identify the new dominant gap after Campaign D closure. Candidate next campaigns (without prescribing):

   - Campaign A: N≥20 repeatability on 3 mainline models (Gemma 4-31B-it / Qwen3.6-27B / Qwen3.6-35B-A3B) — long-running plan
   - Campaign B-1c §2: wall-clock continuity (currently blocked per roadmap line 96)
   - Campaign E / F-1 / F-2 / F-4 / F-5 advancement
   - A campaign-D-follow-up round if upstream watch fires

   The discovery session itself is plan-grade work; it does NOT belong in this closeout handoff's scope.

3. **`supported`-promotion gating for DSV4**: blocked until ml-explore/mlx-lm mainline merges native DSV4 support. The watch ledger created in §2 is the trigger surface. Do NOT pre-stage any `supported` promotion work in this closeout round.

---

## 5. Reading List (self-contained for the fresh session)

The closeout session needs only these documents loaded:

### 5.1 Authoritative state to read in full

- [`docs/architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`](../architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md) §13 + §9.3 (origin of both sweep and watch ledger)
- [`docs/source-of-truth/deepseek-v4-bring-up-status.md`](../source-of-truth/deepseek-v4-bring-up-status.md) §1 + §4 (current authoritative state; do NOT edit further here unless a sweep change is needed; D7 already updated §4)
- [`docs/architect/design/D7-technical-preview-visibility-spec.md`](../architect/design/D7-technical-preview-visibility-spec.md) §6 (sweep work expectation)

### 5.2 Read only the relevant section

- [`docs/architect/02-state-vs-market-gap.md`](../architect/02-state-vs-market-gap.md) §3.5 (the one row to update; do NOT touch other §)
- [`docs/source-of-truth/reference-runtime-comparison-matrix.md`](../source-of-truth/reference-runtime-comparison-matrix.md) §8 (the resolved-gap block; review the existing working-tree diff first)
- [`docs/architect/01-mainline-roadmap.md`](../architect/01-mainline-roadmap.md) Campaign D section near lines 35-38 / 320 / 455 (only if grep shows stale language)

### 5.3 Code/data references (read-only; do NOT edit)

- [`pyproject.toml`](../../pyproject.toml) `[project.optional-dependencies] deepseek-experimental` (anchor for watch ledger)
- [`owlmlx/model_release_candidate_record.py`](../../owlmlx/model_release_candidate_record.py) lines 39-47 (current DSV4 row; D7 already updated)
- [`owlmlx/model_release_candidate_schema.py`](../../owlmlx/model_release_candidate_schema.py) `BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY` (the authoritative banned list to grep against)

### 5.4 Memory anchors

- [[feedback-fresh-session-grade-transitions]] — why this is a fresh session
- [[feedback-staging-discipline]] — only stage round-scope files; leave unrelated dirty files alone
- [[feedback-stale-language-sweep]] — refresh ALL stale references in a doc, not just add a new section
- [[feedback-evidence-language-calibration]] — keep `plausible` / `load-path-compatible` for unverified outcomes; D5/D6/D7 evidence is verified and may be cited as such

---

## 6. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-27 | Initial Campaign D closeout handoff. Trigger: D7 commit `8ecd9f5a feat: add d7 technical-preview visibility tier` landed and pushed; Campaign D is now fully closed. Scope: sweep deferred docs (per plan §13) + create mlx-lm upstream watch ledger (per plan §9.3). Routed work to a fresh session per [[feedback-fresh-session-grade-transitions]] to avoid mixing closeout cleanup with the technical D5/D6/D7 conversation context. No new design-grade or code-grade artifact is in scope. | Codex closeout loop (with user direction) |
