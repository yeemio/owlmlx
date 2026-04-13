# owlmlx Stabilization-1: Upstream Contract Freeze And Runtime Reliability

## 你是谁

你是 `/Users/yeemio/AI/gitrep/owlmlx` 的主线执行者。

你的任务不是继续做 replacement-grade 叙事，也不是把 control-plane 或
operator UI 塞回 `owlmlx`。你的任务是把 `owlmlx` 收口成一个稳定、可信、
可被 `owlcoda` 和 `owlops` 长期依赖的上游 runtime。

## 第一性原则

- `runtime truth > replacement narrative`
- `stable upstream contract > 临时兼容 patch`
- `runtime-only reliability > 再补一个 seam`
- `verified blocked state > 假装 replaceable`
- `owlmlx runtime core != control-plane`

## 当前真实状态

### 已经成立的

- `owlmlx` 已经是可执行 runtime，不再只是 schema 库或实验 runtime。
- 真实 MLX load -> generate -> unload 已成立。
- persistent child session、streaming、OpenAI compat、Anthropic `/v1/messages`、tool seam 已成立。
- `owlcc` 和 `owlcoda` 的真实 cutover proof 已完成。
- `/v1/runtime/status`、restart、health surface 已成立。
- replacement readiness surface 已成立，但最终 verdict 仍然是 `not yet replaceable`。

### 当前关键缺口

- `owlmlx` 作为上游 runtime 的契约还没有被明确收紧为“长期可依赖”状态。
- runtime-only failure mode / soak / reliability harness 还不够强。
- full source-first parity、full production control-plane closure、operations-level replacement 都不是 `owlmlx` 单仓可以解决的问题。
- 如果下一轮 scope 漂移，最容易犯的错就是把 control-plane、policy、operator UX 再拉回 `owlmlx`。

## 本轮唯一目标

把 `owlmlx` 推进到一个更稳的上游 runtime 阶段：

