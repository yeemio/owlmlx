# B · Design-Grade Spec — Prefill Chunking

> **Gate**: 方向 B — Prefill chunking 在 owlmlx serving 路径上落地
> **Layer**: design-grade, downstream of [`../07-perf-optimization-proposal-20260526.md`](../07-perf-optimization-proposal-20260526.md) §5 (方向 B), upstream of code-grade
> **Plan-grade source**: same plan-grade doc, architect-reviewed 2026-05-26; **order revised 2026-05-26** 把 B 提到 C → A 之前（C 在 hybrid 模型上撞 mlx-lm 上游 trim 阻塞，A 大概率受同源问题影响，B 是唯一不依赖 partial cache trim 的方向）
> **Status**: code-grade implementation + smoke evidence landed; B partial gate passed for parameter / progress plumbing; cross-chunk output consistency is diagnostic-only after mlx-lm numeric-path triage
> **Prerequisite**: F-1 plan + design + code-grade landed（✓）；本方向不依赖 C0/C1 算法工作，不依赖 B-1c §2 closure
> **Non-goal**: 不期望物理降低单请求 TTFT（owlmlx 单 worker 设计下，chunked prefill 的 vLLM-style "decode/prefill 交错"收益拿不到）；只承诺**streaming 进度可见性 + chunk-size 配置面 + 峰值内存可测**这三件可达的事

## 1. Purpose

mlx-lm 0.31.3 已经在内部做 chunked prefill（`prefill_step_size` 默认 2048）。owlmlx 当前**没有把这件事暴露给上层** —— 调用方既不能配置 chunk size，也看不到进度，也不知道分块对峰值内存的影响。

B 方向的 owlmlx 侧工作就是把 mlx-lm 已经提供的两个 building blocks 包出来：

```text
mlx-lm 已有：
  stream_generate(..., prefill_step_size=N, prompt_progress_callback=cb)

owlmlx 需要做：
  1. 让调用方通过 per-request 参数或环境变量控制 prefill_step_size
  2. 接住 callback 把进度作为 stream event 吐出来
  3. 测不同 chunk size 对 TTFT / 峰值内存 / 数值稳定性的影响
```

回答四个问题：

```text
Q1 把 chunk size 暴露成 per-request 参数后，调用方真能控制 mlx-lm 行为吗？
Q2 进度事件能正确穿越 child → parent → 上层吗？
Q3 不同 chunk size 在长上下文场景的 TTFT / 峰值内存有显著差异吗？
Q4 同一 `prefill_step_size` 在重复运行中是否 byte-for-byte deterministic？不同 `prefill_step_size` 之间若输出不同，是否属于 mlx-lm 已知的 deterministic numeric-path 差异？
```

## 2. Prerequisites

- mlx-lm 0.31.3（已用）的 `stream_generate` 接受 `prefill_step_size` + `prompt_progress_callback` kwargs（已验证）
- 主力模型可加载（已验证 2026-05-26 long-context-ladder bench）
- F-1 surface 已有（B 不消费 F-1，独立）
- 不依赖 B-1c §2 closure（不动 cache 模块）

## 3. Scope

### In scope

- `mlx_lm_runner.py`：把 `prefill_chunk_tokens` per-request 参数 → 透传到 mlx-lm 的 `prefill_step_size`
- `mlx_lm_runner.py`：仅在显式请求 chunk/progress（`prefill_chunk_tokens`、env fallback 或 explicit flag）且路径为 `stream_generate` / `stream_generate_messages` 时注册 `prompt_progress_callback`，回调里 emit `event: prefill_progress` 的 JSONL 事件
- `mlx_lm_subprocess_backend.py`：parent 端透传 `prefill_chunk_tokens` kwarg；stream parse child 的 `prefill_progress` 事件并 yield 为内部 `StreamEvent`
- 新环境变量 `OWLMLX_PREFILL_CHUNK_TOKENS`（默认 fallback）
- 新 workload runner `scripts/bench/prefill_chunk_compare.py`：对每个模型 × context 长度 × chunk size 测 TTFT / 峰值 RSS / 进度事件数
- 输出稳定性校验：同 prompt / 同 sampler / 同 chunk size 下重复运行必须 byte-for-byte 一致；不同 chunk size 之间的一致率只作为 diagnostic metric
- evidence 落在 `files/evidence/owlmlx/bench/prefill-chunking/`

