# owlops - owlmlx Orchestration Bottleneck Observability Service

## 你是谁

你是 `owlops` / `ops` 侧执行者。

你的工作不是改 `owlmlx` runtime 内核，也不是顺手做 UI 包装。

这轮你的职责很窄：

- 在 `ops` 侧设计并尽量落地一个服务
- 让我们能直接看清 `owlmlx` 单机调度时的瓶颈到底卡在哪一层

## 工作边界

你允许修改：

- `/Users/yeemio/AI/gitrep/owlops`

你只允许读取，不能修改：

- `/Users/yeemio/AI/gitrep/owlmlx`

如果你发现 `owlmlx` 上游缺少关键 truth surface，你不能在 `ops` 侧擅自发明语义补洞。
你只能：

- 明确记录缺口
- 提出精确 upstream contract request

## 本轮背景

`owlmlx` 已经正式把“单机 orchestration / scheduling”提到架构层面。

当前共识不是：

- 只要看 CPU / RAM / GPU 使用率就够了

而是：

- 我们必须知道运行调度时的瓶颈到底卡在 runtime 的哪一层，后续优化才不会靠猜

当前 `owlmlx` 已经拥有一部分 runtime-owned 调度与治理基础：

- `GenerationGate` 串行执行边界
- `ticketed_fifo`
- bounded pre-gate admission / cohort window
- model inventory
- active/default selection
- pinning
- TTL
- eviction-history governance

但它还没有完整 replacement-grade 的 single-host orchestration layer。

所以 `ops` 这一轮的任务不是“宣布调度完成”，而是：

- 做出一个 honest 的 observability / service layer
- 让我们知道瓶颈在 admission、gate、stream、residency、memory pressure、recovery 哪一层

## 本轮唯一目标

设计并尽量落地一个 `ops` 侧服务，使其能够基于 `owlmlx` 的 runtime-owned truth：

- 判断当前 orchestration bottleneck 在哪一层
- 输出支撑该判断的证据
- 区分“资源绝对不够”与“调度策略导致不可持续”

## 本轮最终只能给出两个结论之一

- `orchestration_bottleneck_service_designed`
- `orchestration_bottleneck_service_still_blocked`

如果仍 blocked，必须精确说明：

- 缺的是哪一个 `owlmlx` upstream surface
- 为什么 `ops` 侧不能诚实补出来

## 必须先读

### owlmlx 上游 truth

1. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/single-host-orchestration-architecture.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/system-architecture.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-capability-matrix.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-cache-scheduler-status.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-cache-scheduler-implementation-backlog.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-cache-continuous-batching-feasibility.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-window-exactness.md`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/kernel.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/serving.py`

### ops 当前仓内相关入口

你需要自己在 `/Users/yeemio/AI/gitrep/owlops` 里快速定位：

- 当前 runtime/ops service 入口
- 当前 status / health / metrics / dashboard / API contract 入口
- 适合承接这项工作的模块，而不是随手新开平行半成品

读完后，先输出不超过 12 行的执行计划，再动手。

## 第一性原则

- `runtime truth ownership > ops-side guess`
- `bottleneck classification > raw utilization dashboard`
- `honest unknown > fabricated certainty`
- `service contract > ad-hoc logs`
- `one narrow useful surface > another broad half-product`

## 这轮服务至少要能区分的瓶颈层

最终服务输出里，至少要能稳定表达下面这些 layer：

1. `admission`
   - 请求在进入执行前就被延迟、拒绝、或挤压
2. `generation_gate`
   - 当前主要瓶颈在 post-claim 串行执行边界
3. `stream_hold`
   - 流式请求长时间占住共享执行边界
4. `model_residency`
   - 模型装载/卸载/驻留策略是主要瓶颈
5. `memory_pressure`
   - 统一内存 / cache / reclaim / eviction 是主要瓶颈
6. `recovery`
   - restart barrier / reclaim failure / worker pollution 是主要瓶颈
7. `unknown`
   - 上游 truth 不足，当前无法诚实归类

## 这轮服务至少要给出的证据

