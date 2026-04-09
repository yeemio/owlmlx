# owlmlx Phase 1C: Runtime Bridge — From Document Repo To Execution Participant

**Date**: 2026-04-09
**Status**: Ready for execution
**Depends on**: owlmlx Phase 1A (runtime governance freeze) + Phase 1B (rename + contract mapping) — both complete
**Blocked by**: Nothing — this round is the critical inflection point

---

## 1. Identity And Mission

你不是在继续写 owlmlx 的"真源文档"。

owlmlx 已经有 13 份 source-of-truth 文档。身份、边界、治理、合同映射、命名策略全部已经建立。

**这一轮的使命是：让 owlmlx 从"一套关于 runtime 的注释"变成"一个参与执行的 runtime 组件"。**

如果这一轮完成后 owlmlx 仍然只有 markdown 文件、零代码、零测试、零可执行入口，那这一轮就失败了。

---

## 2. First Principles

1. **代码 > 文档**：owlmlx 已经有足够的文档。这一轮的衡量标准是"owlmlx 里有没有能跑的东西"。
2. **治理必须回注执行链**：主仓的 `phase-delivery-agent-contract.md` 和 `AGENT.md` 才是实际约束执行的文件。owlmlx 治理层如果不接入主仓执行链，就是空转。
3. **迁移必须从最小可验证单元开始**：不是迁整个 runtime，是迁一个具体的、可测试的、有明确 owner 的模块。
4. **主仓是执行主体**：owlmlx 不替代主仓的 phase 推进体系。owlmlx 提供 runtime 真源，主仓消费它。

---

## 3. Current Real State

### owlmlx 侧

| 事实 | 状态 |
|---|---|
| 身份文档 | 13 份，完整 |
| 治理层 | runtime-governance.md + hazardous-operations.md，已冻结 |
| 合同映射 | contract-mapping.md，四分类已建立 |
| 命名收口 | rename-strategy.md，已建立 |
| 可运行代码 | **零** |
| 测试 | **零** |
| 主仓引用 owlmlx | **零** — 主仓没有任何文件 import 或 reference owlmlx |
| 治理层执行约束力 | **零** — 没有机制保证主仓执行时会查 owlmlx 治理规则 |

### 主仓侧（AI/Agent）

| 事实 | 状态 |
|---|---|
| 当前 phase | 42-43，runtime-first-then-kimi 已确立 |
| runtime truth exposure | `/v1/runtime/omlx/status` 已挂载，per-model 可见性是下一优先级（R1） |
| 治理执行 | phase-delivery-agent-contract.md 实际约束每轮执行 |
| safe-resume 实现 | `kimi_bf16_safe_validate.py` 已实装，dry-run 已验证 |
| Kimi 激活门控 | K-GATE-1/2/3 已定义，尚未全部通过 |
| owlmlx 存在感 | **零** — 主仓不知道 owlmlx 存在 |

### 核心矛盾

owlmlx 声称拥有 runtime truth ownership，但主仓的实际执行链路完全不经过 owlmlx。

---

## 4. Key Gaps

| Gap | 严重度 | 说明 |
|---|---|---|
| owlmlx 零代码 | **Critical** | 一个"runtime"没有任何代码，身份不成立 |
| 主仓不引用 owlmlx | **Critical** | ownership 声明没有消费者 |
| 治理层无执行约束力 | **High** | governance 只存在于 markdown，不在执行链路里 |
| contract-mapping 标注过度乐观 | **Medium** | `owned now` 实际是 `principle extracted, implementation in Agent` |
| runtime-governance 与 hazardous-operations 内容重叠 | **Low** | safe-resume 定义出现在两个文件里 |

---

## 5. Must-Read Files

执行前必须完整阅读：

**owlmlx 侧**：
- `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-contracts.md`
- `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-status-schema.md`
- `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/contract-mapping.md`
- `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/runtime-governance.md`

**主仓侧**：
- `/Users/yeemio/AI/Agent/AGENT.md`
- `/Users/yeemio/AI/Agent/docs/source-of-truth/local-llm-platform/phase-delivery-agent-contract.md`
- `/Users/yeemio/AI/Agent/docs/source-of-truth/local-llm-platform/system-architecture.md` §2.3 Runtime Layer
- `/Users/yeemio/AI/Agent/files/verification-assets/phase-42/runtime-first-then-kimi-priority-reset.md`
- `/Users/yeemio/AI/Agent/files/verification-assets/phase-42/kimi-crash-safe-resume-gate.md`

---

## 6. Hard Rules

