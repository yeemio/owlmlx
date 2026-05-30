# Phase: Source-of-Truth Audit-Fix Round (apply the 23 findings — staleness sweep, NO promotions)

> **Grade**: doc-correctness only. NO production code change, NO capability-label
> promotion. The dominant deliverable is: make the source-of-truth docs match
> current code/state, using the verified findings below.
> **Mission**: apply the 23 findings from the 2026-05-30 full source-of-truth
> audit. Every finding is **staleness or an internal inconsistency** — there is
> **NO capability over-statement** in the corpus (the audit confirmed nobody wrote
> `partial`/`experimental` as `supported`). Most are *under*-statements (a doc
> claims LESS than the code now does) or stale module paths / a rename not swept.
> **Pick up in a FRESH session** per [[feedback-fresh-session-grade-transitions]]:
> the audit (the "plan") ran in a long context-heavy session; the fixes (the
> "edits") belong to a clean executor.
> **Prepared**: 2026-05-30, from origin/main `b2f8bb18`.

---

## 1. Identity and mission

You are the source-of-truth **fix executor**. A 15-agent parallel audit over 86
non-phase45 truth docs produced 23 findings (68 docs were clean). Your job: turn
each finding into an accurate doc, **without** changing any capability label,
touching production code, or rewriting frozen historical records destructively.
Add dated correction banners, repoint dead module paths, sweep one rename, and
fix two internal inconsistencies.

## 2. First principles

- **Fix toward accuracy, not toward "more impressive."** Several findings are the
  doc *under*-claiming (scaffold docs written before a wiring commit landed). The
  fix is to state what the code now does — not to inflate it.
