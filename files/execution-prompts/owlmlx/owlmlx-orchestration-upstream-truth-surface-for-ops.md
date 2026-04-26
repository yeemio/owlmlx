# owlmlx - Orchestration Upstream Truth Surface For Ops

## 你是谁

你是 `owlmlx` 主线执行者。

这轮不是继续做 Phase 45 seam 微缩窄，也不是泛化成完整 local scheduler。

这轮你的职责很窄：

- 给 `ops` 提供一个 runtime-owned 的上游 truth surface
- 让 `ops` 能够诚实判断当前 orchestration bottleneck 卡在哪一层

## 工作边界

你允许修改：

- `/Users/yeemio/AI/gitrep/owlmlx`

你只允许读取，不能修改：

- `/Users/yeemio/AI/gitrep/owlops`

如果你发现 `ops` 侧还需要额外消费逻辑，那不是这轮的工作。
这轮只处理 `owlmlx` 自己应该拥有的 upstream truth。

## 本轮背景

`owlmlx` 已经正式把 single-host orchestration 提到架构层面。

现在已经有一条配套的 `ops` 任务：

- `ops` 要做一个 orchestration bottleneck observability / service layer
- 但它不能自己发明 `owlmlx` runtime 语义
- 所以 `owlmlx` 必须先提供足够窄、足够诚实的 upstream truth surface

当前 `owlmlx` 已经有的 runtime-owned 基础包括：

- `GenerationGate`
- `ticketed_fifo`
- bounded pre-gate admission / cohort window
- model inventory / active-default selection
- pinning / TTL / eviction-history governance
- `/v1/runtime/status`
- 一批 Phase 45 cache / scheduler / governance truth surfaces

但当前还没有一个专门面向 orchestration bottleneck classification 的
runtime-owned surface。

当前能直接依赖的现有 signal，主要来自：

- `generation_gate` / `pre_gate_admission` 的 waiters、queue policy、handoff visibility
- runtime inventory / active-default / resident-model truth
- pinning / TTL / eviction-history / restart visibility
- runtime budget truth

但这些 signal 不会自动等于完整 bottleneck classification：

- `memory_budget` 不等于已经拥有 `memory_pressure bottleneck` 判决
- `restartable_models` / `restart visibility` 不等于已经拥有 `recovery bottleneck` 判决
- `/v1/runtime/status` 的 diagnostic sections 不应被偷换成新的稳定 orchestration contract

## 本轮唯一目标

回答一个很窄的问题：

- **`owlmlx` 能不能现在就拥有一个上游 orchestration truth surface，让 `ops` 不必靠猜，就能判断瓶颈位于 admission / gate / stream / residency / pressure / recovery 哪一层？**

## 本轮最终只能给出两个结论之一

- `owlmlx_orchestration_truth_surface_introduced`
- `owlmlx_orchestration_truth_surface_still_blocked`

如果仍 blocked，必须精确说明：

- 缺的是哪一类 runtime-owned signal
- 为什么当前不能诚实归类
- 哪个 contract 需要下一轮补齐

## 必须先读

### 当前 owlmlx truth

1. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/single-host-orchestration-architecture.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/system-architecture.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-capability-matrix.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-cache-scheduler-status.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-cache-scheduler-implementation-backlog.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-cache-continuous-batching-feasibility.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-window-exactness.md`
9. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-multi-model-pinning-control.md`
10. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-multi-model-ttl-policy-control.md`
11. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-multi-model-eviction-history-governance.md`
12. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/kernel.py`
14. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/serving.py`
15. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py`

### 下游 consumer 约束

16. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/owlops-orchestration-bottleneck-observability-service.md`

读完后，先输出不超过 12 行的执行计划，再动手。

## 第一性原则

- `runtime truth ownership > ops-side inference`
- `narrow honest surface > broad orchestration storytelling`
- `unknown when signal is weak > fake bottleneck classification`
- `machine-readable contract > dashboard-first narrative`
- `real runtime evidence > synthetic wording`

## 你这轮最应该做的事

优先考虑引入一个新的、窄而诚实的 runtime-owned surface。

推荐方向：

- 一个 orchestration status / bottleneck surface
- 由 `owlmlx` 自己基于现有 runtime truth 构建
- 只在当前能够诚实支持的 layer 上给出结论
- 对信号不足的 layer 明确给 `unknown` / `insufficient_signal`

## 这轮 surface 至少要覆盖的 bottleneck layers

最终 surface 里，至少要考虑下面这些分类：

1. `admission`
2. `generation_gate`
3. `stream_hold`
4. `model_residency`
5. `memory_pressure`
6. `recovery`
7. `unknown`

注意：

- 并不是要求你这轮就把每一层都做成 fully supported
- 而是要求你诚实回答：哪些层现在已经能 runtime-owned 地判断，哪些还不能

## 这轮 surface 至少要表达两个维度

- 当前最可能的 `bottleneck_layer`
  - 只有在 runtime-owned 证据足够时才允许给出
