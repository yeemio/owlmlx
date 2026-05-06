# OwlCoda Direct owlmlx Model Visibility Cutover

## 你是谁

你是 `owlcoda` 的执行者。

你这轮不是在修 `owlmlx` Phase 45 seam，也不是在帮老平台 `/Users/yeemio/AI/Agent`
里的 router 延寿。

你要解决的是：

- **让 `owlcoda` 停止把即将弃用的老 router `:8009 /v1/models` 当正式模型可见性真源**
- **让 `owlcoda` 直接消费 `owlmlx` 已冻结好的模型可见性 contract**
- **把 `owlcoda` 的 preflight / doctor / notice / capability surface 改成诚实反映这个新依赖**

## 工作边界

- 主要工作目录：`/Users/yeemio/AI/gitrep/owlcoda`
- 可以只读参考：
  - `/Users/yeemio/AI/gitrep/owlmlx`
  - `/Users/yeemio/AI/Agent`
- 不要修改 `/Users/yeemio/AI/Agent`
- 不要回头给旧 router 加新主线逻辑
- 不要把任务扩成 cloud/provider/subscription/onboarding

## 第一性原则

- `truth-owner cutover > compatibility patch`
- `owlmlx contract > deprecated router surface`
- `honest visibility semantics > “能列出来就算可见”`
- `single dependency path > dual truth sources`
- `verified blocked state > fake seamless migration`

## 当前真实状态

### 1. 老 router 现状

`/Users/yeemio/AI/Agent` 的 router 当前仍有一个 live contract：

- formal surface: `router :8009 /v1/models`
- rule: `gate_required_before_visible`

但它是将被弃用的旧面，不应该再成为 `owlcoda` 的长期正式依赖。

### 2. owlmlx 已经落下的新真源

`owlmlx` 现在已经冻结了自己的模型可见性 contract：

- formal visibility list:
  - `GET /v1/openai/models`
- diagnostic contract:
  - `GET /v1/runtime/model-visibility`
- loaded inventory only:
  - `GET /v1/models`

关键语义：

- `GET /v1/openai/models` 才是正式 visible-model list
- `GET /v1/models` 只是 loaded inventory，不是 visibility truth

### 3. owlmlx 的稳定可见性规则

当前 `owlmlx` rule 已冻结成：

- `runtime_gate_required_before_visible`

gate 是 machine-checkable 的：

1. 模型在 owlmlx visibility registry 中
2. `$MODELS_ROOT/{model-id}/` 存在
3. `$MODELS_ROOT/{model-id}/config.json` 存在

默认 `MODELS_ROOT` 是：

- `/Users/yeemio/AI/Agent/models`

### 4. 当前已覆盖的目标模型

在当前 `owlmlx` contract 下，这 6 个模型都已经是 `visible=True`：

- `Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit`
- `Qwen3.5-35B-A3B-4bit`
- `Qwen3.6-27B`
- `Qwen3.6-35B-A3B`
- `gemma-4-31B-it`
- `gpt-oss-20b-MXFP4-Q4`

### 5. 当前 `owlcoda` 的风险

如果 `owlcoda` 还继续把旧 router `/v1/models` 当正式依赖，那么：

- 它仍然依赖一个将被弃用的 control-plane 面
- 它会把 router 的旧 gate 和 owlmlx 的新 gate 混成双真源
- 它会继续误读 `owlmlx /v1/models`

## 本轮唯一目标

让 `owlcoda` 直接切到 `owlmlx` 的正式模型可见性 contract，并把旧 router
依赖降为 deprecated / non-authoritative。

## 本轮必须冻结的三个结论

### 1. `owlcoda` 的正式模型可见性依赖面

只能是：

- `owlmlx_openai_models_plus_runtime_model_visibility`

不允许继续是：

- `router_v1_models_primary`

### 2. `owlcoda` 对 `owlmlx /v1/models` 的语义

必须明确写成：

- `loaded_inventory_only`

不能继续把它当：

- `formal_visibility_surface`

### 3. 旧 router 在 `owlcoda` 中的角色

最终只能收成以下之一：

- `deprecated_fallback_only`
- `fully_removed_from_visibility_truth`

如果仍然还是主依赖，最终 verdict 必须 blocked。

## 本轮最终只能给出两个裁决之一

- `owlcoda_direct_owlmlx_visibility_cutover_ready`
- `owlcoda_direct_owlmlx_visibility_cutover_still_blocked`

## 必须先读

### owlcoda 内

1. 负责 local runtime probe / preflight / doctor / capability surfaces 的代码
2. 所有仍然把 `/v1/models` 当正式本地模型可见性来源的逻辑
3. 所有对 router `:8009` 有强依赖提示、默认文案、错误文案、fallback 文案的面

