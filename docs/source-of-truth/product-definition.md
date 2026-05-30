# owlmlx Product Definition

> Status: authoritative
> Updated: 2026-05-23（§5.3 vMLX 边界按 2026-05 现实校正；新增 §11 Internal Replacement-Grade Depth Posture · §1–10 历史定义维持 2026-04-09 口径）

## 1. Formal Definition

`owlmlx` is our self-owned runtime project for MLX-based model serving and
runtime management on Apple Silicon.

Its role is to become the runtime source of truth for the capabilities we
actually need, rather than extending another runtime indefinitely through local
patches and integration glue.

## 2. Frozen Project Statements

The repository is defined by four frozen statements:

1. `owlmlx` is our own runtime.
2. Its direction is to replace `oMLX`, while absorbing valuable ideas from
   `oMLX`, `vMLX`, and related systems as `owlmlx`'s own architecture.
3. The `large-weight runtime path` is the first mature path inside `owlmlx`;
   `Kimi` is the first validated specimen on that path.
4. The desktop product shell and integration layer above `owlmlx` is not the
   runtime source of truth, regardless of current repository naming.

## 3. Why This Is a Runtime Project

`owlmlx` is justified by runtime-specific goals that have already emerged in our
work:

- Multi-model switching under constrained unified memory
- Memory governance during load, unload, restart, and recovery
- Switch safety when active requests, cache pressure, or restart conditions
  exist
- Runtime truth surfaces that expose honest state to operators and upper layers
- Background-heavy serving for very large-weight models
- Runtime governance for hazardous and host-risking operations

These goals define a runtime program with its own architecture and capability
matrix.

## 4. Formal Runtime Principles

The following are not implementation anecdotes. They are formal runtime
principles of `owlmlx`.

### 4.1 Memory Governance Under Multi-Model Switching

`owlmlx` treats memory governance as a first-class runtime responsibility.

The runtime must make explicit decisions about load, unload, eviction, reclaim,
and restart behavior when multiple models compete for constrained unified
memory. "The model loaded successfully once" is not an adequate success
criterion.

### 4.2 Switch Safety And Active-Request Protection

`owlmlx` treats switching safety as a correctness requirement.

Runtime transitions must account for active requests, in-flight work, and
pressure conditions so that model switching does not silently corrupt serving
behavior or destabilize the runtime under load.

### 4.3 Runtime Truth Exposure

`owlmlx` requires runtime truth to be explicitly exposed upward.

The runtime must surface authoritative state about load status, memory
conditions, switching outcomes, runtime mode, and path-specific limitations.
Upper layers should consume runtime truth, not guess it.

### 4.4 Background-Heavy Serving

`owlmlx` explicitly recognizes that some runtime paths are background-heavy by
nature.

When a workload does not honestly support foreground-interactive behavior, the
runtime should model it as a background-heavy path rather than pretending it
belongs to the same product posture as smaller or faster interactive paths.

### 4.5 Runtime Governance

`owlmlx` treats hazardous operations, safe-resume rules, and heavy execution
protocols as runtime responsibilities.

If a path can threaten host stability or requires controlled re-entry after an
incident, that governance belongs inside runtime truth rather than being left as
temporary project memory.

## 5. Relationship To External Systems

### 5.1 MLX

`MLX` is the underlying compute and tensor substrate.

It is not the runtime identity of this project.

### 5.2 oMLX

`oMLX` is a major reference system and an immediate replacement target.

It matters because it demonstrates useful runtime mechanisms and because our
current platform work has historically depended on it. It does not define
`owlmlx`'s identity.

### 5.3 vMLX

`vMLX` 在 2024–2025 早期是开源 MLX serving project；到 2026-05 已演进为
**Apple 官方背书的 Apple Silicon 单机全栈本地 LLM 方案**（OpenAI / Anthropic
兼容 API + 20+ tool 整合 + vmlx.net 稳定站点）。这改变了 owlmlx 的边界陈述
（旧 README 表述"continuous batching / 多 host / 多租户 cluster 看 oMLX / vMLX"
已经不准；vMLX 在单机端已是 Apple 官方背书的全栈，不需要看向多 host）。

