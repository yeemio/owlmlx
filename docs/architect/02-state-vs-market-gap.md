# owlmlx 现状 vs 市场差距清单

> **文档 grade**：plan-grade · 见 [README.md](README.md)
> **配套**：[01-mainline-roadmap.md](01-mainline-roadmap.md) / [03-real-accomplishments.md](03-real-accomplishments.md) / [04-architecture-canvas.md](04-architecture-canvas.md)
> **日期**：2026-05-25
> **视角**：架构师诚实评估，对外参照 2025–2026 Apple Silicon LLM 栈与本地 LLM runtime 业界事实

---

## 0. 阅读约定

- **状态标签**：✅ strong / 🟡 partial / 🟠 scaffold-only / 🔴 missing or not-in-scope
- **差距分级**：
  - **L0**：业界事实标准，owlmlx 缺失 → 必须明确"刻意不做"还是"技术债"
  - **L1**：业界主流已实装，owlmlx scaffold / partial → 路线图明确目标
  - **L2**：业界论文级或前沿，owlmlx 与业界同处探索期 → 潜在差异化窗口
  - **L3**：业界与 owlmlx 都不主要投入 → 远期预留位

---

## 1. 维度层差距（12 维框架对照）

| # | 维度 | owlmlx 当前 | 业界 hardened 参考 | 差距 | 落后时窗 |
|---|---|---|---|---|---|
| 1 | Repeatability | 🟡 harness 实装；无 N≥20 硬约束；无 seed-to-token 字节一致测试 | vLLM/SGLang seed 管理 | **L1** | 6–12 月 |
| 2 | Capability Honesty | ✅ Stage 1 已清 spec-as-code（151 模块/31K LOC）；CI 强制；§1a Gate | Anthropic API 功能矩阵 | **同业界或领先** | — |
| 3 | Cache Depth | 🟡 session-level reuse 已有 TTFT 证据（7.409× / Gemma 2.246×）且 B-1a/B-1b/§1 prerequisites 已过；B-1c §2 仍卡在 trim-bypass drift | vLLM prefix caching v0.6+；TurboQuant 量化 KV | **L1** | 12–18 月 |
| 4 | Scheduler Depth | 🟡 admission contract 完整；prefill warmup 未 default；负载自适应未实装 | vLLM continuous batching；SGLang structured generation | **L1**（但 owlmlx 明确不追 batching） | 单 worker 场景 6 月 |
| 5 | Admission / Eviction | 🟡 完整决策 + pinned 保护 + TTL；无 background loop（明确约束） | vLLM eviction；AWS SageMaker | **同业界** | — |
| 6 | Status & Provenance | ✅ request lifecycle 维度 strong；🟡 spec accept/reject 维度缺 | Anthropic usage；OpenTelemetry | **L1（spec 维度）** | spec 路径 6–12 月 |
| 7 | Failure Cleanliness | 🟡 recovery_supervisor / settle_barrier / child probe / restart supported | K8s phase；vLLM 稳定边界 | **同业界** | — |
| 8 | Multi-Model Lifecycle | 🟡 pin/TTL/eviction supported；model_lineage supported；缺 hot-swap | mlx-knife 2.0.5；vLLM 多端点 | **L1** | 6 月 |
| 9 | Speculative Path Safety | 🟠 gemma4_mtp_drafter probe；spec_method status 缺；正交矩阵无 | 业界普遍未解决（vLLM #41967；ToolSpec arXiv 2604.13519 2026 才出） | **L2** | 与业界同处探索 |
| 10 | Structured-Output Invariance | 🔴 runtime 不主动验证 JSON/tool schema 不变性 | Claude API guaranteed | **L2** | 业界仅 Anthropic 真正 hardened |
| 11 | OwlOps Consumption | ✅ 27 行 ledger live；test-runs / model-rc / evidence history live | vLLM Prom；Ray Serve | **同业界领先** | — |
| 12 | Heterogeneous Compute (GPU/CPU/ANE) | 🔴 not in scope | 业界整体未解决 | **L3** | 与业界同处空白 |

**统计**：✅ 3 维 / 🟡 7 维 / 🟠 1 维 / 🔴 2 维

---

## 2. 产品 / 品类层差距

### 2.1 vs vMLX（vmlx.net · Apple 官方背书全栈）

