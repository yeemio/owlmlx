# R0 Replacement Re-baseline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (inline) or superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.
> **Spec:** [`R0-replacement-rebaseline-spec.md`](R0-replacement-rebaseline-spec.md)
> **Plan-grade 来源:** [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) 下阶段主线声明 + Runtime-12 §7

**Goal:** 产出 `docs/source-of-truth/runtime13-replacement-rebaseline-verdict.md` —— 基于当前证据，把 4 个 Runtime-12 blocker + 5 个 replacement-grade stability gap 重新分类，每条给 "是否阻断 owlmlx-only cutover" 判定，收窄成驱动 R1/R2/R4 的剩余清单。

**Architecture:** 纯只读评估（READ-ONLY）。对 owlmlx + OwlCoda + OwlCC + oMLX 只读取证；证据按固定优先级（SoT 当前文档 → capability matrix → 真实测试/evidence ledger → 当前代码路径 → commit 仅作补充 provenance）；旧文档仅加顶部 stale banner，不改正文结论。无代码/测试改动。

**Tech Stack:** Markdown docs；`grep`/`read` 跨 4 repo；`scripts/bench/session_kv_soak_audit.py`（已存在，读其输出，不改）；`git log`（仅 provenance）。

---

## 文件结构

- **Create:** `docs/source-of-truth/runtime13-replacement-rebaseline-verdict.md` —— R0 唯一新产物（verdict + 分类 + cutover 判定 + 收窄清单）。
- **Modify（banner-only）:** `docs/source-of-truth/runtime12-replacement-readiness-verdict.md`、`docs/source-of-truth/replacement-grade-stability-gaps.md` —— 仅加顶部 banner 指向 runtime13。
- **Read-only（取证，不写）:** `docs/source-of-truth/runtime-capability-matrix.md`、`README.md`、`files/evidence/owlmlx/...`、owlmlx 相关代码路径；`/Users/yeemio/AI/gitrep/owlcoda`、`/Users/yeemio/AI/gitrep/owlcc`（必要时 `owlcc-byoscc`）、`/Users/yeemio/AI/gitrep/omlx-upstream`。

**节奏说明:** R0 是单一演进文档 + 跨 repo 取证；不每任务一 commit（会造 churn）。全程在工作树累积，**Task 6 一次 docs-only commit**。push 由用户显式放行（本会话已确认 push 受控）。

---

## Task 1: Cutover 实况（跨 repo 只读）

**Files:** Read `/Users/yeemio/AI/gitrep/owlcoda`、`/Users/yeemio/AI/gitrep/owlcc`、`/Users/yeemio/AI/gitrep/omlx-upstream`；Write §2 of runtime13。

- [ ] **Step 1: 读 OwlCoda 的 runtime 指向 / fallback**

只读 grep（不改任何文件）。候选取证项（命中即引用 file:line）：

```bash
cd /Users/yeemio/AI/gitrep/owlcoda
grep -rniE '8066|8009|localRuntimeProtocol|fallback|baseUrl|base_url|upstream|owlmlx|anthropic.*url|provider' \
  --include='*.ts' --include='*.js' --include='*.json' --include='*.md' . | grep -viE 'node_modules|test/|\.test\.' | head -60
```

预期分辨：默认 runtime 是 owlmlx（:8066）还是老平台（参照 campaign-A 记忆：默认 upstream 曾为 :8009，8066 为 config）；是否存在 oMLX/老平台 fallback 分支。

- [ ] **Step 2: 读 OwlCC 同口径**

```bash
cd /Users/yeemio/AI/gitrep/owlcc
grep -rniE '8066|8009|localRuntimeProtocol|fallback|baseUrl|base_url|upstream|owlmlx|provider' \
  --include='*.ts' --include='*.js' --include='*.json' --include='*.py' --include='*.md' . | grep -viE 'node_modules|test/' | head -60
```

- [ ] **Step 3: 写 §2「Cutover 实况」**

在 runtime13 写出：(a) OwlCoda/OwlCC 当前默认 runtime 指向；(b) 是否仍有 oMLX 回退路径；(c) "今天关掉回退会炸什么"（基于配置/代码的判断，**只读、不实操关闭**）。每条带 `repo:file:line` 引用。

**Done-when:** §2 三问全有答案，每条有 owlcoda/owlcc 的具体出处引用；无任何被读 repo 文件被修改（`git -C <repo> status` 干净）。

---

## Task 2: 重判 4 个 Runtime-12 blocker

**Files:** Read capability-matrix / evidence / owlmlx code；Write §3 of runtime13。

- [ ] **Step 1: 逐 blocker 取证 + 分类**

对以下 4 条，各产出一个三元组 ——`分类`（✅4月后已闭合 / ◐部分闭合[写清剩什么] / ⛔仍开放）+ `证据`（按优先级取，commit 仅补充）+ `cutover-blocking 判定`（会 / 不会 / 取决于 X）：

1. **① source-first parity 未冻**（across all interaction shapes）
2. **② 生产控制面闭环未冻**
3. **③ backend 质量 parity 未证** —— 本 campaign **降级 no-regression**；判定只需"是否导致明显退步到阻断 cutover"
4. **④ ops 级替代未验**