### Explicit protocol boundary

当前 subprocess backend 的非 streaming `_exchange(...)` 是**单 payload 响应协议**：parent 写入请求后只读取第一条 JSON payload 作为结果。若 child 在 `generate` / `generate_messages` 非 stream 路径上先吐 `prefill_progress`，parent 会把 progress 当成最终响应，破坏现有协议。

因此 B 第一版只在 streaming 路径 emit progress，且必须显式启用，避免默认 stream 消费者突然多出事件类型。非 streaming 路径可以接受 `prefill_chunk_tokens` 并透传 `prefill_step_size`，但**不得**在本阶段输出 progress event；若未来要支持非 stream progress，必须先另起 protocol-extension design。

### Out of scope（明确**不**在 B 范围内）

- vLLM-style "decode/prefill 交错"调度（违反 `MAX_GENERATION_CONCURRENCY=1`）
- OpenAI / Anthropic SSE 协议扩展（progress 事件先只走 owlmlx 内部 channel + 工具 / OwlOps 端，不破 OpenAI client 兼容）
- 改 mlx-lm 内部 prefill 实现（用现成 API）
- 自动调优 chunk size（先暴露给调用方手动定，后续再考虑 adaptive）
- 跟 prompt cache 协同（方向 A 的事；A 暂停中）
- 跟 ngram speculative decoding 协同（方向 C 的事；C 暂停中）

## 4. Phase Definition + Gate Criteria

B 比 F-2 简单，**单一阶段，命名 `B_prefill_chunking_contract`**。

**Pass criteria**：

| 检查项 | 要求 |
|---|---|
| 参数透传 | 给 child 请求里加 `prefill_chunk_tokens: 1024`，child 应该用 1024 调 stream_generate；observable via debug log 或 progress event 间隔 |
| 进度事件 emission | streaming 长 prompt（≥ 8k tokens）触发 ≥ 2 个 `prefill_progress` 事件；事件的 `processed` 应递增、`total` 一致 |
| Within-chunk determinism | 同一 prompt / 同 sampler（temp=0）/ 同 chunk size 下重复运行，生成的 token 序列必须 byte-for-byte 一致（**100% 通过**） |
| Cross-chunk consistency | 同一 prompt / 同 sampler 在 chunk size [512, 2048, 8192] 之间的输出一致率必须记录；该字段为 diagnostic-only，不阻塞 B，因为 mlx-lm 不同 `prefill_step_size` 会走不同 deterministic numeric path |
| 默认行为不变 | 不传 `prefill_chunk_tokens` 时，行为与改造前一致（baseline 无回归，long_context_ladder.py 数字落在 ±5% 内） |
| 环境变量 fallback | `OWLMLX_PREFILL_CHUNK_TOKENS=4096` 不传 per-request 时生效；per-request 传入时覆盖 env |
| 峰值内存差异可测 | workload runner 能记录 `resource.getrusage` peak RSS per cell；小 chunk 对长上下文应表现出更低峰值（**不预设阈值**，记数据为主） |
| Hybrid 模型兼容 | 三个主力模型（Qwen 27B / Qwen 35B-A3B / Gemma 4 31B）都能在不同 chunk size 下成功生成；B 不依赖 partial cache trim，但兼容性必须由 workload 证明 |

**Evidence**：`files/evidence/owlmlx/bench/prefill-chunking/<ts>-prefill-chunk-compare.jsonl` + rollup

**Failure handling**：

- **参数透传失败**：child 收到参数但 stream_generate 没改行为 → 验证 mlx-lm 版本兼容；可能需要 kwargs 名转换
- **进度事件丢失**：child stdout 缓冲问题 → 检查 _emit + flush
- **非 stream 协议污染**：非 stream `generate` 先吐 progress → parent 单 payload `_exchange` 会误收；本阶段必须禁用非 stream progress
- **Within-chunk determinism 失败**：同一 chunk size 重复运行 hash 不一致 → 硬阻塞；这说明 wrapper 或 mlx-lm 路径存在非确定性，不能作为可配置面交付
- **Cross-chunk consistency 失败**：不同 chunk size 输出 hash 不一致 → 记录差异 token 位置 / preview / hash；若每个 chunk size 自身 deterministic，则按 mlx-lm deterministic numeric-path 差异处理，不阻塞 B
- **Baseline 回归 > 5%**：包装层引入 overhead → 优化或 revert

