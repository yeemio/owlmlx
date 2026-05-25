# Campaign F · F-1 — `speculative_execution_status` Runtime Contract Plan

> **Grade**：plan-grade · architecture intent
> **承载位置**：`docs/architect/06-campaign-F1-plan.md`
> **下游 design-grade**：未起 · 见 §11 hand-off
> **Plan-grade 来源**：[01-mainline-roadmap.md](01-mainline-roadmap.md) Part V · Campaign F · F1
> **语言纪律**：plan-grade 允许 `plausible` / `candidate` / `pending`；不写 `supported`

---

## 1. Purpose

F-1 在 owlmlx 内建立 **runtime-owned `speculative_execution_status` 状态契约**，把现有 spec / MTP 路径的能力档位、激活方法、accept/reject 计量、fallback 链等信息从模块内部局部状态升到统一的 runtime status surface。

不是建一个新的 MTP 实现，也不是把任何 method 从 `experimental` 升 `supported`。F-1 的产出是一个 **contract + endpoint shape**，让上层（OwlOps / OwlCoda / 调试者）能用一个稳定的字段集判断："这个 runtime 启用了什么 spec 方法、它现在能不能 serve、accept 率怎样、出问题时会 fallback 到哪条路径"。

这条 surface 的存在是后续 F-2 / F-3 / F-4 / F-7 等所有 spec 工作的 **正交评估前置** —— 没有这一层，每个 spec 方法都各自定义自己的状态字段，上层无法以一种统一的方式正交比较 spec 路径。

---

## 2. Why Now / Why Parallel

按 [master-outline.md §8.4](../source-of-truth/master-outline.md) 的双轨设计：

- **Track 1**（B-1c §2 allocator-policy closure）在 §2 drift triage active phase，会持续触动 cache_manager / session_kv_cache / memory_pressure_eviction_policy
- **Track 2**（F-1 `speculative_execution_status` 状态契约）**不依赖** G2 closure，可独立起跑

F-1 plan-grade 现在落地的理由：

1. F-1.1 是 contract design，不动 runtime code，也不进 cache / memory 修改面 → 与 Track 1 在 git 路径上零碰撞
2. F-1.1 plan-grade 完成后，design-grade `F-1-spec.md`（下条 session）和 code-grade endpoint stub（再下条 session）都可以与 Track 1 持续并行
3. Track 1 §2 active triage 当下不能被打断（prompt-reset window probe `20260525T055831Z` → swap-bearing 4h `20260525T061019Z` 已产出 gap-blocked evidence），让 F-1 contract 工作由 fresh-context session 同期推进更高效

---

## 3. Scope

### In scope

- `speculative_execution_status` surface 的契约形态（fields、语义、required vs optional）
- HTTP endpoint location 与 `/v1/runtime/status` 现有 diagnostic 段落的关系
- method extensibility 设计（`native_mtp` / `assistant_drafter` / `draft_model` / `eagle` / `ngram` 自第一天起可表达，包括尚未实现的；spec 主动关闭由 top-level `capability_label=disabled` 表达）
- 把现有 `GEMMA4_MTP_CAPABILITY_LABEL = "experimental"`（[gemma4_mtp_drafter.py:23](../../owlmlx/gemma4_mtp_drafter.py)）这类 module-local capability 升级为 surface field
- 与 [runtime-status-schema.md §6](../source-of-truth/runtime-status-schema.md) stable vs diagnostic 分段的归位
- F-2 / F-3 / F-4 / F-7 等后续 gate 与本 surface 的 cross-gate linkage

### Out of scope（明确**不**在 F-1.1 范围内）

- proposer / drafter 实装（n-gram、EAGLE、resident MTP runner 都另起 gate）
- DS4 MTP weights 探测 / 增补
- `mlx_vlm_mtp_runner` 重构（仍维持 deferred CLI per-request load 模式）
- cache_manager / session_kv_cache / memory_pressure_eviction_policy 任何编辑
- spec × structured-output × tool-calling 正交矩阵（F-4 的事）
- endpoint test 实装、failure-mode 处理、test harness（design-grade）
- exact URL 路径决策（design-grade 再定）
- field 名最终序列化形式（camelCase vs snake_case；design-grade 再定）
- session_kv_cache 字段重写（F-1 只读不写）

