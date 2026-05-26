# owlmlx 性能优化技术方案（2026-05-26）

> **Grade**：plan-grade · architecture intent
> **承载位置**：`docs/architect/07-perf-optimization-proposal-20260526.md`
> **下游 design-grade**：未起，每个方向通过后另开 `docs/architect/design/<feature>-spec.md`
> **触发**：2026-05-26 长上下文阶梯 bench 结果 + Rapid-MLX / vLLM / SuffixDecoding 等先进引擎调研
> **语言纪律**：plan-grade 允许 `plausible` / `candidate` / `pending`；不写 `supported`
> **Architect review note**：2026-05-26 复核后，本方案顺序原批准为 C → A → B；但 C 在 F-1 v1 contract 内必须以 `method=ngram` 暴露，SuffixDecoding 是该 method 的实现策略之一，不新增 `method=suffix_decoding`。
>
> **Order revision 2026-05-26 (C2 execution finding)**：C2 在 owlmlx 当前三主力 bench 模型（Qwen 3.6 27B 4bit / Gemma 4 31B 4bit / Qwen 3.6 35B-A3B 4bit）上撞结构性阻塞 —— 这些模型都走 mlx-lm hybrid cache（含 `ArraysCache` 不可 trim 层），speculative decoding 需要的 partial-accept rollback 物理上不可达，是 mlx-lm 上游 issue #980 的范围。**方向 A（prompt cache）大概率受同一上游 bug 影响**（部分前缀匹配同样需要 trim）。**方向 B（prefill chunking）只调 mlx-lm 已有的 `prefill_step_size` / `prompt_progress_callback`，不依赖 partial cache trim**。因此修正推进顺序为：**B 优先 → 等 mlx-lm 修 hybrid trim → 再做 A/C**。C0/C1 算法工作已 commit，对 trimmable 模型（Qwen 2.5 / Llama 3 等）有效，保留不浪费；B 的 hybrid 兼容性仍由 workload gate 判定，不预先写成 supported fact。

---

## 1. 我们现在到底在哪

2026-05-26 跑完了三个主力模型 × 7 个输入长度 × 3 次重复的完整 bench（63 cells，evidence ledger `files/evidence/owlmlx/bench/long-context-ladder/20260526T013407Z-long-context-ladder.jsonl`）。结果跟"我们差很多"的直觉**部分相反**：

| 模型 | 1k 输入速度 | 128k 输入速度 | 对照主流 |
|---|---|---|---|
| Qwen 3.6 35B-A3B 4bit（MoE） | **122 tps** | 64 tps | M4 Max 主流 55-70 tps ⇒ **持平或偏上** |
| Qwen 3.6 27B 4bit（密集） | 32 tps | 19 tps | 密集 27B 主流 30-40 tps ⇒ **持平** |
| Gemma 4 31B 4bit（密集） | 26 tps | 10 tps | 密集 31B 主流 15-25 tps ⇒ **持平或偏上** |

**结论一**：raw decode tps 上我们已经在主流区间。"100+ tps 主流"这个数字在 MoE 上确实是我们也能达到的 —— 122 tps 就在我们手上。

**结论二**：真正的差距不在 raw tps，而在三件**结构性的事**：

1. **默认 / subprocess / MoE serving 路径没有已验证的 prefix / prompt cache 复用** —— native backend 已有 experimental `session_kv_cache`，但默认 serving 还不能把同前缀第二轮请求稳定变成 cache hit。MoE 32k 输入要 12 秒、128k 要 106 秒；在默认路径上第二轮仍要重头算。
2. **长输入 prefill 时间线性恶化** —— 密集模型 128k 输入要 6-8 分钟才出第一个 token。这是 chat / agent / code-edit 场景的天花板。
3. **没有 spec decoding** —— 在结构化输出（agent / code-edit / 工具调用）场景下，外部最佳实践能跑出 2-10× 解码加速；我们一点没拿到。

