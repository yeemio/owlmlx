# R0 — Replacement Re-baseline（Design Spec）

> 文档 grade：design-grade · 见 [README.md](README.md)
> Status：brainstorming-approved（2026-06-03）· pending user spec review
> 日期：2026-06-03
> Campaign：老平台完整替代（**Boundary 替代**）
> Plan-grade 来源：[`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) §IV.1 身份 +「下阶段主线声明（2026-06-03 · 替代收口）」；承接 Runtime-12 §7「Runtime-13 = actual replacement work」
> R0 交付物（单独文档，R0 执行时产出）：`docs/source-of-truth/runtime13-replacement-rebaseline-verdict.md`

---

## 0. 这份 spec 的位置

这是 "老平台完整替代" campaign 的**第一个子战役 R0** 的设计 spec。

- §1 = campaign 框架（已与负责人确认）
- §2 = R0 细节（本子战役的实际内容）
- §4 = 后续子战役 R1/R2/R4 轻量草图（R0 之后才细化）

**R0 是评估型子战役，写操作只有两处**：产出 `runtime13` verdict 文档、给两份旧 owlmlx 文档加 stale banner（见 §2.6）。除此之外全程只读——不改任何运行时 / serving 代码、不动 cutover 配置、不在 OwlCoda / OwlCC / oMLX 等外部 repo 写任何文件。它的价值是为后续全部 scope 立一个有证据的地基，避免在过时 verdict 上"修空气"。

---

## 1. Campaign 框架（已确认）

### 1.1 验收线：Boundary 替代

"完整替代老平台" = 把 **runtime control boundary 从 oMLX（platform 侧）收归 owlmlx 侧**：

- 自有栈（**OwlCoda / OwlCC**）生产流量全部直连 owlmlx、**无 oMLX 回退**；
- **不**要求复刻 oMLX 的 fleet / 连续批处理 / paged KV（README 明确 `not in scope`，刻意选择，不是 gap）；
- 与 `docs/architect/02-state-vs-market-gap.md §2.5` 的 boundary-替代定义、以及 `Internal Replacement-Grade Runtime Depth` 战略一致——这是**内部目标**，公开发布仍 parked。

明确**未选** "+质量 parity" 与 "全能力追平" 两档；详见 §1.2 对 R3 的降级。

### 1.2 分解

| 子战役 | 内容 | 对应 R-12 blocker / gap | 状态 |
|---|---|---|---|
| **R0** | Replacement re-baseline | 全部前置 | 本 spec |
| **R1** | Source-first parity（chat / messages / tools / stream 全交互形态，够 OwlCoda/OwlCC 无回退跑通） | blocker ① | R0 后细化 |
| **R2** | 生产控制面闭环 | blocker ② | R0 后细化 |
| **R4** | Ops cutover（流量全切、无 oMLX 回退）+ customer evidence | blocker ④ + customer-evidence gap | R0 后细化 |
| ~~R3~~ | ~~backend 质量 parity 全证~~ → 降级 **no-regression / 够用** | blocker ③ | **非硬验收线**（验收线选 boundary，非 +parity） |

5 个 replacement-grade stability gap（`host_stable_execution` / `cache_scheduler_depth` / `multi_model_lifecycle_governance` / `heavy_weight_runtime_repeatability` / `customer_runtime_evidence`）**只在威胁"无回退可靠性"时**条件性挂入相关 R，**不追 reference-grade 全闭合**。

### 1.3 起步：R0 先行（证据优先）

不在 2026-04 旧 verdict 上规划。R0 产出的"收窄后剩余 blocker 清单"驱动 R1/R2/R4 各自 scope —— 很可能比旧文档列的少。

---

## 2. R0 设计

### 2.1 目的

用一份**有证据的当前再评估**，取代过时的 4 月 verdict（`runtime12-replacement-readiness-verdict.md` 2026-04-12 / `replacement-grade-stability-gaps.md` 2026-04-22），产出权威结论：

> 要让 OwlCoda/OwlCC 跑 owlmlx-only、无 oMLX 回退，**当前实际**还剩哪些活。

旧文档落后于近期进展（native backend、本周期 B-1c §2 canonical `189d9d5c`、B-2 prefix cache、OpenAI tool-calling 等都在其后），所以 re-baseline 是必做前置。

### 2.2 评估对象

- **4 个 Runtime-12 replacement blocker**：① source-first parity 未冻 ② 生产控制面闭环未冻 ③ backend 质量 parity 未证（本 campaign 降级）④ ops 级替代未验。
- **5 个 replacement-grade stability gap**（见 §1.2）。

### 2.3 方法（全程只读）

**(a) 跨 repo 只读核验**（refinement #2）—— cutover 实况不能只看 owlmlx：

| repo | 路径 | 读什么 |
|---|---|---|
| owlmlx | `/Users/yeemio/AI/gitrep/owlmlx` | 能力矩阵、source-of-truth、evidence ledger、代码路径 |
| OwlCoda | `/Users/yeemio/AI/gitrep/owlcoda` | 当前默认 runtime 指向、是否仍有 oMLX fallback、cutover 配置开关、doctor replacement 判定 |
| OwlCC | `/Users/yeemio/AI/gitrep/owlcc`（必要时 `owlcc-byoscc`） | 同上 |
| oMLX（老平台参照） | `/Users/yeemio/AI/gitrep/omlx-upstream` | 仅作 boundary 对照，不 clone 功能 |

R0 对上述 repo **全程只读**；owlmlx 内除 §2.5 交付物与 §2.6 banner 外亦只读，对 OwlCoda / OwlCC / oMLX 不写任何文件。

**(b) 证据优先级（写死）**（refinement #3）—— 每条结论按此序取证，**commit 只作补充 provenance、不可作为唯一依据**：

1. source-of-truth 当前文档
2. capability matrix
3. 真实测试 / evidence ledger（`files/evidence/...`）
4. 当前代码路径
5. commit（补充 provenance）

**(c) 逐项分类** —— 对 4+5 每项标：✅ 4 月后已闭合 / ◐ 部分闭合（写清还剩什么）/ ⛔ 仍开放，每条挂证据引用（按 (b) 优先级）。

**(d) Cutover-blocking 判定**（refinement #5，负责人追加的 DoD）—— 每个 blocker 额外给一条：

> **当前是否会阻断 owlmlx-only cutover？**（会 / 不会 / 取决于 X）

这比三态分类更贴验收线：一个"部分闭合"的 gap 若**不阻断**无回退 cutover，就不是 R1/R2/R4 的必做项。

### 2.4 特别聚焦：当前 cutover 实况

单列一节，基于跨 repo 只读核：

- OwlCoda / OwlCC 现在指没指 owlmlx？默认 runtime 是什么？
- 还有没有 oMLX 回退路径？
- **"今天关掉回退会炸什么"** —— 给出基于配置/代码的判断（只读，**不实操关闭**）。

这是信号最高的未知项，直接决定 R1/R2/R4 的重量。

### 2.5 交付物

`docs/source-of-truth/runtime13-replacement-rebaseline-verdict.md`（refinement #1），内容：

- 刷新后的 replacement verdict（很可能仍 "not yet replaceable"，但 blocker 清单**收窄、准确**）；
- 收窄后剩余 blocker 清单，逐条 = 映射到 R1/R2/R4 + cutover-blocking 判定 + 证据引用；
- 与当前能力矩阵 / 近期进展对齐。

### 2.6 旧文档处理（克制）（refinement #4）

**不大面积改旧文档结论。** 只在 `runtime12-replacement-readiness-verdict.md` / `replacement-grade-stability-gaps.md` **顶部（及确有必要的段落）加 stale banner 指向 runtime13 verdict**，不重写正文。避免 R0 退化成文档重写战。

### 2.7 Definition of Done

1. 4+5 每项有"当前分类 + 证据引用（按 §2.3(b) 优先级）"。
2. **每个 blocker 有 cutover-blocking 判定**（§2.3(d)）。
3. cutover 实况节完成（跨 repo 只读，§2.4）。
4. `runtime13` verdict 落地；旧两文档加 stale banner 指向它（§2.6）。
5. 收窄后 blocker 清单冻结、可直接驱动 R1/R2/R4。
6. **零无出处断言**；无 commit-only 依据。

### 2.8 R0 明确不做（out of scope）

- 不修任何 blocker / gap；
- 不碰 cutover 配置（不改 OwlCoda/OwlCC 的 runtime 指向、不关 fallback）；
- 不改 owlmlx 运行时代码；
- 不在 OwlCoda / OwlCC / oMLX 等外部 repo 写任何文件（R0 的写操作仅限 owlmlx 内的 `runtime13` verdict + 旧文档 banner）；
- 不升任何 capability label；
- 不做 R1/R2/R4 的实现。

---

## 3. Hard Rules

1. 全程只读（跨 repo 亦只读）。
2. 证据优先级按 §2.3(b)，commit 不可作唯一依据。
3. 单机口径；fleet / 批处理 `not in scope` 不动摇。
4. 内部目标，不复活公开发布框架。
5. 旧文档 stale 标记克制（banner-only）。

---

## 4. 后续子战役（轻量草图 · R0 后按收窄清单细化）

> 以下仅占位，**R0 收窄 blocker 清单后**各自单独走 spec → plan → 实现。

- **R1 Source-first parity**：枚举 OwlCoda/OwlCC 真实用到的交互形态（chat / messages / tools / stream / count-tokens），对每种冻结 parity 证据，确保无回退可跑通。
- **R2 生产控制面闭环**：doctor / health / restart / 可观测在生产口径下闭环（不只 seam proof）。
- **R4 Ops cutover + customer evidence**：把生产流量真实切到 owlmlx-only、关 oMLX 回退，并留运维级证据（长跑、无泄漏、可恢复）。

---

## 5. 验证（R0 怎么算"做对"）

R0 是评估型子战役，不引入代码改动、无新测试。"做对"的验证 = **§2.7 DoD 全满足** + 自检：

- 每条结论可溯源到 §2.3(b) 优先级中的**具体出处**；
- 无 commit-only 依据；
- 旧文档无大面积改写（仅 banner）；
- runtime13 verdict 的剩余 blocker 清单能无歧义地驱动 R1/R2/R4 立项。
