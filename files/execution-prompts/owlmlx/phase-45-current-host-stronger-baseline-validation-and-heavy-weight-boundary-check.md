# owlmlx Phase 45 - Current-Host Stronger Baseline Validation And Heavy-Weight Boundary Check

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

上一轮已经完成：

- `supported_host_candidate_baseline_established`

这意味着：

- 当前开发机不再是 blocked host
- 当前开发机已有一个 runtime-owned verified baseline
- `host_stable_execution` 已经可以诚实写成：
  - `host_ready_for_runtime_validation`

但这**不等于**：

- heavy-weight repeatability 已恢复
- reference-grade stability 已建立
- customer-ready / replacement-ready 已成立

所以这轮的身份很明确：

- **不是再做 candidate baseline**
- **也不是直接追 heavy-weight repeatability**
- **而是做 stronger baseline validation / heavy-weight boundary check**

本轮的作用只有一个：

- 回答当前开发机是否已经从
  - `supported_host_candidate_baseline_established`
  推进到
  - `host_ready_not_repeated`

如果不能推进，就必须把 remaining blocker 冻成更精确的 runtime-owned truth。

## 第一性原则

- `current host baseline > stale blocked narrative`
- `stronger validation > optimistic import success`
- `heavy-weight boundary exactness > premature repeatability claims`
- `exact blocked outcome > vague “closer now” language`
- `one heavier boundary check > reopening old branches`

## 当前真实状态

### 已经成立的

- `summary.status = host_ready_for_runtime_validation`
- `supported_host_candidate_baseline_established`
- default `~/.owlmlx` registry 和 isolated registry 都能选中：
  - `omlx-probe-venv`
- minimal runtime-owned smoke 已成立：
  - `load_ok = true`
  - `generate_ok = true`
  - `model_id = fake-a`
- `summary.evidence_label = early_formal_runtime`
- `dominant_next_gap = host_stable_execution`

### 当前仍然没有成立的

- heavy-weight repeatability restored
- stronger repeated proof on this host
- cache parity
- governance reference-grade parity
- replacement/customer-ready

### 当前最关键的剩余边界

- `heavy_weight_runtime_repeatability` 当前仍是：
  - `local_preconditions_incomplete`

所以这轮不是任意做 heavier work，而是：

- 要么把当前 host 推进到：
  - `host_ready_not_repeated`
- 要么把 `local_preconditions_incomplete` 的 exact blocker 冻得更强

## 本轮唯一目标

做一轮 **current-host stronger baseline validation / heavy-weight boundary check**：

- 证明当前 baseline 不只是 import-ready，而是 heavier runtime validation ready
- 同时不越级声称 repeated heavy-weight proof 已经建立

本轮最终只能给出两个裁决之一：

- `host_ready_not_repeated`
- `boundary_check_still_preconditions_blocked`

## 必须先读