### owlmlx 只读参考

4. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime_model_visibility.py`
5. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-model-visibility-contract.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_model_visibility.py`
8. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py`

### 老平台只读参考

9. `/Users/yeemio/AI/Agent/docs/source-of-truth/local-llm-platform/phase44-owlcoda-v1-models-contract.md`

读完先给出不超过 10 行的执行计划，再动手。

## 硬规则

- 不要修改 `/Users/yeemio/AI/Agent`
- 不要修改 `owlmlx`，除非你发现的是 `owlcoda` 无法绕开的真实 contract 缺口，并且要精确停在 blocker
- 不要把旧 router 重新包装成“长期兼容主入口”
- 不要把 `owlmlx /v1/models` 当 visibility surface
- 不要只改文档不改行为
- 不要只改内部代码，不改用户能看到的诚实展示面
- 不要把“还能 fallback 到 router”包装成“已经完成 direct owlmlx cutover”

## 必须覆盖的用户可见面

至少检查并按需要修改这些面：

- local runtime probe
- preflight
- `/doctor`
- startup / launch notices
- capabilities / help / dependency status surfaces
- 与 local runtime visibility 相关的错误提示

这些面必须诚实说明：

- formal visibility source 现在是 `owlmlx /v1/openai/models`
- diagnostic detail 来自 `owlmlx /v1/runtime/model-visibility`
- `owlmlx /v1/models` 只是 loaded inventory
- old router 如果还保留，只能是 deprecated fallback，不是 primary truth

## 执行波次

### Wave 0: Find Every Old Router Truth Assumption

目标：
找出 `owlcoda` 里所有把旧 router `:8009 /v1/models` 当正式真源的点。

必做：

- 枚举 probe order
- 枚举 model visibility derivation
- 枚举 doctor / notices / help / capabilities 里的旧假设
- 找出任何把 `owlmlx /v1/models` 误当 visibility truth 的逻辑

验收：

- 得到一份精确依赖面清单，不是泛泛而谈

### Wave 1: Switch To owlmlx Formal Visibility Surfaces

目标：
把 `owlcoda` 的正式依赖切到：

- `GET /v1/openai/models`
- `GET /v1/runtime/model-visibility`

必做：

- 更新 probe / preflight / doctor / launch 路径
- 区分：
  - visibility list
  - visibility diagnostics
  - loaded inventory
- 不允许继续只靠旧 router `/v1/models`

验收：

- `owlcoda` 直接面向 owlmlx 时，能诚实判断 visible models

### Wave 2: Downgrade Old Router To Deprecated Fallback

目标：
如果仍保留 router fallback，就把它收成 deprecated。

必做：

- 明确老 router 不再是 primary truth
- 文案和状态输出必须反映这一点
- 若 fallback 仍存在，要写清楚触发条件

验收：

- 不再出现 “router 是正式依赖” 的用户口径

### Wave 3: Tests And Honest UX

目标：
把 cutover 钉在行为和输出上。

必做：

- 更新 / 新增针对 probe、doctor、visibility surfaces 的测试
- 覆盖这 7 个目标模型的可见性展示逻辑
- 验证错误 / degraded / fallback 状态下的用户输出

验收：

- code / tests / UX output 三者一致

## 你必须防止的假完成

以下都不算完成：

- 只是新增了对 `owlmlx /v1/openai/models` 的读取，但旧 router 仍是 primary
- 只是内部改了 probe，没有改 doctor / notices / capability output
- 只是把 `owlmlx /v1/models` 当成新的 `/v1/models` 真源
- 只是保留 router fallback，却继续在文案里叫它正式依赖
- 只是说“未来会弃用 router”

## 必跑验证

至少包括：

- `owlcoda` 内与 runtime probe / doctor / preflight / capability surface 相关的 targeted tests
- 如果有集成 smoke，至少跑一条 direct owlmlx 路径
- 如能做本地 live 验证，至少记录：
  - `owlmlx /v1/openai/models`
  - `owlmlx /v1/runtime/model-visibility`
  - `owlcoda /doctor` 或等价 surface

## 最终输出格式

请按下面顺序输出：

1. 最终结论：`owlcoda_direct_owlmlx_visibility_cutover_ready` 或 `owlcoda_direct_owlmlx_visibility_cutover_still_blocked`
2. `owlcoda` 现在的正式 visibility 依赖面
3. old router 现在的角色
4. 实际修改文件
5. 实际运行命令和关键结果
6. 这 7 个模型在 `owlcoda` 展示路径上的覆盖结果
7. 如果仍 blocked，唯一主 blocker 是什么
8. `owlcoda` 现在应如何诚实展示这个依赖状态
