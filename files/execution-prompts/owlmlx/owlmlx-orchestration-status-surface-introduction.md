# owlmlx - Orchestration Status Surface Introduction

## Goal

Advance `owlmlx` from orchestration architecture truth to one runtime-owned
assessment surface that `ops` can consume without inventing runtime
semantics.

Active goal contract:

- `files/goals/owlmlx/single-host-orchestration-upstream-truth-surface-goal-contract.md`

## 你是谁

你是 `owlmlx` 这条线的执行者。

这轮不是继续 Phase 45 stream seam 微缩窄，也不是去实现完整 local
orchestrator。

这轮只有一个主目标：

- **引入一个最小但诚实的 runtime-owned orchestration status surface**

它必须能让 `ops` 侧消费时不需要自己猜：

- 哪些 bottleneck layers 现在能由 `owlmlx` runtime-owned 地判断
- 哪些 layers 还必须停在 `unknown` / `insufficient_signal`

## 这轮之前的冻结事实

当前架构和代码已经提供的真实基础：

- `docs/source-of-truth/single-host-orchestration-architecture.md`
  已把 `orchestration_status_surface` 冻结为 immediate design program 的
  下一类 contract
- `owlmlx/serving.py`
  已经暴露：
  - `max_concurrent = 1`
  - `queue_policy = ticketed_fifo`
  - `waiters`
  - bounded `pre_gate_admission`
  - `cohort_handoff_status`
- `owlmlx/runtime/kernel.py`
  已经暴露：
  - `active_model_id`
  - inventory / model count
  - budget truth
  - restart visibility
  - governance observations / policy
- `docs/source-of-truth/phase45-request-aggregation-window-exactness.md`
  已把 active stream dependency 冻结到：
  `stream_session_holds_gate_until_completion`

但当前仍然没有：

- 一个 dedicated orchestration surface
- 一个稳定字段集合来表达 layer-by-layer classification status
- 一个可供 `ops` 直接依赖的 upstream contract

## 本轮唯一目标

把下面这个 dominant gap 收成 code + contract + docs + tests：

- `orchestration_status_surface_introduction`

## 本轮最终只能给出两个结论之一

- `owlmlx_orchestration_status_surface_introduced`
- `owlmlx_orchestration_status_surface_still_blocked`

如果是 `still_blocked`，必须冻结：

- 当前最小诚实 surface 已到哪里
- 哪一类 runtime-owned signal 仍然缺失
- 为什么没有这些 signal 就不能稳定给出该层 verdict
- `ops` 在消费时哪些层必须继续显示 `unknown`

## 必须先读

### 当前 broad prompt 与下游约束

1. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/owlmlx-orchestration-upstream-truth-surface-for-ops.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/owlops-orchestration-bottleneck-observability-service.md`

### 当前 owlmlx truth

3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/single-host-orchestration-architecture.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-capability-matrix.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/ownership-boundary.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-window-exactness.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/serving.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/kernel.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 第一性原则

- `runtime truth ownership > ops-side inference`
- `one narrow useful surface > broad orchestration storytelling`
- `authoritative layer assessment > raw utilization narration`
- `unknown when signal is weak > fabricated bottleneck certainty`
- `transport contract or operator entry > doc-only success`

## 这轮最推荐的成功形态

优先级从高到低：

1. 新增一个 runtime-owned orchestration module
2. 新增一个 machine-readable contract surface
3. 新增一个 runtime transport surface
4. 新增针对性测试
5. 同步 source-of-truth

推荐默认 shape：

- `owlmlx/orchestration_status.py`
- `scripts/runtime_orchestration_status.py`
- `GET /v1/runtime/orchestration-status`

如果你证明 transport 这轮不能诚实落地，也至少要有：

- runtime-owned module
- operator entry
- tests
- docs
- 给 `ops` 的稳定 upstream request

## 这轮至少要覆盖的 layer

surface 里至少要有：

1. `admission`
2. `generation_gate`
3. `stream_hold`
4. `model_residency`
5. `memory_pressure`
6. `recovery`
7. `unknown`

同时至少要表达两个维度：

1. `summary.bottleneck_layer`
2. 每层自己的 `classification_status`

`classification_status` 至少要能表达：

- `supported`
- `partial`
- `unknown`
- `insufficient_signal`

## 当前 signal inventory 的最低诚实口径

你应该优先从这些现有 runtime-owned signal 出发：

- `generation_gate.waiters`
- `generation_gate.queue_policy`
- `generation_gate.max_concurrent`
- `generation_gate.pre_gate_admission.*`
- `active_model_id`
- inventory / loaded model count
- `budget.*`
- `restart.restartable_models`
- `restart.auto_restart_dead_session`
- `governance_observations`
- `governance_policy`

你可以把这些 signal 组合成更高层 assessment。
但禁止做下面这些偷换：

- `memory_budget` 可见 ≠ 已拥有 `memory_pressure bottleneck`
- `restartability` 可见 ≠ 已拥有 `recovery bottleneck`
- 只因为 stream code 现在 hold gate，就自动宣称 stream 一定是当前唯一瓶颈
- 只因为有 waiters，就自动宣称 gate 是唯一瓶颈

## 推荐 contract shape

你可以调整字段，但至少要满足 `ops` 可消费与 runtime 诚实性：

```json
{
  "contract": {
    "surface": "owlmlx.orchestration_status",
    "version": "v1"
  },
  "summary": {
    "status": "partial",
    "bottleneck_layer": "generation_gate",
    "confidence": "medium"
  },
  "layer_assessment": {
    "admission": {
      "classification_status": "supported",
      "reason_code": "bounded_pre_gate_window_visible"
    },
    "generation_gate": {
      "classification_status": "supported",
      "reason_code": "serial_ticketed_fifo_waiters_visible"
    },
    "stream_hold": {
      "classification_status": "partial",
      "reason_code": "stream_hold_truth_partially_visible"
    },
    "model_residency": {
      "classification_status": "partial",
      "reason_code": "active_default_and_inventory_visible"
    },
    "memory_pressure": {
      "classification_status": "insufficient_signal",
      "reason_code": "no_direct_pressure_or_reclaim_barrier_signal"
    },
    "recovery": {
      "classification_status": "partial",
      "reason_code": "restart_visibility_without_full_recovery_contract"
    }
  },
  "upstream_truth_sources": [
    "owlmlx.runtime.status.generation_gate",
    "owlmlx.runtime.status.inventory",
    "owlmlx.runtime.status.budget",
    "owlmlx.runtime.status.restart",
    "owlmlx.runtime.status.governance_observations",
    "owlmlx.runtime.status.governance_policy"
  ],
  "missing_signals": []
}
```

## Wave 0: Freeze The Minimum Honest Surface

目标：
先冻结“这轮最小可落地 surface 到底是什么”，不要一上来就把层级判断写满。

必做：

- 判断 authoritative surface 是：
  - 新 transport surface
  - 还是 operator-first surface
- 明确哪些字段属于稳定 contract
- 明确哪些字段只是 runtime status 的输入，不应继续冒充 long-lived stable
  sections

验收：

- authoritative surface 被收死为一个明确答案
- 不留“以后再整理成 contract”的口子

## Wave 1: Land The Runtime-Owned Surface

目标：
让 `owlmlx` 自己能产出 orchestration assessment。

必做：

- 新增 runtime-owned builder / dataclass / to-dict 逻辑
- 只在证据足够的 layer 上给 verdict
- 对不足 layer 给 `unknown` / `insufficient_signal`
- 冻结 `upstream_truth_sources`
- 冻结 `missing_signals`

验收：

- `owlmlx` 自己就能构造一个 stable orchestration payload

## Wave 2: Expose It To Operators / Consumers

目标：
让 `ops` 有明确消费入口。

优先：

- `GET /v1/runtime/orchestration-status`

如果 transport 这轮不适合落地：

- 至少提供稳定 operator entry
- 并明确 `ops` 这轮应消费哪个 surface、为什么

验收：

- 新 surface 不是只能在 Python 内部调用

## Wave 3: Tests And Truth Sync

目标：
让这条 surface 成为 repo truth，而不是一段临时实现。

必做：

- 针对新 builder / transport surface 补测试
- 更新 source-of-truth 文档
- 如 claim 变化，更新 capability matrix / runtime-status schema
- 如果 blocked，新增 blocker doc 并给 `ops` 稳定 upstream request

验收：

- code / tests / docs / prompt 同步

## 绝对不要做的假完成

- 只写文档，不新增 runtime-owned code
- 只在 `/v1/runtime/status` diagnostic sections 上做口头解释
- 让 `ops` 继续自己拼凑 layer meaning
- 把 `/healthz` 或 generic readiness 写成 orchestration verdict
- 把 `memory_budget` 直接改名成 `memory_pressure`
- 把 restartability visibility 直接改名成 `recovery status`
- 没有测试却宣称 stable upstream surface 已可消费

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`introduced` 或 `still_blocked`
2. 最终 verdict
3. authoritative surface 是什么
4. 当前可判断哪些 layers，以及各自依据
5. 当前必须保留 `unknown` / `insufficient_signal` 的 layers，以及缺什么
6. `ops` 应消费哪个 surface
7. 实际修改的文件
8. 实际运行的命令与关键结果
9. 如果仍 blocked，唯一主 blocker 是什么
