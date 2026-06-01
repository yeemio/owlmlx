# owlmlx 总架构师规划 — Apple Silicon Replacement-Grade Runtime 12+ 月战略路线图

> **文档 grade**：plan-grade / architecture intent · 见 [README.md](README.md)
> **承载位置**：`docs/architect/01-mainline-roadmap.md`（authoritative）
> **编制**：2026-05-16（含决策 A–E + F-β + G-b2 + D3 §1/§2 独立结论补强）
> **语言纪律**：遵循 evidence-language calibration（`load-path-compatible` / `plausible` / `experimental scaffold`，不使用未经证据支持的 `supported`）

---

## 顶层维护入口（Current Planning Source）

本文件是 `owlmlx` 顶层 plan-grade 规划的项目内维护入口。`~/.claude/plans/owlmlx-1-*` 只作为 2026-05-16 初稿承载和导入来源；自本轮起，不再把临时承载文件当事实源或维护目标。

| 角色 | 项目内文件 | 状态 |
|---|---|---|
| 顶层主规划 | [01-mainline-roadmap.md](01-mainline-roadmap.md) | **authoritative plan-grade** |
| 现状 vs 市场差距 | [02-state-vs-market-gap.md](02-state-vs-market-gap.md) | companion · plan-grade |
| 已完成真实情况 + 数据对比 | [03-real-accomplishments.md](03-real-accomplishments.md) | companion · plan-grade |
| 架构画布（仓内可 diff 版） | [04-architecture-canvas.md](04-architecture-canvas.md) | companion · plan-grade |

维护裁定：

- 顶层规划由 Codex 在 `docs/architect/**` 内维护；每次架构方向变化先更新本文件，再更新对应 companion。
- `docs/architect/**` 仍是 **plan-grade / architecture intent**，不进入 `docs/source-of-truth/master-outline.md`，除非经 runtime evidence + §1a Promotion Gate 晋级。
- Wave / Campaign 结束时必须反推刷新：主规划结论、对应 companion、README 阅读顺序；不得只在聊天或临时 plan 文件里留下新事实。

当前最新收拢结论：主线仍是 **`owlmlx` runtime engineering mainline**；推进形态是 **6 个 Campaign（A–F）+ Wave G（治理刷新）+ Wave H（server 工程化拆分）**。B-1 Session KV cache `supported` 四条 gate 仍有 B-1c §2 待闭环；Wave H 的 H1 compat routes split 已落到 `server_routes_openai.py`；Campaign D 的 DeepSeek D1-D4 experimental lane 已收口；2026-05-26 performance lane 复盘显示 raw TPS / n-gram serving / prompt cache / prefill chunking 短期不再是最大杠杆；F-4 structured-output 已赢得窄 grammar lane `partial`，整体仍 `experimental`。当前执行主线回到 B-1c §2 measurement-continuity closure。

| 最新落点（2026-05-27） | 状态 | 证据边界 |
|---|---|---|
| B-1b design spec | landed | `docs/architect/design/B-1b-spec.md` |
| B-1b cache reclaim gate | passed · native N=20 | cache-off N=20 + cache-on N=20；20/20 warm hits；`failed_reclaim=0`；`failed_unload=0`；p50/p99 settle duration within threshold |
| B-1c §1 no-swap soak runner | current-Mac interrupted rehearsal passed · continuous 24h still not claimed | first native rehearsal exposed default TTL expiry as drift; TTL-locked 121s native segment recorded `max_drift_bytes=0`; 4h + planned-shutdown aggregate `20260517T161707Z` stayed blocked; 2026-05-19 segment `20260519T014912Z` recorded `measurement_duration_s=28245.605`, wall-clock gap free, max drift 0; 2026-05-20 segment `20260520T075227Z` recorded `measurement_duration_s=53441.374`, wall-clock gap free, max drift 0; 2026-05-21 top-off `20260521T044517Z` recorded `measurement_duration_s=7201.552`, wall-clock gap free, max drift 0; aggregate `20260521T064658Z` records `aggregate_measurement_duration_s=88888.531`, `all_segments_ok_for_rehearsal=true`, `interrupted_no_swap_rehearsal=passed`, `current_mac_section_1_prerequisite_met=true`, while `no_swap_soak_stability=blocked` remains correct because only dedicated/UPS continuous native `mlx_core_active_memory` + required_duration ≥24h can produce continuous stability |
| B-1c §2 soak + swap runner | prompt-reset functional subcriteria clean · wall-clock gap blocker open | `scripts/bench/eviction_soak.py` now has `b1c2-soak-plus-swap` / `b1c2-interrupted-soak-plus-swap` schema paths plus guarded native execution (`--b1c1-prerequisite-satisfied` + explicit 3-model paths required); 4h fail-fast segment `20260522T115939Z` failed at sample `111` / Qwen long session; no-sleep reproduction `20260522T151921Z` confirmed the `.short` token-boundary cause; boundary-safe 4h segment `20260522T164506Z` kept cache drops/expirations/rejects at 0 and swap clean, but failed on active-memory drift (`352321536 > 209715200`); prompt-reset focused probe `20260525T055831Z` reduced trim bypasses to 3 and drift to `171704320 < 209715200`; first prompt-reset swap-bearing segment `20260525T061019Z` kept drops/expirations/rejects at 0, trim bypasses at 3, drift within budget, and swap boundary clean, but wall-clock continuity failed (`measurement_wall_clock_gap_free=false`, 6 gaps, max `7064.873s`), so `clean_for_interrupted_aggregate=false`; no supported claim |
| D1 DeepSeek repeatability runner | passed · experimental lane · messages prompt policy adopted | default `messages` prompt surface passed the formal 5 prompt × 128/512/1024 matrix (`20260517T-d1-full-ladder-adopted-messages-policy.jsonl`) with 15/15 passed, no repetition, and clean load/unload health; raw prompt remains diagnostic failure at p1/1024 and is not the accepted D1 surface; preflight shows Blaizzy `mlx-lm` fork `pc/add-deepseekv4flash-model` at `5c10538136b9038b9626c134612b08afc18d697a` |
| D2 DeepSeek metrics ledger | passed · p1/p2/p4 × 128/512 | fd-buffered child stdout reader fixed the previous stream block; `20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl` records 6/6 passed rows, TTFT p50 593.840ms, decode p50 38.17885 tok/s after first token, child-process RSS p50 7.214432GB (not peak/process-tree aggregate), clean unload |
| D3 DeepSeek MTP checkpoint inspection | passed · explicit missing reason | `20260517T-d3-mtp-checkpoint-inspection.jsonl` records `num_nextn_predict_layers=1`, 2610 weight keys / 19 shards, no MTP key candidates, no extra layer keys, `missingReason=mtp_weights_absent_or_stripped`; DeepSeek remains experimental-only |
| D4 DeepSeek MTP pre-load reject | passed · clean failure isolation | `20260517T-d4-mtp-clean-preload-reject.jsonl` records `decision=rejected_pre_load`, `reason_code=mtp_weights_absent_or_stripped`, `load_attempted=false`, `child_process_started=false`, and stable 8066 health before/after |
| H1 compat route split | landed | `server_routes_openai.py` 拆出 OpenAI / Anthropic compat routes |
| F-2 / perf lane | C0/C1 passed · serving integration paused | n-gram C2 and prompt-cache reuse are blocked/paused on mlx-lm hybrid trim; B prefill chunking configuration/progress surfaces are supported, but wall-clock acceleration is not promised |
| F-4 Structured-Output Invariance | narrow grammar lane partial · overall experimental | `structured-output-grammar-lane.md` freezes the Qwen grammar-on lane (`json_schema_flat` / `enum_constrained` / `function_call_arguments` / `nested_object`) as feature-lane `partial`; Gemma and `thinking_tag_closed` remain residual; no F-4-wide or supported claim |
| Targeted tests | passed | B-1c/D1/session-cache focused suite = 39 passed；subprocess backend = 64 passed（上一轮） |

