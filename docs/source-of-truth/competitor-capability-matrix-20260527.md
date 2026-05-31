# Competitor Capability Matrix Refresh — 2026-05-27

> **⚠ Scope note (2026-05-27)**：本 doc 是 [`02-state-vs-market-gap.md`](../architect/02-state-vs-market-gap.md)（市场差距清单）视角下的 **named competitor capability evidence 补齐**——业界 hardened 参考 runtime（vLLM / SGLang / llama.cpp / mlx-lm / MLC-LLM / mlx-knife）的横向 capability 扫描。**不是** owlmlx vs replacement target（**oMLX** / **vMLX**）的对比——后者见 [`reference-runtime-comparison-matrix.md`](reference-runtime-comparison-matrix.md)，两份 doc 在 owlmlx 既有体系里**本来就是分开的**：一份是"市场格局横扫"，一份是"replacement target 深度对比"。本 doc 不替代任一份。

> **Status**: source-of-truth (snapshot)
> **Author**: refresh-of-record for [`02-state-vs-market-gap.md`](../architect/02-state-vs-market-gap.md) §1 12 维框架，对 6 个被作为"业界"引用但未单独建行的主流 runtime 补齐独立 capability row
> **Boundary**: capability surface as observed in public releases / official docs / open issues, 2026-05-27 view (±2 天)
> **Honest scope**: 不是 parity claim、不是 benchmark 比赛、不是 throughput 对比；是 12 维 capability surface 对齐
> **Subagent evidence chain**: 6 个并行 fresh-context 子调研 agent，各完成 ≥3 次 WebSearch + ≥2 次 WebFetch，全部 evidence URL 已锚定

---

## 0. 为什么要刷新

[`02-state-vs-market-gap.md`](../architect/02-state-vs-market-gap.md)（2026-05-25）已经给 7 个对手建了独立行（vMLX / vllm-mlx / Ollama·LM Studio 类 / Apple FM / oMLX / OwlRunKit / llm_router），但把 **vLLM / SGLang / llama.cpp / mlx-lm / MLC-LLM / mlx-knife** 当作"业界"模糊引用，导致：

1. §1 表格的 "业界 hardened 参考" 列是 abstract 而非 named competitor，无法精确判定 L0/L1/L2/L3
2. §5 "总差距判断" 缺少 named-competitor anchor 时，"必须追的差距 / 刻意不追的差距 / 差异化窗口" 的边界容易漂移
3. §3 各能力细分表里的"vLLM/SGLang 标准"是无 evidence URL 的口头引用

本 snapshot 补齐这 6 个 named competitor 的 12 维独立行 + named evidence，让 [02-state-vs-market-gap.md] 后续 update 可以 cite 本 snapshot 作为锚点而不再口头引用。

**本 snapshot 不替代 [02-state-vs-market-gap.md]**——后者仍是策略决策文档；本 snapshot 是 capability evidence ledger。

---

## 1. 阅读约定

- **能力标签**（沿用 [02-state-vs-market-gap.md] §0）：
  - ✅ strong — 文档 / release notes 显式声明且有 evidence 支持
  - 🟡 partial — 部分实装、限定 path 内 supported、或有 known caveat
  - 🟠 scaffold — 接口存在但完整性 / 稳定性 / coverage 显著不足
  - 🔴 missing — 文档无证据或确认 not in scope
  - N/A — 该轴对该 runtime 类型不适用（如 lifecycle CLI 不评 cache depth）

- **12 能力轴**：与 [02-state-vs-market-gap.md] §1 完全对齐，避免维度漂移

- **Evidence URL 纪律**：每个 ✅ / 🟡 / 🟠 / 🔴 都需在 §3 各竞品独立块里给至少 1 个 URL；本表格层只给标签，URL 在 §3

- **诚实备注**：本 snapshot 不是动手 reproducible benchmark，所有 capability 标签来自公开声明 + open issue 反推，不是字节级验证

---

## 2. 横向 Master Capability Matrix

> **基线时刻**：2026-05-27。版本号见各列首。
> **owlmlx 列**：用 [`runtime-capability-matrix.md`](runtime-capability-matrix.md) 当前 supported / partial / experimental 直接映射；非"业界拉齐"虚标。

| # | 维度 | owlmlx | vLLM v0.21.0 | SGLang v0.5.12.post1 | llama.cpp b9352 | mlx-lm v0.31.3 | MLC-LLM main@2026-05-11 | mlx-knife v2.0.6 |
|---|---|---|---|---|---|---|---|---|
| 1 | Repeatability (N≥20 byte-exact) | 🟡 | 🟡 | 🟡 | 🟠 | 🟠 | 🔴 | N/A |
| 2 | Capability Honesty | ✅ | 🟠 | 🟠 | 🔴 | 🟡 | 🟠 | 🟡 |
| 3 | Cache Depth | 🟡 | ✅ | ✅ | ✅ | 🟠 | 🟡 | N/A |
| 4 | Scheduler Depth | 🟡 (单 worker by design) | ✅ | ✅ | ✅ | 🟡 | ✅ | N/A |
| 5 | Admission / Eviction | 🟡 | 🟡 | ✅ | 🟡 | 🔴 | 🟠 | 🔴 |
| 6 | Status & Provenance | ✅ | ✅ | 🟡 | 🟠 | 🔴 | 🔴 | ✅ |
| 7 | Failure Cleanliness | 🟡 | 🟠 | 🟠 | 🟡 | 🟠 | 🟠 | ✅ |
| 8 | Multi-Model Lifecycle | 🟡 | 🟡 | ✅ | 🟡 | 🔴 | 🟡 | ✅ |
| 9 | Speculative Path Safety | 🟡 (F-1 endpoint landed; method experimental) | 🟠 | 🟡 | 🟡 | 🟠 | 🟡 | N/A |
| 10 | **Structured-Output Invariance** | 🔴 (F-4 in flight) | 🔴 | 🟠 | 🟡 (no invariance claim) | 🔴 | ✅ (xgrammar; invariance 未证) | N/A |
| 11 | Consumption Contract | ✅ | ✅ | ✅ | 🟡 | 🟠 | 🟠 | 🟡 |
| 12 | Heterogeneous Compute | 🔴 (Metal only) | 🟠 (CUDA-first deliberate) | 🟠 (NV/AMD/NPU; Apple Silicon scaffold) | ✅ (16+ backend) | 🟡 (Metal default + TP) | ✅ (Metal/CUDA/Vulkan/WebGPU/iOS/Android) | N/A |

