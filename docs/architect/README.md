# docs/architect/

> **This directory contains plan-grade architecture documents.**
> **It is repo-visible and PR-reviewable, but it is _not_ source-of-truth runtime evidence.**
> **Do _not_ add these files to `docs/source-of-truth/master-outline.md` unless promoted.**

---

## Grade boundary

`docs/architect/` 与 `docs/source-of-truth/` 是**两个不同 grade 的文档层**，不可混淆：

| 维度 | `docs/source-of-truth/` | `docs/architect/`（本目录） |
|---|---|---|
| Grade | runtime evidence + contract truth | plan-grade / architecture-grade intent |
| 收录索引 | `master-outline.md` 入索引 | **不**入 `master-outline.md`（除非 promote） |
| Evidence-language | 严格（`supported` / `partial` / `experimental` / `not in scope`） | 同样严格，但允许 plan-grade hedging（`plausible` / `candidate` / `pending`） |
| 命名约束 | 与 PR #649 vocabulary / capability matrix 对齐 | plan-grade 工作命名（架构师视角） |
| 改动节奏 | 与 runtime 代码与 evidence 同 round | 架构师视角，独立刷新 |
| 消费者 | runtime / OwlOps / OwlCoda / 上层平台 | 决策评审、PR review、新成员上手 |

---

## 阅读顺序

### Plan-grade docs（路线图层 · 战略与框架）

| # | 文档 | 内容 |
|---|---|---|
| 1 | [01-mainline-roadmap.md](01-mainline-roadmap.md) | 主线声明 + 12+ 月战略路线图（6 子战役 + Wave G / Wave H） |
| 2 | [02-state-vs-market-gap.md](02-state-vs-market-gap.md) | 现状 vs 市场差距清单（12 维框架对照） |
| 3 | [03-real-accomplishments.md](03-real-accomplishments.md) | 已完成真实情况 + 四主证据 |
| 4 | [04-architecture-canvas.md](04-architecture-canvas.md) | 架构画布（系统 / 功能 / 业务逻辑 / 路线图，mermaid + 表格 + ASCII） |
| 5 | [05-alignment-audit.md](05-alignment-audit.md) | 代码 ↔ source-of-truth ↔ plan-grade 对齐审计 + 架构 / 功能 / 方向补充 + Wave G narrow 工作单（2026-05-23） |
| 6 | [06-campaign-F1-plan.md](06-campaign-F1-plan.md) | Campaign F-1 `speculative_execution_status` runtime contract plan |
| 7 | [07-perf-optimization-proposal-20260526.md](07-perf-optimization-proposal-20260526.md) | C/A/B 性能与长上下文工程调研；B prefill chunking 收口；C/A paused on mlx-lm hybrid trim |
| 8 | [08-campaign-F4-structured-output-invariance-plan.md](08-campaign-F4-structured-output-invariance-plan.md) | Campaign F-4 structured-output invariance 选型与测量计划 |

### Design-grade docs（gate 层 · 单 gate 可执行口径）

| # | 路径 | 内容 |
|---|---|---|
| D | [design/](design/) | Design-grade specs per gate（**一次一个 gate** · 不批量预先撰写） · 见 [design/README.md](design/README.md) |

design/ 在父目录之下作为 sub-grade 承载层；**与 plan-grade 同 architect 边界**（都不是 source-of-truth），但其下每份 spec 把单个 gate 从"目标 + 验收摘要"细化到形式化 contract + harness 改动点 + evidence 路径。

---

## Promotion 路径

任何 `architect/` 文档要 promote 到 `source-of-truth/`：

1. 必须有对应 runtime 代码 / contract surface / evidence ledger 支撑（不允许"纯文档"晋级）
2. 走 **§1a Promotion Gate**：implementation evidence + test coverage + no false dependency + governance compliance + adoption label resolved
3. 在 `docs/source-of-truth/master-outline.md` 显式登记
4. 本目录中**保留**刷新历史，并在文档头标 `promoted to source-of-truth/<path>` 与 promote 日期

未 promote 之前：

- 不允许其他 source-of-truth 文档反向引用 architect/ 文档作为契约依据
- 不允许 capability-matrix.md 中引用 architect/ 文档作为 `supported` 证据
- runtime 代码 import / consume architect/ 文档中的命名当作契约名是越级

---

## 改动纪律

本目录文档刷新遵循以下纪律（继承自 owlmlx 总纪律）：

- **Evidence-language calibration**：source-read ≠ execution；doc-grade ≠ design-grade；plan-grade 内**允许**`plausible` / `candidate`，但不允许把 plan-grade 写成 source-of-truth 口径
- **Staging discipline**：每轮 round 的 staged set 严格只含本 round scope；不 sweep 不相关 dirty 编辑
- **Module-as-spec forbidden**：本目录文档不得引用未被 runtime 消费的 spec-as-code 模块作为支撑
- **顶层文档反推刷新**：架构 wave 完成时同步刷新本目录的相关章节

---

## 与 source-of-truth 的关系（边界图）

```
docs/source-of-truth/        ← runtime evidence + contract truth
  ├── ARCHITECTURE-TRUTH.md  ← 唯一顶层真源
  ├── master-outline.md      ← 索引
  ├── runtime-capability-matrix.md
  └── ... 200+ 份 evidence/contract docs

docs/architect/              ← plan-grade / architecture intent（本目录）
  ├── README.md (本文)
  ├── 01-mainline-roadmap.md
  ├── 02-state-vs-market-gap.md
  ├── 03-real-accomplishments.md
  └── 04-architecture-canvas.md

docs/phase-prompts/          ← 执行 prompt
docs/handoff/                ← 轮次交接

         architect/ → (promote) → source-of-truth/
              ↑
         (从 source-of-truth/ 衍生架构视角)
              ↓
         architect/ → 反推刷新（wave 完成时）
```

`architect/` ↔ `source-of-truth/` 是**单向 promote + 双向衍生**的关系；不允许 `architect/` 内容**绕过** promote 直接成为 contract 依据。

---

## 当前状态（2026-05-27 consolidated drop）

- **本目录文件**：8 份 plan-grade companion 文档 + 本 README + design/ 子目录承载单 gate spec
- **已 promote 到 source-of-truth/**：0 份
- **承载迁移来源**：`~/.claude/plans/owlmlx-1-*`（Claude Code plan-mode 临时承载；本目录为 authoritative plan-grade 副本）
- **维护入口**：[01-mainline-roadmap.md](01-mainline-roadmap.md) 的"顶层维护入口"小节

---

## 维护规则

- 每次架构方向变更（新设 Campaign / Wave、关键决策落地、reopen condition 调整等）必须同步刷新本目录对应章节
- 先更新 [01-mainline-roadmap.md](01-mainline-roadmap.md)，再更新受影响 companion；不要只更新 `~/.claude/plans/`
- 刷新提交集严格限定在 `docs/architect/**`；不混入 runtime code / bench evidence / source-of-truth/ 内的 untracked 文件
- 决策落地时附 `决策 N · YYYY-MM-DD` 标记，便于追溯
