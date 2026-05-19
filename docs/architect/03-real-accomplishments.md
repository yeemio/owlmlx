# owlmlx 已完成真实情况与数据对比

> **文档 grade**：plan-grade · 见 [README.md](README.md)
> **配套**：[01-mainline-roadmap.md](01-mainline-roadmap.md) / [02-state-vs-market-gap.md](02-state-vs-market-gap.md) / [04-architecture-canvas.md](04-architecture-canvas.md)
> **日期**：2026-05-16
> **视角**：架构师诚实清单。所有数据点均来自 `docs/source-of-truth/runtime-capability-matrix.md`、`README.md`、`files/evidence/`、git log 与近期 commit，**不引用未经证据支持的能力**。

---

## 0. 阅读约定

- 每项给出：**做了什么 + 证据出处 + 状态标签**
- 状态标签：`supported` / `partial` / `experimental` / `not in scope`
- 数据点必引用：测试文件、evidence 目录、commit hash 或 contract 文档
- **不写"可能"、"未来会"、"应该是"** —— 只写已发生的事实

---

## 1. 代码规模盘点

| 项 | 数据 | 出处 |
|---|---|---|
| owlmlx/ 顶层 Python 模块 | 40+ | 代码扫描 |
| owlmlx/runtime/ 子模块 | 14 文件 | 代码扫描 |
| 主要文件 LOC | server.py 2013（Wave H H1 后）/ server_routes_openai.py 829 / kernel.py 1694 / mlx_lm_subprocess_backend.py 2541 / mlx_native_backend.py 1074 / comparative_evidence_runner.py 41K / runtime_monitor_test_console.py 46K | 代码扫描 |
| 测试规模 | 73 test files / 835 test_ functions | `tests/` |
| 测试运行时 | ~38s | README.md "1005 cases, ~38 s" |
| source-of-truth 文档 | 200+ markdown files | `docs/source-of-truth/` ls |
| Python 版本 | 3.11.15 (pinned via .python-version) | README.md |
| 项目依赖 (runtime extra) | mlx>=0.22.0, mlx-lm>=0.22.0, fastapi>=0.115.0, uvicorn[standard]>=0.34.0 | pyproject.toml |

---

## 2. Stage 1/2/3 清理与对齐成果

| 项 | 数据 | 出处 |
|---|---|---|
| Stage 1 (2026-05-11) 下架 spec-as-code | **151 个模块 / 31K LOC** | AGENTS.md + commit `a6d32665` |
| 反规模化 CI 禁令 | 11 类命名模式（`*_exactness` / `*_carrier` / `*_marker` / `*_harness` / `*_feasibility` / `*_rung` / `*_seam` / `*_charter` / `*_manifest` / `*_evidence` / `*_ledger`） | AGENTS.md + `.github/workflows/self-banned-modules.yml` |
| 唯二 grandfathered live history 模块 | `comparative_evidence_history.py` / `model_release_candidate_history.py` | AGENTS.md |
| Stage 2 (2026-05-12) PR #649 对齐 | MemoryWatermark + SettleBarrierEvent + pre_load_check 进 supported | commit `48d42004` + runtime-capability-matrix.md |
| Release channel 分裂 | owlmlx 工程版 ≠ OwlCoda 消费就绪 gate | commit `a21a0a2c` + `public-release-standard.md` |
| Stage 3.1 capability-matrix 刷新 | drop archived-module rows + add Stage 2 vocabulary | commit `16962d27` |
| Stage 3.2 Track A | system-architecture independence diagram；extraction-inventory swap-safe rows → external legacy | commits `f19a09dd`、`5f2c487b`、`59b5979d` |

---

## 3. Runtime 核心能力 supported 清单

> 来源：`docs/source-of-truth/runtime-capability-matrix.md`（2026-05-12 Stage 3.1 c1）

### 3.1 内核与执行

| 能力 | 标签 | 关键证据 |
|---|---|---|
| Executable runtime kernel MVP | `supported` | RuntimeKernel + RuntimeBackend + FakeBackend + MlxLmBackend + 最小 HTTP app；Runtime-2 扩展到 persistent child MLX session |
| Queue-based generation gate | `supported` | `owlmlx/serving.py` GenerationGate；11 tests；`MAX_GENERATION_CONCURRENCY=1` |
| Real MLX model load/generate | `supported` | MlxLmSubprocessBackend 在 `.runtime1-mlx` 上 smoke 通过：`gpt-oss-20b-MXFP4-Q4`、`Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit`、`Qwen3.5-35B-A3B-4bit` |
| Persistent child reuse | `supported` | Runtime-2 同 pid 连续 generate 通过 |
| Steady-state benchmark | 数据 | gpt-oss-20b load ≈ 1.49s、warm median ≈ 0.157s |
| Serialized serving | `supported` | 并发 2 请求保持 serial gate |
| Real streaming (NDJSON) | `supported` | TTFT ≈ 0.218s 实测，POST /v1/generate/stream |
| Dead-child restart policy | `supported` | registration 存活；下一请求 restart |