下一条真实执行线：**B-1c §2 measurement-continuity closure**（同一 prompt-reset swap-bearing policy 的 gap-free 4h segment；先证明单段 aggregate-eligible，再累计 6 × 4h）。F-4 已归档窄 lane，后续 F-4 residual 不阻塞当前 runtime stability 主线；只有新 DS4 artifact / adapter fork 改变 D3 checkpoint inspection 结果时，才启动 D5。

---

## 主线声明（Mainline Statement · 2026-05-16）

当前唯一主线是 **`owlmlx` runtime engineering mainline**——把 `owlmlx` 从"有很多 runtime truth / evidence / contract"推进到 **0.3.0 前真正 replacement-grade 的本机 MLX runtime**：**可长期运行、可观测、内存纪律可靠、能承载本地大模型交互**。

一句话：

> `owlmlx` 要在 0.3.0 前证明：它**不是**文档/治理项目，而是一个**可长期运行、可观测、内存纪律可靠、能承载本地大模型交互的 runtime**。

**OwlCoda 不是主线、`llm_router` 不是主线**——它们分别是上层消费者与过渡资产（详见 §IV.5）。

### 用户确认的规划要点（2026-05-16 · 一次）

- 视野：12+ 个月，含再开放发版条件
- speculative：升级为正式第 6 子战役
- 文档治理：作为独立 Wave G
- `mlx_native_backend.py` 处置：4-gate promote-path（§VI）

### 用户校准追加（2026-05-16 · 二次 / 三次）

- runtime port 校正为 **8066**（README 当前 8082 在 Wave G 文档刷新中校正）
- **Session KV cache `supported` gate 四条**：B-1a / B-1b / B-1c §1 / B-1c §2（D3 决策见 §V）
- **新设 Wave H**：`server.py` 工程化拆分（独立于 Wave G 文档治理）
- **边界资产显式**：OwlRunKit + `llm_router`（§IV.5）
- **bench / evidence 主叙事重组**：四主证据（详见 [03-real-accomplishments.md](03-real-accomplishments.md)）
- **决策 A** · B-1a 锁定 Gemma 4-31B-it
- **决策 B** · Wave H · H1 已完成 / H2-H3 等 B-1 闭环
- **决策 C** · 4-gate G1 通过条件 = B-1a 通过（含 N≥5 prompt 字节等价）
- **决策 D = D3** · B-1c 拆 §1（24h 纯 soak）+ §2（24h soak+swap）；结论字段独立
- **决策 E** · Campaign D 启动时点 = B-1a 完成后

---

## Part I — 外部技术锚定（External Anchoring）

### I.1 Apple Silicon LLM 生态边界（2026-05 现状）

| 层 | 业界已固化（owlmlx 不重做） | 业界尚未共识（owlmlx 有空间） |
|---|---|---|
| MLX substrate | TurboQuant / PolarQuant 3–4bit KV 压缩；Metal decode 自定义内核；单卡 M3/M4 400+ tok/s | 量化感知调度；session/workspace 级 KV lifecycle 治理 |
| 多并发调度 | vllm-mlx continuous batching + paged KV（优于 llama.cpp 21–87%）；vMLX 单机端 OpenAI/Anthropic 全栈 | reliability-bound 调度（保证 spec 路径下 structured output 不破坏）；多租户 prefix cache 安全共享 |
| 消费级 runtime | Ollama / LM Studio / Jan / Cortex 已饱和；mlx-knife 已覆盖 HF 模型生命周期 | 企业级可观测性下沉到 runtime 层；模型供应链溯源；A/B 部署 runtime-owned 接口 |
| OS 层 | macOS Tahoe 26 + Apple FM 框架 | 多模型编排、微调生命周期、企业级 SLA |

