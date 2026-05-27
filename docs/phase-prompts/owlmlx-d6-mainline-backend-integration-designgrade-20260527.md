# Handoff · D6 Mainline Backend Integration · Design-Grade

> **Grade**: design-grade (NOT code-grade)
> **Mission**: write [`docs/architect/design/D6-mainline-backend-integration-spec.md`](../architect/design/) for owlmlx Campaign D upgrade
> **Plan-grade source**: [`docs/architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`](../architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md) (2026-05-27)
> **Status of this handoff**: prepared 2026-05-27 in the plan-grade session; should be picked up by a **fresh session** per [[feedback-fresh-session-grade-transitions]]
> **Language discipline**: this handoff does not claim D6 is implementable today; it defines what the D6 design-spec must answer before any code can be written

---

## 0. 给新 session 的开场指令

**You are the design-grade session for Campaign D6.** 你不依赖任何之前的对话。Plan-grade 已经 landed，feasibility probe 已经做完，所有决策已经在 plan 文档里固化。

你这个 session 的唯一产出：**[`docs/architect/design/D6-mainline-backend-integration-spec.md`](../architect/design/D6-mainline-backend-integration-spec.md)**

不要：
- 写 code（code-grade 是 design-spec 之后的 fresh session）
- 推进到 D5 / D7（D6 关键路径先，D5/D7 各自 fresh session）
- 重做 D1-D4 evidence（既有 evidence 全部 reuse 为 baseline，不重跑）
- 改变 plan-grade 的决策（plan-grade 已 frozen）
- 在 `owlmlx/` 包下新建 spec/validator 模块（per [[project-owlmlx-agents-module-as-spec-rule]]）

要：
- 严格遵守 owlmlx capability honesty 纪律（`experimental` / `partial` / `supported` / `technical_preview` 标签精确使用）
- design-spec 体例参考既有 D1-spec.md / D2-spec.md 的 8-12 节结构
- 所有 acceptance criteria 必须有具体数字 / 字符串 / yaml schema，**严禁 placeholder**
- evidence path 全部锚定到 `files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/`

---

## 1. Mission

D6 把 owlmlx DSV4-Flash 2bit-DQ 从"隔离 lane 跑得动"升级为"主线 backend 可消费"：

```text
当前状态（D1-D4 passed 后的现实）:
  - `.runtime-deepseek-v4-mlx/` 隔离 venv 通过 Blaizzy fork 跑得动
  - 通过 `scripts/bench/deepseek_v4_d1_repeatability.py` 隔离 harness 调用
  - 不走 `MlxLmSubprocessBackend` 主线 path
  - 在 `model_release_candidate_record.py` 标 `lane=flagship_experimental, visibility_status=not_registered`

D6 目标状态:
  - pyproject.toml 加 `deepseek-experimental` optional extras group
  - `MlxLmSubprocessBackend` 通过该 extras group 能 load DSV4-Flash 2bit-DQ
  - 真实 smoke 在 `tests/test_mlx_native_backend_real_smoke.py` (env-gated) 通过
  - 完整 lifecycle (load → generate → unload → clean health) 在 mainline backend path 上 evidence 产出
  - capability label 仍是 `experimental_only`（D6 单独不 promote 到 `partial`，需 D5+D6+D7 一起）
```

D5 (sustained load) 和 D7 (visibility) 都依赖 D6 的 backend path 存在。**D6 是关键路径**。

---

## 2. 必读文档（self-contained 入口）

新 session 必须在写 design-spec 前**完整读完**以下文档。括号里是为什么读：

### 2.1 Plan-grade（最高优先级）
- [`docs/architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`](../architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md)
  - **必读全文**。所有决策、scope、constraints、risks、non-goals 都在这里。design-spec 不能改变 plan-grade 的任何决策。

### 2.2 既有 D 系列 design-spec 体例参考
- [`docs/architect/design/D1-spec.md`](../architect/design/D1-spec.md) — D6 体例最接近 D1（lifecycle 验证）。看其 8 节结构 (Purpose / Scope / Run Shape / Evidence Schema / Harness Requirements / Failure Semantics / Review Checklist / Next Round)
- [`docs/architect/design/D2-spec.md`](../architect/design/D2-spec.md) — 看其 metrics ledger schema、`stream_generate_messages` 语义、stdout fd-buffered reader 经验

