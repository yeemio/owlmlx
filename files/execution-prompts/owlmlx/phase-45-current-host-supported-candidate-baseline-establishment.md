# owlmlx Phase 45 - Current-Host Supported-Candidate Baseline Establishment

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

你现在**不是**继续做 local baseline reentry verification。
那一轮的任务是纠正旧的 blocked truth，并判断当前开发机是否还有资格回到主线。

当前已知新事实是：

- fresh clone + fresh venv 的 `oMLX` / `vMLX` MLX baseline 均可起
- targeted pytest 已通过：
  - `tests/test_mlx_environment.py`
  - `tests/test_host_stability.py`
  - `tests/test_customer_runtime_evidence.py`
  - `tests/test_dominant_gap_reselection.py`
- isolated validation registry 已实测：
  - `register_verified_mlx_baseline.py` 可注册：
    - `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/python`
    - label = `omlx-probe-venv`
  - `runtime_mlx_environment_readiness.py` 可返回：
    - `readiness = ready`
    - `selected_label = omlx-probe-venv`
- 默认 `~/.owlmlx` registry 也已实测：
  - `~/.owlmlx/mlx-verified-python.json` 已包含：
    - `omlx-probe-venv`
  - `runtime_mlx_environment_readiness.py` 可返回：
    - `readiness = ready`
    - `selected_label = omlx-probe-venv`
  - `runtime_host_stable_execution_status.py` 可返回：
    - `summary.status = host_ready_for_runtime_validation`
    - `summary.ready = true`
- historical quarantine residue 仍存在于默认 truth：
  - `~/.owlmlx/mlx-unsafe-python.json` 当前仍保留 6 条 unsafe entries
- 更上层 live truth 仍然没有自动跳级：
  - `runtime_customer_runtime_evidence.py`
    - `evidence_label = early_formal_runtime`
    - `dominant_next_gap = host_stable_execution`
    - `exact_external_blocker = null`
  - `runtime_dominant_gap_reselection.py`
    - `selected_gap = host_stable_execution`

这意味着：

- 当前开发机不再应该继续被当成“默认 blocked host”
- 但也**还没有**自动升级成 “supported-host baseline 已建立”

所以这轮的身份很明确：

- **从 reentry verification 往前走一步**
- **把当前开发机推进成一个正式的 supported-host candidate baseline**
- **但不越级宣称 heavy-weight repeatability / customer-ready / replacement-ready**

## 第一性原则

- `current evidence > stale blocked narrative`
- `candidate baseline establishment > repeated reentry rhetoric`
- `baseline provenance and safety > one lucky import pass`
- `host-ready does not mean replacement-ready`
- `exact closure rung > inflated recovery story`

## 当前真实状态

### 已经成立的

- `owlmlx` 是真实 runtime，不是 toy
- honest label 仍然是：
  - `early_formal_runtime`
  - `below reference-grade stability`
- cache 分支仍冻结在：
  - `structural_ingress_seam_introduced`
- governance fallback 仍停在：
  - `policy_gap_closed`
- 当前 live truth 已从旧 blocked host 叙事回到：
  - `readiness = ready`
  - `host_ready_for_runtime_validation`

### 当前不能宣称的

- supported-host baseline fully established
- heavy-weight repeatability restored
- customer-ready
- replacement-ready
- cache/batching parity

## 本轮唯一目标

把**当前开发机**推进成一个正式的：

- `supported-host candidate baseline`

这要求你建立的不只是：

- import 可用

而是至少包括：

- verified baseline provenance
- default registry truth consistency
- host-stable runtime-owned smoke
- candidate-level closeout truth

本轮最终只能回答一个问题：

- **当前开发机是否已经足够从 `reentry_admissible` 升级成 `supported_host_candidate_baseline_established`**

## 必须先读

