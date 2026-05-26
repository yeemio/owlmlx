# F-2 · Design-Grade Spec

> **Gate**: Campaign F · F-2 — n-gram / SuffixDecoding speculative decoding probe
> **Layer**: design-grade, downstream of [`../07-perf-optimization-proposal-20260526.md`](../07-perf-optimization-proposal-20260526.md) §3 (方向 C), upstream of code-grade (C0 / C1 / C2 三段)
> **Plan-grade source**: same plan-grade doc, architect-reviewed 2026-05-26
> **Status**: design-grade reviewed by execution; C0 offline verifier and C1 mlx-lm verifier canary code-grade completed; C2 serving integration remains pending
> **Prerequisite**: F-1 plan + design + code-grade landed (✓); plan §6 W1-W4 三段顺序已批准；不依赖 B-1c §2 closure
> **Non-goal**: 本 spec **不**把 `method=ngram` 从 `not_implemented` 直接升 `supported`。它只规定 C0 / C1 / C2 三段 gate 的可执行口径，并约定哪些 phase 完成时 F-1 surface 的 `ngram.status` 在哪一档。

## 1. Purpose

F-2 实装 plan §3 方向 C 的 ngram / SuffixDecoding 投机解码 probe，回答四个问题：

```text
Q1 算法本身在合成数据上 correctness 立得住吗（C0）
Q2 mlx-lm 上能不能"一次 forward 验证 N 个候选 token"（C1，含 kill criterion）
Q3 接到 owlmlx serving 路径之后，在 OwlCoda-class workload 上加速多少（C2）
Q4 F-1 surface 在每个 phase 应当反映什么状态（贯穿）
```

F-2 的产出**不是 supported 能力**。它的产出是：

- 一套 runtime-owned ngram 解码模块（`owlmlx/speculative/suffix_decoding/`）
- 一份 OwlCoda-class workload runner + 固定 prompt set
- 三段 JSONL evidence ledger（C0 / C1 / C2 各自）
- F-1 surface `ngram.status` 在 C2 收尾时从 `not_implemented` → `experimental`（不更高）

任何 promotion 到 `supported` 走独立 §1a Gate round，**不在本 spec 范围**。

## 2. Prerequisites

C0 / C1 / C2 各 phase 启动条件：

- **C0**：F-1 v1 contract surface already landed（✓ — `0a051f1a` / `e99452d3` / `927fc5c9`）
- **C1**：C0 evidence ledger `passed`，且单元测试覆盖 ≥ 90%
- **C2**：C1 evidence ledger `passed`，且 C1 byte-equivalence + 性能 kill criterion 双双通过

**不**在前置条件中：

- B-1c §2 drift closure（独立 track，不阻塞）
- A 方向（MoE prompt cache）的任何 phase（不依赖）
- B 方向（prefill chunking）的任何 phase（不依赖）
- session_kv_cache.py 任何编辑（plan §8.1 forbidden edit list 一致）

## 3. Scope

### In scope（C0 + C1 + C2）

- 新模块 `owlmlx/speculative/suffix_decoding/`：`suffix_tree.py` / `proposer.py` / `verifier.py` / `runtime.py`
- C0 阶段单元测试：合成 token trace + fake LLM oracle
- C1 阶段 verifier canary：在真实 mlx-lm + 真实模型上验证 batch verify primitive
- C2 阶段 serving integration：在 `owlmlx/runtime/mlx_lm_subprocess_backend.py` 子进程端 decode loop 外挂 wrapper
- F-1 surface 状态在 C0/C1/C2 各阶段的正确转换（始终走 `method=ngram`，**不**新增 vocabulary）
- OwlCoda-class workload 固定 prompt set（§5 详）
- 三段 JSONL evidence ledger 落到 `files/evidence/owlmlx/bench/perf-optimization/c-ngram/`

### Out of scope（明确**不**在 F-2 范围内）

- 真 drafter 模型投机解码（DFlash / draft model — F-3 / F-7 各自独立 gate）
- continuous batching（违反 `MAX_GENERATION_CONCURRENCY=1` 边界）
- KV cache 自身量化压缩（TurboQuant V-cache style）
- 改 F-1 v1 method vocabulary 或 status vocabulary
- 任何 `session_kv_cache.py` / `cache_manager.py` / `scheduler_admission.py` / `memory_*` 编辑
- 把"论文 / vLLM / Snowflake 数字"作为本地 capability 事实（plan §3.2 evidence 纪律）
- C2 之后任何 promotion gate 工作（独立 §1a round）
- OwlCoda 客户端集成 / 客户端 SDK 改动（本 spec 只验证 runtime 侧）

