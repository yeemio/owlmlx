# owlmlx Phase 45 - Supported-Host Reentry Baseline Establishment

## 你是谁

你是 `owlmlx` 主线执行者。

你现在不是在做本地微分解，也不是在继续 cache / governance fallback。  
本轮的前提已经变化：

- 当前本地 fallback 分支已经收尽
- `dominant_next_gap` 已返回 `host_stable_execution`
- cache 已冻结在 `structural_ingress_seam_introduced`

所以这份 prompt 只在一个条件下使用：

- **已经提供/授权了一个真实 supported host / system image**

如果这个前提不成立，不要硬做，不要回退去继续本地小修，直接按 blocked 收口。

## 第一性原则

- `supported-host baseline > blocked-host repetition`
- `real runtime baseline > narrative closure`
- `substrate closure > parity storytelling`
- `exact blocked outcome > fake forward motion`
- `host truth > specimen convenience`

## 当前真实状态

### 已经成立的

- `owlmlx` 已经是一个真实 runtime，不再只是实验壳。
- honest label 仍然是：
  - `early formal runtime`
  - `below reference-grade stability`
- cache 分支已冻结在：
  - `owlmlx.cache_structural_ingress_seam`
  - `closure_level = structural_ingress_seam_introduced`
- governance fallback 已本地收尽：
  - `pinning`
  - `TTL policy`
  - `eviction-history governance`
- 当前 live truth 已回到：
  - `selected_gap = host_stable_execution`
  - `dominant_next_gap = host_stable_execution`

### 当前不能宣称的

- customer-ready runtime
- reference-grade stability achieved
- heavy-weight repeatability achieved
- replacement-ready
- cache/batching parity

## 本轮唯一目标

在**提供的 supported host / system image** 上，建立 `owlmlx` 的第一个 **verified-safe MLX baseline**，并把它收成 runtime-owned truth，而不是只做一次临时 smoke。

## 使用前提

只有下面两条同时成立，才允许执行这份 prompt：

1. 你已拿到一个明确可用的 supported host / system image
2. 你可以在该 host 上实际执行 baseline establishment / smoke / verification

如果任一不成立：

- 不准回去继续 cache
- 不准回去继续 governance
- 不准重新做当前 blocked host 的 forensics
- 直接输出 `blocked: supported host/image not actually provided`

## 必须先读

