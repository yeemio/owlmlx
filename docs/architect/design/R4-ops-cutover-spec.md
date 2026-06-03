# R4 — Ops Cutover（Phase 1: Readiness + Controlled Smoke）— Design Spec

> 文档 grade：design-grade · 见 [README.md](README.md)
> Status：brainstorming-approved（2026-06-03）· pending user spec review
> 日期：2026-06-03
> Campaign：老平台完整替代（**Boundary 替代**）— R-series **R4**
> Plan-grade 来源：[`../01-mainline-roadmap.md`](../01-mainline-roadmap.md)「下阶段主线声明」; [`../../source-of-truth/runtime13-replacement-rebaseline-verdict.md`](../../source-of-truth/runtime13-replacement-rebaseline-verdict.md) §5（R4）
> **Phase：Phase 1 only** — owlmlx 侧就绪 + 一次受控 smoke。**不**翻正式默认、**不**持续 soak、**不** claim "replacement complete"。

---

## 0. 位置 + 验收口径

R4 是替代收口的核心子战役（runtime13 §5）：把 OwlCoda/OwlCC 切到 owlmlx-only、去 `:8009` 回退、采 customer evidence。**本 spec 只覆盖 Phase 1**：owlmlx 侧就绪 + 一次受控、非默认 OwlCoda agentic smoke，采第一片证据并完成 tool lane 的 live 复测。

- 不翻 OwlCoda/OwlCC **正式默认**（later gated step）。
- 不**全局**去 `:8009`。
- **不 claim replacement complete / 不晋级任何 capability**。pilot 通过 = blocker ④ / gap 5 的一片证据 + tool lane live 证据；替代 verdict 仍 `not yet replaceable`。

---

## 1. 架构

两部分：

- **(A) owlmlx 侧就绪 + 证据 harness** — 全 owlmlx-internal，守 hard rule；harness 放 `scripts/`，**不新建 `owlmlx/` 规格模块**（AGENTS 规则）。
- **(B) 受控、非默认 OwlCoda agentic smoke** — 一个临时 run 配置直连 owlmlx-only（Qwen + tool lane），跑真实工具循环、采证。**不提交 OwlCoda repo 任何文件。**

---

## 2. 配置约定（constraint #1 — `:8066` 是默认不是契约）

- 基址一律走 **`OWLMLX_PILOT_BASE_URL`**，默认示例 `http://127.0.0.1:8066`。spec / harness / evidence **不硬编码端口为契约** —— 端口换了文档不应过早老化。
- model id、session 标识、OwlCoda profile 同理参数化，不写死。

---

## 3. 组件

### 3.1 owlmlx 就绪核验

确认：Qwen 在 `$OWLMLX_PILOT_BASE_URL` 的 native backend 可加载；tool lane（`fe528fe9`）live 可用；可见性真源（`/v1/openai/models`、`/v1/runtime/model-visibility`）正确；monitor/ledger 可采证。

- **readiness 失败也产出 artifact（constraint #4）**：任一就绪项不满足（Qwen 未加载 / visibility 不对 / tool forcing 不工作）→ 落 `pilot_readiness_failed` verdict（含失败项 + 证据），直接喂 R1/R4 blocker。**不允许"没跑成所以没结果"。**

### 3.2 pilot 证据 harness（`scripts/`）

复用 `/v1/runtime/monitor/snapshot` + history + ledger；给 pilot 会话打标；把 §4 的证据落 `files/evidence/owlmlx/...`。

### 3.3 受控 OwlCoda pilot 配置（非默认、临时）

只指 `$OWLMLX_PILOT_BASE_URL`（Qwen）、该会话内关 `:8009` 回退；跑一个真实 agentic 工具循环。**不提交 OwlCoda repo 文件。**

---

## 4. 证据 schema（落盘）

### 4.1 复现信息（constraint #5 — OwlCoda 不提交文件，但命令/env 全记录）

必须记录：**启动命令、env（含 `OWLMLX_PILOT_BASE_URL`）、owlmlx commit、base URL、model id、session id、request ids**。以后复现靠这条。

### 4.2 `fallback_used=false` 双重证明（constraint #2）

不能只凭 pilot 配置声明"关了回退"。证据须含两面：

