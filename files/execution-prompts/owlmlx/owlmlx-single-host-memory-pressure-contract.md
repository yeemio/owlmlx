# owlmlx - Single-Host Memory Pressure Contract

## 你是谁

你是 `owlmlx` 主线执行者。

这轮不是 `owlops` 消费侧工作，也不是 UI / dashboard / ops service。

这轮继续做 `owlmlx` 自己的单机调度层，焦点是 memory pressure。

## 工作目录

`/Users/yeemio/AI/gitrep/owlmlx`

## 本轮定位

`owlmlx` 已经引入：

- `scheduler_admission_contract`
- `model_residency_policy`

现在 admission 能解释为什么非 resident target 不能假装 defer-to-load；residency 能解释 active/default/resident/pinned/ttl/evictable 的当前状态。

下一个 dominant gap 是：

- `memory_pressure_contract`

这不是 full reclaim engine，也不是 recovery supervisor。

## 本轮唯一目标

引入一个窄而真实的 runtime-owned `memory_pressure_contract`。

它要回答：

- 当前 budget truth 能支持哪些 pressure classification？
- 当前是否能根据 runtime-owned truth 做 reclaim / eviction / restart barrier 决策？
- 哪些压力语义仍必须保持 `unknown` 或 `insufficient_signal`？

## 最终 verdict 只能二选一

- `owlmlx_memory_pressure_contract_introduced`
- `owlmlx_memory_pressure_contract_still_blocked`

如果仍 blocked，必须精确说明：

- 缺的是哪一个 runtime-owned pressure / reclaim / barrier signal
- 为什么当前不能诚实冻结 memory pressure contract
- 下一轮应补哪个最小 contract

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/single-host-orchestration-architecture.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/scheduler-admission-contract.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/model-residency-policy.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/orchestration-status-surface.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/memory_budget.py`
7. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/kernel.py`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_memory_budget.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_kernel.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 第一性原则

- `budget truth != pressure event truth`
- `evictable state != pressure victim selection`
- `honest insufficient_signal > fake reclaim confidence`
- `contract + tests > architecture prose`
- `recovery barrier remains separate until really owned`

## 本轮应该定义的 pressure 语义

至少要覆盖：

- `within_budget`
- `near_budget`
- `over_budget`
- `unknown`
- `insufficient_signal`

至少要考虑这些 runtime truth：

- serving budget
- currently loaded memory
- available memory
- utilization
- loaded model count
- TTL-sweep evictable models from residency policy, if available
- restart / recovery visibility as non-decisive context

## 本轮不能做什么

不要做：

- 完整 reclaim engine
- pressure-ranked eviction
- recovery supervisor
- automatic model unload under pressure
- continuous batching
- multi-worker scheduler depth
- UI / dashboard
- OwlOps service implementation

不要宣称：

- memory pressure closure 已完成
- budget utilization 等于 direct pressure event
- eviction history 等于 pressure policy
- restart visibility 等于 recovery barrier

## 推荐成功形态

如果成功，最小成功形态应该包括：

1. runtime-owned contract code
2. plain dict / JSON-serializable output
3. operator or transport entry
4. source-of-truth 文档
5. runtime-status schema 更新
6. tests

## 关键判断规则

你必须明确回答：

1. 当前 budget truth 能冻结哪些 pressure classification？
2. 哪些状态只能 `insufficient_signal`，不能转成 reclaim / eviction / restart？
3. memory pressure contract 与 residency policy 的边界在哪里？
4. memory pressure contract 与 recovery supervisor 的边界在哪里？
5. 当前是否存在 runtime-owned pressure victim selection？如果没有，必须明确说没有。

## 验证要求

至少运行：

- 新增 contract 的 targeted tests
- 相关 `memory_budget` / `runtime_kernel` / `runtime_server` tests
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
4. pressure classifications 支持哪些
5. 哪些仍必须保持 `unknown` / `insufficient_signal`
6. 实际修改的文件
7. 实际运行的命令与关键结果
8. 如果仍 blocked，唯一主 blocker 是什么