历史定性仍然成立：vMLX 贡献了 owlmlx 可借鉴的实现想法、运维模式、打包范式，
且**不是** owlmlx 的 origin story。

**当前边界**（2026-05-23 校正 · 与 §11 互锁）：

owlmlx 与 vMLX 在单机 Apple Silicon 上**场景部分重叠**（OpenAI / Anthropic
API 端点），但**架构定位不同**：

- owlmlx 强制 **memory-discipline-first**——`MemoryWatermark` + settle
  barrier 是每条 load 路径的硬契约；`MAX_GENERATION_CONCURRENCY = 1` 是
  MLX/Metal 同进程并发不安全的物理结论；vMLX 偏向 throughput-first
- owlmlx 把 **capability honesty + speculative path safety + governance**
  作为发版门控（§1a Promotion Gate + evidence-language calibration）；
  vMLX 不以此为闭合标准
- owlmlx 与 **OwlOps / OwlCoda / OwlMom** 形成内部消费闭环
  （`/v1/runtime/*` 27+ 路由已 supported · OwlOps 27 行 ledger live）；
  vMLX 是开源全栈，无对应契约关系

差异化轴明确为 **Reliability + Provenance + Governance**，不是 raw
throughput。详见 §11。

### 5.4 Product Shell Layer

The desktop product shell sits above `owlmlx`.

It integrates runtime truth into user-facing desktop workflows, routing,
operator surfaces, and system lifecycle. It is not the runtime source-of-truth
repository.

Current repository history may still use legacy names for this shell layer, but
those names should not be treated as permanent runtime-truth terminology.

## 6. Adoption Model

`owlmlx` is a self-owned runtime, but self-owned does not mean full rewrite.

### 6.1 Formal Adoption Rule

`owlmlx` reuses open-source runtime mechanisms wherever they are proven and
useful. It does not require — and does not intend — a ground-up rewrite of
every execution layer beneath it.

What `owlmlx` owns is:

- runtime identity
- runtime principles
- runtime governance
- runtime truth contracts
- runtime path semantics
- extraction direction

What `owlmlx` borrows freely:

- MLX tensor execution substrate
- loader and model-format machinery from the MLX ecosystem
- cache scheduling ideas from `oMLX`
- serving and packaging patterns from `vMLX`
- any proven open-source mechanism that fits `owlmlx`'s own principles

### 6.2 Adoption Boundary

When a borrowed mechanism enters `owlmlx`, it accepts `owlmlx`'s capability
labels and governance semantics. The origin system does not automatically
define it as `supported` in `owlmlx`.

Borrowed implementation that has not been evaluated against `owlmlx` runtime
principles must be labeled `partial` or `experimental`, never `supported`.

### 6.3 What Adoption Is Not

- Adoption is not re-branding another project's code as `owlmlx`.
- Adoption is not pretending `owlmlx` invented something it borrowed.
- Adoption is not avoiding credit where implementation came from.
- Adoption is not declaring independence for the sake of optics.

### 6.4 Why This Rule Matters

Without a formal adoption model, `owlmlx` risks two failure modes:

1. **Full-rewrite theater** — wasting effort reimplementing things that already
   work, in order to "look independent"
2. **Identity collapse** — borrowing so heavily that `owlmlx` becomes a thin
   wrapper with no owned truth, defeating the purpose of the project

The adoption model exists to occupy the correct middle ground: own the truth
layer, reuse the execution layer, and be honest about which is which.

## 7. Extraction Map

`owlmlx` needs a disciplined separation between runtime judgments we already own,
ideas we plan to internalize, and external references that are not yet `owlmlx`
capabilities.

### 7.1 Already Ours In Runtime Judgment

These are already part of `owlmlx`'s runtime direction, regardless of where all
implementation currently lives:

- memory governance under multi-model switching
- switch safety and active-request protection
- runtime truth exposure as an owned contract
- background-heavy serving as an explicit runtime class
- runtime governance for hazardous operations and safe-resume

