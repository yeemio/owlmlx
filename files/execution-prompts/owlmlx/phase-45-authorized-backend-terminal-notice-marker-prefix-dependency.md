# owlmlx Phase 45 - Authorized Backend Terminal Notice-Marker-Prefix Dependency

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

当前 cache 主线已经完成：

- pre-gate request-aggregation / cohort window 已 visible
- child exchange aggregated dispatch 已 visible
- cohort-to-child handoff 已 visible
- stream gate release 已从 outer consumer completion 缩窄到 backend-side boundary
- backend terminal-event delivery / terminal-payload commit /
  terminal-payload capture / terminal-record capture / terminal-record prefix
  detection / terminal-action discriminant detection / terminal-notice capture
  / terminal-notice prefix detection / terminal-notice action-discriminant
  detection / terminal-notice action-stem detection / terminal-notice marker
  detection 都已不是当前最接近真实的 active seam

当前 active seam 是：

- **backend_terminal_notice_marker_prefix_dependency**

## 第一性原则

- `active terminal-notice marker-prefix dependency > already-solved notice-marker seam`
- `preserve post-claim serial invariants > stream-path speed`
- `one exact backend-stream verdict > broad batching story`
- `non-stream cohort handoff remains earned checkpoint truth`
- `runtime-owned truth > speculative throughput narrative`

## 当前真实状态

### 已经成立的

- `selected_seam = backend_terminal_notice_marker_prefix_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_marker_prefix_detection`
- stream gate release remains decoupled from outer consumer drain
- a second backend stream can now start before the first iterator consumer
  receives the first stream's terminal event
- a second backend stream can now also start before the first terminal payload
  is committed to the first stream queue
- a second backend stream can now also start before the first terminal payload
  is decoded and captured
- a second backend stream request can now also enter the live backend exchange
  before the first terminal record is fully captured
- a second backend stream request can now also enter the live backend exchange
  before the first terminal-record prefix is fully matched
- a second backend stream request can now also enter the live backend exchange
  before the first terminal done payload reaches its action discriminant
- a second backend stream request can now also enter the live backend exchange
  before the first terminal-notice record is fully captured
- a second backend stream request can now also enter the live backend exchange
  before the first terminal-notice prefix is fully matched
- a second backend stream request can now also enter the live backend exchange
  before the first terminal-notice action discriminant is reached
- a second backend stream request can now also enter the live backend exchange
  before the first terminal-notice action stem is reached
- a second backend stream request can now also enter the live backend exchange
  before the first terminal-notice marker field is fully reached
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

- **在 non-stream 主链已经成立、notice-marker detection 已经不再是当前最接近真实的 blocker 的前提下，backend stream exchange 还能不能从 “terminal notice marker-prefix detection still owns the serial boundary” 这条 exact blocker 再缩一层，而不破坏 post-claim serial invariants，也不夸大成 interleaving / continuous batching？**

本轮最终只能给出两个裁决之一：

- `backend_terminal_notice_marker_prefix_dependency_narrowed`
- `backend_terminal_notice_marker_prefix_dependency_still_blocked`

如果仍 blocked，必须把 blocker 写得比当前更接近真实 backend-stream
boundary。

## 硬规则

- 只准处理 `backend_terminal_notice_marker_prefix_dependency`
- 不准顺手处理 interleaving / continuous batching / cache parity /
  governance / host / heavy-weight reopen
- 不能改变 post-claim `max_concurrent=1`、ticketed FIFO、serial safety
  boundary
- 不能把已经成立的 non-stream handoff truth 写回 blocked
- 如果创建或实质修订了 active seam truth / checkpoint / prompt，不要留在
  chat 或 untracked 状态里

## 必跑测试

- `python3 -m pytest tests/test_cache_stream_backend_terminal_event_harness.py tests/test_cache_stream_backend_terminal_event_exactness.py tests/test_cache_stream_backend_terminal_payload_commit_harness.py tests/test_cache_stream_backend_terminal_payload_commit_exactness.py tests/test_cache_stream_backend_terminal_payload_capture_harness.py tests/test_cache_stream_backend_terminal_payload_capture_exactness.py tests/test_cache_stream_backend_terminal_record_capture_harness.py tests/test_cache_stream_backend_terminal_record_capture_exactness.py tests/test_cache_stream_backend_terminal_record_prefix_harness.py tests/test_cache_stream_backend_terminal_record_prefix_exactness.py tests/test_cache_stream_backend_terminal_action_discriminant_harness.py tests/test_cache_stream_backend_terminal_action_discriminant_exactness.py tests/test_cache_stream_backend_terminal_notice_capture_harness.py tests/test_cache_stream_backend_terminal_notice_capture_exactness.py tests/test_cache_stream_backend_terminal_notice_prefix_harness.py tests/test_cache_stream_backend_terminal_notice_prefix_exactness.py tests/test_cache_stream_backend_terminal_notice_action_discriminant_harness.py tests/test_cache_stream_backend_terminal_notice_action_discriminant_exactness.py tests/test_cache_stream_backend_terminal_notice_action_stem_harness.py tests/test_cache_stream_backend_terminal_notice_action_stem_exactness.py tests/test_cache_stream_backend_terminal_notice_marker_harness.py tests/test_cache_stream_backend_terminal_notice_marker_exactness.py tests/test_cache_request_aggregation_active_seam.py tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py tests/test_runtime_kernel.py tests/test_serving_pre_gate_admission_hook.py -q`

另外必须跑并报告任何与 terminal-notice-marker-prefix narrowing 直接相关的
live/runtime harness。