## 5. Workload Definition

复用现有 `scripts/bench/long_context_ladder.py` 的 prompt 构造逻辑（拼接 reference text 到目标 token 数）。新 workload runner 在它的基础上加 chunk size 维度：

```text
matrix: 3 models × 4 context lengths × 3 chunk sizes × N=3 runs = 108 cells
  models: qwen3.6-27b-4bit, gemma-4-31b-it-4bit, qwen3.6-35b-a3b-4bit
  context lengths: 4k, 16k, 32k, 64k
  chunk sizes: 512, 2048 (default), 8192
  output_tokens: 32 (短即可，本测重点是 prefill)
  runs: 3 each
```

省 128k 因为它在 long_context_ladder 已测过；本测重点是中长 context 上 chunk size 的影响。

## 6. Harness Changes

### 6.1 修改文件

- `owlmlx/runtime/mlx_lm_runner.py`：
  - 在 `_prepare_generation_params` 里识别 `prefill_chunk_tokens` 参数（或从 params 里 pop 出来用 `prefill_step_size` 名传给 mlx_lm）
  - 只在显式请求 chunk/progress 的 `stream_generate` / `stream_generate_messages` 调用前注册 `prompt_progress_callback`，回调里调 `_emit({"event": "prefill_progress", ...})`
  - 在 `generate` / `generate_messages` / `generate_batch` 非 streaming 调用中只透传 `prefill_step_size`，不注册 progress callback
- `owlmlx/runtime/mlx_lm_subprocess_backend.py`：
  - 在 `stream_generate` / `stream_generate_messages` / `generate` 等方法的 kwargs 透传里保留 `prefill_chunk_tokens`
  - parse child stream 时识别 `prefill_progress` 事件并 yield 内部 `StreamEvent(event="prefill_progress", detail=...)`
  - 不修改非 stream `_exchange` 为多 payload 协议

### 6.2 新文件

- `scripts/bench/prefill_chunk_compare.py`：workload runner

### 6.3 Forbidden edits

B 任何一段都**不得**触动：

- `owlmlx/session_kv_cache.py` / `cache_manager.py` / `scheduler_admission.py` / `memory_*` (Track 1 owns)
- `owlmlx/speculative/` (F-2 owns, 已 paused)
- `owlmlx/runtime/speculative_execution_status.py` (F-1 owns, 已稳定)
- F-1 surface 字段名（不新增、不改）

## 7. Evidence

### 7.1 落点

```text
files/evidence/owlmlx/bench/prefill-chunking/
  <ts>-prefill-chunk-compare.jsonl
  <ts>-prefill-chunk-compare-rollup.jsonl
```

### 7.2 Per-cell schema

```yaml
schema_version: b.prefill_chunk.cell.v1
gate: B
run_id: <ts>-prefill-chunk-compare
host: <hw.model>
model_id: qwen3.6-27b-4bit | gemma-4-31b-it-4bit | qwen3.6-35b-a3b-4bit
target_input_tokens: 4096 | 16384 | 32768 | 65536
actual_input_tokens: <int>
chunk_size: 512 | 2048 | 8192
run_idx: 1..3
metrics:
  ttft_ms: <float>
  decode_tps: <float>
  wall_ms: <float>
  prompt_tokens: <int>
  completion_tokens: <int>
  peak_rss_gb_process_lifetime: <float>
  prefill_progress_event_count: <int>
output_byte_hash: <sha256 of completed text>  # for determinism / consistency checks
output_byte_length: <int>
output_text_preview: <short diagnostic prefix, optional>
verdict: pass | fail
```

### 7.3 Rollup schema

```yaml
schema_version: b.prefill_chunk.rollup.v1
gate: B
run_id: <ts>-prefill-chunk-compare
cell_count: 108
ok_cells: <int>
failed_cells: <int>
within_chunk_determinism:
  gate: required
  status: passed | failed | not_measured
  total_groups: <int>                    # = models × context × chunk size
  groups_with_repeated_runs: <int>
  repeated_groups_with_identical_output: <int>
  repeat_match_rate: <float | null>      # repeated groups must be 1.0 to pass
cross_chunk_consistency:
  gate: informational_only
  total_groups: <int>                    # = models × context × runs
  groups_with_identical_output: <int>
  match_rate: <float | null>             # recorded, not a B gate
ttft_chunked_vs_default:
  per_model_per_length: ...     # min/median/max for each chunk size
peak_rss_chunked_vs_default:
  per_model_per_length: ...
baseline_regression_long_context_ladder:
  delta_pct: <float>             # 跟 2026-05-26 baseline 比，必须 ±5% 内
graduates:
  chunk_param_exposed: true | false
  progress_events_observable: true | false | null
  within_chunk_determinism_holds: true | false | null
  cross_chunk_consistency_holds: true | false | null
  baseline_no_regression: true | false
```

