# B-1a · Design-Grade Spec

> **Gate**：Campaign B-1a · Session KV cache 第二模型 / 第二形状 · 同时关闭 §VI 4-gate G1（Cache Parity）
> **Plan-grade 来源**：[`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign B-1a
> **Grade**：design-grade · 见 [`README.md`](README.md)
> **日期**：2026-05-16
> **前置依赖**：plan-grade 已落地（commit `93473e0a`） / Qwen3.6-27B-4bit baseline evidence 已存（`files/evidence/owlmlx/bench/session-kv-cache/20260512T123316Z-owlmlx-native-session-kv-ttft-n4.jsonl`）
> **后置解锁**：B-1b 启动；§VI 4-gate G1 关闭；Campaign D D1 可启动

---

## 1. Context（≤ 3 句）

Qwen3.6-27B-4bit 已实证 session KV warm p50 TTFT 4026.099 ms → 543.389 ms（**7.409×**）。B-1a 验证同一 cache 机制在第二模型 / 第二形状（**Gemma 4-31B-it**）上**复现**，并同时关闭 §VI G1（Cache Parity = native 与 subprocess backend 在非 cache 路径下生成文本字节等价 N≥5；token IDs 仅在现有接口可获得时作为增强字段）。

---

## 2. Scope

### 2.1 In Scope（本 gate 必做）

- **Part A**：Gemma 4-31B-it 在 native backend + session KV 启用下的 warm TTFT 改善 + 5 类 cache 语义（hit / miss / eviction / TTL / restart）一致性
- **Part B**：Gemma 4-31B-it 在 native backend 与 subprocess backend 之间，非 cache 路径下的 generated text UTF-8 bytes 等价（N≥5 prompt）；若 backend 已暴露 token IDs，同步记录 token IDs 等价性

### 2.2 Out of Scope（**禁止**在本 gate 内做）

- ❌ Qwen3.6-35B-A3B 的扩展验证（属 B-1b 后续 / Campaign A）
- ❌ `cache=on` × settle barrier 无回归 N≥20 跑（属 B-1b）
- ❌ 24h+ soak（属 B-1c §1）
- ❌ swap 序列累积 reclaim（属 B-1c §2）
- ❌ 引入新 spec-as-code 模块（违反 Stage 1 禁令）
- ❌ 修改 `session_kv_cache.py` / `MlxNativeBackend` / `MlxLmSubprocessBackend` 契约
- ❌ 调整 `MAX_GENERATION_CONCURRENCY` 或 watermark 阈值
- ❌ 把 native backend 升 default 或调整 release channel
- ❌ 触碰 DS4 venv（`.runtime-deepseek-v4-mlx`）
- ❌ 更新 README 声称 native backend 已 supported
- ❌ 批量预先撰写 B-1b / B-1c / Wave H 的 design spec

---

## 3. Verification Contract

### 3.1 Part A · Session KV second-model 验证

#### 3.1.A Setup

| 项 | 值 |
|---|---|
| Model ID | `gemma-4-31B-it` |
| Model path | `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`（已存在；通过 `model_lineage.py` 校验 HF commit SHA + 记录到 ledger） |
| Backend | `MlxNativeBackend`（in-process · `owlmlx/runtime/mlx_native_backend.py`） |
| Cache 启用 | `OWLMLX_SESSION_CACHE_ENABLED=1`（env）+ `X-Owlmlx-Session-Id: b1a-gemma4-31b-<run-id>` |
| Cache 禁用 baseline | 同一 run，second pass 用 `OWLMLX_SESSION_CACHE_ENABLED=0`（disabled run）|
| Host | `Mac17,6`（与 Qwen3.6-27B baseline 同 host） |
| Temperature | `0.0`（确定性采样） |
| Seed | 固定（与现有 harness 一致；如无既定值，prescribe `42` 并在 ledger 记录） |
| `MAX_GENERATION_CONCURRENCY` | `1`（保持不变） |

#### 3.1.B 测试形态（mirror Qwen3.6-27B baseline）

| 项 | 值 |
|---|---|
| Prompt 形态 | append-only multi-round 对话 |
| Prompt 长度（最终轮） | ≈ 4 200 chars（与 baseline 一致） |
| Rounds | 4（1 cold + 3 warm） |
| `max_tokens` | 2（与 Qwen3.6 baseline `20260512T123316Z-owlmlx-native-session-kv-ttft-n4.jsonl` 保持一致；只验证 first-token / prefill 路径） |
| Round 间间隔 | 与 baseline harness 一致；不主动延长 |

#### 3.1.C 子探针（A.1 – A.5）

| ID | 探针 | 内容 | 必通过条件 |
|---|---|---|---|
| **A.1** | Warm TTFT 改善 | 4 rounds enabled vs 4 rounds disabled（同 prompt / 同 host / 同 run） | `improvement_ratio_p50 >= 1.5`；enabled warm p50 必须低于 disabled warm p50；记录 min / p50 / max，不要求逐轮单调 |
| **A.2** | Hit / miss / drop 计数 | 在 A.1 enabled 跑期间持续观测 | warm rounds: `hit == true` ≥ 2 / 3；任意 round: `drop == 0`；cold round 必为 miss |
| **A.3** | Session LRU eviction probe | 单独短跑：设置 `OWLMLX_SESSION_CACHE_MAX_ENTRIES=1`，同模型创建两个 session，触发 session-cache LRU eviction | eviction counter 增长；被驱逐 session 二次请求 = miss + recover；无 watermark→FATAL |
| **A.4** | Session TTL probe | 单独短跑：设置 `OWLMLX_SESSION_CACHE_TTL_S` 为短值，等待过期后发起同 session 请求 | session cache expiration counter 增长；过期后请求 = miss + new session |
| **A.5** | Runtime restart probe | 单独短跑：通过 `RuntimeKernel.restart_model()` 或 `POST /v1/runtime/restart` 执行一次 model restart | restart 后旧 session entry 被 drop；首个请求 miss + new session，下一 warm 请求可 hit；watermark 状态归位；reclaim 验证通过 |

**注**：A.3 / A.4 / A.5 是 smoke-level 探针（每个 ≤ 5 min host 时间），不是 soak。完整 soak 在 B-1c。

#### 3.1.D Part A pass criteria（rolled-up YAML）

```yaml
part_A_session_kv_second_model:
  A1_warm_ttft_improvement:
    improvement_ratio_p50: ">= 1.5"
    enabled_warm_p50_lt_disabled_warm_p50: true
    warm_min_p50_max_recorded: true
  A2_hit_miss_counters:
    warm_hits_min: 2            # of 3 warm rounds
    drops_total: 0
    cold_round_miss: true
  A3_session_lru_eviction_probe:
    eviction_counter_increased: true
    post_eviction_miss_recover: true
    watermark_fatal_observed: false
  A4_session_ttl_probe:
    expiration_counter_increased: true
    post_expire_miss_new_session: true
  A5_runtime_restart_probe:
    restart_success: true
    old_session_entry_dropped: true
    post_restart_miss_new_session: true
    second_post_restart_warm_hit: true
    reclaim_verified: true
  conclusion: passed | failed   # 五个子探针全 passed 才可 passed
```

---

### 3.2 Part B · 非 cache 路径 byte-equivalence（N≥5 prompt）

#### 3.2.A Setup

| 项 | 值 |
|---|---|
| Model ID | `gemma-4-31B-it` |
| Backends | A: `MlxNativeBackend` · B: `MlxLmSubprocessBackend` |
| Cache 状态 | `OWLMLX_SESSION_CACHE_ENABLED=0`（**显式 OFF**） |
| `X-Owlmlx-Session-Id` | **不设置**（确保非 cache 路径） |
| Temperature | `0.0`（确定性） |
| Seed | 固定（与 Part A 同） |
| `max_tokens` | 128（足以暴露中段 divergence） |

#### 3.2.B 5 类 prompt（覆盖不同形状）

| Prompt ID | 长度 | 内容类别 |
|---|---|---|
| `p1` | ≈ 50 chars | 短事实问答（"What is the capital of France?"） |
| `p2` | ≈ 500 chars | 中等说明请求（解释一个技术概念） |
| `p3` | ≈ 2 000 chars | 长上下文 QA（提供背景 + 提问） |
| `p4` | ≈ 300 chars | 代码补全（function signature + 补全） |
| `p5` | ≈ 1 500 chars | 单轮多语义（类似 multi-turn 拍扁为单 prompt） |

#### 3.2.C 测量

对每个 prompt，分别通过两个 backend 调用 generation：

1. 捕获生成文本的 **UTF-8 byte sequence**（主判定；当前 runtime stream surface 可直接取得）
2. 若 backend 已通过 `StreamEvent.detail` 或等价内部 harness 暴露 token IDs，则同步捕获 token IDs（增强字段，非首版 gate 阻塞项）
3. 捕获文本与 generation 耗时（辅助 debug，耗时非主判定）

**主判定**：生成文本 UTF-8 bytes **完全等价**。Token IDs 等价是增强证据，不作为首版 gate 必要条件，除非下一轮 code-grade 已经无契约漂移地暴露该字段。

#### 3.2.D Part B pass criteria（rolled-up YAML）

```yaml
part_B_non_cache_byte_equivalence:
  prompts_total: 5
  per_prompt:
    - id: p1
      generated_text_utf8_equivalent: true | false
      first_byte_divergence_index: null | <int>
      token_ids_equivalent: true | false | null
      first_token_id_divergence_index: null | <int>
    # ... p2..p5 同上
  conclusion: passed | failed   # 5 个 prompt 全 generated_text_utf8_equivalent == true 才可 passed
  divergence_diagnostic:
    # 仅当 conclusion = failed 时填
    first_failing_prompt: <p1..p5>
    first_byte_divergence_index: <int>
    native_byte_at_index: <int>
    subprocess_byte_at_index: <int>
    suspected_root_cause: <one of: sampler / tokenizer / numeric / stream_framing / unknown>
```

---

### 3.3 B-1a Gate 总 verdict

```yaml
B_1a_second_model_byte_equiv:
  part_A_conclusion: passed | failed
  part_B_conclusion: passed | failed
  overall_conclusion: passed | failed   # Part A AND Part B
  graduates:
    G1_cache_parity: true | false        # Part B passed 即 G1 关闭
    unblock_B_1b: true | false           # overall passed 即 B-1b 可启动
    unblock_campaign_D_D1: true | false  # overall passed 即 D1 可启动
```

#### 2026-05-16 closeout verdict

```yaml
B_1a_second_model_byte_equiv:
  part_A_conclusion: passed
  part_B_conclusion: passed
  overall_conclusion: passed
  graduates:
    G1_cache_parity: true
    unblock_B_1b: true
    unblock_campaign_D_D1: true
  evidence:
    part_A_runtime_kernel:
      path: files/evidence/owlmlx/bench/session-kv-cache/20260516T151100Z-b1a-gemma4-31b-it-session-kv-ttft.jsonl
      execution_boundary: runtime-kernel
      improvement_ratio_p50: 2.246
      disabled_warm_p50_first_token_ms: 1542.972
      enabled_warm_p50_first_token_ms: 687.102
      warm_hits_total: 3
      drops_total: 0
      runtime_kernel_restart_model: completed
    part_B_byte_equivalence:
      path: files/evidence/owlmlx/bench/native-byte-equivalence/20260516T144845Z-b1a-gemma4-31b-it-byte-equiv-n5.jsonl
      prompts: 5
      utf8_equivalent_count: 5
      divergent_count: 0
```

Earlier same-day Part A evidence
`files/evidence/owlmlx/bench/session-kv-cache/20260516T143603Z-b1a-gemma4-31b-it-session-kv-ttft.jsonl`
is retained as a failed diagnostic run for the RuntimeKernel/native MLX
thread-affinity bug. The repaired closeout evidence above supersedes it for
the B-1a verdict.

---

## 4. Harness 改动点（最小）

> **纪律**：复用现有 harness；不新增 spec-as-code 模块；脚本是 runnable code 不是 spec。

### 4.1 复用既有

| 现有 harness / 模块 | 复用方式 |
|---|---|
| `tests/test_repeatability_campaign_harness.py` | 已支持 N runs；本 gate **不**需 N≥20，复用其多轮跑骨架即可 |
| `owlmlx/comparative_evidence_runner.py` | 已支持 measured subprocess 跨 backend 对比；Part B 直接调度 |
| `owlmlx/repeatability_statistics.py` | 计算 warm TTFT 的 mean / stddev / CV / p50 / p99 |
| `owlmlx/session_kv_cache.py` + `MlxNativeBackend` | 直接消费；**禁止**修改契约 |
| `owlmlx/runtime/mlx_lm_subprocess_backend.py` | 直接消费 |
| `owlmlx/model_lineage.py` | 记录 Gemma 4-31B-it HF commit SHA 到 evidence |
| `files/evidence/owlmlx/bench/session-kv-cache/` | 沿用既有 evidence 目录 |

### 4.2 新增 runnable scripts（code-grade 在下一轮实施）

| 脚本路径 | 职责 | 输出 |
|---|---|---|
| `scripts/bench/session_kv_cache_ttft.py`（扩展 `--gate b1a-gemma4` / 或轻量 wrapper） | Part A 全套（A.1 主跑 + A.2 计数 + A.3–A.5 短探针），enabled / disabled 双跑；优先复用现有脚本，避免新增平行 harness | `files/evidence/owlmlx/bench/session-kv-cache/<ts>-b1a-gemma4-31b-it-session-kv-ttft.jsonl` |
| `scripts/bench/native_byte_equivalence.py` | Part B 全套（5 prompt × 2 backend × 1 run），generated text UTF-8 bytes 比对；token IDs 仅可得时记录 | `files/evidence/owlmlx/bench/native-byte-equivalence/<ts>-b1a-gemma4-31b-it-byte-equiv-n5.jsonl` |

**两个脚本均不引入新 Python 模块到 `owlmlx/` 包内**；script-only。CI lint 自动豁免 scripts/。

### 4.3 已知潜在 friction（待 code-grade 确认）

| 风险点 | 排查 | 应对 |
|---|---|---|
| `MlxNativeBackend` / `MlxLmSubprocessBackend` 是否 expose token IDs | code-grade 先查 backend 接口 | 不阻塞首版 gate；首版主判定使用 UTF-8 bytes。若 token IDs 可无契约漂移取得，则作为增强字段记录；若不可得，填 `null` |
| Gemma 4-31B-it 的 seed 行为 | code-grade 跑 disabled-disabled 对照确认 deterministic | 若 seed 不稳定，本 gate 阻塞；先排查 mlx-lm sampler 配置 |
| Gemma 4 context window vs ~4.2k baseline | code-grade 跑前确认 | 若 context window 不够，缩短 prompt 至 baseline 的 80%；记录 ledger |
| Native backend session-scope 是否在 Gemma 4 上有效 | code-grade 第一轮 smoke | 若 native backend 路径在 Gemma 4 上有未知失败模式，先排查 `mlx_native_backend.py` 的模型加载分支 |

---

## 5. Evidence Output Paths（精确）

```
files/evidence/owlmlx/bench/session-kv-cache/
  └── <YYYYMMDDTHHmmssZ>-b1a-gemma4-31b-it-session-kv-ttft.jsonl

files/evidence/owlmlx/bench/native-byte-equivalence/   # 新建子目录
  └── <YYYYMMDDTHHmmssZ>-b1a-gemma4-31b-it-byte-equiv-n5.jsonl
```

### 5.1 文件命名约定

- 时间戳 format：`YYYYMMDDTHHmmssZ`（UTC ISO 8601 紧凑形式，与 Qwen3.6 baseline 一致）
- prefix：`b1a-`（gate ID，便于 grep / 后续清单聚合）
- 模型名：`gemma4-31b-it`（lower-case + hyphen；与 baseline 命名风格对齐）
- 测试维度：`session-kv-ttft` / `byte-equiv-n5`
- 后缀：`.jsonl`（line-delimited JSON，便于增量 append + 流式分析）

### 5.2 ledger 字段最小集（Part A · `session-kv-ttft.jsonl`）

```json
{
  "schema_version": "b1a.v1",
  "gate": "B-1a",
  "part": "A",
  "run_id": "<uuid>",
  "timestamp_utc": "<ISO>",
  "host": "Mac17,6",
  "model": {
    "id": "gemma-4-31B-it",
    "path": "/Users/yeemio/AI/Agent/models/gemma-4-31B-it",
    "hf_commit_sha": "<sha>",
    "mlx_lm_version": "<ver>",
    "quantization": "<spec>"
  },
  "backend": "native",
  "config": {
    "OWLMLX_SESSION_CACHE_ENABLED": "1",
    "session_id": "b1a-gemma4-31b-<run-id>",
    "temperature": 0.0,
    "seed": 42,
    "max_tokens": 2,
    "max_generation_concurrency": 1
  },
  "test_shape": {
    "prompt_chars_approx": 4200,
    "rounds": 4,
    "round_pattern": "append-only"
  },
  "rounds": [
    {"round": 1, "phase": "cold", "first_token_ms": <float>, "hit": false, "drop": false},
    {"round": 2, "phase": "warm", "first_token_ms": <float>, "hit": true, "drop": false},
    {"round": 3, "phase": "warm", "first_token_ms": <float>, "hit": true, "drop": false},
    {"round": 4, "phase": "warm", "first_token_ms": <float>, "hit": true, "drop": false}
  ],
  "summary": {
    "warm_min_first_token_ms": <float>,
    "warm_p50_first_token_ms": <float>,
    "warm_max_first_token_ms": <float>,
    "hits_total": <int>,
    "drops_total": <int>
  },
  "disabled_baseline": {
    "rounds": [...同结构...],
    "warm_p50_first_token_ms": <float>
  },
  "improvement_ratio_p50": <float>,
  "subprobes": {
    "A3_session_lru_eviction": { "passed": <bool>, "events": [...] },
    "A4_session_ttl":          { "passed": <bool>, "events": [...] },
    "A5_runtime_restart":      { "passed": <bool>, "events": [...] }
  },
  "watermark_fatal_observed": false,
  "verdict": "passed | failed"
}
```

### 5.3 ledger 字段最小集（Part B · `byte-equiv-n5.jsonl`）

```json
{
  "schema_version": "b1a.v1",
  "gate": "B-1a",
  "part": "B",
  "run_id": "<uuid>",
  "timestamp_utc": "<ISO>",
  "host": "Mac17,6",
  "model": { ...同 Part A model 段... },
  "config": {
    "OWLMLX_SESSION_CACHE_ENABLED": "0",
    "session_id_header_set": false,
    "temperature": 0.0,
    "seed": 42,
    "max_tokens": 128
  },
  "prompts": [
    {
      "id": "p1",
      "chars": 50,
      "category": "short_factual_qa",
      "native": {
        "generated_text": "<str>",
        "generated_text_utf8_sha256": "<sha256>",
        "token_ids": [<int>, ...] | null,
        "duration_ms": <float>
      },
      "subprocess": {
        "generated_text": "<str>",
        "generated_text_utf8_sha256": "<sha256>",
        "token_ids": [<int>, ...] | null,
        "duration_ms": <float>
      },
      "generated_text_utf8_equivalent": <bool>,
      "first_byte_divergence_index": null | <int>,
      "token_ids_equivalent": <bool> | null,
      "first_token_id_divergence_index": null | <int>
    }
    // p2..p5 同结构
  ],
  "summary": {
    "total_prompts": 5,
    "utf8_equivalent_count": <int>,
    "divergent_count": <int>
  },
  "verdict": "passed | failed",
  "divergence_diagnostic": null | {
    "first_failing_prompt": "p<N>",
    "first_byte_divergence_index": <int>,
    "native_byte_at_index": <int>,
    "subprocess_byte_at_index": <int>,
    "suspected_root_cause": "<one of: sampler | tokenizer | numeric | stream_framing | unknown>"
  }
}
```

---

## 6. Failure Handling

| 失败位置 | 失败语义 | 应对纪律 |
|---|---|---|
| **Part A · A.1** 不达 `improvement_ratio_p50 >= 1.5` | session KV 在 Gemma 4 上无 meaningful 收益 | B-1a 失败；记录 verdict + 不进入 Part B；触发 root-cause 排查（cache 路径是否 fired / KV trim 是否生效 / Gemma 4 attention shape 是否兼容） |
| **Part A · A.2** drops > 0 或 warm hits < 2/3 | cache 语义不一致 | B-1a 失败；不进入 Part B；归因到 session_kv_cache 的 hit logic 或 eviction policy |
| **Part A · A.3 / A.4 / A.5** 任一子探针失败 | cache lifecycle 语义在 Gemma 4 上有差异 | B-1a 失败；记录失败子探针 + 归因；不进入 Part B |
| **Part A 中 watermark→FATAL** | memory governance 紧急保护触发 | B-1a 失败；记录 watermark 跃迁；归因到 Gemma 4 模型尺寸 vs host budget；可能需要重选 baseline 模型 |
| **Part B** 任一 prompt UTF-8 bytes divergent | native 与 subprocess 在非 cache 路径下生成不一致 | B-1a 失败；§VI G1 不能关闭；记录 `first_byte_divergence_index` + 怀疑 root cause；触发**单独的归因 round**（不属于 B-1a 范围） |
| Harness 自身崩溃（非业务失败） | 工具问题，非 gate 结论 | 不计入 B-1a verdict；修 harness 后重跑；记录到 dev log，不污染 ledger |

**关键纪律**：

- Part A 失败 **不**进入 Part B
- Part B 失败 **不**回溯否定 Part A 结论；Part A 仍独立成立
- 任何 watermark→FATAL 都视为 host 安全事件，立即停跑、保留 ledger、人工介入

---

## 7. Out-of-Scope 提醒（再次）

本 gate **不**承担：

| 项 | 谁承担 |
|---|---|
| `cache=on` 下 N≥20 跑后 `failed_reclaim = 0` 报告 | B-1b |
| 24h 纯 soak + `active_memory` 不漂 | B-1c §1 |
| 24h soak + 每 4h × 6 swap | B-1c §2 |
| Qwen3.6-35B-A3B 第三模型扩展 | Campaign A（中期）/ B-1b 后续 |
| `server.py` 路由拆分 | Wave H · H1 |
| `speculative_execution_status` runtime-owned contract | Campaign F-1 |
| README / ARCHITECTURE-TRUTH §2.2 刷新 | Wave G · G1 / G3 |
| native backend 升 `partial` 或 `supported` | §VI 4-gate 全过 + cross-host 重复 |

---

## 8. Acceptance Checklist（review 用）

design-grade review 通过的条件：

- [ ] Scope `in` / `out` 列表清晰，与 plan-grade 一致
- [ ] Part A / Part B 字段命名与 plan-grade `B-1a · second_model_byte_equiv` 风格一致，且不复用 B-1c 的 soak 字段名
- [ ] Part B 5 prompt 类别覆盖 short / medium / long / code / multi-turn-style
- [ ] Pass criteria YAML 字段完整可机读
- [ ] Harness 改动只复用既有，**0** 新 spec-as-code 模块
- [ ] Evidence output paths 与 baseline (`20260512T123316Z-owlmlx-native-session-kv-ttft-n4.jsonl`) 风格一致
- [ ] Failure handling 覆盖 watermark→FATAL 与 Part A/B 失败语义独立
- [ ] Out-of-scope 列表显式禁止 scope creep

---

## 9. 后续 Round 预告（**不**在本 spec 范围）

| 顺序 | Spec | 启动条件 |
|---|---|---|
| 1 | **`B-1a-spec.md`** design-grade review | completed |
| 2 | code-grade 实施（独立 round + PR）：scripts/bench/* + harness 微扩 | completed |
| 3 | B-1a 真实运行 + evidence 落 | completed |
| 4 | B-1a verdict 判定（passed / failed）+ ledger commit | completed: `passed` |
| 5 | passed 后：B-1b-spec.md 起草（独立 round） | B-1a verdict = passed |
| 5' | failed 后：归因 round + 决定是否调整 plan-grade gate 阈值 | B-1a verdict = failed |
