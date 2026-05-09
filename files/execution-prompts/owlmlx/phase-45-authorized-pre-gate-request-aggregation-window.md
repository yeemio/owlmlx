# owlmlx Phase 45 - Authorized Pre-Gate Request-Aggregation Window

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

coordinator 已经明确做出选择：

- 不冻结在 `pre_gate_admission_window_seam_exact`
- 授权一轮**窄口 runtime work**
- 目标是把现有的 bounded pre-gate hook，从 inert seam 推进成真实的
  cohort / request-aggregation window

这轮**不是**：

- 再做 cache truth-only 微分解
- 重开 host / baseline / heavy-weight 分支
- 重开 governance
- 宣称 continuous batching / cache parity / replacement-ready

## 第一性原则

- `runtime-owned pre-gate window > inert bounded hook`
- `preserve post-claim serial invariants > widening speed`
- `one exact request-aggregation window > broad batching narrative`
- `default live harness truth > speculative architectural story`
- `narrow runtime widening > branch sprawl`

## 当前真实状态

### 已经成立的

- supported-host branch 已冻结在：
  - `supported_host_repeatability_visible`
- active dominant gap 已切到：
  - `cache_scheduler_depth`
- active cache surface 已经不是旧的 structural seam，而是：
  - `owlmlx.cache_pre_gate_admission_window_seam`
- 当前 live cache truth：
  - `closure_level = pre_gate_admission_window_seam_exact`
  - `selected_seam = bounded_pre_gate_admission_hook`
  - `selected_seam.status = bounded_hook_present_but_no_request_aggregation_window`

One stale-truth cleanup is also required before or during this round:

- some non-active fallback rationale strings in
  `owlmlx/dominant_gap_reselection.py`
  still talk as if cache were frozen at the old structural ingress seam
- current active cache truth has already moved beyond that checkpoint
- do not leave those stale fallback strings behind while widening the active
  seam further

### 当前不能宣称的

- request aggregation support
- continuous batching support
- aggregated child dispatch
- stream-path rewrite
- cache parity
- replacement-ready / customer-ready runtime

### 当前必须保持冻结的后 claim 不变量

- `max_concurrent_1_after_gate_claim`
- `ticketed_fifo_after_gate_claim`
- `serial_safety_validated_only_after_gate_claim`

## 本轮唯一目标

回答一个更窄的问题：

- **当前已经存在的 bounded pre-gate hook，能不能被推进成一个真实的 runtime-owned request-aggregation / cohort window，同时不破坏 post-claim serial invariants？**

本轮最终只能给出两个裁决之一：

- `request_aggregation_window_visible`
- `pre_gate_window_widening_still_blocked`