**冻结给 `owlcoda` / `owlops` 消费的 runtime 契约，并补齐 runtime-only 稳定性验证与 blocker 级缺口。**

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/AGENTS.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/master-outline.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime12-replacement-readiness-verdict.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/repository-boundaries.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/ownership-boundary.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-capability-matrix.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/server.py`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/kernel.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/backends.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_lm_subprocess_backend.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime_status.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime_health.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/model_inventory.py`
14. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py`
15. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_status.py`
16. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_mlx_lm_subprocess_backend.py`
17. `/Users/yeemio/AI/gitrep/owlops/docs/source-of-truth/system-architecture.md`
18. `/Users/yeemio/AI/gitrep/owlops/docs/source-of-truth/migration-map.md`

读完先输出不超过 10 行的执行计划，再动手。

## 硬规则

- 不把 `owlmlx` 的下一轮写成 `Runtime-13`。这轮是 `Stabilization-1`，不是继续 seam 编号。
- 不新增 `owlmlx` 对 control-plane、dashboard、operator UX 的 ownership。
- 不在 `owlmlx` 内实现 lifecycle daemon、TTL policy、operator action queue、replacement verdict 展示层。
- 不把 “上层还没完成” 伪装成 `owlmlx blocked`；只收 `owlmlx` 自己的 runtime 缺口。
- 不把 inferred 写成 verified。
- 不把 `not yet replaceable` 改写成更积极的结论。
- 如果发现当前工作树已有未提交改动，除非和本轮直接相关，否则不要覆盖或回退。
- 把当前 `mlx_environment.py` / `test_mlx_environment.py` 的 quarantine 改动视为 pre-existing local work；除非本轮直接收紧或文档化该 runtime contract，否则不要把它们混进 Stabilization-1。
- 所有 capability label 必须保持诚实：`supported / partial / experimental / not in scope`。

## 预计时长与 Wave 规划

- Wave 0: 冻结上游消费者真正依赖的 runtime 契约面
- Wave 1: 找出需要在 `owlmlx` 内明确化的 contract gaps
- Wave 2: 实现最小必要的 runtime contract hardening
- Wave 3: 增加 runtime-only reliability / failure-mode harness
- Wave 4: 同步 tests + docs + capability labels
- Wave 5: 验收、gate 记录、边界复核

## Wave 0: Freeze The Consumer Contract Surface

目标：
明确 `owlcoda` 和 `owlops` 实际依赖 `owlmlx` 的哪些 surface，并把“本轮到底收什么”说死。

必做：

- 盘清 `owlmlx` 当前上游 contract surface：
  - `/v1/runtime/status`
  - `/healthz`
  - `/v1/messages`
  - runtime status / health / inventory / budget / restart truth
- 对照 `owlops` 文档，明确哪些是上游必须稳定提供的 contract，哪些还只是内部实现细节。
- 明确列出本轮“runtime-owned”范围，避免把 `owlops` 的 control-plane 任务吸回 `owlmlx`。

验收：

- 有一份明确的 contract freeze 结果，能回答：
  - 上游现在依赖哪些 surface
  - 哪些字段/语义必须稳定
  - 哪些仍然是内部细节或暂不承诺

## Wave 1: Identify Runtime-Only Gaps

目标：
把当前真正属于 `owlmlx` 的 blocker 找出来，不再重复上层 blocker。

必做：

- 逐项核对当前 `runtime-capability-matrix.md` 中和 runtime contract / reliability 直接相关的 `partial` 项。
- 检查 `server.py`、`kernel.py`、`mlx_lm_subprocess_backend.py` 是否还存在：
  - 错误码/错误结构不稳定
  - status detail 语义不清
  - child death / restart / stale registration 边界不明确
  - streaming / messages / restart surface 在 failure mode 下行为不清晰
- 把 gap 限定为 `owlmlx` 自身可修的 runtime gaps。

验收：

- 形成一份不超过 5 项的 runtime-only dominant gap list。
- 每个 gap 都能明确落到具体文件和测试，而不是抽象“还差 production”。

## Wave 2: Harden Runtime Contracts

目标：
对最关键的 1-2 个 runtime contract gap 做实现层收口。

必做：

- 优先处理会直接影响上游稳定消费的 contract gap，例如：
  - `/v1/runtime/status` 字段稳定性 / block reason / detail 语义
  - runtime restart / child restart failure 的结构化返回
  - per-model inventory / health / readiness 的可消费性
- 如果需要新增或收紧 schema，必须同步：
  - server behavior
  - tests
  - capability truth
- 只做 runtime-owned 的 hardening，不做 control-plane policy。

验收：

- 至少一个上游关键 contract 从“可用但模糊”提升到“可稳定消费”。
- 对应回归测试成立。
- 变更能清楚说明：这改善的是 runtime upstream stability，不是产品层 UX。

## Wave 3: Add Runtime Reliability Harness

目标：
把 `owlmlx` 从“能跑”推进到“更可依赖地跑”。

必做：

- 为 runtime-only failure mode 增加验证，优先考虑：
  - child death 后下一次请求的 restart behavior
  - repeated load/unload/restart cycle
  - stream path 在异常下的结构化结束/报错
  - status truth 在 backend failure 后是否仍诚实
- 如果已有脚本适合扩展，优先扩展 `scripts/` 或现有 tests，不要重新发明一套平行框架。
- 允许这轮产出 targeted harness，而不是一口气做完完整 soak 平台。

验收：

- 至少新增一组 runtime-only reliability tests 或 harness。
- 这些验证能覆盖过去 runtime 阶段没有正式钉住的 failure mode。

## Wave 4: Sync Docs And Capability Honesty

目标：
确保实现、测试、能力标签、边界文档一致。

必做：

- 更新 `runtime-capability-matrix.md` 中受影响的 capability label 和 notes。
- 如有必要，新增一份 `Stabilization-1` 真源文档，明确：
  - 本轮收了哪些 runtime contract gaps
  - 哪些仍不在 `owlmlx` 范围内
  - 为什么 control-plane closure 继续留给上层
- 不要重新扩写大而空的 roadmap；只更新直接受影响的真源。

验收：

- docs / code / tests 三者口径一致。
- 没有把上层未完成项偷偷迁回 `owlmlx`。

## Wave 5: Acceptance And Boundary Check

目标：
给这轮一个诚实收口，而不是虚假的“更接近 replaceable”。

必做：

- 复跑本轮相关测试。
- 生成简短 gate 记录：
  - 本轮修了哪些 runtime gaps
  - 哪些 failure mode 被钉住了
  - 哪些 replacement blockers 仍然不属于 `owlmlx`
- 再次检查 `repository-boundaries.md` / `ownership-boundary.md` 与本轮代码是否冲突。

验收：

- 这轮完成后，`owlmlx` 的阶段定位变成“更稳定的 upstream runtime”，而不是“重新承担 control-plane”。

## 必跑测试

- `python3 -m pytest /Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_server.py -q`
- `python3 -m pytest /Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_status.py -q`
- `python3 -m pytest /Users/yeemio/AI/gitrep/owlmlx/tests/test_mlx_lm_subprocess_backend.py -q`
- 如果本轮改到相关 truth modules，再补跑对应 targeted tests
- 如新增脚本或 harness，补跑该脚本并记录结果

## 验收资产

- `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/stabilization1-upstream-contract-freeze.md`
- 如需要，补充到 `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-capability-matrix.md`

## 本轮不在范围内

- `owlops` backend / app 实现
- lifecycle daemon / TTL policy / recovery orchestration
- operator dashboard / desktop UI
- replacement verdict 展示层
- full source-first parity 的产品层 closure
- old platform production replacement verdict 翻转

## 每个 Wave 完成后都要回答的 4 个问题

1. 上游现在多了什么稳定可依赖的 runtime contract？
2. 这轮去掉了什么 runtime 层的不确定性或误导？
3. 这轮新增了什么 failure-mode 验证或 runtime gate？
4. 哪些剩余 blocker 明确不属于 `owlmlx`？

## 最终输出格式

## owlmlx Stabilization-1 Delivery Summary

### Modified files
- [列表]

### Wave-by-wave outcomes
- Wave 0: [一句话]
- Wave 1: [一句话]
- Wave 2: [一句话]
- Wave 3: [一句话]
- Wave 4: [一句话]
- Wave 5: [一句话]

### New user-visible capabilities
- [列表]

### New/updated APIs
- [列表]

### Tests run
- [命令与结果]

### Build/check run
- [命令与结果]

### Release-readiness delta
- [一句话]

### Remaining blockers before user delivery
- [列表]

### Why this phase materially advances toward user delivery
- [一句话]

## 提交信息

如果达到可提交状态，直接 commit：

`owlmlx: stabilize upstream runtime contracts`
