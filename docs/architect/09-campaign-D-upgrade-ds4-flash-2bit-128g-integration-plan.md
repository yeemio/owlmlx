# Campaign D Upgrade · DSV4-Flash 2bit-DQ 128G Integration Plan

> **Grade**: plan-grade · architecture intent
> **承载位置**: `docs/architect/09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`
> **下游 design-grade**: 待写（建议拆为 `design/D5-sustained-load-spec.md` / `design/D6-mainline-backend-integration-spec.md` / `design/D7-technical-preview-visibility-spec.md`，**各自 fresh session 落地** per [[feedback-fresh-session-grade-transitions]]）
> **Plan-grade 来源**: 2026-05-27 用户决策（DSV4 为基础能力，必须追）+ [`reference-runtime-comparison-matrix.md`](../source-of-truth/reference-runtime-comparison-matrix.md) §0.1.4 (新出现的硬差距：DSV4 / hybrid attention)
> **Status**: selected as Campaign D mainline-integration upgrade; runs **parallel to F-4** with no cross-dependency
> **语言纪律**: this plan does not claim DSV4 serving is supported; it defines how to bring DSV4-Flash 2bit-DQ from isolation lane to `technical_preview` visibility tier on the existing 128G host

---

## 1. Goal Contract

| Field | Value |
|---|---|
| `goal_id` | `campaign-d-upgrade-ds4-flash-2bit-128g-integration` |
| `title` | DSV4-Flash 2bit-DQ from isolation lane to `technical_preview` mainline integration on 128G hardware |
| `success_definition` | D5 + D6 + D7 各 stage 满足 §1a evidence threshold；最终 `DeepSeek-V4-Flash-2bit-DQ` 在 [`runtime-capability-matrix.md`](../source-of-truth/runtime-capability-matrix.md) 上从 `experimental_only` 升到 `partial`，并在 `/v1/runtime/model-visibility` diagnostic surface 的 `technical_preview` tier 下注册可见（**明确不进 `/v1/openai/models` default surface**） |
| `blocked_definition` | 任一硬条件成立则 plan 整体 blocked：(a) 128G host 上 sustained load N≥20 rounds 出现内存漂移无法收敛；(b) Blaizzy fork (`pc/add-deepseekv4flash-model`) 长期失修且 mlx-lm 主线未 merge 任何替代 fork；(c) backend health 在 sustained load 后被污染且无 recovery path |
| `hard_rules` | (1) 不上 `supported` tier；目标 visibility = `technical_preview`。(2) 不动 Blaizzy fork 之外的 upstream（不 self-maintain fork）。(3) 不主张 DSV4 parity / replacement vs oMLX / vMLX。(4) plan/design 阶段不写 code。(5) 不在本 campaign 处理 MTP recovery（D3 已 verdict `mtp_weights_absent_or_stripped`，stripped weights 影响）。(6) 严格遵守 [[project-owlmlx-agents-module-as-spec-rule]]：D5/D6/D7 的 validator / harness 走 `tests/` 或 `scripts/`，**不在 `owlmlx/` 包下新建 spec/validator 模块**。 |
| `out_of_scope` | DSV4-Pro 任何 variant；DSV4-Flash 4bit / 8bit / 原版 FP16（128G 跑不动 4bit 已验证，详见 §11 Risks）；MTP speculative integration on DSV4（D8 远期，不在本 plan）；自有 quantization pipeline；OwlCoda live consumer integration；与 oMLX / vMLX 的 measured TPS 对比；256G+ hardware target |
| `current_truth` | D1-D4 全部 passed in isolated `.runtime-deepseek-v4-mlx` lane（D1: 15/15 ladder rows / D2: TTFT p50=593.84ms decode p50=38.18 tok/s / D3: MTP weights stripped verified / D4: clean pre-load reject verified）；2026-05-11 single-cycle full lifecycle proved on port 8067（load 14.125s / TTFT cold 24821ms / TPS 32 / unload freed 100GB / backend health clean）；2bit-DQ artifact 已 local at `~/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ` (~90GB) |
| `remaining_gaps` | (1) 缺 sustained-load N≥20 evidence（既有 D1 是 5 prompts × 3 token ladder，每条只跑 1 次，不是 same-prompt N≥20）；(2) 缺 mainline backend integration evidence（既有路径走 `scripts/bench/deepseek_v4_d1_repeatability.py` 隔离 harness，不走 `MlxLmSubprocessBackend` 主线）；(3) 缺 visibility surface registration（当前 `lane=flagship_experimental, visibility_status=not_registered`）；(4) [`deepseek-v4-bring-up-status.md`](../source-of-truth/deepseek-v4-bring-up-status.md) §4 Blocked Scope 当前禁止任何 visibility registration，本 plan 通过后需 update 该 §4 把限制松绑到 "可在 `technical_preview` 下注册，禁止在 `supported` 下" |
| `dominant_next_gap` | D6 mainline backend integration 是关键路径——D5 sustained load 与 D7 visibility 都依赖 D6 的 backend path 存在 |