**关键判读**：vMLX 已是 Apple 官方背书全栈 — owlmlx 不在 raw throughput 上竞争，差异化轴 = **Reliability + Provenance + Governance**。

### I.2 本地 LLM Runtime 通用技术趋势

| 维度 | 业界状态 | 对 owlmlx 的指向 |
|---|---|---|
| Speculative Decoding | MTP / EAGLE-3 / Medusa / n-gram 平台化（vLLM/SGLang/TRT-LLM） | spec 不可避免；**痛点是 spec × structured-output × tool-calling 兼容性**（vLLM issue #41967）——这是 owlmlx 最大差异化空间（Campaign F） |
| Continuous Batching | vLLM / SGLang / TRT-LLM 标准；vllm-mlx 已带到 Apple Silicon | owlmlx **明确不做**（单 worker by design）；用 admission/eviction 精细化作为简化等价物 |
| KV cache 跨请求/会话 | vLLM prefix caching v0.6+；Anthropic workspace 隔离；TurboQuant 量化 KV | owlmlx 已实证 session-level 7.409×；下一步 workspace-aware safety + 跨模型版本 invalidation |
| MoE / Long-Context | DeepSeek V4 1.6T/49B + FP4 + CSA/HCA | DS4-Flash 2bit-DQ 维持 `experimental adapter optimization candidate`，不晋级 |
| Tool Calling × Spec | thinking-mode + spec + multi-tool silent breakage 普遍 | owlmlx 作为 6th campaign 核心命题（spec path 下 bit-for-bit 不变） |
| Apple Silicon 异构 | GPU/CPU/ANE 三器件分工无成熟方案 | 不当主线投入；backend Protocol / status schema 预留扩展点 |

### I.3 外部信号对 owlmlx 路线最有价值的 3 个收敛点

1. **Spec × structured-output × tool-calling 可靠性保证**是开源 runtime 普遍缺陷
2. **Session/workspace 级 KV lifecycle 管理**是企业多轮场景的成本杠杆（40–60% 下降量级）
3. **Apple Foundation Models 不是竞争者，是护城河延伸**——Apple FM 不做多模型编排 / 微调 / 企业可观测

---

## Part II — 平台架构评估框架（12 维）

| # | 维度 | Hardened 判据 | 反模式 |
|---|---|---|---|
| 1 | Repeatability | N≥20 重复同 prompt 输出字节一致；seed 显式可追 | "偶尔快、偶尔破坏" |
| 2 | Capability Honesty | 正交组合完整性测试；破坏率 <0.1% | 声称支持但 silent 破坏 |
| 3 | Cache Depth | 跨请求/会话/工作区 prefix 复用；多租户安全 | request-local KV；OOM=crash |
| 4 | Scheduler Depth | TTFT/ITL/throughput 三角可调；负载分类自动选路 | 固定 batch、固定 split |
| 5 | Admission / Eviction | resource budget 明确；SLA-aware；可观测拒绝率 | OOM crash；silent suspend |
| 6 | Status & Provenance | request lifecycle 完整事件流；artifact 来源链；spec accept/reject ratio | "OK/ERROR 二值" |
| 7 | Failure Cleanliness | 失败显式通知；无 zombie；资源回收；级联抑制 | crash 整 runtime |
| 8 | Multi-Model Lifecycle | model registry 版本化；hot swap；版本并存 | 一次一个模型 |
| 9 | Speculative Path Safety | draft 受 constraint checker；tool calling 完整性 | spec 启用静默丢工具参 |
| 10 | Structured-Output Invariance | quant-invariant；batch-invariant；spec-invariant | "通常能输出有效 JSON" |
| 11 | OwlOps Consumption | metrics 导出；结构化日志；OTel tracing | minimal metrics |
| 12 | Heterogeneous Compute | device assignment；KV 异构存放；ANE-aware quant | 全 GPU 硬编码 |

详细对照见 [02-state-vs-market-gap.md](02-state-vs-market-gap.md)。

---

## Part III — owlmlx 当前状态快照

### III.1 身份与边界（既定锚点）

- **身份**：Apple Silicon 上自有的 MLX serving runtime，memory-discipline-first，**单 worker by design**（`MAX_GENERATION_CONCURRENCY = 1`）
- **底层**：MLX substrate（`mlx`、`mlx-lm`、`mlx-vlm`）—— 借用执行底座
- **消费者**：OwlOps（live · 27 行 ledger）/ OwlCoda（gated · 非主线）/ OwlMom（间接 · 5 Vue 页 FROZEN）/ OwlRunKit（候选 broker · 非主线）
- **替代对象**：oMLX 作为 runtime control boundary（不是替代每行代码）

### III.2 实现代码现实（来自 Phase 1 代码扫描）

- 顶层结构：owlmlx/ 40+ 模块 + runtime/ 14 文件
- 关键文件 LOC：server.py 2013（H1 后）/ server_routes_openai.py 829 / kernel.py 1694 / mlx_lm_subprocess_backend.py 2541 / **mlx_native_backend.py 1074**
- 测试：73 test files / 835 test_ functions
- 后端：subprocess（default · supported）+ native（experimental · session-scope opt-in）

### III.3 12 维诚实自评（架构师视角）