### 3.2 Memory governance（PR #649 对齐）

| 能力 | 标签 | 关键证据 |
|---|---|---|
| Memory watermark（4 级） | `supported` | `owlmlx/memory_watermark.py`；32 tests；GREEN < 65% < YELLOW < 80% < RED < 90% < FATAL |
| Settle barrier event | `supported` | `owlmlx/settle_barrier_event.py` + `GET /v1/runtime/reclaim-barrier-event` |
| Reclaim barrier stats surface | `supported` | `RuntimeKernel.reclaim_barrier_stats()` + `GET /v1/runtime/reclaim-barrier-event/stats`；commit `6141d134` 2026-05-16 |
| Non-resident admission via pre_load_check | `supported` | PR #649-shaped；admit_and_load / defer / reject / unknown |
| Memory budget truth | `supported` | `owlmlx/memory_budget.py`；32 tests |

### 3.3 Multi-model lifecycle

| 能力 | 标签 | 关键证据 |
|---|---|---|
| Pin / Unpin | `supported` | RuntimeKernel.pin_model() / unpin_model()；pin 状态过 restart 存活 |
| TTL 与 sweep | `supported` | set_model_ttl / clear_model_ttl / sweep_expired_models |
| Eviction history | `supported` | runtime-owned；同时记录 TTL unload 与 pinned-expiry skip |
| Model inventory | `supported` | `owlmlx/model_inventory.py`；18 tests |
| Model lineage | `supported` | `owlmlx/model_lineage.py`；22 tests |

### 3.4 Status & Provenance surface

| 端点 | 标签 |
|---|---|
| `GET /healthz` | `supported` |
| `GET /v1/runtime/status` | `supported`（frozen contract） |
| `GET /v1/runtime/orchestration-status` | `supported` |
| `GET /v1/runtime/memory-watermark` | `supported` |
| `GET /v1/runtime/reclaim-barrier-event[/stats]` | `supported`（commit `6141d134`） |
| `GET /v1/runtime/recovery-supervisor-contract` | `supported` |
| `GET /v1/runtime/request-context-length-truth` | `supported` |
| `GET /v1/runtime/model-visibility` | `supported` |
| `GET /v1/openai/models` / `GET /v1/models` | `supported` |
| `POST /v1/runtime/restart` | `supported` |

### 3.5 API 兼容性

| 兼容层 | 标签 |
|---|---|
| OpenAI `/v1/chat/completions`（含 SSE） | `supported` |
| OpenAI `/v1/completions` | `supported` |
| OpenAI `/v1/embeddings` | `supported` |
| Anthropic `/v1/messages` | `supported` |
| Anthropic `/v1/messages/count_tokens` | `supported` |
| OwlCC consumer cutover | `supported`（Runtime-7） |
| OwlCoda native cutover | `supported`（Runtime-8） |
| Source-first OwlCoda cutover | `supported`（Runtime-9） |
| Source-first tool-loop parity | `partial`（Runtime-10） |

---

## 4. Experimental 能力清单（scaffold / probe · 未晋级）

| 能力 | 标签 | 关键证据 |
|---|---|---|
| Native MLX backend (in-process) | `experimental` | `owlmlx/runtime/mlx_native_backend.py` 1074 行；server.py:2088 `"scope": "native_backend_explicit_session_id_only"` |
| Session-scoped native KV cache | `experimental` | `owlmlx/session_kv_cache.py` + `MlxNativeBackend`；env `OWLMLX_SESSION_CACHE_ENABLED=1` + header `X-Owlmlx-Session-Id` 双门 |
| DeepSeek-V4-Flash 2bit-DQ adapter | `experimental` | 隔离 `.runtime-deepseek-v4-mlx` venv；D1/D2 passed；D3 MTP absent/stripped；D4 clean pre-load reject passed |
| Bounded pre-gate admission ingress seam | `experimental` | `owlmlx/serving.py` |
| Gemma 4 MTP drafter probe | `experimental` | `owlmlx/gemma4_mtp_drafter.py` CLI wrap |
| Overflow / NVMe-tier execution path | `experimental` | Hypura 列为 external reference |
| High-fidelity teacher / reference runtime path | `experimental` | Gemma 已转 production mainline |

---

## 5. 真实数据对比（performance + evidence）

