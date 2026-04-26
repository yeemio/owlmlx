# owlmlx Phase 45 - Local Baseline Reentry After Re-Validation

## 你是谁

你是 `owlmlx` Phase 45 主线执行者。

你现在不是继续做 cache / governance 微分解，也不是直接恢复整条 supported-host mainline。  
你要处理的是一个更前置、也更关键的问题：

- 之前把“当前开发机 baseline blocked”当成硬前提来冻结主线
- 但 2026-04-16 的完整复盘显示，这个前提已经被削弱
- 所以现在必须先做：
  - **旧 truth 纠错**
  - **窄口 baseline reentry 验证**

这轮不是大反转，不准直接写成“问题解决了”。  
这轮只回答一个问题：

- **当前开发机是否已经够资格从 blocked dev host 升级成 supported-host candidate**

## 第一性原则

- `current re-validation > stale blocker narrative`
- `baseline truth correction > checkpoint inertia`
- `narrow reentry verification > broad mainline restart`
- `real smoke > import optimism`
- `exact admissible / still-blocked verdict > fuzzy progress language`

## 当前真实状态

### 历史上真实发生过的

- fresh MLX / Metal 初始化曾经出现过崩溃
- `.runtime1-mlx` / `.runtime2-mlx` 曾进入 quarantine / unsafe 叙事
- 这也是之前冻结 `supported_host_return` checkpoint 的核心依据之一

### 2026-04-16 新复盘确认的

完整调查文档：

- `/Users/yeemio/AI/gitrep/runtime-probes/2026-04-16-mlx-omlx-vmlx-baseline-investigation.md`

关键新事实：

- fresh clone + fresh venv 的 `oMLX`：
  - `import mlx.core` 通过
  - `import omlx` 通过
  - `python -m omlx.cli --help` 通过
- fresh clone + fresh venv 的 `vMLX`：
  - `import mlx.core` 通过
  - `import vmlx_engine` 通过
  - `python -m vmlx_engine.cli --help` 通过
- 旧环境复测：
  - `owlmlx/.runtime2-mlx` 的 fresh `import mlx.core` 现在通过
  - brew `oMLX 0.3.4` env 的 fresh `import mlx.core` 现在通过

### 这意味着什么

当前已经不能继续把：

- “开发机 current MLX baseline 仍然 blocked”

当成一个未经复核的硬前提。

更准确的说法是：

- 历史上确实崩过
- 但当前这轮 fresh re-validation 里已经**不再稳定复现**
- `owlmlx` 当前 blocked truth 更像：
  - stale quarantine
  - old verified-baseline registry
  - old host-stable narrative

### 当前 live re-validation 结果

已实测成立：

- `register_verified_mlx_baseline.py` 可成功把新的 safe candidate 注册成：
  - `omlx-probe-venv`
  - `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/python`
- `runtime_mlx_environment_readiness.py` 现在可返回：
  - `readiness = ready`
  - `selected_label = omlx-probe-venv`
  - `python_executable = /Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/python`

### 当前不能宣称的

- customer-ready
- heavy-weight repeatability restored
- replacement-grade closure restored
- supported-host baseline fully established

## 本轮唯一目标

做一轮**窄口 local baseline reentry verification**，先把旧误判纠正掉，再判断当前开发机是否已经重新具备成为 `supported-host candidate` 的资格。

这轮最多只允许输出两种裁决之一：

- `reentry_admissible`
- `still_blocked`

## 必须先读