### 2.3 既有 DSV4 状态（D6 design 必须 reflect）
- [`docs/source-of-truth/deepseek-v4-bring-up-status.md`](../source-of-truth/deepseek-v4-bring-up-status.md) — 全文。特别关注：
  - §1 Current Status: D1-D4 verdict + 2026-05-11 single-cycle lifecycle 数据
  - §2 Upstream Dependency: Blaizzy fork 路径 + transformers fallback
  - §3.2 Intermediate Path (PR Branch): 就是 D6 要实施的 pyproject extras group 方案
  - §3.3 Memory Budget Constraint: 96-100GB peak unified memory（D6 不放宽）
  - §4 Blocked Scope: **当前禁止 visibility registration**。D6 不动这一条；D7 才动。
  - §5 Test Contract: 既有 `test_mlx_native_backend.py` reject 路径 + D4 MTP-specific 测试，D6 在 `test_mlx_native_backend_real_smoke.py` 加新 case

### 2.4 既有 D1-D4 evidence (复用 baseline)
- `files/evidence/owlmlx/deepseek-v4/d1-isolated-repeatability/20260517T-d1-full-ladder-adopted-messages-policy.jsonl`
- `files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl`
- `files/evidence/owlmlx/deepseek-v4/d3-checkpoint-inspection/20260517T-d3-mtp-checkpoint-inspection.jsonl`
- `files/evidence/owlmlx/deepseek-v4/d4-preload-reject/20260517T-d4-mtp-clean-preload-reject.jsonl`

只 grep / 不全读。D6 不重做这些 evidence，但 reference schema 字段。

### 2.5 既有 owlmlx 承载代码（design-spec 要 reference 的接触面）
- `owlmlx/runtime/mlx_lm_subprocess_backend.py` — D6 需要让这个 backend 能 load DSV4。读其 load path
- `owlmlx/runtime/backends.py` — backend Protocol 接口定义
- `owlmlx/model_release_candidate_record.py` 第 39-47 行 `DEFAULT_MODEL_RELEASE_CANDIDATES` 数据
- `tests/test_mlx_native_backend.py` — 既有 reject 路径 contract 测试
- `tests/test_mlx_native_backend_real_smoke.py` — D6 要在这里加 env-gated DSV4 case（**不增加新 test 文件**，扩展既有的）
- `scripts/bench/deepseek_v4_d1_repeatability.py` — D5/D6 共用基础 harness，看其当前 isolated harness 调用方式
- `pyproject.toml` — D6 要加 optional dependency group，看现有 extras 命名约定

### 2.6 Capability honesty 锚点
- [`docs/source-of-truth/runtime-capability-matrix.md`](../source-of-truth/runtime-capability-matrix.md) §6 Label Promotion Rules — D6 不 promote capability label
- [`docs/source-of-truth/public-claim-matrix.md`](../source-of-truth/public-claim-matrix.md) §3 — banned vocabulary 适用，D6 evidence 不含与 oMLX/vMLX 的 measured TPS 对比

---

## 3. Compressed Plan-Grade Context（避免新 session 还要 re-derive 决策）

以下是 plan-grade 的决策摘要。新 session 读完 plan-grade 后这一节是 cross-check：

### 3.1 用户决策（已 frozen，design-spec 不可改）
- **量化版本**: 仅 DSV4-Flash 2bit-DQ（~90GB，128G Mac 跑得动；4bit 141GB 跑不动）
- **覆盖范围**: 仅 Flash，不做 Pro
- **上游策略**: Blaizzy fork `pc/add-deepseekv4flash-model` commit `5c10538136b9038b9626c134612b08afc18d697a` + upstream watch
- **并行关系**: 与 F-4 并行，不互相阻塞
- **目标 visibility tier**: `technical_preview`（D7 之事），**严禁** `supported`

### 3.2 D6 与其他 stage 的关系
| Stage | 状态 | D6 对其依赖 |
|---|---|---|
| D1 isolated repeatability | passed 2026-05-17 | reference baseline |
| D2 metrics ledger | passed 2026-05-17 | reference baseline |
| D3 MTP checkpoint inspection | passed 2026-05-17 | closed，D6 不动 |
| D4 clean pre-load reject | passed 2026-05-17 | D6 之后 reject 路径仍保留作为 fallback |
| **D5 sustained-load N≥20** | not started | depends on D6 backend path |
| **D7 technical_preview visibility** | not started | depends on D5 + D6 |
| D8 MTP recovery | 远期 | not in scope of D6 plan |