取证起点（只读）：`runtime-capability-matrix.md`（如 OpenAI/Anthropic compat、tool-calling、doctor 行）、近期 evidence、`server_routes_openai.py` 等代码路径；近期 commit（`10e023d4`/`fe528fe9`/`189d9d5c`/`a4637151`）仅作 provenance。

- [ ] **Step 2: 写 §3**，4 条三元组成表/小节。

**Done-when:** 4 个 blocker 每条都有 分类 + 证据引用（标注证据级别）+ cutover-blocking 判定；§3 不含无出处断言。

---

## Task 3: 重判 5 个 replacement-grade stability gap

**Files:** Read `replacement-grade-stability-gaps.md` + capability-matrix + evidence；Write §4 of runtime13。

- [ ] **Step 1: 逐 gap 取证 + 同三元组**

对：`host_stable_execution` / `cache_scheduler_depth` / `multi_model_lifecycle_governance` / `heavy_weight_runtime_repeatability` / `customer_runtime_evidence`，各给 分类 + 证据 + cutover-blocking 判定。

重点核对旧文档已知陈旧点（只读对照 capability-matrix）：native MLX backend 已落（旧"dominant gap=cache_scheduler→native backend"已 superseded）；B-1c §2 fast-count canonical 已过（`189d9d5c`）；B-2 prefix cache 进行中；多模型 pin/TTL/eviction supported。

- [ ] **Step 2: 写 §4**，5 条三元组。

**Done-when:** 5 个 gap 每条 分类 + 证据 + cutover-blocking 判定；显式标出"4 月文档已 stale 但此处按当前证据重判"的项。

---

## Task 4: 合成收窄清单 + 刷新 verdict

**Files:** Write §1 + §5 of runtime13。

- [ ] **Step 1: 写 §5「收窄后剩余 blocker 清单」**

从 Task 2/3 里筛出 cutover-blocking 判定 = "会" 或 "取决于" 的项，逐条映射到 **R1 / R2 / R4**（R3 已降级）。判定 = "不会" 的项标注"非 cutover 必做"，移出关键路径。

- [ ] **Step 2: 写 §1「刷新 verdict」**

一句话 verdict（很可能仍 `not yet replaceable`，但附**当前**、收窄的理由），并显式声明：不晋级任何 capability；Session KV / prefix cache 仍 `experimental`。

**Done-when:** §5 每项 → R-target + cutover-blocking；§1 verdict 与 §3/§4 结论自洽（无矛盾）。

---

## Task 5: 旧文档加 stale banner（克制）

**Files:** Modify（banner-only）`runtime12-replacement-readiness-verdict.md`、`replacement-grade-stability-gaps.md`。

- [ ] **Step 1: 各加一条顶部 banner**

形如：

```markdown
> **⚠️ Re-baselined 2026-06-03 — see [`runtime13-replacement-rebaseline-verdict.md`](runtime13-replacement-rebaseline-verdict.md).** 本文档的 blocker/gap 结论为 2026-04 point-in-time；最新分类与 cutover-blocking 判定以 Runtime-13 为准。本文档正文未改写。
```

- [ ] **Step 2: 确认只加 banner**

```bash
git diff --numstat -- docs/source-of-truth/runtime12-replacement-readiness-verdict.md docs/source-of-truth/replacement-grade-stability-gaps.md
```

**Done-when:** 两文档各仅 +N/−0（纯加 banner），正文结论零改写。

---

## Task 6: DoD 自检 + 一次 commit

**Files:** 全部 R0 产物。

- [ ] **Step 1: 对照 spec §2.7 DoD 自检**

逐条核：4+5 每项有分类+证据；每 blocker 有 cutover-blocking 判定；§2 cutover 实况完成；runtime13 落地 + 两旧文档 banner；§5 清单冻结可驱动 R1/R2/R4；零无出处断言、无 commit-only 依据。

- [ ] **Step 2: 精确 stage + 提交（docs-only）**

```bash
git add docs/source-of-truth/runtime13-replacement-rebaseline-verdict.md \
        docs/source-of-truth/runtime12-replacement-readiness-verdict.md \
        docs/source-of-truth/replacement-grade-stability-gaps.md
git diff --cached --name-only   # 期望恰好 3，且无 uv.lock/speculative 等无关脏文件
git commit -m "docs(replacement): R0 re-baseline -> runtime13 verdict (no promotion)"
```

- [ ] **Step 3: push 留给用户显式放行**（本会话 push 受控；不自动 push）。

**Done-when:** 3 文件已 commit；暂存无泄漏；HEAD 为该 commit；未 push。

---

## Self-Review（写计划后自检）

- **Spec coverage:** R0 spec §2.3(方法/跨repo/证据优先级)→Task 1-3；§2.4(cutover 实况)→Task 1；§2.5(交付物)→Task 1-4；§2.6(banner 克制)→Task 5；§2.7(DoD)→Task 6;§2.8(out-of-scope，纯只读)→贯穿（无代码/测试/cutover-config 改动）。无遗漏。
- **Placeholder scan:** 无 TBD/TODO；每任务有具体 grep/写作内容 + done-when。runtime13 各 §的内容在执行时由证据填充（评估型任务的正常形态，非占位）。
- **一致性:** §编号（§1 verdict / §2 cutover / §3 blockers / §4 gaps / §5 收窄清单）在 Task 1-4 与 spec §2.5 对齐；三元组字段（分类/证据/cutover-blocking）在 Task 2/3 一致。