1. `/Users/yeemio/AI/gitrep/runtime-probes/2026-04-16-mlx-omlx-vmlx-baseline-investigation.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/replacement-grade-stability-gaps.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-host-stable-execution-status.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-dominant-gap-reselection.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-supported-host-return.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_environment.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/host_stability.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/customer_runtime_evidence.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_mlx_environment_readiness.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/scripts/register_verified_mlx_baseline.py`
13. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_host_stable_execution_status.py`
14. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_customer_runtime_evidence.py`
15. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_dominant_gap_reselection.py`

读完后先输出不超过 12 行的执行计划，再动手。

## 硬规则

### 1. 本轮禁止事项

本轮不允许：

- 继续 cache widening
- 继续 governance micro-rounds
- 继续沿用“当前 baseline blocked”旧口径而不复核
- 直接恢复 `supported_host_baseline_establishment`
- 直接翻转 heavy-weight / repeatability / replacement 结论
- MiniMax / specimen 题材漂移

### 2. 纠错规则

如果新证据成立，就必须明确写出：

- 哪部分旧判断已经过时
- 哪部分仍然有效
- 旧 checkpoint 为什么在当时是诚实的
- 为什么现在需要重评

不准写成“之前都错了”，也不准继续嘴硬写成“旧 blocker 仍然无条件成立”。

### 3. reentry 规则

本轮只允许验证：

- verified baseline selection
- fresh `mlx.core` import
- fresh `mlx_lm` import
- baseline registration
- readiness surface re-check
- host stable execution re-check
- 一个最小 `owlmlx` baseline smoke

如果为了避免污染历史 registry / quarantine，需要临时把 registry 指到 `/tmp`
或其他隔离路径做验证：

- 允许这样做
- 但只能算 **validation-only isolated proof**
- 不准把隔离 registry 的通过直接写成“默认 `~/.owlmlx` truth 已恢复”
- 默认真实 registry / quarantine 是否已同步恢复，必须单独交代

### 4. 证据等级规则

本轮最多只允许推进到：

- `historical blocker revalidated`
- `baseline reentry under verification`
- `supported-host candidate admissible`

不允许直接推进到：

- `supported-host baseline established`
- `heavy-weight repeatability restored`
- `customer-ready`
- `replacement-ready`

## 预计时长与 Wave 规划

- Wave 0: investigation truth intake
- Wave 1: stale truth correction
- Wave 2: baseline registry / readiness re-check
- Wave 3: narrow host-stable smoke
- Wave 4: customer evidence + dominant-gap resync
- Wave 5: coordinator checkpoint closeout

## Wave 0: Investigation Truth Intake

目标：
- 先把 2026-04-16 复盘结果正式吸收进 Phase 45 语境

必做：
- 精确列出：
  - 哪些 fresh import / CLI probe 已通过
  - 哪些旧环境也已复测通过
  - 旧 quarantine / registry 是如何影响当前 truth 的

验收：
- 不再存在“继续沿用旧 blocker 前提”的语义偷懒

## Wave 1: Stale Truth Correction

目标：
- 修正已经过时的 blocked baseline 叙事

必做：
- 更新：
  - `phase45-host-stable-execution-status`
  - `phase45-customer-runtime-evidence-ledger`
  - `phase45-dominant-gap-reselection`
- 如果需要，新增一份 `local re-validation` 真源，把：
  - historical crash
  - current non-reproduction
  - stale quarantine / registry
  写清楚

验收：
- 旧 truth 不再把“当前 baseline blocked”写成未经复核的硬事实

## Wave 2: Baseline Registry / Readiness Re-Check

目标：
- 证明当前机器是否已经重新拥有一个可用 verified baseline

必做：
- 实际跑：
  - `register_verified_mlx_baseline.py --python /Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/python --label omlx-probe-venv --execution-mode default_metal`
  - `runtime_mlx_environment_readiness.py`
- 顺序要求：
  - 先注册，再复查 readiness / host-stable surface
  - 不准把 registration 和 readiness 并发跑完后拿旧结果当结论
- 明确记录：
  - selected baseline
  - execution mode
  - readiness verdict
- 区分：
  - true reentry
  - accidental local pass

验收：
- readiness surface 给出更新后的真实结论
- 必须区分：
  - isolated registry verdict
  - default `~/.owlmlx` registry verdict

## Wave 3: Narrow Host-Stable Smoke

目标：
- 不止 import，要做最小 `owlmlx` baseline smoke

必做：
- 跑一条最小 host-stable / runtime baseline smoke
- 只验证：
  - baseline path can boot
  - minimal runtime-owned path is alive
- 不准在这轮扩到 heavy-weight repeatability

验收：
- 有真实 smoke verdict
- 能明确说当前开发机是：
  - `reentry_admissible`
  - 或 `still_blocked`

## Wave 4: Customer Evidence + Dominant-Gap Resync

目标：
- 让上层 truth 跟上新验证结果

必做：
- 更新 customer runtime evidence
- 重新跑 dominant gap reselection
- 只在新证据真的改变主线时才改 dominant gap

验收：
- customer evidence 和 dominant gap 都和新 baseline 事实一致

## Wave 5: Coordinator Checkpoint Closeout

目标：
- 收口，不偷开下一条线

必做：
- 新增一个 coordinator checkpoint
- 只回答：
  - 当前开发机是否已经成为 `supported-host candidate`
  - 下一步是否允许进入 `supported_host_baseline_establishment`
- 不准直接继续做下一阶段

验收：
- 统筹者看完能直接做二选一：
  - `reentry admissible`
  - `still blocked`

## 必跑验证

至少跑并报告：

- targeted pytest
  - `tests/test_mlx_environment.py`
  - `tests/test_host_stability.py`
  - `tests/test_customer_runtime_evidence.py`
  - `tests/test_dominant_gap_reselection.py`
- 真实脚本：
  - `runtime_mlx_environment_readiness.py`
  - `register_verified_mlx_baseline.py`
  - `runtime_host_stable_execution_status.py`
  - `runtime_customer_runtime_evidence.py`
  - `runtime_dominant_gap_reselection.py`

## Verification Assets / Gate Records

至少更新或新增：

- `phase45-host-stable-execution-status`
- `phase45-customer-runtime-evidence-ledger`
- `phase45-dominant-gap-reselection`
- 一份新的 `local baseline re-validation` 真源
- 一份新的 coordinator checkpoint

如果本轮使用了隔离 registry / quarantine：

- 真源里必须单独写一节：
  - 为什么需要隔离 registry
  - 隔离验证结论是什么
  - 默认 `~/.owlmlx` 目前是什么状态
  - 后续是否还需要做默认 registry 的迁移/清理/解除 quarantine

## Out of Scope

- heavy-weight repeatability closure
- cache branch reopen
- governance branch reopen
- customer-ready / replacement-ready verdict changes
- specimen-specific performance stories

## 最终输出格式

你的最终汇报必须包含：

- `Modified files`
- `Wave-by-wave outcomes`
- `Current baseline truth`
- `Tests run`
- `Build/check run`
- `Runtime baseline checked`
- `Isolated vs default registry truth`
- `Release-readiness delta`
- `Remaining blockers before supported-host reentry`
- `Coordinator verdict`

最后的 `Coordinator verdict` 只能是其中一个：

- `reentry_admissible`
- `still_blocked`

## Commit Message

使用：

- `owlmlx: revalidate local baseline and reopen host-stable truth`
