# R1 — Tool-Calling Family Parity (Qwen + Gemma, native, OpenAI shape) — Design Spec

> 文档 grade：design-grade · 见 [README.md](README.md)
> Status：Phase-1 closed 2026-06-05 · code landed (format-bug fix `55e0762e` + evidence `41ab7202`) · Gemma `tool_choice` forcing = **applied (model-free construction-confirmed)** · Gemma `auto`/`none` = **load-path-compatible (live deferred)** · stays `experimental`, promotes nothing; §1a untouched · evidence: `files/evidence/owlmlx/replacement/r1-tool-parity/20260605T130129Z-r1-gemma-feasibility.json`
> Campaign：替代收口 R-series — **R1**（blocker ①：source-first / tool-calling parity 超出 Qwen-only experimental）
> Plan-grade 来源：[`../../source-of-truth/runtime13-replacement-rebaseline-verdict.md`](../../source-of-truth/runtime13-replacement-rebaseline-verdict.md) §5（R1）；关联 `project-owlcoda-tool-calling-campaign-a`（Route 1 / mlx_lm registry）
> **Phase：Phase-1 only** — verify + forcing for **Qwen (done) + Gemma**, native backend, OpenAI shape。**停在 `experimental`，不走 §1a 晋级**。

---

## 0. 位置 + 验收口径

R1 收 blocker ①:把 tool-calling 从 "Qwen-only experimental" 扩到消费者实际用的家族/shape。

**Model-free scout（2026-06-04）已确立**:Gemma(`gemma-4-31B-it`)的 tool-call **emit + parse + `auto`/`none`** 是 **load-path-compatible**(mlx_lm 按 chat-template 自动选 `gemma4` parser,owlmlx `_parse_native_tool_calls` 泛型消费 `tokenizer.tool_parser`,无需 owlmlx 改码)。**唯一代码缺口 = `tool_choice` forcing**(`_tool_choice_forcing_ebnf` 硬编码 qwen3_coder XML;Gemma 的 `<|tool_call>call:name{…}<tool_call|>` 格式不同 → 当前 Gemma 的 forced/named 请求跑成 unforced)。

**Phase-1 = (A) live-verify Gemma `auto`/`none` + (B) family-aware forcing(qwen3_coder | gemma4)**。

**验收**:Gemma `auto`/`none` 经一次 live 跑确认(emit+parse)**或**落 gap artifact;Qwen 行为不变;Gemma forcing 分支给出明确 verdict:要么 forced/named 工作并有证据,要么证明 Gemma envelope/grammar 在当前栈不可行并落 documented gap + graceful-degrade diagnostic。后一种分支不声明 Gemma forcing capability。证据落盘;capability label 诚实更新(仍 `experimental`,scope=Qwen+Gemma native);**不晋级、promotes nothing**。

---

## 1. 架构

两块独立 + 取证,**native 后端 + OpenAI shape only**:

- **(A) Live Gemma 可行性 probe（scout-first 第一步）** — `scripts/probe/` 脚本,model-free 静态断言 + 一次 live 跑;解掉 model-free 读不出的未知(实际 emit 格式 spacing/换行是否符 parser 预期、think-tag 交错、arg 边界如 `<|"|>` 字符串/嵌套);落 evidence artifact。
- **(B) Family-aware `tool_choice` forcing** — 在**现有** `owlmlx/runtime/mlx_native_backend.py`(**不新建 `owlmlx/` 模块**)把 `_tool_choice_forcing_ebnf` 改成按家族分派;新增 `_gemma4_forcing_ebnf`。

---

## 2. 家族识别（约定）

- 识别当前活跃家族:优先 `tokenizer.tool_parser_type`(mlx_lm 加载时可能写入);否则由 `tokenizer.tool_call_start` marker 推断:`"<tool_call>"`→`qwen3_coder`,`"<|tool_call>"`→`gemma4`。owlmlx 本就读 `tool_call_start`,所以这是稳的。
- **绝不**单一家族硬编码。未知家族 + 请求 forcing → 返回 `None`(unforced,与今天对未知家族一致)+ 诊断 `tool_choice_forcing_unsupported_family`(降级,绝不打断生成)。

---

## 3. 组件

### 3.1 forcing 分派（`mlx_native_backend.py`，改现有）
`_tool_choice_forcing_ebnf(tools, tool_choice, *, parser_family)` → 分派:`qwen3_coder`→`_qwen3_coder_forcing_ebnf`(**不动**)、`gemma4`→`_gemma4_forcing_ebnf`(**新增**)、其它→`None` + 诊断。调用点(native `generate`)传入 §2 检出的 family。