- 每一层当前的 `classification_status`
  - 至少要能表达 `supported` / `partial` / `unknown` / `insufficient_signal`

`ops` 需要的不只是一个 `bottleneck_layer` 字符串。
它还需要知道：哪些 layer 现在可以由 `owlmlx` 诚实判断，哪些必须继续停在
`unknown`。

## 这轮至少要回答的设计问题

1. authoritative surface 是什么？
   - 优先：新的 runtime-owned surface
   - 或者：新的 operator / transport surface，稳定引用现有 runtime truth
   - 不要通过改写 `/v1/runtime/status` 既有 stable sections 来偷渡 contract

2. 当前哪些信号已经足够支撑 bottleneck classification？
   - gate waiters
   - queue policy
   - pre-gate admission / cohort handoff visibility
   - stream hold
   - active / resident models
   - TTL / eviction / restart observations
   - budget truth
   - 其他

3. 哪些仍然不足？
   - 不足时必须怎么表达

4. `ops` 最终应该消费哪个 surface？
   - 以及它应把哪些字段当稳定 contract

## 推荐成功形态

本轮最推荐的成功形态是：

1. 新增一个 runtime-owned orchestration surface
2. 它有明确 contract shape
3. 它有可运行入口或 runtime transport surface
4. 它有测试
5. 它有 source-of-truth 文档
6. 它能被 `ops` prompt 直接引用

## 你可以考虑的 shape

下面只是推荐 shape，不是强制字段全集：

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
      "reason": "bounded_pre_gate_window_and_handoff_visible"
    },
    "generation_gate": {
      "classification_status": "supported",
      "reason": "serial_ticketed_fifo_waiters_visible"
    },
    "stream_hold": {
      "classification_status": "partial",
      "reason": "stream_session_holds_gate_until_completion_visible"
    },
    "model_residency": {
      "classification_status": "partial",
      "reason": "active_default_and_resident_models_visible"
    },
    "memory_pressure": {
      "classification_status": "insufficient_signal",
      "reason": "no_direct_runtime_owned_pressure_event_or_reclaim_barrier"
    },
    "recovery": {
      "classification_status": "partial",
      "reason": "restartability_visible_but_not_full_recovery_bottleneck_contract"
    }
  },
  "scheduler": {
    "queue_policy": "ticketed_fifo",
    "max_concurrent": 1,
    "waiters": 2
  },
  "stream": {
    "holds_shared_boundary": true
  },
  "residency": {
    "active_model_id": "..."
  },
  "recovery": {
    "restart_visibility": "visible"
  },
  "upstream_truth_sources": [
    "owlmlx.runtime.status.generation_gate",
    "owlmlx.runtime.status.governance_observations",
    "owlmlx.runtime.status.governance_policy"
  ],
  "missing_signals": []
}
```

如果你认为更合适的 shape 不是这个，也可以改。
但必须满足：

- `ops` 能消费
- `owlmlx` 能诚实生成
- 不会把当前 partial 状态写成 solved orchestration

## 绝对不要做的假成功

- 把 `/healthz` 或一般 health 状态写成 orchestration 结论
- 因为有 queue waiters 就自动宣称 `generation_gate` 一定是唯一瓶颈
- 没有 stream/runtime evidence 时硬写 `stream_hold`
- 没有 pressure signal 时硬写 `memory_pressure`
- 只因为 `memory_budget`、`loaded_model_count`、`ttl_expired_model_ids` 可见，就把它们写成 `memory_pressure bottleneck`
- 只因为 `restartable_models`、`restart_restore_visible` 可见，就把它们写成 `recovery bottleneck`
- 把 `/v1/runtime/status` 的 diagnostic-only 字段当成 `ops` 唯一稳定 contract
- 在 `owlmlx` 侧假装已经拥有完整 local orchestrator
- 只写文档，不给 contract / code / tests

## 如果当前只能 still_blocked

那你必须同步写清楚：

- 当前最小诚实 surface 已经到哪里
- 哪一类信号缺失导致还不能冻结 bottleneck classification
- `ops` 在这些信号补齐前应该怎样处理：
  - 哪些 layer 可判断
  - 哪些 layer 必须显示 `unknown`

## 需要同步的 surfaces

如果成功引入上游 truth surface，至少同步：

- runtime-owned code
- transport or operator entry
- source-of-truth 文档
- runtime-status schema / capability matrix（如适用）
- tests

如果仍 blocked，至少同步：

- blocker doc
- runtime-status schema 中对缺失 signal 的诚实口径
- 给 `ops` 的 stable upstream request

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`introduced` 或 `still_blocked`
2. 最终 verdict
3. authoritative upstream surface 是什么
4. 当前可判断哪些 bottleneck layers，以及各自依据
5. 当前必须保留 `unknown` 的 layers 是哪些，以及各自缺什么 signal
6. `ops` 应消费哪个 surface
7. 实际修改的文件
8. 实际运行的命令与关键结果
9. 如果仍 blocked，唯一主 blocker 是什么
