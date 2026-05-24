# 05 · 对齐审计 + 架构 / 功能 / 方向补充

> **Grade**: plan-grade（与本目录其他文件同 grade · 不入 `docs/source-of-truth/master-outline.md`）
> **Updated**: 2026-05-23（首次落盘 + Wave G 第一刀 8 commit 后回填 resolved SHAs）
> **目的**: 对齐 (a) owlmlx 代码现实、(b) `docs/source-of-truth/` 当前文档断言、(c) `docs/architect/` plan-grade 路线，三层之间的差异，并补充架构师视角的现状架构、功能视图、12+ 月方向。

## Wave G 落地进度（2026-05-23 同日批量）

| Commit | 范围 | Resolved 审计项 |
|---|---|---|
| `eff8b20d` | 落盘本文 + architect/README.md 索引更新 | （奠基） |
| `5c98776b` | ARCHITECTURE-TRUTH §2.2 / §2.3 模块/测试/文档盘点 | #1 #2 #3 #12 |
| `e3b6dfad` | product-definition §5.3 vMLX 边界 + §11 internal-depth posture | #5 #6 #7 |
| `9601328d` | master-outline §8 dominant question + §5 Wave G-5 banner | #8 #10（partial）#17 #20 |
| `4ffdb267` | runtime-capability-matrix Wave H · H1 行 + B-1c §1 footnote | #11 #14 |
| `ca6491d8` | README speculative posture + Development status | #15 #18 |
| `d98203a1` | AGENTS.md read order + non-negotiable truth | #19 |

**14 项 resolved · 4 项 open · 5 项 healthy 维持**。详见 §4 各小节。

下次批量结算的目标候选：
- #4（ARCHITECTURE-TRUTH §7.3 truth-substrate identity 框架重写 · 不是简单数字刷新）
- #9 + #10 full + #13（Wave G-4：phase45 文档归档 / 命名约束 / 迁移路径）
- #16（session-kv-cache-experimental.md 与 capability matrix 同步审计）

---

## §1. 用途与边界

本文是**审计 + 补充**，不是契约：

- **不**替代 `ARCHITECTURE-TRUTH.md`、`product-definition.md`、`runtime-capability-matrix.md` 中任何 supported / partial / experimental 标签
- **不**晋级任何能力（promotion 仍走 §1a Gate）
- **不**直接被 runtime 代码或 harness 消费
- **作用**：把代码 5+ 周的真实演进与 source-of-truth 文档之间的漂移显式列出，为后续 Wave G governance refresh 准备工作单
- **节奏**：每次 Campaign wave 完成时 architect 反推刷新一次本文；与其他 architect/ 文件同 grade

本文的"代码现实"基于 2026-05-23 工作树扫描；与 `01-mainline-roadmap.md` 中的 wave 状态描述独立产生（防止 confirmation bias）。

---

## §2. 代码现实快照（2026-05-23）

### 2.1 模块清单

| 范畴 | 数量 | 说明 |
|---|---:|---|
| `owlmlx/*.py` 顶层模块 | 36 | 不含 runtime/ 子目录 |
| `owlmlx/runtime/*.py` 模块 | 17 | 含 `__init__.py` |
| 总 Python 模块（owlmlx 域） | 53 | |
| 总 LOC（owlmlx + owlmlx/runtime） | 29,730 | `wc -l owlmlx/runtime/*.py owlmlx/*.py` |

### 2.2 测试规模

| 范畴 | 数量 |
|---|---:|
| `tests/test_*.py` 文件 | 77 |
| `def test_*` 函数（recursive grep） | 919 |

### 2.3 HTTP 路由表面（Wave H · H1 之后）

| 模块 | 路由数 | 路由集合（按类） |
|---|---:|---|
| `owlmlx/runtime/server.py` | 42 | core control (8) · runtime status (24) · test-runs (5) · monitor (5) |
| `owlmlx/runtime/server_routes_openai.py` | 5 | `/v1/chat/completions` · `/v1/completions` · `/v1/messages` · `/v1/messages/count_tokens` · `/v1/openai/models` |
| 合计 | 47 | OpenAI/Anthropic 兼容层已隔离至独立模块 |

**未拆分（Wave H · H2/H3 待启）**：22 个 `/v1/runtime/*` 状态端点 + 5 个 `/v1/runtime/test-runs*` admin 端点 + 5 个 `/v1/runtime/monitor*` 端点 + 8 个核心控制 (`/v1/load` / `/v1/generate[/stream]` / `/v1/unload` / `/v1/models` / `/v1/runtime/restart` / `/healthz` / `/metrics`)。

### 2.4 顶部 10 个模块（按 LOC）