---

## 2. Why Campaign D Upgrade Now

三条独立 trigger 同时成立：

1. **2026-05-27 capability-surface refresh** ([`reference-runtime-comparison-matrix.md` §0.1.4](../source-of-truth/reference-runtime-comparison-matrix.md))显示：
   - **oMLX v0.3.9.dev1** 已 **DeepSeek V4 Pro/Flash full port**
   - **vMLX v1.5.49** 已 **DSV4 Flash native SWA+CSA/HCA composite prefix cache**
   - **owlmlx 仅 clean pre-load reject** —— **新出现的硬差距**
2. **用户 2026-05-27 拍板**: DSV4 是基础能力，必须追（不是路线选择，是行业基线）。
3. **物理可行性已验证**:
   - D1-D4 passed in isolated lane → 不是从零做
   - 2bit-DQ 90GB < 128G → 装得下
   - 已 measured lifecycle (load 14s / TTFT cold 24821ms / TPS 32 / unload freed 100GB) → 跑得动

不延后的理由：oMLX/vMLX 每周新 release，capability-surface gap 持续扩大；既有 D1-D4 evidence 趁新鲜复用比未来重做成本低。

---

## 3. Replacement-Grade Question

Campaign D upgrade 问：

```text
当 owlmlx 在 128G Mac 上运行 DSV4-Flash 2bit-DQ（通过 Blaizzy fork 集成的 mainline backend
而非 isolated lane）时，能否：
(a) sustained load N≥20 rounds 下保持内存稳定（无漂移）
(b) 通过 MlxLmSubprocessBackend 正常 load / generate / unload
(c) 在 technical_preview visibility tier 下被 OwlOps 等上层消费
(d) sustained load 后 backend health 与 settle barrier 保持 clean
```

不问的（明确 out of scope）:
- 与 oMLX/vMLX 的 measured TPS 对比（用户决策"先定位 128G 可用范围"，不追比赛）
- DSV4-Pro 支持
- DSV4 上的 MTP speculative
- 多并发 DSV4 serving

---

## 4. Scope

### In scope

- **D5: 128G sustained-load + N≥20 repeatability**
- **D6: Mainline backend integration**（pyproject extras group + MlxLmSubprocessBackend 集成 + tests/ env-gated case）
- **D7: technical_preview visibility registration**
- **既有 D1-D4 evidence reuse** as baseline
- **mlx-lm upstream watch ledger** 建立（任一 release 触发本 plan re-check）
- **[`deepseek-v4-bring-up-status.md`](../source-of-truth/deepseek-v4-bring-up-status.md) §4 Blocked Scope update**（visibility 限制松绑到 `technical_preview`）
- **owlmlx model_lineage / model_release_candidate_record 升级**：从 `lane=flagship_experimental, visibility_status=not_registered, verdict=experimental_only` 升到 `lane=technical_preview, visibility_status=technical_preview_registered, verdict=partial`

### Out of scope

- **DSV4-Pro** 任何 variant
- **DSV4-Flash 4bit / 8bit / FP16 原版**（128G 跑不动 4bit ≈141GB；FP16 ≈149GB；详见 §11）
- **MTP speculative integration on DSV4**（D8 远期 / 受 D3 stripped weights 阻塞）
- **自有 mlx-lm fork 维护**（继续用 Blaizzy fork + upstream watch）
- **自有 quantization pipeline**（用 HuggingFace `mlx-community` 现成 2bit-DQ）
- **OwlCoda live consumer end-to-end** 集成
- **与 oMLX / vMLX measured TPS 对比**（[`public-claim-matrix.md`](../source-of-truth/public-claim-matrix.md) §3 已明确 banned vocabulary 适用）
- **进 `/v1/openai/models` default surface**（明确仅 `technical_preview` tier）
- **256G+ hardware target**（外部硬件依赖）
- **修改 `owlmlx/` 包下任何模块以承载 DSV4 specific 逻辑**（per [[project-owlmlx-agents-module-as-spec-rule]]，validator/harness 走 `tests/` / `scripts/`）

