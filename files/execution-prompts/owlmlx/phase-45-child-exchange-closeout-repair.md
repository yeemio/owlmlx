# owlmlx Phase 45 - Child-Exchange Closeout Repair

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

当前 round 的 seam shift 已经成立：

- `child_exchange_aggregated_dispatch_visible`
- active seam 已前推到：
  - `cohort_to_child_exchange_handoff_dependency`

但本轮还**不能 close out**，因为当前 targeted test bundle 在真实复跑下
不是全绿：

- `tests/test_serving_pre_gate_admission_hook.py::test_pre_gate_hook_exists_before_claim_without_reopening_post_claim_invariants`

失败点是：

- `second_result.was_queued` 期望为 `True`
- 实际返回为 `False`

这轮的唯一目标是：

- **把当前 seam shift 收干净**
- 明确 `was_queued` 在 pre-gate cohorting 下的语义
- 修实现或修测试/真源，但不能两头含糊

## 本轮不是

- 不是新一轮 handoff dependency widening
- 不是 stream round
- 不是 continuous batching round
- 不是 host / governance / heavy-weight round

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-child-exchange-aggregated-dispatch-exactness.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-active-seam.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-window-exactness.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime3-serving-surface.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/serving.py`
6. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_serving_pre_gate_admission_hook.py`
7. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_cache_child_exchange_aggregated_dispatch_exactness.py`
8. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_cache_request_aggregation_active_seam.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-child-exchange-aggregated-dispatch-visible.md`

读完后先输出不超过 10 行的修复计划，再动手。

## 硬规则

### 1. 不许回退 seam truth

本轮不能把已经成立的：

- `child_exchange_aggregated_dispatch_visible`

写回 blocked。

如果最终不得不回退，必须拿出比当前更硬的 runtime evidence，而不是只因
为单个测试失配就改写上层真相。

### 2. 明确 `was_queued` 语义

你必须二选一并冻结：

1. `was_queued` 继续表示 **任何进入 post-claim FIFO 等待** 的请求  
2. `was_queued` 在 pre-gate cohorting 之后只表示 **claim 后等待**

如果是第 2 种，必须更新测试和相关 truth 表达，不能只改实现。

### 3. 不许越界到 handoff

本轮不允许开始：

- `cohort_to_child_exchange_handoff_dependency`

这轮只能收当前 child-exchange round 的 closeout。

### 4. Active truth versioning

如果你修了当前 seam 的 active truth / checkpoint / tests，不要留在 chat
或 untracked 状态里。

## Wave Plan

- Wave 0: freeze the exact failure and current semantics conflict
- Wave 1: decide authoritative `was_queued` meaning under pre-gate cohorting
- Wave 2: implement the narrow repair
- Wave 3: rerun the same targeted test bundle
- Wave 4: sync truth/checkpoint if semantics wording changed
- Wave 5: close out with a clean verdict

## 必跑测试

至少跑并报告：

- `python3 -m pytest tests/test_mlx_lm_subprocess_backend.py tests/test_cache_child_exchange_aggregated_dispatch_harness.py tests/test_cache_child_exchange_aggregated_dispatch_exactness.py tests/test_cache_request_aggregation_window_exactness.py tests/test_cache_request_aggregation_active_seam.py tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py -q`

## Allowed Verdicts

- `child_exchange_closeout_repaired`
- `child_exchange_closeout_still_inconsistent`

## Final Output Format

Your final report must include:

- `Modified files`
- `Authoritative was_queued semantics`
- `Why implementation or tests changed`
- `Checks run`
- `Honest verdict`