| 维 | 状态 |
|---|---|
| #1 Repeatability | partial（harness 实装；N≥20 未强制） |
| #2 Capability Honesty | **strong**（Stage 1 已清 spec-as-code；CI 强制；§1a Gate） |
| #3 Cache Depth | partial（session-level 7.4×；cache_manager 单请求） |
| #4 Scheduler Depth | partial / spec-only（admission contract 完整；warmup 未 default） |
| #5 Admission / Eviction | partial（决策完整；synchronous-only） |
| #6 Status & Provenance | **strong**（request lifecycle 维度）/ partial（spec 维度） |
| #7 Failure Cleanliness | partial（recovery_supervisor / settle_barrier supported） |
| #8 Multi-Model Lifecycle | partial（pin/TTL/eviction supported；hot-swap 缺） |
| #9 Speculative Path Safety | **scaffold-only**（gemma4_mtp_drafter probe） |
| #10 Structured-Output Invariance | partial lane / overall experimental（Qwen grammar-on JSON / enum / function_call / nested-object lane 已过；Gemma 与 thinking-tag residual） |
| #11 OwlOps Consumption | **strong**（27 行 ledger live） |
| #12 Heterogeneous Compute | **not in scope**（远期预留） |

---

## Part IV — 架构方向决策

### IV.1 身份再确认（12+ 月战略身份）

> "为 Apple Silicon 单机企业级 agentic / batch evaluation 场景而生的 **memory-discipline-first replacement-grade MLX runtime**"

差异化轴三条：**Reliability** + **Provenance** + **Governance**（不追 raw throughput / continuous batching / 消费级 GUI / Apple FM 同质化）。

### IV.2 边界提交（不可妥协）

- **单 worker by design**：`MAX_GENERATION_CONCURRENCY = 1` —— 不通过实验性绕过
- **memory-discipline-first**：watermark + settle barrier + reclaim-verified
- **runtime truth flows upward**：上层消费、不重定义
- **adoption rule**：借入 = `partial` / `experimental`，永不自动 `supported`
- **module-as-spec forbidden**：Stage 1 下架 151 模块 / 31K LOC，CI 强制
- **runtime port 8066**（README 8082 在 Wave G 校正）

### IV.3 vMLX 现状下的边界澄清

旧 README "continuous batching / 多 host / 多租户 cluster 看 oMLX/vMLX" 已不准——vMLX 是 Apple 官方背书全栈。**Wave G 刷新**为：

> owlmlx 与 vMLX 在单机 Apple Silicon 上场景部分重叠（OpenAI/Anthropic API 端点）。差异化：
> - owlmlx 强制 memory-discipline-first（vMLX 偏 throughput-first）
> - owlmlx 把 capability honesty + spec path safety + governance 作为发版门控
> - owlmlx 与 OwlOps/OwlCoda/OwlMom 形成内部消费闭环；vMLX 是开源全栈，无此契约关系

### IV.4 与 Apple Foundation Models（Tahoe+）相对位置

- 不冲突；Apple FM 不做多模型编排 / 微调 / 企业可观测
- 远期 hook：backends.py Protocol 预留 `AppleFoundationModelsBackend` 扩展点

### IV.5 邻接资产位置（Adjacent Assets）

| 资产 | 位置 | 与 owlmlx 的边界关系 |
|---|---|---|
| **OwlRunKit** | owlmlx 之外（候选位） | lifecycle / env broker：`.runtime*-mlx` venv 切换、模型 artifact 下载、host preflight。owlmlx 只暴露 `pre_load_check` / `host_pressure` / `model_visibility` contract |
| **`llm_router`** | 过渡资产（transitional） | **不入** owlmlx mainline。当前承担本地 runtime 间路由切换；待 owlmlx replacement-grade 后由 owlmlx mainline 替代或由 OwlOps 上收 |
| **OwlCoda** | 上层消费者 | release channel split (`a21a0a2c`) 已确立 owlmlx engineering ≠ OwlCoda consumer readiness。**OwlCoda 卡顿不延迟 owlmlx 主线** |
| **OwlMom** | 上层消费者（间接） | 5 Vue 页 FROZEN；数据走 OwlOps 聚合 |

**边界纪律**：

- 主规划任何 wave **不得**把 OwlRunKit / `llm_router` 的能力下沉到 owlmlx 内部模块
- 如需协作，仅通过 runtime-owned HTTP / contract surface
- 任何 `llm_router` → `owlmlx` 反向依赖视为 R12 风险事件

---

## Part V — 六大子战役 + 治理 + 拆分 Wave 的 12+ 月路线图

### Campaign A — Host-Stable Repeatability

- **目标**：把 `memory_discipline_baseline_missing`（master-outline §8 当前 dominant gap）转化为 N≥20 真实硬证据，证明 Gemma 4-31B-it / Qwen3.6-27B / Qwen3.6-35B-A3B 三条主线稳定可重复
- **近期闭环（0–3 月）**：A1 N≥20 + A2 seed-to-token + A3 reclaim stats 入 summary
- **中期（3–6 月）**：扩 Qwen3.6-35B-A3B + dirty recovery 覆盖
- **远期（6–12 月）**：纳入 DS4-Flash 2bit-DQ；RC1 达成
- **验收**：N≥20 跨 3 模型；TTFT CV<10%、TPS CV<20%；零 dirty post-run；ledger 连续

### Campaign B — Cache / Scheduler Depth

- **目标**：cache_manager 从 single-request gateway → real policy layer；不主张 continuous batching
- **当前**：`session_kv_cache.py` + `MlxNativeBackend` 实证 Qwen3.6-27B-4bit warm p50 TTFT **7.409×**；B-1a Gemma 4-31B-it RuntimeKernel 复现 **2.246×**，并通过 native/subprocess N≥5 UTF-8 byte equivalence

**近期闭环（0–3 月）· Session KV cache `supported` gate 四条**（升级语义：experimental → supported，**不是** partial 中转）：

#### B-1a · 第二模型 / 第二形状（决策 A1 · 2026-05-16）

**锁定 Gemma 4-31B-it** 作为第二模型复现 session KV warm TTFT 改善。

