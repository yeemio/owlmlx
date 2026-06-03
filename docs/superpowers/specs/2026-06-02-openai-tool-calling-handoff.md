# OwlMLX 工具调用 lane — Handoff（2026-06-02）

> 用大白话写给下一个人（或下一个会话）。目标：不用回看聊天记录，也能接着干。

---

## 一句话现状

owlmlx 的 OpenAI 工具调用，已经从"能聊天的实验接口"推进到 **工具循环 / 切模型 / 强制选工具 都通了**。
本次会话的三件事**已经提交、并 push 到 `origin/main`**（`10e023d4` = ①+②，`fe528fe9` = ③）；代码层面已经没有未提交的活了。唯一还没纳入版本库的是这两份 spec/handoff 文档（untracked，见第三节）。

---

## 一、已经在 main 上的（背景，别人之前推的）

- `cb0bd7cd` — 实验性 OpenAI 工具调用 lane：接受 OpenAI 工具消息格式（不再 422）、把工具历史喂进模板、Qwen 的 XML 工具调用解析成 OpenAI `tool_calls`、流式发 tool delta、`<think>` 隔离、source-of-truth 标 `experimental`。
- `f063d0df` — 工具调用诊断可见性：三处原来"静默失败"的地方，加了 warning + 可查的 `detail` 字段（`tool_parser_missing` / `tool_parse_dropped` / `template_render_fallback`）。

> 注：HEAD 现在还压了几个**无关的** bench/docs 提交（`420c2865`、`969796bf`、`1646ae93`）。

---

## 二、本次会话做的三件事（**已提交 + 已 push 到 origin/main**）

三件都走了 TDD（先写失败测试、再实现），并过了全量回归（model-free **1241 passed / 1 skipped**）。已落成两个 commit 并 push：`10e023d4`（①+②）、`fe528fe9`（③）。

### ① 流式重复 delta 修复（小，非阻塞）
- **是什么**：普通（非 buffered）流式分支里，同一个工具调用会在 `tool_use` 事件和 `done` 事件**各发一次**，导致重复。
- **怎么修**：加了 `tool_calls_streamed` 守卫——`tool_use` 发过了，`done` 就不再发；`finish_reason` 仍正确为 `tool_calls`。
- **文件**：`owlmlx/runtime/server_routes_openai.py` + 1 个回归测试。
- 注：OwlCoda 实际走 buffered 分支，本来不踩这个坑；这是顺手清的 latent bug。

### ② 切模型自动卸载（原始问题 5）
- **是什么**：以前内存不够切模型 → 返回 503 → OwlCoda 当成"过载"**反复重试** → 一串 confusing failure。
- **怎么修**：
  - kernel 新增 `load_model(evict_to_fit=True)`：内存不够时，**自动卸掉非 pinned 的旧模型**腾地方再加载；**pinned 的永不卸**。
  - compat 路由：把 `evict_to_fit=True` 接上；如果卸完还是放不下（目标自身超预算 / 全被 pin），返回 **409（不重试）** 而不是 503。
- **文件**：`owlmlx/runtime/kernel.py`、`owlmlx/runtime/server_routes_openai.py` + 2 个 kernel 测试 + 2 个路由测试。

### ③ tool_choice 强制选工具（Phase 2 #1）
- **是什么**：`tool_choice="required"`（必须调某个工具）或具名（必须调函数 X）时，以前只当 `auto` 处理、不强制。现在真强制。
- **怎么做**：用 **xgrammar 语法约束**把模型输出"逼"成合法的 Qwen 工具调用格式。
  - `_tool_choice_forcing_ebnf(tools, tool_choice)`：按工具表 + tool_choice 生成一份 EBNF 语法（required → 允许任一工具；具名 → 只允许那个函数；参数名取自各函数 schema）。
  - 复用了 F-4 现成的语法处理器（给它加了一个 `ebnf` 类型），在 native backend 的 `generate` 里挂成 `logits_processor`。
  - **优雅降级**：语法构建失败也不会让生成崩，只是不强制 + 记一条诊断。
- **可行性**：先做了 **model-free** 探测（只加载 tokenizer，不烧大模型），**6/6 通过**（named 只放行指定函数、required 强制任一工具、都拒绝纯文本）。
- **文件**：`owlmlx/runtime/mlx_native_backend.py`、`owlmlx/runtime/mlx_lm_runner.py` + 6 个测试 + 1 个 probe。
- **路由不用改**：路由本来就把 `tool_choice` 透传下去了。

---

## 三、完整文件清单（已提交，落在哪个 commit）

已提交（+504/−12，分两个 commit）。**`10e023d4`** = ①+②（`kernel.py`、`server_routes_openai.py` + 两个对应测试）；**`fe528fe9`** = ③（`mlx_native_backend.py`、`mlx_lm_runner.py`、`test_mlx_native_backend.py`）：

