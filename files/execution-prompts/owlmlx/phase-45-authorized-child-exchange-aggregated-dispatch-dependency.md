# owlmlx Phase 45 - Authorized Child-Exchange Aggregated-Dispatch Dependency

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

当前 cache 主线已经完成：

- bounded pre-gate hook 存在
- real pre-gate request-aggregation / cohort window 已可见
- active seam 已不再是 ingress/window

coordinator 现在授权的不是再做 window 轮，而是：

- **child_exchange_aggregated_dispatch_dependency**

这轮不是：

- 重开 host / heavy-weight
- 重开 governance
- 重做 ingress/window
- 讲 continuous batching / parity / replacement-ready

## 第一性原则

- `active child-exchange dependency > already-solved ingress window`
- `preserve post-claim serial invariants > dispatch widening speed`
- `one exact child-exchange dependency verdict > broad batching story`
- `stream hold stays secondary until child exchange moves`
- `runtime-owned truth > speculative throughput narrative`

## 当前真实状态

### 已经成立的

- supported-host branch 已冻结在：
  - `supported_host_repeatability_visible`
- cache active seam 已推进到：
  - `owlmlx.cache_request_aggregation_active_seam`
- current live cache truth:
  - `seam_rung = aggregation_active_seam_exact`
  - `selected_seam = child_exchange_aggregated_dispatch_dependency`
  - `selected_seam.status = single_request_per_child_exchange_blocks_aggregated_dispatch`
- preserved secondary dependency:
  - `stream_session_holds_gate_until_completion`
- preserved secondary runtime branch:
  - `turboquant_preconditions = preconditions_exact`

### 当前不能宣称的

- aggregated child dispatch already exists
- stream release / interleaving exists
- continuous batching exists
- cache parity exists

### 必须继续冻结的 post-claim invariants

- `max_concurrent_1_after_gate_claim`
- `ticketed_fifo_after_gate_claim`
- `serial_safety_validated_only_after_gate_claim`

## 本轮唯一目标

回答一个更窄的问题：

- **在 pre-gate cohort window 已存在的前提下，child exchange 能不能从 one-request-per-exchange 向 aggregated dispatch 迈进一步，同时不破坏 post-claim serial invariants、也不把 stream path 一起带动？**

本轮最终只能给出两个裁决之一：

- `child_exchange_aggregated_dispatch_visible`
- `child_exchange_dependency_still_blocked`

如果仍 blocked，必须把 blocker 写得比当前更接近真实 runtime seam。

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/replacement-grade-stability-gaps.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-active-seam.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-window-exactness.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-dominant-gap-reselection.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-request-aggregation-window-visible.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_request_aggregation_active_seam.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_request_aggregation_window_exactness.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/customer_runtime_evidence.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/dominant_gap_reselection.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/serving.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_cache_request_aggregation_active_seam.py`
14. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_cache_request_aggregation_window_exactness.py`
15. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_serving_pre_gate_admission_hook.py`
16. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_kernel.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 硬规则

### 1. 依赖边界硬限制

这轮只准处理：

- `child_exchange_aggregated_dispatch_dependency`

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

即便 child exchange 有进展，也不能把：

- `stream_session_holds_gate_until_completion`

一起写成已解决。

它必须继续保持 secondary，除非你被迫证明 child exchange 根本离不开
stream rewrite；如果真到这一步，只能收成 blocked。

### 4. truth 表达硬限制

必须分开写：

- request-aggregation window truth
- child-exchange dependency truth
- preserved stream secondary truth
- higher-level evidence sync

不准把 “child exchange 变动了一点” 写成 “request aggregation 已完成”。

### 5. active truth versioning

如果这轮创建或实质修订了 active seam truth / checkpoint / prompt，
不要留在 chat 或 untracked 状态里。

主线依赖文件必须纳入版本管理，或在最终汇报里明确解释为什么不是 active
path 必需文件。

## Wave Plan

- Wave 0: scope freeze
- Wave 1: child-exchange exact dependency design
- Wave 2: narrow runtime implementation
- Wave 3: tests + live/runtime evidence
- Wave 4: truth sync
- Wave 5: checkpoint closeout

## Wave 0: Scope Freeze

目标：
- 把当前 round 限定在 child exchange dependency

必做：
- 记录当前 active seam
- 记录 preserved stream secondary truth
- 记录 frozen post-claim invariants

验收：
- 本轮不会漂移成 stream round 或 continuous batching round

## Wave 1: Child-Exchange Exact Dependency Design

目标：
- 把 child-exchange widening 的最小语义写清

必做：
- 明确：
  - aggregated dispatch 到底允许什么
  - 仍不允许什么
  - 与 pre-gate cohort window 的接口关系
  - 与 post-claim serial invariants 的边界

验收：
- design exact enough to implement without reopening stream or scheduler branches

## Wave 2: Narrow Runtime Implementation

目标：
- 在 runtime path 上为 child exchange 引入最小 widening

必做：
- 实现最窄的 aggregated-dispatch dependency widening
- 保持 stream hold secondary
- 不触碰 post-claim invariants

验收：
- child exchange no longer only implies one-request-per-exchange
  或 exact blocker becomes narrower than before

## Wave 3: Tests + Live/Runtime Evidence

目标：
- 把 widening 变成可验证 truth

必做：
- 补 focused tests
- 必须覆盖：
  - active seam shift
  - child dependency status
  - customer evidence / dominant gap carriage
  - runtime/kernel or serving behavior relevant to child exchange

验收：
- tests and live/runtime evidence agree

## Wave 4: Truth Sync

目标：
- 让上层 truth honest 吃到 child-exchange 结果

必做：
- 更新：
  - `phase45-request-aggregation-active-seam`
  - 必要时新的 child-exchange dependency truth
  - `phase45-customer-runtime-evidence-ledger`
  - `phase45-dominant-gap-reselection`
  - `replacement-grade-stability-gaps`
  - `master-outline`

验收：
- active cache truth matches runtime result exactly

## Wave 5: Checkpoint Closeout

目标：
- 收口，不越级到 stream / continuous batching

必做：
- 新增 coordinator checkpoint
- 只回答：
  - child exchange aggregated dispatch 是否已可见
  - 如果是，下一 active dependency 是什么
  - 如果不是，exact blocker 是什么

验收：
- coordinator can pick the next dependency round without reopening this seam

## 必跑测试

至少跑并报告：

- `python3 -m pytest tests/test_cache_request_aggregation_active_seam.py tests/test_cache_request_aggregation_window_exactness.py tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py -q`

如果新增 child-exchange truth surface，对应测试必须一起补上。

另外必须跑并报告任何与 child exchange widening 直接相关的 live/runtime
script or harness command。

## 必更新的真源

本轮最少更新：

- `phase45-request-aggregation-active-seam`
- 一份新的 child-exchange dependency truth / checkpoint
- `phase45-customer-runtime-evidence-ledger`
- `phase45-dominant-gap-reselection`
- 一份新的 coordinator checkpoint

## Out Of Scope

- governance
- host/baseline
- heavy-weight repeatability
- stream rewrite
- continuous batching
- benchmark / optimization / product story

## Final Output Format

Your final report must include:

- `Modified files`
- `Wave-by-wave outcomes`
- `Child-exchange widening introduced`
- `Live/runtime evidence`
- `Higher-level truth sync`
- `Tests run`
- `Remaining blockers before stream-path work`
- `Coordinator verdict`