- **状态**：已通过 closeout（Gemma 4-31B-it RuntimeKernel 复现 2.246×，并通过 native/subprocess N≥5 UTF-8 byte equivalence）
- 绝对倍率不强求 7.4×，只要 hit / miss / eviction / TTL / restart 语义一致 + warm TTFT 单调改善
- **附加**（与 §VI G1 互锁，决策 C3）：包含"非 cache 路径下 generation tokens 字节等价 (N≥5 prompt)" 检查
- **B-1a 通过即视为 G1（Cache Parity）通过**——单一来源避免重复造证
- 理由：Gemma 4 同时为 Campaign F（spec safety）铺路；与 Qwen3.6 形状差异大，"第二形状"说服力强

#### B-1b · `cache=on` × settle barrier 无回归

- **状态**：passed（2026-05-17 native N=20 cache-off/cache-on）；`cache_on_no_regress = passed`
- **入口**：`uv run python scripts/bench/eviction_soak.py --gate b1b-cache-on-no-regress --backend native --rounds 20 --cache-mode both ...`
- N=20 跑后 `failed_reclaim = 0`（**不**走 N=10 探针）
- session KV 启用不在 unload 路径上引入 reclaim mismatch
- reclaim-barrier-event/stats 分布与 cache=off 基线对齐（中位数 / p99 / failed 计数）

#### B-1c · 长上线稳定 · 拆成两段 48h+（决策 D3 · 2026-05-16）

**B-1c §1 · 纯 soak（当前 Mac 路线 = 可中断分段累计 ≥24h；dedicated host 可追加 continuous 24h）**

- 混合负载：短 / 中 / 长 session = **1:1:1**
- **无人为 unload / swap**
- 验证单一命题："`cache=on` 不破坏 `active_memory`"
- 漂移阈值：`min(200 MB, 0.5% host budget)`
- 当前 Mac / laptop 路线：多个可中断 native segment 累计 ≥24h；每个 segment 内无 hard failure、无 measurement wall-clock gap、ledger index 连续、cleanup unload / settle 干净；聚合结论字段 `interrupted_no_swap_rehearsal = passed | failed | blocked`
- dedicated host / UPS 路线（可选更强证据）：单段 continuous ≥24h；额外产出 `no_swap_soak_stability = passed | failed`
- **不再假设当前 Mac 能 continuous 24h**；host sleep / power gap 是运行环境事实，必须被记录为 segment boundary 或 gap，不许被抹平

**B-1c §2 · soak + swap（≥24h，§1 通过后启动）**

- §1 基础上每 4h 一次 model swap（Qwen3.6-27B ↔ Gemma 4-31B ↔ Qwen3.6-35B-A3B 轮换，共 6 次）
- 验证累积切换 reclaim 在 24h 上下文下行为干净
- 验收：每次 swap 后 settle_barrier 通过 + `failed_reclaim` 累积 = 0 + `active_memory` 漂移 < §1 阈值
- 任意一次 swap 触发 watermark→FATAL 即整条 §2 失败
- **结论字段**：`soak_plus_swap_stability = passed | failed`（独立陈述）

**两段编排纪律**：

1. §1 的当前 Mac 路线达到 `interrupted_no_swap_rehearsal = passed` 且 `current_mac_section_1_prerequisite_met = true` 后才启动 §2 native execution；若未来拿到 dedicated host / UPS，`no_swap_soak_stability = passed` 可作为更强证据补充
2. **§2 失败不撤销 §1 结论**——当前 Mac 的 `interrupted_no_swap_rehearsal = passed` 或 dedicated host / UPS 的 `no_swap_soak_stability = passed` 都作为独立事实保留；但 supported / release gate **不能 graduate**（gate 要求 §1 + §2 同时 passed 且经 §1a Promotion Gate）
3. §1 与 §2 各自产出**独立 ledger**，不混合（防归因混淆，R14）
4. **不允许**"§1 §2 合并跑 36h"假装通过 48h；**不允许**"§1 失败重启后接续 §2"——§1 失败时 §2 必须重头
5. 总占用 ≥48h host 时间，建议夜间 / 周末启动

#### B-1 supported 晋级条件

**四条全部** passed：

- `B-1a · second_model_byte_equiv = passed`
- `B-1b · cache_on_no_regress = passed`
- `B-1c §1 · interrupted_no_swap_rehearsal = passed`（current Mac 的 §2 前置）或 `no_swap_soak_stability = passed`（dedicated host / UPS continuous 更强证据）；任一 §1 结论都不单独 promotion
- `B-1c · soak_plus_swap_stability = passed`

当前状态：**3/4 前置推进**（B-1a、B-1b、B-1c §1 current-Mac interrupted prerequisite 已过）；B-1c §2 token-boundary / unknown-drop / over-budget-drift 已收窄到 prompt-reset candidate，首条 swap-bearing segment 的功能子指标 clean，但 wall-clock continuity 失败，不能计入 aggregate。仍需 gap-free 4h fail-fast segments × 6 / aggregate ≥24h；未进入 supported 晋级判断。

加 §1a Promotion Gate + `extraction-inventory.md` §8 → session KV cache 行从 `experimental` 升 `supported`。

#### Campaign B · 其他近期闭环（0–3 月）

- B2：cache_manager 退出 scaffold-only，按 `release-floor-3-1-cache-scheduler-capability-audit.md` 选 1–2 个 extension point 实装；**不**实装跨用户共享
- B3：scheduler_admission 加入 prefill warmup 决策权（与 Campaign C 联动）

#### Campaign B · 中期 / 远期 / 跨战役

- **中期（3–6 月）**：workspace-aware safety boundary；session TTL/驱逐契约
- **远期（6–12 月）**：跨模型版本 invalidation；prefix-cache 跨会话探针（status surface only）；量化-cache 共享可行性
- **跨战役**：依赖 Campaign A（共用 N≥20 harness）；为 Campaign C/F 提供 cache 状态契约；**B-1 supported 晋级是 RC2（owlmlx native-only 能力）的最早期到达项**；B-1a 通过同时关闭 §VI 4-gate G1
- **与 Campaign D 编排（决策 E3）**：D 不与 B-1a 抢资源；D1 启动时点 = B-1a 完成后