| 模块 | LOC | 性质 |
|---|---:|---|
| `runtime/mlx_lm_subprocess_backend.py` | 2541 | subprocess backend（生产路径） |
| `runtime/server.py` | 2013 | HTTP 主入口 + 路由 + 中间件 + admin 端点 |
| `runtime/kernel.py` | 1694 | RuntimeKernel：load/generate/unload/restart/settle |
| `runtime_monitor_test_console.py` | 1267 | 内部测试台（OwlOps 消费） |
| `runtime/mlx_native_backend.py` | 1215 | native backend（session-scope opt-in only） |
| `comparative_evidence_runner.py` | 1130 | comparative bench 主驱动 |
| `serving.py` | 1009 | GenerationGate + pre-gate hook + admission seam |
| `runtime/mlx_lm_runner.py` | 896 | mlx_lm child process runner |
| `runtime/serving_hardening.py` | 857 | hardening contract（recovery / abort / restart） |
| `runtime/server_routes_openai.py` | 829 | Wave H · H1 已拆 |

---

## §3. 文档现实快照

### 3.1 `docs/source-of-truth/` 总览

| 维度 | 数量 |
|---|---:|
| 总 .md 文件 | 208 |
| 非 `phase45-*` | 103 |
| `phase45-*` 前缀文件 | 105 |
| `master-outline.md §5` 列入索引的文件数 | 145 |
| 索引中 `phase45-*` 文件 | 79 |

### 3.2 `phase45-*` 递归命名清单（节选）

`master-outline.md §5 #114–#128`、`stream-backend-terminal-notice-leading-discriminator-marker-...-exactness.md` 路径出现 **4+ 层 hyphen-嵌套**：

```
phase45-stream-backend-terminal-notice-leading-discriminator-marker-
  earlier-runtime-owned-boundary-
  earlier-earlier-boundary-
  exactness.md
```

15 份此类文件在源代码层已通过 Stage 1 (2026-05-11) `self-banned-modules.yml` CI 禁令清除（`_exactness.py` / `_carrier.py` / `_marker.py` 等），但**doc-as-spec** 形式仍在 source-of-truth 内驻留——这是 `R2` 风险的当前 materialization。

### 3.3 `docs/architect/` 现状

| 文件 | 状态 |
|---|---|
| `README.md` | gatekeeper · plan-grade 边界已立 |
| `01-mainline-roadmap.md` | 战略主线 · 含 6 campaign + Wave G/H · 维护入口 |
| `02-state-vs-market-gap.md` | 外部对照 |
| `03-real-accomplishments.md` | 已完成事实 · 含四主证据 |
| `04-architecture-canvas.md` | 架构画布（mermaid） |
| `05-alignment-audit.md` | 本文（新增） |
| `design/B-1a-spec.md` | passed |
| `design/B-1b-spec.md` | passed |
| `design/B-1c-section-1-spec.md` | interrupted_no_swap_rehearsal=passed (2026-05-21) |
| `design/B-1c-section-2-spec.md` | 4h boundary-safe 跑漂 352MB > 200MB budget |
| `design/D1-spec.md` | passed under adopted `messages` prompt policy |
| `design/D2-spec.md` | p1/p2/p4 × 128/512 ladder passed |
| `design/D3-spec.md` | inspection passed · `missingReason=mtp_weights_absent_or_stripped` |
| `design/D4-spec.md` | clean pre-load reject passed |

### 3.4 README.md / AGENTS.md 现状

| 文件 | 关键事实 |
|---|---|
| `README.md` | 已含 B-1a/B-1b 数据；已含 8066 端口；已含 vMLX 边界（部分）；speculative posture 当前写"not in scope"，与 `gemma4_mtp_drafter.py` / D3+D4 矛盾 |
| `AGENTS.md` | Read order 16 条未含 `docs/architect/`；"Non-Negotiable Project Truth" 未含 internal replacement-grade depth 战略转向 |

---

## §4. 对齐差读（Misalignment Ledger）

四级 severity：**critical**（影响外部对 owlmlx 真实性的判断）/ **high**（影响内部决策路径）/ **medium**（影响新成员上手准确性）/ **low**（命名 / 索引整洁度）。

### 4.1 critical — 模块 / 测试规模断言陈旧

| # | 文档位置 | 状态 |
|---|---|---|
| 1 | `ARCHITECTURE-TRUTH.md §2.2` "19 个 Python 模块 / 357 tests" → 53 / 919 | **resolved by `5c98776b` · 2026-05-23** |
| 2 | `ARCHITECTURE-TRUTH.md §2.2 模块表` 最高 `serving.py ~480`、`runtime/server.py ~80` → 2013/2541/1694/1215 等 13 个超 500 LOC 模块 | **resolved by `5c98776b` · 2026-05-23** |
| 3 | `ARCHITECTURE-TRUTH.md §2.3` "29 个 source-of-truth 文档" → 208 份 | **resolved by `5c98776b` · 2026-05-23** |
| 4 | `ARCHITECTURE-TRUTH.md §7.3` "11 truth modules / 357 tests / 7 platform consumers ✓" · identity 框架（truth substrate pillar）不再占主体 | **open** · 需要 §3 / §7 框架级重写，不是简单数字刷新；下次架构师 round 处理 |