### 7.2 Borrow And Internalize

These may be borrowed from external systems, but only by being rewritten as
`owlmlx` architecture:

- cache, scheduling, and lifecycle ideas from `oMLX`
- serving and packaging patterns from `vMLX`
- any future runtime mechanism that fits `owlmlx`'s own principles and
  capability model

### 7.3 External Reference Only

The following do not count as `owlmlx` supported capability merely because they
exist elsewhere:

- an external runtime feature we have not adopted into `owlmlx` truth
- an upstream admin or UI surface we only observe from outside
- a specimen-specific behavior that has not been elevated into path-level or
  core-runtime truth

## 8. First Mature Path

The first mature path in `owlmlx` is the `large-weight runtime path`.

This path exists for models whose weight size, loading behavior, latency
profile, and serving pattern do not fit standard interactive runtime
expectations.

Current truth:

- It is background-heavy rather than foreground-interactive
- It requires honest capability labels
- It should not be named after a single specimen forever
- `Kimi` is the first validated specimen on this path

## 9. Current Non-Claims

`owlmlx` does not currently claim:

- that generalized foreground runtime is fully solved
- that all current platform runtime behavior already belongs in this repository
- that external runtime ideas can be copied without reinterpretation
- that the first mature path is the only future path

## 10. Product Success Criteria

`owlmlx` starts succeeding when it can do three things clearly:

1. Define runtime truth without borrowing identity from upstream projects
2. Separate runtime ownership from desktop-shell ownership
3. Provide a stable home for runtime-specific evolution, extraction, and
   productization

## 11. Internal Replacement-Grade Depth Posture（2026-05-23 addendum）

> Status: authoritative addendum to §1–10
> 来源：`docs/architect/01-mainline-roadmap.md §IV.1 / §IV.5`（plan-grade）
> 触发：2026-05-10 战略转向 + governance commit `a21a0a2c`（release channel
> split: owlmlx engineering ≠ OwlCoda consumer readiness）

§1–10 的 formal definition、frozen project statements、runtime principles、
adoption model 全部维持不变。本节是 2026-05-10 战略转向后必须补充的**身份
精炼**——把 §1 的 "runtime project for MLX-based model serving and runtime
management on Apple Silicon" 进一步收口为：

> **owlmlx 的 12+ 月战略身份是**：为 Apple Silicon 单机企业级 agentic /
> batch evaluation 场景而生的 **memory-discipline-first replacement-grade
> MLX runtime**。

### 11.1 服务对象收口

- **In**：单机 Apple Silicon (Mac Studio / Mac Pro) · 1–10 simultaneous
  users behind a request queue · 企业级 agentic / batch evaluation 场景 ·
  长 uptime · 模型 swap 频繁
- **Out**：消费级单用户 UI（LM Studio / Ollama / Apple Foundation Models
  已占位）· 多 host fleet · 多租户 cluster · 持续 batching throughput
  竞速

### 11.2 差异化三轴（与 §4 Formal Runtime Principles 互锁）

| 轴 | 含义 | 对应 §4 原则 |
|---|---|---|
| **Reliability** | speculative path safety + structured-output invariance + repeatability (N≥20) | §4.1 memory governance · §4.2 switch safety |
| **Provenance** | request lifecycle 事件流 + artifact 来源链 + spec accept/reject ratio + reproduce metadata | §4.3 runtime truth exposure |
| **Governance** | capability honesty + admission/eviction 公开算法 + OwlOps consumption | §4.5 runtime governance + §6 adoption model |

**不追赶**（明示 · 与 §9 Current Non-Claims 一致 · 扩展）：

- raw throughput（vMLX 已饱和单机端 · 见 §5.3）
- continuous batching（vllm-mlx 已实装；owlmlx README "not in scope"）
- 消费级 UI（LM Studio / Ollama / LMM Studio 已占位）
- Apple Foundation Models 同质化（macOS Tahoe 26 + FM 框架已覆盖消费级
  本地推理）

