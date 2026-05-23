# owlmlx 架构真源

> Status: **唯一权威** — 与本文件冲突的其他文档，以本文件为准
> Updated: 2026-05-23（§2.2 / §2.3 代码与文档盘点按工作树重盘点；§1 / §3 / §4 / §5 / §6 / §7 / §8 维持 2026-04-12 历史口径，待后续独立刷新）

## 1. owlmlx 是什么

owlmlx 是我们在 Apple Silicon 上的**自有 MLX runtime**。

它的终局是**替代 oMLX**，成为一个能独立 load model、serve inference、manage memory、handle lifecycle 的完整 runtime system。

它**不是**：
- oMLX 的 fork 或 wrapper
- 平台的 type library / schema 包
- 一堆 enum 和 dataclass 的集合
- 文档项目

## 2. 诚实现状

### 2.1 owlmlx 今天实际是什么

一个完成 **Runtime-11 degraded-routing closure** 的早期 runtime。

它不再只是 truth derivation library：现在有自有 `RuntimeKernel`、
backend adapter 边界、FakeBackend、最小 HTTP entry，并且 kernel 自己消费
memory budget / model inventory / runtime health / GenerationGate。

但它仍不是 production runtime：生产 serving hardening、控制面迁移和平台替换还未完成。

| 维度 | 现状 | 目标状态 |
|---|---|---|
| 能启动 server 吗 | **能，Runtime-3 已有 runtime status / restart / streaming surface** | 能：生产级 HTTP serving |
| 能 load model 吗 | **能，persistent child 真实 MLX load 已验证** | 能：真实 MLX 权重加载 |
| 能 generate token 吗 | **能，persistent child 真实 completion 已验证** | 能：真实模型 completion |
| 能管理内存吗 | **能做 load 前预算检查和 inventory 状态跟踪** | 能：主动 load/unload/evict/reclaim |
| 能感知自身状态吗 | **能，从 kernel 自身 backend status 推导 health，并上推到 runtime surface** | 能：真实 runtime probe 自己 |
| 能恢复故障吗 | **能做 child ping / next-request restart / explicit restart** | 能：更完整 restart/recovery policy |

### 2.2 代码盘点

> 历史口径：Runtime-7 完成交付时为 19 个 Python 模块、357 tests。本节按 2026-05-23 工作树重盘点；下文模块表与历史口径不冲突，是 Stage 1（2026-05-11 archived 151 spec-as-code 模块）+ Stage 2（2026-05-12 PR #649 alignment）+ Stage 3.1 + B-1a/B-1b/B-1c §1 + Wave H · H1 闭合期间的真实演进结果。

**当前规模**：53 个 Python 模块（`owlmlx/` 36 + `owlmlx/runtime/` 17）· 77 test 文件 / 919 test 函数 · `owlmlx/` + `owlmlx/runtime/` 总 LOC 29,730。

**Runtime-7 之后新增的主战场**（按出现顺序，非 LOC 顺序）：

- **内存纪律子系统（PR #649 alignment）**：`memory_watermark.py`、`memory_actuator.py`、`settle_barrier_event.py`、`host_pressure.py`、`memory_pressure_classifier.py`、`memory_pressure_eviction_policy.py`、`memory_budget.py`（既有）
- **Admission & cache 子系统**：`scheduler_admission.py`、`model_load_admission.py`、`nonresident_model_admission_policy.py`、`nonresident_loadability_lineage.py`、`cache_manager.py`、`cache_truth.py`、`cache_residency_tracker.py`、`cache_scheduler_status.py`、`session_kv_cache.py`（experimental · native only）
- **Multi-model lifecycle 子系统**：`model_inventory.py`、`model_lineage.py`、`model_residency_policy.py`、`model_profile.py`、`quantization_metadata.py`、`model_release_candidate_history.py` / `_record.py` / `_schema.py`
- **Status & provenance 子系统**：`runtime_health.py`、`orchestration_status.py`、`runtime_model_visibility.py`、`runtime_monitor_test_console.py`、`recovery_supervisor.py`、`comparative_evidence_history.py` / `_record.py` / `_runner.py` / `_schema.py`、`request_context_length_truth.py`、`reasoning_trace_policy.py`、`termination_recovery_policy.py`
- **Process boundary（experimental side）**：`runtime/mlx_native_backend.py`（in-process · session-scope opt-in only）、`runtime/mlx_vlm_mtp_runner.py`（MTP probe scaffold）、`gemma4_mtp_drafter.py`（drafter probe）
- **Runtime hardening**：`runtime/serving_hardening.py`、`runtime/specimen_gate.py`、`runtime/first_smoke_decision.py`、`runtime/host_stability.py`、`runtime/technical_preview.py`、`runtime/mlx_environment.py`、`abort_recovery.py`
- **HTTP routes 拆分（Wave H · H1）**：2026-05-17 拆出 `runtime/server_routes_openai.py`（OpenAI/Anthropic 兼容 5 routes）；`runtime/server.py` 保留 42 routes 待 H2/H3