### 3.2 `_gemma4_forcing_ebnf(funcs, param_names)`（新增，纯函数）
EBNF 约束到 `<|tool_call>call:` + fname-alternation + `{` + param-key-alternation + values + `}<tool_call|>`。**scope = 约束信封 + 函数名 + 参数键;值放松**(对齐 qwen builder 的 scope:约束 fname + param-names,值不强约束)。build 失败 → `None` + 诊断(降级)。**Feasibility 风险(probe 目标)**:Gemma 的 `<|tool_call>`/`<tool_call|>` 可能是单一特殊 token,xgrammar EBNF over token 边界能否表达该信封是未知;若不可行,gemma forcing 记为 **documented gap** + 优雅降级(`auto`/`none` 仍工作),不视为 R1 auto/none parity 失败,也不产生 Gemma forcing capability claim。

### 3.3 live probe（`scripts/probe/r1_gemma_tool_calling_feasibility.py`）
- **model-free**:断言 Gemma template → 推出 `gemma4`;markers 在;qwen forcing EBNF 能 build;Gemma forcing EBNF 要么能 build,要么产出 documented-infeasible verdict。
- **live**(需活 owlmlx + Gemma):`auto` tools 请求 → tool_calls emit+parse;`required`/named 请求 → forcing 生效或产出 documented graceful-degrade diagnostic。落 evidence(每家族 sub-results:parse/auto/none/forced/forcing_verdict)。
- live 跑吃机器时间(Gemma ~62GB)→ 执行时 surface run-now-vs-defer(见 §9.4)。

---

## 4. 证据（落盘）
`files/evidence/owlmlx/replacement/r1-tool-parity/`:probe verdict(per-family:parse / auto / none / forced 各 sub-result)+ 复现(cmd · env · owlmlx commit · model id · base URL)。**诚实**:model-free 部分 = "load-path-compatible";live 未知只有真跑后才升 "live-confirmed"。

---

## 5. 数据流
OpenAI `tools`/`tool_choice` → native `generate` → 检出 family → (需 forcing) 分派 EBNF → grammar logits processor → 模型按受控格式 emit → `_parse_native_tool_calls`(泛型家族 parser)→ `tool_calls` + `finish_reason=tool_calls`。

---

## 6. 错误处理 / 回滚
未知家族请求 forcing → `None` + 诊断(unforced,模型自行决定)。EBNF build 失败 → 降级(今天行为)。不动任何消费者默认;experimental lane;回滚 = revert(无默认被改)。

---

## 7. Definition of Done
1. Gemma `auto`/`none` tool-calling 一次 live 跑确认(tool_calls emit+parse)**或**落 documented gap artifact。
2. Family-aware forcing:qwen3_coder **不变**;gemma4 branch 必须落一个明确 verdict:
   - `applied`:forced/named 工作(model-free EBNF + live confirmation),或
   - `documented_infeasible`:Gemma envelope/special-token forcing 在当前栈不可表达;forced tool_choice 优雅降级并写诊断,且**不声明 Gemma forcing capability**。
3. 未知家族 forcing → `None` + `tool_choice_forcing_unsupported_family` 诊断。
4. Model-free 测试:gemma4 EBNF builder + 分派(qwen→qwen、gemma→gemma、unknown→None)。
5. 证据(§4)+ 复现落盘。
6. capability matrix 措辞更新:Qwen+Gemma native、**仍 `experimental`**、scope 写清;**不晋级 supported**;§1a 不动。
7. 零无出处断言;experimental 仍 experimental;**promotes nothing**。

---

## 8. 范围外
- subprocess(supported)后端 tool-calling(它今天**零** tool 支持 = 单独更大的活)。
- Qwen / Gemma 以外家族(DeepSeek / Mistral / …)——YAGNI,消费者未用到再说。
- Anthropic tool_use parity。
- experimental→supported 晋级(later §1a Phase-2,需 per-family N≥规模证据 + 先观测稳定性)。
- true incremental tool-call streaming(粗粒度已 conformant,UX-only)。

---

## 9. Hard Rules
1. forcing 改**现有** `mlx_native_backend.py`;probe 进 `scripts/probe/`;测试进 `tests/`;**不新建 `owlmlx/` 规格模块**(AGENTS)。
2. family-aware,绝不单一家族硬编码;未知家族 → 降级 `None` + 诊断。
3. 停在 `experimental`;不走 §1a 晋级;借来的 mlx_lm 机制**不自动**升 supported。
4. live probe 吃机器时间(Gemma ~62GB)→ 跑前 surface 成本 + run-now-vs-defer。
5. 不动消费者默认;native + OpenAI shape only。
6. evidence-language 校准:model-free = "load-path-compatible";"live-confirmed" 仅在真跑后。

---

## 10. 验证（怎么算"做对"）
§7 DoD 全满足 + 测试绿 + live probe 证据可复现 + Gemma forcing verdict 分支明确 + 无 experimental→supported 跳跃 + Qwen 无回归。