> **主叙事重组（2026-05-16 校准）**：
> runtime engineering mainline 的核心证据 = **① Session KV TTFT 提升 / ② 模型切换 reclaim 干净 / ③ 长上线稳定 / ④ 队列尾延迟**。
> 短提示 TPS（旧 §5.2）是 README 工程噪音，**不是 runtime mainline 主叙事**——保留作为附录但不再作为主推数据。
> Wave G 的 README 刷新会把 README "Short-prompt TPS on Mac17,6" 段降到附录或移除。

### 5.0 四主证据全景

| # | 主证据 | 状态 | 关键数据 / Gap |
|---|---|---|---|
| **①** Session KV TTFT 提升 | ✅ 已实证（Qwen3.6-27B-4bit, 7.409×；Gemma 4-31B-it, 2.246×） | 见 §5.1；supported gate 已过 B-1a + B-1b，待 B-1c §1 / B-1c §2 |
| **②** 模型切换 reclaim 干净 | 🟡 部分实证（settle barrier + reclaim stats supported；B-1b cache-on no-regress 已过） | 见 §5.2 |
| **③** 长上线稳定（48h+ 两段 soak） | 🔴 **缺** —— B-1c §1 runner 已具备 24h/native-only graduation guard 与 interrupted rehearsal aggregation；短 native rehearsal 已证明 TTL 需锁定，但无 24h+ 真实 soak 报告 | 见 §5.3；Campaign B-1c §1 + §2 |
| **④** 队列尾延迟（p50/p99/p99.9） | 🔴 **缺** —— GenerationGate supported；serial 已证；N 并发下分布未公开 | 见 §5.4 |

### 5.1 ✅ 主证据 ① · Session KV cache TTFT 实测（Qwen + Gemma）

> 出处：
> `files/evidence/owlmlx/bench/session-kv-cache/20260512T123316Z-owlmlx-native-session-kv-ttft-n4.jsonl` +
> `files/evidence/owlmlx/bench/session-kv-cache/20260516T151100Z-b1a-gemma4-31b-it-session-kv-ttft.jsonl` +
> README.md Session KV evidence 表

| 模型 / 配置 | Warm round-2 TTFT | Warm round-3 TTFT | Warm round-4 TTFT | p50 提升 |
|---|---:|---:|---:|---:|
| Qwen3.6-27B-4bit disabled | 3397.977 ms | 4026.099 ms | 4419.626 ms | — |
| Qwen3.6-27B-4bit enabled | 536.325 ms | **543.389 ms** | 652.471 ms | **7.409×** |
| Gemma 4-31B-it disabled | 1542.972 ms | 1558.077 ms | 1537.596 ms | — |
| Gemma 4-31B-it enabled | 679.811 ms | **687.102 ms** | 695.413 ms | **2.246×** |

- **提升倍率公式**：`disabled.warm_p50_first_token_ms / enabled.warm_p50_first_token_ms`
- Qwen 命中：**3 hit / 0 drop**
- Gemma B-1a 命中：**3 hit / 0 drop**，`RuntimeKernel.restart_model()` 子探针 completed
- 提示形态：~4.2k chars、append-only、4 rounds
- 标签维持 `experimental`：native backend only、default off、显式 session id、append-only reuse

### 5.2 🟡 主证据 ② · 模型切换 reclaim 干净

> 出处：runtime-capability-matrix §3.2 + commit `6141d134` reclaim barrier stats surface (2026-05-16)

**已实装 supported**：

- `owlmlx/memory_watermark.py`（PR #649 four-level；32 tests）
- `owlmlx/settle_barrier_event.py` + `GET /v1/runtime/reclaim-barrier-event`
- `RuntimeKernel.reclaim_barrier_stats()` + `GET /v1/runtime/reclaim-barrier-event/stats`：unload-boundary duration 与 backend-reported reclaim 分布
- `pre_load_check` 四值 verdict

**新增 B-1b no-regress 证据（2026-05-17）**：

- Evidence:
  `files/evidence/owlmlx/bench/cache-settle-no-regress/20260517T013342Z-b1b-gemma-4-31B-it-cache-on-no-regress-rollup.jsonl`
- Gemma 4-31B-it native cache-off baseline：N=20
- Gemma 4-31B-it native cache-on candidate：N=20
- cache-on warm hits：20/20
- `failed_reclaim_events_total = 0`
- `failed_unload_events_total = 0`
- `failure_measurement_count = 0`
- settle duration alignment：baseline p50/p99 = 1065.832 / 1115.409 ms；candidate p50/p99 = 1055.574 / 1473.198 ms；p50/p99 within threshold

**当前缺**：

- 模型切换（A→B→A）序列下累计 reclaim 漂移未公开（Campaign B-1c §2 gate）