**Top-15 模块（按 LOC，覆盖 ≥ 75% 总 LOC）**：

| 模块 | LOC | 性质 |
|---|---:|---|
| `runtime/mlx_lm_subprocess_backend.py` | 2541 | subprocess backend（生产路径 · persistent child lifecycle） |
| `runtime/server.py` | 2013 | HTTP entry + 42 routes（Wave H · H1 之后 · H2/H3 待启） |
| `runtime/kernel.py` | 1694 | RuntimeKernel: load / generate / unload / restart / settle / pin / TTL / eviction history |
| `runtime_monitor_test_console.py` | 1267 | 内部测试台（OwlOps 消费） |
| `runtime/mlx_native_backend.py` | 1215 | native backend（experimental · session-scope opt-in） |
| `comparative_evidence_runner.py` | 1130 | comparative bench 主驱动（OwlOps consumer） |
| `serving.py` | 1009 | GenerationGate + pre-gate cohort hook + admission seam |
| `runtime/mlx_lm_runner.py` | 896 | mlx_lm child process runner（stdin/stdout JSON 协议） |
| `runtime/serving_hardening.py` | 857 | hardening contract（recovery / abort / restart） |
| `runtime/server_routes_openai.py` | 829 | Wave H · H1 已拆（OpenAI/Anthropic 兼容） |
| `runtime/mlx_environment.py` | 744 | environment probe + verified baseline registry |
| `nonresident_model_admission_policy.py` | 709 | non-resident admission verdict |
| `termination_recovery_policy.py` | 625 | termination 恢复策略 |
| `memory_actuator.py` | 612 | 内存执行（watermark + actuator） |
| `scheduler_admission.py` | 599 | scheduler admission contract |

余 38 模块按 LOC 分布在 100–600 之间，覆盖 schema / lineage / policy / training / status surface 等细分职责。

**关键事实**（保持自 Runtime-12 历史结论 · 仍然成立）：launch readiness、operability、replaceability 仍是控制面分离输出；父进程仍永不 import mlx_lm；single worker by design (`MAX_GENERATION_CONCURRENCY = 1`) 是 MLX/Metal 同进程并发不安全的物理结论。

**HTTP 表面**：47 路由（subprocess + native 共用 · OpenAI 兼容 5 + Anthropic 兼容 2 + 核心 lifecycle 8 + `/v1/runtime/*` 状态 27 + admin/monitor 5）。详细路由分类见 `docs/architect/05-alignment-audit.md §2.3`。

### 2.3 文档盘点

> 历史口径：2026-04-12 当时为 29 个 source-of-truth 文档。本节按 2026-05-23 工作树重盘点。

**当前规模**：`docs/source-of-truth/` 208 份 .md 文档。

| 范畴 | 数量 | 说明 |
|---|---:|---|
| 非 `phase45-*` 文档 | 103 | 顶层契约 + capability matrix + 各 wave 闭合契约（runtime-*、stabilization-*、product-definition、master-outline 等） |
| `phase45-*` 前缀文档 | 105 | 历史 wave 45 期间的 cache / scheduler / pre-claim / stream-backend 细化契约；其中约 15 份出现 4+ 层 hyphen 嵌套递归命名 |
| `master-outline.md §5` canonical reading list 编号文件 | 145 | 其中 79 为 `phase45-*` |

**plan-grade architect 文档**（独立目录 `docs/architect/` · **不**入 `master-outline.md` 索引 · 详见 `docs/architect/README.md`）：5 份 plan-grade（含 `01-mainline-roadmap.md` / `02-state-vs-market-gap.md` / `03-real-accomplishments.md` / `04-architecture-canvas.md` / `05-alignment-audit.md`）+ `design/` 子目录 8 份 design-grade gate spec（B-1a / B-1b / B-1c §1 / B-1c §2 / D1 / D2 / D3 / D4）。

