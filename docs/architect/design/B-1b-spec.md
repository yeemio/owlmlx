# B-1b · Design-Grade Spec

> **Gate**：Campaign B-1b · `cache=on` × settle barrier no regression
> **Plan-grade 来源**：[`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign B-1b
> **Grade**：design-grade · 见 [`README.md`](README.md)
> **日期**：2026-05-16
> **前置依赖**：B-1a closeout verdict = `passed`（见 [`B-1a-spec.md`](B-1a-spec.md#2026-05-16-closeout-verdict)）
> **后置解锁**：B-1c §1 pure soak 可启动；B-1 supported gate 从 1/4 前进到 2/4

---

## 1. Context（≤ 3 句）

B-1a 已证明 session KV cache 在 Qwen3.6-27B-4bit 与 Gemma 4-31B-it 上有 warm TTFT 收益，并关闭 §VI G1 Cache Parity。B-1b 只验证一个更窄的问题：**打开 session KV cache 后，explicit unload / settle barrier / reclaim stats 不发生回归**。本 gate 不做 24h soak，不做模型 swap 序列，不把 session KV cache 升级为 `supported`。

B-1a evidence anchors：

- `files/evidence/owlmlx/bench/session-kv-cache/20260512T123316Z-owlmlx-native-session-kv-ttft-n4.jsonl`
- `files/evidence/owlmlx/bench/session-kv-cache/20260516T151100Z-b1a-gemma4-31b-it-session-kv-ttft.jsonl`
- `files/evidence/owlmlx/bench/native-byte-equivalence/20260516T144845Z-b1a-gemma4-31b-it-byte-equiv-n5.jsonl`

---

## 2. Scope

### 2.1 In Scope（本 gate 必做）

- Native backend + Gemma 4-31B-it，跑 **cache-off baseline N=20** 与 **cache-on candidate N=20**
- N 的计数单位 = 一次完整 operation boundary：
  `load_model` → 生成请求 → `unload_model` → settle sampler → `reclaim_barrier_stats()` / `settle_barrier_event`
- `cache=on` candidate 每轮必须真实触发 session cache path：同一 session 至少 1 cold + 1 warm request；warm request 需要观测到 hit，且该轮 `drops == 0`
- 对比 cache-on 与 cache-off 的 reclaim-barrier-event/stats 分布：`duration_ms` p50 / p99、failed counts、missing signals、backend-reported reclaim fields
- 输出两个 per-mode jsonl ledger + 一个 rollup jsonl verdict row

### 2.2 Out of Scope（禁止在本 gate 内做）

- B-1c §1 的 24h+ pure soak
- B-1c §2 的 24h+ soak + every-4h model swap
- Qwen3.6-35B-A3B 第三模型扩展
- continuous batching / scheduler policy changes
- 修改 `session_kv_cache.py`、`RuntimeKernel`、`MlxNativeBackend`、`settle_barrier_event.py` 的 runtime contract
- 引入任何 `owlmlx/` 包内新 spec-as-code module
- 调整 memory watermark 阈值、`MAX_GENERATION_CONCURRENCY`、release channel、README supported labels
- 触碰 DS4 venv、DS4/MTP research note、source-of-truth promotion 文档或 evidence 文件

---

## 3. Verification Contract

### 3.1 Setup

| 项 | 值 |
|---|---|
| Model ID | `gemma-4-31B-it` |
| Model path | `/Users/yeemio/AI/Agent/models/gemma-4-31B-it` |
| Backend | `MlxNativeBackend` through `RuntimeKernel` |
| Host | `Mac17,6`（沿用 B-1a host truth；code-grade 写入 ledger） |
| Rounds | `20` per mode；`cache_off_baseline` 先跑，`cache_on_candidate` 后跑 |
| Generation shape | short deterministic request；`temperature=0.0`、`seed=42`、`max_tokens=2` |
| Cache-off mode | `OWLMLX_SESSION_CACHE_ENABLED=0`，不设置 `X-Owlmlx-Session-Id` |
| Cache-on mode | `OWLMLX_SESSION_CACHE_ENABLED=1`，每轮设置 `X-Owlmlx-Session-Id: b1b-gemma4-31b-r<round>` |
| Concurrency | `MAX_GENERATION_CONCURRENCY=1`（不得改） |

### 3.2 Per-Round Required Observations

每一轮都必须记录：

- `load_result.ok`
- generation result(s)：cache-off 1 request；cache-on 1 cold + 1 warm request
- session cache snapshot：`active_entries`、`hits`、`misses`、`drops`、`evictions`、`rejects`（cache-off 可为 `null`，但必须显式记录）
- `unload_result.ok`
- settle sampler：`active_memory_before_bytes`、`active_memory_after_load_bytes`、`active_memory_after_unload_settled_bytes`、`settle_barrier_iterations`、`settle_barrier_duration_ms`
- `settle_barrier_event.summary.barrier_state` 与 `barrier.unresolved_event_count`
- `reclaim_barrier_stats.summary.failure_measurement_count`
- `reclaim_barrier_stats.duration_ms` distribution after the round
- `reclaim_barrier_stats.observed_active_memory_freed_bytes` / `observed_cache_memory_freed_bytes` / `expected_minus_observed_active_bytes` when present
- `watermark_before` / `watermark_after`

### 3.3 Pass / Fail YAML

```yaml
B_1b_cache_on_no_regress:
  baseline:
    mode: cache_off_baseline
    rounds_required: 20
    rounds_completed: 20
    failed_reclaim_events_total: 0
    failed_unload_events_total: 0
    unresolved_reclaim_barrier_events: 0
    failure_measurement_count: 0
    barrier_state_all_clean: true
    watermark_fatal_observed: false
  candidate:
    mode: cache_on_candidate
    rounds_required: 20
    rounds_completed: 20
    session_cache_warm_hits_min: 20      # one warm hit per candidate round
    session_cache_drops_total: 0
    failed_reclaim_events_total: 0
    failed_unload_events_total: 0
    unresolved_reclaim_barrier_events: 0
    failure_measurement_count: 0
    barrier_state_all_clean: true
    watermark_fatal_observed: false
  distribution_alignment:
    duration_ms_p50_candidate_lte: "baseline.p50 * 1.20 + 100ms"
    duration_ms_p99_candidate_lte: "baseline.p99 * 1.50 + 250ms"
    missing_signals_symmetric: true
    reclaim_delta_distribution_checked_when_present: true
    reclaim_delta_p50_abs_candidate_lte: "baseline.abs_p50 * 1.25 + 256MiB"
    reclaim_delta_p99_abs_candidate_lte: "baseline.abs_p99 * 1.50 + 512MiB"
  cache_on_no_regress: passed | failed | blocked
  conclusion: passed | failed | blocked
  graduates:
    cache_on_no_regress: true | false
    unblock_B_1c_section_1: true | false
```

**Notes**：

- `failed_reclaim_events_total` 由 `reclaim_barrier_stats.events` 与 `settle_barrier_event` 派生；任何 `barrier_state == failed_reclaim` 或 unresolved failed-reclaim event 都计入失败。
- `failed_unload_events_total` 不是 plan-grade 主字段，但 B-1b 不允许通过一个 failed-unload round 来声称 no-regress。
- 如果 backend 没有暴露 active/cache reclaim bytes，但 baseline 与 candidate 的 `missing_signals` 对称，仍可用 duration + event + failure counts 判定；如果只有 candidate 缺信号，则 fail。

---

## 4. Harness Changes（code-grade 最小改动点）

> **纪律**：只改 runnable scripts/tests；不新增 `owlmlx/` spec-as-code module。

| Surface | 改动 |
|---|---|
| `scripts/bench/eviction_soak.py` | 增加 `--gate b1b-cache-settle` 或同等 runner mode；支持 single-model N=20、`--cache-mode off|on`、per-round session id、stats snapshot |
| `scripts/bench/session_kv_cache_ttft.py` | 只复用其 session-cache env/header helpers；不把 TTFT 逻辑扩进 B-1b verdict |
| `RuntimeKernel.reclaim_barrier_stats()` | 只读消费；不得修改 contract |
| `GET /v1/runtime/reclaim-barrier-event` | 只读消费；不得修改 contract |
| tests | code-grade 可加 script-level parser/smoke tests；不需要 runtime contract 测试，除非 harness 暴露出真实 bug |

允许的实现形态：

1. 首选：扩展 `scripts/bench/eviction_soak.py` 的 runner mode。
2. 备选：新增 `scripts/bench/cache_settle_no_regress.py` 作为 thin wrapper，内部复用 eviction-soak sampler 与 session-cache helper。

两种形态都必须保持 evidence schema 一致，并且不得在 `owlmlx/` 包内新增设计型 dataclass/builders。

---

## 5. Evidence Output Paths

```text
files/evidence/owlmlx/bench/cache-settle-no-regress/
  ├── <YYYYMMDDTHHmmssZ>-b1b-gemma4-31b-it-cache-off-n20.jsonl
  ├── <YYYYMMDDTHHmmssZ>-b1b-gemma4-31b-it-cache-on-n20.jsonl
  └── <YYYYMMDDTHHmmssZ>-b1b-gemma4-31b-it-cache-on-no-regress-rollup.jsonl
```

### 5.1 Per-Mode Ledger Row

```json
{
  "schema_version": "b1b.v1",
  "gate": "B-1b",
  "run_id": "<uuid>",
  "mode": "cache_off_baseline | cache_on_candidate",
  "round": 1,
  "timestamp_utc": "<ISO>",
  "host": "Mac17,6",
  "model": {
    "id": "gemma-4-31B-it",
    "path": "/Users/yeemio/AI/Agent/models/gemma-4-31B-it",
    "hf_commit_sha": "<sha>",
    "mlx_lm_version": "<ver>"
  },
  "backend": "native",
  "config": {
    "OWLMLX_SESSION_CACHE_ENABLED": "0 | 1",
    "session_id": null,
    "temperature": 0.0,
    "seed": 42,
    "max_tokens": 2,
    "max_generation_concurrency": 1
  },
  "session_cache": {
    "active_entries_before_unload": 0,
    "active_entries_after_unload": 0,
    "cold_request_hit": false,
    "warm_request_hit": true,
    "hits_delta": 1,
    "misses_delta": 1,
    "drops_delta": 0,
    "evictions_delta": 0,
    "rejects_delta": 0
  },
  "operation": {
    "load_ok": true,
    "generation_ok": true,
    "unload_ok": true,
    "settle_barrier_iterations": 2,
    "settle_barrier_duration_ms": 12.345
  },
  "memory": {
    "active_memory_before_bytes": 0,
    "active_memory_after_load_bytes": 0,
    "active_memory_after_unload_settled_bytes": 0,
    "watermark_before": "GREEN",
    "watermark_after": "GREEN"
  },
  "settle_barrier_event": {
    "barrier_state": "clean",
    "unresolved_event_count": 0,
    "total_event_count": 0
  },
  "reclaim_barrier_stats_after_round": {
    "summary": {
      "measurement_count": 1,
      "failure_measurement_count": 0,
      "event_count": 0,
      "unresolved_event_count": 0
    },
    "duration_ms": {"p50": 12.345, "p99": 12.345},
    "observed_active_memory_freed_bytes": {"p50": 0, "p99": 0},
    "observed_cache_memory_freed_bytes": {"p50": 0, "p99": 0},
    "expected_minus_observed_active_bytes": {"p50": 0, "p99": 0},
    "missing_signals": []
  },
  "round_verdict": "passed | failed"
}
```

For `cache_off_baseline`, `session_cache` fields may be `null` except `drops_delta=0`; the ledger must still state cache was disabled and no session header was sent.

### 5.2 Rollup Row

```json
{
  "schema_version": "b1b.v1",
  "gate": "B-1b",
  "run_id": "<uuid>",
  "timestamp_utc": "<ISO>",
  "baseline_ledger": "files/evidence/owlmlx/bench/cache-settle-no-regress/<ts>-b1b-gemma4-31b-it-cache-off-n20.jsonl",
  "candidate_ledger": "files/evidence/owlmlx/bench/cache-settle-no-regress/<ts>-b1b-gemma4-31b-it-cache-on-n20.jsonl",
  "baseline_rounds": 20,
  "candidate_rounds": 20,
  "candidate_warm_hits": 20,
  "candidate_drops_total": 0,
  "failed_reclaim_events_total": 0,
  "failed_unload_events_total": 0,
  "failure_measurement_count": 0,
  "duration_alignment": {
    "baseline_p50_ms": 0.0,
    "candidate_p50_ms": 0.0,
    "baseline_p99_ms": 0.0,
    "candidate_p99_ms": 0.0,
    "p50_within_threshold": true,
    "p99_within_threshold": true
  },
  "missing_signals_symmetric": true,
  "cache_on_no_regress": "passed | failed | blocked",
  "conclusion": "passed | failed | blocked",
  "graduates": {
    "cache_on_no_regress": true,
    "unblock_B_1c_section_1": true
  }
}
```

---

## 6. Failure Semantics

| Situation | Verdict | Discipline |
|---|---|---|
| cache-off baseline has failed reclaim/unload, watermark→FATAL, or missing stats route | `blocked` | No B-1b candidate verdict; fix baseline/harness/environment first |
| cache-on candidate has any failed reclaim/unload or unresolved barrier event | `failed` | Preserve candidate ledger; do not rerun silently to wash out failure |
| cache-on warm hit missing in any round | `failed` | Candidate did not test `cache=on`; inspect session id/header/env path |
| cache-on `drops_delta > 0` | `failed` | Cache lifecycle interfered with unload path; root-cause in separate round |
| candidate duration p50/p99 exceeds threshold | `failed` | No-regress claim not met, even if failed count is zero |
| candidate-only missing reclaim signals | `failed` | Signal regression is a no-regress failure |
| harness crash before both N=20 ledgers complete | `blocked` | Tooling failure, not runtime pass/fail; fix harness and rerun from round 1 |
| watermark→FATAL in any round | `failed` for candidate, `blocked` for baseline | Stop immediately, keep partial ledger, do not continue into B-1c |

Passing B-1b means only:

```yaml
cache_on_no_regress: passed
```

It does **not** mean:

- `no_swap_soak_stability = passed`
- `soak_plus_swap_stability = passed`
- session KV cache is `supported`
- native backend is default-ready

---

## 7. Acceptance Checklist（review 用）

- [ ] B-1a closeout evidence paths are linked and not rewritten
- [ ] Scope is limited to `cache=on` × settle barrier N=20 no-regress
- [ ] N=20 is defined as 20 operation-boundary rounds per mode
- [ ] cache-off baseline and cache-on candidate each have independent ledgers
- [ ] pass/fail YAML exposes `cache_on_no_regress = passed | failed`
- [ ] `failed_reclaim = 0` is grounded in both event state and stats summary
- [ ] distribution alignment covers p50 / p99 / failed counts / missing signals
- [ ] failure semantics distinguish `failed` from `blocked`
- [ ] harness changes are script-only or test-only; no new `owlmlx/` spec module
- [ ] B-1c §1 / §2 remain explicitly out of scope

---

## 8. 后续 Round 预告（不在本 spec 范围）

| 顺序 | Work | 启动条件 |
|---|---|---|
| 1 | B-1b design-grade review | this spec lands |
| 2 | code-grade harness implementation | review + user sign-off |
| 3 | cache-off N=20 baseline run | harness passes smoke |
| 4 | cache-on N=20 candidate run | baseline clean |
| 5 | B-1b verdict + ledger commit | both ledgers complete |
| 6 | B-1c §1 design/code/run | `cache_on_no_regress = passed` |