### 5.3 🔴 主证据 ③ · 长上线稳定（48h+ 两段 soak · 缺）

**当前状态**：

- `scripts/bench/eviction_soak.py` 已从 placeholder 切到 owlmlx-first soak runner（commit `6b0c1bfd`），并已具备 B-1c §1 interrupted rehearsal aggregation
- 2026-05-17 短 native rehearsal 暴露默认 60s TTL 会在 measurement 内触发 session cache expiration，从而造成 237–247MB active-memory 摆动；runner 已锁定 B-1c TTL，随后 121s native segment 记录 `max_drift_bytes=0`、`session_cache_expirations_total=0`、clean unload，但因 duration 不足仍正确保持 `blocked`
- 2026-05-17 4h TTL-locked native rehearsal (`20260517T090114Z`) 记录 `measurement_duration_s=14401.581`、`measurement_samples=235`、短/中/长 prompt mix `79/78/78`、`max_drift_bytes=0`、session cache expiration/drop/reject 全 0、FATAL 0、unresolved reclaim barrier 0、cleanup unload OK、settle 后 active memory 28 bytes；因 required duration 仍为 24h，`no_swap_soak_stability=blocked`，不产生 supported graduation claim
- 2026-05-17 planned-shutdown segment (`20260517T132938Z`) 通过 SIGTERM graceful stop 落盘：`measurement_duration_s=9988.399`、`measurement_samples=161`、短/中/长 prompt mix `54/54/53`、`max_drift_bytes=0`、session cache expiration/drop/reject 全 0、FATAL 0、unresolved reclaim barrier 0、cleanup unload OK、settle 后 active memory 28 bytes；与 4h segment 聚合为 `20260517T161707Z` interrupted rehearsal，合计 `24389.98s`、`all_segments_ok_for_rehearsal=true`、仍 `blocked`
- 2026-05-18 continuous-24h attempt (`20260518T004835Z`) 因 host sleep / power gap + planned stop 只能入账为 interrupted segment：raw rollup 记录 `measurement_duration_s=9315.302`、`measurement_samples=152`、短/中/长 prompt mix `51/51/50`、`max_drift_bytes=0`、session cache expiration/drop/reject 全 0、FATAL 0、unresolved reclaim barrier 0、cleanup unload OK、settle 后 active memory 28 bytes；人工复核 ledger timestamp 发现 measurement wall-clock gap：sample 136→137 gap `2974.612s`、sample 146→147 gap `726.108s`，因此该段保持 `blocked`，不计入 continuous 24h graduation
- 2026-05-19 runner 已补 `measurement_wall_clock_gap_free` / `wall_clock_continuity` rollup 字段，后续 24h run 必须同时满足 ledger index 连续与 measurement wall-clock 连续
- 2026-05-19 用户校准：当前 Mac / laptop 环境**肯定会中断**，因此 B-1c §1 当前路线改为可中断分段累计 ≥24h；continuous 24h 保留为 dedicated host / UPS 的更强证据，不再作为当前机器上的默认期待
- 2026-05-19 planned-stop native segment (`20260519T014912Z`) 通过 SIGTERM graceful stop 落盘：`measurement_duration_s=28245.605`、`measurement_samples=461`、短/中/长 prompt mix `154/154/153`、`measurement_wall_clock_gap_free=true`、最大 measurement wall-clock gap `66.922s`、`max_drift_bytes=0`、session cache expiration/drop/reject 全 0、FATAL 0、unresolved reclaim barrier 0、cleanup unload OK、settle 后 active memory 28 bytes；aggregate `20260519T094117Z` 因累计 `28245.605s < 86400s` 正确保持 `blocked`
- 2026-05-19 B-1c §2 fake/schema runner 已落：可生成 `b1c2-soak-plus-swap` / `b1c2-interrupted-soak-plus-swap` schema、swap phase 与 prerequisite guard；这只是 code/schema readiness，不是 native §2 evidence
- 但 **无 24h+ operator-interruptible aggregate 报告**——`active_memory` 漂移、`failed_reclaim`、watermark 跃迁、ledger index 连续性、segment 内 wall-clock 连续性等关键指标尚未聚合通过

**晋级 gate · 两段 48h+ 拆分（决策 D3 · 2026-05-16）**：