**轴 10 字段重要警告**：MLC-LLM 通过 xgrammar 整合声明 "structured generation with speculative decoding support"（[XGrammar-2 blog 2026-05-04](https://blog.mlc.ai/2026/05/04/xgrammar-2-fast-customizable-structured-generation)），但**没有 byte-for-byte invariance 验证**——这是 capability claim 与 invariance 验证不可混淆的关键节点；见 §3.5 与 §4.1。

---

## 3. 各竞品独立快照

每竞品快照固定结构：Identity / 12 维状态 / 与 owlmlx 相对位置 / 关键 open issue / 诚实备注。所有 URL 截至 2026-05-27 可访问。

### 3.1 vLLM v0.21.0

**Identity**
- Version / date: v0.21.0（2026-05）· [Releases](https://github.com/vllm-project/vllm/releases) · [docs.vllm.ai](https://docs.vllm.ai/en/latest/)
- 一句话定位：CUDA-first、多 GPU、生产规模、吞吐优先的开源 LLM serving 金标准栈
- 场景：H100/MI300 集群、TP/PP/DP/EP/CP parallel、disaggregated prefill-decode、Prometheus/OTel 可观测

**12 维状态（带 evidence）**

1. **Repeatability 🟡** — 官方文档明示 "does not guarantee reproducibility by default"；需 `VLLM_ENABLE_V1_MULTIPROCESSING=0` 或 batch invariance 开启；仅 same-HW + same-version 内承诺；无 N≥20 字节一致测试 · [reproducibility docs](https://docs.vllm.ai/en/latest/usage/reproducibility/)
2. **Capability Honesty 🟠** — 部分 feature page 标 `(Experimental)`（如 Disaggregated Prefilling、Custom Proposer Backend），但无跨版本 promotion gate · [disagg_prefill](https://docs.vllm.ai/en/latest/features/disagg_prefill/)、[v0.9 compat matrix](https://docs.vllm.ai/en/v0.9.0/features/compatibility_matrix.html)
3. **Cache Depth ✅** — Automatic Prefix Caching（SHA256/CBOR hash + cache_salt 隔离）、FP8/NVFP4 KV、TurboQuant 2-bit KV（4× capacity）、KV Offload → Hybrid Memory Allocator · [APC design](https://docs.vllm.ai/en/latest/design/prefix_caching/)、[FP8 KV blog](https://vllm-project.github.io/2026/04/22/fp8-kvcache.html)
4. **Scheduler Depth ✅** — V1 engine 默认 continuous batching + PagedAttention + chunked prefill；Disaggregated P/D 通过 NIXL/P2pNccl/LMCache/Mooncake；v0.21 加 bi-directional KV transfer · [PyTorch P/D blog](https://pytorch.org/blog/disaggregated-inference-at-scale-with-pytorch-vllm/)
5. **Admission / Eviction 🟡** — LRU 基线；BlockEvictionPolicy / Tail-Optimized LRU 仍是 RFC；无 pin/TTL 一级 API · [issue #36311](https://github.com/vllm-project/vllm/issues/36311)、[issue #37823](https://github.com/vllm-project/vllm/issues/37823)
6. **Status & Provenance ✅** — Prometheus `vllm:*` namespace + OTel tracing（`--otlp-traces-endpoint`）；request-level histogram + engine-level gauge；无 contract.version 抽象 · [metrics design](https://docs.vllm.ai/en/stable/design/metrics/)
7. **Failure Cleanliness 🟠** — issue #39146 报 base scheduler 下 temp=0 非确定 + KV block corruption；issue #28726 报 unbounded CPU mem growth；无 settle barrier / recovery supervisor 抽象 · [#39146](https://github.com/vllm-project/vllm/issues/39146)、[#28726](https://github.com/vllm-project/vllm/issues/28726)
8. **Multi-Model Lifecycle 🟡** — Sleep Mode（2025-10）支持热切多模型，18-20× 快于冷启；LoRA 热切走 queue；无 model lineage / SHA 溯源 · [Sleep Mode blog](https://blog.vllm.ai/2025/10/26/sleep-mode.html)
9. **Speculative Path Safety 🟠** — 方法广（EAGLE/MTP/Medusa/n-gram/Suffix/PARD/MLP/Draft），但 **safety 信号差**：spec×tool 至少 7 个 open bug · [spec_decode docs](https://docs.vllm.ai/en/latest/features/speculative_decoding/)
10. **Structured-Output Invariance 🔴（关键）** — **issue [#41967](https://github.com/vllm-project/vllm/issues/41967)** Gemma4+MTP 流式多工具丢首参数，截至 2026-05 **仍 OPEN**；同族 open bug：[#35800](https://github.com/vllm-project/vllm/issues/35800)、[#38106](https://github.com/vllm-project/vllm/issues/38106)、[#36872](https://github.com/vllm-project/vllm/issues/36872)、[#40831](https://github.com/vllm-project/vllm/issues/40831)、[#42005](https://github.com/vllm-project/vllm/issues/42005)、[#34650](https://github.com/vllm-project/vllm/issues/34650)、[#27969](https://github.com/vllm-project/vllm/issues/27969)。XGrammar 0.2.0 structural tags 已并入 v0.21，**但不修字节级不变性**
11. **Consumption Contract ✅** — Prom + OTel 双轨；SUSE / Splunk / Dash0 / Parseable 多家 sink · [metrics design](https://docs.vllm.ai/en/stable/design/metrics/)
12. **Heterogeneous Compute 🟠（刻意）** — 主分支 CUDA-first；CPU backend in `docs/installation/cpu`；Apple Silicon 走社区 [vllm-metal](https://github.com/vllm-project/vllm-metal) 和 vllm-mlx fork；主仓 MPS "experimental, silent fail"

**与 owlmlx 相对位置**
- **vLLM 领先**：Cache Depth（APC + FP8/NVFP4 + cache_salt 三层栈 owlmlx 短期无法对标）、Scheduler Depth（Disaggregated P/D 已在 Meta/LinkedIn/Mistral 生产）、Consumption Contract（Prom + OTel 双轨）
- **持平**：Multi-Model Lifecycle（Sleep Mode vs owlmlx hot-swap，能力不同但目标近似）、Admission / Eviction（双方都还在 RFC 阶段）、Status & Provenance（双方都缺 contract.version 显式承诺）
- **owlmlx 领先**：Capability Honesty（vLLM 无系统化 promotion 纪律）、Repeatability（vLLM 文档明示不保证字节一致）、Structured-Output Invariance（vLLM 7+ open bug 未收敛）
- **vLLM 刻意不做**：Heterogeneous Compute / Apple Silicon（CUDA-first deliberate，Mac 推社区 plugin）、byte-level Repeatability（让位给吞吐）

**对 owlmlx 路线的影响**
- F-4 (Structured-Output Invariance) 与 vLLM #41967 / #34650 / #27969 / #40831 是**相同 capability gap 的不同 runtime 表象**——vLLM 长期 OPEN 是 F-4 差异化 thesis 的最强外部证据
- vLLM TurboQuant 2-bit KV × spec decode 的退化 token loop（#40831）证明"quant × spec × structured 三角形"全行业未解；owlmlx F-4 应明确把 quant 路径放进破坏检测器

### 3.2 SGLang v0.5.12.post1

**Identity**
- Version / date: v0.5.12.post1（2026-05-26 patch；v0.5.12 主版本 2026-05-16）· [GitHub](https://github.com/sgl-project/sglang) · [docs.sglang.io](https://docs.sglang.io)
- 一句话定位：以 RadixAttention 前缀复用 + structured generation（xgrammar 默认）为差异化主轴的高性能 LLM/多模态服务框架（LMSYS 主导）
- 场景：NV/AMD GPU 生产、RL rollouts、PD disaggregation、agentic / structured tool-calling

**12 维状态（带 evidence）**

1. **Repeatability 🟡** — deterministic-inference 模块，跑 50 trials 验证 batch-size 不变性，**token-level 一致而非 bit-exact**；MoE 不支持，TP 仅 1-2，radix cache 须 disable · [deterministic_inference docs](https://docs.sglang.io/advanced_features/deterministic_inference.html)、[LMSYS blog 2025-09-22](https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/)
2. **Capability Honesty 🟠** — SpecV2 文档显式标 "experimental"；缺统一 promotion gate / contract.version · [speculative_decoding docs](https://docs.sglang.io/advanced_features/speculative_decoding.html)、[Q2 roadmap #22949](https://github.com/sgl-project/sglang/issues/22949)
3. **Cache Depth ✅** — RadixAttention + HiCache L1/L2/L3（GPU/host/Mooncake/3FS），W4A4/W4A8 量化 kernels，UnifiedRadixTree + SWA · [LMSYS HiCache blog](https://www.lmsys.org/blog/2025-09-10-sglang-hicache/)
4. **Scheduler Depth ✅** — continuous batching + paged attn + chunked prefill（默认 8192）+ PD disaggregation + Decode Radix Cache · [Continuous Batching docs](https://sgl-project-sglang-93.mintlify.app/concepts/continuous-batching)
5. **Admission / Eviction ✅** — TTL pinning（300-3600s，`SGLANG_HICACHE_MAX_PINNED_RATIO` 预算），优先级 heap，超预算请求拒绝；priority preemption · [issue #8743](https://github.com/sgl-project/sglang/issues/8743)
6. **Status & Provenance 🟡** — Prometheus `sglang:` prefix metrics + tracing extra + NVIDIA Dynamo W3C TraceContext 传播；contract.version 未见 · [Prometheus Metrics docs](https://sgl-project-sglang-93.mintlify.app/observability/metrics)、[NVIDIA Dynamo SGLang observability](https://docs.nvidia.com/dynamo/backends/sg-lang/observability)
7. **Failure Cleanliness 🟠** — 部分自动 fallback（DFLASH/NGRAM 不兼容直接 error），但 spec×structured 路径下不退化；issue [#16541](https://github.com/sgl-project/sglang/issues/16541) 报告 100% silent failure；无 settle barrier / recovery supervisor 概念
8. **Multi-Model Lifecycle ✅** — Model Gateway 集中 worker lifecycle，Universal Memory 多模型驻留 + CPU/disk offload · [sgl_model_gateway docs](https://docs.sglang.io/advanced_features/sgl_model_gateway.html)
9. **Speculative Path Safety 🟡** — EAGLE/EAGLE3/MTP/DFLASH/STANDALONE/NGRAM/SpecV2；SpecV2 默认但 topk=1 限制；Spec×structured 不安全
10. **Structured-Output Invariance 🟠** — xgrammar/outlines/llguidance 三后端；**但 spec×structured 已知破坏一致性**：
    - **issue [#9187](https://github.com/sgl-project/sglang/issues/9187)**：EAGLE 让 JSON 在第一个分支 token 卡死直到 max_tokens，silent failure
    - **issue [#16541](https://github.com/sgl-project/sglang/issues/16541)**：DSV3.1 PD + spec v2 100% 失败，mimo "Tokens not accepted"
    - **issue [#3724](https://github.com/sgl-project/sglang/issues/3724)**：nextn + xgrammar scheduler 崩溃
    - **issue [#5702](https://github.com/sgl-project/sglang/issues/5702)**：NEXTN + shared-experts-fusion 精度损失
    - **无公开声明字节不变性**
11. **Consumption Contract ✅** — `--enable-metrics` Prometheus，多进程聚合，OTLP 导出 · [Prometheus Metrics docs](https://sgl-project-sglang-93.mintlify.app/observability/metrics)
12. **Heterogeneous Compute 🟠** — NV + ROCm + TPU + 华为 NPU + Intel XPU 完整；MLX/Metal 仅 Q1 roadmap 草案，v0.5.10 release note 提"native MLX backend"但 Q2 roadmap 未落地 · [Apple Silicon roadmap #19137](https://github.com/sgl-project/sglang/issues/19137)、[MLX backend #17846](https://github.com/sgl-project/sglang/issues/17846)

**Structured Output × Speculative Decoding 深挖（F-4 直接对标）**

| 问题 | 答案 |
|---|---|
| SGLang 当前如何处理 spec + structured output 组合？ | **不安全且未保证字节不变**——多枚 open issue 一致复现 silent failure 与 scheduler 崩溃 |
| 是否有公开证据声明字节不变性？ | **没有**。determinism 文档只覆盖 dense + 单/双 TP + radix-off，且明确不提 spec/structured 兼容 |
| 是否有 fallback / disable spec 行为？ | **无自动 fallback**。Workaround 是手动关 `--speculative-algorithm`；SpecV2 保留 `topk=1` 与模型白名单等 hard gate |
| Q2 roadmap (#22949) 是否列入修复？ | **未列入**。deterministic inference 仅作为 RL 共用 primitive 列出，未列 structured×spec 修复 |
| owlmlx F-4 是否仍有差异化？ | **有，且差异化更明确**——SGLang 的 spec×structured 在两年版本迭代后仍 known broken + silent failure，工程优先级落在 throughput/HiCache/PD 而非 invariance |

**与 owlmlx 相对位置**
- **SGLang 领先**：Cache Depth（HiCache L1/L2/L3 + Mooncake/3FS）、Scheduler Depth（PD disaggregation + Decode Radix + EP scaling）、Multi-Model Lifecycle（Model Gateway + Universal Memory）
- **持平**：Consumption Contract、Admission / Eviction（颗粒度不同）、Speculative Path Safety（双方都"算法存在但组合路径未完全证实"）
- **owlmlx 领先**：**Structured-Output Invariance**（owlmlx F-4 把 spec/quant 与 structured 路径的不变性当成 promotion gate；SGLang 长期 known broken）、Capability Honesty、Heterogeneous Compute / Apple Silicon
- **SGLang 刻意不做**：Apple Silicon / 单机消费级（绑 NV/AMD/NPU/TPU 集群）、structured×spec 的 bit-for-bit 不变性证明

**对 owlmlx 路线的影响**
- F-4 thesis 在 SGLang 对比下从"独占差异化"调整为"**路线选择差异化**"——SGLang 把 invariance 当作 throughput 旁路，owlmlx 把 invariance 当作 promotion gate
- xgrammar-2 (2026-05-04) 声称 "speculative decoding support"，但 SGLang 端同期 #9187 / #16541 仍 OPEN——**xgrammar 层声明 ≠ serving 层验证**

### 3.3 llama.cpp b9352

**Identity**
- Version / date: b9352（2026-05-26 23:48 UTC）· [Releases](https://github.com/ggml-org/llama.cpp/releases) · 组织名已由 `ggerganov` 迁至 `ggml-org`
- 一句话定位：C/C++、零依赖、跨硬件后端最广的 LLM 推理栈，GGUF 生态根基
- 场景：单 host 本地推理、Ollama / LM Studio / Jan / GPT4All 的底层引擎、CI、嵌入式

**12 维状态（带 evidence）**

1. **Repeatability 🟠** — CUDA 有 opt-in deterministic mode（[PR #16016](https://github.com/ggml-org/llama.cpp/pull/16016)，RMSNorm/MatMul/Attention/KV-cache 批不变 kernel）；**Metal 不在覆盖范围**；spec path 存在 deterministic 回归（[issue #23335](https://github.com/ggml-org/llama.cpp/issues/23335) draft-mtp 改变 Qwen3.6 输出）；无官方 N≥20 测试套件
2. **Capability Honesty 🔴** — README 只对 Hexagon/OpenVINO 标 `[In Progress]`；router mode / MCP proxy / built-in tools 在 server README 只散见 "experimental"，未结构化暴露 · [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
3. **Cache Depth ✅** — `--cache-prompt` 默认开；`--cache-type-k/v` 支持 f16/q8_0/q4_0 等 KV 量化；`/slots/<id>/save` 与 `/restore` API + `--slot-save-path` 持久化 · [discussion #13606](https://github.com/ggml-org/llama.cpp/discussions/13606)
4. **Scheduler Depth ✅** — `--cont-batching` 默认开；prompt 自动按 512 token chunked prefill；single forward pass 混合 decode + prefill chunk · [discussion #4130](https://github.com/ggml-org/llama.cpp/discussions/4130)
5. **Admission / Eviction 🟡** — Router mode 有 LRU + `--models-max`；**无 pin / 无 TTL / 无显式 admission gate**；[issue #20137](https://github.com/ggml-org/llama.cpp/issues/20137) 显示并发下 `--models-max` 有 TOCTOU race
6. **Status & Provenance 🟠** — `/models` 给 loaded/loading/unloaded 三态；`/slots` 给 per-slot 速率；**无 contract.version、无 runtime-owned status object**
7. **Failure Cleanliness 🟡** — 子进程隔离的 router 保证 crash 不连累；prompt cache checkpoint slot-local，`-np>1` 会丢（[issue #22942](https://github.com/ggml-org/llama.cpp/issues/22942)）；无 pre-load reject / settle barrier
8. **Multi-Model Lifecycle 🟡** — Router mode 支持多模型驻留 + hot-swap（按 `model` 字段路由）；无 lineage、无 pin · [HF router mode blog](https://huggingface.co/blog/ggml-org/model-management-in-llamacpp)
9. **Speculative Path Safety 🟡** — 支持 draft-simple / draft-eagle3 / draft-mtp / ngram-* 共 8 种；MTP 于 2026-05-16 入 master；[issue #23335](https://github.com/ggml-org/llama.cpp/issues/23335) 记录 draft-mtp 改变确定性输出；**官方未声明与 tool calling / grammar 兼容性保证**
10. **Structured-Output Invariance 🟡** — GBNF 语法 + JSON Schema → GBNF 自动转换是一等公民；2026-03 加 autoparser；**spec×grammar 在 llama.cpp 端无 invariance 保证文档** · [grammars README](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md)
11. **Consumption Contract 🟡** — `/metrics` Prometheus 端点（`prompt_tokens_total` / `generation_tokens_total` / `kv_cache_usage_ratio` / queue depth）；router mode 下 `/metrics` 需 `?model=` 且触发 autoload（[issue #23096](https://github.com/ggml-org/llama.cpp/issues/23096)）；无 SLO/contract.version · [PR #18001](https://github.com/ggml-org/llama.cpp/pull/18001)
12. **Heterogeneous Compute ✅** — 16+ 后端：Metal/CUDA/HIP/MUSA/Vulkan/SYCL/OpenVINO/ZenDNN/CANN/OpenCL/zDNN/RPC/WebGPU/VirtGPU + CPU (NEON/AVX/Accelerate/BLAS/BLIS)；Apple Silicon 首类

**Apple Silicon 上 vs owlmlx 深挖**
- Metal 后端成熟度：llama.cpp Metal 是 day-one 一等公民，在 M3 Ultra / M4 Max 稳定；社区 benchmark（Qwen 3.5 35B-A3B on M4 Max 32GB）报 **MLX 比 llama.cpp Metal 高 15-30% 吞吐、低约 10% 内存**；两者都不接 ANE
- GGUF vs MLX-format：llama.cpp 强制 GGUF（含 Q4_K_M / Q5_K_M / Q8_0 / IQ-quant），生态最大但每改格式要 requantize；MLX 直接吃 safetensors + MLX-format，转换链短——这是 owlmlx 选 MLX 而不接 GGUF 的工程理由
- 公开 benchmark 指示性：M4 Max 70B Q4_K_M ≈ 70 tok/s decode；M3 Ultra DeepSeek V3 Q4_K_M ≈ 10-15 tok/s decode（社区数字，非 reproducible）

**与 owlmlx 相对位置**
- **llama.cpp 领先**：Heterogeneous Compute（16+ backend）、Scheduler Depth（continuous batching + chunked prefill 大规模实战）、Cache Depth（slot KV save/restore + 量化 KV 双独立轴）
- **持平**：Speculative Path Safety（双方都有实装、双方都未承诺 grammar/tool 兼容）、Structured-Output Invariance（双方均有 JSON schema → grammar 但都未声明 spec-on invariance）、Multi-Model Lifecycle
- **owlmlx 领先**：Repeatability（owlmlx 设计 N≥20 byte-exact 路线；llama.cpp Metal 路径无 deterministic kernel）、Capability Honesty、Status & Provenance（runtime-owned + contract.version）
- **llama.cpp 刻意不做**：Capability Honesty trace（社区项目无 SLO 文化）、production-grade admission control（[#20137](https://github.com/ggml-org/llama.cpp/issues/20137) 表明上限只是 best-effort）

### 3.4 mlx-lm v0.31.3（**substrate, not competitor**）

**Identity**
- Version / date: v0.31.3（2026-04-22）· [Releases](https://github.com/ml-explore/mlx-lm/releases) · [Repo](https://github.com/ml-explore/mlx-lm)
- 与 mlx / mlx-examples 关系：mlx 是底层 array 框架；mlx-lm 早期作为 `mlx-examples/llms` 存在，已独立成 `ml-explore/mlx-lm`，专注 LM 层（generate / cache / server / speculative / quant util）
- 一句话定位：**Apple 官方的 LM-on-MLX substrate 库 + 单进程 OpenAI-compatible 参考 server**，目标 "能跑 + 够快 + 工程参考"，**不是产品级 serving runtime**

**12 维状态（带 evidence；mlx-lm 是 owlmlx 上游 substrate，标签反映 substrate 角色）**

1. **Repeatability 🟠** — `generate()` 接受 seed，但 server batching 模式下 "per-request positive seed values are ignored in continuous batching mode"；要复现必须 `--disable-batching`；[issue #259](https://github.com/ml-explore/mlx-lm/issues/259) 显示 trim_prompt_cache 路径 logits 不可重复
2. **Capability Honesty 🟡** — 无 experimental/stable 显式分级；release notes 写实；speculative decoding 文档未标注 MoE 失效模式（[issue #1132](https://github.com/ml-explore/mlx-lm/issues/1132) 用户自发现 -35%）
3. **Cache Depth 🟠** — `mlx_lm.cache_prompt` CLI + `--prompt-cache-file` 在 **generate** 路径可用；**server 路径不支持** `--prompt-cache-file`（[issue #1178](https://github.com/ml-explore/mlx-lm/issues/1178) **OPEN**）；`trim_prompt_cache` 对 `KVCache` 可用，**对 `RotatingKVCache` 不可 trim**（[issue #980](https://github.com/ml-explore/mlx-lm/issues/980) **OPEN**）、对 SSM/Mamba state 不可 trim；v0.31.2 补 "Caching system prompt for non-trimmable caches"——**侧面承认 trim 路径只覆盖 pure full-attention 模型**
4. **Scheduler Depth 🟡** — server 自 v0.30.4 起有 BatchGenerator + `--decode-concurrency=32` + `--prompt-concurrency=8`；continuous batching 真正可用是 2026 年；**无 paged KV / 无 SLO-aware 调度**
5. **Admission / Eviction 🔴** — `ModelProvider` 是单模型 + process-lifetime cache；**无 admission control / 无 queue / 无 TTL / 无 eviction** · [DeepWiki §2.1](https://deepwiki.com/ml-explore/mlx-lm/2.1-model-loading-and-management)
6. **Status & Provenance 🔴** — 无 /metrics / 无 Prometheus / 无 runtime stats；只有 OpenAI completion payload
7. **Failure Cleanliness 🟠** — release notes 频繁修 cache dim mismatch / tool parser 边界 / NoneType 崩溃，无显式 fail-clean 约束；崩溃靠 process restart 兜底
8. **Multi-Model Lifecycle 🔴** — DeepWiki 直接确认：「ModelProvider manages a single model per server instance ... must run separate server instances for different models」
9. **Speculative Path Safety 🟠** — `--draft-model` + `num_draft_tokens` 已落地，**batching 模式下自动禁用**；MoE / draft-size-close 场景实测 **-35% 吞吐**（[#1132](https://github.com/ml-explore/mlx-lm/issues/1132)）；**MTP** 通过 [PR #990](https://github.com/ml-explore/mlx-lm/pull/990)（27B Qwen3.5 上 1.57x）截至 2026-05 **仍未 merge**（17 天无 review）；**n-gram / suffix decoding 上游无原生支持**
10. **Structured-Output Invariance 🔴** — README 不提；社区路径靠 Outlines + llm-structured-output 外挂 logits processor；mlx-lm.server 无 native JSON mode / grammar / function-call schema 校验
11. **Consumption Contract 🟠** — server 暴露 OpenAI `/v1/chat/completions` + `/v1/completions` + 正确 `finish_reason`（v0.30.5 才补） + tool_calls（v0.31.x 多次修 Gemma4/Mistral/MiniMax parser）；**无超出 OpenAI 的 capability/quota/headroom 端点**
12. **Heterogeneous Compute 🟡** — Metal 默认；`MLX_FORCE_CPU=1` 切 CPU；v0.31.0 加 tensor parallel、v0.30.6 加 distributed inference；**ANE 路径不在 scope**

**substrate 与 owlmlx 的边界（关键）**

| 类别 | 内容 |
|---|---|
| mlx-lm 已做、owlmlx 不重做 | tokenizer wrapper、generate loop、quant load / safetensors I/O、KVCache/RotatingKVCache/MambaCache 数据结构本身、HF Hub 下载、tool-call parser 体系、tensor parallel 原语、单 process OpenAI 协议表层 |
| mlx-lm 不做、owlmlx 必须自做 | admission control（`scheduler_admission` / `model_load_admission`）、memory actuator + watermark + eviction policy（`memory_actuator` / `memory_watermark` / `memory_pressure_eviction_policy`）、resident model registry（`model_inventory` / `model_residency_policy`）、capability honesty / specimen gate（`specimen_gate` / `technical_preview` / `speculative_execution_status`）、failure-clean recovery（`abort_recovery` / `recovery_supervisor` / `runtime_health`）、repeatability statistics、structured-output invariance、provenance/metric 暴露、suffix decoding |
| mlx-lm 做了 + owlmlx 重做（重叠区） | **speculative decoding**——上游 `--draft-model` 已存在；owlmlx 还在自研 `suffix_decoding/` 与 `gemma4_mtp_drafter.py`，理由是上游 MTP PR #990 未 merge 且 batching 模式 spec 被禁用，但**一旦上游动作 owlmlx 这层有被吞掉的风险**——需持续盯 PR #990 |
| mlx-lm 做得有问题、owlmlx 反向影响 | **`trim_prompt_cache` 是 Campaign F-2 C2 的硬阻塞**——owlmlx 在 `mlx_native_backend.py::_trim_prompt_cache_with_reason` 枚举 5 种 reason code（`_unavailable` / `_exception` / `_bool_result` / `_int_result` / `_invalid_result`）是对上游 #980 + 接口返回类型不稳定的防御层。上游修好 #980 前，owlmlx 只能在 pure full-attention 模型上启用 trim 路径，hybrid / SSM 必须降级到 non-trimmable cache + full recompute |

**"只用 mlx-lm + 简单 HTTP wrapper" 缺什么**（owlmlx 存在的根本理由）
1. 多模型驻留 + 在线切换（mlx-lm.server 单模型）
2. 内存预算 + 驱逐（无 watermark / 无 eviction / 无 capacity 预判）
3. Admission control / queue 上限 / per-request capability gate
4. Capability honesty 层（无 experimental/stable / 无 specimen gate）
5. Failure-clean lifecycle（加载失败 / 推理崩溃后的资源回收 / 状态注销）
6. Runtime metric / provenance / repeatability 统计
7. 绕开上游 trim 缺陷的 cache 策略（hybrid/SSM 模型 prefix cache 复用）

### 3.5 MLC-LLM main@2026-05-11

**Identity**
- Version / date: GitHub Releases 只挂 `v0.1.dev0`（2023-04-29），无 tagged release；以 `main` 滚动推进，最新 commit `2008fe83`（2026-05-11，TVM runtime refactor 跟进）· [Repo](https://github.com/mlc-ai/mlc-llm)
- 一句话定位：Universal LLM Deployment Engine with ML Compilation——用 TVM 编译路径把一份模型同时输出到 Metal / CUDA / ROCm / Vulkan / WebGPU / iOS Metal / Android OpenCL
- Apple Silicon 上相对成熟度：成熟但非首选——第三方对比研究（[arxiv 2511.05502](https://arxiv.org/abs/2511.05502)，2025）测得 ~190 tok/s，比 mlx-lm（~230 tok/s）低约 17%，但 **64K-128K 长上下文是 Apple Silicon 上唯一保持线性的 runtime**

**12 维状态（带 evidence）**

1. **Repeatability 🔴** — 文档与 issues 均无 byte-equal 复现承诺；REST API 接受 `seed` 但 best-effort；无 issue / 测试断言反复测过 N≥20
2. **Capability Honesty 🟠** — 量化方案文档标 `q4f16_awq` 为 "not stable"（[configure_quantization](https://github.com/mlc-ai/mlc-llm/blob/main/docs/compilation/configure_quantization.rst)）；server/engine 层无统一 experimental 标签
3. **Cache Depth 🟡** — REST API 提供 `prefix_cache_max_num_recycling_seqs`（[rest.html](https://llm.mlc.ai/docs/deploy/rest.html)）；KV 量化 issue 与 q4 weight 路径完备；但 [MLCEngine blog 2024-10](https://blog.mlc.ai/2024/10/10/optimizing-and-characterizing-high-throughput-low-latency-llm-inference) 自陈 prefix caching 未在主线 bench 内
4. **Scheduler Depth ✅** — Paged KV cache（[arxiv 2511.05502](https://arxiv.org/abs/2511.05502) 指为 Apple Silicon 长上下文优势根因）；continuous batching 默认；commit `3436` 显式提到 `prefill_chunk_size` greedy sub-batching
5. **Admission / Eviction 🟠** — `prefix_cache_max_num_recycling_seqs` 暗示 LRU recycle；无 pin / TTL / 拒绝接入 API
6. **Status & Provenance 🔴** — 无 contract.version；`GET /v1/models` 仅 OpenAI 兼容 list
7. **Failure Cleanliness 🟠** — 编译期会拒绝不支持模型；runtime 层无系统化 reject / recovery；issue tracker 多个 GPU OOM 挂死案例
8. **Multi-Model Lifecycle 🟡** — `--additional-models` 仅服务于 speculative draft model，非通用 hot-swap；多模型按进程拆分
9. **Speculative Path Safety 🟡** — `--speculative-mode={disable, small_draft, eagle, medusa}` 完整路径；官方 blog 自陈 Eagle/Medusa 未在主 bench 内
10. **Structured-Output Invariance ✅（声明）/ 🟡（invariance 未证）** — xgrammar（同团队孵化）原生集成；[XGrammar-2 blog 2026-05-04](https://blog.mlc.ai/2026/05/04/xgrammar-2-fast-customizable-structured-generation) 自陈集成进 MLC-LLM/SGLang/vLLM/TRT-LLM 主干，含 Structural Tag、tool calling、**声明 speculative decoding support**——**但没有 byte-for-byte invariance 验证证据**
11. **Consumption Contract 🟠** — OpenAI 兼容 `usage` 字段够；无 Prometheus/OTLP 一等公民
12. **Heterogeneous Compute ✅** — AMD(Vulkan/ROCm) + NVIDIA(Vulkan/CUDA) + Apple Metal + Intel Vulkan + WebGPU/WASM + iOS Metal + Android Adreno/Mali OpenCL——**同代码同编译路径覆盖所有平台是行业内独一份**

**项目重心信号（关键）**
- 2025-11-22 [issue #3382](https://github.com/mlc-ai/mlc-llm/issues/3382) "Is this project abandoned?" 由 tqchen 亲自回复："we are still actively working on it. A lot of the recent dev has been pushing towards the low-level compilation… xgrammar that gets integrated into major engines"——**官方承认重心已从 MLC-LLM serving 移向 TVM 底层 + xgrammar 模块化**
- 2026 commit graph 30+ commit 多为 TVM refactor 跟随、模型 template 增补、WebGPU 子调度；功能性 serving 创新（speculative / prefix cache / admission）自 2024-10 后无显著推进
- → **MLC-LLM 在 Apple Silicon 上正在被 mlx-lm 甩开**，但 xgrammar 与 TVM 仍是 owlmlx 不能忽略的 substrate

**与 owlmlx 相对位置**
- **MLC 领先**：Heterogeneous Compute（跨 6+ 后端一份模型）、Structured-Output Invariance（xgrammar 声明层）、Scheduler Depth（paged KV + chunked prefill + continuous batching 三件套）
- **持平**：Speculative Path Safety、Cache Depth、Capability Honesty
- **owlmlx 领先**：Repeatability（owlmlx N≥20 byte-exact 路线，MLC 完全缺位）、Status & Provenance（runtime-owned + contract.version）、Admission / Eviction（pin / TTL / 显式驱逐）
- **MLC 刻意不做**：byte-equal 复现（设计哲学是"编译产物可移植"）、runtime-owned contract / provenance（其上游身份是 SDK 编译器）

### 3.6 mlx-knife v2.0.6（**lifecycle-adjacent, not serving competitor**）

**Identity**
- Version / date: v2.0.6（2026-05-12）· [Repo](https://github.com/mzau/mlx-knife) · [PyPI](https://pypi.org/project/mlx-knife/)
- 一句话定位：Apple Silicon 上的 "ollama-like" MLX 模型 lifecycle CLI（pull / rm / list / show / convert / quantize / serve），HuggingFace cache 为底座；text-first，vision/audio 是 curated 子集
- 维护状态：**active**（2.0.3→2.0.6 在 2025-11 至 2026-05 半年内 4 次 release）

**关键能力（针对 owlmlx multi-model lifecycle 维度）**
- **content_hash v2**（2.0.6 引入）：sentinel `.mlxk_workspace.json` 记录 per-file `path / size / mtime_ns / sha`；safetensors header-only hash；JSON 字段 `origin / content_hash / hash_modified / clean / display_name`；push 操作返回 `commit_sha / commit_url`
- **resumable download + repair-index**：`.mlxk2_download_complete` marker；`convert --repair-index` 修过 7+ 个 broken model；五点 health-check；mtime-drift self-heal；path traversal 防护
- **量化谱系**：`source_repo` + `bits/group_size` 保留在 workspace；convert 时有 re-quantize 警告
- **JSON envelope**：所有命令 `--json` 统一 envelope（`status/command/data/error`）；[docs/json-api-specification.md](https://github.com/mzau/mlx-knife/blob/main/docs/json-api-specification.md)；但 schema 版本契约未对外稳定
- **pin / TTL**：**没有**——纯手动 lifecycle

**与 owlmlx 的关系**
- **可借用模式（不该自研）**：
  - **content_hash v2 file-level recipe**（path/size/mtime_ns/sha 四元组）——owlmlx `model_lineage` 当前 `sha256` 是单值，可考虑借鉴 per-file index
  - **sentinel-based migration**（v1→v2 原地 rewrite 无破坏性）——对 owlmlx schema 演进有参考价值
  - **resumable + repair-index 工程模式**
- **owlmlx 已有、mlx-knife 没做**：
  - 面向 **runtime** 的 lineage truth 抽象（`normalize_model_lineage` / `validate_model_lineage` / `derive_lineage_change_type`）——mlx-knife 只关心 workspace 静态状态，没有"served 模型变更类型"概念
  - admission / eviction / scheduler / serving 全栈关联——mlx-knife 完全不在场
- **可能分工**：mlx-knife 是 artifact 层 source-of-truth，owlmlx 是 runtime 层 lineage truth；如果未来 owlmlx catalog 联邦，mlx-knife sentinel 是天然 upstream

---

## 4. 跨竞品读出

### 4.1 owlmlx 真正的差异化窗口（无竞品 solved）

下列 5 条轴，**没有任何一家竞品** 给出 byte-for-byte invariance / N≥20 byte-exact / 系统化 promotion gate 的 serving-runtime-grade 证据：

#### 4.1.1 Structured-Output Invariance × Speculative Decoding（**F-4 thesis 确认**）

| Runtime | 当前状态 | 证据 |
|---|---|---|
| vLLM | 🔴 7+ open bug 长期未收敛 | #41967 #34650 #27969 #40831 #35800 #38106 #36872 #42005 全部 OPEN |
| SGLang | 🟠 known broken + silent failure；Q2 roadmap 未列入修复 | #9187 #16541 #3724 #5702 |
| llama.cpp | 🟡 GBNF 一等公民，但无 spec×grammar invariance 保证文档 | grammars/README.md 不涉及 |
| mlx-lm | 🔴 not in scope | — |
| MLC-LLM | ✅（声明）/ 🟡（未证）xgrammar-2 声明 speculative support | XGrammar-2 blog 2026-05-04，无 invariance verification |
| mlx-knife | N/A | — |

**结论**：**F-4 invariance thesis 在 2026-05-27 视角下成立**。这是 owlmlx 在跨 runtime 比较里唯一"占据未被覆盖窗口"的轴。其他 runtime 的状态分布在"open bug 不修 / 把 invariance 当 throughput 旁路 / 只声明不验证"三种 anti-pattern 上。

#### 4.1.2 N≥20 Byte-Exact Repeatability

| Runtime | 当前状态 |
|---|---|
| vLLM | 🟡 文档明示 "does not guarantee reproducibility by default" |
| SGLang | 🟡 token-level（非 bit-exact）；MoE/radix-cache 不支持 |
| llama.cpp | 🟠 CUDA only deterministic kernel；**Metal 路径无 deterministic kernel** |
| mlx-lm | 🟠 batching 下 seed 被忽略；要复现必须 `--disable-batching` |
| MLC-LLM | 🔴 完全缺位 |

**结论**：Campaign A 的 N≥20 byte-exact 是 **Apple Silicon 路径上完全无人占领的轴**（llama.cpp Metal 也未做）。

#### 4.1.3 Capability Honesty + Promotion Gate

**6 个竞品全部 🟠 scaffold 或 🔴 missing**——没有一家做系统化的 experimental / partial / supported 三级标签 + promotion gate 纪律。最接近的是 MLC-LLM 在 quant 文档标 "not stable"（局部诚实），mlx-knife 有 `MLXK2_ENABLE_ALPHA_FEATURES=1` gate（feature flag 风格），但都不是 owlmlx [§1a Promotion Gate](runtime-capability-matrix.md) 这种 cross-cutting 治理。

#### 4.1.4 Memory Watermark + Settle Barrier（PR #649）

无竞品有等价机制——vLLM 的 unbounded CPU mem growth（#28726）正是"无 watermark 抽象"的代价。owlmlx [`memory_watermark`](../../owlmlx/memory_watermark.py) + [`settle_barrier_event`](../../owlmlx/settle_barrier_event.py) 在跨 runtime 比较里是独立 capability。

#### 4.1.5 Runtime-Owned Status + contract.version

vLLM / SGLang / llama.cpp 都有 Prometheus metric，但**都没有 contract.version 抽象**——这是 owlmlx 把 metric 从"diagnostic surface"升级到"upper-layer consumable contract"的关键区别。

### 4.2 owlmlx 落后的轴（must-decide whether to chase）

| 维度 | 落后量 | 决策 |
|---|---|---|
| Cache Depth multi-tier | 重大——vLLM/SGLang 都有 L1/L2/L3 + 量化 KV | **不追自有 multi-tier**（与单 host 单 worker by design 一致），但 hybrid model trim 阻塞需通过 [mlx-lm #980 upstream watch](#43-mlx-lm-上游缺陷的-leverage) 缓解 |
| Scheduler Depth (continuous batching / paged / chunked) | 重大——全行业标配 | **明确不追**（[02-state-vs-market-gap.md §3.3](../architect/02-state-vs-market-gap.md) 已固定为 L0 类刻意不做）。Wave G-3 README 刷新需强化此表述 |
| Heterogeneous Compute breadth | 重大——llama.cpp 16+ backend，MLC 6+ 平台 | **不追广度**（owlmlx 是 Apple Silicon-only by design），但 backend Protocol 预留 sparse-dispatch hook 与 Apple FM hook 是合理预留 |
| Multi-Model Lifecycle (Model Gateway / Sleep Mode) | 中等——SGLang/vLLM 走更高抽象 | **路线选择不同**：owlmlx 走 pin/TTL/eviction history ledger，SGLang/vLLM 走 hot-swap 速度优化；评估 borrow `mlx-knife content_hash v2` |

### 4.3 mlx-lm 上游缺陷的 leverage

mlx-lm 作为 owlmlx 上游 substrate，三个 open issue 直接影响 owlmlx 路线：

| Issue / PR | 影响 owlmlx 的什么 | 建议 owlmlx 动作 |
|---|---|---|
| [mlx-lm #980](https://github.com/ml-explore/mlx-lm/issues/980)（hybrid 模型 prefix cache 全部失效，trim 不支持 RotatingKVCache/SSM） | **Campaign F-2 C2 trim 路径硬阻塞** | 上游 watch；owlmlx native trim_with_reason 防御层保留；hybrid 路径继续走 non-trimmable cache + full recompute |
| [mlx-lm #1178](https://github.com/ml-explore/mlx-lm/issues/1178)（server 不支持 prompt-cache-file） | mlx-lm subprocess backend 端不能用上游 prompt cache；owlmlx 必须自己管理 session KV | 维持现状，自有 `session_kv_cache.py` 路径独立于上游 |
| [mlx-lm PR #990](https://github.com/ml-explore/mlx-lm/pull/990)（native MTP for Qwen3.5/3.6） | 一旦 merge，owlmlx `gemma4_mtp_drafter.py` 这层有被吞掉的风险 | 上游 watch；F-1 endpoint 抽象保留——抽象是稳定的，drafter 实现可替换 |

**collective signal**：mlx-lm 在 prefix cache / multi-model / structured output 这三轴上**短期不会修**（重大缺陷长期 OPEN 且无 maintainer 表态）。这是 owlmlx 存在的根本理由，但也意味着 owlmlx 永远在与上游 substrate 的工程惯性较量——不能假设上游会主动配合。

### 4.4 SGLang xgrammar-2 (2026-05-04) 与 F-4 的关系

XGrammar-2 blog 自陈：
- "Speculative decoding support"
- 集成进 MLC-LLM / SGLang / vLLM / TRT-LLM 主干
- 加入 Structural Tag、tool calling

**这是否威胁 F-4 差异化？**

| 角度 | 答案 |
|---|---|
| xgrammar 层有 speculative support 声明？ | 是 |
| serving 层（SGLang/vLLM/MLC）有 byte-for-byte invariance 验证？ | **否**——SGLang #9187/#16541 同期 OPEN，vLLM #41967 同期 OPEN，MLC 无 invariance benchmark |
| 是 capability 层声明 vs runtime 层验证的差距？ | 是。**这是 xgrammar 声明 ≠ serving-runtime 验证** |

**结论**：xgrammar-2 不构成 F-4 thesis 威胁，反而是 F-4 thesis 的支撑——"structured generation 层声明 spec support" 与 "serving runtime 路径上 byte-for-byte invariance" 是不同的 capability gate，owlmlx F-4 主攻后者。

### 4.5 MLC-LLM 重心迁移信号的战略含义

tqchen 公开承认（[issue #3382](https://github.com/mlc-ai/mlc-llm/issues/3382)）MLC 团队重心已从 MLC-LLM serving 移向 TVM 底层 + xgrammar 模块化。含义：
- Apple Silicon 上 MLC-LLM 作为 serving runtime **正在被 mlx-lm 甩开**
- 但 xgrammar 作为 substrate 在跨 runtime 渗透——**未来 owlmlx 在 F-4 验证时，xgrammar 可能是引入的 reference rule engine，不是 invariance 验证对象**
- TVM 在 Apple Silicon 上的工程意义减弱（MLX 直接编译路径更短）

---

## 5. Sweep Targets（既有 doc 中需要 refresh 的过期断言）

按 [[feedback-stale-language-sweep]] 纪律，新 evidence 出现时需 sweep 既有 doc，不只是叠加新 section。下列 refresh 目标按文件归类，**未在本 snapshot 内执行**（避免 staging discipline 违规），由后续 follow-up round 处理：

### 5.1 `docs/architect/02-state-vs-market-gap.md`

| Line / 段落 | 当前写法 | 建议 refresh |
|---|---|---|
| §1 #9 Speculative Path Safety | "vLLM #41967；ToolSpec arXiv 2604.13519 2026 才出" | 补 SGLang #9187 #16541 + llama.cpp #23335 作为附加 evidence，cite 本 snapshot §3 |
| §1 #10 Structured-Output Invariance | "Claude API guaranteed" | 补 xgrammar-2 2026-05-04 "声明 spec support 但 invariance 未证" 的 nuance；cite 本 snapshot §4.4 |
| §2.3 Ollama / LM Studio 类 | 列了消费级 runtime 但未提 llama.cpp 是其上游引擎 | 加一行 "底层引擎：llama.cpp"，引用本 snapshot §3.3 |
| §3.1 spec×structured "Claude API 之外业界普遍无" | 抽象引用 | 直引本 snapshot §4.1.1 表格 |
| §3.2 KV Cache "vLLM v0.6+" | 版本陈旧 | 改为 v0.21（APC + FP8/NVFP4 + KV Offload），cite 本 snapshot §3.1 |
| §3.4 "mlx-knife 2.0.5" | 版本陈旧 | 改为 v2.0.6 + content_hash v2，cite 本 snapshot §3.6 |

### 5.2 `docs/source-of-truth/runtime-capability-matrix.md`

| Line / 行 | 当前写法 | 建议 refresh |
|---|---|---|
| Capability "Session-scoped native KV cache reuse" | trim_prompt_cache 缺陷描述是 owlmlx 内部视角 | 加一行 "上游 root cause: mlx-lm #980 (RotatingKVCache 不可 trim, SSM 不可 trim) OPEN 截至 2026-05-27"，让 F-2 C2 blocker 的上游 trace 在能力矩阵层可见 |
| Capability "Speculative execution status surface" | F-1 evidence landed | 加 cross-ref："业界对比见 [competitor-capability-matrix-20260527.md §4.1.1](competitor-capability-matrix-20260527.md)" |

### 5.3 `docs/source-of-truth/reference-runtime-comparison-matrix.md`

| 段落 | 建议 refresh |
|---|---|
| §1 Purpose | 当前 only oMLX/vMLX；建议加 footnote："broader competitor coverage 见 [competitor-capability-matrix-20260527.md](competitor-capability-matrix-20260527.md)" |

---

## 6. Recommended Follow-ups（evidence-only，不构成 commitment）

1. **F-4 plan-grade 应 cite 至少 4 个 competitor open issue 作为"业界未解决"的硬证据**：vLLM #41967 / #34650 / #40831；SGLang #9187 / #16541——这把 F-4 thesis 从"我们认为业界未解决"升级为"具名 cite 业界长期 open 的 invariance gap"
2. **mlx-knife content_hash v2 模式应评估是否借入 owlmlx model_lineage**——per-file SHA index + sentinel-based schema migration，是 owlmlx 已知 debt 的对症缓解
3. **mlx-lm upstream watch list**（任一 merge 都会影响 owlmlx 路线）：#980 / #1178 / PR #990——建议建立 owlmlx-side 的 upstream watch ledger，每月查一次
4. **SGLang xgrammar-2 与 F-4 应建立对比 test fixture 而非互不相关**——如果 F-4 完成 invariance 验证基础设施，可以反向跑一次 SGLang #9187 复现来量化 owlmlx 优势
5. **Wave G-3 README 刷新应明确"continuous batching / paged KV 不在 scope 是刻意选择而非 gap"**——基于本 snapshot §4.2 的 named competitor evidence，把"刻意不做"从模糊表述升级为"vLLM/SGLang/llama.cpp/MLC 全行业标配，owlmlx 单 host 单 worker by design"
6. **MLC-LLM 重心迁移对 owlmlx 的 xgrammar 引入决策有影响**——如果 owlmlx F-4 未来需要 reference grammar engine，xgrammar 是合理候选（同团队孵化、跨 runtime 中立）

---

## 7. Update Rule

本 snapshot 是 **dated** evidence record。Refresh 触发条件：

1. **任一竞品 major release**（semver bump 或等价）：vLLM / SGLang / llama.cpp / mlx-lm / MLC-LLM / mlx-knife
2. **任一 cited open issue 关闭**：特别是 mlx-lm #980 / #1178 / vLLM #41967 / SGLang #9187 #16541
3. **owlmlx 新增竞品对比需求**（如 TensorRT-LLM / TGI / Together Inference 进入对比 scope）
4. **12 轴框架在 [02-state-vs-market-gap.md] 改动**
5. **本 snapshot 内某 capability 标签被本仓库 evidence record 推翻**

不构成 update 理由：内部主观感受 / 路线图调整压力 / 想"声明 parity" 的冲动。

---

## 8. 诚实备注

- **本 snapshot 不是 reproducible benchmark**——所有 capability 标签来自公开声明 + open issue 反推，未做字节级独立验证
- **6 个竞品 release cadence 极快**，本 snapshot 在 2-4 周后有部分行可能过期（特别是 SGLang post 版本 / llama.cpp build 滚动）；任何引用本 snapshot 做战略决策的工作，应核对 cited URL 的当前状态
- **xgrammar / TVM 层并未单独建行**——它们是 substrate 而非 serving runtime；本 snapshot 关注 serving runtime layer，substrate 层 capability 在 §3.5 / §4.4 / §4.5 提及但未独立打分
- **未覆盖竞品**：TensorRT-LLM、TGI（HuggingFace text-generation-inference）、Together Inference、Fireworks、Anyscale Ray Serve、LightLLM、PowerInfer——这些与 owlmlx 场景距离更远，本轮未纳入 scope
- **本 snapshot 不替代** [02-state-vs-market-gap.md] 的策略读出 / [public-claim-matrix.md] 的外部传播红线 / [reference-runtime-comparison-matrix.md] 的 oMLX/vMLX 深度对比——三者都仍是各自范围的 source-of-truth

---

**Subagent evidence chain summary**：
- vLLM 调研：23 tool uses, agentId a92fdf236bc95dffd
- SGLang 调研：26 tool uses, agentId a41076d6947ece87b
- llama.cpp 调研：18 tool uses, agentId a9e8fd5a425055907
- mlx-lm 调研：24 tool uses, agentId a0dbbffae689678ee
- MLC-LLM 调研：22 tool uses, agentId aaac7a8bc2e451d4c
- mlx-knife 调研：11 tool uses, agentId a7650c39ddbb289f4

所有 6 份子调研报告以本 snapshot §3 各小节为最小可消费形式落盘；如需 reproduce 任一行的 evidence chain，可用对应 agentId via SendMessage 重新拉取完整 trace。