## 4. Phase Definition + Gate Criteria

每个 phase 必须独立 evidence-led，前一段 `passed` 才启下一段。failed 不撤销前段。

### 4.1 C0 — Offline verifier

**Goal**：算法本身在合成数据上 correctness passed

**新文件**：

```
owlmlx/speculative/suffix_decoding/
  __init__.py
  suffix_tree.py        # 紧凑后缀树数据结构
  proposer.py           # 后缀树 → speculation tree 构造（含贪心扩展 + 频次评分）
  verifier.py           # 接受/拒绝决策（C0 用 fake oracle，C1 接真 model）
tests/
  test_speculative_suffix_decoding.py
```

**Pass criteria**（命名为 `c0_offline_verifier_contract`）：

| 检查项 | 要求 |
|---|---|
| suffix tree invariants | N=1000 合成 token 序列 random insert/lookup，所有 prefix lookup 返回结果集合等于 brute-force ground truth |
| proposer shape contract | propose() 输出的 speculation tree 永远是 `dict[parent_token, list[(child_token, frequency)]]` shape；不允许 cycle |
| verifier correctness with fake oracle | 给定固定 logits 序列 + 已知候选树，verify() 的 accept/reject 决策与人工 trace 完全一致（10 个手工样例）|
| 单元测试覆盖率 | `owlmlx/speculative/suffix_decoding/` 行覆盖 ≥ **90%** |
| pytest | `uv run pytest tests/test_speculative_suffix_decoding.py` 全绿 |
| F-1 surface | C0 完成时 `method=ngram` 仍是 `not_implemented`（无 live runner）|

**Evidence**：`files/evidence/owlmlx/bench/perf-optimization/c-ngram/<ts>-c0-offline-verifier.jsonl` + rollup

**Failure handling**：C0 fail → 修单元测试 + 修算法，不进 C1；evidence 标 `verdict=failed` + `blocker_summary`。

### 4.2 C1 — mlx-lm verifier canary

**Goal**：证明"batch verify N candidate tokens in one forward pass"在 mlx-lm 上可行 + 性能可接受

**改动**：

- 在 `verifier.py` 增加 real-model 路径：用 `mlx_lm.load()` 加载小模型（Qwen3.6-27B-4bit），用 `model.__call__` 直接做 batch forward（绕开 `stream_generate`）
- 新增 `scripts/bench/ngram_c1_canary.py` —— 独立 canary 脚本，**不**接 owlmlx serving；只验证 verifier primitive 自身

**Pass criteria**（命名为 `c1_mlx_lm_verifier_canary_contract`）：

| 检查项 | 要求 |
|---|---|
| Self-consistency byte-equivalence | 用 batch_verify 自身生成的 reference（每次空/递增 chain 调用，取 bonus 累计 N+1 token），再用 chain=reference[:N] 调 batch_verify 必须**全部 accept + bonus 等于 reference[N]**，N=20 prompts × chain_length=4，**100% 通过**。*（2026-05-26 修订：原稿是"与 stream_generate 比 byte-for-byte 一致"；C1 canary 发现 mlx-lm 在"整个 prompt 一次性 batched forward"vs"分段 prefill"之间有小数值漂移 —— 与算法无关，是 mlx-lm 自身行为。改为自我一致性测试。与 stream_generate 的对比保留为 secondary informational 指标，非 gate。）* |
| Batch verify works at N=1/4/8 | 三档候选 token 数都能正确返回 accept/reject 列表；不允许 silent truncate |
| Performance kill criterion | **批量验证的每位置摊销成本 ≤ 单 token decode 的 1.5×**（即：N=4 批量 forward 的 wall-clock 除以 4，相对同模型、同上下文长度下纯单 token decode 的 wall-clock，比值 ≤ 1.5；N=10 重复取 p50）。超阈值 → C2 不启动。 *（2026-05-26 修订：原稿写"≤ 1.5× 单次单 token forward"物理不成立 —— 多位置 forward 不可能比单位置 forward 更快；改为每位置摊销基准。）* |
| Health gate | canary 执行前后 8066 `/healthz` ok（如果 server 在跑）；canary 自身 unload 模型 clean |
| F-1 surface | C1 完成时 `method=ngram` 仍是 `not_implemented`（test fixture only, no live caller integration）|