| 段 | 时长 | 内容 | 干预 | 验收 | 结论字段 |
|---|---|---|---|---|---|
| **B-1c §1 · 纯 soak** | 当前 Mac：可中断分段累计 ≥24h；dedicated host：可追加 continuous ≥24h | 混合负载（短/中/长 session = 1:1:1） | **无人为 swap** | 每段 `active_memory` 漂移 < `min(200 MB, 0.5% host budget)` + 中途无 watermark→FATAL + `failed_reclaim = 0` + ledger index 连续 + segment 内 measurement wall-clock 无 host sleep / power gap；aggregate 总时长 ≥24h | `interrupted_no_swap_rehearsal = passed \| failed \| blocked`；dedicated host 才可产出 `no_swap_soak_stability = passed \| failed` |
| **B-1c §2 · soak + swap** | ≥24h（§1 通过后启动） | 同 §1 混合负载 | 每 4h × 6 次 Qwen3.6-27B ↔ Gemma 4-31B ↔ Qwen3.6-35B-A3B 轮换 | 每次 swap settle_barrier 通过 + 累积 `failed_reclaim = 0` + 漂移 < §1 阈值 + 任意 swap 触发 FATAL 即整 §2 失败 | `soak_plus_swap_stability = passed \| failed` |

**结论独立陈述纪律（用户校准 2026-05-16）**：

- **§1 与 §2 必须独立陈述**，**不**能合成 "48h soak passed"
- **§2 失败不撤销 §1**：当前 Mac 的 `interrupted_no_swap_rehearsal = passed` 或 dedicated host / UPS 的 `no_swap_soak_stability = passed` 作为独立事实保留
- 但 supported / release gate **不能 graduate**：gate 要求 §1 + §2 **同时** passed 且经 §1a Promotion Gate

**编排纪律**：

- 当前 Mac 路线达到 `interrupted_no_swap_rehearsal = passed` 且 `current_mac_section_1_prerequisite_met = true` 后才启动 §2 native execution；dedicated host / UPS 的 `no_swap_soak_stability = passed` 只是更强证据
- §1 与 §2 各自产出**独立 ledger**，不混合（防归因混淆，R14）
- 总占用 ≥48h host 时间，建议夜间 / 周末启动

**这是 Session KV cache 从 `experimental` → `supported` 的最强 gate**。也是 RC2 间接支撑。

### 5.4 🔴 主证据 ④ · 队列尾延迟（缺）

**当前状态**：

- `GenerationGate`（`MAX_GENERATION_CONCURRENCY = 1`）已 supported；serialized concurrent serving 已通过 `scripts/runtime3_serialized_concurrency_check.py` 证明
- 但 **N 并发下 p50 / p99 / p99.9 分布未公开**——只有"serial gate 保持"的二值结论，没有尾延迟数据

**待补**：

- N≥20 重复 + 并发 N=2 / N=4 / N=8 下的 TTFT 与端到端 latency 分布
- 与 Campaign A repeatability harness 联动产出
- 公开为 `/v1/runtime/*` 端点或 ledger 字段，供 OwlOps 消费

### 5.5 工程对比噪音（非主叙事 · 已降权）

> 出处：README.md:91–98
> **状态**：保留作为附录引用；**不再作为主推数据**。Wave G README 刷新会把它从亮点降为附录或移除。

短提示 TPS on Mac17,6（max_tokens=64，temperature=0）：

| 模型 | owlmlx tok/s | 参考 runtime tok/s | 参考 runtime |
|---|---:|---:|---|
| Qwen3.6-27B | 5.45 | 2.81 | oMLX |
| Qwen3.6-35B-A3B | 3.53 | 2.44 | oMLX |
| Gemma 4 | 3.75 | 3.83 | vMLX |

**为什么降权**：

- 短提示是工程对比噪音，不反映 runtime mainline 的核心命题
- 与 vMLX 在 Gemma 4 上基本持平，不构成差异化
- README 把它当亮点会**误导外部对 owlmlx 战略价值的判断**——价值不在 raw throughput

### 5.6 Session KV cache `supported` gate 四条状态（明确 · 当前 2/4）

> 对应 Campaign B-1a / B-1b / B-1c §1 / B-1c §2

| Gate | 状态 | 缺什么 |
|---|---|---|
| **B-1a · 第二模型 / 第二形状** | ✅ | Gemma 4-31B-it 已复现 session KV warm TTFT 改善（2.246×，RuntimeKernel 路径）+ 非 cache 路径 N≥5 prompt 字节等价；§VI 4-gate G1 Cache Parity 已关闭 |
| **B-1b · `cache=on` × settle barrier 无回归** | ✅ | Gemma 4-31B-it cache-off N=20 / cache-on N=20 passed；20/20 warm hits；`failed_reclaim=0`；cache=off 基线对齐 |
| **B-1c §1 · 纯 soak（24h+）** | ❌ | runner 已落且 fake/schema smoke 不可毕业；4h + planned-shutdown native interrupted rehearsal 合计 24389.98s 干净但仍为 `blocked`；2026-05-18 continuous-24h attempt 因 host sleep / power gap 出现 `2974.612s` measurement wall-clock gap，只能作为 interrupted segment；2026-05-19 clean planned-stop segment 28245.605s / wall-clock gap free / max drift 0，aggregate 仍 `blocked`；当前 Mac 路线改为可中断分段累计 ≥24h，仍缺 aggregate `interrupted_no_swap_rehearsal = passed` |
| **B-1c §2 · soak + swap（24h+）** | ❌ | fake/schema runner 已落但 native evidence 未启动；§1 通过后；每 4h × 6 次 swap；累积 `failed_reclaim = 0` + 漂移 < §1 阈值；`soak_plus_swap_stability = passed` |