→ 后果：任何外部读者按 `ARCHITECTURE-TRUTH.md` 接 owlmlx，对其规模、复杂度、能力梯度的第一印象与代码现实差 2–25×。

### 4.2 critical — Identity / 战略定位陈旧

| # | 文档位置 | 状态 |
|---|---|---|
| 5 | `product-definition.md §1` 未含 "internal replacement-grade depth" 战略身份精炼 | **resolved by `e3b6dfad` · 2026-05-23**（新增 §11 addendum） |
| 6 | `product-definition.md §5.3 vMLX` （审计原写 §5.2 误 · 实际 §5.2 是 oMLX · §5.3 才是 vMLX）边界陈述未含 vMLX 全栈化现实 | **resolved by `e3b6dfad` · 2026-05-23**（§5.3 重写 · 含 2026-05 现实校正） |
| 7 | `product-definition.md` 无 release channel split 章节（owlmlx engineering ≠ OwlCoda consumer readiness） | **resolved by `e3b6dfad` · 2026-05-23**（§11.3 含 OwlCoda 边界 + commit `a21a0a2c` 引用） |
| 8 | `master-outline.md §8` "dominant gap = `memory_discipline_baseline_missing`" 已被 PR #649 + B-1a/b/c §1 闭合 | **resolved by `9601328d` · 2026-05-23**（§8 重置为双 dominant gap：`session_kv_drift_under_swap_workload` + `native_backend_promote_path_g2_closure`） |

→ 后果：上游契约文档与 architect 战略主线之间存在 5+ 周漂移；外部读者依据 source-of-truth 接 owlmlx 会落到错误的"替代 oMLX"叙事，而非内部 replacement-grade depth 叙事。

### 4.3 critical — Phase45 递归命名扩散

| # | 文档位置 | 状态 |
|---|---|---|
| 9 | 105 份 `phase45-*` 文件（含 15 份 4+ 层 hyphen 嵌套递归命名）在 `docs/source-of-truth/` 内驻留 | **open** · Wave G-4 独立 round · 涉及文件归档 / 命名约束 / 迁移路径，需用户参与决策；本次 Wave G-5 仅做 banner 标记不动文件 |
| 10 | `master-outline.md §5 #50–#85 + #87–#128` 78 份 `phase45-*` 在 canonical reading list 内编号 | **partial · resolved by `9601328d` · 2026-05-23**（Wave G-5 banner 明确"脱离 canonical reading sequence"；canonical 现为 #1–49 + #86 + #129–145 共 67 项 · 全部非 phase45）· 完整归档仍待 Wave G-4 |

→ 后果：源代码层已禁的反模式，文档层仍在生长；Stage 1 治理收益部分被反向稀释。

### 4.4 high — Wave H · H1 已落但未在 source-of-truth 登记

| # | 文档位置 | 状态 |
|---|---|---|
| 11 | `runtime-capability-matrix.md` 无 Wave H · H1 行 | **resolved by `4ffdb267` · 2026-05-23**（§4 新增 "HTTP routes modular split (Wave H · H1)" 行 · supported · 含 H2/H3 deferral 说明） |
| 12 | `ARCHITECTURE-TRUTH.md §2.2 模块表` 无 `server_routes_openai.py` | **resolved by `5c98776b` · 2026-05-23**（Top-15 模块表含 829 LOC · 新增 "HTTP routes 拆分（Wave H · H1）" 主战场段落） |
| 13 | `master-outline.md §5` 无 Wave H 拆分相关条目 | **open** · Wave H 是 architect 路线条目，按 plan-grade / source-of-truth 边界纪律不入 master-outline §5；如需登记应在 capability matrix（已通过 #11 resolved）或 ARCHITECTURE-TRUTH §2.2（已通过 #12 resolved）；本条作为"已通过其他路径覆盖"标记 |

→ 后果：2026-05-17 之后任何对 server.py 行数 / 模块边界的契约引用都过时。

### 4.5 high — Session KV cache 进度断点不一致

| # | 文档位置 | 状态 |
|---|---|---|
| 14 | `runtime-capability-matrix.md` 第 118 行 session KV cache 行未含 B-1c §1 interrupted prerequisite met + §2 4h 段 drift triage 状态 | **resolved by `4ffdb267` · 2026-05-23**（行内新增 `20260521T064658Z` `interrupted_no_swap_rehearsal=passed` + `20260522T164506Z` `max_drift_bytes=352321536 > 209715200` · 仍 experimental） |
| 15 | `README.md` "Development status" 信息密度落后实际进展 1 周 | **resolved by `ca6491d8` · 2026-05-23**（B-1c §1 passed + §2 drift triage 句加入 · Wave H · H1 提及） |
| 16 | `session-kv-cache-experimental.md` 与 capability matrix 同步状态未审计 | **open** · 与 §VI G2 闭合后由 architect 反推刷新一并处理；本轮不在 §8 工作单内 |

