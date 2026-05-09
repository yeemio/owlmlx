# owlmlx - OwlCoda Runtime Model Visibility Truth Source Cutover

## 你是谁

你是 `owlmlx` 主线执行者。

这轮不是继续做 Phase 45 cache seam 微缩窄。

这轮要处理的是一个更上层、但仍然必须由 `owlmlx` 诚实回答的问题：

- `owlcoda` 现在依赖的 `/v1/models` 可见性 contract 还落在老平台
  `/Users/yeemio/AI/Agent`
- `owlmlx` 虽然已经能直接提供 `/v1/messages`、`/v1/runtime/status`、
  `/healthz`，并且当前也有一个 `/v1/models`
  route
- 但 `owlmlx` 当前 `/v1/models` 只是 loaded inventory snapshot，不等于
  “可见模型真源”

## 本轮唯一目标

回答一个更窄、也更关键的问题：

- **`owlmlx` 能不能现在就成为 `owlcoda` 的正式 model visibility truth source，而不把 runtime / control-plane boundary 搞塌？**

这不是问 `owlmlx` 能不能服务。

这轮只问：

- `owlmlx` 能不能拥有并暴露一个 runtime-owned 的 model visibility
  contract，让 `owlcoda` 不再把老平台 router `:8009` 当成 `/v1/models`
  真源？

## 本轮最终只能给出两个裁决之一

- `owlcoda_runtime_model_visibility_truth_source_introduced`
- `owlcoda_runtime_model_visibility_truth_source_still_blocked`

如果仍 blocked，必须精确说明 blocker 是：

- runtime-owned visibility truth 还缺了什么
- 为什么当前 `owlmlx /v1/models` 还不能诚实替代老平台 contract

## 当前已知真实状态

### `owlmlx` 已经具备的

- `owlmlx /v1/messages` 已有真实 cutover proof
- `owlmlx /v1/runtime/status` 已是稳定 runtime-owned contract
- `owlmlx /v1/models` 当前存在，但返回的是 runtime inventory / budget /
  health / gate snapshot，不是老平台那种 catalog visibility contract
- `owlmlx/model_inventory.py` 已经是 runtime-owned per-model truth schema

### 当前没解决的

- 老平台 `/Users/yeemio/AI/Agent/llm_router/app.py` 上最近落了
  `gate_required_before_visible`
- `owlcoda` 当前依赖的“哪些模型应该 visible”真源，仍是那个老平台
  router contract
- 所以问题不是“owlmlx 不能服务”，而是“owlmlx 还没正式接住这条 control-plane
  truth”

## 第一性原则

- `runtime truth ownership > platform fallback contract`
- `formal truth source > accidental reachable endpoint`
- `narrow honest cutover > fake replacement language`
- `runtime/control-plane boundary > convenience copy-paste`
- `real contract + tests > doc-only migration`

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime8-owlcoda-cutover-verification.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-contracts.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/ownership-boundary.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/capability-absorption-inventory.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-capability-matrix.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/model_inventory.py`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/kernel.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py`
11. `/Users/yeemio/AI/Agent/docs/source-of-truth/local-llm-platform/phase44-owlcoda-v1-models-contract.md`
12. `/Users/yeemio/AI/Agent/llm_router/models.py`
13. `/Users/yeemio/AI/Agent/llm_router/app.py`
14. `/Users/yeemio/AI/Agent/tests/test_v1_models_contract.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 边界规则

### 1. 仓库边界

你只允许修改：

- `/Users/yeemio/AI/gitrep/owlmlx`

你不允许修改：

- `/Users/yeemio/AI/Agent`
- `/Users/yeemio/AI/gitrep/owlcoda`

外部仓只允许读取，作为当前真相输入。

### 2. 语义边界

你不能把任务做成下面这些错误方向：

- 看到 `owlmlx` 已经有 `/v1/models` 就直接宣称问题解决
- 把当前 loaded inventory snapshot 误写成 old router visibility contract
- 简单复制老平台 `gate_required_before_visible` 逻辑到 `owlmlx`，却没有
  runtime-owned truth 依据
- 反过来把 runtime 应有的 model visibility truth 又推回 platform
- 顺手扩成 admin UI / onboarding / shell product work

### 3. 诚实规则

如果当前最诚实的答案是：

- `owlmlx` 现在只拥有 loaded inventory truth
- 但还没有 owned available-model visibility truth

那你必须停在 `still_blocked`，不能因为有 endpoint 就假装 cutover 已经完成。

## 本轮成功的唯一 honest 路径

如果这轮能成功，必须同时满足：

1. `owlmlx` 明确拥有一个 runtime-owned model visibility contract
2. 这个 contract 有稳定 surface，供 `owlcoda` 直接消费
3. 这个 surface 的语义不再依赖老平台 router 才成立
4. contract 与 `owlmlx` 的 runtime-owned model truth 相一致
5. 有测试证明它不是口头约定
6. 文档清楚写明：
   - authoritative source 是什么
   - `owlcoda` 应该先读什么
   - 旧平台 `/v1/models` 在这条链路里是什么角色

## 你需要回答的关键设计问题

这轮你必须明确回答，不能含糊：

1. `owlcoda` 未来应该把哪个 surface 当正式真源？
   - `owlmlx /v1/runtime/status.inventory`
   - 一个新的 runtime-owned visibility surface
   - 兼容形式的 `owlmlx /v1/models`

2. visibility rule 到底是什么？
   - loaded-inventory-only
   - runtime-owned gate required before visible
   - 还是别的更窄、但可验证的 runtime-owned 规则

3. 当前 old platform contract 中，哪些语义应该被吸收进 `owlmlx`？
4. 哪些仍应保留在 control-plane，而不属于 runtime？

## 优先实现方向

优先找“最小诚实 cutover”，不要默认做最大改造。

更推荐的成功形态是：

- 让 `owlmlx` 明确拥有 per-model visibility truth
- 让 `owlcoda` 可直接消费这个 runtime-owned truth
- 平台若要 proxy，可以 proxy，但不再重新定义语义

不推荐的假成功形态是：

- 继续让 old platform 当真源，只是文案说成 `owlmlx`
- 在 `owlmlx` 里暴露一个表面兼容 route，但其真相仍然来自 platform

## 需要同步的 surfaces

如果成功引入 runtime-owned truth source，至少同步：

- runtime-owned contract code
- runtime transport surface
- source-of-truth docs
- tests
- 一个新的 execution prompt 或 checkpoint，说明后续 cutover 如何进行

如果仍 blocked，也要同步：

- 为什么 blocked
- 当前 `owlmlx /v1/models` 到底只是什么，不是什么
- `owlcoda` 在 cutover 前应继续依赖什么

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`introduced` 或 `still_blocked`
2. 本轮 exact verdict
3. authoritative truth source 是什么
4. exact visibility rule 是什么
5. `owlcoda` 应消费哪个 surface
6. 实际修改的文件
7. 实际运行的命令与关键结果
8. 如果仍 blocked，唯一主 blocker 是什么