### 3.3 D6 in-scope（必须在 design-spec 中覆盖）
- pyproject.toml `deepseek-experimental` extras group 定义
- `MlxLmSubprocessBackend` 通过该 extras group 加载 DSV4-Flash 2bit-DQ
- 在 `tests/test_mlx_native_backend_real_smoke.py` 加 env-gated DSV4 case
- 完整 lifecycle evidence (load / generate / unload / clean health) 在 mainline backend path 上记录
- backend_health snapshot 在 lifecycle 前后对比
- 与既有 D2 metrics ledger 的 cross-validation（同 prompt 在 isolated harness vs mainline backend 上 TTFT / decode TPS / RSS 不应有显著漂移；漂移阈值在 design-spec 中定义）

### 3.4 D6 out-of-scope（design-spec 不写、新 session 不做）
- N≥20 sustained load（D5 之事）
- visibility surface registration（D7 之事）
- MTP speculative on DSV4（D8 远期）
- DSV4-Pro / 4bit / 8bit
- 与 oMLX/vMLX 的 measured TPS 对比
- 修改 `deepseek-v4-bring-up-status.md §4 Blocked Scope`（D7 之事，D6 不动）
- 修改 mlx-lm upstream 或 transformers 上游
- 在 `owlmlx/` 包下新建 DSV4 specific spec/validator 模块

---

## 4. D6 Design-Spec 必含章节（参考 D1/D2 体例）

新 session 写出的 design-spec 至少包含以下章节。每节的内容标准如下：

### §1 Purpose
- D6 的精确 mission（参考本 handoff §1）
- 与 D1/D2 的关系（baseline reference but not re-running）
- Non-goal: D6 不 promote capability label 到 `partial`

### §2 Scope
- in / out 表（参考 D1-spec.md §2 / D2-spec.md §2 体例）
- 必须列：runtime environment / pyproject extras group / model artifact / prompt surface / generation surface / lifecycle phases / evidence path / capability label

### §3 pyproject Extras Group Definition
- `[project.optional-dependencies]` 下新增 `deepseek-experimental` 的精确定义
- 依赖路径示例（不必是最终值，但必须是 valid Python packaging）：
  ```toml
  deepseek-experimental = [
    "mlx-lm @ git+https://github.com/Blaizzy/mlx-lm@5c10538136b9038b9626c134612b08afc18d697a",
  ]
  ```
- 与既有 `runtime` extra 的隔离边界（**不进 default install**）
- 安装命令样例：`uv venv .runtime-deepseek-experimental --python 3.13` 后用
  `uv pip install --python .runtime-deepseek-experimental/bin/python <pinned mlx-lm fork>`；
  不使用 `uv sync --extra ... --python <target>`，避免 uv 项目 sync 重建正常 `.venv`
- transformers 5.7.0 fallback 是否需要 pin 在该 extra 内（由 design-spec 决定）

### §4 Backend Integration Surface
- `MlxLmSubprocessBackend` 加载 DSV4 的 call path（精确到方法名 / 关键参数）
- model_type=deepseek_v4 时的 import / fallback 行为（参考 deepseek-v4-bring-up-status.md §2：`importlib.util.find_spec(f"mlx_lm.models.{model_type}")`）
- 与既有 isolated harness `scripts/bench/deepseek_v4_d1_repeatability.py` 的关系：design-spec 明确"哪些 path mainline backend 走，哪些 path 仍在 isolated harness"
- 如果 mainline backend 需要扩展接口（如新增 model_type 探测 hook），design-spec 必须列出**精确改动位置**（file:line），不允许 placeholder

### §5 Lifecycle Run Shape
参考 D1-spec.md §3 体例：

```yaml
d6_run_shape:
  preflight:
    mainline_runtime_path: <精确 venv path>
    deepseek_experimental_extras_installed: true | false
    mlx_lm_source:
      origin: <module path>
      git_commit: <expected = 5c10538136b9038b9626c134612b08afc18d697a or null>
    backend_class: MlxLmSubprocessBackend
    model_artifact_path: ~/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ
  lifecycle:
    load:
      timeout_s: <设定值>
      max_load_time_s: <预期上界，参考 2026-05-11 数据 14.125s>
    generate:
      prompt_id: <复用 D1 五 prompts 中的哪个/几个>
      prompt_surface: messages
      generation_surface: stream_generate_messages
      max_tokens: <128 / 512 / 1024 中选一个>
    unload:
      timeout_s: <设定值>
      expected_freed_gb: <预期下界，参考 2026-05-11 数据 100GB>
    health:
      before_load: snapshot
      after_load: snapshot
      after_generate: snapshot
      after_unload: snapshot
```