---

## 5. Stage Shape

类比 F-4 plan 的 staged evidence approach，Campaign D upgrade 分 3 个 stage（与既有 D1-D4 编号续接）：

| Stage | 目标 | 复用既有 evidence | Minimum output | Expected wall time |
|---|---|---|---|---|
| **D5** | 128G sustained-load N≥20 repeatability 在 isolated lane（不动 backend path）| D1 ladder harness | N=20 rounds × 1 fixed prompt = 20 generations + watermark/settle observation | < 4 hours / resumable |
| **D6** | Mainline backend integration（pyproject extras + `MlxLmSubprocessBackend` path + env-gated real-smoke test）| D2 metrics harness | 1 full lifecycle through mainline backend + 5 sanity generations | < 2 hours |
| **D7** | `technical_preview` visibility registration（model_release_candidate lane 升级 + visibility diagnostic 暴露 + [`deepseek-v4-bring-up-status.md`](../source-of-truth/deepseek-v4-bring-up-status.md) §4 update）| D4 reject path 保留 fallback | 1 visibility-surface evidence record + 1 capability-matrix update | < 1 hour (after D5/D6) |

### 关键路径排序

D6 mainline backend integration **必须先做**——D5 (sustained load) 与 D7 (visibility) 都依赖 D6 的 backend path 存在。建议执行顺序：**D6 → D5 → D7**。

### N≥20 选择理由

[`02-state-vs-market-gap.md`](02-state-vs-market-gap.md) §1 第 1 维 Repeatability 把 "N≥20 seed-to-token 字节一致测试" 标为 L1 必追差距。Campaign A 是 owlmlx-wide repeatability 主线；D5 是 Campaign A 在 DSV4 上的特定应用。**D5 共用 Campaign A 的 N≥20 evidence schema**，不另立标准。

---

## 6. Acceptance Wording

Campaign D upgrade 各 stage 通过的 capability label 演进：

| Stage 通过 | 写入位置 | Wording |
|---|---|---|
| D5 passed (sustained-load) | model_release_candidate_record | `deepseek_v4_flash_2bit_dq_128g_sustained_load=passed` (含 N=20 evidence pointer) |
| D6 passed (mainline backend) | model_release_candidate_record | `deepseek_v4_flash_2bit_dq_mainline_backend_integration=passed` (含 backend path + lifecycle evidence pointer) |
| D7 passed (visibility) | runtime-capability-matrix.md | `DeepSeek-V4-Flash-2bit-DQ` 行从 `experimental_only` 升到 `partial`，含 D5+D6 evidence pointer 与 `technical_preview` tier 标记 |
| 任一 stage hard fail | 无 promotion | 失败 taxonomy 成为下一 dominant gap；plan 重新进入 §1a review |

**严格不允许**：跳过任一 stage 直接到 `supported`（[[runtime-capability-matrix.md §6 Label Promotion Rules]] enforced）。

---

## 7. Relationship To Existing D Stages

| 既有 stage | 状态 | 在本 plan 中的角色 |
|---|---|---|
| D1 (isolated repeatability ladder) | passed 2026-05-17 | **D5 baseline**——D5 是同 harness 的 N≥20 扩展 |
| D2 (metrics ledger p1/p2/p4 × 128/512) | passed 2026-05-17 | **D6 baseline**——D6 在 mainline backend 上重做相同 metrics 形成对比 |
| D3 (MTP checkpoint inspection) | passed 2026-05-17 | **closed 不重做**——MTP weights stripped verdict 是 D8 远期判据 |
| D4 (clean pre-load reject) | passed 2026-05-17 | **D7 fallback path**——D7 升 visibility 后 D4 reject 路径仍保留作为 unsupported variant 的 reject 兜底 |