### Campaign C — Qwen3.6 / Gemma 4 主线 TTFT Default-Path Optimization

- **目标**：把 cold-first-response 五因素分解（load / template / prefill / first decode / thinking-profile）；warmup 从 experimental 升 default；解除 Qwen3.6-35B-A3B / gemma-4-31B-it 的 `needs_optimization` verdict
- **近期闭环（0–3 月）**：C1 五因素 instrument + C2 warmup default-on + C3 thinking-mode 对比
- **中期 / 远期**：扩 Gemma 4 reasoning channel；≥3 主线 verdict 解除 → 支持 RC1
- **验收**：warmup default-on；≥1 主线 verdict 升 `ready`（按 §1a）

### Campaign D — DeepSeek V4 Family Bring-Up（隔离 backend hardening）

- **目标**：DS4-Flash 2bit-DQ 从短烟测提升到"可重复验证 + clean health + load→generate→unload→clean health 全链"；**不**进入默认 model surface
- **启动时点（决策 E3）**：D1 启动时点 = **Campaign B-1a 完成后**（host 进入 B-1b N=20 跑期间，DS4 隔离 venv 并行启动；不污染主 venv，主要竞争 CPU/GPU 时段）
- **近期闭环（0–3 月，B-1a 完成后）**：
  - D1：同 isolated runtime 连续 5 次 prompt 无重启；max_tokens 阶梯 (128/512/1024) coherence / 重复 / 停止符。**当前状态**：passed under adopted `messages` prompt policy；formal default run `20260517T-d1-full-ladder-adopted-messages-policy.jsonl` completed 15/15 rows with `repetition_flag=false`, clean load/unload health, and no restart. Raw prompt p1/1024 remains a diagnostic failure and is not the accepted surface.
  - D2：load time / TTFT / decode TPS / child-process RSS sample / backend health 完整 ledger。**当前状态**：passed for p1/p2/p4 × 128/512 after replacing blocking `readline()` child stdout handling with fd-buffered reads; evidence `20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl` records 6/6 passed rows, TTFT p50 593.840ms, decode p50 38.17885 tok/s after first token, child-process RSS p50 7.214432GB (not peak/process-tree aggregate), clean unload. DeepSeek remains experimental-only.
  - D3：checkpoint MTP 权重检查。**当前状态**：passed as inspection gate; evidence `20260517T-d3-mtp-checkpoint-inspection.jsonl` records `num_nextn_predict_layers=1`, no `mtp` / draft / speculative weight keys, no extra layer keys beyond `num_hidden_layers=43`, and `missingReason=mtp_weights_absent_or_stripped`. This is not a DeepSeek MTP serving claim.
  - D4：失败必须 clean pre-load reject，不污染 8066 runtime health。**当前状态**：passed; evidence `20260517T-d4-mtp-clean-preload-reject.jsonl` records `decision=rejected_pre_load`, `reason_code=mtp_weights_absent_or_stripped`, `load_attempted=false`, `child_process_started=false`, and stable 8066 `/healthz` before/after. This proves failure isolation, not DS4 native MTP serving.
- **中期 / 远期**：第二 DS4 variant；upstream mlx_lm `deepseek_v4` 合并跟踪；RC2 支撑
- **验收**：5×连续无重启通过；ledger 完整；失败链 clean；progressive max_tokens 通过

### Campaign E — OwlOps Internal Consumption Closed Loop

- **目标**：runtime-owned monitor / metrics / test-runs / bottleneck classifier 持续把 live data 喂给 OwlOps；OwlMom Wave 8 UI 决策与本战役分离
- **近期闭环（0–3 月）**：E1 reclaim-barrier stats 入 release/report + E2 TTFT 五因素入 test-runs + E3 bottleneck classifier 端点
- **中期 / 远期**：spec accept/reject ratio + tool-arg 完整性 metric；RC3 支撑
- **验收**：3 个 campaign metric 在 OwlOps live；live ledger >90 天连续无 gap；bottleneck classifier partial 晋级

### Campaign F — Speculative Path Safety + Structured-Output Invariance（第 6 子战役）

- **目标**：在不破坏 capability honesty 前提下建立 runtime-owned `speculative_execution_status` surface 与正交测试矩阵；证明 spec 路径下 tool calling / structured output / thinking-tag 闭合 bit-for-bit 不变
- **当前**：F1 `speculative_execution_status` diagnostic surface 已落地（F-1.2 endpoint + F-1.3 kernel observe APIs + fixture evidence `20260525T142617Z`），endpoint self-promotion 仍未执行；F2 n-gram/suffix C0/C1 已过但 C2 serving integration paused on mlx-lm hybrid trim；F4 Structured-Output Invariance 已归档窄 grammar lane `partial`（Qwen × JSON/enum/function_call/nested-object），F-4 整体仍 `experimental`；`assistant_drafter` 仍为 experimental，MTP serving 正交矩阵尚无 promotion evidence
- **近期闭环（0–3 月）**：F1 `speculative_execution_status` runtime-owned contract + F2 n-gram/suffix probe (Round 0) + F4.0 validator / F4.1 smoke matrix + F3 Gemma 4 resident MTP A/B（待 drafter / trim blocker 解除后恢复）
- **中期（3–6 月）**：F4 正交矩阵 ≥20 case + F5 draft constraint checker + F6 MTP+session KV combo
- **远期（6–12 月）**：F7 DS4 native MTP path + F8 主 serving 受控启用 + F9 RC2 强支撑
- **验收**：`speculative_execution_status` 端点 supported；正交矩阵 ≥20 case 通过；F4 矩阵 N≥1000 随机测试破坏率 <0.1%

### Wave G — Governance Refresh