- **(a) OwlCoda 侧**：实际 base URL / provider 配置快照（证明指向 owlmlx，不是 `:8009`）。
- **(b) 请求路径**：日志 / harness 证明本轮**未访问** `:8009` / oMLX fallback path。可接受形式：owlmlx 侧 request ledger 覆盖本轮全部请求 **且** 无对 `:8009` 的出站；或 OwlCoda 侧 fallback 计数 = 0 **且** 出站 host 仅 owlmlx。

### 4.3 tool lane live 复测 = 独立子门（constraint #3）

agentic loop "passed" **不**自动 = tool lane verified。拆成 4 条**独立**记录：

- `tool_call_emitted=true` — owlmlx 真发出 tool_call
- `tool_call_executed=true` — OwlCoda 真执行了该工具
- `tool_result_roundtrip=true` — 工具结果回填 owlmlx
- `final_answer_after_tool=true` — 回填后 owlmlx 续写出最终答案

任一为 false = tool lane live 复测**未过**（即便 loop"看起来"完成）。

### 4.4 health gate（constraint #6 — watermark 谨慎口径）

`watermark_red_observed=false` 可作 **health gate**，但只记成 **"本会话未触发 RED"**，**不**写成 stability 结论。sustained stability 是 R4 Phase B（soak）的事，本 spec 不 claim。

---

## 5. 数据流

OwlCoda（pilot 配置）→ owlmlx `$OWLMLX_PILOT_BASE_URL`（native, Qwen）→ `tool_calls` → OwlCoda 执行工具 → 回 owlmlx → final answer；owlmlx monitor/ledger 记录；harness 抽证（§4）。

---

## 6. 错误处理 / 回滚

- owlmlx-only 中途失败（工具解析 / 模型错）= **记下来**（证据，喂 R1/诊断）；pilot 内**不**自动回退 `:8009`（正是要验的）。
- readiness 失败 → `pilot_readiness_failed` artifact（§3.1）。
- 回滚：pilot 非默认、日常驱动没动，**无需回滚**。

---

## 7. Definition of Done

1. owlmlx 就绪核验通过 **或** 落 `pilot_readiness_failed` artifact（§3.1）。
2. 若就绪：一次真实 agentic 工具循环 owlmlx-only 完成。
3. 证据含 §4.1 复现信息（命令 / env / commit / base URL / model / session / request ids）。
4. `fallback_used=false` 经 §4.2 **双重**证明（配置快照 + 无 `:8009` 出站）。
5. tool lane 4 子门（§4.3）各自独立记录（true/false）。
6. health gate（§4.4）按"本会话未触发 RED"口径记录，**不**外推 stability。
7. 产出 pilot verdict（`passed` / `pilot_readiness_failed` / `loop_failed`）+ 喂 blocker ④ / gap 5 + R1 的 findings。
8. 零无出处断言；**不** claim replacement complete、**不**晋级 capability。

---

## 8. 范围外

- 不翻 OwlCoda/OwlCC 正式默认；不全局去 `:8009`。
- 不碰非-Qwen 工具调用（→ R1）；更广交互形态 parity（→ R1）。
- 不做持续 soak（→ R4 Phase B）。
- owlmlx 改动仅 owlmlx-internal（就绪核验 + 证据 harness in `scripts/`）；不提交 OwlCoda/OwlCC 文件。
- 不 claim sustained stability。

---

## 9. Hard Rules

1. owlmlx 侧改动只在 owlmlx 内（harness 进 `scripts/`，不新建 `owlmlx/` 规格模块）。
2. 基址走 `OWLMLX_PILOT_BASE_URL`；`:8066` 仅默认示例、非契约。
3. `fallback_used=false` 双重证明，缺一不可。
4. tool lane 4 子门独立判定，不靠 loop 整体"看起来通过"代替。
5. readiness 失败必产 artifact，不允许"没结果"。
6. watermark 只作 health gate，不作 stability 结论。
7. 不翻默认、不 claim replacement complete、不晋级 capability。

---

## 10. 验证（怎么算"做对"）

Phase 1 pilot 做对 = §7 DoD 全满足 + 证据可经 §4.1 复现 + §4.2 / §4.3 / §4.4 的口径**未被越界 claim**（无单次 pilot → sustained stability、无 loop-passed → tool-lane-verified、无 pilot-passed → replacement-complete 的跳跃）。