**四条全过** → §1a Promotion Gate → `experimental` 升 `supported`。当前 2/4 达成。

**晋级越级红线**：

- 不允许"§1 §2 合并跑 36h"假装通过 48h
- 不允许"§1 失败重启后接续 §2"——§1 失败时 §2 必须重头
- 不允许"B-1a 跳过字节等价检查"（与 §VI G1 互锁）
- 不允许把 current-Mac `interrupted_no_swap_rehearsal = passed` 或 dedicated `no_swap_soak_stability = passed` 当作整个 B-1c 通过——必须 §1 + §2 都 passed 才 graduate

### 5.7 DeepSeek-V4-Flash 2bit-DQ 隔离短烟测（附录数据）

> 出处：`docs/source-of-truth/deepseek-v4-bring-up-status.md` + `ds4-mtp-local-llm-stack-research.zh-20260514.md` §3.1

| 指标 | 值 |
|---|---:|
| Artifact 大小（index） | ~96.5 GB |
| 总参数 | 284.3 B |
| 峰值 RSS | **96.574 GB** |
| Generation throughput | **33.706 tokens/sec** |
| 路径 | `.runtime-deepseek-v4-mlx` 隔离 venv + DeepSeek V4 PR branch |
| Stock mlx-lm 含 deepseek_v4.py | 当时 **不含** |
| 4bit artifact 行为 | **exit 137** |

注：这条早期峰值 RSS 使用的是短烟测内存口径；D2 metrics ledger 的
`child_rss_gb` 是生成后、卸载前对子进程的单点 RSS 样本。两者 scope / timing
不同，不能直接当作同一种内存指标比较。

- 严格维持 `experimental`：依赖 PR runtime、未闭环 repeated serving、未闭环 long output、MTP 权重检查未做
- 不进入 default `GET /v1/openai/models`

#### D1 p1 token-ladder diagnostic（2026-05-17）

> 出处：`files/evidence/owlmlx/deepseek-v4/d1-isolated-repeatability/`

| Run | 参数 | 结果 | 关键观察 |
|---|---|---|---|
| `20260517T-d1-p1-token-ladder-continue.jsonl` | p1 · 128/512/1024 · default `max_kv_size=512` · `continue_on_failure` | 128/512 passed；1024 failed | 1024 `repetition_flag=true`；`max_repeated_window_count=4`；load/unload/clean-health all true |
| `20260517T-d1-p1-1024-sampler-diagnostic.jsonl` | p1 · 1024 · `temp=0.2` · `top_p=0.9` · `top_k=40` | failed | sampler variant still repeats；not just deterministic temp=0 behavior |
| `20260517T-d1-p1-1024-kv2048-diagnostic.jsonl` | p1 · 1024 · `max_kv_size=2048` | failed | same repeated-window hash as default 1024; not cleared by larger KV window |
| `20260517T-d1-p5-1024-stop-diagnostic.jsonl` | p5 · 1024 · `stop=["<END>"]` | failed | stop-marker prompt still repeats; repeated-window count 9; clean lifecycle remains true |
| `20260517T-d1-p1-1024-direct-vs-runner.jsonl` | p1 · 1024 · direct `mlx_lm.generate` vs owlmlx runner | diagnostic failed | `classification=adapter_or_artifact_likely`; direct and runner produced the same `completion_sha256=40070e0a...` and repeated-window hash `e4017c...`; runner lifecycle remained clean |
| `20260517T-d1-p1-1024-messages-surface-diagnostic.jsonl` | p1 · 1024 · `--prompt-surface messages` | passed | runner `generate_messages`; `completion_chars=330`; `repetition_flag=false`; clean lifecycle |
| `20260517T-d1-full-ladder-messages-surface-diagnostic.jsonl` | all 5 prompts · 128/512/1024 · `--prompt-surface messages` | passed | 15/15 passed; no repetition flags; load/unload/clean-health all true |
| `20260517T-d1-full-ladder-adopted-messages-policy.jsonl` | all 5 prompts · 128/512/1024 · default prompt policy | passed | adopted `messages` default; 15/15 passed; no repetition flags; load/unload/clean-health all true |