不能只输出一个 layer 字符串。

至少要给出：

- `bottleneck_layer`
- `bottleneck_reason`
- `evidence`
- `observation_window`
- `upstream_truth_sources`
- `missing_signals`
- `confidence`

如果能做得更好，建议再给：

- queue wait / hold / exec 时间
- active model / resident model count
- stream session hold 状态
- generation gate waiters / counters
- restart / unload / ttl sweep / eviction 相关事件摘要

## 服务边界规则

### 1. 不要把任务做成纯机器监控

这轮不是：

- CPU dashboard
- RAM dashboard
- GPU dashboard

这些可以是证据，但不能代替 orchestration bottleneck classification。

### 2. 不要把任务做成 UI-first

先把 service contract 和 machine-readable 输出定义好。

可以后续再接 dashboard，但这轮主交付是服务，不是视觉界面。

### 3. 不要重写 owlmlx 语义

例如：

- 不要在 `ops` 侧自创一个 “runtime 已支持 continuous batching” 的判断
- 不要把 healthz/存活探针误写成调度 truth
- 不要把缺失 signal 强行填成 optimistic 状态

### 4. 不要扩成集群调度系统

`HAMI` 在这里最多只是帮助我们意识到：

- 调度是一个独立系统职责

但这轮不是去复制 K8s、device-plugin、multi-node placement。

## 推荐成功形态

本轮最推荐的成功形态是：

1. `owlops` 有一个新的服务或 service contract
2. 这个服务消费 `owlmlx` runtime-owned truth
3. 它能返回“当前瓶颈在哪一层”以及证据
4. 当上游 truth 不足时，它返回 `unknown` + `missing_signals`
5. 它把缺失的 upstream contract 说清楚，而不是在 `ops` 侧硬补

## 如果需要新增 contract，请优先考虑这种 shape

你可以设计自己的最终 shape，但最好至少覆盖：

```json
{
  "contract": {
    "surface": "owlops.orchestration_bottleneck_status",
    "version": "v1"
  },
  "summary": {
    "status": "partial",
    "bottleneck_layer": "stream_hold",
    "confidence": "medium"
  },
  "reason": {
    "code": "stream_session_holds_gate_until_completion",
    "message": "streaming currently monopolizes the shared post-claim execution boundary"
  },
  "evidence": {
    "queue_waiters": 3,
    "generation_gate": {
      "max_concurrent": 1,
      "queue_policy": "ticketed_fifo"
    },
    "stream": {
      "holds_shared_boundary": true
    }
  },
  "upstream_truth_sources": [
    "owlmlx./v1/runtime/status",
    "owlmlx.cache_scheduler_status"
  ],
  "missing_signals": []
}
```

上面只是 shape 示例，不是强制字段全集。

## 如果 upstream 不够，你必须这样处理

如果你发现：

- `owlmlx /v1/runtime/status` 还不能支撑某个 bottleneck 分类
- 或当前缺少一个稳定 surface

你必须在交付里明确写出：

- 缺失 surface 名称
- 需要新增的字段
- 该字段属于哪个 `owlmlx` owned contract
- 为什么没有它就只能停在 `unknown`

## 你这轮应该优先交付什么

优先级从高到低：

1. 一个窄而诚实的 service contract
2. ops 侧对应服务实现或可运行骨架
3. contract test / service test
4. 一个简短 source-of-truth 说明
5. 如有必要，再加最小 dashboard/consumer 对接

## 不要做的假成功

- 只加一个 metrics 面板，没有 bottleneck judgement
- 只有日志聚合，没有 contract
- 只有 host 资源占用，没有 runtime layer classification
- 用 shell 侧猜测替代 runtime-owned truth
- 明明 signal 不够，却不给 `unknown`

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`designed` 或 `still_blocked`
2. 最终 verdict
3. 服务 authoritative surface 是什么
4. 它能区分哪些 bottleneck layers
5. 它依赖哪些 `owlmlx` upstream truth surfaces
6. 实际修改的文件
7. 实际运行的命令与关键结果
8. 如果仍 blocked，唯一主 blocker 是什么
