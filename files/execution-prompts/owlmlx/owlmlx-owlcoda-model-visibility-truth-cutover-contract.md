# owlmlx OwlCoda Model Visibility Truth Cutover Contract

## 你是谁

你是 `/Users/yeemio/AI/gitrep/owlmlx` 这条线上的执行者。

你这轮不是在继续 Phase 45 runtime seam，也不是在给老平台 router 打补丁找理由。
你要处理的是另一个问题：

- **让 `owlmlx` 成为 `owlcoda` 依赖的正式模型可见性真源**
- **明确 `/v1/models` 或等价 visibility / inventory surface 到底归谁拥有**
- **把老平台 router 从 truth owner 收成 proxy / consumer，或者在做不到时停在最窄 blocker**

## 第一性原则

- `single truth owner > duplicated visibility logic`
- `honest availability contract > accidental model listing`
- `runtime-owned semantics > shell-side drift`
- `loaded inventory != available visibility`
- `verified blocker > fake cutover`

## 当前真实状态

### 已经成立的

- `owlcoda` 已经可以直接消费 `owlmlx` 的 `/v1/messages`、`/v1/runtime/status`、`/healthz`。
- `owlcoda` runtime probe 顺序已经不是只看 `/v1/models`，而是：
  1. `/v1/runtime/status`
  2. `/v1/models`
  3. `/healthz`
- `owlmlx` 现在已经暴露：
  - `GET /v1/models`
  - `GET /v1/openai/models`
- `owlmlx` 已经有 runtime-owned `model_inventory` schema。

### 还没有解决的

- 当前 `owlmlx /v1/models` 和 `owlmlx /v1/openai/models` 实际表达的是
  **当前 runtime 已载入 inventory**，不是 “哪些模型应稳定对 `owlcoda` 可见”。
- `owlmlx/model_inventory.py` 明确写着它 **不拥有**：
  - router model list discovery
  - catalog reading and management
- 老平台 `/Users/yeemio/AI/Agent` 上已经存在一个有效 contract：
  - formal surface 是 `router :8009 /v1/models`
  - rule 是 `gate_required_before_visible`
- 所以当前真正的 semantic gap 是：
  **`owlmlx` 还没有正式接住“稳定可见模型集合”这条真源；它只有 loaded runtime inventory。**

### 这轮明确不在解决什么

- 不解决当前 Phase 45 cache/request-aggregation seam
- 不解决 serial boundary 的继续收窄
- 不解决 cloud/provider/subscription/onboarding
- 不解决广义 control-plane 重构
- 不把 “当前已载入模型” 假装说成 “平台稳定可见模型”

## 本轮唯一目标

把 `owlmlx` 的模型可见性 contract 收成一个**可供 `owlcoda` 长期依赖**的正式答案：

- **哪个 `owlmlx` surface 是正式 truth surface**
- **模型何时应该出现在这个 surface**
- **老平台 router 在 cutover 后还剩什么角色**

如果做不到，就停在唯一主 blocker，不要把已有 loaded inventory 伪装成完成 cutover。

## 本轮必须冻结的三个单选答案

### 1. 正式 truth surface

只能三选一：

- `owlmlx_v1_models_is_formal_visibility_surface`
- `owlmlx_v1_openai_models_is_formal_visibility_surface`
- `owlmlx_new_visibility_surface_is_required`

如果选第三种，必须给出明确 endpoint 名称和稳定字段，不准写成 “以后再定”。

### 2. 可见性规则

只能二选一：

- `runtime_inventory_auto_visible`
- `runtime_gate_required_before_visible`

如果选第二种，gate 必须同时满足：

- machine-checkable
- owlmlx-owned
- 能被测试覆盖
- 不是老平台 router 私有内部状态

### 3. 老平台 router 的 cutover 角色

只能三选一：

- `router_is_proxy_of_owlmlx_visibility_truth`
- `router_is_consumer_of_owlmlx_visibility_truth`
- `router_remains_truth_owner`

如果答案仍是 `router_remains_truth_owner`，本轮最终 verdict 必须是 blocked。

## 本轮最终只能给出两个裁决之一

- `owlmlx_model_visibility_truth_ready`
- `owlmlx_model_visibility_truth_still_blocked`

## 必须覆盖的模型

你至少要对这 6 个模型给出诚实覆盖结论：

- `Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit`
- `Qwen3.5-35B-A3B-4bit`
- `Qwen3.6-27B`
- `Qwen3.6-35B-A3B`
- `gemma-4-31B-it`
- `gpt-oss-20b-MXFP4-Q4`

不能只回答抽象 contract，而不回答这 6 个模型在新 contract 下到底：

- 已满足
- 部分满足
- 仍未满足

## 必须先读

### owlmlx 内

1. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-authorized-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-earlier-runtime-owned-boundary-dependency.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/repository-boundaries.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-contracts.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/ownership-boundary.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime8-owlcoda-cutover-verification.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime9-source-first-and-replacement-verdict.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/model_inventory.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py`

### 老平台只读参考

11. `/Users/yeemio/AI/Agent/docs/source-of-truth/local-llm-platform/phase44-owlcoda-v1-models-contract.md`
12. `/Users/yeemio/AI/Agent/llm_router/models.py`
13. `/Users/yeemio/AI/Agent/llm_router/app.py`
14. `/Users/yeemio/AI/Agent/tests/test_v1_models_contract.py`

读完先输出一个不超过 10 行的执行计划，再动手。

## 硬规则

- 不准把这轮写成 Phase 45 seam 继续推进。
- 不准把 loaded runtime inventory 直接偷换成 stable model visibility truth。
- 不准修改 `owlcoda` 仓库。
- 不准把任务扩成 catalog/onboarding/cloud/provider 体系治理。
- 不准留下双真源：
  - `owlmlx` 一套
  - 老 router 再一套独立 gate
- 如果需要新增 owlmlx-owned visibility gate，必须给出：
  - schema
  - derive rule
  - tests
  - source-of-truth
- 如果发现现有 `owlmlx /v1/models` 不适合作 formal visibility surface，可以新增更窄 surface，
  但必须把 `/v1/models` 和新 surface 的语义区分写死。
- 不准只改文档不改行为。
- 不准把 “目录里有模型”“manifest 注册了”“catalog 出现了” 自动包装成 `owlmlx` 已稳定可见，除非你明确把它吸收到 owlmlx-owned rule 并用测试证明。
- 如果需要动老平台，只允许做最小 cutover/proxy/consumer 对齐，不准顺手重构整个平台。

## 执行波次

### Wave 0: Freeze The Semantic Gap

目标：
先证明当前问题不是“少一个 endpoint”，而是“loaded inventory 和 available visibility 不是同一 contract”。

必做：

- 明确写出当前 `owlmlx /v1/models`、`owlmlx /v1/openai/models` 的真实语义。
- 明确写出老平台 router `/v1/models` 的真实语义。
- 对比这两类 surface：
  - 当前载入
  - 应稳定可见
- 判断现有 owlmlx surface 是否可以直接承担这个 contract，还是必须新增更窄 surface。

验收：

- 形成一份不含糊的 semantic-gap 结论。

### Wave 1: Land The owlmlx-Owned Visibility Contract

目标：
在 `owlmlx` 内落地正式 truth owner。

必做：

- 在三选一里收死 formal surface。
- 在二选一里收死 visibility rule。
- 如果需要新 endpoint，就最小实现它，并保证语义稳定。
- 如果需要新 gate，就让 gate 明确可检查、可测试、可文档化。
- 不能继续依赖老 router 私有 gate 才能解释 `owlmlx` 自己的可见性。

验收：

- `owlmlx` 自己就能回答：
  - 哪些模型现在应可见
  - 为什么可见
  - 为什么不可见

### Wave 2: Freeze The Router Cutover Role

目标：
把老平台 router 从 owner 降到 proxy / consumer，或者诚实确认仍 blocked。

必做：

- 明确 router 在 cutover 后到底是：
  - proxy
  - consumer
  - 仍是 owner
- 如果可以做最小 downstream cutover，对齐：
  - formal surface 说明
  - 代理/消费逻辑
  - 对应测试
- 如果不能做 live cutover，也要给出一份最小 downstream follow-up：
  - 要改哪些文件
  - 需要删掉或降级哪些老 gate
  - 为什么现在还不能宣称 owlmlx 已接管

验收：

- 不再留下 “owlmlx 文档说它是 owner，但 router 代码还自己决定可见性” 这种双真源状态。

### Wave 3: Tests, Truth, And Honest Coverage

目标：
让 contract 不是口头说法。

必做：

- 补或改针对性的测试。
- 新增或更新最小 source-of-truth 文档，直接服务这条 contract。
- 对这 7 个模型给出实际覆盖结果。

验收：

- code / tests / docs 三者一致。
- 新 contract 能被 `owlcoda` 诚实消费。

## 你要特别警惕的假完成

以下都不算完成：

- 只是发现 `owlmlx` 已经有 `/v1/models`
- 只是把 loaded inventory 改个名字
- 只是写文档说“以后 router 会代理 owlmlx”
- 只是让 1 个当前已 load 的模型出现
- 只是证明 `owlcoda` probe 能打到 `owlmlx`
- 只是把老 router 的 gate 复制一份到 `owlmlx`，但 owner 语义仍不清楚

## 必跑验证

至少覆盖：

- `python3 -m pytest /Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py -q`
- 如果新增了 visibility contract tests，跑对应 targeted tests
- 如果最小改动了老平台 router，跑对应 targeted router tests
- 如能做 live 本地验证，再补：
  - 新 formal surface 的 `curl`
  - old router cutover 后的 `curl`

## 最小验收资产

- `owlmlx` 内一份新的 source-of-truth 文档，冻结 model visibility contract
- 对应代码与测试
- 如需要，补一份最小 downstream cutover note 或 prompt

## 最终输出格式

请按下面顺序输出：

1. 最终结论：`owlmlx_model_visibility_truth_ready` 或 `owlmlx_model_visibility_truth_still_blocked`
2. formal truth surface
3. visibility rule
4. router cutover role
5. 这 7 个模型的覆盖结果
6. 实际修改文件
7. 实际运行命令和关键结果
8. 如果仍 blocked，唯一主 blocker 是什么
9. `owlcoda` 现在应如何诚实展示这个依赖状态