| 维度 | vMLX | owlmlx 当前 | 差距 |
|---|---|---|---|
| 单机 OpenAI / Anthropic API | ✅ 全栈 | ✅ supported | 平 |
| 内置工具调用层（20+ tools） | ✅ 内置 | 🔴 不内置 | **场景边界差异**（owlmlx 把工具层让给 OwlCoda） |
| Speculative decoding | ✅ 已集成 | 🟠 scaffold | **L1** 落后 |
| Quant 路线（FP4/FP8/TurboQuant） | ✅ 已集成 | 🟡 借用 mlx-lm | **L1**（不追自有） |
| Memory governance (watermark/settle) | 🔴 无显式 | ✅ supported（PR #649） | **owlmlx 领先** |
| 内部 OwlOps 消费契约 | 🔴 N/A | ✅ 27 行 ledger | **不可比** |
| Capability honesty + promotion gate | 🔴 无 | ✅ §1a Gate + CI 禁令 | **owlmlx 领先** |

**结论**：vMLX = throughput-first + 全栈一体化；owlmlx = memory-discipline-first + 内部消费者契约闭环。**不竞争 raw throughput，竞争 reliability + governance**。

### 2.2 vs vllm-mlx（waybarrios/vllm-mlx · 社区端口）

| 维度 | vllm-mlx | owlmlx 当前 |
|---|---|---|
| Continuous batching | ✅ 已实现 | 🔴 not in scope（明确选择） |
| Paged KV cache | ✅ 已实现 | 🔴 not in scope |
| 吞吐对比 llama.cpp | +21–87% | N/A（场景不同） |
| 单 host 单 worker 场景 | 🟡 非核心 | ✅ 主战场 |
| Memory watermark / settle barrier | 🔴 无 | ✅ supported |

**结论**：vllm-mlx 在 multi-host / 多并发批量推理场景已是参考；owlmlx 不追，但 Wave G 文档刷新需明确"continuous batching not in scope **是刻意选择，不是 gap**"。

### 2.3 vs Ollama / LM Studio / Jan / Cortex（消费级 runtime）