Current D1 boundary: D1 is passed for the isolated DeepSeek experimental lane
under the adopted `messages` / chat-template prompt policy. Raw prompt remains
documented as a diagnostic failure and does not define the D1 gate.

#### D2 metrics ladder（2026-05-17）

> 出处：`files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/`

| Run | 参数 | 结果 | 关键观察 |
|---|---|---|---|
| `20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl` | p1/p2/p4 · 128/512 · `messages` / `stream_generate_messages` | passed | 6/6 rows passed；`missing_metrics=[]`；TTFT p50 593.840ms；decode p50 38.17885 tok/s after first token；child RSS p50 7.214432GB |

Current D2 boundary: D2 is passed for this isolated experimental ladder, but it
does not make DeepSeek V4 supported or visible on the default model surface.

#### D3 checkpoint / MTP inspection（2026-05-17）

> 出处：`files/evidence/owlmlx/deepseek-v4/d3-checkpoint-inspection/`

| Run | 参数 | 结果 | 关键观察 |
|---|---|---|---|
| `20260517T-d3-mtp-checkpoint-inspection.jsonl` | local artifact metadata inspection | passed | `num_nextn_predict_layers=1`；2610 weight keys / 19 shards；MTP key candidates = 0；extra layer keys = 0；`missingReason=mtp_weights_absent_or_stripped` |

Current D3 boundary: current local artifact has no usable MTP checkpoint path;
DeepSeek V4 stays `experimental_only`.

#### D4 clean pre-load reject / failure isolation（2026-05-17）

> 出处：`files/evidence/owlmlx/deepseek-v4/d4-preload-reject/`

| Run | 参数 | 结果 | 关键观察 |
|---|---|---|---|
| `20260517T-d4-mtp-clean-preload-reject.jsonl` | consume D3 inspection + probe 8066 `/healthz` before/after | passed | `decision=rejected_pre_load`；`reason_code=mtp_weights_absent_or_stripped`；`load_attempted=false`；`child_process_started=false`；`default_model_surface_changed=false`；runtime health stable |

Current D4 boundary: owlmlx cleanly rejects unavailable DeepSeek MTP before
load. This is not generation evidence and does not make DeepSeek V4 supported.

### 5.8 Gemma 4 MTP drafter probe（附录数据）

> 出处：`docs/source-of-truth/gemma4-mtp-drafter-probe-20260506.md`

| 指标 | 值 |
|---|---:|
| Target | `gemma-4-31B-it` |
| Drafter | `gemma-4-31B-it-assistant-bf16` |
| Adapter | `mlx-vlm 0.5.0` GitHub main probe |
| Acceptance smoke | **2.86 accepted tokens / 7 rounds** |
| A/B：MTP mean | 19949.029 ms |
| A/B：non-MTP mean | 22688.640 ms |
| 比值 | **0.8793**（约 12% wall-time 改善） |
| 形态 | fresh CLI per request，**不是** resident serving |

### 5.9 Heavy-weight repeatability（Gemma 4-31B-it · 附录数据）

> 出处：master-outline §8 + phase45-heavy-weight-repeatability-status.md

| 项 | 状态 |
|---|---|
| `owlmlx.heavy_weight_runtime_repeatability` | exists |
| 当前结果 | `supported_host_repeatability_visible` on this host |
| 原 Kimi heavy boundary | 冻结于 `122.0G > 116.0G`（不适合本机） |
| 已选 budget-fit heavy boundary | `gemma-4-31B-it` 进入成功，`62.0G <= 116.0G` |
| 重复运行证据 | 两次 default `~/.owlmlx` truth 下成功重复 |
| **N≥20 硬约束** | **当前未强制**（Campaign A 路线图） |

### 5.10 Steady-state benchmark（gpt-oss-20b-MXFP4-Q4 · 附录数据）

| 指标 | 值 |
|---|---:|
| Load 时间 | ≈ **1.49 s** |
| Warm median latency | ≈ **0.157 s** |
| Streaming TTFT | ≈ **0.218 s** |
| Serialized concurrent serving | 并发 2 请求保持 serial gate |

---

## 6. OwlOps consumption 实测情况

| 项 | 状态 |
|---|---|
| model-release-candidate ledger | **27 行 live** |
| comparative-evidence-history | live append-and-read |
| test-runs preflight / list / create | 端点 live |
| host_pressure sampling | RSS / CPU / throttle snapshot via psutil |
| runtime_monitor_test_console | 46K LOC functional |
| OwlOps observation closure proof | **done**（27-row ledger） |

