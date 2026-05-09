# owlmlx Phase 45 - Authorized Narrow Repeated Heavy-Weight Validation

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

上一轮已经完成：

- current host is `host_ready_for_runtime_validation`
- one budget-fit heavy boundary has entered once on the current host
- selected target is:
  - `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- current repeatability truth is still:
  - `budget_fit_heavy_boundary_entered`

coordinator 已经明确选择 `H1`。

这意味着这轮**不是**：

- 再证明 host 能不能做 heavier validation
- 再做 retarget
- 再辩 baseline 是否成立
- 重开 cache / governance

这轮只做一件事：

- **在默认 `~/.owlmlx` truth 上，对同一条 budget-fit heavier path 做一轮窄口 repeated heavy-weight validation**

## 第一性原则

- `default ~/.owlmlx truth > isolated /tmp diagnostic truth`
- `same selected budget-fit path > retarget churn`
- `repeated proof visibility > one more optimistic smoke`
- `exact repeat outcome > narrative inflation`
- `narrow repeated validation > reopening frozen branches`

## 当前真实状态

### 已经成立的

- `host_stable_execution = host_ready_for_runtime_validation`
- default `~/.owlmlx` registry selects:
  - `omlx-probe-venv`
- historical quarantine residue remains visible but not blocking
- selected heavier target remains:
  - `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- selected boundary still fits current serving budget:
  - `62.0G <= 116.0G`
- one real heavy boundary entry already exists on this path

### 当前不能宣称的

- heavy-weight repeatability restored
- parity / replacement-ready / customer-ready
- cache/governance closure
- supported-host repeated proof already visible

## 本轮唯一目标

回答一个更窄的问题：

- **这条已经进入一次的 budget-fit heavier path，能不能在当前 host 的默认 `~/.owlmlx` truth 上重复成立到“proof visible”级别？**

本轮最终只能给出两个裁决之一：