| 维度 | Ollama / LM Studio | owlmlx 当前 |
|---|---|---|
| GUI / 一键安装 | ✅ | 🔴 not in scope |
| GGUF 生态 | ✅ 标准 | 🔴 不接 GGUF |
| 模型 catalogue / 下载 | ✅ 内置 | 🔴 让给 mlx-knife / OwlRunKit |
| Multi-model concurrency | 🟡 串行切换 | ✅ pin/TTL/eviction supported |
| 企业级可观测 | 🔴 minimal | ✅ /v1/runtime/* full |
| Tool calling reliability under quant | 🟡 无保证 | 🟡 Campaign F 路线图 |

**结论**：消费级"通用本地推理"已饱和；owlmlx 不进入红海，定位"企业级 agentic / batch evaluation"，**不交叉**。

### 2.4 vs Apple Foundation Models / Tahoe（OS 层方案）

| 维度 | Apple FM | owlmlx 当前 |
|---|---|---|
| 调用入口 | macOS 原生 API | HTTP gateway port **8066** |
| 模型来源 | Apple Intelligence 同源 | HuggingFace / 自训练 |
| 多模型编排 | 🔴 单一模型 | ✅ supported |
| 微调 / 训练后部署 | 🔴 不支持 | ✅ training-to-serving contract supported |
| 企业级 SLA / 可观测 | 🔴 不支持 | ✅ /v1/runtime/* full |
| 隐私 / 完全本地 | ✅ on-device | ✅ on-device |

**结论**：Apple FM **不是**竞争者，是 owlmlx 的护城河延伸。owlmlx 占据"Apple FM 之上的企业级 runtime"位置；远期 hook 把 Apple FM 视作 substrate-class 选项。

### 2.5 vs oMLX（参考系统 · replacement target）

| 维度 | oMLX | owlmlx 当前 |
|---|---|---|
| Apple Silicon multi-host fleet | ✅ 主战场 | 🔴 not in scope |
| 单 host 内 runtime control boundary | ✅ 既有 | 🟡 Runtime-9 verdict "not yet replaceable"；Runtime-12 doctor emit 明确 blocker |
| Memory governance | 🟡 patches | ✅ PR #649 对齐 supported |
| Replacement 含义 | — | 替代 oMLX 作为 **runtime control boundary**（不是替代每行代码） |

**结论**：owlmlx 的 "replace oMLX" = **boundary 层替代**——runtime control 从 platform-side 收归 owlmlx-side。当前 verdict "not yet replaceable" 是 12+ 月路线图核心目标。

### 2.6 vs OwlRunKit（lifecycle / env broker 候选位 · 非 owlmlx 内）

| 维度 | OwlRunKit（候选） | owlmlx 立场 |
|---|---|---|
| `.runtime*-mlx` venv 切换 | ✅ 该承担 | 🔴 owlmlx 不实装；只暴露 `mlx_environment` 探测 |
| 模型 artifact 下载 / HF pull | ✅ 该承担 | 🔴 owlmlx 不实装；可参考 mlx-knife |
| host preflight 触发 | ✅ 该承担 | ✅ owlmlx 暴露 `pre_load_check` / `host_pressure` contract |
| 模型 lineage 维护 | 🟡 协作 | ✅ owlmlx 拥有 `model_lineage`，OwlRunKit 读取 |
| HTTP serving | 🔴 不该承担 | ✅ owlmlx 拥有 |

**结论**：OwlRunKit 是 owlmlx 之外的 lifecycle/env broker 候选位，**不是** owlmlx 扩展。任何把 broker 能力下沉到 owlmlx 内部的 PR 视为 §IV.5 边界违规。

### 2.7 vs `llm_router`（过渡资产 · transitional）

| 维度 | `llm_router` | owlmlx 立场 |
|---|---|---|
| 当前承担 | 几条本地 runtime 之间路由切换 | — |
| 是否 owlmlx mainline | 🔴 **不是** | — |
| 是否替代 owlmlx | 🔴 **不是** | owlmlx replacement-grade 后逐步**接管或被 OwlOps 上收** |
| 主规划依赖 | 🔴 不依赖 | 任何 wave 不向 `llm_router` 借入或反向依赖 |
| 退出条件 | RC2 达成后逐步退役 | — |

**结论**：`llm_router` 是历史路由资产。**主规划不为它做兼容、不为它扩展**。退役不由 owlmlx 主线驱动，是 OwlOps 上收或 owlmlx replacement-grade 后的自然结果。

---

## 3. 特定能力层差距

### 3.1 Speculative Decoding 家族

| 能力 | 业界状态 | owlmlx 当前 | 立场 |
|---|---|---|---|
| MTP（DeepSeek V3/V4 native） | ✅ 平台化 | 🟠 Gemma 4 probe；DS4 MTP 未触 | Campaign F |
| EAGLE-2 / EAGLE-3 | ✅ 平台化（2.3–6×） | 🔴 未触 | Campaign F watch |
| P-EAGLE | 🟡 早期实装 | 🔴 | schema 预留字段 |
| Medusa | ✅ 平台化 | 🔴 | 不追 |
| n-gram / suffix decoding | 🟡 主流低优先 | 🔴 | **Campaign F Round 0 第一站** |
| `speculative_execution_status` runtime-owned | 🔴 业界普遍无 | 🔴 | **Campaign F-1 立即建** |
| Spec × tool calling reliability | 🔴 (vLLM #41967) | 🔴 | **Campaign F-4/F-5** |
| Spec × structured output bit-for-bit | 🔴（Claude API 之外业界普遍无） | 🔴 | **Campaign F 核心差异化** |

### 3.2 KV Cache 管理

| 能力 | 业界状态 | owlmlx 当前 | 立场 |
|---|---|---|---|
| Prefix caching 跨请求 | ✅ vLLM v0.6+ | 🟠 cache_manager scaffold | Campaign B-2 |
| Prefix caching workspace 隔离 | ✅ Anthropic 范式 | 🔴 | Campaign B 中期 |
| 跨模型 prefix 共享 | 🟡 PrefillShare 论文级 | 🔴 | 远期 status surface |
| Session-level append-only 复用 | 🟡 各 runtime 差异大 | 🟠 experimental（TTFT + no-regress prerequisites 强；§2 stability 未过） | **owlmlx 有差异化证据，但未 supported** |
| Tail-edit / trimmable cache | 🟡 部分支持 | 🟡 reason-code instrumentation + safe trim bypass；频繁 fallback drift 未闭合 | Campaign B-1 §2 当前 blocker |
| KV 量化（TurboQuant 3-bit / PolarQuant） | ✅ mlx-lm/mlx-vlm 生产 | 🟡 借用上游 | 不追自有 |
| KV offload to disk | 🔴 业界都未做 | 🔴 | 不追 |

### 3.3 Continuous Batching / Paged Attention

| 能力 | 业界状态 | owlmlx 立场 |
|---|---|---|
| Continuous batching | ✅ vLLM/SGLang/TRT-LLM 标准 | **🔴 not in scope 刻意不做**（单 worker by design） |
| Paged KV cache | ✅ vLLM 2023 起 | **🔴 not in scope 刻意不做** |
| Chunked prefill | ✅ vLLM | 🔴 不追 |
| Disaggregated prefill-decode | 🟡 vLLM 0.7+ experimental | 🔴 不追 |

**L0 类差距但 owlmlx 明确选择**。Wave G-3 README 刷新需强化此表述。

### 3.4 Multi-Model & Lifecycle

| 能力 | 业界状态 | owlmlx 当前 | 立场 |
|---|---|---|---|
| Model registry 版本化 | ✅ mlx-knife / vLLM 多端点 | 🟡 model_lineage + model_release_candidate supported | Campaign E |
| Hot-swap 灰度 | ✅ vLLM 多端点 | 🔴 | Campaign B/E 中期 |
| TTL 驱逐 | ✅ vLLM | ✅ supported | 平 |
| Eviction history ledger | 🟡 部分支持 | ✅ supported（runtime-owned） | **owlmlx 领先** |
| 模型供应链溯源（HF commit SHA） | 🟡 mlx-knife 部分 | ✅ model_lineage supported | **owlmlx 领先** |
| A/B / 金丝雀部署接口 | 🟡 部分 | 🔴 | 中期 |

### 3.5 Quantization & MoE

| 能力 | 业界状态 | owlmlx 当前 | 立场 |
|---|---|---|---|
| FP4 / FP8 mixed precision | ✅ DeepSeek V4 / mlx-lm | 🟡 借用 | 不追自有 |
| TurboQuant KV / PolarQuant 3-bit | ✅ mlx-lm/mlx-vlm 生产 | 🟡 借用上游 | 不追自有 |
| MoE 1.6T / 49B 激活 | ✅ DeepSeek V4-Pro | 🔴 Apple Silicon 不适合 | 不追，但 backend Protocol 预留 sparse-dispatch hook |
| Hybrid attention (CSA / HCA) | ✅ DeepSeek V4 | 🔴 不实装 | 不追 |
| Mamba / SSM hybrid | 🟡 论文级 | 🔴 不实装 | 不追 |

---

## 4. 时间维度差距（业界领先窗口）

| 落后窗口 | 差距点 | 主规划应对 |
|---|---|---|
| **业界领先 12–18 月** | Prefix caching 跨请求复用；KV 量化生产 | Campaign B 中期补部分；KV 量化不自做 |
| **业界领先 6–12 月** | N≥20 repeatability gate；Multi-model hot swap；spec status surface | Campaign A/B/E/F 路线图 0–6 月 |
| **业界领先 6 月** | mlx-knife 集成；session TTL 显式契约 | Campaign B 中期 |
| **同业界（同处探索）** | Spec × structured output / tool calling reliability；Apple Silicon 异构计算 | **Campaign F 最大差异化窗口** |
| **owlmlx 领先** | Memory watermark + settle barrier (PR #649)；evidence-language 纪律；§1a Gate；runtime-owned eviction history；model_lineage 溯源；27 行 OwlOps ledger | 保持 |

---

## 5. 总差距判断

### 5.1 必须追的差距（L1 · 进路线图）

1. **N≥20 repeatability 硬约束**（Campaign A）
2. **Cache depth 跨请求 prefix**（Campaign B）
3. **prefill warmup default-on**（Campaign C）
4. **DS4 native lifecycle 闭环**（Campaign D）
5. **OwlOps 消费 spec/cache metric**（Campaign E）
6. **Spec × structured output 不变性**（Campaign F）

### 5.2 可选差异化窗口（L2 · 潜在领先）

1. **Spec path safety 正交矩阵 + draft constraint check**（业界普遍未防护）
2. **Workspace-aware safety boundary**（业界 Anthropic 之外少见）
3. **Apple Silicon 异构计算扩展点**（业界整体未驾驭）

### 5.3 刻意不追的差距（明确选择）

1. **Continuous batching / paged KV / chunked prefill**（与单 worker by design 冲突）
2. **GGUF 生态 / 消费级 GUI**（与企业级定位冲突）
3. **自有 quant pipeline / 自有 KV 量化算法**（mlx-lm 上游已饱和）
4. **MoE 1.6T 类超大模型**（Apple Silicon 物理限制）
5. **Hybrid Mamba / SSM 模型架构创新**（不属于 runtime 层）

### 5.4 远期预留（L3 · hook only）

1. **Apple Foundation Models 集成**（backend Protocol hook）
2. **GPU/CPU/ANE 异构 spec draft-target 分工**（status schema 字段预留）
3. **跨模型 prefix 共享**（PrefillShare 类前沿，等业界先落地）

---

## 6. 一句话总结

> owlmlx 目前在"raw throughput"和"业界标准能力数量"上**落后业界主流 runtime 6–18 月**，但在"memory governance"和"capability honesty 治理"上**与业界并行或领先**，且在"speculative path 下结构化输出可靠性"上**占据业界普遍未防护的差异化窗口**。
>
> 12+ 月路线图目标 = close 必要 L1 差距 + 占据 L2 差异化窗口 + 坚守刻意不追的边界。
