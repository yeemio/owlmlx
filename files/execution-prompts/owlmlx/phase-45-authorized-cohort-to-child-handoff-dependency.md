# owlmlx Phase 45 - Authorized Cohort-To-Child Handoff Dependency

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

当前 cache 主线已经完成：

- bounded pre-gate hook 存在
- real pre-gate request-aggregation / cohort window 已可见
- one non-stream child exchange 已可承载多个 request
- child exchange 自身不再是 active seam

coordinator 现在授权的不是再做 ingress/window，也不是再做 child
exchange capability，而是：

- **cohort_to_child_exchange_handoff_dependency**

这轮不是：

- 重开 host / heavy-weight
- 重开 governance
- 重做 ingress/window
- 重做 child-exchange capability
- 讲 continuous batching / parity / replacement-ready

## 第一性原则

- `main-path cohort handoff > already-solved child exchange capability`
- `preserve post-claim serial invariants > widening speed`
- `one exact handoff verdict > broad batching story`
- `stream hold stays secondary until handoff moves`
- `runtime-owned truth > speculative throughput narrative`

## 当前真实状态

### 已经成立的

- supported-host branch 已冻结在：
  - `supported_host_repeatability_visible`
- cache active seam 已推进到：
  - `owlmlx.cache_request_aggregation_active_seam`
- current live cache truth:
  - `seam_rung = aggregation_active_seam_exact`
  - `selected_seam = cohort_to_child_exchange_handoff_dependency`
  - `selected_seam.status = pre_gate_cohort_not_yet_handed_off_to_aggregated_child_exchange`
- preserved secondary dependency:
  - `stream_session_holds_gate_until_completion`
- preserved secondary runtime branch:
  - `turboquant_preconditions = preconditions_exact`

### 当前不能宣称的

- main serving path already hands cohorts into aggregated child exchange
- stream release / interleaving exists
- continuous batching exists
- cache parity exists

### 必须继续冻结的 post-claim invariants

- `max_concurrent_1_after_gate_claim`
- `ticketed_fifo_after_gate_claim`
- `serial_safety_validated_only_after_gate_claim`

## 本轮唯一目标

回答一个更窄的问题：

- **在 bounded pre-gate cohort window 已存在、child exchange 也已支持 aggregated non-stream dispatch 的前提下，main serving path 能不能把这个 bounded cohort 真正 hand off 到 aggregated child exchange，同时不破坏 post-claim serial invariants，也不把 stream path 一起带动？**

本轮最终只能给出两个裁决之一：

- `cohort_handoff_visible`
- `cohort_handoff_still_blocked`

如果仍 blocked，必须把 blocker 写得比当前更接近真实 runtime seam。

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/replacement-grade-stability-gaps.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-window-exactness.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-active-seam.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-child-exchange-aggregated-dispatch-exactness.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-dominant-gap-reselection.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-child-exchange-aggregated-dispatch-visible.md`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_request_aggregation_active_seam.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/serving.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/kernel.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_lm_subprocess_backend.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 硬规则

### 1. 依赖边界硬限制

这轮只准处理：

- `cohort_to_child_exchange_handoff_dependency`

不准顺手处理：

- stream release / stream interleaving
- continuous batching
- multi-worker scheduler depth
- cache parity

### 2. serial safety 硬限制

不能改变：

- post-claim `max_concurrent=1`
- post-claim ticketed FIFO
- serial safety boundary begins only after whole-request gate claim

### 3. stream stays secondary

即便 cohort handoff 有进展，也不能把：

- `stream_session_holds_gate_until_completion`

一起写成已解决。

### 4. truth 表达硬限制

必须分开写：

- request-aggregation window truth
- child-exchange capability truth
- cohort-to-child handoff truth
- preserved stream secondary truth
- higher-level evidence sync

### 5. active truth versioning

如果这轮创建或实质修订了 active seam truth / checkpoint / prompt，
不要留在 chat 或 untracked 状态里。

## Wave Plan

- Wave 0: scope freeze
- Wave 1: handoff exact dependency design
- Wave 2: narrow runtime implementation
- Wave 3: tests + live/runtime evidence
- Wave 4: truth sync
- Wave 5: checkpoint closeout

## 必跑测试

至少跑并报告：

- `python3 -m pytest tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py tests/test_mlx_lm_subprocess_backend.py tests/test_cache_request_aggregation_window_exactness.py tests/test_cache_request_aggregation_active_seam.py tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q`

如果新增 handoff truth surface，对应测试必须一起补上。

另外必须跑并报告任何与 cohort handoff 直接相关的 live/runtime script or
harness command。