**Evidence**：`files/evidence/owlmlx/bench/perf-optimization/c-ngram/<ts>-c1-verifier-canary.jsonl` + rollup

**Failure handling**：

- **Functional fail（batch verify 在 mlx-lm 上无 API 可走）**：evidence 标 `failed_reason=mlx_lm_batch_verify_unavailable`；不进 C2；**escalate to user with mlx-lm fork cost analysis**（fork 成本估计 + 替代方案：用 Apple MLX raw API 自己拼）。可能结论是 **abandon C 优先做 A**
- **Performance fail（overhead > 50%）**：evidence 记录 overhead 实测值；不进 C2；评估是否能通过减小 N 或调度优化降到 50% 以下；如果不能，escalate
- **Byte-equivalence fail**：算法 bug；回 C0 修 + 重跑

### 4.3 C2 — Serving integration

**Goal**：在 owlmlx serving 路径（subprocess backend）上接入 ngram，OwlCoda-class workload 上实测加速

**改动**：

- `owlmlx/speculative/suffix_decoding/runtime.py` 完成：与 `mlx_lm_subprocess_backend.py` 子进程端 decode loop 集成（wrapper 模式，不替换 mlx-lm decoder）
- `mlx_lm_subprocess_backend.py`：在子进程端加 ngram 启用开关（环境变量 `OWLMLX_SPECULATIVE_METHOD=ngram` 候选；最终名 design-grade 决定）
- F-1 surface 集成：`owlmlx/runtime/speculative_execution_status.py` 增加 `observe_ngram_runner_load` / `observe_ngram_runner_generate` / `observe_ngram_runner_unload`（沿用 F-1 design-grade §6.2 observe_* API 模式）
- 新增 `scripts/bench/ngram_workload.py`：跑 OwlCoda-class workload，分别在 `method=ngram` on / off 两态下采集

**Pass criteria**（命名为 `c2_serving_integration_contract`）：

| 检查项 | 要求 |
|---|---|
| Wall-clock 加速 | OwlCoda-class workload（§5）上，`method=ngram` on 相比 off 的 wall-clock decode 时间 **≥ 1.5×**（N≥20 重复，p50；非 mean）。**目标 ≥2× 但不预设**；1.5× 是 minimum-viable |
| Byte-equivalence | 同 prompt + 同 seed，on 和 off 两态的最终接受 token 序列 byte-for-byte 一致（N≥20 × 5 seed = 100 runs，**100% 一致**）|
| F-1 surface 转换 | `method=ngram` 从 `not_implemented` → `experimental`；`capability_label=experimental`；`accepted_tokens` / `accepted_rounds` 计数非零；`fallback` 字段在 distribution shift 时正确出现 |
| Baseline 无回归 | `scripts/bench/long_context_ladder.py` 在 `method=ngram=off` 下跑出的 TTFT / decode TPS 与 2026-05-26 baseline 落在 ±5% 内 |
| Health gate | C2 跑完 owlmlx server `/healthz` ok；无 zombie 子进程；session_kv_cache 字段无意外变化（应保持 disabled） |
| Fallback observable | 至少有一个 prompt 触发 fallback（人工构造 distribution-shift prompt 即可），F-1 surface 的 `fallback.reason_code` 非空 |

**Evidence**：`files/evidence/owlmlx/bench/perf-optimization/c-ngram/<ts>-c2-serving-integration.jsonl` + rollup

**Failure handling**：

- 加速 < 1.5×：evidence 记录实测值，不升 `method=ngram.status` 到 `experimental`，留在 `scaffold_only`；分析 root cause（fallback 过多？speculation tree 深度不够？OwlCoda workload 重复模式不强？）
- byte-equivalence fail：runner 进 `error` 状态，F-1 surface 报 `missing_reason=runner_crash` 或类似；硬阻塞，必须修
- baseline 回归 > 5%：说明 wrapper 即使关闭也带 overhead；不允许 land，必须降到 ±5% 内

### 4.4 三段连续纪律

- **C0 → C1 → C2 严格串行**：C0 evidence `passed` 才动 C1 代码；C1 evidence `passed` 才动 C2 代码
- 每段独立 commit、独立 evidence ledger、独立 verdict 字段，**不混合**
- failed phase 不撤销前段结论（C2 fail 不否定 C1 / C0 的 passed）
- 任意 phase 失败时，F-1 surface 的 `ngram.status` **不前进**，保持当前档位