→ 后果：外部读者无法看到 §1 当前-Mac 路径已达 prerequisite 这一关键事实；§VI 4-gate G2 进度被低估。

### 4.6 high — `master-outline.md §8` Dominant Question 已过时

| # | 文档位置 | 状态 |
|---|---|---|
| 17 | `master-outline.md §8` "dominant gap = `memory_discipline_baseline_missing`" 已被 PR #649 + B-1a/b/c §1 闭合 | **resolved by `9601328d` · 2026-05-23**（§8 重置为双 dominant gap + 双 Track 并行执行路径 + 历史口径作为 closing evidence 列出） |

→ 后果：源代码层正在向"下一刀做归因"的方向走，但顶层 outline 仍指向"先建 baseline"。

### 4.7 medium — README speculative posture 与代码矛盾

| # | 文档位置 | 状态 |
|---|---|---|
| 18 | `README.md` "What ships now" 表把 speculative 与 continuous batching 等并列"not in scope"，与 `gemma4_mtp_drafter.py` + `mlx_vlm_mtp_runner.py` + D3+D4 否定面契约矛盾 | **resolved by `ca6491d8` · 2026-05-23**（拆出独立行 "Speculative decoding (`gemma4_mtp_drafter.py` · `mlx_vlm_mtp_runner.py`): probe surface only · not in serving path" · 引用 Campaign F + D3+D4 negative-face contract） |

→ 后果：speculative 在 README 看是"不会做"，在 `01-mainline-roadmap.md §V Campaign F` 是"第 6 子战役"，在代码是"probe 已在"——三层矛盾。

### 4.8 medium — AGENTS.md Read Order 不含 `docs/architect/`

| # | 文档位置 | 状态 |
|---|---|---|
| 19 | `AGENTS.md` Read Order 16 条直接从 README → master-outline → source-of-truth；plan-grade `docs/architect/` 不出现在导航 | **resolved by `d98203a1` · 2026-05-23**（Read Order 顶部新增 item 0 = `docs/architect/README.md` plan-grade 入口 · Non-Negotiable Project Truth 新增 §11 internal-depth posture + OwlCoda 边界引用） |

→ 后果：新成员/LLM-assisted PR 无法发现 plan-grade 层；可能将 architect 视角的讨论误送 source-of-truth。

### 4.9 low — `master-outline.md §5` 索引膨胀

| # | 文档位置 | 状态 |
|---|---|---|
| 20 | `master-outline.md §5` 145 个文件编号混杂（79 phase45-* + runtime12-* + stabilization*-* 等） | **resolved by `9601328d` · 2026-05-23**（Wave G-5 banner 明确 canonical reading sequence = #1–49 + #86 + #129–145 共 67 项 · phase45-* 78 项脱离 canonical 但仍在 numbered list 内保持向后兼容；完整归档仍待 Wave G-4） |

→ 后果：canonical reading list 已不可阅读；新成员无法按编号 1–145 顺序消化。

### 4.10 healthy — 这些层目前对齐良好（不要错动）

| # | 内容 | 状态 |
|---|---|---|
| 21 | `runtime-capability-matrix.md` Stage 1/Stage 2 alignment | 准确 · 2026-05-12 c1 |
| 22 | `runtime-capability-matrix.md` Memory Watermark / Settle Barrier / `pre_load_check` rows | 准确 · PR #649 已落 |
| 23 | `native-mlx-backend-capability-matrix.md §1a Promotion Gate` | 准确 · 提供四条 promotion 拒绝硬规则 |
| 24 | `README.md` "What this is" 与 `01-mainline-roadmap.md §IV` 主线声明 | 准确 · 已含 memory-discipline-first + single worker by design + 8066 port |
| 25 | B-1a/B-1b 验证证据链 → capability matrix → README 反向引用路径 | 端到端一致 |

---

## §5. 架构补充（既有 ARCHITECTURE-TRUTH §3 之外）

`ARCHITECTURE-TRUTH.md §3` 现在说"Layer 2: Core runtime (load, serve, memory, switch, introspect) ← Runtime-3 minimal kernel 存在"。这条**没错但已不完整**。Layer 2 实际已分化为 7 个子系统：

### 5.1 Layer 2 实际的 7 个子系统