D1-D4 各 evidence 在 D5/D6/D7 中**不重做**，只作为 reference 对比基线。这是本 plan 能在 < 1 工作日完成的根本——绝大多数 baseline 已 sunk-cost。

---

## 8. Relationship To Other Campaigns

| Campaign | 关系 | 影响 |
|---|---|---|
| **F-4 Structured-Output Invariance** | 并行 / 无 cross-dependency | D7 之后可作为 F-4 evidence stream 的额外 model: `DeepSeek-V4-Flash-2bit-DQ` 加入 F-4.2 stratified matrix 候选（不阻塞 F-4 本身） |
| **Campaign A (N≥20 Repeatability)** | D5 共用 Campaign A 的 N≥20 evidence schema | D5 是 Campaign A 在 DSV4 lane 的实例化；harness 共用 |
| **B-1c §2 (wall-clock continuity)** | 独立 / 不阻塞 | DSV4-Flash 是单 host 单 worker by design，不进 cache reuse / session-level KV path，B-1c blocker 不影响 D |
| **F-1 (speculative_execution_status)** | endpoint surface 保留 / method 不 promote on DSV4 | F-1 endpoint 在 DSV4 上返回 `speculative_method=not_applicable`（D3 stripped weights verdict）；不构成 F-1 promotion blocker |
| **F-2 (n-gram suffix decoding)** | 不交叉 | F-2 在 Qwen/Gemma 主线，DSV4 不进 F-2 evidence stream |

---

## 9. Integration Boundary

### 9.1 Upstream dependency

- **Primary**: Blaizzy fork `pc/add-deepseekv4flash-model` commit `5c10538136b9038b9626c134612b08afc18d697a`（owlmlx 已经在用，已验证 D1-D4 通过）
- **Editable install location**: `/tmp/mlx-lm-dsv4`（owlmlx 隔离 venv `.runtime-deepseek-v4-mlx/` 已配置）
- **mlx-lm 主线**: `0.31.3` (2026-04-22) **不含** `deepseek_v4.py`；多个 PR (1192/1201/1195/1189/1067) 处于 open/draft，**主线 merge 时间未知**
- **transformers**: `5.7.0` 不识别 `deepseek_v4` model_type；fork 的 `tokenizer_utils.py` 已 patch，走 `PreTrainedTokenizerFast` fallback

### 9.2 owlmlx 内的承载位置

- **pyproject.toml**: 新增 optional dependency group `deepseek-experimental = ["mlx-lm @ git+https://github.com/Blaizzy/mlx-lm@pc/add-deepseekv4flash-model"]`
  - **不进** mainline `runtime` extra
  - **不进** default install
  - 仅 D6 design-grade 落地后启用