---

## 7. Replacement readiness verdict（runtime-12 frozen）

| 项 | 状态 |
|---|---|
| Launch readiness | distinct truth via `doctor` |
| Replacement readiness | distinct truth via `doctor` |
| Old platform 替代 verdict | **`not yet replaceable`**（Runtime-9 frozen） |
| Doctor 输出 | explicit verdict + blocker list（Runtime-12 frozen） |
| Source-first prompt path | ✅ 通过 `owlcoda serve -> owlmlx /v1/messages` 执行 |
| Source-first tool loop | `partial`（Runtime-10 frozen） |
| Replacement closure | **未达成**——12+ 月路线图核心目标 |

---

## 8. Vue 子系统冻结情况（属于 OwlOps/OwlMom · 消费者锚点）

| 页面 | 状态 |
|---|---|
| batch/execute | ✅ FROZEN（reference page） |
| mbr/approval | ✅ FROZEN（reference page） |
| dashboard | ✅ FROZEN（Batch Workstation paradigm） |
| release | ✅ FROZEN（PROVENANCE chain） |
| report | ✅ STRUCTURE FROZEN（capability list + WHAT NEXT） |
| Goal Loop Round 03 状态 | All 5 pages in UI-True system ✓ / compile ✓ / build ✓ / SUCCESS DEFINITION MET |

---

## 9. 最近 5 周 commit 真实节奏（git log 节选）

| Commit | 日期 | 说明 |
|---|---|---|
| `6141d134` | 2026-05-16 | feat: add reclaim barrier stats surface |
| `453e8558` | 2026-05-12 | docs: clarify session kv ttft evidence |
| `d276bf33` | 2026-05-10 | perf: enable session kv suffix reuse |
| `62c4ce73` | 2026-05-10 | bench: add session kv cache ttft baseline |
| `fc27a021` | 2026-05-09 | feat: add experimental session kv cache |
| `bc91c535` | 2026-05-08 | chore: ignore runtime trend ledger |
| `8f45b20f` | 2026-05-08 | refactor: rename live contract modules |
| `6b0c1bfd` | 2026-05-08 | bench: add eviction soak baseline |
| `57a1c31f` | 2026-05-08 | perf: remove cohort wait and byte reads |
| `a21a0a2c` | 2026-05-12 | governance: split runtime release channel |
| `a6d32665` | 2026-05-11 | chore: retire spec scaffolds and rename histories |
| `48d42004` | 2026-05-12 | stage-2.1(c2/2): wire MemoryWatermark into runtime consumer path |
| `06a64196` | 2026-05-12 | stage-2.1(c1/2): archive 35 broken root scripts missed by Stage 1 |
| `00a871f9` | 2026-05-11 | stage-2(c4/5): rewrite README — drop oMLX/vMLX framing, headline watermark+settle |

**最近 5 周主线**：Stage 1/2/3 清理 → PR #649 对齐 → release channel 分裂 → cohort wait removed → session KV cache 立项 → TTFT baseline → suffix reuse → docs clarify → reclaim barrier stats surface

---

## 10. 一句话总结（按 2026-05-16 二次校准）

> **runtime mainline 实测可运行的核心能力**：
> ① Session KV TTFT **7.409×** 实证（Qwen3.6-27B-4bit，主证据 #1） +
> ② Memory governance PR #649 对齐 + reclaim barrier stats supported（主证据 #2 部分实证） +
> ③ OpenAI/Anthropic API 兼容 + persistent child MLX serving + 多模型 pin/TTL/eviction-history +
> ④ 27-row OwlOps ledger live + comparative_evidence_history live。
>
> **runtime mainline 实测尚未闭环**（路线图工作面）：
> ① Session KV cache supported gate **四条** 2/4（B-1a 第二模型已过；B-1b cache=on settle 无回归已过；待 B-1c §1 纯 soak + B-1c §2 soak+swap） +
> ② N≥20 host-stable repeatability + 队列尾延迟（主证据 #4） +
> ③ Qwen35 TTFT default warmup + DeepSeek V4 lifecycle + speculative path safety 正交矩阵 +
> ④ native backend 4-gate promote-path + `server.py` 工程化拆分（Wave H；H1 compat routes split 已落，H2/H3 未闭环）。
>
> **降权数据**：短提示 TPS（vs oMLX +45–94%、vs vMLX 持平）不是 runtime mainline 主叙事；Wave G README 刷新会降为附录。
>
> **Replacement verdict**：当前仍是 **not yet replaceable**——是 12+ 月路线图核心目标，最早合理 reopen 窗口 2026-11 ~ 2027-01。