```
                    ┌──────────────────────────────────────┐
                    │  HTTP surface (server.py + routes_*) │
                    │  47 endpoints                        │
                    └──────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────────┐
                    │   Lifecycle kernel (kernel.py)      │
                    │   load · generate · unload          │
                    │   restart · settle barrier          │
                    └─────────────────────────────────────┘
       ┌──────────┬──────────┴──────────┬──────────┬──────────┐
       ▼          ▼                     ▼          ▼          ▼
  ┌─────────┐ ┌────────────┐  ┌───────────────┐ ┌──────┐ ┌──────────┐
  │ Process │ │  Memory    │  │  Admission &  │ │Multi │ │ Status & │
  │boundary │ │ discipline │  │     cache     │ │model │ │provenance│
  ├─────────┤ ├────────────┤  ├───────────────┤ ├──────┤ ├──────────┤
  │subprocess│ │watermark   │  │scheduler_     │ │inven │ │runtime_  │
  │backend  │ │budget      │  │  admission    │ │tory  │ │  health  │
  │native   │ │pressure_*  │  │model_load_    │ │linea │ │orchestra │
  │ backend │ │host_       │  │  admission    │ │ge    │ │tion_     │
  │mlx_lm_  │ │  pressure  │  │nonresident_   │ │profi │ │  status  │
  │ runner  │ │settle_     │  │ admission_pol │ │le    │ │recovery_ │
  │mlx_vlm_ │ │  barrier_  │  │cache_manager  │ │relea │ │supervisor│
  │ mtp_run │ │   event    │  │cache_truth    │ │se_   │ │comparat. │
  │         │ │            │  │session_kv_    │ │candi │ │  evid_*  │
  │         │ │            │  │  cache        │ │date  │ │monitor_  │
  │         │ │            │  │cache_resid_   │ │_*    │ │ test_    │
  │         │ │            │  │  tracker      │ │      │ │  console │
  └─────────┘ └────────────┘  └───────────────┘ └──────┘ └──────────┘
       │            │                  │            │           │
       └────────────┴──────────┬───────┴────────────┴───────────┘
                               ▼
                  ┌────────────────────────┐
                  │  MLX substrate (Layer 1)│
                  │  (Apple, not owlmlx)    │
                  └────────────────────────┘
```

| 子系统 | 主要模块 | LOC 量级 | 状态 |
|---|---|---:|---|
| **HTTP surface** | `server.py` + `server_routes_openai.py` | 2842 | supported (核心) · Wave H 拆分中 |
| **Lifecycle kernel** | `runtime/kernel.py` | 1694 | supported |
| **Process boundary** | `subprocess_backend.py` + `native_backend.py` + `mlx_lm_runner.py` + `mlx_vlm_mtp_runner.py` | ~5500 | subprocess: supported · native: experimental |
| **Memory discipline** | `memory_watermark.py` + `memory_budget.py` + `memory_pressure_*.py` + `host_pressure.py` + `settle_barrier_event.py` + `memory_actuator.py` | ~2800 | supported（PR #649 已对齐） |
| **Admission & cache** | `scheduler_admission.py` + `model_load_admission.py` + `nonresident_model_admission_policy.py` + `cache_manager.py` + `cache_truth.py` + `session_kv_cache.py` + `cache_residency_tracker.py` + `cache_scheduler_status.py` | ~3500 | supported (admission) · experimental (session KV cache) |
| **Multi-model lifecycle** | `model_inventory.py` + `model_lineage.py` + `model_release_candidate_*.py` (3) + `model_residency_policy.py` + `model_profile.py` + `quantization_metadata.py` + `nonresident_loadability_lineage.py` | ~2500 | supported (pin/TTL/eviction history) · partial (governance observation) |
| **Status & provenance** | `runtime_health.py` + `orchestration_status.py` + `runtime_model_visibility.py` + `runtime_monitor_test_console.py` + `recovery_supervisor.py` + `comparative_evidence_*.py` (4) + `serving_status.py` | ~4000 | supported（请求生命周期维度） · partial（artifact 维度） |

**ARCHITECTURE-TRUTH §3 应补：** Layer 2 不再是"一个 minimal kernel"，是 7 个子系统的耦合体；4-layer 模型作为**外部叙事**仍正确，但内部架构师视角必须看到 7 子系统。

### 5.2 子系统之间的契约边界

- **HTTP → Lifecycle kernel**：所有 routes 经 `RuntimeKernel` 实例（不直接调用 backend）
- **Lifecycle kernel → Process boundary**：通过 `RuntimeBackend` Protocol（`backends.py`）；subprocess 与 native 互为 fallback / experimental
- **Lifecycle kernel → Memory discipline**：每条 load 路径经 `pre_load_check` + `MemoryWatermark`；每条 unload 路径经 `settle_barrier_event`
- **Lifecycle kernel → Admission & cache**：通过 `scheduler_admission` 与 `cache_manager`；`session_kv_cache` 仅与 native backend 双向耦合（这是 native backend 当前最强的存在理由）
- **Lifecycle kernel ↔ Multi-model lifecycle**：`model_inventory` 既被 kernel 写入也被 HTTP 读出
- **Status & provenance** 是单向**只读 fan-out**：从 kernel 状态生成；不反向影响决策