1. **这一轮结束时 owlmlx 必须有至少一个可运行的 Python 模块和对应的测试。** 否则轮次判定为失败。
2. **不得继续新增纯文档型 source-of-truth 文件。** 现有 13 份已经足够。只允许修正和回接。
3. **主仓必须出现至少一处对 owlmlx 的正式引用。** 否则 ownership 声明无消费者。
4. **contract-mapping.md 的 `owned now` 标签必须修正为诚实分类。**
5. **不迁移大段实现代码。** 迁移目标是一个最小可验证的 runtime truth 模块。
6. **失败是合法结果。** 如果发现某个迁移路径不可行，记录原因并标 blocked，不假装成功。

---

## 7. Wave Plan

| Wave | 目标 | 预估 |
|---|---|---|
| Wave 1 | 修正 contract-mapping 诚实度 + 消除文档重叠 | 20 min |
| Wave 2 | 在 owlmlx 里建立第一个可运行的 runtime truth 模块 | 45 min |
| Wave 3 | 为该模块写测试 | 20 min |
| Wave 4 | 在主仓建立对 owlmlx 的正式引用链 | 30 min |
| Wave 5 | 把 owlmlx 治理规则注入主仓执行合同 | 30 min |
| Wave 6 | 验证 + 诚实标注 + 最终报告 | 20 min |

---

## 8. Wave-By-Wave Tasks

### Wave 1: Contract Mapping 诚实度修正

**目标**: 让 contract-mapping.md 的分类反映真实状态。

**任务**:
- 把 `kimi-crash-safe-resume-gate.md` 和 `kimi-nextgen-next-round-entry-safe-resume.md` 的标注从 `owned now` 改为 `principle owned, implementation in Agent repo`
- 在 runtime-governance.md §5 safe-resume contract 后加引用链：`First instance: K-Q4 safe-resume gate, defined in Agent repo files/verification-assets/phase-42/kimi-crash-safe-resume-gate.md`
- 在 hazardous-operations.md §4 mandatory reclassification rule 后加引用链：`First instance: K-Q3 → K-Q3a reclassification, defined in Agent repo files/verification-assets/phase-42/kimi-nextgen-next-round-entry-safe-resume.md`
- 消除 runtime-governance.md §5 和 hazardous-operations.md §6 的 safe-resume 重复定义：governance 保留完整定义，hazardous-operations 改为引用

**验收**: contract-mapping.md 无 `owned now` 标注指向仍完全在主仓的实现

**为什么这个 wave 重要**: 如果分类不诚实，后续所有基于 mapping 的迁移决策都会出错

### Wave 2: 第一个可运行的 Runtime Truth 模块

**目标**: owlmlx 第一次拥有可执行代码。

**迁移目标选择逻辑**:
- 必须是 owlmlx contract-mapping 里标为 `owned but still shell-hosted` 的东西
- 必须足够小，一个文件能装下
- 必须有明确的输入输出可测试
- 最佳候选：**runtime status schema 的 Python 定义和验证逻辑**

**任务**:
- 在 owlmlx 根目录建立 `owlmlx/` Python package（`__init__.py`）
- 创建 `owlmlx/runtime_status.py`：定义 runtime status schema 的 Python dataclass 或 TypedDict，包含 `runtime-status-schema.md` 里定义的字段
- 包含一个 `validate_runtime_status(data: dict) -> ValidationResult` 函数，验证一个 status 响应是否符合 owlmlx schema
- 包含诚实的 capability label 常量：`SUPPORTED`, `PARTIAL`, `BEST_EFFORT`, `MANUAL_ONLY`, `BLOCKED`, `UNSUPPORTED`

**验收**: `python -c "from owlmlx.runtime_status import validate_runtime_status; print('ok')"` 能跑通

**为什么这个 wave 重要**: owlmlx 从文档仓库变成有代码的仓库。这是身份转折点。

### Wave 3: 测试

**目标**: owlmlx 的代码有测试保护。

**任务**:
- 创建 `tests/test_runtime_status.py`
- 测试 `validate_runtime_status` 对合法 status 数据返回通过
- 测试对缺失必要字段的数据返回失败
- 测试对 capability label 不在允许值内的数据返回失败
- 测试 large-weight path 特有字段的验证

**验收**: `python -m pytest tests/ -v` 全绿

**为什么这个 wave 重要**: 没有测试的代码不是 runtime truth，是又一份 prose

### Wave 4: 主仓引用链

**目标**: 主仓正式知道 owlmlx 存在。

**任务**:
- 在主仓 `docs/source-of-truth/local-llm-platform/system-architecture.md` §2.3 Runtime Layer 末尾加一段：说明 owlmlx 是 runtime truth 的上游真源，链接到 owlmlx 仓库位置
- 在主仓 `AGENT.md` 的 authority hierarchy 里加一条：当任务涉及 runtime identity、runtime governance、hazardous operation classification 时，owlmlx source-of-truth 是补充权威来源
- 在 owlmlx `extraction-inventory.md` 里更新：标注 Wave 2 迁移的模块已完成首次提取

