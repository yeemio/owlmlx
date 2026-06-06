# R4 Phase B · B1 — Stage the Default Flip（OwlCoda owlmlx-primary + `:8009` fallback retained）— Design Spec

> 文档 grade：design-grade · 见 [README.md](README.md)
> Status：draft 2026-06-06 · Phase B sub-gate **B1**（of B1 flip → B2 soak → B3 remove）
> Campaign：替代收口 R-series — **R4 Phase B**（blocker ④ + gap 5：ops cutover + customer-runtime evidence）
> Plan-grade 来源：[`../../source-of-truth/runtime13-replacement-rebaseline-verdict.md`](../../source-of-truth/runtime13-replacement-rebaseline-verdict.md) §5（R4）；[`r4-phase1-pilot-closeout.md`](../../source-of-truth/r4-phase1-pilot-closeout.md) §4
> **Phase：B1 only** — 设计 + **owlmlx 侧** flip-readiness 门 + flipped-state 证据 schema。**消费者翻默认/改码 EXECUTION 全程 gated（runbook，用户执行）**。不删 `:8009`、不 claim sustained、promotes nothing。

---

## 0. 位置 + Phase B 分解 + 验收口径

runtime13 R4 = 把消费者切到 owlmlx + 去 `:8009` + 采 customer evidence。Phase-1 pilot ✅（一次受控 `OwlCoda→owlmlx→Qwen→Bash→final` loop，`da6f35e3`）。Phase B = **真 cutover**，按**不可逆性 staged**（用户 2026-06-06 定序）：

- **B1（本 spec）**：OwlCoda 翻默认到 **owlmlx-primary + `:8009` 兜底保留**（翻默认可逆 = revert config）；附 OwlCC preflight 修法（解锁 future repoint）。owlmlx 侧出 flip-readiness go/no-go 门 + flipped-state 证据 schema。
- **B2（later spec）**：真流量 **sustained soak**（采 customer-runtime evidence）。
- **B3（later spec）**：去 `:8009` + OwlCC repoint。

**消费者回退不对称（scout 确认）**：
- **OwlCoda**：多后端（`ollama/lm-studio/vllm/owlmlx`）+ owlmlx-gate + 跨后端容灾 → 能"owlmlx-primary + `:8009` 兜底"，**翻默认安全可逆**。
- **OwlCC**：single `routerUrl`（一个指针，无内建 fallback）→ repoint 即 owlmlx-only 无兜底（= Phase-1 裸跑姿态）→ **repoint 推迟到 B3**；B1 只先做其 preflight 修法。

→ **B1 聚焦 OwlCoda。**

**验收**：owlmlx 侧 flip-readiness 门给 `go`/`no_go` verdict（`go` 才允许翻）；flipped-state 证据 schema 定义并（用户翻默认后）采证，或落 "designed, execution gated" 状态；consumer flip + rollback runbook 落；OwlCC preflight 修法落（gated）；**promotes nothing；不删 `:8009`；verdict 仍 `not yet replaceable`**。

---

## 1. 架构

- **(A) owlmlx 侧**（`scripts/`，**复用 R2 conformance + R4 readiness harness**，不新建 `owlmlx/` 模块 — AGENTS 规）：flip-readiness 编排器 + flipped-state 证据 schema/assembler。
- **(B) 消费者侧**（**gated**：runbook + OwlCC 代码修法；owlmlx **不自动**改消费者 config）：OwlCoda owlmlx-gate 翻 + OwlCC preflight 修 + 回滚程序。

---

## 2. flip-readiness go/no-go 门（owlmlx 侧，`scripts/`）

翻 OwlCoda 默认**前**必须 owlmlx 侧 green。编排器 = thin orchestrator，复用既有：
- **R2 conformance**（`r2_control_plane_conformance.py probe-contracts`）：OwlCoda 的 4 个 owlmlx-gate 契约 pass（已知 `contract_gap_found` 的唯一 gap 是 OwlCC-side `/v1/models`，**不阻断 OwlCoda 翻默认**）。
- **R4 readiness**（`r4_ops_cutover_pilot.py probe-readiness`）：OwlCoda 要的 model（Qwen；Gemma 视 R1）visible + loadable + tool lane live + monitor 可达。
- visibility 真源（`/v1/openai/models`、`/v1/runtime/model-visibility`）正确。

聚合纯函数 `evaluate_flip_readiness(conformance_verdict, readiness_verdict) -> {verdict: go|no_go, blocking[]}`：仅当 conformance 无 **OwlCoda-side** gap **且** readiness pass → `go`；否则 `no_go` + blocking 列表。**任一不绿必产 `no_go` artifact（不允许"没结果"）。**

---

## 3. flip + fallback-retention（消费者侧，gated runbook）

- **OwlCoda**：owlmlx-gate 设 owlmlx 为 **primary** backend；`:8009`/其它 backend **保留为 fallback**（OwlCoda 原生跨后端容灾）。**绝不删 fallback**（删 = B3）。
- **OwlCC preflight 修法**：preflight 读 `/v1/openai/models` 取可用性真相（R2 冻结契约），不再单读 `/v1/models→data[].id`。**仅修 preflight；repoint 推迟 B3。**
- **回滚**：revert OwlCoda config（owlmlx-gate 退回原默认）；OwlCC preflight 修法是纯增强（读对的 endpoint），无需回滚。**可逆。**