### 5.3 native backend 的"4-gate 阶梯"位置（架构层）

`§VI` 给出的 4-gate 在架构上对应"native backend 从 in-process opt-in adapter 升级为 fallback-eligible primary backend"的路径：

| Gate | 架构层含义 | 当前进度（事实层） |
|---|---|---|
| G1 · Cache Parity | session KV cache 语义 + 非 cache 路径字节等价 | **B-1a 通过** = G1 done |
| G2 · Reclaim Verified | settle barrier 在 native 路径上 hardened | B-1b cache-on no-regress 通过 + B-1c §1 interrupted 通过 → 约 60% · §2 漂 352MB 是 G2 真正的工作面 |
| G3 · Structured-Output Invariance | tool / JSON / thinking-tag 在 native 上字节等价 + 正交矩阵 ≥20 case | 未启动（Campaign F-4/5） |
| G4 · Speculative Path Landing | spec 在 native 上稳定 + F4 矩阵未破坏 + DS4 native MTP | 未启动；**D3+D4 已闭合"unsafe 否定面"**，是 G4 的输入而非达成 |

**架构师注**：G3 不依赖 G2 完成；可以在 §2 解决过程中并行起 Campaign F-1（runtime-owned `speculative_execution_status` 状态契约）。当前 sequence 把 F 整体推到 G2 之后是节奏选择，不是依赖。

---

## §6. 功能视图（不是 README "What ships now" 的扁平版）

README 的能力表是面向用户的"能不能用"，本节是面向架构师的"由什么子系统支撑、契约边界在哪里"。

| Functional 能力 | 入口 surface | 子系统支撑 | 实际状态 | 注意 |
|---|---|---|---|---|
| OpenAI 兼容推理 | `/v1/chat/completions` · `/v1/completions` · `/v1/embeddings` | HTTP (routes_openai) → Lifecycle kernel → Subprocess backend | supported | 5 条路由已 Wave H · H1 隔离；SSE [DONE] 终结协议稳定 |
| Anthropic 兼容推理 | `/v1/messages[/count_tokens]` · `/v1/openai/models` | 同上（routes_openai） | supported | runtime-native message path（不再 server-only flattening） |
| 核心 lifecycle 控制 | `/v1/load` · `/v1/generate[/stream]` · `/v1/unload` · `/v1/runtime/restart` | HTTP (server.py) → kernel | supported | 仍在 server.py · Wave H 不动 |
| 健康 / 元信息 | `/healthz` · `/metrics` · `/v1/models` | HTTP (server.py) → kernel | supported | healthz 是 liveness 契约（Stabilization-1 frozen） |
| Memory watermark 可视 | `/v1/runtime/memory-watermark` | Memory discipline → HTTP | supported | PR #649 alignment |
| Reclaim barrier 事件流 | `/v1/runtime/reclaim-barrier-event[/stats]` | Memory discipline → HTTP | supported | URL 保留为兼容历史；`contract.surface` 已迁到 settle barrier 词汇 |
| Admission 决策 read-only | `/v1/runtime/model-load-admission` · `/v1/runtime/nonresident-model-admission-policy` · `/v1/runtime/scheduler-admission-contract` | Admission & cache → HTTP | supported | 4-outcome 决策（admit_and_load / defer / reject / unknown） |
| Multi-model 治理 | `/v1/runtime/model-release-candidates[/history]` · `/v1/runtime/model-residency-policy` · `/v1/runtime/model-visibility` | Multi-model lifecycle → HTTP | supported (3) · partial (governance observation) | pin/TTL/eviction history 已固化 |
| Orchestration 层评估 | `/v1/runtime/orchestration-status` | Status & provenance → HTTP | supported | 6 子层（admission / generation gate / stream hold / residency / pressure / recovery）每层有独立 `partial` / `insufficient_signal` 标 |
| Recovery 契约 | `/v1/runtime/recovery-supervisor-contract` | Status & provenance → HTTP | supported | 不声称自动 recovery loop |
| Comparative evidence | `/v1/runtime/comparative-evidence[/history]` | Status & provenance → HTTP | supported | OwlOps live consumer |
| Runtime monitor 内部测试台 | `/v1/runtime/monitor/{snapshot,history,events}` · `/v1/runtime/test-runs*` | Status & provenance → HTTP | supported | OwlOps 27 行 ledger live |
| Session KV cache（实验） | `OWLMLX_SESSION_CACHE_ENABLED=1` + `X-Owlmlx-Session-Id` | Admission & cache + Native backend | experimental | 默认 off · native only · append-only reuse · §VI G2 在归因 |
| Native backend（实验） | `OWLMLX_SESSION_CACHE_ENABLED=1` 触发 | Process boundary | experimental | 仅在 session-scope 显式 opt-in 时启用；session KV cache 的物理承载 |
| MTP 探针（实验） | `gemma4_mtp_drafter.py` · `mlx_vlm_mtp_runner.py` | Process boundary | scaffold-only | F-1 未起 · D3 已闭合 "weights absent → reject" 否定面 |
| Test runs admin | `/v1/runtime/test-runs/{run_id}[/abort]` | Status & provenance | supported | OwlOps consumption · 内部 |