本方案聚焦这三件事。

---

## 2. 三个改造方向总览

| 方向 | 改什么 | 用户可见效果 | 工程量 | 推荐顺序 |
|---|---|---|---|---|
| **B** Prefill chunking | 暴露 mlx-lm 已有 `prefill_step_size`，把 `prompt_progress_callback` 转成 owlmlx 内部 stream event | 长 prompt 不再"卡 6 分钟无信号"，能上报 prefill 进度；同时量化 chunk size 对 TTFT / 峰值内存 / within-chunk determinism / cross-chunk consistency 的影响 | 低-中（1-2 周） | **1（当前）** |
| **C** n-gram / SuffixDecoding probe | 加一层"基于历史输出做投机预测"的解码包装 | 同 prompt 重复模式下 decode **候选快 2-5×**；agent / code-edit 场景特别明显 | 中（3-4 周） | paused on mlx-lm #980 |
| **A** Prompt cache 在 MoE serving 路径落地 | 让 owlmlx 真正消费 mlx-lm 已有的 prompt cache 原语，让相同前缀第二次请求**跳过 prefill** | 多轮对话第 2+ 轮 TTFT 从几十秒掉到亚秒 | 中-高（3-4 周） | paused on trim risk |

**为什么现在改顺序**：

- **B 先做**：它不需要 rollback / trim hybrid cache，只暴露 mlx-lm 已有参数和 callback；风险小，能立刻补上长上下文进度可见和 chunk-size 量化证据。
- **C 暂停**：C0/C1 已证明算法和 batch verify 可行，但 C2 serving integration 在 hybrid cache 上需要 partial-accept rollback，当前被 mlx-lm issue #980 卡住。
- **A 暂停**：A 的 prefix / prompt cache 复用很有价值，但部分前缀匹配也可能碰到同类 trim 语义；在 B 不动 cache 的窗口里先把可执行项收口。

---

## 3. 方向 C — n-gram / SuffixDecoding speculative decoding

### 3.1 What

