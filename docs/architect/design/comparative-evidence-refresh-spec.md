# Comparative-Evidence Refresh — Cold vs Warm, vs References — Design Spec

> 文档 grade：design-grade · 见 [README.md](README.md)
> Status：brainstorming-approved 2026-06-05 · pending user spec review
> Campaign：对标（comparative gap measurement）— owlmlx vs 上游参考 runtimes（oMLX / vMLX），**非** legacy `:8009`（见 §8）
> 上游契约：[`../../source-of-truth/comparative-evidence-harness-contract.md`](../../source-of-truth/comparative-evidence-harness-contract.md)（**冻结，本 campaign 不改**）
> Plan-grade 来源：[`runtime13`](../../source-of-truth/runtime13-replacement-rebaseline-verdict.md) §3 blocker ③（backend quality parity，demoted → no-regression）
> **停在测量；promotes nothing；§1a 不动；schema 禁词照守。**

---

## 0. 一句话

把 2026-04 的 comparative-evidence（owlmlx vs oMLX，gemma，`single_prompt_short`）**刷新成当前 owlmlx**（native 后端 + 2026-06 一批 serving 修复之后），并加一条**多轮复用**工况，产出一张诚实的**双轴差距地图**：冷态短 prompt（owlmlx 最差工况）vs 多轮复用（owlmlx cache 纪律真正发挥的现实 agentic 负载）。

---

## 1. 位置 + 验收口径

**为什么做**：runtime13 §3 blocker ③ 白纸黑字「**no formal parity-vs-legacy comparison**」；§4 throughput/concurrency「under-measured」。现有唯一的 measured 对标（`20260428T004500Z`）是 owlmlx vs oMLX 在 `single_prompt_short` 上 **owlmlx ~3.6× 慢**（0.1613 vs 0.5778 tok/s，RSS 59.8GB vs 53.8GB）。那是 owlmlx 的**冷态最差工况**（每请求冷启、零缓存复用），且数据已 6 周陈旧（native 后端 + 修复之后未复测）。

**验收**：对 gemma-4-31B-it，在两条 workload（`single_prompt_short` + `multi_prompt_serial`）上，对每个可用 reference（oMLX 为主、vMLX best-effort）产出现有契约的三态 verdict（`measured`/`inconclusive`/`rejected`）记录，落 ledger + 经现有 HTTP 端点可读；每条 record 带 N≥5 复跑的 mean + CV/方差（stable-label）。**禁词照守**（`parity`/`equivalent`/`matches`/`beats`/`replaces`/`superior`… 由 schema validator 强制）。**promotes nothing**，evidence-language 校准成「单 host、点测量、vs 上游参考」——**不是** parity / replacement / no-regression-closed 结论。

**这张图回答什么**：owlmlx 当前相对上游参考，在「冷态」差多少、在「现实多轮复用」差/领先多少。**不回答**「能不能替代 `:8009`」（那是 §8 范围外）。

---

## 2. 架构

**复用，不重造。** `comparative_evidence_runner.py` / `comparative_evidence_schema.py` / `comparative_evidence_record.py` / `comparative_evidence_history.py` / `/v1/runtime/comparative-evidence[/history]` HTTP 端点 —— **全部一行不改**。

**新增全在 `scripts/` + `tests/`**（守 AGENTS『模块即规格』纪律：不在 `owlmlx/` 下新建规格模块，也不扩冻结的 schema/runner）：
- per-(runtime × workload) 的 **wrapper driver** 脚本；
- 一个固定的**多轮 prompt set** + `prompt_set_hash`；
- 扩 `scripts/runtime_comparative_evidence.py` 加一条 `run-measured-multi-turn` operator 子命令（复用现有 `run-measured-short-prompt` 模式）。

runner 照旧：用 caller-supplied subprocess argv 跑 wrapper（`subprocess.Popen`），量 wall-clock / TTFT / RSS（常驻 server 的 RSS 经 runner 现有 `external_listener_ports` / `external_pids` 采）。`workload_class` 是 record 上的**标签**（runner 不据它改执行逻辑）——所以多轮工况完全由 wrapper 实现，runner 无需改。

---

## 3. 组件

### 3.1 Wrapper drivers（`scripts/`，新增）
每个 (runtime × workload) 一个可被 runner argv 调起的 driver，把一条 workload 跑成一次 attempt：读 prompt（或多轮序列）、打该 runtime 的 server、把生成结果写 stdout（供 runner 的 `tokens_method` / `first_token_strategy` 解析）。
- **owlmlx**：经 `:8066`；`multi_prompt_serial` 时跨请求带同一 `x-owlmlx-session-id`（触发 session-KV / prefix 复用）。
- **oMLX / vMLX**：经各自原生 server / **最佳**多轮路径（见 §3.3 公平契约）。

### 3.2 多轮 prompt set（`scripts/` 或 fixture，新增）
一段**现实 agentic 序列**——共享前缀、逐轮追加（如：read file → 基于其内容 edit → run → 基于报错 fix 的连续对话）。固定内容 → 固定 `prompt_set_hash` 做复现。`single_prompt_short` 复用现有 2026-04 prompt（保持与老 record 可比）。

### 3.3 公平契约（解读关键，写进每条 record 的复现元数据）
每个 runtime 走它**最好可用**的多轮/缓存路径。若某 reference **没有**复用机制 → 多轮工况下它就是 cache-vs-no-cache 的**真实产品差异**，如实记录（**不**叫 "beats"/"wins" —— schema 禁，且本就该诚实陈述为「该 runtime 在此工况无原生复用」）。reference 是否具备复用、用了哪条路径，必须写进 record 复现字段，否则 warm 轴不可解读。