**新增视角**：把 README "what ships now" 的 11 行升级为 25+ 行的功能 / 子系统 / 状态三维矩阵。本表可在 Wave G-5 编入 `runtime-contracts.md` 作为 contract surface 的统一索引。

---

## §7. 未来开发方向（architect 视角精炼）

`01-mainline-roadmap.md` 已给出 6 campaign + Wave G/H + 4-gate native promote。本节是**在最近一周新增证据后**对方向的小幅调整。

### 7.1 近期（0–3 月）

**核心**：B-1c §2 漂移归因 + Wave G 第一刀

| 优先级 | 项目 | 节奏纪律 |
|---|---|---|
| P0 | B-1c §2 allocator-policy closure — Qwen-only no-swap probe 已复现 drift (`20260524T113306Z`) | 下一刀不跑 aggregate；先定 settle / prompt-growth window / high-watermark accounting / budget rationale |
| P0 | **Wave G 第一刀 narrow doc edits**（见 §8 工作单） | docs-only · 不动 runtime code · 不抢 §2 资源 |
| P1 | Campaign F-1 — `speculative_execution_status` runtime-owned 状态契约 | 不必等 G2 完成；可与 §2 归因并行 |
| P1 | Wave H · H2 计划 spec drafting（不实施） | 等 B-1c §2 settle 后再 implement |

### 7.2 中期（3–6 月）

**核心**：G2 closure + Wave H 完成拆分 + Campaign C 起 instrumentation

| 优先级 | 项目 | 解锁条件 |
|---|---|---|
| P0 | B-1c §2 final aggregate · supported promotion | allocator-policy closure 后才恢复；当前不得 claim supported |
| P1 | Wave H · H2 实施 (`server_routes_runtime.py`) | B-1c §2 settle |
| P1 | Wave H · H3 实施 (`server_routes_dev.py`) | H2 落后 |
| P1 | Campaign C-1 — cold-first-response 5-factor instrumentation | session KV supported promote 后 |
| P2 | Campaign F-2/F-3 — n-gram/suffix probe + Gemma 4 resident MTP wrapper | F-1 落后 |
| P2 | D-recurring — DS4 在 D-style isolated ledger 的 steady-state 重跑（脱离一次性 closeout） | D2 ladder 闭合后 |

### 7.3 远期（6–12 月）

**核心**：RC1/RC2/RC3 路径上的实质动作

| 优先级 | 项目 | 解锁条件 |
|---|---|---|
| P0 | Campaign F-4/F-5 — 正交矩阵 + draft constraint checker | F-1/F-2/F-3 落后 |
| P0 | §VI G3 (Structured-Output Invariance) promote-path | F-4 矩阵 ≥20 case 通过 |
| P1 | Campaign C-2/C-3 — warmup default-on · thinking-mode TTFT 分布 | C-1 落后 |
| P1 | Wave G-5 — `runtime-contracts.md` 统一契约语义编入 | 6 campaign 中 3 个有新契约时启动 |
| P2 | §VI G4 (Speculative Path Landing) | F-4 + DS4 native MTP path 落后 |
| P2 | reopen condition triggers · 任一达成后同步刷新 capability matrix | 三条 reopen 之一达成 |

### 7.4 持续治理纪律（continuous）

| 项目 | 频率 |
|---|---|
| ARCHITECTURE-TRUTH §2.2 模块表对照代码扫描 | 每 4 周一次 · architect-reviewed |
| `master-outline.md §5` canonical list 增长审查 | 每次 wave 完成 |
| `phase45-*` 递归命名扩散巡检 | 月度（CI 加 lint 规则更佳） |
| spec-as-code 命名禁令（`*_exactness.py` / `*_carrier.py` / `*_marker.py` 等）巡检 | 已有 CI；扩展到 `*-exactness.md` 类 doc 名 |
| architect/ ↔ source-of-truth/ promote 路径审计 | 每个 reopen condition 达成时 |

---

## §8. 立刻可落的 Wave G 工作单（narrow · 不动 runtime code · 与 B-1c §2 解耦）

### 8.1 8 个 narrow doc edit（按依赖排序）