---

## 4. Contract Surface Commitments

### 4.1 Surface identity

- **Surface name**：`owlmlx.speculative_execution_status`（沿用 [runtime-status-schema.md §9 Phase 45](../source-of-truth/runtime-status-schema.md) 既有的 `owlmlx.<surface_name>` 命名 pattern，如 `owlmlx.host_stable_execution` / `owlmlx.cache_scheduler_status`）
- **Version**：`v1`（plan-grade 锁定 major；minor 升级走 additive-only）
- **默认位置**：作为 `/v1/runtime/status` 的 **diagnostic section**，与 `session_kv_cache` / `reclaim_barrier` 同级
- **可选独立 endpoint**：`/v1/runtime/speculative_execution_status`（精确路径 design-grade 再定，本 plan 只承诺独立访问 path 存在）

### 4.2 Required Semantic Fields

| Field | 类型 | 含义 |
|---|---|---|
| `surface` | string | 固定为 `"owlmlx.speculative_execution_status"` |
| `version` | string | 当前为 `"v1"` |
| `method` | string \| null | 当前激活的 spec method；`null` 表示 spec 未启用或 runner 未 load |
| `available_methods` | list[MethodEntry] | 本 runtime 知道的 spec method 清单（含尚未实装的，标 `status=not_implemented`） |
| `capability_label` | string | 当前激活 method 的能力档位：`disabled` / `not_implemented` / `scaffold_only` / `experimental` / `partial` / `supported` |
| `runner_status` | string | 当前激活 method 的 runner 健康状态：`unloaded` / `loaded` / `deferred_cli_per_request` / `error` |

`MethodEntry` shape:

| Field | 类型 | 含义 |
|---|---|---|
| `method` | string | method 名（值集见 §5.1） |
| `status` | string | `not_implemented` / `scaffold_only` / `experimental` / `partial` / `supported` |
| `notes` | string \| null | 简短解释（如 `"deferred_cli_per_request via mlx_vlm"`） |

### 4.3 Optional Semantic Fields

| Field | 类型 | 含义 |
|---|---|---|
| `drafter_id` | string \| null | method 有 drafter 时的 drafter 路径或 model id |
| `accepted_tokens` | int | 自 runner load 以来累计 accepted tokens |
| `rejected_tokens` | int | 自 runner load 以来累计 rejected tokens；当前 mlx-vlm summary 未直接暴露时不得伪造 |
| `accepted_rounds` | int | 自 runner load 以来累计 accept rounds |
| `last_request_at` | timestamp \| null | 最近一次 spec 请求的时间戳（freshness 判定用） |
| `runner_started_at` | timestamp \| null | runner 进入 loaded 状态的时间戳 |
| `fallback` | FallbackEntry \| null | 当前 method 不可用时上次降级的目标（shape design-grade 再定） |
| `cache_sharing` | CacheSharingEntry \| null | 与 session_kv_cache 的交互声明（**read-only**；F-1 不修改 cache；shape design-grade 再定） |
| `missing_reason` | string \| null | method 不可用时的原因（沿用 [D3 spec](design/D3-spec.md) `missingReason=mtp_weights_absent_or_stripped` pattern） |

### 4.4 字段不变量

- **Missing optional field MUST NOT be misread as method support**（与 [runtime-status-schema.md §4](../source-of-truth/runtime-status-schema.md) 通用规则一致）
- **`method=null` MUST imply runner_status ∈ {unloaded, deferred_cli_per_request, error}**；不允许 `method=null, runner_status=loaded`
- **`available_methods` MUST 包含所有已知 method**，即使 status 为 `not_implemented`；调用者据此正交比较 runtime 的 spec 能力面
- **`capability_label` MUST 描述当前激活 method 的真实档位**，不允许沿用 endpoint 自身的 `supported` 状态

### 4.5 示例（non-normative · 仅说明 shape）

**Case A — spec 未启用（owlmlx 默认状态）：**