- **目标**：消除文档-代码漂移；扼制 phase45 递归命名扩散；6 子战役契约语义统一；刷新 README 对 vMLX / spec posture 的表述；刷新 ARCHITECTURE-TRUTH §2.2 + product-definition §11
- **近期闭环（0–3 月）**：G1 ARCH-TRUTH §2.2 刷新 + G2 product-def §11 正式声明 + G3 README 刷新（vMLX 边界 + port 8066 + spec posture）
- **中期 / 远期**：G4 phase45 命名扩散治理 + G5 runtime-contracts.md 统一 + G6 backends.py 异构 hook 注释
- **验收**：ARCH-TRUTH §2.2 与代码扫描漂移 <1 周；product-definition §11 已立；phase45 #114–#128 类递归命名归档或合并；runtime-contracts.md 包含 6 子战役新增契约

### Wave H — Runtime Server 工程化拆分（Maintainability · 新设）

- **目标**：`owlmlx/runtime/server.py`（原 2807 行；H1 后约 2013 行）按职责拆分；**保持 HTTP / SSE / contract bit-for-bit 不变**；服务 runtime 代码可维护性，**不**为治理 metric 好看
- **节奏（决策 B1 · 2026-05-16）**：
  - **H1 已完成（2026-05-16）**：`server_routes_openai.py` —— OpenAI / Anthropic 兼容 endpoint + SSE 序列化已从 `server.py` 拆出；targeted route / hardening tests 通过
  - **H2 等 B-1 闭环后**：`server_routes_runtime.py` —— `/v1/runtime/*` status surface（理由：B-1 会向 status surface 加 hit/miss metrics + soak 端点，先稳定 B-1 再拆 H2）
  - **H3 与 H2 同期**：`server_routes_dev.py` —— test-console / admin / dev-only
- **中期 / 远期**：H4 envelopes 共享 helper + H5 contract 零回归测试
- **验收**：全套 835 test 通过；`server.py` ≤ 1200 行；新端点不回灌 server.py
- **反规模化约束**：拆分模块**不得**包含 `*_exactness` / `*_carrier` / `*_marker` / `*_harness` / `*_feasibility` / `*_rung` / `*_seam` / `*_charter` 命名

---

## Part VI — `mlx_native_backend.py` 战略处置（4-gate Promote-Path）

`mlx_native_backend.py` 1074 行，server.py:2088 显式承认 `"scope": "native_backend_explicit_session_id_only"`；正在产出真实证据（Qwen3.6-27B-4bit warm p50 TTFT 7.409×）。

**架构师裁定：保留并按 4-gate 阶梯条件化晋级**（不 decommission，也不冻结）。

| Gate | 条件 | 对应 Campaign | 时间窗 |
|---|---|---|---|
| **G1: Cache Parity** | session KV 在 native 上 hit/miss/eviction/TTL/restart 语义与 subprocess 等价 + 非 cache 路径 generation tokens 字节等价 N≥5 prompt。**通过条件 = B-1a 通过**（决策 C3） | Campaign B-1a | 0–3 月 |
| **G2: Reclaim Verified** | settle barrier 在 native 上经验证；reclaim-barrier-event/stats 对 native unload 同样 hardened | Campaign A-3、Campaign B | 0–6 月 |
| **G3: Structured-Output Invariance** | tool calling / JSON schema / thinking-tag 闭合在 native 路径上与 subprocess 字节等价；正交矩阵 ≥20 case 全过 | Campaign F-4、F-5 | 3–9 月 |
| **G4: Speculative Path Landing** | spec 在 native 上稳定运行（resident MTP / n-gram）；F4 矩阵未破坏；DS4 native MTP path 跑通 | Campaign F-7、F-8 | 6–12 月 |

四个 Gate 全过 → `experimental` 升 `partial`；再经跨 host 重复运行（外部 reopen condition 触发期）方可升 `supported`。期间 subprocess backend 保留为 **fallback**。

**关键纪律**：

- Wave G 的 README 刷新中**不**预先宣告 native backend 将成默认
- **不允许**"G1–G4 未达但 ROI 太诱人先放开默认"的越级
- 任何 Gate 推进必须经 §1a Promotion Gate

---

## Part VII — 风险登记（Risk Register）

| # | 风险 | 概率 | 影响 | 控制 |
|---|---|---|---|---|
| R1 | Spec-as-code regrowth | 高 | 高 | CI `self-banned-modules.yml`；月度 grep 巡检 |
| R2 | Phase45 递归命名扩散 | 高 | 中 | Wave G-4 文档命名约束 |
| R3 | Capability label inflation | 中 | 极高 | §1a Gate 强制；evidence-language calibration |
| R4 | Native backend strand drift | 中 | 高 | §VI 4-gate 绑定 Campaign B/F |
| R5 | Strategic ambiguity（"内部 vs 发版"） | 中 | 中 | release-channel split (`a21a0a2c`) 已立 |
| R6 | Spec path footgun | 高 | 极高 | Campaign F-4/F-5 矩阵 + draft constraint checker |
| R7 | Apple FM 市场挤压 | 低 | 中 | §IV.1/IV.4 "Apple FM 之上的企业级 runtime"定位 |
| R8 | DS4 上游 mlx_lm 集成漂移 | 中 | 中 | `.runtime-deepseek-v4-mlx` 隔离 |
| R9 | 5 周文档漂移持续累积 | 高（已发生） | 中 | Wave G 持续约束 |
| R10 | OwlCoda 消费就绪 gate 卡顿 | 中 | 中 | §IV.5 已明确"不在主线" |
| R11 | `server.py` 单文件膨胀 | 高 | 中 | **Wave H 拆分**；H1 已把 OpenAI/Anthropic compat routes 拆到 `server_routes_openai.py`；H2/H3 后续推进；CI 行数 lint |
| R12 | `llm_router` 被误当主线 | 中 | 高 | §IV.5 transitional；不向 `llm_router` 借入或反向依赖 |
| R13 | Session KV gate **四条**偏短跑（B-1a + B-1b + B-1c §1 + B-1c §2） | 高 | 极高 | 必须**全部**满足；§1 / §2 独立 ledger；§2 必须 §1 通过后启动；**不允许**合并跑或缩短；B-1c §1 需要 ledger index + wall-clock continuity 双重连续 |
| R14 | B-1c §2 swap 失败归因混淆 | 中 | 高 | §1 / §2 独立 ledger；§2 失败不回溯 §1；归因清单（swap 触发 vs cache 长跑） |
| R15 | Wave H 拆迁中 contract 回归未发现 | 中 | 高 | 全套 835 test 强制通过；拆分 PR 分 "move only" / "behavior" 两轮 review |

