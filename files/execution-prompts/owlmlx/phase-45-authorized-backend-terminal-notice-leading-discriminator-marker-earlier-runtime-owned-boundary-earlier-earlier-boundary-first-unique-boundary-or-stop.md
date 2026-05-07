# owlmlx Phase 45 - Authorized: Earlier-Earlier-Boundary First-Unique-Boundary Freeze, or Stop

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

当前 active seam 是：

- `backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`

上一轮新增的诚实事实是：

- 一条 distinct earlier-earlier runtime-owned terminal record
  `runtime_owned_terminal_earlier_earlier_boundary` 已经存在于 existing
  earlier-boundary record 之前
- existing earlier-boundary trigger 已从共享前缀 `_e` 收紧为 `_earlier_b`
- 新 earlier-earlier trigger 是 `_earlier_e`
- second backend stream request 可以在 reach `runtime_owned_terminal_earlier_earlier_boundary`
  后、reach `runtime_owned_terminal_earlier_boundary` 前写出
- post-claim `max_concurrent=1` / ticketed FIFO / serial safety 仍保持

## 本轮目标（两选一）

A. 做 metadata-only first-unique-boundary 冻结：证明 earlier-earlier-boundary
   detection 已经是 newer earlier-earlier-boundary record 上的 first honest
   unique boundary（literal prefix before `runtime_owned_terminal_earlier_earlier_b`
   是与 earlier_boundary record 的 shared 前缀，所以不是 honest transport
   boundary）。这种纯文档/exactness 层 freeze 在本项目有 Apr 23 / 本轮 first-
   unique-boundary 两次先例，是合法 narrowing。

B. 做真实 backend 改动：再引入一条 distinct earlier-earlier-earlier
   runtime-owned terminal record（e.g. `runtime_owned_terminal_earlier_earlier_earlier_boundary`）
   位于 `runtime_owned_terminal_earlier_earlier_boundary` 之前。需要新 trigger
   `_earlier_earlier_e`、新 hook、新 harness。

如果两条都做不到，必须停在 `still_blocked` 并明确最窄 blocker。

## 硬规则

- 只准在当前 earlier-earlier-boundary seam 内部收窄
- 不准重开 MTP / Gemma assistant / reference comparison
- 不准扩成 stream interleaving、continuous batching、cache parity
- 不准重开 governance / host / heavy-weight
- 不能改变 post-claim `max_concurrent=1`、ticketed FIFO、serial safety
- 不准把 preserved secondary truth 重新说成 active seam
- 如果选择 A 但已经做过两轮同型 metadata freeze，要明确这是第三次同型操作并询问是否值得
- active truth / checkpoint / next prompt 不要留在 untracked 或只停在 chat

## 最小入口

先对齐这些 surfaces：

1. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-earlier-earlier-boundary-introduced.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-stream-backend-terminal-notice-leading-discriminator-marker-earlier-runtime-owned-boundary-earlier-earlier-boundary-exactness.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-request-aggregation-active-seam.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_lm_subprocess_backend.py`
5. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.py`
6. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.py`

## 第一组命令

```
git status -s
python3 -m pytest tests/test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.py tests/test_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_harness.py -q
python3 scripts/runtime_cache_stream_backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_exactness.py --run-harness | head -30
```

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`narrowed` 或 `still_blocked`
2. 选择的路径（A / B / 停）
3. 本轮 exact verdict
4. 本轮 active seam（应该仍然是 earlier_earlier_boundary_dependency 或被诚实推进的更深 seam）
5. 本轮 active status
6. 实际修改的文件
7. 实际运行的命令与关键结果
8. 如果没有成功收窄，明确唯一主 blocker 是什么
