# R2 — Production Control-Plane Closure（consumer-contract conformance + operability rehearsal）— Design Spec

> 文档 grade：design-grade · 见 [README.md](README.md)
> Status：draft 2026-06-06 · scope = **档2**（consumer-contract closure + control-plane operability rehearsal）· auth/rate-limit/quota **out of scope** · promotes nothing；§1a 不动
> Campaign：替代收口 R-series — **R2**（blocker ②：production control-plane closure）
> Plan-grade 来源：[`../../source-of-truth/runtime13-replacement-rebaseline-verdict.md`](../../source-of-truth/runtime13-replacement-rebaseline-verdict.md) §3 blocker ② + §5（R2）
> **Phase：Phase-1 closure only** — 验证现有控制面 surface 闭合消费者契约 + 一次受控 operability 演练。**停在现有 capability label，不走 §1a 晋级。**

---

## 0. 位置 + 验收口径

R2 收 blocker ②（production control-plane closure）。**关键定性（R0 / runtime13 已确立）**：控制面 **surface 已基本建好** —— `/v1/runtime/status` frozen contract、`/healthz`、restart、model-visibility、monitor/metrics 皆 **supported**；runtime13 §3 评 blocker ② = `◐ surfaces strong`，「大多不阻断 …… remaining is **ops verification**」。代码侧坐实：owlmlx 现已服务 ~41 个 control-plane endpoint。

**因此 R2 ≠ 造控制面，而是收口最后一公里：**
- **(A) 消费者契约闭环** —— 验证现有控制面 endpoint 的**响应形状/语义**真的满足消费者实际读取的契约（OwlCoda `owlmlx-gate`、OwlCC preflight）。
- **(B) 控制面 operability 演练** —— 用现有 endpoint 跑一次受控控制面生命周期（load → status → switch → evict → restart → watermark），证明各面在状态变迁时报告正确。
- **(C) last-mile 契约冻结** —— probe 抓到的「消费者依赖但未冻结」契约写进 source-of-truth 定死。

**验收**：每个消费者契约给 per-contract conformance verdict；operability 演练给 lifecycle verdict；聚合 R2 verdict 三态（`passed` / `contract_gap_found` / `rehearsal_failed`）；证据 + 复现落盘；抓到的 gap 落 documented gap（**诚实结论，非要藏的失败**）；operator runbook 落盘；**promotes nothing，labels 不变，不动消费者默认**。

---

## 1. 架构

两个独立 verifier + 证据/runbook 层，**全部进 `scripts/` + `tests/`，不新建 `owlmlx/` 模块**（守 AGENTS module-as-spec 规）：

- **(A) 消费者契约 conformance probe**（`scripts/replacement/r2_control_plane_conformance.py`）— 只读打 owlmlx 控制面 endpoint，对每个消费者契约断言响应字段 / 语义。
- **(B) 控制面 operability 演练**（`scripts/replacement/r2_control_plane_operability.py`）— 驱动控制面生命周期，断言每步状态被对应面正确报告。**会改运行态 → 隔离 bench server。**
- **(C) 证据 + 冻结 + runbook** — evidence artifact、source-of-truth 契约冻结、operator runbook。

断言逻辑写成**纯函数**（给响应 dict → 返回 sub-verdict），与 HTTP / IO 分离，`tests/` 无需活 server 即可单测（仿 R4 evaluator 模式）。

---

## 2. 消费者契约定义（从消费者源码反推，不靠猜）

契约的**真相在消费者解析代码**；实现时先读 OwlCoda `admin/src/lib/availability.ts`（+ `admin/src/api/types.ts`）与 OwlCC `src/preflight.ts`，把它们实际解析的字段 / 期望固化为断言。本节给出 R0 跨仓只读已知的契约骨架（跨仓读 **只读**，不改消费者任何文件）：