## 8. Failure Handling（per pass criterion，§4 表里已细化）

跨阶段共通规则：

- 任何 failure 记录到 evidence，verdict 标 `failed` + `blocker_summary`
- baseline 回归 > 5%：硬阻塞，不允许 land
- within-chunk determinism 失败：硬阻塞，回退实现或升级为 mlx-lm determinism blocker
- cross-chunk consistency 失败但每个 chunk size 自身 deterministic：记录差异分布，不阻塞 B；如果差异不是 mlx-lm 已知 numeric-path 范畴，再升级为 triage blocker

## 9. Out-of-scope reminders

- 不做 vLLM-style decode/prefill 交错（违反单 worker 边界）
- 不破 OpenAI / Anthropic SSE 协议
- 不动 mlx-lm 内部 prefill 实现
- 不做 adaptive chunk size 自动调优
- 不接 OwlOps 可视化（独立 round）
- 不证明任何能力升 `supported`（promotion 走独立 §1a Gate）

## 10. Status / Next Step

- **Current**：code-grade implementation + smoke + half workload evidence landed; B partial gate passed for configuration surface, streaming progress visibility, and within-chunk determinism across 3 models / 3 lengths / 3 chunks / 2 runs
- **On approval**：
  - code-grade session 已实装 §6.1 / §6.2 改动 + 写 §5 workload runner，已落 smoke evidence
  - smoke 已证明 chunk 参数和 progress event 可工作；determinism smoke `20260526T084239Z-prefill-chunk-determinism-smoke` 证明同一 chunk size 重复运行 hash 一致，不同 chunk size 之间是 deterministic numeric-path 差异
  - half workload `20260526T090253Z-prefill-chunk-half-50m` completed 54/54 cells in 1720.072s with `within_chunk_determinism.status=passed`, `progress_events_observable=true`, and no failed cells
  - 64k supplement `20260526T133018Z-prefill-chunk-64k-supplement` recorded Qwen 27B run-1 across chunks 512/2048/8192: 3/3 pass, progress observable, cross-chunk consistency 1.0, TTFT 563-605s. It was stopped after run-1 because Qwen 27B 64k is a 9-10 minute-per-cell workload on this host; N=2 determinism is not measured in that partial
  - Qwen 35B-A3B targeted 64k `20260526T140719Z-prefill-chunk-qwen35-64k-targeted` completed 6/6 cells in 938.612s; within-chunk determinism and cross-chunk consistency both passed, with median TTFT 173.63s / 144.21s / 147.08s for chunks 512 / 2048 / 8192
  - Gemma 4 31B targeted 64k `20260526T142420Z-prefill-chunk-gemma31-64k-targeted` completed 6/6 cells in 1277.599s; within-chunk determinism and cross-chunk consistency both passed, with median TTFT 228.54s / 185.47s / 219.58s for chunks 512 / 2048 / 8192
  - 下一步是给 Qwen 27B 64k 补 N=2 determinism，或直接将 B partial 定性为 4k/16k/32k full clean + 64k targeted clean except Qwen27 repeat pending；cross-chunk consistency 继续记录但不作为 pass/fail
- **Re-open of A / C**：等 mlx-lm 修 issue #980 (hybrid cache trim) 后重新评估

### 10.1 Hand-off 纪律

