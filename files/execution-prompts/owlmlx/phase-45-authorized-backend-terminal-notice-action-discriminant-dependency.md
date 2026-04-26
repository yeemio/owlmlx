# owlmlx Phase 45 - Authorized Backend Terminal Notice-Action-Discriminant Dependency

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

当前 cache 主线已经完成：

- pre-gate request-aggregation / cohort window 已 visible
- child exchange aggregated dispatch 已 visible
- cohort-to-child handoff 已 visible
- stream gate release 已从 outer consumer completion 缩窄到 backend-side boundary
- backend terminal-event delivery 已不是当前最接近真实的 active seam
- backend terminal-payload commit 也已不是当前最接近真实的 active seam
- backend terminal-payload capture 也已不是当前最接近真实的 active seam
- backend terminal-record capture 也已不是当前最接近真实的 active seam
- backend terminal-record prefix detection 也已不是当前最接近真实的 active seam
- backend terminal-action discriminant detection 也已不是当前最接近真实的 active seam
- backend terminal-notice capture 也已不是当前最接近真实的 active seam
- backend terminal-notice prefix detection 也已不是当前最接近真实的 active seam

当前 active seam 是：

- **backend_terminal_notice_action_discriminant_dependency**

## 第一性原则

- `active terminal-notice action-discriminant dependency > already-solved notice-prefix seam`
- `preserve post-claim serial invariants > stream-path speed`
- `one exact backend-stream verdict > broad batching story`
- `non-stream cohort handoff remains earned checkpoint truth`
- `runtime-owned truth > speculative throughput narrative`

## 当前真实状态

### 已经成立的

- `selected_seam = backend_terminal_notice_action_discriminant_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_action_discriminant_detection`
- stream gate release remains decoupled from outer consumer drain
- a second backend stream can now start before the first iterator consumer
  receives the first stream's terminal event
- a second backend stream can also start before the first terminal payload is
  committed to the first stream queue
- a second backend stream can also start before the first terminal payload is
  decoded and captured
- a second backend stream request can now also enter the live backend exchange
  before the first terminal record is fully captured
- a second backend stream request can now also enter the live backend exchange
  before the first stream fully matches its terminal-record prefix on child
  stdout
- a second backend stream request can now also enter the live backend exchange
  before the first terminal done payload reaches its action discriminant on
  child stdout
- a second backend stream request can now also enter the live backend exchange
  before the first terminal-notice record is fully captured
- a second backend stream request can now also enter the live backend exchange
  before child stdout fully matches the first terminal-notice prefix
- `turboquant_preconditions = preconditions_exact`

### 当前不能宣称的

- stream interleaving exists
- continuous batching exists
- cache parity exists
- replacement-ready / customer-ready exists

### 必须继续冻结的 post-claim invariants

- `max_concurrent_1_after_gate_claim`
- `ticketed_fifo_after_gate_claim`
- `serial_safety_validated_only_after_gate_claim`

## 本轮唯一目标

回答一个更窄的问题：

- **在 non-stream 主链已经成立、consumer drain / terminal-event delivery /
  terminal-payload commit / terminal-payload capture / terminal-record capture /
  terminal-record prefix detection / terminal-action discriminant detection /
  terminal-notice capture / terminal-notice prefix detection 都已经不是当前
  最接近真实的 blocker 的前提下，backend stream exchange 还能不能从
  “terminal notice-action-discriminant detection still owns the serial
  boundary” 这条 exact blocker 再缩一层，而不破坏 post-claim serial
  invariants，也不夸大成 interleaving / continuous batching？**

本轮最终只能给出两个裁决之一：

- `backend_terminal_notice_action_discriminant_dependency_narrowed`
- `backend_terminal_notice_action_discriminant_dependency_still_blocked`

