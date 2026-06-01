# owlmlx Reference Runtime Comparison Matrix

> Status: authoritative
> Updated: 2026-05-30 (capability-surface refresh + DSV4 lane correction; measured-data floor 仍以 2026-05-06 为基线)
> Scope: honest runtime-only comparison between `owlmlx` and the current local reference runtimes `oMLX` / `vMLX`
>
> **2026-05-27/30 refresh boundary**: 本次 refresh **仅** capability surface（来自 [`jundot/omlx`](https://github.com/jundot/omlx/releases) + [`jjang-ai/vmlx`](https://github.com/jjang-ai/vmlx/releases) 公开 release notes + 本仓库 `runtime-capability-matrix.md` 2026-05-25/30 update），**不含 probe 复测**——measured TPS / 同 host 数字保留 §0 中 2026-05-06 addendum 基线。要做 measured rerun 见 `scripts/runtime_comparative_evidence.py` + 兄弟目录 `<runtime-probes>/omlx-probe`、`<runtime-probes>/vmlx-probe`。

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
- `DeepSeek-V4-Flash-2bit-DQ`: in the 2026-05-06 measured comparison baseline,
  `owlmlx` also rejected before observable first token through the same missing
  `deepseek_v4` loader support, and the failed load originally dirtied 8066
  backend health until restart.
- `DeepSeek-V4-Flash-2bit-DQ`: follow-up runtime evidence first proved a clean
  pre-load `unsupported_model_family` response, and later Campaign D D5/D6/D7
  moved the owlmlx-owned lane to `partial` / `technical_preview` through the
  `.runtime-deepseek-experimental` path. That newer internal capability does
  **not** replace the 2026-05-06 measured comparison floor and does **not**
  imply default `/v1/models` visibility, stock-mlx-lm support, or parity with
  oMLX/vMLX DeepSeek full-port/composite-cache paths.
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

## 0.1 Capability Surface Refresh — 2026-05-27

Since the 2026-05-06 measured-data baseline, both oMLX and vMLX shipped substantial
capability releases (oMLX: 9 releases in 6 weeks; vMLX: 10 releases + major version
jump). The measured TPS data in §0 is preserved as-is (no probe rerun in this
refresh), but the capability-surface assertions in §3 / §4 / §8 below are recalibrated
against the 2026-05-27 release surface.

### 0.1.1 oMLX (`jundot/omlx`)

- **Latest as of 2026-05-27**: v0.3.12 — 9 releases since v0.3.5 (2026-04-15)
- **Native MTP** for Qwen3.5/3.6 + Gemma 4 (vision path) + DeepSeek-V4 — v0.3.9 (2026-05-21);
  this is the first MTP-on-MLX coverage spanning three model families on this reference runtime
- **DeepSeek V4 Pro/Flash full port** — v0.3.9.dev1 (2026-05-06); F8_E8M0/fp8 quant branch
- **Memory governance overhaul** — v0.3.10 (2026-05-24) / v0.3.11 (2026-05-26) / v0.3.12 (2026-05-27):
  - `phys_footprint`-based enforcement on prefill admission
  - Adaptive prefill chunk throttle 1024 → 512 → 256 → 128 under caution
  - Self-raising Metal wired-limit; kernel `iogpu.wired_limit_mb` visibility
  - 3-tier active-memory reclaim (Safe 20% / Balanced 50% / Aggressive 80%)
  - Hard ceiling = `min(static_reserve, live_available, metal_cap)`
  - Custom tier for manual ceiling pinning
- **PoolingCache / BatchPoolingCache** for DeepSeek V4; **paged_ssd_cache v3** format — v0.3.9
- **Chunked prefill** (one chunk per scheduler step, decode-non-blocking) — v0.3.9rc1 / v0.3.9
- **VLM continuous batching + native TTS streaming** — v0.3.8 (2026-04-30)
- **DFlash Gemma 4** support (via dflash-mlx 0.1.7); **ParoQuant** pluggable quant loader — v0.3.9
- **Tool calling fixes**: thinking-model extractor name-matching; `tools: []` vs `tools: None`;
  Gemma 4 empty `tool_use.input` repair — v0.3.8.dev3 / v0.3.10
- **CLI / TUI**: `omlx launch <claude|codex|opencode|openclaw|pi|copilot|hermes>` agent picker — v0.3.9
- Evidence source: <https://github.com/jundot/omlx/releases>

### 0.1.2 vMLX (`jjang-ai/vmlx`)

- **Latest as of 2026-05-27**: v1.5.49 — 10 releases since v1.3.34 (2026-04-09);
  **major version jump 1.3.x → 1.5.x** signals broader engine maturation
- **DSV4 Flash native SWA+CSA/HCA composite prefix cache** with 256-token block indexing — v1.5.49 (2026-05-24)
- **Native Qwen3.6 MTP** honoring validated `vmlx_mtp_tuning.json` depth — v1.5.40 / v1.5.43
- **DSML streaming tool-call buffering** for DSV4 Flash — v1.5.41
- **MCP auto-discovery** from `mcp.json` / `mcp.yaml` + **multi-round tool chaining with structured `tool_calls`** — v1.5.45 (2026-05-20)
- **TurboQuant KV for hybrid SSM** attention layers; hybrid SSM cache telemetry separates live TurboQuant KV from stored q4/q8 — v1.5.40 / v1.5.43
- **DeepSeek-R1 reasoning parser** preserves implicit-reasoning contract (no stray `</think>` markers) — v1.5.42
- **Parser registry expansion**: MiniMax M2/M2.5/M2.7 restored; Mistral Small 4 VLM multimodal path restored; ZAYA XML tool streaming buffering; DSV4 / Hy3 / Gemma / Qwen all gated — v1.5.44 → v1.5.49
- **macOS DMG split**: Sequoia-compatible and Tahoe-native lanes; platform-specific MLX wheels — v1.5.44
- Evidence source: <https://github.com/jjang-ai/vmlx/releases>

### 0.1.3 owlmlx (本仓库 same 3 周新事件)

> Source: `runtime-capability-matrix.md` Stage 3.2 / 3.3 update + Campaign A-F docs

- **F-1** `speculative_execution_status` runtime-owned diagnostic surface + endpoint fixtures landed:
  5/5 fixture pass + 20 round-trips; `endpoint_self_promotion_eligible=true`;
  `graduates.endpoint_supported=false` / `graduates.any_method_supported=false` /
  `assistant_drafter` remains `experimental`. F-1 is endpoint eligibility evidence only,
  not a speculative-method promotion.
- **B-1a** Gemma 4-31B RuntimeKernel native warm p50 TTFT 1542.972 ms → 687.102 ms (**2.246×**),
  3 hits / 0 drops, RuntimeKernel restart completed
- **B-1b** cache-on N=20 no-regress passed: native cache-off + cache-on each N=20 completed
  with 20/20 warm hits, `failed_reclaim=0`, `failed_unload=0`, settle p50/p99 within threshold
- **B-1c §1** prerequisite met: current-Mac `interrupted_no_swap_rehearsal=passed`
  with `aggregate_measurement_duration_s=88888.531` (≈24.69h) across 3 clean native segments
- **B-1c §2** prompt-reset 子指标 (drops/drift/swap-boundary) 已清；首条 one-swap segment
  preserved functional subcriteria (drops/expirations/rejects 0, trim bypasses 3,
  `max_drift_bytes=171704320 < 209715200`, `swap_boundaries_clean=true`) 但仍 `blocked`，
  原因 `measurement_wall_clock_gap_free=false`（6 个 wall-clock gaps，max 7064.873s）
- **F-2** C0/C1 passed (n-gram suffix decoding 路径正确性 + serving cache prerequisites)；
  **C2 trim 路径被 mlx-lm #980 hybrid model trim 缺陷阻塞**（详见 `competitor-capability-matrix-20260527.md §4.3` upstream watch）
- **F-4 grammar-constrained structured-output lane landed**: the Qwen grammar-on
  lane (`json_schema_flat` / `enum_constrained` / `function_call_arguments` /
  `nested_object`) is `partial` as a feature-lane only; F-4 overall remains
  `experimental`, with Gemma and `thinking_tag_closed` residuals isolated in
  `structured-output-grammar-lane.md`

### 0.1.4 关键 surface-shift summary

| 关键能力轴 | 2026-04-16 baseline | 2026-05-27 refresh | 对 owlmlx 含义 |
|---|---|---|---|
| Memory governance（Apple Silicon） | owlmlx PR #649 watermark + settle barrier 为该轴**显著领先** | **oMLX v0.3.10-.12 已落 phys_footprint + adaptive throttle + 3-tier reclaim + hard ceiling**；vMLX 未在该轴做重大动作 | **owlmlx 领先距离 narrow**，但**设计哲学不同**：owlmlx = settle barrier verify unload reclaim contract；oMLX = live adaptive ceiling under pressure。仍是 owlmlx 强项，但不再是 "无对手" 维度 |
| Native MTP | 业界普遍缺；oMLX 提及但未跨 family | **oMLX 已跨 Qwen3.5/3.6 + Gemma 4 + DSV4**；**vMLX 已 native Qwen3.6 with tuning JSON** | **owlmlx F-1 endpoint surface 仍是 capability-honesty 独有的抽象**，但 owlmlx 在 "MTP 实装能力" 上已 lag；F-1 防止 method 仓促升级是 thesis 正确做法 |
| DeepSeek V4 / hybrid attention 模型 | oMLX/vMLX 均不直接支持；owlmlx 2026-05-06 measured comparison 也是 reject | **oMLX v0.3.9.dev1 full port**；**vMLX v1.5.49 SWA+CSA/HCA composite cache**；owlmlx Campaign D 已有 `.runtime-deepseek-experimental` technical-preview `partial` lane | **owlmlx 不再是单纯 clean pre-load reject**，但仍未达到 stock/default/full-port/composite-cache parity；gap 仍显著，且 technical-preview lane 不等于 measured reference parity |
| Continuous batching / chunked prefill | oMLX/vMLX 均有 CB 主线，未来路线已知 | **oMLX v0.3.9 chunked prefill 已落**；**vMLX TurboQuant KV for hybrid SSM 已落** | owlmlx **明确不追**（单 worker by design 已定），与 02-state-vs-market-gap.md §3.3 一致；gap 是 deliberate 不是 missing |
| Structured tool calling | 业界普遍未 invariance-validate | **vMLX v1.5.45 MCP auto-discovery + multi-round structured `tool_calls` 已落** | **owlmlx F-4 仍占据 "byte-for-byte invariance under spec/quant" 这一细分轴**，但 "structured tool calling 基础设施" 这条 broader 轴上 vMLX 已 ahead；F-4 thesis 应明确**只**主张 invariance 这条窄 axis，不主张 structured tool calling 广义 capability |
| 模型家族广度（parser registry / format） | 已知 owlmlx 选择窄；vMLX 已广 | **vMLX 再次扩展 Mistral Small 4 / MiniMax M2.x / Hy3 / ZAYA / DSV4 parser**；oMLX 加 DFlash Gemma 4 | owlmlx 选择窄是 deliberate boundary，未变；但**当 reviewer 评估 "broader productized family surface" 时，owlmlx 离 reference 更远** |
| Repeatability / capability honesty 纪律 | owlmlx 独有 | **未变** —— oMLX / vMLX release notes 未出现 promotion gate / experimental→supported 分级 / N≥20 byte-exact 测试承诺 | **owlmlx 在该轴 still 业界唯一**，是 thesis 核心 anchor |

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

> **2026-05-27 refresh read**：owlmlx 自身 label 不变（promotion gate 未触发新一级），但**相对 oMLX/vMLX 的 capability surface 距离 widened** —— 两侧在 6 周内各自 9 / 10 个 release。tier 结构性不变，但**压力上升**。详见 §0.1。

### owlmlx

Current honest label remains:

- `early_formal_runtime`
- `below reference-grade stability`

### Relative to oMLX (2026-05-27 refreshed read)

`owlmlx` is no longer a toy relative to `oMLX`.

Current honest posture:

- **one tier behind in runtime maturity** —— tier 未变；但 capability surface 距离扩大：
  - **Native MTP** 已覆盖 Qwen3.5/3.6 + Gemma 4 + DSV4（oMLX v0.3.9）—— owlmlx F-1 仍 experimental method；owlmlx 优势变为 "runtime-owned status surface + capability honesty 纪律" 而非 "MTP 实装能力本身"
  - **DeepSeek V4 Pro/Flash full port**（oMLX v0.3.9.dev1）—— owlmlx 2026-05-06 comparison baseline 是 clean reject；Campaign D 后已有 `.runtime-deepseek-experimental` technical-preview `partial` lane，但仍不是 stock/default/full-port parity，DSV4 路径上 gap 仍显著
  - **Memory governance overhaul**（oMLX v0.3.10-.12: phys_footprint + adaptive throttle + self-raising Metal wired limit + 3-tier active-memory reclaim + hard ceiling）—— **显著 narrow 此前 owlmlx PR #649 watermark + settle barrier 的领先距离**。两者设计哲学不同：owlmlx = settle barrier verify unload reclaim contract，oMLX = live adaptive ceiling under pressure。仍是 owlmlx 强项，但**不再是 "对手无显式压力分级" 的状态**
  - **Chunked prefill**（oMLX v0.3.9rc1/.9）已落 —— owlmlx 仍 by-design 不追
- closest gaps now concentrate in:
  - host-stable execution confidence（未变）
  - heavy-weight repeatability（未变）
  - **DeepSeek V4 / hybrid attention 模型家族支持**（新出现的硬差距）
  - deeper cache/scheduler closure（仍是问题；相对量减小因 owlmlx B-1a/b/§1 也在推进）
  - **Native MTP 实装本身**（新出现：owlmlx F-1 是 endpoint 抽象，oMLX 是跨 family 实装）

### Relative to vMLX (2026-05-27 refreshed read)

`owlmlx` is materially closer on substrate identity than before, but `vMLX` 自 2026-04-09 至 2026-05-27 共 **10 个 release** 且 **major version jump 1.3.x → 1.5.x** 信号引擎层广义成熟。

Current honest posture:

- **one to two tiers behind** —— tier 未变；但**向 2 tiers 一侧偏移**：
  - **DSV4 Flash native SWA+CSA/HCA composite prefix cache**（vMLX v1.5.49）已落 —— owlmlx 已有 technical-preview `partial` lane，但不具备 vMLX 这类 composite-cache/default-surface parity
  - **Native Qwen3.6 MTP** with validated tuning JSON（vMLX v1.5.40/.43）已落 —— owlmlx F-1 endpoint 仍 experimental method
  - **MCP auto-discovery + multi-round structured `tool_calls`**（vMLX v1.5.45）已落 —— 部分覆盖了 owlmlx F-4 雄心；但 **vMLX 未声明 byte-for-byte invariance**，所以 F-4 在 "invariance" 这条窄 axis 上仍有差异化窗口（详见 §0.1.4 关键 surface-shift summary）
  - **TurboQuant KV for hybrid SSM** attention layers（vMLX v1.5.40/.43）—— hybrid SSM 模型路径 vMLX 在量化 KV 维度新增 sophistication
  - **macOS DMG**: Sequoia + Tahoe-native lanes split + platform-specific MLX wheels —— packaging 进一步专业化
  - **Parser registry 广度扩展**：Mistral Small 4 / MiniMax M2.x / Hy3 / ZAYA / DSV4 / Qwen / Gemma 全 gated —— model family breadth 已显著超过 owlmlx
- biggest deficits concentrate in:
  - **scheduler / batching depth**（未变；TurboQuant KV for hybrid SSM 是新增 sophistication 信号）
  - **broader cache path maturity**（gap 扩大，composite cache + TurboQuant 都在推进）
  - **broader model family support**（新出现的硬差距 —— v1.5.x parser registry 比 v1.3.34 时显著更广）
  - packaging / runtime-product operationalization（未变；DMG split 是细化）

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

> **2026-05-27 refresh note**：上表 14 行的 tier verdict（ahead/close/behind/not-owned）结构性未变（boundary 未改），但下列行的 oMLX/vMLX 侧具体 capability 已发生 surface 变化，详见 §0.1：
>
> - **Continuous batching / deeper scheduler work**: oMLX 加 chunked prefill (v0.3.9) + VLM CB (v0.3.8)；vMLX TurboQuant KV for hybrid SSM 是新增 sophistication；owlmlx 仍 deliberate not-pursued
> - **Cache evidence / truth surfaces**: oMLX 加 PoolingCache + paged_ssd_cache v3 (v0.3.9)；vMLX SWA+CSA/HCA composite prefix cache (v1.5.49)；**owlmlx truth ledger 仍领先；practical cache maturity 仍落后但 owlmlx B-1a/b/§1 在收敛**
> - **Multi-model lifecycle governance**: oMLX 加 `omlx launch` agent picker TUI (v0.3.9)；vMLX parser registry 广义扩展 (v1.5.44 → .49)
> - **Heavy-weight repeatability**: 无公开变化信号 —— owlmlx 在该轴上 still 业界唯一在追"N≥20 byte-exact"的项目
> - **Memory governance**（隐含 14 行外的新轴）: oMLX v0.3.10-.12 新增 phys_footprint + adaptive throttle + 3-tier reclaim + hard ceiling；**未来若 14 行升级为 16 行，应单列 Memory Governance + Speculative Path Safety 两条新轴**
>
> 14 行 tier verdict 未在本 refresh 中触动 —— 改动需要 measured 复测（见 §0.1 boundary 与 §9 update rule）。

## 5. "Deleted / Not-Owned" Comparison

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

> **2026-05-27 refresh** (capability-surface only; measured-data floor 仍以 2026-05-06 为基线)

### What has changed since 2026-04-16

- **owlmlx side** (Stage 3.2 / 3.3 updates per `runtime-capability-matrix.md`):
  F-1 endpoint+fixtures landed (5/5 fixture pass) / B-1a Gemma 2.246× warm TTFT /
  B-1b cache-on N=20 no-regress passed / B-1c §1 prerequisite met (24.69h cumulative clean) /
  B-1c §2 prompt-reset 子指标 clean (drops/drift/swap-boundary 0) but **wall-clock continuity gap-blocked** /
  F-2 C0/C1 passed, C2 trim **blocked on mlx-lm #980 upstream** /
  F-4 grammar-constrained Qwen structured-output lane registered as feature-lane
  `partial` while F-4 overall remains `experimental`
- **oMLX side** (9 releases v0.3.5 → v0.3.12):
  native MTP across Qwen3.5/3.6 + Gemma 4 + DSV4 / DeepSeek V4 Pro/Flash full port /
  **memory governance overhaul** (phys_footprint + adaptive throttle + 3-tier reclaim + hard ceiling) /
  chunked prefill / DFlash Gemma 4 / ParoQuant / VLM continuous batching
- **vMLX side** (10 releases, major version jump v1.3.34 → v1.5.49):
  DSV4 Flash native SWA+CSA/HCA composite prefix cache /
  native Qwen3.6 MTP with tuning JSON / MCP auto-discovery + structured `tool_calls` /
  TurboQuant KV for hybrid SSM / DMG Sequoia/Tahoe-native split /
  parser registry breadth expansion

### Net read

- owlmlx **own progress is real and concentrates on the differentiating axes**
  (capability honesty / runtime-owned status / settle barrier reclaim verification /
  session KV cache TTFT evidence / spec path safety surface abstraction /
  structured output invariance plan/design)
- **but the capability-surface distance to oMLX and vMLX widened on the
  non-differentiating axes** (native MTP implementation / DSV4 model family /
  practical cache sophistication / chunked prefill / packaging)
- The tier verdict (one tier behind `oMLX`, one-to-two tiers behind `vMLX`)
  is **structurally unchanged but pressure has increased** —— oMLX/vMLX 6 周内的
  release 节奏比 owlmlx 同期更密；如果 owlmlx 不在 next quarter 内交付 F-4
  invariance 与 A campaign hard repeatability，**capability-surface gap 会侵蚀
  differentiating thesis 的解释力**

### Honest strategic read

- **closer than before on differentiating axes** (capability honesty + runtime-owned truth + invariance + settle barrier)
- **further behind on capability-surface area** (native MTP / DSV4 / model family breadth / packaging)
- **still not close enough to claim replacement** (tier 未变)
- **better than a toy** (未变)
- **still below reference-grade stability** (未变)
- **owlmlx 的 thesis 仍 valid**——capability honesty + runtime-owned truth + spec-path invariance 这三条在 oMLX/vMLX 2026-05-27 surface 上**仍无对应物**；但 thesis 的解释力依赖 F-4 落地 + B-1c §2 wall-clock gap 解开 + A campaign hard evidence 进一步加固，否则 capability-surface gap 持续扩大会让外部 reviewer 难以解读 owlmlx 的 "narrow but deep" 路线
- **首次出现的硬差距**：DeepSeek V4 / hybrid attention 模型家族 —— oMLX 已 full port + vMLX 已 composite cache，owlmlx 已通过 Campaign D 建立 technical-preview `partial` lane，但仍未达到 stock/default/full-port/composite-cache parity。后续应在 architect doc 里**明确声明 "technical_preview lane only" 是否足够，还是要主动追 default / composite-cache parity**

## 9. Update Rule

This document has two update layers since the 2026-05-27 refresh:

### 9.1 Capability-Surface Refresh (§0.1 / §3 / §4 refresh-notes / §8)

Trigger when **any** of:
1. `owlmlx` upgrades or downgrades its honest label (e.g., promotes a capability
   from `experimental` to `partial`, or downgrades a previously `supported` claim)
2. `owlmlx` materially re-enters or loses host-stable execution
3. one of the major comparison dimensions changes:
   - heavy-weight repeatability
   - scheduler/cache depth
   - shell/runtime boundary
   - **memory governance**（2026-05-27 新增，因 oMLX v0.3.10-.12 在该轴大幅 catch-up）
   - **speculative path safety / native MTP**（2026-05-27 新增，因 oMLX/vMLX 均跨 family 落地）
4. public `oMLX` or `vMLX` reference surfaces materially change（≥3 个 release / 单次 major version jump / 任一新增 capability 进入上述 dimension）

Capability-surface refresh **不要求** probe rerun，只需公开 release notes + 本仓库
runtime-capability-matrix.md 的最新 update。

### 9.2 Measured-Data Rerun (§0 Latest Live Evidence Addendum)

Trigger when **any** of:
1. capability-surface refresh 累积 ≥ 2 次后，外部 reviewer 有理由怀疑 measured 数字陈旧
2. owlmlx 跨过任一 §1a Promotion Gate（如 B-1c §2 wall-clock gap 解开 / F-4 invariance landed）
3. owlmlx 进入新 host / 新 macOS 大版本
4. 新模型家族进入 model release candidate 程序（如 owlmlx 主动追 DSV4，则需 measured 对比）

Measured rerun **要求**：runtime-probes venv 复检 + `scripts/runtime_comparative_evidence.py
run-measured-short-prompt` + 写入 `files/evidence/owlmlx/comparative-evidence/` 新 dated 目录。

### 9.3 Non-Reasons to Update

- 内部主观感受
- 路线图 promotional 压力
- 想"声明 parity" 的冲动
- 外部 release 数量震荡但本质 capability 不变（如纯 bugfix release）