### 3.4 Operator 入口（扩现有脚本）
`scripts/runtime_comparative_evidence.py` 加 `run-measured-multi-turn`（与现有 `run-measured-short-prompt` 同构：组 RuntimeRunnerConfig + WorkloadInputs，调 runner，落 record）。

---

## 4. 默认旋钮（spec review 时可调）

| 旋钮 | 默认 | 理由 |
|---|---|---|
| 模型 | `gemma-4-31B-it`（单模型 v1） | 2026-04 已证 oMLX 可稳测的对；62GB 适配单 host budget；保持紧凑 |
| 参考 | oMLX 为主 + vMLX best-effort | oMLX 有历史 measured 对；vMLX 历史爱 fail → 失败如实 `rejected`，不静默跳过 |
| N（每格） | 5 | 够出 stable-label（CV 阈值 TTFT≤0.30 / TPS≤0.20 / stable≤0.10；min-sample=5） |
| Workload | `single_prompt_short` + `multi_prompt_serial` | 冷态最差 + 现实复用，构成双轴 |
| Host | 当前单 host（Mac17,6-arm64-…-128GB） | 契约禁跨 host 晋级；与老 record 同 host_class 才可比 |

---

## 5. 数据流

operator 触发子命令 → wrapper 驱动 runtime（subprocess argv，N 次 attempt）→ runner 量 wall-clock/TTFT/RSS + 解析 tokens → 聚合 mean + CV/方差 → 打 `workload_class` 标签的 record（过 schema validator，含禁词检查）→ 现有 JSONL ledger（`OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH` 或显式路径）→ 现有 HTTP 端点可读。

---

## 6. 指标 + verdict

- **指标**（现有 6 个必填，不增不减）：`throughput_tokens_per_second`、`first_token_latency_ms`、`peak_resident_set_bytes`、`wall_clock_ms`、`completed_request_count`、`failure_count`(+causes)。
- **统计**：每格 mean + 现有 `repeatability_statistics` 的 stddev / CV / stability_label。**全套置信区间/效应量 = 范围外**（Approach 2，后续）。
- **verdict**：现有三态 `measured` / `inconclusive` / `rejected`（per 契约 §5）。reference 不可用/崩溃 → `rejected` + 冻结原因（非跳过）。
- **产出物**：一张「冷态短 prompt：owlmlx vs ref 差 X×；多轮复用：owlmlx vs ref 差/领先 Y×」的双轴地图，附 CV/stable-label 与每个 reference 的复用路径说明。

---

## 7. 错误处理 / 诚实

- reference 挂 / 非零退出 / 无 stdout → record `verdict_grade=rejected` + 冻结 reason（runner 既有行为，绝不伪造测量）。
- 单 host，**不跨 host 晋级**（契约禁）。
- **禁词**由 schema validator 强制；**promotes nothing**；§1a 不动。
- evidence-language 校准纪律：结论一律「单 host 点测量、vs 上游参考、特定模型/工况」；**绝不**写 parity / equivalent / replacement / no-regression-closed。
- 多轮工况若 reference 无复用，record 必须显式标注，避免被误读成 owlmlx「更快」是普适结论。

---

## 8. 范围外

- **vs legacy `:8009`**：契约把 reference 冻结为 oMLX/vMLX；加 `:8009` 要**重开契约**（§9）且 `:8009` 在 OwlCoda/OwlCC（跨 repo）——单独更大的 campaign。
- **CI / 效应量 / 显著性硬化**（Approach 2）。
- **differentiator sidecar**（reliability/provenance/governance/缓存复用加速比，Approach 3）。
- 任何 experimental→supported 晋级；跨 host 晋级；多模型矩阵（v1 单 gemma）。
- 改 runner / schema / record / ledger / HTTP 端点（全部冻结复用）。

---

## 9. Hard Rules

1. **复用冻结 harness**：runner / schema / record / ledger / HTTP 一行不改；新增只在 `scripts/` + `tests/`（AGENTS『模块即规格』纪律）。
2. **禁词 + promotes nothing**：schema validator 自动拦；结论 evidence-language 校准。
3. **公平契约**：每 runtime 走最佳可用多轮路径；reference 复用能力写进复现元数据。
4. **不伪造**：reference 失败 → `rejected` + 冻结 reason，绝不跳过/补值。
5. **重 bench 跑吃机器时间**（gemma 62GB + oMLX/vMLX 各自加载）→ 执行时 **surface 成本 + run-now-vs-defer**（先报机器成本纪律）。
6. **plan→code 切 fresh session**：本 spec + 其 implementation plan 是 plan-grade；实际 bench 代码 + 跑在 fresh session（fresh-session grade-transition 纪律）。
7. 单 host、与老 record 同 host_class 才与 2026-04 可比。

---

## 10. 验证（怎么算"做对"）

§1 验收满足 + 两条 workload × (oMLX 必、vMLX best-effort) 各落 record（measured 或诚实 rejected）+ N≥5 带 CV + 禁词零触发 + evidence-language 校准 + 无晋级 + runner/schema 零改动 + 双轴地图可复现（cmd · env · owlmlx commit · model id · prompt_set_hash · 各 reference 复用路径）。