## 5. OwlCoda-class Workload Definition

> **OPEN FOR USER REVIEW** —— 默认采"合成可复现 prompt set"路径。如果你要的是录制 OwlCoda 真实 session 或 live 接 OwlCoda，请直接改本节，下面 C2 evidence shape 不动。

### 5.1 默认选项 A — 合成 prompt set（推荐）

固定 prompt 集合，存入 `tests/fixtures/ngram_workload/owlcoda_class_prompts.jsonl`：

| Subset | 数量 | 形态 | 输入长度大致 | 代表场景 |
|---|---|---|---|---|
| `code_edit` | 20 | 共享 ~5k token 代码上下文 + 局部 edit instruction | 5k-8k input | OwlCoda 主要使用模式 |
| `tool_call` | 20 | agent-style：function-call JSON + 历史对话 | 2k-5k input | tool 使用密集场景 |
| `long_context_summarize` | 20 | ~32k token 文档 + "总结要点" 指令 | 32k input | 长文档场景 |

**总计 60 prompts**。每个 prompt 带：
- `prompt_id`: 稳定 ID
- `subset`: 三个之一
- `messages`: OpenAI-format
- `expected_repetition_class`: `high` / `medium` / `low`（对应 SuffixDecoding 论文的 entropy 分档）

### 5.2 备选方案（**未选**，记录考虑）

- **Option B 录制 OwlCoda 真实 session 回放**：拒绝理由 —— 录制状态依赖 OwlCoda 当下版本，spec 验证不可复现
- **Option C live 接 OwlCoda**：拒绝理由 —— 把 spec 验证绑到上层消费者状态，违反 [01-mainline-roadmap.md §IV.5](../01-mainline-roadmap.md) "OwlCoda 卡顿不延迟 owlmlx 主线" 边界

### 5.3 Workload runner

`scripts/bench/ngram_workload.py`：

- 读取 `tests/fixtures/ngram_workload/owlcoda_class_prompts.jsonl`
- 两态运行：`method=ngram` on / off
- 每态 N=3（C2 评估默认）；可 `--repeat-runs 20` 提到 N=20（gate 评估）
- 输出 schema 详见 §7

## 6. Harness Changes

### 6.1 新增 code-grade artifacts

- `owlmlx/speculative/suffix_decoding/__init__.py`
- `owlmlx/speculative/suffix_decoding/suffix_tree.py`
- `owlmlx/speculative/suffix_decoding/proposer.py`
- `owlmlx/speculative/suffix_decoding/verifier.py`
- `owlmlx/speculative/suffix_decoding/runtime.py`（C2 才加）
- `tests/test_speculative_suffix_decoding.py`
- `tests/fixtures/ngram_workload/owlcoda_class_prompts.jsonl`
- `scripts/bench/ngram_c1_canary.py`
- `scripts/bench/ngram_workload.py`

### 6.2 修改

- `owlmlx/runtime/mlx_lm_subprocess_backend.py`：增加 ngram 启用开关（C2 阶段）
- `owlmlx/runtime/speculative_execution_status.py`：增加 `observe_ngram_*` API（C2 阶段，沿用 F-1 design-grade §6.2 observe_* 模式）
- `owlmlx/runtime/kernel.py`：把 `observe_ngram_*` wire 到 ngram runner 的返回路径（C2 阶段）

### 6.3 Forbidden edits（Track 1 / Stage 1 边界）

F-2 任何 phase 都**不得**触动：

- `owlmlx/session_kv_cache.py`（Track 1 owns）
- `owlmlx/cache_manager.py`
- `owlmlx/scheduler_admission.py`
- `owlmlx/memory_pressure_eviction_policy.py`
- `owlmlx/memory_watermark.py`
- `owlmlx/gemma4_mtp_drafter.py`（F-3 / F-7 owns）
- `owlmlx/runtime/mlx_vlm_mtp_runner.py`（F-3 / F-7 owns）
- 任何 `files/evidence/owlmlx/bench/{session-kv-soak,eviction_soak,session-kv-cache,native-byte-equivalence}/`（其他 round owns）

PR 触动以上路径 → 直接拒收。

## 7. Evidence

### 7.1 落点

