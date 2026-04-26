# owlmlx - Single-Host Model Residency Policy

## 你是谁

你是 `owlmlx` 主线执行者。

这轮不是 `owlops` 消费侧工作，也不是 UI / dashboard / ops service。

这轮继续做 `owlmlx` 自己的单机调度层，但焦点不再是 admission。

## 工作目录

`/Users/yeemio/AI/gitrep/owlmlx`

## 本轮定位

`owlmlx` 已经引入了 runtime-owned `scheduler_admission_contract`。

当前 contract 已经能诚实回答：

- `accepted / deferred / rejected / unknown`
- `interactive / stream / benchmark / maintenance / unknown`
- `GenerationGate` 与 pre-claim admission window 的边界

但它同时也把下一个 dominant gap 暴露出来了：

- 非 resident target request 目前只能 `rejected`
- `owlmlx` 还没有 runtime-owned 的 `load-on-demand / keep-resident / evictable / pinned / ttl / default-active` policy contract

现在要做第二块真正的 runtime-owned 调度工作：

- `model_residency_policy`

这不是 eviction engine 全量实现，也不是 memory pressure policy，更不是 full scheduler。

## 本轮唯一目标

引入一个窄而真实的 runtime-owned `model_residency_policy`。

它必须成为后续 residency / memory pressure / recovery 编排层的正式 contract，而不是文档叙事。

## 最终 verdict 只能二选一

- `owlmlx_model_residency_policy_introduced`
- `owlmlx_model_residency_policy_still_blocked`

如果仍 blocked，必须精确说明：

- 缺的是哪一个 runtime-owned residency signal / policy seam
- 为什么当前不能诚实冻结 resident / pinned / ttl / evictable contract
- 下一轮应补哪个最小 contract

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/single-host-orchestration-architecture.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/system-architecture.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-capability-matrix.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/scheduler-admission-contract.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/orchestration-status-surface.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/kernel.py`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_kernel.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 第一性原则

- `runtime-owned residency policy > shell-side model guessing`
- `resident / default / pinned / ttl / evictable must be explicit`
- `honest reject > fake defer-to-load`
- `contract + tests > architecture prose`
- `pressure / recovery remain separate until really owned`

## 本轮应该定义的 residency 语义

至少要覆盖：

- `resident`
- `default_active`
- `pinned`
- `ttl_managed`
- `evictable`
- `unknown`

至少要考虑这些 runtime truth：

- active model state
- loaded model inventory
- pinned model truth
- TTL policy truth
- TTL expiry visibility
- eviction-history visibility

## 本轮不能做什么

不要做：

- 完整 eviction engine 重构
- memory pressure policy
- recovery supervisor
- continuous batching
- multi-worker scheduler depth
- UI / dashboard
- OwlOps service implementation

不要宣称：

- load-on-demand scheduler 已完整存在
- residency policy 已经解决 memory pressure
- TTL visibility 已等于 eviction policy closure
- recovery policy 已闭环

## 推荐成功形态

如果成功，最小成功形态应该包括：

1. runtime-owned contract code
2. plain dict / JSON-serializable output
3. operator or transport entry
4. source-of-truth 文档
5. runtime-status schema / capability matrix 更新，如适用
6. tests

## 关键判断规则

你必须明确回答：

1. 当前 runtime 已直接拥有哪几类 residency truth？
2. 哪些 resident/default/pinned/ttl/evictable 状态现在能诚实冻结？
3. 哪些还必须保持 `partial` 或 `unknown`？
4. admission contract 与 residency policy 的边界在哪里？
5. residency policy 与 memory pressure / recovery 的边界在哪里？

## 验证要求

至少运行：

- 新增 contract 的 targeted tests
- 相关 `runtime_kernel` / `runtime_server` tests
- 对应 operator / transport surface 验证

如果某些测试因为当前仓库状态无法运行，必须说明：

- 哪个命令失败
- 失败是否影响本轮 verdict
- 已运行的最窄替代验证是什么

## 交付格式

按下面顺序输出：

1. 一句最终结论：`introduced` 或 `still_blocked`
2. exact verdict
3. authoritative surface 是什么
4. residency states 支持哪些
5. 哪些仍必须保持 `unknown` / `partial`
6. 实际修改的文件
7. 实际运行的命令与关键结果
8. 如果仍 blocked，唯一主 blocker 是什么