**已识别的治理目标**（不在本次盘点范围内）：`phase45-*` 递归命名扩散与 4+ 层 hyphen 嵌套是 Stage 1（2026-05-11）已在源代码层禁止的 spec-as-code 反模式在文档层的重现，作为 Wave G-4 独立 round 处理。本节仅记盘点事实，**不**做归并 / 迁移 / 删除。详细审计与建议见 `docs/architect/05-alignment-audit.md §3.2 / §4.3 / §8`。

历史定性仍然成立：多数 source-of-truth 文档描述的是**目标架构**或**历史 wave 闭合契约**，不是**当前实现**的每行代码——这不是错（方向文档与历史契约都有存在价值），但不能把方向文档等同于已交付能力。

### 2.4 平台消费关系

平台（AI/Agent）import owlmlx 的 7 个模块做推导：

| 平台文件 | 消费的 owlmlx 模块 | 做什么 |
|---|---|---|
| metrics.py | model_inventory, runtime_health | 构建 inventory snapshot → 推导 load_state/wait_tier |
| control_service.py | model_inventory, memory_budget | budget 检查：能不能 load 这个模型 |
| context_concurrency_policy.py | context_concurrency | 按 context length 限并发 |
| abort_recovery.py (platform) | abort_recovery | 委托状态跟踪给 AbortRecoveryTracker |
| primary_line_status.py | model_lineage | normalize/validate catalog lineage |
| distilled_cache_substrate.py | cache_truth | cache flag/profile/restart 推导 |
| kimi-sharded-engine.py | serving | GenerationGate 并发控制 |

**这 7 个消费关系证明 owlmlx 作为 truth substrate 是有价值的。Runtime-0 之前，
真正的 runtime 行为（probe、load、serve、restart）过去全在平台侧。Runtime-0
补上了 owlmlx 自己的最小 kernel，Runtime-2 又补上了 persistent child 真实 MLX 会话。
但平台消费关系仍然只代表 schema/truth 复用，不代表生产 runtime 迁移完成。**

## 3. 四层架构（诚实版）

system-architecture.md 定义了四层。Runtime-3 后，Layer 2 已有最小可执行 kernel、真实 MLX child session、以及第一批 runtime control surface：

```
Layer 4: Product integration (平台 ops_dashboard、dashboard、API)     ← 存在，在平台
Layer 3: Runtime paths (large-weight path, standard path)             ← GenerationGate + Runtime-3 path
Layer 2: Core runtime (load, serve, memory, switch, introspect)       ← Runtime-3 minimal kernel 存在
Layer 1: MLX substrate (tensor execution)                             ← 存在，是 Apple 的

owlmlx 实际占据的位置：Layer 2 最小 kernel + truth substrate。还不是 production runtime。
```

## 4. 从 truth library 到 runtime 的差距

### 4.1 缺失的 runtime 能力（按优先级）

| # | 能力 | 现状 | 为什么需要 |
|---|---|---|---|
| 1 | **Safe real MLX model loader** | 持久 child 已完成真实 `load`；clean `.runtime1-mlx` 已通过 import probe；`gpt-oss-20b` 和 `Qwen3.5-27B` 已完成 Runtime-2 真实复用 smoke | 下一步是 child health probe / restart，不再是“能不能真 load” |
| 2 | **Safe real inference engine** | persistent child 已完成真实 `generate many` | 下一步是 steady-state metrics、restart policy、streaming |
| 3 | **Production HTTP server** | Runtime-3 已有 runtime status / restart surface | 下一步是 streaming、配置、部署入口、控制面完整化 |
| 4 | **Memory controller** | load 前预算检查 + inventory | 要能主动 load/unload/evict/reclaim |
| 5 | **Self-introspection** | kernel status 可自推导；persistent child `ping` health probe 已接入 backend status | 下一步是把 probe 结果上推到更明确的 runtime/API 语义 |
| 6 | **Process lifecycle** | persistent child `load / unload / next-request restart` 已存在 | 下一步是 restart policy 的更高层治理和 SLO |

Runtime-3 当前的运行纪律已经明确：