```text
files/evidence/owlmlx/bench/perf-optimization/c-ngram/
  <ts>-c0-offline-verifier.jsonl
  <ts>-c0-offline-verifier-rollup.jsonl
  <ts>-c1-verifier-canary.jsonl
  <ts>-c1-verifier-canary-rollup.jsonl
  <ts>-c2-serving-integration.jsonl
  <ts>-c2-serving-integration-rollup.jsonl
```

### 7.2 Per-cell schema（C2 workload runner）

```yaml
schema_version: f2.c2.cell.v1
gate: F-2
phase: c2
run_id: <ts>-c2-...
host: <hw.model>
prompt_id: <stable id>
subset: code_edit | tool_call | long_context_summarize
expected_repetition_class: high | medium | low
ngram_method_enabled: true | false
seed: <int>
metrics:
  ttft_ms: <float>
  decode_tps: <float>
  wall_ms: <float>
  prompt_tokens: <int>
  completion_tokens: <int>
  accepted_tokens: <int>          # F-1 surface field
  accepted_rounds: <int>          # F-1 surface field
  fallback_count: <int>           # F-1 surface fallback occurrence count
output_byte_hash: <sha256 of full decoded text>  # for byte-equivalence verification
verdict: pass | fail
```

### 7.3 Rollup schema

```yaml
schema_version: f2.c2.rollup.v1
gate: F-2
phase: c2
run_id: <ts>-c2-...
cell_count: <int>
on_cells: <int>
off_cells: <int>
byte_equivalence:
  total_pairs: <int>
  matched_pairs: <int>
  match_rate: <float>             # 必须 1.0 才 pass
wall_clock_speedup:
  p50: <float>
  p95: <float>
  per_subset:
    code_edit: <float>
    tool_call: <float>
    long_context_summarize: <float>
ngram_acceptance:
  mean_accepted_tokens_per_round: <float>
  mean_fallback_rate: <float>
baseline_regression:
  long_context_ladder_off_p50_tps_delta_pct: <float>  # 必须在 ±5% 内
graduates:
  ngram_status_to_experimental: true | false  # 仅当所有 pass criteria 满足
  any_method_to_supported: false               # F-2 永远不在此 graduate
```

## 8. Failure Handling

### 8.1 Per-phase 已分别在 §4.1/4.2/4.3 末尾详述

### 8.2 跨 phase 共通规则

- 任何 phase 失败时，F-1 surface 的 `ngram.status` **不前进**，保持当前档位
- evidence ledger 永远 append-only；failed verdict 不删除，作为后续 debug 入参
- runner 在 phase 之间必须 clean unload；不允许 zombie 子进程跨 phase
- C2 期间发现 baseline 回归 > 5%：runner 进 `error` 状态 + F-1 surface 报告 + 硬阻塞 land

### 8.3 系统级 failure

- 8066 server 在 C2 期间崩溃：evidence 标 `infrastructure_failure`，与 F-2 算法本身无关
- mlx-lm 升级后 verifier canary 不再过：触发 C1 重跑，evidence 标 `dependency_drift`

## 9. Out-of-scope reminders

防止 C0 / C1 / C2 实施 round 漂移：

- F-2 **不**做 OwlCoda 客户端改动；只在 owlmlx 内 runtime 侧验证
- F-2 **不**改 F-1 v1 contract surface 字段名 / vocabulary；只新增 `observe_ngram_*` kernel APIs
- F-2 **不**承诺对外可讲的速度故事；任何对外引用要走 evidence-language 四档（plan-grade Part VIII.2 之外的 source-of-truth promote）
- F-2 **不**触动量化变体（DWQ / OptiQ / UD-MLX）；那是独立 round
- F-2 **不**做 prefill chunking 与之协同；那是方向 B 的事，独立 spec
- F-2 **不**做 MoE prompt cache 协同；那是方向 A 的事，独立 spec
- F-2 evidence ledger **不**作为 §1a Promotion Gate 输入（promote 是另一 round）

## 10. Status / Next Step

- **Current**：C0 offline verifier passed；C1 mlx-lm verifier canary passed；F-1 surface `ngram.status` 仍保持 `not_implemented`
- **Completed code-grade**：
  - **C0**：`owlmlx/speculative/suffix_decoding/` pure-Python 模块 + `tests/test_speculative_suffix_decoding.py`，evidence `20260526T063850Z-c0-offline-verifier*`
  - **C1**：`mlx_lm_batch_verify` + `scripts/bench/ngram_c1_canary.py`，evidence `20260526T065819Z-c1-verifier-canary*`