### 2.1 OwlCC preflight 契约
- `GET /healthz` → 期望 `{ok, readiness, …}`；preflight 据此判活 + 可路由。
- `GET /v1/models` → preflight 取模型清单做可用性判断。
- **已知风险（重点目标）**：owlmlx `/v1/models` 语义 = **仅已加载**（loaded inventory），而**可用性真相在 `/v1/openai/models`**。若 OwlCC preflight 把 `/v1/models` 当「可用模型全集」，则与 owlmlx 语义错位 → R2 必须显式断言并出 verdict + 落契约（要么消费者改读 `/v1/openai/models`，要么文档定死语义供 cutover runbook 指引）。
- owlmlx 须存在 OwlCC 所需 shape：Anthropic `/v1/messages`（**数据面存在性**，非推理质量 —— 那归 R1 / R4）。

### 2.2 OwlCoda owlmlx-gate 契约
- `GET /v1/openai/models` → 可用性真相（OpenAI 格式 list，仅 visible 模型）。
- `GET /v1/runtime/model-visibility` → 诊断（visible / technical_preview / blocked + per-model gate reason）。
- `GET /v1/models` → 仅已加载清单（loaded inventory only，语义与上二者区分）。
- gate 已在消费者侧建模（`types.ts` 区分 `owlmlx_runtime_model_visibility | legacy_router_platform_model_visibility`）→ R2 断言 owlmlx 三个面的响应满足 gate 的解析期望。

---

## 3. 组件

### 3.1 消费者契约 conformance probe（`scripts/replacement/r2_control_plane_conformance.py`，新增）
- 子命令 `probe-contracts --base-url <owlmlx>`：按 §2 逐契约 GET → 纯函数 `evaluate_<contract>(response_json) -> ContractVerdict`（字段在 / 语义对 / 缺失项列举）。
- 输出 per-contract verdict + 聚合 conformance verdict；落 evidence。**只读**，不改任何运行态。
- 不依赖消费者运行 —— 契约期望以断言形式内联（来源：消费者源码引用，记在 probe 注释 + §2）。

### 3.2 控制面 operability 演练（`scripts/replacement/r2_control_plane_operability.py`，新增）
- 子命令 `rehearse --base-url <bench> --model <small>`：按序驱动并断言 ——
  1. **load** `POST /v1/load` → `GET /healthz` + `/v1/runtime/status` 反映 `active_model_id` / `readiness=ready`；
  2. **model-switch** load / 切第二模型 → status 反映新 active；
  3. **evict** `GET /v1/runtime/memory-pressure-eviction-policy`（候选排序）→ `POST /v1/runtime/memory-pressure-eviction` → 返回 `selected_victim` + status 反映；
  4. **restart** `POST /v1/runtime/restart` → `GET /v1/runtime/recovery-supervisor-contract` + status 反映；
  5. **watermark** 全程 `GET /v1/runtime/memory-watermark` → `level` + recommended action 与内存变迁一致。
- 每步纯函数断言 → step sub-verdict；聚合 lifecycle verdict。
- **会改运行态** → **隔离 bench server（不碰 :8066），最小够用模型**；执行时 **flag 机器成本 + run-now-vs-defer**（重模型 load / evict 吃时间与内存）。

### 3.3 证据 + 契约冻结 + runbook
- 证据 → `files/evidence/owlmlx/replacement/r2-control-plane/`（per-contract + lifecycle verdict + 完整复现）。
- **契约冻结**：probe 抓到的「消费者依赖但 source-of-truth 未冻结」契约（首要：`/v1/models` vs `/v1/openai/models` 语义）→ 写进相应 source-of-truth（如 `runtime-model-visibility-contract.md`）或 R2 closeout 定死。**仅文档**；除非确认 owlmlx 真 bug 才动码（动码走独立 TDD round）。
- **operator runbook** `docs/architect/design/R2-control-plane-runbook.md`：cutover 前 / 中操作员如何用这些 endpoint 验证控制面 readiness（含每契约 expected 响应 + 演练复现步骤）。

---

## 4. 证据（落盘）
`files/evidence/owlmlx/replacement/r2-control-plane/`：
- **conformance**：per-contract verdict（contract id / endpoint / 断言项 / `pass|gap` / 实际响应摘要）；
- **operability**：per-step sub-verdict + lifecycle verdict + 演练 bench recipe；
- **复现**：cmd · env · owlmlx commit · base URL · model id · endpoints。

