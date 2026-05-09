# owlmlx - Single-Host Scheduler Admission Contract

## 你是谁

你是 `owlmlx` 主线执行者。

这轮不是 `owlops` 消费侧工作，也不是 UI / dashboard / ops service。

这轮开始做 `owlmlx` 自己的单机调度层。

## 工作目录

`/Users/yeemio/AI/gitrep/owlmlx`

## 本轮定位

`owlmlx` 已经把 single-host orchestration 提到架构层面。

现在要做第一块真正的 runtime-owned 调度工作：

- `scheduler_admission_contract`

这不是完整 local scheduler，也不是 continuous batching。

它要回答的是：

- 请求进入执行边界之前，runtime 应该如何自动判断、接纳、延迟、拒绝、或标记 unknown？
- 哪些 admission 信号已经由 `owlmlx` runtime 真实拥有？
- 哪些信号仍然缺失，不能假装已经可调度？

## 本轮唯一目标

引入一个窄而真实的 runtime-owned `scheduler_admission_contract`。

它必须成为后续自动调度层的第一个正式 contract，而不是一段文档叙事。

## 最终 verdict 只能二选一

- `owlmlx_scheduler_admission_contract_introduced`
- `owlmlx_scheduler_admission_contract_still_blocked`

如果仍 blocked，必须精确说明：

- 缺的是哪一个 runtime-owned signal
- 为什么当前不能诚实冻结 admission contract
- 下一轮应补哪个最小 contract

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/single-host-orchestration-architecture.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/system-architecture.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-capability-matrix.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-cache-scheduler-status.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-cache-scheduler-implementation-backlog.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-cache-continuous-batching-feasibility.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-window-exactness.md`
9. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-pre-gate-admission-hook-exactness.md`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/serving.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/kernel.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_serving.py`
14. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 第一性原则

- `runtime-owned policy > shell-side routing`
- `automatic admission decision > manual operator guessing`
- `honest unknown > fake scheduling confidence`
- `post-claim serial safety > throughput ambition`
- `contract + tests > architecture prose`

## 本轮应该定义的 admission 语义

至少要覆盖：

- `accepted`
- `deferred`
- `rejected`
- `unknown`

至少要考虑这些请求类别：

- `interactive`
- `stream`
- `benchmark`
- `maintenance`
- `unknown`

至少要考虑这些 runtime 信号：

- generation gate state
- gate waiters / queued counters
- pre-gate admission window state
- model residency / active model state
- memory budget pressure
- restart / recovery state
- stream hold state, if currently available

## 本轮不能做什么

不要做：

- 完整 local scheduler
- continuous batching
- multi-worker scheduler depth
- UI / dashboard
- OwlOps service implementation
- cluster scheduling / HAMI 形态复制
- 对 post-claim `max_concurrent=1` 和 `ticketed_fifo` 的绕过

不要宣称：

- full local scheduler exists
- continuous batching exists
- multi-worker serving is safe
- admission contract alone solves model residency / memory pressure / recovery

## 推荐成功形态

如果成功，最小成功形态应该包括：

1. runtime-owned contract code
2. plain dict / JSON-serializable output
3. operator or script entry
4. source-of-truth 文档
5. runtime-status schema / capability matrix 更新，如适用
6. tests

可以考虑这样的 surface 名称：

- `owlmlx.scheduler_admission_contract`

可以考虑这样的脚本入口：

- `scripts/runtime_scheduler_admission_contract.py`

可以考虑这样的文档：

- `docs/source-of-truth/scheduler-admission-contract.md`

这些名称不是强制，但最终必须清晰、可查、可测。

## 建议 contract shape

你可以调整字段，但最小 shape 应该表达：

```json
{
  "contract": {
    "surface": "owlmlx.scheduler_admission_contract",
    "version": "v1"
  },
  "summary": {
    "status": "partial",
    "admission_decision": "deferred",
    "request_class": "stream",
    "confidence": "medium"
  },
  "reason": {
    "code": "post_claim_generation_gate_busy",
    "message": "The serialized generation gate is active and has waiters."
  },
  "signals": {
    "generation_gate": {},
    "pre_gate_admission": {},
    "budget": {},
    "recovery": {}
  },
  "preserved_invariants": [
    "max_concurrent_1_after_gate_claim",
    "ticketed_fifo_after_gate_claim",
    "no_hidden_bypass_of_whole_request_gate_claim"
  ],
  "missing_signals": []
}
```

## 关键判断规则

你必须明确回答：

1. 当前 admission decision 是根据哪些 runtime-owned 信号得出的？
2. 哪些请求类别现在能被 runtime 诚实分类？
3. 哪些类别必须保持 `unknown`？
4. 哪些状态只能 `deferred`，不能 `accepted`？
5. 什么情况下必须 `rejected`？
6. admission contract 和 `GenerationGate` 的边界在哪里？

## 和现有 Phase 45 cache/scheduler truth 的关系

当前已知 truth：

- `GenerationGate` 仍是 post-claim 安全边界
- `max_concurrent=1` 仍是当前 validated floor
- `ticketed_fifo` 仍是当前 post-claim policy
- bounded pre-gate admission / cohort window 已经存在
- continuous batching 仍未完成
- stream hold 仍是当前调度深度中的关键 blocker

这轮要做的是：

- 把 admission decision 变成 runtime-owned contract
- 为后续 request scheduler / residency / memory pressure policy 铺路

不是：

- 改写这些已冻结 truth
- 把 admission contract 包装成 batching

## 验证要求

至少运行：

- 新增 contract 的 targeted tests
- 相关 `serving` / `runtime_server` tests
- 对应 operator script，如果新增了脚本入口

如果某些测试因为当前仓库状态无法运行，必须说明：

- 哪个命令失败
- 失败是否影响本轮 verdict
- 已运行的最窄替代验证是什么

## 交付格式

按下面顺序输出：

1. 一句最终结论：`introduced` 或 `still_blocked`
2. exact verdict
3. authoritative surface 是什么
4. admission decisions 支持哪些
5. request classes 支持哪些
6. 哪些仍必须保持 `unknown`
7. 实际修改的文件
8. 实际运行的命令与关键结果
9. 如果仍 blocked，唯一主 blocker 是什么