### §6 Evidence Schema
参考 D2-spec.md §3 体例。每行 evidence record 必须包含：
- `schema_version: d6.mainline-backend.v1`
- `gate: D6`
- `backend_class: MlxLmSubprocessBackend`（明确**不是**隔离 harness）
- `deepseek_experimental_extras_active: true`
- `mlx_lm_source.git_commit: <commit hash>`
- backend_health snapshot 对比
- lifecycle metrics (load_time_s / ttft_ms / decode_tps / child_rss_gb)
- cross-validation diff vs D2 baseline（必须 < design-spec 中定义的漂移阈值）
- `verdict: passed | blocked | failed`

Evidence 落盘位置：`files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/<ts>-d6-<run-id>.jsonl`

### §7 Acceptance / Pass Criteria
- 完整 lifecycle (load / generate / unload / clean health) 在 mainline backend 通过
- backend_health 在 lifecycle 前后无污染（特别是 child process restart_observed=false）
- cross-validation 与 D2 baseline metrics 漂移在阈值内（设定值由 design-spec 定义；建议 ≤ 20% on TTFT, ≤ 15% on decode TPS, ≤ 1GB on child_rss_gb）
- `tests/test_mlx_native_backend_real_smoke.py` env-gated DSV4 case 通过
- pyproject extras group 单独安装可重现（在 clean fresh venv 上 reproducible）
- 不引入对既有 `runtime` extra 的 dependency 污染

### §8 Failure Semantics
参考 D1-spec.md §6 体例：

| Failure | Classification | Next action |
|---|---|---|
| Extras group install failed (Blaizzy fork unreachable) | `blocked` | upstream watch trigger; 切换候选 fork |
| `MlxLmSubprocessBackend` 无法识别 model_type=deepseek_v4 | `failed` | design-spec 中预设的 import fallback path 失效 |
| Lifecycle 中 child restart_observed=true | `failed` | record snapshot；不进 D6 promotion |
| Cross-validation metrics 超漂移阈值 | `failed` | 不 promote；记录 diff 进入下一 dominant gap |
| backend_health 污染 | `failed` | record；D4 reject path 是否仍可恢复 health 由 design-spec 评估 |
| 128G host 内存压力到 watermark RED | `blocked` | 不 fail，记录 watermark snapshot；这是 D5 之事，D6 单次 lifecycle 不应触发 |

### §9 Harness Requirements
参考 D1-spec.md §5 体例：

- 不在 `owlmlx/` 包下新建模块
- 复用 `scripts/bench/deepseek_v4_d1_repeatability.py`（D5/D6 共用）
- 新增 mainline backend execution mode（CLI flag 或 subcommand，design-spec 决定具体）
- 不增加 `*_contract.py` / `*_evidence.py` / `*_harness.py` / `*_ledger.py` 类型新模块
- 测试只扩展既有 `tests/test_mlx_native_backend_real_smoke.py`，不增加新 test 文件

### §10 Review Checklist
design-spec 末尾必须含 review checklist（参考 D1-spec.md §7）。条目至少包含：
- [ ] pyproject `deepseek-experimental` extras group 定义精确且不污染 `runtime` extra
- [ ] `MlxLmSubprocessBackend` load path 改动位置 file:line 精确
- [ ] Lifecycle run shape yaml schema 完整
- [ ] Evidence schema yaml schema 完整
- [ ] cross-validation 阈值数字明确（TTFT / decode TPS / RSS）
- [ ] Failure semantics 表格覆盖至少 6 种 failure mode
- [ ] 无 `owlmlx/` 包下新建 spec/validator 模块
- [ ] capability label 仍是 `experimental_only`（D6 单独不 promote）
- [ ] 无 measured TPS 对比 oMLX/vMLX
- [ ] 无 visibility surface registration（保留给 D7）

### §11 Next Round（D6 design-spec 落地后）
- code-grade fresh session 喂 D6-spec 进去，实施 pyproject + backend integration + test 扩展
- code-grade 完成后，evidence 落盘到 `files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/`
- D6 passed 后，启动 D5 design-grade（共用 backend path）
- D5 design-grade 落地后，启动 D5 code-grade
- D5 passed 后，启动 D7 design-grade
- D7 通过后，capability matrix update + sweep follow-up（按 plan-grade §13）

---

## 5. Hard Rules / 纪律（design-spec 必须 enforce）

下列每条都必须在 design-spec 中显式 reflect（不是隐含）：

