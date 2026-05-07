# owlmlx Phase 45 - GPT-5.4 Executor Prompt - Backend Terminal Notice Leading-Discriminator Marker Earlier Runtime-Owned Boundary Stem Dependency

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

本轮模型槽位是：

- `GPT-5.4`

## 工作目录

- `/Users/yeemio/AI/gitrep/owlmlx`

## 先读这些文件

1. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-packet-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-dependency.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-authorized-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-discriminant-dependency.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-narrowed.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-stem-exactness.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-active-seam.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_lm_subprocess_backend.py`
7. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_harness.py`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_exactness.py`

## 统筹约束

- 本 prompt 受当前 coordinator packet 约束。
- 不要自行改写本轮范围、模型分工或审核边界。

## 当前冻结 Truth

当前已冻结：

- `summary.verdict = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_prefix_dependency_narrowed`
- `selected_seam.seam = backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_dependency`
- `selected_seam.status = backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`

当前 harness 真相也已冻结：

- second request 是否早于 first terminal event consumed，必须在写出当刻判定
- 关键判定是写出时刻的 `not first_terminal_event_consumed.is_set()`
- 不能在线程 `join()` 之后再回看最终态并反推这一事实

## 本轮唯一目标

回答一个更窄的问题：

- `owlmlx` 能不能把当前 `earlier-runtime-owned boundary stem detection`
  再缩到同一条 runtime-owned boundary record 内部更早的 discriminant
  boundary，而不破坏 post-claim serial invariants，也不夸大成
  interleaving / continuous batching / cache parity？

## 硬规则

- 只准处理当前 `stem_dependency` 内部的 discriminant 缩窄。
- 不准顺手扩到 interleaving、continuous batching、cache parity、
  governance、host、heavy-weight reopen。
- 不能改变 post-claim `max_concurrent=1`、ticketed FIFO、serial safety
  boundary。
- 如果无法诚实收窄，就停在最窄真实 blocker，不要假装前推。
- 如果创建或实质修订了 active seam truth、checkpoint、next prompt，必须
  一起落盘，不要只留在聊天里，也不要留成 untracked。
- `runtime_customer_runtime_evidence.py --specimen-path /tmp/specimen --skip-governance-harness`
  如果运行，只能算 sanity run，不能抬成 dominant-gap truth。

## 实施要求

- 优先从当前 runtime-owned boundary record 内部继续缩窄，不要把叙述回退
  到 prefix 仍是 active seam。
- harness 必须继续用 second-request write-time snapshot 做判定。
- 任何“second request was written before first terminal event consumed”的
  结论，都必须来自写出时刻快照，而不是事后重建。
- 运行本轮对应的 exactness 或 harness operator，并复核 active seam
  operator 输出。
- 复用当前主线已经在用的 focused suite 与 broader seam or backend suite。
- 如果代码、truth、checkpoint、next prompt 其中一面变了，其余几面要一并
  对齐。

## 给审核者的交接产物

本轮结束后，至少要留下这些可审核产物：

- executor 最终结论
- 实际修改文件列表，或者明确的 no-code still-blocked 说明
- live verification 结果
- 实际运行命令
- 本轮 fresh exactness 或 active-seam 输出

不要让 reviewer 在没有这些产物的情况下开审。

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`narrowed` 或 `still_blocked`
2. 本轮 exact verdict
3. 本轮 active seam
4. 本轮 active status
5. 实际修改的文件
6. 实际运行的命令与关键结果
7. 如果没有成功收窄，明确剩余 blocker 是什么，并停在最窄诚实 seam