| 文件 | 属于 |
| --- | --- |
| `owlmlx/runtime/kernel.py` (+43) | ② |
| `owlmlx/runtime/server_routes_openai.py` (+43/−12) | ① + ② |
| `owlmlx/runtime/mlx_native_backend.py` (+101) | ③ |
| `owlmlx/runtime/mlx_lm_runner.py` (+3) | ③（ebnf 类型） |
| `tests/test_server_routes_openai.py` (+116) | ① + ② |
| `tests/test_memory_pressure_eviction_policy.py` (+53) | ② |
| `tests/test_mlx_native_backend.py` (+157) | ③ |

probe 也已提交（在 `fe528fe9` 里，+117）：

- `scripts/probe/phase2_tool_choice_forcing_feasibility.py` — ③ 的 model-free 可行性 probe。

仍未纳入版本库（untracked，是否提交待你定）：

- `docs/superpowers/specs/2026-06-02-openai-tool-calling-design.md` — 设计 spec（含 Phase 1/2 全貌）。
- `docs/superpowers/specs/2026-06-02-openai-tool-calling-handoff.md` — 本文件。

> **没碰**任何无关脏文件（`docs/architect/01-mainline-roadmap.md`、`owlmlx/speculative/suffix_decoding/__init__.py`、`uv.lock`、bench evidence 等照旧）。

---

## 四、下一步（建议顺序）

1. ~~先提交这三件~~ —— **✅ 已完成**：代码 + 测试 + probe 已分两个 commit 提交并 push 到 `origin/main`（`10e023d4` = ①+②，`fe528fe9` = ③）。
   - 唯一悬而未决：这两份 spec/handoff 文档要不要也纳入版本库（见第三节）。
2. **live 复测**（8066 + Qwen3.6，真机）：
   - 工具循环：发带 `tools` 的请求 → 期望 `tool_calls` + `finish_reason="tool_calls"`，回填 tool result 后能续写。
   - 切模型：在一个模型常驻时请求另一个 → 期望自动卸旧、加载新（而不是 503 重试）。
   - 强制选工具：`tool_choice="required"` → 期望**一定**返回 tool_call；具名 → 返回的就是那个函数。
3. **Phase 2 还剩**：
   - **#2 真增量流式**：逐 token 发 tool delta（现在是"攒齐一次发"，已合规，纯体验提升）。无机器成本。
   - **#3 多模型家族**：gemma 等。要加载模型做 probe（机器成本）。
4. **D（工具循环缓存命中）**：仍未做。根因是 OwlCoda 不传会话 id，所有请求挤进一个全局缓存桶。要么 OwlCoda 传 id，要么 owlmlx 自己派生。

---

## 五、诚实边界（**没有** claim 的，别误读）

- 全程 `experimental`，没有升 `supported`。
- ③ 的 tool_choice 强制 + native 工具解析：**只支持 Qwen / qwen3_coder**。别的家族（gemma/DeepSeek…）格式不同，没接。
- ③ 只在**非流式 / buffered 路径**生效（也就是 OwlCoda 走的那条）；真增量流式下的强制没单独做。
- ③ 的"真模型确实被逼出工具调用"是**可行性已证**（model-free 探测 + F-4.1 已证端到端语法生成可行），但**没在 live 真跑过**。
- ③ required 情况下参数名是"所有被选函数参数的并集"（偏松）；具名情况是精确的。参数**值**的类型没强制。
- ① 修的是非 buffered 分支（OwlCoda 不踩）。

---

## 六、怎么跑测试

```
# 工具/路由/切模型相关
.venv/bin/python -m pytest tests/test_mlx_native_backend.py tests/test_server_routes_openai.py \
  tests/test_memory_pressure_eviction_policy.py tests/test_reasoning_trace_policy.py -q

# 全量（排除会加载真模型的 4 个文件，避免机器成本）
.venv/bin/python -m pytest tests/ -q \
  --ignore=tests/test_deepseek_v4_d1_repeatability.py \
  --ignore=tests/test_mlx_native_backend_real_smoke.py \
  --ignore=tests/test_mlx_native_backend_real_upstream_binding.py \
  --ignore=tests/test_runtime_comparative_evidence_measured_runner.py

# ③ 的可行性 probe（只加载 tokenizer，秒级）
.venv/bin/python scripts/probe/phase2_tool_choice_forcing_feasibility.py
```

当前结果：全量 **1241 passed / 1 skipped**。

---

## 七、关键指针

- 设计全貌：`docs/superpowers/specs/2026-06-02-openai-tool-calling-design.md`
- 记忆（跨会话）：auto-memory `project-owlcoda-tool-calling-campaign-a`
- 活跃 backend：8066 走 `mlx_native_backend`（不是 mlx_lm 自带 server，也不是 subprocess runner）
- 规矩：probe/validator 放 `scripts/` 或 `tests/`，**不在 `owlmlx/` 下新建规格模块**；借来的机制先入 `experimental`。