1. **不上 `supported` tier**（D6 单独不 promote，D5+D6+D7 一起才 promote 到 `partial`，且 visibility 仅到 `technical_preview`）
2. **不主张 parity / replacement vs oMLX / vMLX**（[`public-claim-matrix.md`](../source-of-truth/public-claim-matrix.md) §3 banned vocabulary enforced）
3. **不写 code** (本次 session 是 design-grade，code 在下一轮 fresh session)
4. **不在 `owlmlx/` 包下新建 spec/validator 模块** (per [[project-owlmlx-agents-module-as-spec-rule]])
5. **不修改既有 D1-D4 evidence**（reuse 为 baseline，不重做）
6. **不修改 `deepseek-v4-bring-up-status.md` §4 Blocked Scope**（visibility 限制松绑是 D7 之事）
7. **不修改 mlx-lm upstream 或 transformers 上游**（继续走 Blaizzy fork + tokenizer fallback）
8. **不引入对 `runtime` extra 的污染**（`deepseek-experimental` 严格隔离）
9. **不主张 measured TPS 对比 oMLX/vMLX**（D6 evidence 不含 comparative ledger row）
10. **不假设 mlx-lm 主线会近期 merge native DSV4**（continue Blaizzy fork; upstream watch ledger 由 plan §9.3 维护）

---

## 6. Acceptance for This Handoff

新 session 完成 D6 design-spec 的 acceptance：

1. design-spec 落盘到 `docs/architect/design/D6-mainline-backend-integration-spec.md`
2. design-spec 至少含本 handoff §4 列出的 11 节
3. design-spec 中无 placeholder（无 "TBD" / "to be filled" / "similar to D1" / "see plan for details" 等推卸）
4. design-spec 中所有 yaml schema 完整可读
5. design-spec §10 Review Checklist 11 条全部具体（非 generic）
6. design-spec 通过 self-review（per superpowers:writing-plans 自查）
7. 不引入对本 handoff §5 Hard Rules 任一条的违背

design-spec landed 后，新 session 应该：
- 收口本 session
- 报告 design-spec 路径
- 提示下一步是 D6 code-grade fresh session（载体为 D6 design-spec）

---

## 7. 上一个 session 做了什么（context for this handoff）

2026-05-27 同一日内，上一个 session 完成了三件事：

1. **市场对比 refresh**：[`docs/source-of-truth/reference-runtime-comparison-matrix.md`](../source-of-truth/reference-runtime-comparison-matrix.md) 从 2026-05-06 capability surface 升级到 2026-05-27（§0.1 / §3 / §4 refresh-note / §8 / §9 全部 refresh）。新增 [`competitor-capability-matrix-20260527.md`](../source-of-truth/competitor-capability-matrix-20260527.md) 作为业界格局横扫（注意是 market-gap 视角，**不是** reference-runtime 视角）。
2. **DSV4 决策**：用户拍板 DSV4 为基础能力必须追，进路线图。确认 Flash only / 扩展既有 Campaign D / 2bit-DQ / 与 F-4 并行 / 目标 visibility = `technical_preview`。
3. **Feasibility probe**：验证 mlx-lm 上游状态（主线未 merge，6+ PR open）/ HuggingFace 2bit-DQ 本地已有 90GB / D1-D4 全 passed / 2026-05-11 single-cycle lifecycle 跑过。
4. **Plan-grade**：[`09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`](../architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md) landed，定义 D5/D6/D7 + 远期 D8/D9。

上一个 session 之所以**不直接推进到 D6 design-grade**，是因为 [[feedback-fresh-session-grade-transitions]] 纪律：plan → design 之间必须切 fresh session 避免连续叙事稀释 capability-honesty。

本 handoff 就是上一个 session 的最后产出，目标是让新 fresh session 能 self-contained 接力。

---

## 8. Plan-Grade 之后的并行工作（FYI，不在本 D6 session 范围）

- **F-4 code-grade**：[`docs/phase-prompts/owlmlx-f4-structured-output-invariance-codegrade-20260527.md`](owlmlx-f4-structured-output-invariance-codegrade-20260527.md) 已经 self-contained handoff，可任何 fresh session 拉起跑。F-4 与 D6 互相独立。
- **Sweep follow-up**：5 处 stale-language refresh（详见 plan-grade §13），独立一轮，不在 D6 session 范围。
- **mlx-lm upstream watch ledger**：plan-grade §9.3 建议新建 `docs/source-of-truth/mlx-lm-upstream-watch.md`，独立 round，不在 D6 session 范围。

---

## 9. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-27 | Initial D6 design-grade handoff after Campaign D upgrade plan-grade landed. Trigger: 用户要求 fresh-session handoff 让 D6 design-spec 可独立启动。Scope: self-contained 入口，新 session 不依赖本对话历史就能产出 D6-spec.md。 | Codex architect loop (with user direction) |
