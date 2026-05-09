# owlmlx Phase 45 - Fit-Within-Budget Heavy-Boundary Retarget

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

当前不是继续争论 “current host 能不能做 heavier validation”，
而是已经拿到一个更精确的事实：

- current host baseline 是绿的
- selected Kimi heavy specimen path 是绿的
- 但 selected heavy boundary 在 current host 上 exact-blocked：
  - `122.0G > 116.0G`
  - `error_code = memory_budget_exceeded`

所以这轮**不是**：

- 重复同一个 Kimi 122G heavy boundary 失败
- 回去重开 cache / governance
- 把一次 blocked 重写成 repeatability 恢复

这轮只做一件事：

- **找一个能 fit 当前 host serving budget 的 heavier boundary target / precondition set**

如果找不到，就要诚实停在 exact blocked truth。

## 第一性原则

- `exact budget blocker > repeated failed rerun`
- `fit-within-budget retarget > narrative optimism`
- `one honest heavier boundary > fake repeatability`
- `do not reopen old branches to avoid a memory truth`
- `if nothing fits, say so`

## 当前真实状态

### 已经成立的

- current host is a supported candidate baseline
- `host_stable_execution = host_ready_for_runtime_validation`
- selected Kimi specimen path is complete
- the exact budget blocker is frozen in:
  - `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-current-host-heavy-boundary-budget-blocker.md`
- `heavy_weight_runtime_repeatability = local_preconditions_incomplete`

### 当前不能宣称的

- Kimi heavy boundary entered successfully
- `host_ready_not_repeated`
- heavy-weight repeatability restored
- replacement/customer-ready/parity

## 本轮唯一目标

尝试把 heavier validation 从：

- **an over-budget Kimi boundary**

转成：

- **one budget-fitting heavy boundary on the same current host**

本轮最终只能给出两个裁决之一：

- `budget_fit_heavy_boundary_entered`
- `no_honest_budget_fit_target_found`

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-current-host-heavy-boundary-budget-blocker.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-heavy-weight-repeatability-status.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-dominant-gap-reselection.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-current-host-heavy-boundary.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_heavy_weight_repeatability_status.py`
7. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_large_weight_first_smoke.py`
8. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_customer_runtime_evidence.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_dominant_gap_reselection.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 硬规则

### 1. 本轮禁止事项

本轮不允许：

- 继续测试 `122G > 116G` 这条同一 heavy boundary
- 重开 cache widening
- 重开 governance micro-rounds
- 讲 benchmark / optimization
- 讲 parity / replacement / customer-ready
- 把 lighter smoke 冒充 heavy boundary

### 2. retarget 规则

新 target / precondition set 必须满足：

- still counts as a **heavier boundary**, not trivial smoke
- can honestly fit the current host serving budget
- does not rely on silent cheating or undocumented config hacks

如果找不到这样的 target：

- 直接输出 `no_honest_budget_fit_target_found`
- 不准强行做“差不多”的故事

### 3. evidence 规则

本轮最多只允许推进到：

- `budget_fit_heavy_boundary_entered`

不允许直接推进到：

- `host_ready_not_repeated`
- `supported_host_repeatability_visible`
- `runtime_evidence_expanding`

## 预计时长与 Wave 规划

- Wave 0: retarget search freeze
- Wave 1: fit-within-budget candidate selection
- Wave 2: first heavier boundary attempt
- Wave 3: truth sync
- Wave 4: checkpoint closeout

## Wave 0: Retarget Search Freeze

目标：
- 明确当前 round 不再重复打同一个 over-budget Kimi 边界

必做：
- 记录当前 blocked target
- 记录 current host serving budget truth
- 明确新 round 的 candidate selection standard

验收：
- 不再存在“再试一次同样 122G target”的偷懒路径

## Wave 1: Fit-Within-Budget Candidate Selection

目标：
- 找出一个 honest heavier boundary candidate

必做：
- 搜索当前可用 heavier targets / memory precondition sets
- 只保留：
  - heavier than trivial fake smoke
  - within current host serving budget
  - operationally honest
- 选 exactly one best candidate
- 如果没有候选，直接收 blocked

验收：
- 一个 selected budget-fit heavier boundary candidate
  或 exact no-fit verdict

## Wave 2: First Heavier Boundary Attempt

目标：
- 在 current host 上试一次预算内 heavier boundary

必做：
- 跑 first heavy boundary check
- 明确记录：
  - entered or blocked
  - exact reason
- 不要求 repeated proof

验收：
- one exact budget-fit boundary verdict exists

## Wave 3: Truth Sync

目标：
- 让 runtime-owned truth 跟上 retarget 结果

必做：
- 更新：
  - `phase45-heavy-weight-repeatability-status`
  - `phase45-customer-runtime-evidence-ledger`
  - `phase45-dominant-gap-reselection`
- 如果仍 blocked，就把新 blocker 写得比旧 blocker 更精确

验收：
- truth matches the retarget result exactly

## Wave 4: Checkpoint Closeout

目标：
- 收口，不偷开 repeated heavy-weight validation

必做：
- 新增一个 coordinator checkpoint
- 只回答：
  - budget-fit heavier boundary 是否进入成功
  - 下一步是否值得授权真正的 repeated heavy validation

验收：
- 统筹者可以直接做下一步判断

## 必跑测试

至少跑并报告：

- `python3 -m pytest tests/test_heavy_weight_repeatability_status.py tests/test_first_smoke_decision.py tests/test_specimen_gate.py tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q`

另外必须跑：

- `runtime_heavy_weight_repeatability_status.py`
- `runtime_large_weight_first_smoke.py`
- `runtime_customer_runtime_evidence.py`
- `runtime_dominant_gap_reselection.py`

## 必更新的真源

本轮最少更新：

- `phase45-heavy-weight-repeatability-status`
- `phase45-customer-runtime-evidence-ledger`
- `phase45-dominant-gap-reselection`
- 一份新的 retarget coordinator checkpoint

## Out Of Scope

- repeated heavy-weight proof
- cache branch reopen
- governance branch reopen
- benchmark / optimization / product story

## 最终输出格式

你的最终汇报必须包含：

- `Modified files`
- `Wave-by-wave outcomes`
- `Selected retarget candidate`
- `Heavy boundary verdict`
- `Tests run`
- `Runtime checks run`
- `Release-readiness delta`
- `Remaining blockers before repeated heavy validation`
- `Coordinator verdict`

最后的 `Coordinator verdict` 只能是：

- `budget_fit_heavy_boundary_entered`
- `no_honest_budget_fit_target_found`

## Commit Message

使用：

- `owlmlx: retarget heavy boundary to fit current host budget`