SuffixDecoding 是 Snowflake 在 NeurIPS 2025 公开、已 production 化的 model-free 投机解码方法（[arxiv 2411.04975](https://arxiv.org/abs/2411.04975)、[github suffix-decoding.github.io](https://suffix-decoding.github.io/)）。**不需要 drafter 模型**，靠两棵后缀树：

- **全局后缀树**：服务启动时从历史输出离线建（1000 条样本 0.3 秒，10 万条 ~62 秒）；运行时增量更新
- **每请求后缀树**：跟踪当前生成中的请求

每步解码时：找匹配模式 → 贪心扩展投机树 → LLM 单次 forward 验证整棵树 → 接受的 token 进全局树

### 3.2 Why（实测速度）

| 场景类型 | 输入特征 | 实测加速 |
|---|---|---|
| 开放聊天 | 低重复（entropy ~3.43） | 1.5× 起步 |
| SQL 生成 | 中度结构（entropy ~2.50） | **2.19×** |
| Agentic 任务 | 一般 | **5.3×** |
| 高度结构化（agent enrichment） | 极低 entropy ~0.17 | **10.41×** |

**对 owlmlx 直接意义**：OwlCoda 这种代码编辑场景天然是"高度结构化"类型 —— 代码模板、tool 调用 JSON、相邻编辑共享大量 token 序列。理论加速空间在 **2-5×**，但在进入 capability label 前必须用 repo-local OwlCoda-class workload 验证；不得把论文 / vLLM / Snowflake 数字直接升级成本地事实。

### 3.3 How

**实现 layer**：先把 C 作为 F-2 的 `method=ngram` 实装候选，而不是新增 F-1 method value。设计阶段可以把实现称为 SuffixDecoding，但 runtime surface 仍使用 F-1 v1 已锁定的 `ngram`。第一版不要直接承诺 full serving wrapper；先分三段：

1. **C0 offline verifier**：固定 token trace / fake logits / suffix tree 单元测试，证明 propose/accept/reject 语义正确。
2. **C1 local mlx-lm verifier canary**：绕过 `stream_generate`，用 model call 或局部 fork 的 generate step 验证"一批候选 token 单次 forward 验证"可行。
3. **C2 serving integration**：只有 C1 通过后，才在 `owlmlx/runtime/mlx_lm_subprocess_backend.py` 子进程端 decode loop 外包 wrapper。

算法本身可以新建独立 runtime 模块，但必须从第一轮 code-grade 起被 backend 或 kernel 消费，不能落成 spec-as-code：

```
owlmlx/
  speculative/
    suffix_decoding/
      __init__.py
      suffix_tree.py        # 数据结构：紧凑后缀树
      proposer.py           # 后缀树 → speculation tree 构造
      verifier.py           # 单次 forward 验证 + 接受决策
      runtime.py            # 与 mlx_lm 子进程 decode loop 的集成点
```

**关键设计点**：

1. **数据结构**：后缀树存 token id 序列，每节点带频次。论文给的 footprint 是 **10.75 bytes/token**，对 10 万历史 token 大约 1 MB，可控
2. **集成接口**：wrapper 模式，**不替换** mlx-lm decoder。在 stream_generate 的 token loop 外面包一层 "speculate → verify"
3. **fallback**：当后缀树置信度低于阈值时（distribution shift），降级到普通逐 token 解码。论文称分布漂移时初始降到 1.5×，500 个请求后恢复
4. **可关闭**：通过 [`owlmlx.speculative_execution_status`](design/F-1-spec.md) F-1 contract surface 暴露 `method=ngram`，能 disable / 监控接受率；SuffixDecoding 只作为该 method 的 `implementation_strategy` / notes，不扩 F-1 v1 method vocabulary
5. **不需要新模型**：纯算法 + 后缀树存储，部署上是 0 摩擦

### 3.4 Risk / Unknown

- mlx-lm 的 `stream_generate` 没有直接的"verify N candidate tokens in one forward pass"接口。我们要么 fork stream_generate，要么直接走 model.__call__ 自己拼。**这是最大的实现不确定点**
- 后缀树并发安全（多请求共享全局树时的锁竞争）。我们单 worker 设计下相对简单
- 接受率监控、动态阈值调整 —— 第一版可以静态阈值，第二版再加 adaptive

### 3.5 Effort

- C0 算法 + 数据结构 + fake verifier：**1 周**
- C1 mlx-lm verifier canary：**1 周**
- C2 decode loop 集成：**1 周**
- F-1 `ngram` surface wire + 接受率 metrics + OwlCoda-class workload 验证：**1 周**
- **Total：3-4 周**

---

## 4. 方向 A — MoE prompt cache 落地到 serving 路径

### 4.1 What

mlx-lm **已经有完整的 prompt cache 原语**（我们查过本地 `mlx_lm/models/cache.py`）：

- `make_prompt_cache(model)` — 自动按模型架构选 cache 类型
- `KVCache` / `RotatingKVCache` / `ChunkedKVCache` / `QuantizedKVCache` / `LRUPromptCache` / `PromptTrie`
- MoE 模型自己实现 `make_cache()` 方法，所以 mlx-lm 对 MoE 也有 cache 支持

**我们缺的不是底层 cache 原语**，而是**让 owlmlx serving 路径真正用上它们**。

现状：
- 我们自己写过 [`owlmlx/session_kv_cache.py`](../../owlmlx/session_kv_cache.py)（636 行）—— 但**只服务 native backend**，且只验证了密集模型；native backend 已能 report `upstream_make_prompt_cache_reachable` / `bound_session_scoped_experimental`
- subprocess backend（`mlx_lm_subprocess_backend.py`，默认 serving 路径）有 persistent child / generation reuse 可见性，但没有把 `mlx_lm.models.cache.make_prompt_cache` 作为跨请求 cache handle 消费
- MoE 模型走默认 subprocess 路径时，每次请求仍按 full prefill 处理；MoE cache hit 的 byte-equivalence / health budget 尚未验证

### 4.2 Why（量化收益）

bench 实测数字直接说话：

| 场景 | 现状（每次 prefill） | 加 prompt cache 后第 2+ 轮 |
|---|---|---|
| Qwen 35B-A3B 32k 输入第二轮 | 12 秒 prefill + decode | cache hit 后目标 < 5% baseline TTFT（是否亚秒待测） |
| Qwen 35B-A3B 128k 输入第二轮 | 106 秒 prefill | cache hit 后目标 < 5% baseline TTFT |
| Qwen 27B 128k 输入第二轮 | 360 秒（6 分钟） | cache hit 后目标 < 5% baseline TTFT |

**对 OwlCoda 这种"上下文是项目代码、每次只改局部"的场景**，cache 命中率候选很高 —— 但 95% 前缀重叠只能作为 workload 假设，必须落成 N≥20 的真实请求分布证据后，才能写成 capability 事实。若命中成立，第二轮长上下文请求存在 10-100× 的 TTFT 杠杆。

### 4.3 How

**两条改造路径，分别对应两个 backend**：

#### 路径 A1 — native backend：扩展现有 session_kv_cache

- 工作量小：[`session_kv_cache.py`](../../owlmlx/session_kv_cache.py) 已经做了 session 隔离、TTL、watermark eviction
- 需要做的：把 entry 的 `cache_object` 字段从"假设是 `KVCache` list"扩展到支持 MoE 模型自定义的 cache 类型（通过 `model.make_cache()` 返回什么就存什么）
- 增加 hit/miss 在 MoE 上的字节等价性验证（B-1a/B-1b 测过密集 7.4× / 2.246×，MoE 数字未知）
- **Effort：1-1.5 周**

#### 路径 A2 — subprocess backend：新建 cache 转储机制

- subprocess backend 把模型加载在子进程里，cache state 跨 IPC 是大问题
- **两个候选方案**：
  - **A2-a 子进程内 cache reuse**：当前 backend 已是 persistent child，但 request exchange 仍是单请求语义；需要在 child 内维护 prompt cache state，并把请求间 cache hit/miss/eviction 作为 runtime truth 返回
  - **A2-b cache 序列化到磁盘**：每次请求结束把 cache state 序列化（mlx-lm 已有 [issue #917](https://github.com/ml-explore/mlx-examples/issues/917) 讨论这个），下次请求先 load。读盘成本可能抵消 prefill 节省，**不建议**
- 推荐 **A2-a**，跟方向 B（prefill chunking）有协同 —— 都依赖 child 内部可控的 prefill / decode loop，而不是单纯调用黑盒 `stream_generate`
- **Effort：2-3 周**

#### 整体 Effort

- A1（native）：1-1.5 周
- A2（subprocess + resident worker）：2-3 周
- F-1 surface 扩展 `cache_sharing` 字段反映真实 cache state（已经在 [F-1-spec.md §4.9](design/F-1-spec.md) 设计了 shape）：1-2 天
- 测试 + B-1a-style 字节等价性验证 + 真实多轮 workload 加速验证：1 周
- **Total：4-6 周**

### 4.4 Risk / Unknown

- **MoE cache 的内存压力**：MoE 一个层有大量 expert 权重 resident，KV cache 加 prompt cache 后内存压力比密集模型高。需要重测 watermark / eviction 在 MoE 上的行为（这正好接 B-1c §2 那条主线）
- **subprocess resident worker 改造**会动 `mlx_lm_subprocess_backend.py` 核心逻辑，与 Wave H 拆分 server.py 的工作要协调
- mlx-lm 自己的 `LRUPromptCache` / `PromptTrie` 我们要不要直接复用？还是 owlmlx 维持自己 session 隔离语义？**建议复用 mlx-lm 原语**减少代码量，session 隔离逻辑放外层
- vLLM 上有报告："MoE 模型 KV cache 有 double penalty"（[$qs$ 不等式 arxiv](https://arxiv.org/pdf/2603.08960)）—— expert routing 碎片化 + 大权重池挤占 KV headroom。**MoE prompt cache 实测收益可能比理论值低**，需要 N≥20 验证

---

## 5. 方向 B — Prefill chunking

### 5.1 What

vLLM V1 默认开启 chunked prefill（[vLLM optimization docs](https://docs.vllm.ai/en/stable/configuration/optimization/)）：

- 长 prompt 分成大小为 `max_num_batched_tokens`（默认 2048）的块
- 调度器优先 decode 请求，剩余 token budget 用来跑 prefill chunks
- 一个长 prompt 跨多个 scheduler step 完成 prefill
- 主要价值是**多请求场景下** decode/prefill 交错，提升吞吐 + 降 ITL

### 5.2 Why（对 owlmlx 的收益分析）

owlmlx 的设计前提是 `MAX_GENERATION_CONCURRENCY=1`（单 worker by design），所以 vLLM 那个"交错 decode 和 prefill"的核心价值 **拿不到**。chunked prefill 对我们的实际价值：

- ✅ **TTFT 进度可见**：128k 输入跑 6 分钟，用户什么都看不到。分块后可以每跑完一块上报"已处理 X% prompt"，体验改善（但不是物理变快）
- ✅ **给 cache miss 让出推测窗口**：分块期间可以检查后续 chunk 跟 cache 是否还有部分匹配 —— 跟方向 A 协同
- ❌ **不能直接降 TTFT**：单 worker、无并发请求，物理总计算量没省
- ❌ **不能直接提吞吐**：同上

### 5.3 How

mlx-lm 已经提供 B 所需的直接 building blocks：

- `stream_generate(..., prefill_step_size=N, ...)`
- `prompt_progress_callback(processed, total)`

我们的实现不手动切 prompt、不 fork mlx-lm prefill loop，也不扩 OpenAI / Anthropic SSE 协议。owlmlx 侧只做三件事：

- 在 child runner 中把 per-request `prefill_chunk_tokens` 和 env fallback `OWLMLX_PREFILL_CHUNK_TOKENS` 映射到 mlx-lm `prefill_step_size`
- 仅在显式请求 chunk/progress 的 internal streaming path 注册 `prompt_progress_callback`，把 callback 转成 child JSONL `event="prefill_progress"`，parent 再 yield 为内部 `StreamEvent`
- 新增 workload runner 测 3 模型 × 4 context × 3 chunk size 的 TTFT / 峰值 RSS / within-chunk determinism / cross-chunk consistency

**Effort**：1-2 周（主要是参数透传、stream event plumbing、workload/evidence）

### 5.4 Risk / Unknown

- 不同 `prefill_step_size` 的**数值路径**必须记录。理论上 attention 是 causal 的，但 C1 canary 和 B smoke triage 已经证明 mlx-lm 不同 prefill execution path 可能出现 deterministic 输出分叉。B 的硬 gate 是**同一 chunk size 重复运行必须 byte-for-byte deterministic**；跨 chunk 一致率降为 diagnostic-only
- progress event 先只走 owlmlx 内部 stream channel；非 stream subprocess `_exchange` 仍是单 payload 协议，B 不得让非 stream path 先吐 progress

### 5.5 为什么现在排第 1

原计划里，B 的真实价值主要是用户体验（进度可见），不是物理加速，所以排在 C/A 之后。C2 后发现 C/A 都被 hybrid trim blocker 牵住，B 反而成为唯一当前可执行、且不会触动 Track 1 cache 模块的性能方向。它不升 supported，不写加速结论，只补配置面、进度面和测量面。

---

## 6. 推荐推进顺序 + 时间窗

| 周次 | 方向 | 阶段 | 关键交付 |
|---|---|---|---|
| W1 | **B Prefill chunking** | B contract + stream event plumbing | `prefill_chunk_tokens` → `prefill_step_size`；explicit stream-only `prefill_progress` event；非 stream `_exchange` 不变 |
| W1-W2 | **B** | workload + evidence | 3 模型 × 4 context × 3 chunk size；TTFT / peak RSS / within-chunk determinism / cross-chunk consistency rollup |
| blocked | **C ngram/suffix** | C2 serving integration | 等 mlx-lm issue #980 支持 hybrid cache trim / rollback 后重开 |
| blocked | **A prompt cache** | MoE / subprocess cache reuse | 等 Track 1 与 hybrid trim 风险收口后重开 |
| later | **整体** | 综合 bench + 对外可对照的速度故事整理 | 只有 B/A/C 各自 evidence clean 后再重跑 long-context-ladder 对照 |

**关键依赖**：当前不再要求 C 先完成。B 的优势是独立、不动 cache trim、不动 `session_kv_cache.py`，因此先把可执行的配置面 / 进度面 / measurement 面补齐。

**关键里程碑**：B 末尾不产出"物理加速"故事，只产出长上下文 prefill 可观测性和 chunk-size 风险画像；C/A 的速度故事等上游 blocker 清掉后再恢复。

---

## 7. 不做什么（明确防 scope creep）

- **不做 continuous batching**：违反 `MAX_GENERATION_CONCURRENCY=1` 边界（[01-mainline-roadmap.md §IV.2](01-mainline-roadmap.md)）
- **不做真 drafter 模型投机解码（DFlash / draft model）**：W1-W12 内不做。理由：需要训 / 找配对的 drafter 模型，复杂度跨数量级。F-3 Gemma resident MTP A/B 是另一条独立路线
- **不做 KV cache 自身的量化压缩**（Rapid-MLX 的 TurboQuant V-cache）：mlx-lm 有 `QuantizedKVCache` 但 owlmlx 主线 0.3.0 不在这个轴上投入，等 A/C 落地后再评估
- **不动 mlx-community 4bit 量化变体**：我们昨天跑的 DWQ 下载尝试已经死了，且既然默认 4bit 已经持平主流，不值得继续投入。**未来要换量化（DWQ / OptiQ）是独立小 round**
- **不做 OwlOps 端的 perf 可视化扩展**：方向 A 落地后 cache hit rate 应该走 F-1 status surface 暴露，OwlOps 端能不能可视化是它自己 round 的事

---

## 8. 怎么证明改造有效（度量纪律）

每个方向必须有一致的 evidence 形态，对照 2026-05-26 这次的 baseline。长上下文基础能力复用 `scripts/bench/long_context_ladder.py`；C 方向允许 design-grade 定义一个固定 OwlCoda-class workload runner，但必须复用同一套 JSONL / rollup / host metadata discipline，不能另起泛化 bench framework。

| 方向 | 关键指标 | 对照 baseline |
|---|---|---|
| **C** ngram/SuffixDecoding | OwlCoda-class workload 上的 wall-clock decode 时间、accepted_tokens、accepted_rounds、fallback rate | 同 workload 关 `method=ngram` 的实测；目标 ≥2× |
| **A** Prompt cache | 第二轮同 prefix 请求的 TTFT | 第一轮 prefill 时间；目标 cache 命中时 < 5% |
| **B** Prefill chunking | 长输入 TTFT / 峰值 RSS 可测 + 内部 stream `prefill_progress` 事件可见 + within-chunk determinism；cross-chunk consistency 仅诊断 | 2026-05-26 long-context baseline；默认路径目标 ±5% 内，非默认 chunk size 不预设提速 |

**统一 evidence 落点**：每个 design-grade spec 自定子目录；B 使用 `files/evidence/owlmlx/bench/prefill-chunking/<时间戳>-*.jsonl`。

**晋级路径**：每个方向都要有 N≥20 重复 + clean health 才上 `partial`；`supported` 要走 §1a Promotion Gate（不在本方案范围）。

---

## 9. 与现有 roadmap / campaign 的关系

| 现有工作 | 与本方案的关系 |
|---|---|
| **F-1 `speculative_execution_status` surface**（[design/F-1-spec.md](design/F-1-spec.md) 已落地） | 方向 C 消费既有 `method=ngram` surface；SuffixDecoding 是 `ngram` 的实现策略 / notes。方向 A 的 cache state 走 F-1 的 `cache_sharing` 字段 ✓ |
| **B-1c §2 drift triage**（Track 1，仍在进行）| 方向 A 在 MoE 上验证时会触动 session_kv_cache，跟 §2 是同一份模块。**必须等 §2 收口后才动 A1**（路径冲突） |
| **F-2 ngram probe**（Campaign F · F2，原 roadmap）| 本方案 **方向 C 就是 F-2 的具体实装**。可以把 F-2 retitle 为"ngram / SuffixDecoding probe"，但不改 F-1 v1 vocabulary |
| **F-3 Gemma resident MTP A/B**（Campaign F · F3）| 不在本方案，独立路线。条件：等真有用的 Gemma drafter |
| **Wave H2 server_routes 拆分** | B 第一版不扩 OpenAI / Anthropic SSE，不要求动 server.py；若后续把 progress 暴露到 HTTP streaming，再与 H2 协调 |

**主线对齐声明**：本方案不修改 [01-mainline-roadmap.md](01-mainline-roadmap.md) 的 12+ 月战略路线，只是把 Campaign F 的 F-2 具体化、把 Campaign B 的 prompt cache 工作扩到 MoE。**身份与边界（单 worker / memory-discipline-first）不变**。

---

## 10. References

### 外部技术参考

- **SuffixDecoding 论文**：[arxiv 2411.04975](https://arxiv.org/abs/2411.04975)
- **SuffixDecoding 主页 + 代码**：[suffix-decoding.github.io](https://suffix-decoding.github.io/)
- **SuffixDecoding production 集成（Snowflake Arctic Inference / vLLM）**：[snowflake engineering blog](https://www.snowflake.com/en/engineering-blog/suffixdecoding-arctic-inference-vllm/)
- **vLLM chunked prefill**：[docs.vllm.ai/optimization](https://docs.vllm.ai/en/stable/configuration/optimization/)
- **vLLM 前缀缓存 / MoE 实践**：[llm-d.ai/blog/kvcache-wins-you-can-see](https://llm-d.ai/blog/kvcache-wins-you-can-see)、[deepwiki vllm KV cache](https://deepwiki.com/vllm-project/vllm/3.4-kv-cache-management-and-prefix-caching)
- **mlx-lm prompt cache 现状**：[github mlx-lm](https://github.com/ml-explore/mlx-lm)、[mlx-examples issue #917](https://github.com/ml-explore/mlx-examples/issues/917)
- **mlx-lm hybrid 模型 prefix cache bug**：[mlx-lm issue #980](https://github.com/ml-explore/mlx-lm/issues/980)
- **MoE 推理 double penalty 论文**：[arxiv 2603.08960](https://arxiv.org/pdf/2603.08960)
- **Rapid-MLX（直接竞品）**：[github raullenchai/Rapid-MLX](https://github.com/raullenchai/Rapid-MLX)

### 内部 baseline

- 2026-05-26 长上下文阶梯 bench：`files/evidence/owlmlx/bench/long-context-ladder/20260526T013407Z-long-context-ladder.jsonl`
- 现有 session_kv_cache：[`owlmlx/session_kv_cache.py`](../../owlmlx/session_kv_cache.py)
- F-1 contract surface：[design/F-1-spec.md](design/F-1-spec.md)
- 主线 roadmap：[01-mainline-roadmap.md](01-mainline-roadmap.md)

---

## 11. 状态 / 下一步

- **当前状态**：plan-grade 已按 C2 blocker 重新排序；方向 C 的 F-2 C0/C1 已完成并通过，但 C2 serving integration blocked on mlx-lm hybrid trim；B code-grade 已实现参数 / progress plumbing，smoke + half workload 支持 partial 收口：同一 chunk size deterministic，progress event observable，跨 chunk divergence 作为 diagnostic-only；64k targeted 已证明 Qwen 27B 可跑但单 cell 9-10 分钟级，Qwen 35B-A3B 64k targeted 6/6 pass 且 chunk 2048/8192 明显优于 512
- **下一步**：
  - 方向 B 补 full workload：已完成 half workload `20260526T090253Z`（3 模型 × 4k/16k/32k × 3 chunks × N=2，54/54 pass，elapsed=1720.072s）；64k supplement `20260526T133018Z` 已完成 Qwen27 run-1 三档 chunk（3/3 pass，TTFT 563-605s）；Qwen35 targeted `20260526T140719Z` 完成 6/6（median TTFT 173.63s / 144.21s / 147.08s）。下一步按 per-model targeted 64k schedule 补 Gemma；cross-chunk consistency 只记录不 gate
  - 方向 C 保留 C0/C1 与当前 C2 attempt，不继续 serving integration，等 mlx-lm issue #980
  - 方向 A 暂停，不动 `session_kv_cache.py` / Track 1 文件
- **每个 design-grade spec 评审通过后**才进 code-grade（依 [01-mainline-roadmap.md Part VIII.3](01-mainline-roadmap.md) 层级 handoff 纪律）

---

## 12. 变更历史

| Date | 变更 | 由 |
|---|---|---|
| 2026-05-26 | 初稿，基于当日长上下文 bench + 外部最佳实践调研 | architect session |
| 2026-05-26 | 复核修订：锁 C→A→B 顺序；将 C 的 surface 收敛到 F-1 v1 `method=ngram`；收窄 prompt-cache 现状措辞；把 C 拆成 C0/C1/C2；补 evidence 纪律 | Codex architect review |
| 2026-05-26 | 状态更新：F-2 C0/C1 已完成并通过；C2 serving integration 成为方向 C 下一步 | C1 closeout |
| 2026-05-26 | C2 blocker 后重排：B 优先；C/A 暂停；B 使用 mlx-lm `prefill_step_size` / `prompt_progress_callback`，不扩 HTTP SSE，不预设 hybrid supported 结论 | B kickoff review |
| 2026-05-26 | B code-grade smoke：参数 / progress plumbing 工作，但 Qwen 27B 4bit 4k prompt 的 chunk 512 vs 2048 cross-chunk consistency 失败；进入 numeric-path triage | B smoke closeout |
| 2026-05-26 | B gate 修订：determinism smoke `20260526T084239Z` 证明同一 chunk size 重复运行必须 deterministic；跨 chunk divergence 确认为 mlx-lm `prefill_step_size` deterministic numeric-path 差异，降为 diagnostic-only；B partial 收口，等待 full workload | B quality gate |
| 2026-05-26 | B half workload `20260526T090253Z`：54/54 cells pass，elapsed=1720.072s，within-chunk determinism 27/27 repeated groups passed，progress observable，cross-chunk consistency 12/18 groups identical (diagnostic-only) | B half workload |
| 2026-05-26 | B 64k partial `20260526T133018Z`：Qwen27 64k run-1 chunks 512/2048/8192 all pass，TTFT 591.8s / 563.7s / 605.4s，progress observable；stopped after run-1 because default order makes Qwen27 64k a 30+ minute front-loaded blocker | B 64k triage |
| 2026-05-26 | B Qwen35 64k targeted `20260526T140719Z`：6/6 pass，elapsed=938.612s，within-chunk determinism passed，cross-chunk consistency 1.0，median TTFT 173.63s / 144.21s / 147.08s for chunks 512 / 2048 / 8192 | B 64k targeted |