**诚实**：verdict 仅表「consumer-contract conformance + 受控 operability 已验证」，**非** parity / equivalent / replacement-complete；一次受控演练 ≠ sustained。

---

## 5. 数据流
消费者契约（反推自消费者源码）→ probe 打 owlmlx 控制面 endpoint → 纯函数 shape / 语义断言 → per-contract / per-step sub-verdict → 聚合 R2 verdict（`passed` / `contract_gap_found` / `rehearsal_failed`）→ 证据落盘 +（有 gap）documented gap +（未冻结）source-of-truth 冻结 → operator runbook。

---

## 6. 错误处理 / 回滚
- probe 只读；演练跑隔离 bench（不碰生产 :8066）；产物全是 docs / evidence。
- contract gap / rehearsal 失败 → 产对应 verdict + artifact（**不**静默、**不**掩盖）；不阻断、不改默认。
- 回滚 = revert docs / evidence（无运行态默认被改）。

---

## 7. Definition of Done
1. 每个 §2 消费者契约有 per-contract conformance verdict（`pass` 或 documented gap），断言来源（消费者源码）有引用。
2. `/v1/models` vs `/v1/openai/models` 语义错位被**显式**断言并出 verdict + 落契约冻结 / 指引。
3. 控制面 operability 演练一次受控跑（隔离 bench）给出 5 步 sub-verdict + lifecycle verdict（或落 `rehearsal_failed` artifact）。
4. 聚合 R2 verdict 三态明确。
5. 纯函数 evaluator 单测（contract evaluators + lifecycle step evaluators），无需活 server。
6. 证据（§4）+ 复现落盘；operator runbook 落盘。
7. capability / source-of-truth 措辞**诚实更新**：控制面消费者契约 conformance + operability 已验证（**受控、一次性**），**不晋级**、promotes nothing、§1a 不动。
8. 零无出处断言；不动消费者默认；不去 :8009。

---

## 8. 范围外
- **auth / api-key / rate-limit / quota / usage-ledger** —— owlmlx 当前为零；按 stabilization1 + R0，控制面 ownership / auth 属 platform-shell / 网络层，**不归单主机 boundary**（选 R2 即排除）。
- 多后端 **routing**、模型 **curation**（`model_fleet/status.json`）—— platform-shell。
- fallback **移除** + 默认翻转 + sustained soak —— **R4**（Phase B）。
- backend 质量 parity —— R4 内 no-regression。
- experimental → supported 晋级 —— 不做。
- 演练**不**下稳定性 / sustained 结论；watermark 仅 per-session health gate，不作稳定性判据。

---

## 9. Hard Rules
1. probe / 演练进 `scripts/replacement/`；测试进 `tests/`；**不新建 `owlmlx/` 模块**（AGENTS）。
2. conformance probe **只读**；operability 演练**只在隔离 bench**，不碰 :8066。
3. 契约期望**反推自消费者源码**，不靠猜；断言来源有引用。
4. 演练吃机器时间 → 跑前 flag 成本 + run-now-vs-defer；用最小够用模型。
5. 不动消费者默认；不去 :8009；不 promote、labels 不变、§1a 不动。
6. evidence-language 校准：只说 conformance / operability-verified（受控、一次性），**禁** parity / equivalent / replaces / replacement-complete / superior。
7. 抓到 gap = documented gap（诚实落盘），除非真 bug 才动码（独立 TDD round）。
8. staging 只动 round-scope 文件；**绝不** stage `uv.lock` / `owlmlx/speculative/*` / 既有脏文件。

---

## 10. 验证（怎么算"做对"）
§7 DoD 全满足 + evaluator 单测绿 + conformance probe 证据可复现 + operability 演练 verdict 明确（或 documented `rehearsal_failed`）+ `/v1/models` 语义错位有显式处理 + runbook 落盘 + 无 capability 晋级 + 不动默认 / 不去 :8009。