1. `/Users/yeemio/AI/gitrep/owlmlx/files/goals/owlmlx/replacement-grade-stability-alignment-goal-contract.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/replacement-grade-stability-gaps.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
4. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-dominant-gap-reselection.md`
5. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-host-stable-execution-status.md`
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/phase45-heavy-weight-repeatability-status.md`
7. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-supported-host-return.md`
8. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/host_stable_execution.py`
9. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/heavy_weight_repeatability_status.py`
10. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/customer_runtime_evidence.py`
11. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_host_stable_execution.py`
12. `/Users/yeemio/AI/gitrep/owlmlx/scripts/runtime_heavy_weight_repeatability_status.py`

读完先输出不超过 12 行的执行计划，再动手。

## 硬规则

### 1. 本轮禁止事项

本轮不允许：

- 继续 cache widening
- 继续 governance micro-rounds
- specimen-specific优化题材
- MiniMax 题材漂移
- product/control-plane/UI work
- replacement verdict inflation

### 2. baseline 规则

你要建立的是 **supported-host baseline**，不是“一次偶然跑通”。

所以必须收成：

- baseline provenance
- baseline registration rule
- baseline safety/validation rule
- baseline smoke result
- baseline exact blocked/unblocked truth

### 3. honest 规则

如果 baseline 仍失败：

- 直接把失败收成更精确的 runtime-owned blocker
- 不准把“更接近了”写成“baseline 成立了”

如果 baseline 只支持 import / smoke，不支持 repeatability：

- 只能升级 `host_stable_execution`
- 不能越级升级 `heavy_weight_runtime_repeatability`

### 4. 证据等级规则

本轮最多只允许推进到：

- `supported-host baseline established`
- 或
- `supported-host blocker exactness improved`

不允许直接升级到：

- customer-ready
- reference-grade parity
- replaceable

## 预计时长与 Wave 规划

- Wave 0: supported-host intake freeze
- Wave 1: baseline provenance and registration
- Wave 2: baseline smoke / validation
- Wave 3: status + repeatability boundary sync
- Wave 4: customer evidence + dominant gap reselection
- Wave 5: honest closeout

## Wave 0: Supported-host intake freeze

目标：
- 先把“这台 host/image 到底是什么”收清楚，避免临时环境冒充 baseline

必做：
- 记录 supported host / system image 的：
  - machine identity
  - OS / system image identity
  - runtime prerequisites
  - python / mlx baseline prerequisites
- 明确这条 host 为什么属于 “supported-host attempt”，而不是 another local experiment

验收：
- 有清楚的 baseline intake truth

## Wave 1: Baseline provenance and registration

目标：
- 把 baseline 变成可登记、可复用、可拒绝坏环境的正式路径

必做：
- 明确 baseline registry / registration rule
- 如果已有 registry 机制，扩展到新 host/image
- 如果 probe/validation 通过，才允许登记
- 如果 probe 失败，不得写成 verified baseline

验收：
- baseline 不再只是口头路径，而是有正式注册/拒绝规则

## Wave 2: Baseline smoke / validation

目标：
- 在 supported host 上拿到第一条真实 baseline smoke

必做：
- 跑最小可重复 baseline smoke
- 明确区分：
  - import-level success
  - runtime boot success
  - first serve/smoke success
- 如果失败，冻结 exact blocker

验收：
- baseline smoke 结果有真实 verdict，不再停在推测

## Wave 3: Status + repeatability boundary sync

目标：
- 不让 host baseline 和 heavy-weight repeatability 混成一件事

必做：
- 更新：
  - `host_stable_execution`
  - `heavy_weight_runtime_repeatability`
- 明确写：
  - 哪一部分已经推进
  - 哪一部分仍未推进
- 如果只有 baseline 成功而 repeatability 还没成功，就明确把界线写死

验收：
- host baseline truth 和 heavy-weight truth 不打架

## Wave 4: Customer evidence + dominant gap reselection

目标：
- 把本轮结果同步进更上层的 runtime-owned 结论

必做：
- 更新 customer runtime evidence ledger
- 如有必要，更新 dominant gap reselection
- 只在 truth 真的变化时才改 dominant gap

验收：
- customer ledger 和 dominant gap 都反映最新 supported-host 结果

## Wave 5: Honest closeout

目标：
- 收口，不夸大

必做：
- 明确写：
  - baseline 是否建立成功
  - 如果成功，`owlmlx` 多了什么真实 substrate ability
  - 如果失败，blocker 比之前精确了什么
  - heavy-weight repeatability 是否真的动了
- 如果本轮后又进入新的 coordinator checkpoint，要停，不准偷开下一条分支

验收：
- 统筹看完后能直接决定是继续 heavy-weight / evidence，还是再次 blocked

## 必跑测试

至少跑：

- `python3 -m pytest /Users/yeemio/AI/gitrep/owlmlx/tests -q`

如果全量不现实，必须跑：

- 与 baseline / host stable / heavy weight / customer evidence 直接相关的 targeted pytest
- 并在最终汇报中写清为什么这样选

另外必须跑：

- baseline 相关 live script / smoke

## 必更新的真源

本轮最少更新：

- `phase45-host-stable-execution-status.md`
- `phase45-heavy-weight-repeatability-status.md`
- `phase45-customer-runtime-evidence-ledger.md`
- 如有必要：
  - `phase45-dominant-gap-reselection.md`
  - `master-outline.md`

## 本轮不在范围内

- cache widening
- governance fallback revisit
- MiniMax optimization
- UI / control-plane / packaging work
- replacement verdict 翻转

## 每个 Wave 完成后都要回答的 4 个问题

1. baseline 现在多了什么真实可复用 truth？
2. `owlmlx` 现在少了什么 blocked-host 幻觉或推测？
3. 这轮推进的是 baseline，还是 repeatability，边界清楚吗？
4. 离 supported-host runtime substrate closure 还差什么？

## 最终输出格式

## owlmlx Phase 45 Supported-Host Reentry Delivery Summary

### Supported host / image used
- [明确写清]

### Modified files
- [列表]

### Wave-by-wave outcomes
- Wave 0: [一句话]
- Wave 1: [一句话]
- Wave 2: [一句话]
- Wave 3: [一句话]
- Wave 4: [一句话]
- Wave 5: [一句话]

### New runtime-owned capabilities
- [列表]

### New/updated runtime surfaces
- [列表]

### Tests run
- [命令与结果]

### Build/check run
- [命令与结果]

### Evidence / truth updated
- [列表]

### Honest posture after this round
- [一句话]

### Remaining blockers before supported-host runtime substrate closure
- [列表]

### Why this round materially advances substrate closure
- [一句话]

## 提交信息

如果达到可提交状态，直接 commit：

`owlmlx: establish supported-host baseline`