```json
{
  "surface": "owlmlx.speculative_execution_status",
  "version": "v1",
  "method": null,
  "capability_label": "disabled",
  "runner_status": "unloaded",
  "available_methods": [
    {"method": "native_mtp", "status": "not_implemented", "notes": "DS4 MTP weights absent or stripped (see D3)"},
    {"method": "assistant_drafter", "status": "experimental", "notes": "deferred_cli_per_request via mlx_vlm"},
    {"method": "draft_model", "status": "not_implemented", "notes": null},
    {"method": "eagle", "status": "not_implemented", "notes": null},
    {"method": "ngram", "status": "not_implemented", "notes": "F-2 candidate"}
  ]
}
```

**Case B — assistant_drafter 激活，per-request CLI 路径：**

```json
{
  "surface": "owlmlx.speculative_execution_status",
  "version": "v1",
  "method": "assistant_drafter",
  "capability_label": "experimental",
  "runner_status": "deferred_cli_per_request",
  "drafter_id": "/Users/.../gemma-4-31B-it-assistant-bf16",
  "accepted_tokens": 142,
  "accepted_rounds": 11,
  "last_request_at": "2026-05-25T07:14:22Z",
  "available_methods": [
    {"method": "assistant_drafter", "status": "experimental", "notes": "deferred_cli_per_request via mlx_vlm"},
    "..."
  ]
}
```

JSON 字段命名（snake_case vs camelCase）以及 timestamp 序列化形式由 design-grade 定。

---

## 5. Method Extensibility Design

### 5.1 Day-One Method Vocabulary

`method` 与 `available_methods[].method` 取值集合（v1 锁定）：

| Value | 当前 owlmlx 状态（plan-grade 视角） |
|---|---|
| `native_mtp` | runtime 内嵌 MTP 路径（如 DS4 native MTP）；当前 `not_implemented`，依赖 [D3 missing reason](design/D3-spec.md) 解除 |
| `assistant_drafter` | Gemma4 assistant drafter via mlx-vlm；当前 `experimental`（[mlx_vlm_mtp_runner.py](../../owlmlx/runtime/mlx_vlm_mtp_runner.py) `deferred_cli_per_request`） |
| `draft_model` | 通用 draft model（如 vLLM `--draft-model`-style）；当前 `not_implemented` |
| `eagle` | EAGLE / EAGLE-3 系；当前 `not_implemented` |
| `ngram` | n-gram / suffix-based speculative（F-2 候选）；当前 `not_implemented` |

> **关于"spec 主动关闭"状态的表达**：top-level `method` 取 `null` 表示"无激活 method"；spec 显式关闭的语义由 top-level `capability_label="disabled"` 承担。`disabled` **不**作为 `method` 值出现，避免 `method=null` 与 `method=disabled` 两种语义重复。

### 5.2 Extensibility 纪律

- **新 method 加入 MUST 是 schema-additive**：在 v1 vocabulary 内加新 entry 不构成 schema break
- **新 method 加入前 MUST 先在 `available_methods` 暴露**：`{method=<new>, status=not_implemented}`；之后再 wire 实际 runner
- **method 退役 MUST 走 deprecation 流程**：先标 `status=deprecated`（v1 vocabulary 不含此值，加入即 minor bump），至少一个 release window 后再删除
- **vocabulary 扩展**：v1 锁定的 5 个 method value 之外的新 method（如未来的 `medusa` / `mtp_v2`）需要 minor bump 但仍是 additive；vocabulary contract break 走 major

### 5.3 status / capability_label 取值集合（v1 锁定）

合法值域有两层：

- `available_methods[].status` ∈ { `not_implemented`, `scaffold_only`, `experimental`, `partial`, `supported` }（5 值）
- 顶层 `capability_label` ∈ 以上 5 值 ∪ { `disabled` }（6 值）

共享语义：