如果仍 blocked，必须把 blocker 写得比当前更接近真实 backend-stream
boundary。

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/replacement-grade-stability-gaps.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-active-seam.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-stream-backend-terminal-notice-capture-exactness.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-stream-backend-terminal-notice-prefix-exactness.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-dominant-gap-reselection.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-backend-terminal-notice-action-discriminant-narrowed.md`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_request_aggregation_active_seam.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_stream_backend_terminal_notice_prefix_exactness.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/customer_runtime_evidence.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_lm_subprocess_backend.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_lm_runner.py`
14. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_cache_stream_backend_terminal_notice_prefix_exactness.py`
15. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_cache_stream_backend_terminal_notice_prefix_harness.py`
16. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_cache_request_aggregation_active_seam.py`
17. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_customer_runtime_evidence.py`
18. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_dominant_gap_reselection.py`
19. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_runtime_kernel.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 硬规则

### 1. 依赖边界硬限制

这轮只准处理：

- `backend_terminal_notice_action_discriminant_dependency`

不准顺手处理：

- stream interleaving
- continuous batching
- cache parity
- governance / host / heavy-weight reopen
- unrelated scheduler branches

### 2. serial safety 硬限制

不能改变：

- post-claim `max_concurrent=1`
- post-claim ticketed FIFO
- serial safety boundary begins only after whole-request gate claim

### 3. 已成立的 non-stream truth 不许回退

不能把已经成立的：

- bounded pre-gate cohort window
- aggregated non-stream child exchange
- cohort-to-child handoff
- stream gate release decoupled from consumer drain
- second stream starts before first iterator consumer receives terminal event
- second stream starts before first terminal payload commit
- second stream starts before first terminal payload capture
- second stream request enters live backend exchange before first terminal
  record capture
- second stream request enters live backend exchange before first terminal
  record prefix is fully matched
- second stream request enters live backend exchange before first terminal
  done payload reaches its action discriminant
- second stream request enters live backend exchange before first terminal
  notice is fully captured
- second stream request enters live backend exchange before first terminal
  notice prefix is fully matched

写回 blocked。

### 4. truth 表达硬限制

必须分开写：

- non-stream request-aggregation truth
- current backend-stream terminal-notice-action-discriminant truth
- higher-level evidence sync

不准把 “terminal-notice-action-discriminant seam 缩小了一点” 写成
“stream interleaving / continuous batching 已成立”。

### 5. active truth versioning

如果这轮创建或实质修订了 active seam truth / checkpoint / prompt，
不要留在 chat 或 untracked 状态里。

## Wave Plan

- Wave 0: scope freeze
- Wave 1: backend terminal-notice action-discriminant exact dependency design
- Wave 2: narrow runtime implementation
- Wave 3: tests + live/runtime evidence
- Wave 4: truth sync
- Wave 5: checkpoint closeout

## 必跑测试

至少跑并报告：

- `python3 -m pytest tests/test_cache_stream_backend_terminal_event_harness.py tests/test_cache_stream_backend_terminal_event_exactness.py tests/test_cache_stream_backend_terminal_payload_commit_harness.py tests/test_cache_stream_backend_terminal_payload_commit_exactness.py tests/test_cache_stream_backend_terminal_payload_capture_harness.py tests/test_cache_stream_backend_terminal_payload_capture_exactness.py tests/test_cache_stream_backend_terminal_record_capture_harness.py tests/test_cache_stream_backend_terminal_record_capture_exactness.py tests/test_cache_stream_backend_terminal_record_prefix_harness.py tests/test_cache_stream_backend_terminal_record_prefix_exactness.py tests/test_cache_stream_backend_terminal_action_discriminant_harness.py tests/test_cache_stream_backend_terminal_action_discriminant_exactness.py tests/test_cache_stream_backend_terminal_notice_capture_harness.py tests/test_cache_stream_backend_terminal_notice_capture_exactness.py tests/test_cache_stream_backend_terminal_notice_prefix_harness.py tests/test_cache_stream_backend_terminal_notice_prefix_exactness.py tests/test_cache_request_aggregation_active_seam.py tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py -q`

另外必须跑并报告任何与 terminal-notice-action-discriminant narrowing
直接相关的 live/runtime script or harness command。

## 必更新的真源

本轮最少更新：

- `phase45-request-aggregation-active-seam`
- 一份新的 backend terminal-notice-action-discriminant exactness truth / checkpoint
- `phase45-customer-runtime-evidence-ledger`
- `phase45-dominant-gap-reselection`
- 一份新的 coordinator checkpoint

## Out Of Scope

- governance
- host/baseline
- heavy-weight repeatability
- continuous batching
- benchmark / optimization / product story