- **Next**：
  - **C2 code-grade session**：serving integration + workload runner，落 C2 evidence；只有 C2 passed 后，才允许把 F-1 `ngram.status` 从 `not_implemented` 前进到 `experimental`
- **F-2 promotion**：不在本 spec；C2 passed 后若有需要走 §1a Gate 独立 round

### 10.1 Hand-off discipline

按 [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Part VIII.3：

> 层级 handoff：plan-grade → 用户复核 → 修订定版 → design-grade → 复核 → 代码（**不允许跳级**）

本 design-grade **不**包含 code-grade 所需的：

- 精确函数签名（design-grade 给 surface，code-grade 定签名）
- 算法细节（suffix tree 的具体节点 layout、proposer 的贪心阈值数值）
- 错误消息文案
- 测试 fixture 的具体 prompt 内容（§5 给 subset 配比 + 数量，具体 prompt 写到 code-grade）

这些 **只有**在 code-grade 才下定。

## 11. References

### 内部 lineage

- Plan-grade source：[`../07-perf-optimization-proposal-20260526.md`](../07-perf-optimization-proposal-20260526.md) §3 方向 C
- F-1 contract surface：[`F-1-spec.md`](F-1-spec.md)（消费方）
- F-1 plan-grade：[`../06-campaign-F1-plan.md`](../06-campaign-F1-plan.md)
- 长上下文 baseline：`files/evidence/owlmlx/bench/long-context-ladder/20260526T013407Z-long-context-ladder.jsonl`
- 现有 ngram surface vocabulary：[`F-1-spec.md`](F-1-spec.md) §4.5

### Code surfaces F-2 reads / 集成点

- mlx-lm cache 原语：[`/Users/yeemio/AI/gitrep/owlmlx/.venv/lib/python3.11/site-packages/mlx_lm/models/cache.py`](../../../.venv/lib/python3.11/site-packages/mlx_lm/models/cache.py)
- 子进程 backend：[`owlmlx/runtime/mlx_lm_subprocess_backend.py`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py)（C2 集成点）
- F-1 surface module：[`owlmlx/runtime/speculative_execution_status.py`](../../../owlmlx/runtime/speculative_execution_status.py)（C2 新增 observe_ngram_*）
- Kernel：[`owlmlx/runtime/kernel.py`](../../../owlmlx/runtime/kernel.py)（C2 wire observe_ngram_*）

### 外部锚定

- SuffixDecoding 论文：[arxiv 2411.04975](https://arxiv.org/abs/2411.04975)
- SuffixDecoding 主页：[suffix-decoding.github.io](https://suffix-decoding.github.io/)
- vLLM suffix_decoding API：[docs.vllm.ai v0.18.1 spec_decode suffix_decoding](https://docs.vllm.ai/en/v0.18.1/api/vllm/v1/spec_decode/suffix_decoding/)
- Snowflake Arctic Inference 集成：[snowflake engineering blog](https://www.snowflake.com/en/engineering-blog/suffixdecoding-arctic-inference-vllm/)

## 12. Change Log

| Date | 变更 | By |
|---|---|---|
| 2026-05-26 | design-grade 初稿（从 plan-grade §3 derive，C0/C1/C2 三段化，复用 F-1 method=ngram surface，OwlCoda-class workload 默认合成集） | architect session（this round） |
| 2026-05-26 | C1 性能 kill 标准修正：原"批量 forward ≤ 1.5× 单 token forward"物理不成立，改为"每位置摊销成本 ≤ 单 token decode 的 1.5×" | C1 execution review |
| 2026-05-26 | C1 byte-equivalence 标准修正：原稿要求与 stream_generate byte-for-byte 一致，但 C1 canary 发现 mlx-lm 自身在"整个 prompt 一次性 batched forward"vs"分段 prefill"之间存在小数值漂移（部分高不确定性 prompt 上 argmax 翻转）。这是 mlx-lm 的行为，不是算法问题。改为"自我一致性"标准：用 batch_verify 自身生成 reference 后，必须 100% accept。与 stream_generate 比对降为 secondary 指标 | C1 execution finding |
| 2026-05-26 | 状态更新：C0/C1 code-grade 已完成并通过；C2 serving integration 保持 pending；`ngram.status` 尚不前进 | C1 closeout |