按 [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Part VIII.3：plan-grade → 用户复核 → 修订定版 → design-grade → 复核 → 代码。本 design-grade 不包含 code-grade 所需的：

- 具体函数签名
- per-request 参数命名最终决定（候选：`prefill_chunk_tokens` vs `prefill_step_tokens` vs `prefill_chunk_size`，code-grade 定）
- progress event 字段命名（候选见 §7.2，code-grade 定最终序列化）

## 11. References

- Plan-grade source：[`../07-perf-optimization-proposal-20260526.md`](../07-perf-optimization-proposal-20260526.md) §5
- mlx-lm `generate_step` signature with `prefill_step_size` + `prompt_progress_callback`：`.venv/lib/python3.11/site-packages/mlx_lm/generate.py` line 307-348
- mlx-lm `_prefill` 内部循环：line 581+
- 现有 long-context baseline：`files/evidence/owlmlx/bench/long-context-ladder/20260526T013407Z-long-context-ladder.jsonl`
- 现有 long-context bench script：`scripts/bench/long_context_ladder.py`（被复用 prompt 构造逻辑）
- C1 canary 发现的 mlx-lm batched-vs-split 数值漂移：`docs/architect/design/F-2-ngram-suffix-spec.md` §4.2 change log
- B determinism smoke：`files/evidence/owlmlx/bench/prefill-chunking/20260526T084239Z-prefill-chunk-determinism-smoke-rollup.jsonl`
- B half workload：`files/evidence/owlmlx/bench/prefill-chunking/20260526T090253Z-prefill-chunk-half-50m-rollup.jsonl`
- B 64k partial：`files/evidence/owlmlx/bench/prefill-chunking/20260526T133018Z-prefill-chunk-64k-supplement-rollup.jsonl`
- B Qwen35 64k targeted：`files/evidence/owlmlx/bench/prefill-chunking/20260526T140719Z-prefill-chunk-qwen35-64k-targeted-rollup.jsonl`
- B Gemma 64k targeted：`files/evidence/owlmlx/bench/prefill-chunking/20260526T142420Z-prefill-chunk-gemma31-64k-targeted-rollup.jsonl`
- F-1 surface（B 不消费）：[`F-1-spec.md`](F-1-spec.md)

## 12. Change Log

| Date | 变更 | By |
|---|---|---|
| 2026-05-26 | design-grade 初稿；plan §5 derive；mlx-lm 已提供 `prefill_step_size` + `prompt_progress_callback`，owlmlx 侧工作是 expose + callback emit + workload；不依赖 trim，但 hybrid 兼容性仍由 workload gate 判定 | architect session（B kickoff round） |
| 2026-05-26 | review amend：progress event scope 收紧到显式启用的 streaming 路径，避免污染 subprocess 非 stream 单 payload `_exchange` 和默认 stream 消费者；移除 "100% 兼容" 预设结论 | codex quality gate |
| 2026-05-26 | code-grade smoke：Qwen 27B 4bit / 4k prompt / chunks 512 vs 2048 均 pass generation + progress events，但 cross-chunk consistency match_rate=0.0；进入 numeric-path triage | codex code-grade |
| 2026-05-26 | gate 修订：determinism smoke 证明同一 chunk size 重复运行 byte-for-byte deterministic（repeat_match_rate=1.0），跨 chunk divergence 是 mlx-lm 不同 `prefill_step_size` 的 deterministic numeric-path 行为；B gate 改为 within-chunk determinism required，cross-chunk consistency diagnostic-only | codex quality gate |
| 2026-05-26 | half workload：3 models × 3 lengths (4k/16k/32k) × 3 chunks × 2 runs = 54 cells；54/54 pass，elapsed=1720.072s，within_chunk_determinism passed (27/27 repeated groups)，progress_events_observable=true，cross_chunk_consistency match_rate=0.666667 informational-only | codex half workload |
| 2026-05-26 | 64k supplement partial：Qwen 27B 64k run-1 chunks 512/2048/8192 all pass，TTFT 591.8s / 563.7s / 605.4s，progress events 130 / 34 / 10，cross-chunk consistency 1.0；stopped after run-1 because the cell cost is 9-10 min and N=2 determinism was not measured | codex 64k triage |
| 2026-05-26 | Qwen 35B-A3B 64k targeted：6/6 cells pass，elapsed=938.612s，within-chunk determinism passed，cross-chunk consistency 1.0，median TTFT 173.63s / 144.21s / 147.08s for chunks 512 / 2048 / 8192 | codex 64k targeted |
| 2026-05-26 | Gemma 4 31B 64k targeted：6/6 cells pass，elapsed=1277.599s，within-chunk determinism passed，cross-chunk consistency 1.0，median TTFT 228.54s / 185.47s / 219.58s for chunks 512 / 2048 / 8192 | codex 64k targeted |