**验收**: 在主仓 grep `owlmlx` 能找到至少 2 处正式引用

**为什么这个 wave 重要**: 没有消费者的 ownership 声明是自说自话

### Wave 5: 治理回注主仓执行合同

**目标**: owlmlx 的治理规则进入主仓的实际执行纪律。

**任务**:
- 在主仓 `phase-delivery-agent-contract.md` 末尾新增一个 section：`§ Runtime Governance Gate`
  - 当任务涉及 heavy runtime operation（大权重模型加载、BF16 extraction、full-engine validation）时，必须先检查 owlmlx `runtime-governance.md` 和 `hazardous-operations.md`
  - 如果操作符合 hazardous operation 分类，必须走 laddered execution protocol（dry-run → single-unit → serial → thresholded → expansion）
  - safe-resume contract 在 owlmlx governance 里定义，具体实例在主仓 verification-assets 里
- 在主仓 `kimi-crash-safe-resume-gate.md` 顶部加一行注释：`Governance principle: owlmlx/docs/source-of-truth/runtime-governance.md §5`

**验收**: 主仓 phase-delivery-agent-contract 里能 grep 到 `owlmlx` 和 `runtime-governance`

**为什么这个 wave 重要**: 这是治理层从"空转文档"变成"执行约束"的关键步骤

### Wave 6: 验证 + 诚实标注 + 最终报告

**目标**: 全面验证这一轮的交付物，诚实标注能力状态。

**任务**:
- 运行 owlmlx 测试：`python -m pytest tests/ -v`
- 在主仓 grep owlmlx，确认引用链存在
- 更新 owlmlx `runtime-capability-matrix.md`：把 `Fully self-owned implementation stack` 从 `partial` 标注详细说明：`partial — first Python module exists, schema validation only, no serving capability`
- 更新 owlmlx `roadmap.md`：标注 Phase 1C 完成，记录实际产出 vs 计划产出
- 写最终报告

**验收**:
- 测试全绿
- 主仓引用链存在
- capability matrix 标注诚实
- 最终报告包含所有 required sections

---

## 9. Required Tests And Build Checks

- `python -m pytest tests/ -v` 在 owlmlx 目录下全绿
- `python -c "from owlmlx.runtime_status import validate_runtime_status"` 成功
- 主仓 `grep -r "owlmlx" /Users/yeemio/AI/Agent/docs/` 至少 2 个结果

---

## 10. Out Of Scope

- 不迁移 oMLX serving 逻辑
- 不迁移 kimi-sharded-engine.py
- 不迁移 kimi_bf16_safe_validate.py
- 不改主仓的 router/dashboard/desktop 代码
- 不替换主仓现有的 runtime status 暴露链路
- 不做 owlmlx 的 pip 包发布
- 不写新的纯文档型 source-of-truth

---

## 11. Branch Conditions

**如果 Wave 2 发现 runtime-status-schema 不适合作为首个迁移模块**（比如它的字段完全依赖 oMLX 内部实现，无法脱离 oMLX 独立验证）：
- 降级为：在 owlmlx 里建立 governance validation 工具——一个检查主仓执行计划是否符合 owlmlx hazardous-operation 规则的 linter
- 这仍然是"可运行代码"，只是方向从"schema 迁移"变成"governance 工具"

**如果 Wave 4 发现主仓 AGENT.md 的 authority hierarchy 不适合直接修改**（比如 hierarchy 结构太紧凑，加 owlmlx 会造成混乱）：
- 降级为：在主仓 system-architecture.md 里加引用，AGENT.md 暂不动
- 记录 blocked 原因

---

## 12. Final Output Format

### 最终报告必须包含

- Modified files（owlmlx 侧 + 主仓侧分开列）
- Wave-by-wave outcomes（pass / partial / blocked / failed）
- New user-visible capabilities
- Tests run（完整输出）
- owlmlx 代码行数（不含空行和注释）
- 主仓 owlmlx 引用数
- Capability matrix 变更
- Remaining blockers before owlmlx becomes a real runtime participant
- Why this phase materially advances owlmlx toward being a runtime rather than a document collection

---

## 13. Commit Messages

**owlmlx 侧**:
```
Phase 1C: first executable runtime module + governance reference chains

- Add owlmlx/runtime_status.py with schema validation
- Add tests/test_runtime_status.py
- Fix contract-mapping honesty labels
- Add governance reference chains to forensics instances
- Remove safe-resume duplication between governance and hazardous-ops docs
```

**主仓侧**:
```
Reference owlmlx as upstream runtime truth source

- Add owlmlx reference in system-architecture.md runtime layer
- Add runtime governance gate in phase-delivery-agent-contract.md
- Link safe-resume-gate.md to owlmlx governance principle
```