---

## Part VIII — 验收与证据语言

### VIII.1 通用验收方法

- **复用现有 harness**（不新建）：
  - `tests/test_repeatability_campaign_harness.py` —— Campaign A
  - `owlmlx/comparative_evidence_runner.py` —— Campaign B/C/D
  - `owlmlx/repeatability_statistics.py` —— 共享 CV / stability_label
  - `scripts/bench/eviction_soak.py` —— B/A soak baseline
- **Promotion 路径**：`extraction-inventory.md` §8 + `native-mlx-backend-capability-matrix.md` §1a 双重 gate

### VIII.2 证据语言四档

| 状态 | 语言 |
|---|---|
| 未经执行的源代码检视 | ❌ 不写 "supported" / "loadable"；写 "load-path-compatible" |
| Source-read 但未执行 | "load-path-compatible" / "likely-admissible-pending-load" |
| 已执行但未做 N≥20 重复 | "plausible outcome" / "experimental smoke" |
| N≥20 + §1a 全过 | "supported" |

### VIII.3 工程纪律

- **Staging discipline**：每 wave 提交集严格本 wave scope；不 sweep 不相关 dirty 编辑
- **不新增 spec-as-code 模块**（AGENTS.md Stage 1 禁令）
- **每个 wave 完成时反推文档刷新**（Wave G 持续约束）
- **层级 handoff**：plan-grade → 用户复核 → 修订定版 → design-grade → 复核 → 代码（**不允许跳级**）

---

## Part IX — Re-Open Release Conditions

| # | 条件 | 对应 Campaign | 估计达成时点 |
|---|---|---|---|
| RC1 | ≥3 主线 model family N≥20 repeatability 证据 | A + C + D | 6–9 月 |
| RC2 | ≥1 owlmlx 自有、超出 stock `mlx_lm`（load+generate）的能力（建在 `mlx_lm` 之上但提供其不具备的能力；措辞修正见 `product-definition.md §11.4`） | B（session KV）+ F（spec safety on native）+ D（DS4 native MTP） | 9–12 月 |
| RC3 | OwlOps 稳定消费 live runtime truth 并形成内部 operational 闭环 | E | 6–9 月 |

**全部 3 条同时满足最早合理窗口**：**2026-11 ~ 2027-01**（6–8 个月）。

诚实预测，不承诺，不动员；任何加速尝试不得通过越级 promotion 实现。

---

## 关键文件参考

| 类别 | 文件 |
|---|---|
| 顶层契约（Wave G 刷新） | `docs/source-of-truth/ARCHITECTURE-TRUTH.md` / `product-definition.md` / `master-outline.md` / `README.md` / `AGENTS.md` |
| 能力矩阵与晋级 gate | `docs/source-of-truth/runtime-capability-matrix.md` / `native-mlx-backend-capability-matrix.md` / `extraction-inventory.md` |
| 架构与治理 | `docs/source-of-truth/system-architecture.md` / `ownership-boundary.md` / `runtime-governance.md` / `hazardous-operations.md` |
| 核心 runtime 代码（A–E 主战场） | `owlmlx/runtime/server.py` / `kernel.py` / `mlx_lm_subprocess_backend.py` / `mlx_native_backend.py` / `owlmlx/session_kv_cache.py` / `cache_manager.py` / `scheduler_admission.py` / `memory_pressure_eviction_policy.py` / `memory_watermark.py` / `settle_barrier_event.py` |
| Campaign F 主战场 | `owlmlx/gemma4_mtp_drafter.py` / `runtime/mlx_vlm_mtp_runner.py` / `docs/source-of-truth/ds4-mtp-local-llm-stack-research.zh-20260514.md` |
| 测试与证据 harness（复用，不新建） | `tests/test_repeatability_campaign_harness.py` / `owlmlx/comparative_evidence_runner.py` / `repeatability_statistics.py` / `scripts/runtime_repeatability_campaign.py` / `scripts/bench/eviction_soak.py` |
| 释放渠道与消费契约 | `docs/source-of-truth/public-release-standard.md` / `public-developer-preview-readiness.md` / `public-surface.md` / `model-release-candidate-program.md` / `owlcoda-learning-loop-coordination.md` |

---

## 写在最后（架构师立场）

owlmlx 不是 vMLX 的竞争者、不是 vllm-mlx 的复刻、不是 LM Studio 的开源版。它是为 **Apple Silicon 单机企业级 agentic / batch evaluation 场景**而生的 **memory-discipline-first replacement-grade MLX runtime**，差异化轴是 **Reliability + Provenance + Governance**，不是 raw throughput。

在 12 维框架中：

- **#2 / #6 / #11** 已 strong
- **#1 / #3–#8** 处于 partial，正按计划深化
- **#9 / #10** 是当前最大空白，也是相对于开源 runtime 最容易做出差异化的机会
- **#12** 是远见预留位

按本规划 6 子战役 + Wave G + Wave H 推进，**6–8 个月窗口**内具备 reopen 公开发版条件的 plausible 路径。不承诺时点，不放松证据语言纪律，不允许越级晋级。