### 11.3 边界资产位置（Adjacent Assets · 不入 owlmlx mainline）

| 资产 | 与 owlmlx 的边界关系 |
|---|---|
| **OwlRunKit** | owlmlx 之外的 lifecycle / env broker 候选位。owlmlx 暴露 `pre_load_check` / `host_pressure` / `model_visibility` 等 runtime-owned contract 供其调用；owlmlx 不拥有这些能力 |
| **`llm_router`** | 过渡资产（transitional）。当前承担"几条本地 runtime 之间的路由切换"，待 owlmlx replacement-grade 后逐步由 owlmlx mainline 替代或由 OwlOps 上收。**不**入 owlmlx mainline；任何 `llm_router → owlmlx` 反向依赖出现视为风险事件 |
| **OwlCoda** | 上层消费者（不是 owlmlx 身份组成）。release channel split (`a21a0a2c`) 已确立 **owlmlx engineering ≠ OwlCoda consumer readiness**——OwlCoda 卡顿**不**延迟 owlmlx 主线 |
| **OwlMom** | 上层消费者（间接）。5 Vue 页面已 FROZEN · 数据走 OwlOps 聚合 · 不直接消费 `/v1/runtime/*` |

任何 wave 不得把 OwlRunKit / `llm_router` 的能力**下沉到** owlmlx 内部模块。
协作仅通过 runtime-owned HTTP / contract surface 暴露字段。

### 11.4 Re-Open 发版条件（架构师诚实预测 · 不承诺）

owlmlx 公开发版的再开放门槛冻结为三条 reopen condition，每条对应一个
Campaign 簇：

| RC | 条件 | 对应 Campaign | 估计达成时点 |
|---|---|---|---|
| RC1 | 至少 3 条主线 model family 有 N≥20 重复运行证据 | Campaign A + C + D | 6–9 月 |
| RC2 | 至少一个 owlmlx 自有、超出 stock `mlx_lm`（仅 load+generate）的 runtime 能力——可建在 `mlx_lm` 之上但提供其不具备的能力（如跨请求 session-KV 复用 / grammar 约束解码 / native MTP） | Campaign B（session KV）+ Campaign F（spec on native）+ Campaign D（DS4 native MTP） | 9–12 月 |
| RC3 | OwlOps 稳定消费 live runtime truth 并形成内部 operational 闭环 | Campaign E | 6–9 月 |

> **RC2 措辞修正（2026-05-30）**：原表述"非 wrapping mlx_lm"不准确——owlmlx 的原生后端本身就 wrap 了 `mlx_lm.stream_generate`（见 `native-mlx-backend-capability-matrix.md` 的 `decode_step` 行，已标 `supported`），且 Mac 上的 runtime 普遍建在 MLX / `mlx_lm` 之上。RC2 的真实门槛是"owlmlx **自有、超出 stock `mlx_lm` 的 load+generate** 的能力"，不是"不用 `mlx_lm`"。grammar 约束 lane（F-4，`partial`）与 session-KV 复用是符合该定义的候选；是否满足 RC2 仍走单独 review，不在此自动判定。

具体 Wave / Gate 路线见 `docs/architect/01-mainline-roadmap.md §V`。本节
**不**承诺时点；任何加速尝试不得通过越级 promotion 实现（promotion 仍走
§1a Gate）。

### 11.5 本节不做的事

- **不**晋级任何 capability label
- **不**替代 §1–10 的 formal definition / frozen statements / runtime
  principles / adoption model
- **不**重定义 `oMLX` 替代关系（§5.2 仍然有效）
- **不**改变 §6 adoption model
- **不**晋级 architect-grade 内容到 source-of-truth 契约（plan-grade /
  source-of-truth grade 边界保持）

本节是身份**精炼**而不是身份**重写**：与 §1 Formal Definition 互锁，与
§5.3 vMLX 边界互锁，与 `docs/architect/01-mainline-roadmap.md` plan-grade
战略互锁；当 plan-grade 路线刷新时本节同步刷新。