- **Preserve history.** Frozen round-records / dated snapshots may keep their
  original text; the right fix there is a dated banner ("since superseded by
  commit X"), not a destructive rewrite.
- **Do NOT change any capability label.** No `supported`/`partial`/`experimental`
  edges move in this round. This is doc-truth alignment, not a promotion review.
- **Verify each finding against current code before editing.** The audit verified
  them, but re-confirm with `grep`/`git show` so your edit cites real anchors.
- **The `reclaim_barrier_event` → `settle_barrier_event` rename is a known
  backlog** (commit `015c7580` says so). Sweep the doc references — but KEEP the
  HTTP route URL `/v1/runtime/reclaim-barrier-event` and kernel-internal event
  vocabulary, which were intentionally NOT renamed.

## 3. Current real state (verified, 2026-05-30)

| Fact | State | Anchor |
|---|---|---|
| origin/main == HEAD | `b2f8bb18`, synced (0/0) | `git rev-parse` |
| F-4 grammar lane | closed out, registered `partial` in capability matrix | `f8e0c6fc`, `a0f313bb`, `12449b23` |
| B-1c §2 | blocker taxonomy landed (runtime functional; blocked on measurement continuity) | `e7600dd8`, spec §11 |
| RC2 wording | fixed (was "非 wrapping mlx_lm"); 3 high-risk-tier stale banners added | `b2f8bb18` |
| Full audit (this round's input) | 86 docs, 15 agents, **23 findings / 68 clean, ZERO over-claiming** | §4 below (embedded) |
| 7 dirty/untracked files | leave OUT of every commit (§6) | `git status` |
| reference-runtime-comparison-matrix.md | **DIRTY (M)** + has a HIGH-confidence DeepSeek staleness — handle as the §8 Wave-6 sub-task, NOT a normal edit | §4 finding R0 |

## 4. The 23 findings (verified; this is the work-list)

> Issue types: (3) stale/superseded · (5) internal/cross-doc contradiction ·
> (2) mlx_lm/native phrasing. Confidence: H/M/L.

### Theme A — rename `owlmlx.reclaim_barrier_event` → `owlmlx.settle_barrier_event` (commit `015c7580`). KEEP route URL + kernel event vocab.
| # | Doc | Location | Conf | Fix |
|---|---|---|---|---|
| A1 | `reclaim-barrier-event.md` | §2 L27-39 | H | module `owlmlx/reclaim_barrier_event.py`→`settle_barrier_event.py`; `build_reclaim_barrier_event`→`build_settle_barrier_event`; `*_to_dict` likewise; surface `"owlmlx.reclaim_barrier_event"`→`"owlmlx.settle_barrier_event"`. Keep route `/v1/runtime/reclaim-barrier-event` + kernel `reclaim_barrier` section as-is. |
| A2 | `recovery-supervisor-contract.md` | §4 L75 | H | surface name → `owlmlx.settle_barrier_event` (the consuming `recovery_supervisor.py` already imports `build_settle_barrier_event`). §2 of this doc is correct — do not touch. |
| A3 | `orchestration-status-surface.md` | §4 L104, §5 L124 | M | both `owlmlx.reclaim_barrier_event` surface refs → `owlmlx.settle_barrier_event`. |
| A4 | `release-readiness-backlog.md` | §5 row 3.4 L255 | M | dead ref `tests/test_reclaim_barrier_event.py` → `tests/test_settle_barrier_event.py`. |
| A5 | `release-readiness-execution-plan.md` | §6 L1267-1270, ~L1419 | L | historical round-record. Add a dated note that module/surface/test were later renamed (`015c7580`); keep the route URL. Optional — it is an append-only log. |

### Theme B — scaffold docs not refreshed after their wiring commit landed (doc claims LESS than code). Add a dated banner; do NOT rewrite the scaffold narrative.
| # | Doc | Location | Conf | Fix |
|---|---|---|---|---|
| B1 | `cache-manager-architecture.md` | §8 L222/231, §9 L236-237 | H | §1 already says CacheManager IS consumed by `MlxNativeBackend` (2026-05-12). §8/§9 still say "unwired / adapter untouched". Add banner: wired via C-1.1/C-1.2 (`mlx_native_backend.py` instantiation + acquire/release; commit `fc27a021`); keep "no matrix row promoted" (true). |
| B2 | `memory-actuator-architecture.md` | §1 L41-44, §3 L73-78, §12 L352-354 | H | "owlmlx calls none of `mx.clear_cache`/`set_cache_limit`/`set_wired_limit`" is false post-`9f3c03c9`: native unload calls `release_single_model`→`mx.clear_cache()`; load calls `configure_allocator_floor`. `UnloadResult` now carries freed-bytes (`types.py`). Add dated banner; scope §2/§11.2/§12 "not yet/out-of-scope" to the scaffold round. |
| B3 | `serving-hardening-architecture.md` | §1 L18-26, §2 L33-51, §5.1 L115, §10 | H | "server.py has zero hardening primitives / not modified" is false post-`20645b7d`/`e339c774`: RequestIdMiddleware, GracefulShutdown, error-envelope handlers, MetricsSnapshotExporter, `GET /metrics` are wired. Add dated banner; refresh stale line anchors (file is 2056 lines not 2343; `serving.py` `.wait()` at 193/300/456/599 not 417). Note the one still-unwired hardening (§5.2 timeout/disconnect). |

### Theme C — dead module paths from Stage-1 archival (modules moved to `archive/spec-layer-v0/owlmlx/`).
| # | Doc | Location | Conf | Fix |
|---|---|---|---|---|
| C1 | `large-weight-path-truth.md` | §3 Owned Modules L60-68 | M | rows `validate_runtime_status` / `normalize_large_weight_runtime_status` cite archived `owlmlx/runtime_status.py` (archived `1475e339`). Repoint to live owner `owlmlx/runtime_health.py` (+ `runtime/types.py`/`kernel.py`) or note consolidation. Other 3 rows verified live — keep. |
| C2 | `ownership-boundary.md` | §3.1 row R2 | L | R2 Current-Location `owlmlx/runtime_status.py` → `owlmlx/runtime/types.py` (RuntimeStatus) + `kernel.py` (status/status_dict). Other ~10 paths verified OK. |
| C3 | `cache-manager-architecture.md` | §3 L57/61/70, §5.3 L134 | M | "141 `cache_*.py` files in `owlmlx/`" + `cache_pre_claim_*/pre_gate_*/closure_rung/counter_*` paths are stale (archived `a6d32665`/`a2bc5dd5`); only 4 cache_*.py live in `owlmlx/`. Update count + repoint to `archive/spec-layer-v0/` or note archival. |
| C4 | `repeatability-harness-architecture.md` | §2 L60-69, §3 L90/92/93 | L | 3 modules (`heavy_weight_repeatability_status.py`, `cache_repeatability_evidence.py`, `cache_runtime_observation_harness.py`) cite live `owlmlx/` paths but are archived. Doc is already "archived scaffold" — repoint paths or one-line archival note. |

### Theme D — internal inconsistencies.
| # | Doc | Location | Conf | Fix |
|---|---|---|---|---|
| D1 | `runtime-contracts.md` | §2 L16 | H | "three first-class contract families" but the list below has **five** (§§4-8 each document one). Change "three" → "five". |
| D2 | `training-substrate-contract.md` | §5.2 L129-139 | L | loss `10.7 → 6.1` contradicts peer `gemma-high-fidelity-role.md` + commit `3483afe4` (`10.5 → 6.5`); and `180-254 tok/s` conflates the 65 tok/s pilot with the viability test. Reconcile to the peer doc's numbers + split pilot vs viability. |

### Theme E — stale repo-hygiene facts (`uv.lock` committed `90cefa5e`, 2026-05-09).
| # | Doc | Location | Conf | Fix |
|---|---|---|---|---|
| E1 | `python-environment.md` | TL;DR L12, L131, L36-37 | M | "deliberately does NOT stage `uv.lock` yet" is false — committed `90cefa5e`. Update to "now staged/committed". |
| E2 | `python-environment-research.md` | §1.3 L64 | L | header "uv.lock state (untracked in git)" — now tracked. Dated 2026-05-08 snapshot; one-line "Update (2026-05-09): since committed" suffices. |

### Theme F — low-confidence judgment calls (decide per-item; default = light touch).
| # | Doc | Location | Conf | Fix |
|---|---|---|---|---|
| F1 | `native-mlx-backend-conversion-path-ownership.md` | §1 L12 | L | cites a `README.md` "Project Definition" section that does NOT exist; the identity quote lives in `AGENTS.md:39` / `master-outline.md:225`. Repoint the citation (claim text is fine). |
| F2 | `model-line-placement.md` | §3.5 L141, §4 L181 | L | `Qwen3.5-35B-A3B-4bit` old name in a **frozen Round-3 (2026-04-10) record**. Either refresh to Qwen3.6 or leave with a dated note. Judgment — it is a historical placement record. |
| F3 | `runtime-spine-architecture-blueprint.zh.md` | §5 L302 | L | bare "不是 ... wrapper" in an identity row. Defensible in context (surrounding text frames MLX as the wrapped substrate). Optional: disambiguate to "不是薄封装 passthrough wrapper — 在 mlx/mlx-lm 之上拥有独立 runtime 身份". |

## 5. Must-read files (load before editing)

1. The 7 hard-rule dirty files list (§6) — never stage them.
2. `docs/source-of-truth/public-claim-matrix.md` §3 — banned vocabulary (do not introduce as claims).
3. For each finding: the cited code anchor (e.g. `owlmlx/runtime/mlx_native_backend.py`, `owlmlx/settle_barrier_event.py`, `owlmlx/runtime/server.py`) — re-verify before editing.
4. `docs/source-of-truth/runtime-capability-matrix.md` — the canonical labels (so you confirm you are NOT moving any).

## 6. Hard rules

- [ ] **NO capability-label change.** Grep your diff: no `supported`/`partial`/`experimental`/`not_in_scope` edge moves. This round only aligns prose/paths/names to code.
- [ ] **NO production code change.** Docs only. If you reach for `owlmlx/**/*.py`, stop.
- [ ] **Leave these 7 dirty/untracked files OUT of every commit**: `reference-runtime-comparison-matrix.md`, `owlmlx/speculative/suffix_decoding/{__init__.py,runtime.py}`, `docs/architect/04-architecture-canvas.html`, `competitor-capability-matrix-20260527.md`, `ds4-mtp-local-llm-stack-research.zh-20260514.md`, `owl-lora-pipeline/`, `软件著作权申请资料/`.
- [ ] **Banned vocab** (`parity`/`equivalent`/`production_ready`/`production-grade`/`beats`/`matches`) introduced as a CLAIM in no new line (disclaimers OK).
- [ ] **Preserve history**: frozen round-records / dated snapshots get a dated banner, not a destructive rewrite.
- [ ] **Verify before edit**: re-confirm each finding's anchor with grep/git; if a finding does NOT reproduce against current code, SKIP it and note why (the audit could be wrong — honest negatives are valid).
- [ ] **Push only if the user says so** this round; else leave local and report ahead count.

## 7. Pre-registered acceptance

- Every High + Medium finding (A1-A4, B1-B3, C1, C3, D1, E1) is either fixed or explicitly skipped-with-reason.
- Low findings (A5, C2, C4, D2, E2, F1-F3) are each either fixed or listed as a deliberate leave-as-is with one-line rationale.
- No capability label changed; banned-vocab grep on diff empty; `git diff --check` clean.

## 8. Wave plan (~2-3h, branch at Wave 6)

### Wave 1 — Rename sweep (A1-A4; A5 optional) (~30 min)
- Sweep `reclaim_barrier_event` → `settle_barrier_event` doc refs. KEEP route URL + kernel vocab. Verify against `owlmlx/settle_barrier_event.py` + `recovery_supervisor.py`.
- **Acceptance**: the 4 surface/module/test refs corrected; route URL untouched.

### Wave 2 — Scaffold banners (B1-B3) (~40 min)
- Add dated "wiring since landed (commit X)" banners; refresh stale line anchors in B3. Verify each against the cited code lines.
- **Acceptance**: each scaffold doc points readers to current as-built state; scaffold history preserved.

### Wave 3 — Dead module paths (C1-C4) (~30 min)
- Repoint archived-module citations to live owners or `archive/spec-layer-v0/`; fix the "141 files" count.
- **Acceptance**: no doc cites a non-existent `owlmlx/` module path as live.

### Wave 4 — Internal inconsistencies + repo facts (D1, D2, E1, E2) (~20 min)
- `runtime-contracts` three→five; reconcile `training-substrate` numbers to the peer doc + commit; uv.lock now-committed.
- **Acceptance**: D1 count agrees with the list; D2 numbers agree across both docs.

### Wave 5 — Judgment calls (F1-F3) (~15 min)
- F1 repoint README citation; F2 decide refresh-vs-historical-note; F3 optional disambiguation. Record each decision.
- **Acceptance**: each low finding has a recorded disposition.

### Wave 6 — Checks, commit, report (~15 min)
- `git diff --check`; banned-vocab grep on diff; grep confirming no capability-label edge moved; stage ONLY the docs you fixed (NOT the 7 dirty files). One or a few thematic commits.
- **Acceptance**: clean checks; dirty set intact; ahead count reported.

### Wave 6b — (SEPARATE sub-task) reference-runtime-comparison-matrix DeepSeek staleness (R0)
- This doc is **already dirty (M)**. It still frames owlmlx DeepSeek as "clean reject only / forever reject" (§0.1.4, §3, §8), contradicting the DeepSeek-V4-Flash `partial`/`technical_preview` promotion (D5/D6/D7). HIGH confidence, real.
- **First read the existing dirty diff** (`git diff -- docs/source-of-truth/reference-runtime-comparison-matrix.md`) to understand what is already modified, THEN decide with the user whether to fold the DeepSeek fix in or keep it separate. Do NOT blind-commit a mixed dirty file.

## 9. Required tests / checks

- `git diff --check` clean.
- Banned-vocab grep on the diff returns empty (claims only; disclaimers OK).
- `git diff | grep -E '^[-+].*(supported|partial|experimental|not_in_scope)'` shows NO label edge moved (only path/name/prose/banner changes).
- Spot-verify ≥3 fixes against the cited code anchor.

## 10. Verification assets to produce

- A short fix-ledger: each of the 23 findings → {fixed | skipped+reason | deferred}.
- The commit(s) touching only the fixed docs.

## 11. Out of scope

- Any capability-label promotion / demotion (this is alignment, not review).
- Production code changes.
- The 7 dirty files (except R0, handled as the careful Wave-6b sub-task).
- Re-auditing (done) and the ~80 phase45 docs (not in this round's corpus).

## 12. Final report format (required)

- Modified files · Wave-by-wave outcomes · fix-ledger (23 findings disposition)
- New user-visible capability: NONE (doc-truth alignment only) — state this explicitly
- Tests/checks run + results · `git diff --check` + banned-vocab + label-edge scan
- Capability-honesty delta: confirm no label moved
- Remaining: R0 DeepSeek dirty-file decision; any skipped findings
- Why this round materially advanced delivery: the source-of-truth now aligns with code (no stale/contradictory claims a future reader would trust)

## 13. Suggested commit message

`docs(source-of-truth): apply audit findings — rename sweep + scaffold banners + dead-path repoints (no label changes)`

## 14. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-30 | Initial fix-round prompt. Routes the 23 verified findings from the full 86-doc source-of-truth audit (15-agent workflow, 0 over-claims, all staleness/inconsistency) to a fresh executor, with a no-promotion / no-code / preserve-history discipline, a rename sweep, scaffold banners, dead-path repoints, two inconsistency fixes, and a separate careful sub-task for the dirty DeepSeek comparison-matrix. Authored after the F-4 + B-1c closeouts to keep grade transitions on a fresh session. | SoT audit session (with user direction) |