| Value | 含义 | 出现位置 |
|---|---|---|
| `not_implemented` | runtime 知道该 method 名但没有任何 runner / scaffold | `available_methods[].status` + `capability_label` |
| `scaffold_only` | runtime 有 module-level scaffold（如 inspection / 类型定义）但没有 serving path | `available_methods[].status` + `capability_label` |
| `experimental` | 有 runner，但 capability honesty 上是 experimental | `available_methods[].status` + `capability_label` |
| `partial` | 有 runner 且通过 N≥20 重复，但未达 4-gate promote-path 全过 | `available_methods[].status` + `capability_label` |
| `supported` | 通过 [§1a Promotion Gate](../source-of-truth/extraction-inventory.md) | `available_methods[].status` + `capability_label` |
| `disabled` | spec 主动关闭（与 top-level `method=null` 同时出现） | **仅** `capability_label` |

---

## 6. `capability_label` Surfacing

### 6.1 现状

当前 [gemma4_mtp_drafter.py:23](../../owlmlx/gemma4_mtp_drafter.py) 已定义：

```python
GEMMA4_MTP_DRAFTER_SURFACE = "owlmlx.gemma4_mtp_drafter"
GEMMA4_MTP_DRAFTER_VERSION = "v1"
GEMMA4_MTP_CAPABILITY_LABEL = "experimental"
```

但 **仅模块内部可见**：

- 模块自身使用
- 单测引用
- **没有任何 runtime status surface 暴露**

这等于 capability honesty 在 runtime 边界上是隐式的：上层只能通过"endpoint 调用是否成功"判断，无法区分"endpoint 失败因为 method 没启用"与"endpoint 失败因为 method 是 experimental 阶段崩了"。

### 6.2 F-1 升级

`capability_label` 从 module constant 升为 **surface field**：

- 现有 `GEMMA4_MTP_CAPABILITY_LABEL` 不重命名、不变值；保留为 source of truth
- `speculative_execution_status` endpoint 在 `available_methods[*].status` 与顶层 `capability_label` 字段中 **读取并暴露**该 constant
- 任何 method 后续添加 capability label 都遵循同样的 surfacing 纪律

### 6.3 Surface honesty 关键不变量

> **endpoint 自身的 `supported` 状态 ≠ 任何 method 的 capability**

- F-1 endpoint 本身可以晋级 `supported`（status reporting 不涉及 spec 正确性）
- 但 endpoint 返回的 `method=*` / `capability_label=*` 字段必须显式标注 method 自身档位
- 严防"status surface 绿 → 用户误读为 spec 路径绿"（master-outline R3 capability-label-inflation 风险）

---

## 7. Stable vs Diagnostic 归位

按 [runtime-status-schema.md §6 Stabilization-1 Contract Freeze](../source-of-truth/runtime-status-schema.md)：

| 段落类型 | 当前内容 | F-1 归位 |
|---|---|---|
| Stable | `contract` / `summary` / `health` / `inventory` / `budget` / `restart` | **不主张** F-1 全面进入 stable |
| Diagnostic | `backend.detail` / `session_kv_cache` / `reclaim_barrier` / `governance_observations` / etc. | **F-1 主要驻地** |

### 7.1 默认 Diagnostic

`speculative_execution_status` 作为新的 diagnostic section，与 `session_kv_cache` 完全平行：

- 上层（OwlOps / OwlCoda）消费 MUST 视为 best-effort detail，不构成 long-lived field-stable promise
- diagnostic 段不进入 `/healthz` smaller liveness contract
- 任何 stable 化诉求走 §1a Promotion Gate

### 7.2 可选 Stable 子集（design-grade 评估）

为让上层在不消费 diagnostic 段时也能感知 spec 启用情况，**允许**（不强制）在 `summary` 中暴露窄子集：

| Field | 类型 | 含义 |
|---|---|---|
| `spec_enabled` | bool | `method != null` 且 `capability_label ∈ {experimental, partial, supported}` 且 `runner_status != error` |
| `spec_method_count_available` | int | `available_methods` 中 status ∉ {not_implemented} 的数量 |

该子集为 minimal-additive；design-grade 评估对 `summary` 既有契约的兼容性后再决定是否真正 land。

---

## 8. Integration Boundaries

### 8.1 F-1 **不**修改

明确禁止 F-1.1 / F-1.2 编辑面：