> EXECUTION 是 gated runbook step —— owlmlx **不**自动改消费者仓 / config。runbook 写清每步命令 + 验证 + 回滚。

---

## 4. flipped-state 证据 schema（owlmlx 侧，落盘）

翻默认后采（复用 R4 evidence + monitor/ledger）：
- **翻前** flip-readiness verdict（`go`）。
- **翻后**：owlmlx request ledger 覆盖默认流量（证明 owlmlx 在服务，via request-id inbound 覆盖，同 Phase-1 手法）。
- **`fallback_used` 基线**（OwlCoda 侧 fallback 计数 / 出站 host）：**`>0` = owlmlx 仍有缺口的诚实信号**（喂回 R1/诊断）；`=0` = 本批未触发回退（**不外推 sustained —— 那是 B2**）。
- 复现：cmd · env · owlmlx commit · 消费者 config 快照（证明 primary=owlmlx + fallback 保留）· model · session · request-ids。

**诚实**：B1 证据 = "flip staged + 初始真流量被 owlmlx 服务 + `:8009` 兜底保留"，**非** sustained（B2）、**非** replacement-complete、**非** capability 晋级。

---

## 5. 数据流

flip-readiness 门(`go`) → 消费者按 runbook 翻 OwlCoda 默认（owlmlx-primary + `:8009` fallback）+ 修 OwlCC preflight → 真流量进 owlmlx → owlmlx ledger/monitor 采证 + OwlCoda fallback 计数 → flipped-state 证据（§4）。

---

## 6. 错误处理 / 回滚

- flip-readiness `no_go` → **不翻**，落 verdict + blocking 项（喂 R1/R2/诊断）。
- 翻后 owlmlx 出问题 → OwlCoda **自动回退 `:8009`**（这正是保留 fallback 的意义）；`fallback_used>0` 记为诚实信号；可随时 revert config 全退回原默认。
- B1 **不删 `:8009`、不碰 OwlCC repoint** → 回滚成本低、风险可控。

---

## 7. Definition of Done

1. flip-readiness 门 harness（复用 R2 + R4，纯函数聚合）给 `go`/`no_go` verdict + blocking artifact。
2. flipped-state 证据 schema 定义；用户翻默认后采证，**或**（未翻时）落 "designed, execution gated" 状态记录。
3. consumer flip + rollback runbook 落（OwlCoda owlmlx-gate 翻法 + `:8009` 兜底保留 + revert 步骤 + 验证命令）。
4. OwlCC preflight 修法落（gated；读 `/v1/openai/models`）+ 说明不破 OwlCC 其它 preflight 行为。
5. §4 复现信息齐。
6. 纯函数 evaluator 单测（`evaluate_flip_readiness` 的 go / no_go 分支）。
7. promotes nothing；**不删 `:8009`**；OwlCC repoint 不在本 gate；verdict 仍 not-yet。
8. 零无出处断言；honest：B1 ≠ sustained ≠ replacement-complete。

---

## 8. 范围外

- sustained soak（**B2**）、去 `:8009`（**B3**）、OwlCC repoint（**B3**）。
- 非-OwlCoda 消费者翻默认（OwlCC = B3）。
- capability 晋级 / §1a Gate。
- 真翻默认的 **EXECUTION**（用户按 runbook gated 做；owlmlx 侧只建门 + 证据 schema + runbook + OwlCC 修法）。
- 非-Qwen tool-calling parity（→ R1）。

---

## 9. Hard Rules

1. owlmlx 侧改动只在 owlmlx 内（harness 进 `scripts/`，**复用** R2/R4，**不新建 `owlmlx/` 模块**）。
2. flip-readiness 不绿不翻；`no_go` 必产 artifact，不允许"没结果"。
3. `:8009` 兜底 **B1 保留**，绝不在 B1 删（B3 才删）。
4. consumer flip / OwlCC 改码 EXECUTION 是 **gated runbook step**；owlmlx **不**自动改消费者 config 或提交消费者仓文件。
5. `fallback_used>0` 诚实记为 owlmlx 缺口信号，不藏、不粉饰。
6. 不晋级 capability；不 claim sustained / replacement-complete。
7. evidence-language 校准：B1 = "flip staged + 初始真流量服务 + 回退保留"；**禁** sustained / parity / equivalent / replaces / replacement-complete / superior。
8. staging 只动 round-scope；**绝不** `uv.lock` / `owlmlx/speculative/*` / 既有脏文件。

---

## 10. 验证（怎么算"做对"）

§7 DoD 全满足 + `evaluate_flip_readiness` 单测绿 + runbook 可操作（含回滚）+ OwlCC preflight 修法不破其它 preflight + 无越界 claim（无 B1→sustained、无 flip→replacement-complete 跳跃）+ `:8009` 兜底在 B1 保留。
