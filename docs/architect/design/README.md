# docs/architect/design/

> **Design-grade specs for plan-grade campaigns.**
> Downstream of plan-grade ([`../01-mainline-roadmap.md`](../01-mainline-roadmap.md)),
> upstream of code-grade (实际 harness 脚本 + bench 运行)。

---

## 这一层做什么

每个 design spec 把**一个 gate**（如 `B-1a`）从 plan-grade 的"目标 + 验收摘要"细化到可执行的口径：

- **Verification contract** —— 形式化的 pass/fail 字段、阈值、独立结论命名
- **Harness 改动点** —— 在现有 harness（`test_repeatability_campaign_harness.py` / `comparative_evidence_runner.py` / `repeatability_statistics.py` / `scripts/bench/eviction_soak.py`）上的**最小**扩展点；不新增 spec-as-code 模块
- **Evidence output paths** —— jsonl ledger 落盘的具体目录与文件名约定
- **Failure handling** —— gate 中途失败时的归因 / 重启 / 继续 / 上报口径
- **Out-of-scope 提醒** —— 显式列出本 gate **不**承担的责任（防 scope creep）

---

## 这一层**不**做什么

- ❌ 写代码（code-grade 是下一层，独立 round + PR）
- ❌ 一次性展开多个 gate 的 spec（**严格一次一个 gate**）
- ❌ 在前置 gate 通过前批量展开后续 gate 的实施细节
- ❌ 引用未被 runtime 消费的 spec-as-code 模块作为支撑（Stage 1 禁令）
- ❌ 把 design 文档当 source-of-truth contract（promote 需走 §1a Gate）

---

## 当前 specs