1. `/Users/yeemio/AI/gitrep/runtime-probes/2026-04-16-mlx-omlx-vmlx-baseline-investigation.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/replacement-grade-stability-gaps.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-host-stable-execution-status.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-dominant-gap-reselection.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-local-baseline-reentry-after-revalidation.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_environment.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/host_stability.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/customer_runtime_evidence.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/scripts/register_verified_mlx_baseline.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_mlx_environment_readiness.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_host_stable_execution_status.py`
14. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_customer_runtime_evidence.py`
15. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_dominant_gap_reselection.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 硬规则

### 1. 本轮禁止事项

本轮不允许：

- 继续 cache widening
- 继续 governance micro-rounds
- 把 current host baseline establishment 写成 heavy-weight repeatability 恢复
- 直接重开 specimen-first 叙事
- MiniMax / benchmark / optimization 题材漂移
- replacement / parity / customer-ready 结论翻转

### 2. registry 规则

这轮必须明确区分：

- `isolated validation registry`
- `default ~/.owlmlx registry`

如果默认 registry 已经恢复：

- 要明确写“恢复到了什么程度”

如果默认 registry 仍带历史 quarantine residue：

- 要明确写“残留还在，但不再构成当前 host blocked truth”

不准把这两件事混成一句话。

### 3. baseline 规则

本轮建立的是：

- `supported-host candidate baseline`

不是：

- full supported-host baseline program closure

所以必须至少收成：

- baseline candidate provenance
- baseline selection rule
- baseline smoke truth
- default registry status
- host-stable contract refresh

### 4. 证据等级规则

本轮最多只允许推进到：

- `supported_host_candidate_baseline_established`

或：

- `candidate_baseline_still_incomplete`

不允许直接推进到：

- `heavy_weight_repeatability_restored`
- `approaching_reference_grade_stability`
- `customer-ready`
- `replacement-ready`

## 预计时长与 Wave 规划

- Wave 0: baseline candidate intake freeze
- Wave 1: registry and provenance normalization
- Wave 2: candidate baseline smoke
- Wave 3: host-stable contract refresh
- Wave 4: customer evidence and dominant-gap sync
- Wave 5: candidate-baseline checkpoint closeout

## Wave 0: Baseline Candidate Intake Freeze

目标：
- 先把当前开发机为什么重新成为 candidate 讲清楚

必做：
- 记录：
  - 当前 machine / host identity
  - 当前 baseline python 路径
  - 当前 execution mode
  - 当前 verified label
- 明确旧 blocked truth 为什么过时
- 明确本轮不是“新 host bring-up”，而是“当前 host candidate promotion”

验收：
- candidate baseline intake truth 清楚

## Wave 1: Registry And Provenance Normalization

目标：
- 把 baseline 从“现在能用”推进到“默认 truth 也能解释”

必做：
- 分开核对：
  - isolated registry verdict
  - default `~/.owlmlx` registry verdict
- 记录：
  - default verified baselines 文件状态
  - default unsafe/quarantine 文件状态
  - 历史 residue 是否仍存在
- 如果需要，小幅修正 default truth 使其与 live evidence 一致
- 不准为了好看去抹掉有价值的历史 unsafe 记录

验收：
- 默认 registry truth 和 live baseline truth 不再打架

## Wave 2: Candidate Baseline Smoke

目标：
- 拿到一条最小但真实的 candidate baseline smoke

必做：
- 基于当前 verified baseline 跑：
  - fresh `mlx.core` import
  - fresh `mlx_lm` import
  - 最小 runtime-owned baseline smoke
- 明确区分：
  - import success
  - readiness success
  - host-ready success
  - baseline smoke success
- 如果 smoke 失败，冻结 exact blocker

验收：
- candidate baseline 不再只是 readiness 绿色，而是有真实 smoke verdict

## Wave 3: Host-Stable Contract Refresh

目标：
- 让 `host_stable_execution` 从旧 blocked truth 更新到新 candidate truth

必做：
- 更新：
  - `phase45-host-stable-execution-status`
- 明确写：
  - historical blocked context
  - current revalidated context
  - 为什么现在已不该继续写成 `host_blocked_move_validation`
- 如果还有残余限制，也必须精确写出

验收：
- host-stable truth 与 live script 一致

## Wave 4: Customer Evidence And Dominant-Gap Sync

目标：
- 让更上层 truth 跟上 candidate baseline establishment

必做：
- 更新：
  - `phase45-customer-runtime-evidence-ledger`
  - `phase45-dominant-gap-reselection`
- 只在 evidence 真变化时才改 dominant gap
- 如果 `host_stable_execution` 从 blocked 变 candidate-established：
  - 必须明确写下一步是不是进入 heavy-weight repeatability / stronger baseline validation

验收：
- customer evidence 和 dominant gap 与新 host truth 一致

## Wave 5: Candidate-Baseline Checkpoint Closeout

目标：
- 收口，不直接偷开下一条线

必做：
- 新增一个 coordinator checkpoint
- 只回答：
  - 当前开发机是否已成为 `supported_host_candidate_baseline_established`
  - 下一步是否允许进入更强的 baseline validation / heavy-weight boundary check
- 不准直接继续做下一阶段

验收：
- 统筹者看完能直接做下一步二选一

## 必跑测试

至少跑并报告：

- `python3 -m pytest tests/test_mlx_environment.py tests/test_host_stability.py tests/test_customer_runtime_evidence.py tests/test_dominant_gap_reselection.py -q`

另外必须跑：

- `register_verified_mlx_baseline.py`
- `runtime_mlx_environment_readiness.py`
- `runtime_host_stable_execution_status.py`
- `runtime_customer_runtime_evidence.py`
- `runtime_dominant_gap_reselection.py`

## 必更新的真源

本轮最少更新：

- `phase45-host-stable-execution-status`
- `phase45-customer-runtime-evidence-ledger`
- `phase45-dominant-gap-reselection`
- 一份新的 candidate baseline checkpoint

如果本轮仍使用了 isolated registry 辅助验证：

- 真源里必须单列：
  - isolated verdict
  - default registry verdict
  - historical quarantine residue posture

## Out Of Scope

- heavy-weight repeatability closure
- cache branch reopen
- governance branch reopen
- benchmark / optimization work
- product / control-plane / shell work
- replacement or parity storytelling

## 最终输出格式

你的最终汇报必须包含：

- `Modified files`
- `Wave-by-wave outcomes`
- `Current host candidate truth`
- `Tests run`
- `Runtime baseline checked`
- `Isolated vs default registry truth`
- `Release-readiness delta`
- `Remaining blockers before stronger runtime validation`
- `Coordinator verdict`

最后的 `Coordinator verdict` 只能是其中一个：

- `supported_host_candidate_baseline_established`
- `candidate_baseline_still_incomplete`

## Commit Message

使用：

- `owlmlx: establish current-host supported candidate baseline`