- `owlmlx/session_kv_cache.py`
- `owlmlx/cache_manager.py`
- `owlmlx/scheduler_admission.py`
- `owlmlx/memory_pressure_eviction_policy.py`
- `owlmlx/memory_watermark.py`
- 任何 `bench/*` / `files/evidence/*` 现有 ledger（Track 1 owns）

此为 staging discipline + Track 1 §2 drift triage 归因纯净度双重约束。

### 8.2 F-1 **读取**

- [owlmlx/runtime/mlx_vlm_mtp_runner.py](../../owlmlx/runtime/mlx_vlm_mtp_runner.py) — assistant_drafter method 的 runner_status / accepted/rejected counters / drafter id
- [owlmlx/gemma4_mtp_drafter.py](../../owlmlx/gemma4_mtp_drafter.py) — `GEMMA4_MTP_CAPABILITY_LABEL` / `GEMMA4_MTP_DRAFTER_SURFACE` / `GEMMA4_MTP_DRAFTER_VERSION` constants

### 8.3 F-1 **新增**

- 新 status section module（design-grade 命名，候选 `owlmlx/runtime/speculative_execution_status.py`）
- `/v1/runtime/status` 内新增 diagnostic section
- 可选独立 endpoint（design-grade 决定精确路径）

### 8.4 Wave H2 编排

[01-mainline-roadmap.md Part V Wave H](01-mainline-roadmap.md) 的 H2（`server_routes_runtime.py` 拆分）gated on B-1 闭环。F-1 endpoint 实装时点（F-1.2 / 后续 session）会 **先落在 `server.py`**，H2 启动时与其它 `/v1/runtime/*` 路由一起 sweep 到 `server_routes_runtime.py`。

PR 描述纪律：F-1.2 endpoint 实装 PR 必须显式声明 "将被 Wave H2 移动"，避免 H2 reviewer 误以为漏拆。

---

## 9. Cross-Gate Linkage

| 下游 gate | 与 F-1 的关系 |
|---|---|
| **F-2** n-gram / suffix probe | F-2 实装时在 `available_methods` 中把 `ngram.status` 从 `not_implemented` 升 `experimental`；不需改 F-1 schema |
| **F-3** Gemma 4 resident MTP A/B | F-3 完成后把 `assistant_drafter.status` 的 `notes` 从 `deferred_cli_per_request` 改为 `resident`；F-3 前置等 session-kv B-1c §2 closure，`20260525T061019Z-...-native-swap` 只能算 gap-blocked one-swap evidence |
| **F-4** 正交矩阵 ≥20 case | F-4 直接 consume `speculative_execution_status` 的 `method` / `accepted_tokens` / `rejected_tokens` / `fallback`；F-1 是 F-4 的接口前置 |
| **F-5** draft constraint checker | F-5 可在 F-1 surface 中新增 `constraint_check_status` optional field（schema-additive） |
| **F-6** MTP + session KV combo | F-6 用 F-1 的 `cache_sharing` 字段表达；F-6 前置等 B-1c §2 closure |
| **F-7** DS4 native MTP path | F-7 实装时把 `native_mtp.status` 从 `not_implemented` 升 `experimental`，并填 `missing_reason` / `drafter_id`；F-7 前置等新 DS4 artifact 出现 |
| **§VI G3** Structured-Output Invariance | G3 consume F-4 矩阵；F-4 consume F-1 surface |
| **§VI G4** Speculative Path Landing | G4 require F-7 + F-1 surface 持续 supported |

---

## 10. Risk

| # | 风险 | 概率 | 影响 | 控制 |
|---|---|---|---|---|
| F1-R1 | endpoint surface 出现"绿"被误读为 spec 路径"绿" | 高 | 极高 | §6.3 不变量 + 显式 `capability_label` 字段 + 上层 consumer 文档明示 |
| F1-R2 | method vocabulary 早期锁定后续 method 进入需 break schema | 中 | 高 | §5.2 day-one 暴露 6 个 method（含未实装）+ additive-only 纪律 |
| F1-R3 | F-1 endpoint 与 Wave H2 编排冲突 | 低 | 中 | §8.4 PR 描述声明 + H2 sweep when ready |
| F1-R4 | optional field 数量膨胀，diagnostic section 退化为"什么都装" | 中 | 中 | design-grade 评估每个 optional field 是否真服务于一个明确 consumer（F-4 / F-5 / F-6） |
| F1-R5 | `cache_sharing` 字段被理解为"F-1 修改 cache" | 中 | 中 | §8.1 明示 read-only + cache_sharing 字段说明只读 |
| F1-R6 | accepted/rejected counters 跨 runner load / unload 语义不清 | 中 | 中 | design-grade 显式定义 "since runner_started_at" 而非 "lifetime" |