1. `/Users/yeemio/AI/gitrep/runtime-probes/2026-04-16-mlx-omlx-vmlx-baseline-investigation.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/replacement-grade-stability-gaps.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-host-stable-execution-status.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-heavy-weight-repeatability-status.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-dominant-gap-reselection.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-current-host-supported-candidate-baseline.md`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/heavy_weight_repeatability_status.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/customer_runtime_evidence.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_heavy_weight_repeatability_status.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_customer_runtime_evidence.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_dominant_gap_reselection.py`

读完先输出不超过 12 行的执行计划，再动手。

## 硬规则

### 1. 本轮禁止事项

本轮不允许：

- 继续 cache widening
- 继续 governance micro-rounds
- 基准/性能/benchmark 题材漂移
- MiniMax / product narrative 漂移
- 把 boundary check 写成 repeatability restored
- 宣称 parity / replacement-ready / customer-ready

### 2. heavy-weight 规则

这轮做的是：

- **boundary check**

不是：

- repeated heavy-weight proof

所以必须严格区分：

- baseline stronger validation passed
- heavy-weight preconditions satisfied
- first heavy boundary check passed
- repeated heavy-weight proof visible

这四层不能混成一句话。

### 3. specimen 规则

如果 `specimen_path`、weights、或 prerequisite truth 不足：

- 不准跳过
- 不准编故事
- 直接冻结 exact preconditions blocker

如果 heavier boundary check 只做到：

- preconditions satisfied
- first boundary smoke attempted

也不能直接写成：

- repeatability restored

### 4. 证据等级规则

本轮最多只允许推进到：

- `host_ready_not_repeated`

或：

- `boundary_check_still_preconditions_blocked`

不允许直接推进到：

- `supported_host_repeatability_visible`
- `runtime_evidence_expanding`
- `approaching_reference_grade_stability`
- `customer-ready`

## 预计时长与 Wave 规划

- Wave 0: heavier-boundary intake freeze
- Wave 1: preconditions exactness check
- Wave 2: stronger baseline validation
- Wave 3: first heavy boundary check
- Wave 4: truth sync
- Wave 5: coordinator checkpoint closeout

## Wave 0: Heavier-Boundary Intake Freeze

目标：
- 明确这轮 heavier validation 到底验证哪条边界

必做：
- 记录：
  - 当前 verified baseline
  - 当前 execution mode
  - 当前 heavy-weight specimen target（如果存在）
  - 当前 preconditions truth
- 明确这轮不是 repeatability round，而是 stronger boundary round

验收：
- heavier-boundary intake truth 清楚

## Wave 1: Preconditions Exactness Check

目标：
- 把 `local_preconditions_incomplete` 拆成 exact current truth

必做：
- 核对 heavy-weight 所需 preconditions：
  - specimen_path
  - weights completeness
  - baseline availability
  - any required config/launch preconditions
- 明确哪些已满足，哪些未满足
- 如果仍不满足，直接生成更精确 blocked truth

验收：
- heavy-weight preconditions 不再只是模糊“不完整”

## Wave 2: Stronger Baseline Validation

目标：
- 证明当前 baseline 可以承受更强一层的 runtime validation

必做：
- 在当前 verified baseline 上跑 stronger validation
- 必须至少超出“fake-a minimal smoke”，但仍保持 boundary check 范围
- 明确区分：
  - import success
  - minimal smoke success
  - stronger baseline validation success

验收：
- current-host baseline 不再只停留在 candidate smoke 层

## Wave 3: First Heavy Boundary Check

目标：
- 试一次真实 heavy-weight boundary，而不是直接要求 repeated proof

必做：
- 如果 preconditions 已满足，尝试一次 first heavy boundary check
- 只要求回答：
  - boundary can be entered
  - or exact blocker remains
- 不要求 repeated proof
- 如果失败，冻结 exact failure shape

验收：
- heavy-weight boundary truth 比 `local_preconditions_incomplete` 更强

## Wave 4: Truth Sync

目标：
- 让上层 truth 跟上更强边界结果

必做：
- 更新：
  - `phase45-heavy-weight-repeatability-status`
  - `phase45-customer-runtime-evidence-ledger`
  - `phase45-dominant-gap-reselection`
- 只在 truth 真的变化时才升级 rung

验收：
- higher-level truth 与当前 heavier boundary verdict 一致

## Wave 5: Coordinator Checkpoint Closeout

目标：
- 收口，不偷开 repeatability 主线

必做：
- 新增一个 coordinator checkpoint
- 只回答：
  - 当前 host 是否已到 `host_ready_not_repeated`
  - 下一步是否授权真正的 repeated heavy-weight validation
- 不准直接继续做下一阶段

验收：
- 统筹者看完能直接做下一步二选一

## 必跑测试

至少跑并报告：

- `python3 -m pytest tests/test_mlx_environment.py tests/test_host_stability.py tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q`

另外必须跑：

- `runtime_heavy_weight_repeatability_status.py`
- `runtime_customer_runtime_evidence.py`
- `runtime_dominant_gap_reselection.py`

如果本轮动到 baseline 相关实现，也补跑对应 targeted pytest。

## 必更新的真源

本轮最少更新：

- `phase45-heavy-weight-repeatability-status`
- `phase45-customer-runtime-evidence-ledger`
- `phase45-dominant-gap-reselection`
- 一份新的 heavier-boundary coordinator checkpoint

## Out Of Scope

- repeated heavy-weight proof
- cache branch reopen
- governance branch reopen
- benchmark / optimization work
- product / control-plane / shell work
- replacement storytelling

## 最终输出格式

你的最终汇报必须包含：

- `Modified files`
- `Wave-by-wave outcomes`
- `Current heavier-boundary truth`
- `Tests run`
- `Runtime baseline checked`
- `Heavy-weight preconditions checked`
- `Release-readiness delta`
- `Remaining blockers before repeated heavy-weight validation`
- `Coordinator verdict`

最后的 `Coordinator verdict` 只能是其中一个：

- `host_ready_not_repeated`
- `boundary_check_still_preconditions_blocked`

## Commit Message

使用：

- `owlmlx: validate stronger baseline and check heavy-weight boundary`