- **scripts/**: 既有 `scripts/bench/deepseek_v4_d1_repeatability.py` 升级（D5/D6 共用）
- **tests/**: 既有 `tests/test_deepseek_v4_d1_repeatability.py` 扩展 + 新增 `tests/test_mlx_native_backend_real_smoke.py` (env-gated) 加 DSV4 case
- **owlmlx/**: **不增加任何 DSV4 specific spec 模块**（per [[project-owlmlx-agents-module-as-spec-rule]]）。唯一可能修改：`owlmlx/model_release_candidate_record.py` 的 `DEFAULT_MODEL_RELEASE_CANDIDATES` 数据更新（不是新增模块）

### 9.3 mlx-lm Upstream Watch Ledger

建立 owlmlx-side upstream watch（不是 mlx-lm 内部状态）：

```yaml
# 建议位置: docs/source-of-truth/mlx-lm-upstream-watch.md
upstream_watch:
  - issue: ml-explore/mlx-lm#1233
    title: "Add model support for DeepSeek-V4 (deepseek_v4)"
    triggers_on: merge / close
    impact: 若 merge 任一 fork 进入主线 release，本 plan §9.1 需切换 fork 路径
  - pr: ml-explore/mlx-lm#1192 (Blaizzy)
    title: "Add DeepSeek-v4 (Flash/Pro)"
    triggers_on: merge / close / abandon
    impact: 本 plan 当前 primary dependency；若 abandon 需切换至 #1195/#1189/#1201
  - pr: ml-explore/mlx-lm#1201 (akashgoswami)
    triggers_on: merge / draft→ready
    impact: 候选切换目标
  - pr: ml-explore/mlx-lm#1195 (rltakashige)
    triggers_on: merge / draft→ready
    impact: 候选切换目标
```

watch ledger 每月 review 一次（plan 内不强制每月跑，只是建议节奏）；watch 触发后**重新进入本 plan §1a review**，不自动 promote。

---

## 10. Evidence Paths

```text
files/evidence/owlmlx/deepseek-v4/
  d5-sustained-load/
    <ts>-d5-128g-sustained-load-n20.jsonl
    <ts>-d5-128g-sustained-load-rollup.jsonl
  d6-mainline-backend-integration/
    <ts>-d6-mainline-backend-lifecycle.jsonl
    <ts>-d6-mainline-backend-metrics.jsonl
  d7-technical-preview-visibility/
    <ts>-d7-visibility-surface-registration.jsonl

files/evidence/owlmlx/model-release-candidates/
  <ts>-dsv4-flash-2bit-dq-promotion-d5.jsonl
  <ts>-dsv4-flash-2bit-dq-promotion-d6.jsonl
  <ts>-dsv4-flash-2bit-dq-promotion-d7-partial.jsonl
```

**严格规则**：没有 §1a evidence pointer 的 capability label 变更不允许 promotion 进 `runtime-capability-matrix.md`。

---

## 11. Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| **128G constraint sustained-load 内存漂移** | DSV4-Flash 2bit-DQ 占用 ~90GB，留 ~38GB 给 OS + Metal + KV cache + activations。Sustained load 下 KV cache 增长或内存碎片可能突破 watermark | D5 在 N≥20 rounds 期间 sample memory_watermark + settle_barrier_event；任一 `WatermarkAction=eviction` 或 settle barrier failure 即 fail |
| **Blaizzy fork 长期失修** | 当前 dependency 是社区个人 fork (PR #1192)；若 maintainer 停止响应，owlmlx 路径变孤儿 | §9.3 upstream watch ledger；若 fork 失修 ≥3 月 → 切换至 #1195/#1189/#1201；不自维护 |
| **mlx-lm 主线 merge 不同 fork** | upstream 可能 merge 其他 fork（#1195/#1189），与 Blaizzy fork API 不一致 | extras group 隔离 + upstream watch 触发 plan re-review；切换走新 release 而非热替换 |
| **transformers 5.7.0 不识别 deepseek_v4** | 已知问题，fork 已 patch fallback | 不主动追 transformers 主线；继续走 fork 内 `PreTrainedTokenizerFast` fallback |
| **MTP weights stripped (D3)** | 2bit-DQ artifact 不含 MTP weights，speculative path 不可走 | 明确 not in scope；F-1 endpoint 在 DSV4 上返回 `speculative_method=not_applicable`；D8 远期单独 plan |
| **4bit variant 在 128G 上 OOM** | 已验证：4bit ≈141GB > 128GB | 明确 out of scope；4bit 本地 artifact 保留但不进 D plan |
| **TPS 对比诱惑** | oMLX/vMLX 6 周内大量 DSV4 release，外部 reviewer 自然问"谁更快" | `public-claim-matrix.md` §3 banned vocabulary enforce；D 系列 evidence 不含 measured TPS comparison row |
| **`deepseek-v4-bring-up-status.md` §4 vs visibility registration 冲突** | 既有 doc 明确 "any visibility registration on GET /v1/openai/models 不允许 until upstream merges" | D7 design-grade 中明确：visibility 仅进 `/v1/runtime/model-visibility` diagnostic + `technical_preview` tier，**不进** `/v1/openai/models`；并 update §4 限制为 "禁止在 supported tier，允许在 technical_preview tier" |
| **既有 evidence 时间戳老化** | D1-D4 evidence 是 2026-05-17，到 D5 execution 时可能 > 1 个月 | D5 在 mainline backend 上跑时同步重做 single-cycle lifecycle smoke 作为 cross-validation；不强制重做 D1-D4 全套 |

---

## 12. Non-Goals (explicit list)

为防止 plan 在执行中 scope creep，本 plan 明确**不做**以下任一项：

1. 不上 `supported` tier；目标终点是 `partial` + `technical_preview` visibility
2. 不做 DSV4-Pro 任何 variant
3. 不做 DSV4-Flash 4bit / 8bit / 原版 FP16（128G 上跑不动 4bit；其他超规格）
4. 不做 MTP speculative on DSV4（D8 远期 / D3 stripped weights 阻塞）
5. 不做 256G+ hardware target（外部依赖，本 plan 锁定 128G）
6. 不做 OwlCoda live consumer end-to-end 集成
7. 不自维护 mlx-lm fork（仅 upstream watch + 候选切换）
8. 不主张 parity / replacement vs oMLX / vMLX
9. 不在 `owlmlx/` 包下新建 DSV4 specific spec/validator 模块（per [[project-owlmlx-agents-module-as-spec-rule]]）
10. 不修改 mlx-lm 上游或 transformers 上游代码
11. 不在 plan/design 阶段写 code（保留给 code-grade 的 fresh session）
12. 不引入 measured TPS 对比 evidence（保留 banned vocabulary enforcement）

---

## 13. Status / Next Step

### Decision

Campaign D upgrade (D5 / D6 / D7) 接受为 Campaign D 升级路径，2026-05-27 立项。

### Next Execution Round

1. **Land design-grade specs**（建议拆 3 份，**各自 fresh session** per [[feedback-fresh-session-grade-transitions]]）：
   - `docs/architect/design/D6-mainline-backend-integration-spec.md`（**关键路径，先做**）
   - `docs/architect/design/D5-sustained-load-spec.md`
   - `docs/architect/design/D7-technical-preview-visibility-spec.md`
2. **Review thresholds** in each design-grade（特别是 D5 N=20 hard gate / D6 lifecycle pass criteria / D7 visibility tier 约束）
3. **Code-grade execution**（各 stage 一个 fresh session 喂 design-grade prompt 进去）：
   - D6 code-grade first（pyproject extras + backend integration + env-gated real-smoke test）
   - D5 code-grade after D6 backend path landed
   - D7 code-grade after D5 evidence accumulates
4. **Sweep follow-up**（与本 plan 独立的 staging round）：
   - Update [`deepseek-v4-bring-up-status.md`](../source-of-truth/deepseek-v4-bring-up-status.md) §4 Blocked Scope（visibility 限制松绑到 `technical_preview`）
   - Update [`02-state-vs-market-gap.md`](02-state-vs-market-gap.md) §3.5（DSV4 从"刻意不追"改为"L1 必追，Campaign D upgrade in flight"）
   - Update [`reference-runtime-comparison-matrix.md`](../source-of-truth/reference-runtime-comparison-matrix.md) §8 "新出现的硬差距" 块（标 "active Campaign D upgrade target"）
   - Update [`runtime-capability-matrix.md`](../source-of-truth/runtime-capability-matrix.md) DSV4 行（D7 之后从 `experimental_only` 到 `partial`）
   - Add [`mlx-lm-upstream-watch.md`](../source-of-truth/mlx-lm-upstream-watch.md) ledger（per §9.3）

### Parallel work

F-4 走自己的 fresh session 进 code-grade（D 系列不阻塞 F-4）。Campaign A N≥20 repeatability 主线可与 D5 共用 evidence schema。

---

## 14. References

### owlmlx 内
- [`01-mainline-roadmap.md`](01-mainline-roadmap.md) Campaign D 部分（line 35-38 D1-D4 summary / line 320 future positioning / line 455 owner）
- [`08-campaign-F4-structured-output-invariance-plan.md`](08-campaign-F4-structured-output-invariance-plan.md)（plan-grade 模板）
- [`02-state-vs-market-gap.md`](02-state-vs-market-gap.md) §3.5 (Quantization & MoE) + §1 #1 Repeatability
- [`docs/source-of-truth/deepseek-v4-bring-up-status.md`](../source-of-truth/deepseek-v4-bring-up-status.md)（既有 D1-D4 verdict + §4 Blocked Scope 待 update）
- [`docs/source-of-truth/deepseek-v4-flash-adapter-optimization-candidate.md`](../source-of-truth/deepseek-v4-flash-adapter-optimization-candidate.md)
- [`docs/source-of-truth/reference-runtime-comparison-matrix.md`](../source-of-truth/reference-runtime-comparison-matrix.md) §0.1.4 (新出现的硬差距)
- [`docs/source-of-truth/competitor-capability-matrix-20260527.md`](../source-of-truth/competitor-capability-matrix-20260527.md)
- [`docs/source-of-truth/runtime-capability-matrix.md`](../source-of-truth/runtime-capability-matrix.md) DSV4 行 + §6 Label Promotion Rules
- [`docs/source-of-truth/public-claim-matrix.md`](../source-of-truth/public-claim-matrix.md) §3 banned vocabulary

### D1-D4 evidence records (复用 baseline)
- `files/evidence/owlmlx/deepseek-v4/d1-isolated-repeatability/20260517T-d1-full-ladder-adopted-messages-policy.jsonl`
- `files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl`
- `files/evidence/owlmlx/deepseek-v4/d3-checkpoint-inspection/20260517T-d3-mtp-checkpoint-inspection.jsonl`
- `files/evidence/owlmlx/deepseek-v4/d4-preload-reject/20260517T-d4-mtp-clean-preload-reject.jsonl`

### 既有 design-grade specs (D1-D4)
- `docs/architect/design/D1-spec.md`
- `docs/architect/design/D2-spec.md`
- `docs/architect/design/D3-spec.md`
- `docs/architect/design/D4-spec.md`

### owlmlx 内承载 scripts / tests
- `scripts/bench/deepseek_v4_d1_repeatability.py`（D5/D6 共用基础 harness）
- `scripts/runtime_repeatability_campaign.py`（cross-campaign harness）
- `scripts/runtime_comparative_evidence.py`（comparative ledger 入口）
- `tests/test_deepseek_v4_d1_repeatability.py`
- `tests/test_repeatability_campaign_harness.py`
- `tests/test_mlx_native_backend.py`（reject 路径 contract）
- `tests/test_mlx_native_backend_real_smoke.py`（env-gated 真实 smoke；D6 扩展加 DSV4 case）

### 外部 / upstream
- [mlx-lm 主线](https://github.com/ml-explore/mlx-lm) v0.31.3 (2026-04-22)
- [mlx-lm PR #1192 (Blaizzy)](https://github.com/ml-explore/mlx-lm/pull/1192)（primary upstream dependency）
- [mlx-lm issue #1233](https://github.com/ml-explore/mlx-lm/issues/1233)（DSV4 model support 总 tracking）
- [mlx-lm PR #1195 / #1189 / #1201 / #1067](https://github.com/ml-explore/mlx-lm/pulls?q=DeepSeek+V4)（候选切换目标）
- [mlx-community/DeepSeek-V4-Flash-2bit-DQ](https://huggingface.co/mlx-community/DeepSeek-V4-Flash-2bit-DQ)（HF artifact，本地 90GB 已 cached at `~/AI/Agent/model-candidates/`）

### 相关 memory
- [[project-owlmlx-strategic-pivot-internal-depth]]（stage 1 internal replacement-grade）
- [[project-owlmlx-agents-module-as-spec-rule]]（不在 `owlmlx/` 下新建 spec/validator 模块）
- [[feedback-fresh-session-grade-transitions]]（plan/design/code 切 fresh session）
- [[feedback-plan-grade-feasibility-probe]]（已 satisfied：本 plan 前的 feasibility probe 已完成 mlx-lm upstream 状态 / HF artifact 可用性 / 既有 D1-D4 evidence reuse）
- [[feedback-equivalence-standard-after-baseline]]（D5/D6/D7 acceptance 标准锚定 D1-D4 既有 baseline，不引入 oMLX/vMLX 对比 baseline）
- [[feedback-stale-language-sweep]]（plan landed 后需扫 §13 列出的 5 处 stale 表述）

---

## 15. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-27 | Initial Campaign D upgrade plan-grade. Trigger: 2026-05-27 capability-surface refresh 显示 oMLX/vMLX 已 full port DSV4 vs owlmlx clean-reject-only；用户拍板 DSV4 为基础能力必追；feasibility probe 已验证 (Blaizzy fork 可用 + 2bit-DQ 90GB 本地已有 + D1-D4 evidence 全 passed)。决策：Flash only / 2bit-DQ only / Blaizzy fork + upstream watch / 与 F-4 并行 / 目标 visibility = `technical_preview` 非 `supported`。 | Codex architect loop (with user direction) |