---

## 11. Status / Next Step

- **当前状态**：plan-grade → design-grade → code-grade F-1.2/F-1.3 已落地；
  evidence `20260525T142617Z` 记录 5/5 contract fixtures + 20 fresh
  round trips passed
- **下一步**：二选一但不冲突：
  - endpoint §1a Promotion Gate：只晋级 F-1 status surface 本身，不晋级任何
    speculative method
  - F-2：n-gram / suffix probe 作为第一个 additive method-status 扩展
- **晋级路径**：F-1 endpoint **本身**经 §1a Promotion Gate 后可晋 `supported`；endpoint 暴露的 method capability **不**因此晋级

### 11.1 Hand-off 纪律

按 [01-mainline-roadmap.md Part VIII.3](01-mainline-roadmap.md) 工程纪律：

> 层级 handoff：plan-grade → 用户复核 → 修订定版 → design-grade → 复核 → 代码（**不允许跳级**）

本 plan-grade **不**包含 design-grade 所需的：

- 精确 URL
- field 序列化形式
- test 文件路径
- contract test 实装
- `FallbackEntry` / `CacheSharingEntry` 字段完整 shape

这些 **只有**在 design-grade 才下定。

---

## 12. References

### owlmlx 内部

- Plan-grade 来源：[01-mainline-roadmap.md Part V · Campaign F · F1](01-mainline-roadmap.md)
- Plan-grade 12-d 框架定位：[02-state-vs-market-gap.md](02-state-vs-market-gap.md) #9 Speculative Path Safety / #10 Structured-Output Invariance
- Master-outline 双轨决定：[../source-of-truth/master-outline.md §8.4](../source-of-truth/master-outline.md)
- 现有 runtime status 契约：[../source-of-truth/runtime-status-schema.md](../source-of-truth/runtime-status-schema.md) §6 / §9
- 现有 capability label / module surface：[../../owlmlx/gemma4_mtp_drafter.py](../../owlmlx/gemma4_mtp_drafter.py) / [../../owlmlx/runtime/mlx_vlm_mtp_runner.py](../../owlmlx/runtime/mlx_vlm_mtp_runner.py)
- 初始 probe note：[../source-of-truth/gemma4-mtp-drafter-probe-20260506.md](../source-of-truth/gemma4-mtp-drafter-probe-20260506.md)
- DS4 spec lane：[design/D3-spec.md](design/D3-spec.md) / [design/D4-spec.md](design/D4-spec.md)（未纳入 repo 的 research note 不作为本 plan 的 committed source）

### 外部锚定

- vLLM speculative decoding methods: https://docs.vllm.ai/en/latest/features/speculative_decoding/
- vLLM MTP (Gemma4 assistant note): https://docs.vllm.ai/usage/speculative_decoding/mtp/
- SGLang speculative decoding (EAGLE-2/3 / MTP / n-gram): https://docs.sglang.ai/advanced_features/speculative_decoding.html
- Transformers DeepSeek V4 (`num_nextn_predict_layers`): https://huggingface.co/docs/transformers/model_doc/deepseek_v4
- LMSYS DeepSeek V4 Day 0 (MTP in-graph metadata): https://www.lmsys.org/blog/2026-04-25-deepseek-v4/

---

## 13. 变更历史

| Date | 变更 | 由 |
|---|---|---|
| 2026-05-25 | plan-grade draft 初稿 | architect session（this round） |
| 2026-05-25 | quality-gate cleanup: method/capability value split, committed-source references, counter honesty | Codex review |
