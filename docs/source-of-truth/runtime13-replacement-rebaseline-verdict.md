# Runtime-13 — Replacement Re-baseline Verdict

> Status: **Runtime-13 re-baseline (assessment only — promotes nothing)**
> Date: 2026-06-03
> Supersedes (classification only): `runtime12-replacement-readiness-verdict.md` (2026-04-12) + `replacement-grade-stability-gaps.md` (2026-04-22) point-in-time blocker/gap classifications. Those docs' narrative bodies stand as history.
> Spec: `docs/architect/design/R0-replacement-rebaseline-spec.md`
> Plan-grade 来源: `docs/architect/01-mainline-roadmap.md`「下阶段主线声明（替代收口）」; Runtime-12 §7 ("Runtime-13 = actual replacement work")
> Evidence priority (every finding): current source-of-truth doc → capability matrix → real tests/evidence ledger → current code path → commit (provenance only).

---

## §1 Verdict

**Old-platform replacement: still NOT yet replaceable** — but the *critical path is materially narrower* than the 2026-04 four-blocker / five-gap enumeration.

**Replacement target (confirmed 2026-06-03):** the **local legacy-router control boundary at `:8009`** (the `llm_router` transitional asset — roadmap §IV.5; OwlCoda's own `legacy_router_platform`) that the consumers (OwlCoda / OwlCC) actually cross. oMLX is the upstream fleet reference and a downstream backend concern, **not a per-line clone target** (§IV.2 boundary holds).

**Why not-yet:** neither consumer is owlmlx-only by default (committed defaults point at `:8009` / `:11434`), and there is **no sustained owlmlx-only ops evidence** (§2). That is an **ops-cutover + evidence** gap, not a runtime-substrate gap.

**What is NO LONGER on the critical path (vs April):** the stability gaps (cache/scheduler depth, multi-model governance, host breadth) are largely **not cutover-blockers** for a single-host boundary replacement (§4). The April "dominant gap = `cache_scheduler_depth` → native backend next" framing is **superseded** (native backend landed; B-1c §2 fast-count canonical passed `189d9d5c`).

This re-baseline **promotes nothing**: Session KV / automatic prefix cache stay `experimental`; the §1a Promotion Gate is unchanged.

---

## §2 Cutover reality (cross-repo READ-ONLY, 2026-06-03)

**OwlCC — single runtime pointer:**
- default `routerUrl = http://127.0.0.1:8009` (`owlcc/config.example.json:4`; `OWLCC_ROUTER_URL` default; `owlcc/src/preflight.ts` probes that one URL's `/healthz` + `/v1/models`).
- No owlmlx-direct default. Cutover = repoint `routerUrl` to owlmlx `:8066` **and** ensure owlmlx serves OwlCC's needed shapes (Anthropic `/v1/messages`, `/v1/models`).

**OwlCoda — owlmlx is one backend among many, but cutover is partially scaffolded:**
- backends = `['ollama','lm-studio','vllm','owlmlx']` (`owlcoda/admin/src/components/AddModelDialog.tsx:56`); admin dev-proxy default `:8009` (`owlcoda/admin/vite.config.ts:7`); `config.example.json` routerUrl `:11434`.
- **owlmlx-gate already modeled:** `owlcoda/admin/src/api/types.ts:45` distinguishes `'owlmlx_runtime_model_visibility' | 'legacy_router_platform_model_visibility'`; `admin/src/lib/availability.ts` + `admin/src/i18n.tsx` carry an `owlmlx-gate` plus "Cut this runtime over to owlmlx … when available", "use owlmlx `/v1/openai/models` as availability truth", "`/v1/runtime/model-visibility` for diagnostics", "`/v1/models` as loaded inventory only". The cutover path is **designed and availability-gated** — not default-on.
- OwlCoda advertises cross-backend + model fallback as supported (`owlcoda/README.md:400-403`) — 容灾 that an owlmlx-only posture would remove reliance on.

**Live-config caveat:** `config.json` is **gitignored** in both repos → the actual runtime pointer is environment-specific. Committed defaults are **not** owlmlx-only.

**"Remove legacy `:8009` fallback today" → breaks what:**
- OwlCC loses its only runtime unless `routerUrl` is repointed to a reachable owlmlx serving its models/shapes.
- OwlCoda requires owlmlx to pass its own availability-gate for every needed model + interaction shape, and removes the cross-backend/model fallback safety net — so owlmlx reliability + shape-parity must be high enough to not need it.

---

## §3 The 4 Runtime-12 blockers, re-classified

| # | Blocker | Now | Evidence (priority-tagged) | Cutover-blocking? | → |
|---|---|---|---|---|---|
| ① | source-first parity (all interaction shapes) | ◐ partial | matrix: OpenAI `/v1/chat/completions`+`/v1/completions`, Anthropic `/v1/messages`+`count_tokens`, SSE = **supported**; OpenAI tool-calling = **experimental (Qwen-only)**; Runtime-10 source-first tool-loop parity = **partial** | **取决于** — blocks any consumer flow needing tool-calling beyond Qwen, or a not-yet-parity shape | **R1** |
| ② | production control-plane closure | ◐ (surfaces strong) | matrix: `/v1/runtime/status` frozen contract, `healthz`, restart contract, model-visibility, monitor/metrics = **supported**; Runtime-9 control-plane operability proven; Runtime-12 doctor verdict surface complete; "production closure" last-mile not frozen | **大多不阻断** — surfaces exist; remaining is ops verification | **R2** |
| ③ | backend quality parity (**DEMOTED → no-regression**) | ◐ no-regression lens | matrix: real serving **supported** (subprocess backend, multi-model), `gemma-4-31B-it` production mainline; native backend experimental; no formal parity-vs-legacy comparison | **取决于** — only if owlmlx serving a needed model regresses vs the legacy path | no-regression check inside **R4** |
| ④ | ops-level replacement not verified | ⛔ open | §2: defaults not owlmlx-only; no sustained owlmlx-only ops evidence | **会** — this IS the cutover | **R4** |

---

## §4 The 5 replacement-grade stability gaps, re-classified

| Gap | Now (vs 2026-04) | Evidence | Cutover-blocking? |
|---|---|---|---|
| `host_stable_execution` | ◐ mostly closed | supported-host baseline established; `gemma-4-31B-it` 62G fits + repeated proof; host-stability rows **supported** | **不会** (single-host candidate valid) |
| `cache_scheduler_depth` | ◐ — April "dominant / native-next" **STALE** | native backend landed; B-1c §2 fast-count canonical `189d9d5c`; B-2 in progress; Session KV / prefix cache experimental; continuous batching out-of-scope **by design** | **不会** (perf/reliability enhancer, not a boundary blocker; consumers don't need batching) |
| `multi_model_lifecycle_governance` | ✅ mostly closed | pin / TTL / eviction-history **supported** (matrix); governance observation `partial` | **不会** |
| `heavy_weight_runtime_repeatability` | ◐ | `gemma` repeated proof; DeepSeek technical-preview `partial`; Kimi 122G > 116G budget-blocked (out of single-host scope) | **取决于** — only if a needed consumer model exceeds budget / lacks repeat proof |
| `customer_runtime_evidence` | ⛔ open | still `early_formal_runtime`; no owlmlx-only consumer ops evidence | **会** (overlaps blocker ④; the evidence R4 must produce) |

---

## §5 Narrowed remaining-blocker list → R-series

**Critical path (cutover-blocking = 会 / 取决于):**

- **R1 — source-first parity gap:** bring tool-calling to parity for the consumers' *actual* shapes (beyond Qwen-only experimental); confirm every interaction shape OwlCoda/OwlCC use is `supported`, not `experimental`. [blocker ①]
- **R2 — production control-plane closure:** finalize the last-mile ops/control-plane closure beyond seam-proof. [blocker ②]
- **R4 — ops cutover + customer evidence (the core):** flip defaults to owlmlx (OwlCoda via its existing `owlmlx-gate`; OwlCC `routerUrl` repoint), remove legacy `:8009` fallback, run sustained owlmlx-only, capture customer-runtime evidence to move past `early_formal_runtime`. Folds in the no-regression check (demoted blocker ③) and any budget-fit / repeatability confirmation for the consumers' needed models (conditional gap 4). [blockers ④ + ③; gap 5 + conditional gap 4]

**Off critical path (NOT cutover-blockers — do not gate the cutover on these):**

- `cache_scheduler_depth` (gap 2), `host` long-run breadth (gap 1), multi-model governance beyond-closed (gap 3). These continue as runtime-quality work (e.g., B-2), independent of the boundary cutover.

---

## §6 Scope & honesty

- Assessment-only: **promotes nothing**. Verdict stays `not yet replaceable`. Session KV / prefix cache stay `experimental`. §1a Promotion Gate unchanged.
- "替代" = boundary-level (owlmlx takes the `:8009` runtime control boundary); **not** fleet / batching / per-line clone (§IV.2 out-of-scope holds).
- Evidence priority honored: classifications lean on the current capability matrix + cross-repo source reads; commits cited only as provenance.
- Cross-repo reads were **READ-ONLY**; no file in owlmlx / OwlCoda / OwlCC / oMLX was modified by R0 except this verdict + the two stale banners (§ added to `runtime12` + `replacement-grade-stability-gaps`).
- Next: R1 / R2 / R4 each gets its own design spec → plan → execution, driven by §5. R3 stays demoted to a no-regression check inside R4.