- `supported_host_repeatability_visible`
- `repeated_validation_still_unproven`

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/replacement-grade-stability-gaps.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-host-stable-execution-status.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-heavy-weight-repeatability-status.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-dominant-gap-reselection.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-budget-fit-heavy-boundary.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/heavy_weight_repeatability_status.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/customer_runtime_evidence.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/dominant_gap_reselection.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_large_weight_first_smoke.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_heavy_weight_repeatability_status.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_customer_runtime_evidence.py`
14. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_dominant_gap_reselection.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 硬规则

### 1. 目标路径硬限制

本轮只准打：

- `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`

不准：

- 回到 `/Users/yeemio/AI/Agent/models/Kimi-K2.5-3bit`
- 另选别的 lighter / heavier target
- 再做 retarget

### 2. truth 硬限制

本轮 primary evidence 必须来自：

- 默认 `~/.owlmlx` registry truth

可以保留 isolated `/tmp` registry 作为 diagnostic reference，
但：

- 不准拿纯 `/tmp` 隔离结果充当本轮主结论
- 不准用 isolated truth 覆盖 default truth

### 3. 分层表达硬限制

必须分开写：

- default `~/.owlmlx` baseline truth
- historical quarantine residue
- repeat run outcomes
- higher-level truth sync

不准把这些层混成一句 “都绿了”。

### 4. frozen branch 硬限制

本轮不允许：

- 重开 cache widening
- 重开 governance micro-rounds
- benchmark / optimization 漂移
- parity / replacement / customer-ready 叙事
- 把 repeated validation 写成 `repeatability restored`

### 5. proof 判定硬限制

只有在默认 `~/.owlmlx` truth 上，selected path 出现：

- at least two successful repeat runs
- exact same selected target
- exact same supported baseline posture

才允许把本轮结果写成：

- `supported_host_repeatability_visible`

如果 repeat run 数量不够，或者任一 run exact-blocked / failed：

- 只能收口为 `repeated_validation_still_unproven`

### 6. script/interface 硬限制

如果 `runtime_customer_runtime_evidence.py` 或
`runtime_dominant_gap_reselection.py` 还不能把 repeated proof visible
带上来：

- 可以做 narrow patch
- 必须补 targeted tests
- 只准补这条 repeated-proof truth carriage
- 不准顺手扩别的叙事面

## 预计时长与 Wave 规划

- Wave 0: authorization freeze
- Wave 1: default-registry preflight
- Wave 2: repeat run 1
- Wave 3: repeat run 2
- Wave 4: truth sync
- Wave 5: coordinator checkpoint closeout

## Wave 0: Authorization Freeze

目标：
- 把 H1 边界写死到执行面

必做：
- 记录：
  - authorized path
  - default-registry requirement
  - forbidden branches
- 明确这轮不是 retarget round，不是 host-argument round

验收：
- execution scope 只有 repeated validation

## Wave 1: Default-Registry Preflight

目标：
- 在默认 `~/.owlmlx` truth 上确认 baseline 仍然成立

必做：
- 跑 default registry readiness / host-stability checks
- 明确记录：
  - selected baseline
  - execution mode
  - quarantine residue still historical, not active blocker
- 如果 default truth 已变坏，冻结 exact blocker 并停

验收：
- default-registry preflight exact and current

## Wave 2: Repeat Run 1

目标：
- 在授权 target 上做第一条 repeat run

必做：
- 使用默认 `~/.owlmlx` truth
- 在 `/Users/yeemio/AI/Agent/models/gemma-4-31B-it` 上跑真实 heavy run
- 记录：
  - gate
  - load
  - generate
  - unload
  - generated text
  - exact failure shape if any

验收：
- first repeat run truth exists

## Wave 3: Repeat Run 2

目标：
- 在同一 target / 同一 default truth 上做第二条 repeat run

必做：
- 继续使用默认 `~/.owlmlx` truth
- 保持同一 specimen path / same path semantics
- 再记录一次：
  - gate
  - load
  - generate
  - unload
  - generated text
  - exact failure shape if any

验收：
- second repeat run truth exists

## Wave 4: Truth Sync

目标：
- 让 runtime-owned truth 跟上 repeated validation 结果

必做：
- 更新：
  - `phase45-heavy-weight-repeatability-status`
  - `phase45-customer-runtime-evidence-ledger`
  - `phase45-dominant-gap-reselection`
- 如果 repeated proof visible，确保 surface 能诚实表达：
  - `supported_host_repeatability_visible`
- 如果没 visible，冻结 exact remaining blocker / insufficiency

验收：
- upper-layer truth 与 repeat-run result exact 对齐

## Wave 5: Coordinator Checkpoint Closeout

目标：
- 收口，不偷开下一层叙事

必做：
- 新增：
  - `phase-45-coordinator-checkpoint-narrow-repeated-heavy-weight-validation.md`
- 只回答：
  - repeated proof visible 了没有
  - 如果没有，exact remaining blocker 是什么
- 不准顺手推进 parity / replacement / customer-ready

验收：
- 统筹者可以直接决定后续主线

## 必跑测试

至少跑并报告：

- `python3 -m pytest tests/test_heavy_weight_repeatability_status.py tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q`

如果动到 script surface，再补相应 targeted pytest。

另外必须跑：

- `runtime_host_stable_execution_status.py`
- `runtime_large_weight_first_smoke.py` 至少两次
- `runtime_heavy_weight_repeatability_status.py`
- `runtime_customer_runtime_evidence.py`
- `runtime_dominant_gap_reselection.py`

## 必更新的真源

本轮最少更新：

- `phase45-heavy-weight-repeatability-status`
- `phase45-customer-runtime-evidence-ledger`
- `phase45-dominant-gap-reselection`
- 一份新的 repeated-validation coordinator checkpoint

## Out Of Scope

- cache branch reopen
- governance branch reopen
- any new retarget selection
- parity / replacement / customer-ready claims
- benchmark / optimization narratives

## 最终输出格式

你的最终汇报必须包含：

- `Modified files`
- `Wave-by-wave outcomes`
- `Default-registry baseline truth`
- `Historical quarantine residue`
- `Repeat run outcomes`
- `Tests run`
- `Runtime checks run`
- `Release-readiness delta`
- `Remaining blockers after repeated validation`
- `Coordinator verdict`

最后的 `Coordinator verdict` 只能是：

- `supported_host_repeatability_visible`
- `repeated_validation_still_unproven`

## Commit Message

使用：

- `owlmlx: run narrow repeated heavy-weight validation on selected budget-fit path`