- 父进程不直接 import `mlx_lm`
- 默认环境探测只检查当前解释器
- 已知危险 MLX venv 只能显式 opt-in 诊断
- 环境问题要报告成结构化失败，不允许用默认诊断制造重复崩溃
- 真实模型会话必须通过 persistent child lifecycle，不回退到 one-shot 默认路径
- child health 以 `ping` 为准，不允许只看进程是否还活着
- dead child restart 只在保留 registration 的前提下发生，不在当前失败请求里偷偷重试
- serialized concurrent serving 仍然是 runtime truth，不允许因为 persistent child 而默认放开并发

### 4.2 已经完成的（truth library 价值）

| # | 能力 | 模块 | 价值 |
|---|---|---|---|
| 1 | Memory budget truth | memory_budget.py | 未来 memory controller 用它判断 |
| 2 | Concurrency boundary | context_concurrency.py | 未来 serving 用它限流 |
| 3 | Abort recovery state | abort_recovery.py | 未来 lifecycle 用它判断恢复 |
| 4 | Health derivation chain | runtime_health.py | 未来 introspection 用它推导状态 |
| 5 | Model inventory schema | model_inventory.py | 未来 loader 用它跟踪已加载模型 |
| 6 | Lineage validation | model_lineage.py | 未来 loader 用它校验权重来源 |
| 7 | Cache truth contract | cache_truth.py | 未来 cache manager 用它决定策略 |
| 8 | Generation gate | serving.py | 已经是真正的 runtime 组件 |

**这些不是废物。它们是未来 runtime 的判断层基础。但判断层不等于 runtime 本身。**

## 5. 文档权威性排序

从本文件生效起，owlmlx 文档权威性：

```
1. ARCHITECTURE-TRUTH.md (本文件) — 唯一顶层真源
2. runtime code (owlmlx/*.py) — 代码即实现事实
3. tests/ — 验证事实
4. product-definition.md — 冻结的方向声明
5. system-architecture.md — 架构目标（标注哪些已实现、哪些未实现）
6. 其他 source-of-truth docs — 参考，与本文件冲突时以本文件为准
```

## 6. 术语矫正

| 之前用的词 | 问题 | 改为 |
|---|---|---|
| "absorbed" | 暗示 owlmlx 吸收了 runtime 能力 | "schema extracted" — 提取了 schema/derivation |
| "consumed" | 暗示平台依赖 owlmlx runtime | "platform imports" — 平台 import 了 owlmlx 的 schema |
| "convergence" | 暗示两个 runtime 在靠拢 | "schema unification" — schema 层统一了 |
| "runtime truth" | 暗示 owlmlx 拥有 runtime 事实 | "derivation truth" — owlmlx 拥有推导规则 |
| "owlmlx-owned" | 对于 enum/derivation 没问题 | 保留，但不用于描述 runtime 执行能力 |

## 7. 下一步方向

### Chosen Direction: Executable Runtime Kernel First

**Option D (stay as truth library) rejected** — owlmlx 要成为 runtime，不是 schema 包。

**Option C (wrap oMLX as subprocess) rejected** — wrapper 不是 runtime。

**Option A/B merged into A': Executable Runtime Kernel** — owlmlx 先成为可执行 runtime kernel，借用 MLX ecosystem 的 loader/generation 机制（mlx-lm），不从零重写底层 transformer。自有 = 拥有 runtime 入口、状态、治理、内存决策、服务语义。不等于重写每一行执行代码。

"替代 oMLX" 的精确含义：**owlmlx 替代 oMLX 作为我们的 runtime control boundary**。不是第一天替代 oMLX 的每一行代码。

**从本决策生效起，owlmlx 不再以 schema extraction 为主线。** 未来 schema 工作只允许在直接支撑 RuntimeKernel 实现时进行。

### 7.1 Runtime Kernel MVP — 最低交付定义

第一版已证明一件事：**owlmlx 自己能作为 runtime kernel 活起来**。

| # | 交付物 | 说明 |
|---|---|---|
| 1 | 自有 kernel | `RuntimeKernel` 管理 load/generate/unload/status |
| 2 | Backend adapter | `RuntimeBackend`, `FakeBackend`, `MlxLmBackend` |
| 3 | Generation endpoint | FakeBackend 可 completion；mlx-lm generate 调用路径可 mock 验证 |
| 4 | 最小 HTTP API | `GET /healthz`, `POST /v1/load`, `POST /v1/generate`, `GET /v1/models`, `POST /v1/unload` |
| 5 | Truth substrate 集成 | load 前走 memory_budget 预算检查，serve 走 GenerationGate，health 走 runtime_health snapshot |