如果仍 blocked，必须把 blocker 写得比现在更靠近真实 runtime seam，
而不是回退到 “hook 不存在”。

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/replacement-grade-stability-gaps.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-cache-pre-gate-admission-window-seam.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-pre-gate-admission-hook-exactness.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-post-structural-pre-gate-window.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_pre_gate_admission_window_seam.py`
7. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_pre_gate_admission_hook_exactness.py`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_request_aggregation_window_exactness.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_request_aggregation_active_seam.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/customer_runtime_evidence.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/dominant_gap_reselection.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_cache_pre_gate_admission_hook_exactness.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_cache_pre_gate_admission_window_seam.py`
14. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_cache_request_aggregation_window_exactness.py`
15. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_customer_runtime_evidence.py`
16. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_dominant_gap_reselection.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 硬规则

### 1. widening 边界硬限制

这轮只准做：

- 在现有 bounded pre-gate hook 之上，引入真实 cohort / request-aggregation
  window 所需的**最小 runtime-owned widening**

不准做：

- child exchange parallelism
- aggregated dispatch beyond the window
- stream-path rewrite
- interleaved decode
- continuous batching productization
- cache parity 叙事

### 2. serial safety 硬限制

这轮不能改变：

- post-claim `max_concurrent=1`
- post-claim ticketed FIFO
- serial safety validated boundary begins only after whole-request gate claim

如果你的实现需要触碰这些，直接停并收成 blocked。

### 3. truth 表达硬限制

必须分开写：

- existing bounded hook truth
- newly introduced window truth
- preserved secondary blockers
- higher-level evidence sync

不准把 window 可见、aggregated child dispatch、stream release 混成一句
“request aggregation 打通了”。

### 4. contract surface 硬限制

如果你引入新的 runtime-owned surface，它必须：

- 明确 scope 是 pre-gate request-aggregation / cohort window
- 不改写已冻结的 supported-host proof truth
- 不让 `customer_runtime_evidence` 跳出 `early_formal_runtime`

### 5. live evidence 硬限制

这轮必须给出至少一条 live harness / script 证据，证明：

- 不是只有 inert hook
- 而是窗口语义真的可见

如果做不到 live visible，只能收成：

- `pre_gate_window_widening_still_blocked`

### 6. frozen branch 硬限制

这轮不允许：

- 重开 governance
- 重开 host/baseline
- 重开 heavy-weight
- 回退到 structural ingress seam
- 把 old blocker 重写成 “no bounded hook exists”

### 7. Active Truth Must Be Versioned

If this round creates or materially revises any active cache truth,
checkpoint, or execution material, do not leave it only in chat or as
untracked files.

Before closeout, add any newly-created or newly-active files to version
control, especially:

- cache source-of-truth docs
- new checkpoint prompts
- current active execution prompt revisions
- any new active request-aggregation/cohort truth surface referenced by the
  final verdict

If a file remains intentionally untracked, call it out explicitly in the final
report and explain why it is not required for the active path.

## 预计时长与 Wave 规划

- Wave 0: scope freeze
- Wave 1: exact runtime widening design
- Wave 2: narrow implementation
- Wave 3: tests + live harness
- Wave 4: truth sync
- Wave 5: checkpoint closeout

## Wave 0: Scope Freeze

目标：
- 把本轮 widening 边界写死

必做：
- 记录当前 exact blocker
- 记录 preserved post-claim invariants
- 明确 secondary blockers 仍然是 secondary
- 清掉与当前 active cache truth 冲突的 stale structural-ingress wording
  （至少包括 non-active fallback rationale，不要求重写整个 branch
  history）

验收：
- 本轮不会漂移成 broader batching round

## Wave 1: Exact Runtime Widening Design

目标：
- 把“真实 request-aggregation window”在当前 path 上的最小语义写清

必做：
- 明确：
  - cohort candidacy 在哪里形成
  - 这个 window 拥有什么，不拥有什么
  - 哪些状态仍是 observational-only
  - 哪个点以前仍然进入 whole-request gate claim
- 如果需要新增或改造 surface：
  - 先把 contract sections 和 blocker vocabulary 定准

验收：
- widening target exact enough to implement without reopening old branches

## Wave 2: Narrow Implementation

目标：
- 在 runtime path 上引入最小可见 window 语义

必做：
- 实现最窄的 runtime-owned widening
- 让它能和现有 bounded hook 正确组合
- 不触碰 post-claim serial invariants
- 如果现有 `cache_request_aggregation_window_exactness` /
  `cache_pre_gate_admission_window_seam` / 邻接 surface 需要同步，
  只改这一条链的最小必要部分

验收：
- runtime path is no longer limited to an inert hook only
  或 exact blocked reason is narrower than before

## Wave 3: Tests + Live Harness

目标：
- 把 widening 变成可验证 truth，而不是代码猜想

必做：
- 补 focused tests
- 至少补/改：
  - exactness tests
  - seam tests
  - `customer_runtime_evidence` / `dominant_gap_reselection` carriage tests
- 跑 live script / harness，证明：
  - window visible or exact blocked

验收：
- test truth + live truth agree

## Wave 4: Truth Sync

目标：
- 让上层 truth honest 地吃到这轮 widening 结果

必做：
- 更新：
  - `phase45-cache-pre-gate-admission-window-seam`
  - 必要时新的 request-aggregation window/cohort truth 文档
  - `phase45-customer-runtime-evidence-ledger`
  - `phase45-dominant-gap-reselection`
  - `replacement-grade-stability-gaps`
  - `replacement-grade-stability-alignment-goal-contract`
  - `master-outline`
- 如果 blocked，写 exact blocker，不准回退成旧 blocker

验收：
- dominant cache truth matches live implementation exactly

## Wave 5: Checkpoint Closeout

目标：
- 收口，不越级宣称 broader batching 成立

必做：
- 新增一个 coordinator checkpoint
- 只回答：
  - request-aggregation window 是否已经可见
  - 如果已可见，下一 dominant blocker 是什么
  - 如果仍 blocked，exact blocker 是什么

验收：
- coordinator can choose the next cache move without redoing this round

## 必跑测试

至少跑并报告：

- `python3 -m pytest tests/test_cache_pre_gate_admission_hook_exactness.py tests/test_cache_pre_gate_admission_window_seam.py tests/test_cache_request_aggregation_window_exactness.py tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q`

如果新增 runtime-owned surface，对应测试必须一起补上。

另外必须跑并报告：

- `python3 scripts/runtime_cache_pre_gate_admission_hook_exactness.py --run-harness`
- `python3 scripts/runtime_cache_pre_gate_admission_window_seam.py`
- `python3 scripts/runtime_cache_request_aggregation_window_exactness.py --run-harness`
- `python3 scripts/runtime_customer_runtime_evidence.py --include-known-venvs --supported-host-proof-visible --supported-host-repeat-runs 2`
- `python3 scripts/runtime_dominant_gap_reselection.py --include-known-venvs --supported-host-proof-visible --supported-host-repeat-runs 2`

## 必更新的真源

本轮最少更新：

- `phase45-cache-pre-gate-admission-window-seam`
- 一份新的 request-aggregation window / cohort checkpoint 或真源
- `phase45-customer-runtime-evidence-ledger`
- `phase45-dominant-gap-reselection`
- 一份新的 coordinator checkpoint

## Out Of Scope

- governance
- host/baseline
- heavy-weight repeatability
- child exchange parallelism
- stream-path rewrite
- continuous batching parity
- benchmark / optimization / product story

## 最终输出格式

你的最终汇报必须包含：

- `Modified files`
- `Wave-by-wave outcomes`
- `Runtime widening introduced`
- `Live harness results`
- `Higher-level truth sync`
- `Tests run`
- `Remaining blockers before broader cache widening`
- `Coordinator verdict`

## Commit Message

`owlmlx: widen bounded pre-gate hook into request-aggregation window`