| # | 文件 | 变更 | LOC 量级 | 解决审计项 |
|---|---|---|---:|---|
| G-1 | `docs/source-of-truth/ARCHITECTURE-TRUTH.md` | §2.2 模块 / 测试盘点表全面刷新（19 → 53 模块、357 → 919 tests、含 Wave H · H1）；Updated 改为 2026-05-23 | ~80 | #1 #2 #4 #12 |
| G-2 | `docs/source-of-truth/ARCHITECTURE-TRUTH.md` | §2.3 文档盘点刷新（29 → 208；说明 phase45 proliferation 是 Wave G-4 目标） | ~15 | #3 |
| G-3 | `docs/source-of-truth/product-definition.md` | 新增 §11 "Internal Replacement-Grade Depth Posture"；引用 `01-mainline-roadmap.md §IV.1` 主线声明；不改 §1–10 历史；Updated 改为 2026-05-23 | ~50 | #5 #6 #7 |
| G-4 | `docs/source-of-truth/product-definition.md` | §5.2 vMLX 边界陈述刷新（按 `01-mainline-roadmap.md §IV.3`） | ~20 | #6 |
| G-5 | `docs/source-of-truth/master-outline.md` | §8 Dominant Question 刷新（baseline_missing → drift_under_swap + native_promote_path）；§5 canonical list 拆出 phase45-* 进 archive 子列表；Updated 改为 2026-05-23 | ~40 | #8 #17 #20 |
| G-6 | `docs/source-of-truth/runtime-capability-matrix.md` | 新增 Wave H · H1 行（server_routes_openai.py 拆出 · supported）；session KV cache 行新增 B-1c §1 interrupted prerequisite met 注脚（不晋级 supported） | ~10 | #11 #14 |
| G-7 | `README.md` | §"What ships now" speculative 行：从 "not in scope" 改为 "probe surface only · not in serving path"（与 `01-mainline-roadmap.md §V Campaign F` 一致）；Development status 段加 B-1c §1 prerequisite met 一句 | ~15 | #15 #18 |
| G-8 | `AGENTS.md` | Read Order 顶部加 `docs/architect/README.md`（作为 0 号，标 plan-grade 入口）；Non-Negotiable Project Truth 加一条引用 `product-definition.md §11`（after G-3 落后） | ~10 | #19 |

**总计**：240 LOC、8 个文件、零 runtime code 改动。

### 8.2 不在本工作单内的事

- **不**移动 / 删除 105 份 phase45-* 文件本身（这是 Wave G-4 的范围，需要独立 round 与命名约束讨论）
- **不**改 `runtime-capability-matrix.md` 任何标签 supported/partial（Wave G 不晋级）
- **不**改 `native-mlx-backend-capability-matrix.md`（健康文档，不动）
- **不**改 `session-kv-cache-experimental.md`（待 §VI G2 闭合后由 architect 反推）
- **不**改 architect/01–04 任何主线文件（B-1c §2 settle 之前不动）

### 8.3 staging 纪律提醒

- 每条 G-* 独立 commit；不混合
- commit 范围严格 `docs/source-of-truth/**` 或 `README.md` 或 `AGENTS.md` 或 `docs/architect/**` 中的**单一文件**
- 不夹带 untracked：`docs/architect/04-architecture-canvas.html`、`docs/source-of-truth/ds4-mtp-local-llm-stack-research.zh-20260514.md`、`软件著作权申请资料/` 都**不**进 G-1 ~ G-8 任一 commit

### 8.4 与 B-1c §2 解耦的理由

- G-1 ~ G-8 不依赖 §2 结果（除 G-7 中 speculative posture 涉及 Campaign F 起跑时间，但用"probe surface only"足以覆盖 §2 之前的状态）
- §2 漂移归因可与 doc refresh 并行执行；归因不会因 doc refresh 而改变路径
- B-1c §1 prerequisite met 是已经发生的事实（2026-05-21 落盘），不等 §2

---

## §9. 不进入本审计的范围（scope guard）

- ❌ runtime code 变更建议（本文是 doc 对齐审计，不出 code patch）
- ❌ test 改动建议（本文不替代 systematic-debugging 或 TDD）
- ❌ B-1c §2 漂移归因的具体方案（已在 `01-mainline-roadmap.md` Campaign B 与 `design/B-1c-section-2-spec.md §10`）
- ❌ Wave G-4 (phase45 docs archive) 的具体迁移路径（独立 round）
- ❌ Wave H · H2/H3 的 routes 拆分细节（设计层在 `01-mainline-roadmap.md §V Wave H`）
- ❌ Promotion gate 论证（任何 supported 晋级仍走 §1a Gate）

---

## §10. 维护规则

- 每次 architect/01-mainline-roadmap.md 主线刷新时同步审视本文
- 每次 Wave G commit 落后，删掉本文 §4 中已解决的审计项（保留 # 编号但标 `resolved by <commit-sha>`）
- 本文不入 `master-outline.md` 索引（plan-grade）
- 本文晋级到 source-of-truth 的条件：所有 §4 审计项 resolved 之后，把本文核心结论合并入 ARCHITECTURE-TRUTH §2 / product-definition / master-outline §8，本文整体降为历史快照