第一版不追求性能，不强制真实模型加载。目标是架构闭环，不是跑 31B。

### 7.2 实际内部结构（Runtime-7）

```
owlmlx/
  runtime/
    types.py                      # 结果类型 + RuntimeErrorCode
    backends.py                   # RuntimeBackend Protocol + FakeBackend
    kernel.py                     # RuntimeKernel: load/generate/unload/status 核心
    server.py                     # 最小 HTTP entry (FastAPI)
    mlx_lm_backend.py             # in-process mlx-lm adapter（仅 probe 用途）
    mlx_lm_runner.py              # 子进程 runner：命令循环、持久 model session
    mlx_lm_subprocess_backend.py  # 父进程安全 backend，persistent child lifecycle
    mlx_environment.py            # 环境探测 + 安全选择
```

未来可能新增但 Runtime-1 还不需要的：

```
    memory.py          # 消费 memory_budget / model_inventory → 主动 evict
    lifecycle.py       # 消费 runtime_health / abort_recovery → process restart
```

### 7.3 之前工作的重新定性

R11-R18 的价值：给 RuntimeKernel 准备了判断层。

| 之前叫 | 改为 |
|---|---|
| Runtime absorption 进度 58% | Truth substrate readiness: 11 modules / 286 tests / platform consumed |
| 下一个吸收 gap | **不再有。主线切到 RuntimeKernel。** |

诚实的 scorecard 拆成两张：

```
Truth substrate readiness:  11 truth modules, 357 tests, 7 platform consumers ✓
Runtime executability:      Runtime-0 MVP ✓ → Runtime-1 真实模型验证 ✓ → Runtime-2 persistent child ✓
Runtime serving surface:    Runtime-3 restart/status/streaming surface ✓
Runtime migration seam:     Runtime-4 chat/completions + SSE + model discovery ✓
Runtime compat entrypoints: Runtime-5 backend-owned message handling + completions/chat compatibility ✓
Anthropic cutover seam:     Runtime-6 `/v1/messages` + count_tokens + Anthropic SSE + tool-use seam ✓
Real Owl consumer cutover:  Runtime-7 `owlcc run` direct endpoint tool loop completed ✓
Real OwlCoda cutover:       Runtime-8 native/headless + native REPL + resume/tool-loop continuation ✓
Source-first cutover:       Runtime-9 source-first prompt path through `owlcoda serve -> owlmlx` ✓
Control-plane operability:  Runtime-9 runtime probe + preflight + dry-run against direct `owlmlx` ✓
Source-first tool loop:     Runtime-10 real source-first tool loop against `owlmlx` ✓
Downgrade-path hardening:   Runtime-10 `healthz` no longer fabricates transport protocol ✓
Degraded-routing closure:   Runtime-11 `auto + healthz-only` local routing now fails closed ✓
Replacement readiness:     Runtime-12 `doctor` now emits explicit verdict + blocker list ✓
Replacement verdict:        Runtime-9 = old platform not yet replaceable ✓
Subprocess isolation:       父进程永不 import mlx_lm，子进程 abort → 结构化错误 ✓
Real local smoke baseline:  gpt-oss-20b + Qwen3.5-27B + Qwen3.5-35B-A3B 通过 ✓
Persistent child proof:     gpt-oss-20b / Qwen3.5-27B 同一 pid 连续 generate 通过 ✓
Steady-state benchmark:     gpt-oss-20b load≈1.49s, warm median≈0.157s ✓
Serialized serving proof:   gpt-oss-20b 并发2请求保持 serial gate ✓
Real streaming proof:       gpt-oss-20b TTFT≈0.218s, real token events through RuntimeKernel ✓
Same-model comparison:      Qwen3.5-35B-A3B Runtime-3 vs old platform completed ✓
Production readiness:       not yet
```

## 8. 本文件的维护规则

- 每次 owlmlx 有重大变更（新模块、新 runtime 能力、架构方向变化），更新本文件
- §2.2 代码盘点必须反映实际模块列表
- §4.1 缺失能力随实现进展移除
- 不允许其他文档声称 owlmlx 拥有本文件 §4.1 中标注为"不存在"的能力