| Gate | Spec | 状态 | Plan-grade 来源 |
|---|---|---|---|
| **B-1a** | [`B-1a-spec.md`](B-1a-spec.md) | 已通过 · closeout 已落盘 | [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign B-1a |
| **B-1b** | [`B-1b-spec.md`](B-1b-spec.md) | 已通过 · native N=20 evidence 已落盘 | 同上 Campaign B-1b |
| **B-1c §1** | [`B-1c-section-1-spec.md`](B-1c-section-1-spec.md) | runner + graceful interruption + interrupted rehearsal aggregation 已落；2026-05-18 continuous attempt 因 host sleep / power gap 保持 blocked；2026-05-19 / 2026-05-20 / 2026-05-21 三段 clean native segment 聚合 `20260521T064658Z` 已达到 `interrupted_no_swap_rehearsal=passed` / `current_mac_section_1_prerequisite_met=true`；continuous 24h `no_swap_soak_stability` 仍未声明 | 同上 Campaign B-1c §1 |
| **B-1c §2** | [`B-1c-section-2-spec.md`](B-1c-section-2-spec.md) | design-grade spec + fake/schema runner 已落；native §2 runner 已落；Qwen token-boundary drop 已由 boundary-safe prompt 修正；prompt-reset policy 已有 gap-free one-swap aggregate input `20260601T025321Z`（drop/expiration/reject=0、trim bypass=3、drift within budget、swap boundary clean）；fast forced-swap canaries `20260601T125751Z` / `20260601T134131Z` 证明 5min cadence 下 swap boundaries 仍 clean。最新 canary 全部 measurement row 用 `cache_object_nbytes`，Gemma raw drift=751370240 bytes、resident cache=1054965760 bytes、unaccounted=0；raw-RSS false-fail 已收敛为 `cache_object_resident_accounted` 功能漂移门，剩余 blocker 是 aggregate / policy，后续必须保持 5min swap cadence，不能继续被动凑 4h 单次切换 | 同上 Campaign B-1c §2 |
| **B-2** | [`B-2-mainstream-prefix-cache-compatibility-spec.md`](B-2-mainstream-prefix-cache-compatibility-spec.md) | design-grade spec 已落；B-2.1 read-only prefix-candidate classifier 已落；B-2.2 real cache metadata plumbing 已落，只在 backend detail 存在时写 OpenAI/Anthropic cache usage；仍不自动复用 cache handle，不做 `supported` 晋级 | [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign B-2 |
| **Wave H · H1** | code-grade landed: `server_routes_openai.py` | 已完成 · OpenAI/Anthropic compat routes 拆出 | 同上 Wave H |

## 并行 Campaign Specs

| Campaign | Spec | 状态 | Plan-grade 来源 |
|---|---|---|---|
| **D1** | [`D1-spec.md`](D1-spec.md) | passed under adopted `messages` prompt policy; raw prompt remains diagnostic failure | [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign D |
| **D2** | [`D2-spec.md`](D2-spec.md) | p1/p2/p4 × 128/512 metrics ladder passed | [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign D |
| **D3** | [`D3-spec.md`](D3-spec.md) | inspection passed; `missingReason=mtp_weights_absent_or_stripped` | [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign D |
| **D4** | [`D4-spec.md`](D4-spec.md) | clean pre-load reject passed; consumes D3 missing reason; no load attempted | [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign D |
| **F-1** | [`F-1-spec.md`](F-1-spec.md) | code-grade F-1.2 + F-1.3 landed; endpoint + kernel observe APIs + fixture evidence `20260525T142617Z`; no method promotion | [`../06-campaign-F1-plan.md`](../06-campaign-F1-plan.md) (in turn from [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign F · F1) |
| **F-2** | [`F-2-ngram-suffix-spec.md`](F-2-ngram-suffix-spec.md) | C0/C1 passed; C2 serving integration paused on mlx-lm hybrid trim | [`../07-perf-optimization-proposal-20260526.md`](../07-perf-optimization-proposal-20260526.md) direction C |
| **F-3** | [`F-3-resident-mtp-spec.md`](F-3-resident-mtp-spec.md) | design-grade draft · **BLOCKED on `mlx-lm #980`** (hybrid-model trim); unblock path = owlmlx non-trimmable resident feasibility probe (§2.2). Gemma4 / `mlx-vlm` line only; produces resident pure-decode A/B evidence, promotes nothing | [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign F · F-3 (line 335) |
| **B prefill chunking** | [`B-prefill-chunking-spec.md`](B-prefill-chunking-spec.md) | configuration/progress surfaces supported; wall-clock acceleration not promised; cross-chunk consistency diagnostic-only | [`../07-perf-optimization-proposal-20260526.md`](../07-perf-optimization-proposal-20260526.md) direction B |
| **F-4** | [`F-4-structured-output-invariance-spec.md`](F-4-structured-output-invariance-spec.md) | design-grade draft; validator + smoke matrix next; no code-grade implementation yet | [`../08-campaign-F4-structured-output-invariance-plan.md`](../08-campaign-F4-structured-output-invariance-plan.md) |

**节奏纪律**：design spec **一次一个**，per round 落盘 + review；不允许批量预先撰写未启动的 gate。

---

## 与 plan-grade / source-of-truth 的关系

```
plan-grade (../*.md)                ← 战略 / 路线图 / 12 维框架 / 风险
    ↓ derive (gate-by-gate)
design-grade (./*.md)               ← 本目录：单 gate 的可执行口径
    ↓ implement (code-grade)
runtime code + harness scripts      ← bench 脚本 / 测试 / evidence runner
    ↓ measurement output
files/evidence/owlmlx/bench/...     ← jsonl ledger
    ↓ promote (经 §1a Gate)
docs/source-of-truth/               ← runtime evidence + contract truth
```

design-grade **不**直接被 runtime 代码 import；它指导 code-grade 写实际的 harness 脚本。harness 脚本产生 evidence；evidence 经 §1a Gate 才 promote 到 source-of-truth。

---

## 改动纪律

继承 [`../README.md`](../README.md) 的所有纪律，并额外：

- **每个 spec 一个 commit**（docs-only，不混入 runtime code 与 evidence）
- 每个 spec **写明前置依赖与后置解锁**（哪个 gate 通过了才能启动我；我通过了能解锁哪些）
- spec 中**字段命名**与 plan-grade 中的命名严格对齐（如 `no_swap_soak_stability` / `soak_plus_swap_stability` 不能换名）
- spec 落盘后 code-grade 实施前，需要架构师 review + 用户签字两道
