# owlmlx Phase 45 - Authorized Backend Terminal Notice Leading-Discriminator Prefix Dependency

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

当前 cache 主线已经完成：

- pre-gate request-aggregation / cohort window 已 visible
- child exchange aggregated dispatch 已 visible
- cohort-to-child handoff 已 visible
- stream gate release 已从 outer consumer completion 缩窄到 backend-side boundary
- terminal-notice marker-key lead 已冻结成旧 terminal-notice record 上的第一个唯一边界
- owlmlx 现在已经引入一个新的 runtime-owned terminal-notice leading-discriminator record

当前 active seam 是：

- **backend_terminal_notice_leading_discriminator_dependency**

## 第一性原则

- `active terminal-notice leading-discriminator dependency > old marker-key-lead boundary`
- `preserve post-claim serial invariants > stream-path speed`
- `one exact backend-stream verdict > broad batching story`
- `runtime-owned truth > speculative throughput narrative`

## 当前真实状态

### 已经成立的

- `selected_seam = backend_terminal_notice_leading_discriminator_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_detection`
- one runtime-owned terminal-notice leading-discriminator record now exists
  ahead of the old marker-key-lead seam
- a second backend stream request can now be written before child stdout
  reaches the first terminal-notice marker-key lead on the old notice record
- marker-key lead remains preserved as the first unique boundary on the old
  terminal-notice record
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

- **在 runtime-owned leading-discriminator record 已经成立、而旧 marker-key-lead 只作为 preserved secondary truth 的前提下，backend stream exchange 还能不能从 “terminal notice leading-discriminator detection still owns the serial boundary” 这条 exact blocker 再缩一层，而不破坏 post-claim serial invariants，也不夸大成 interleaving / continuous batching？**

本轮最终只能给出两个裁决之一：

- `backend_terminal_notice_leading_discriminator_dependency_narrowed`
- `backend_terminal_notice_leading_discriminator_dependency_still_blocked`

如果仍 blocked，必须把 blocker 写得比当前更接近真实 backend-stream
boundary。

## 硬规则

- 只准处理 `backend_terminal_notice_leading_discriminator_dependency`
- 不准顺手处理 interleaving / continuous batching / cache parity /
  governance / host / heavy-weight reopen
- 不能改变 post-claim `max_concurrent=1`、ticketed FIFO、serial safety
  boundary
- 不能把已经成立的 non-stream handoff truth 写回 blocked
- 如果创建或实质修订了 active seam truth / checkpoint / prompt，不要留在
  chat 或 untracked 状态里
