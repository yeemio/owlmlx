# OpenAI 兼容工具调用(Campaign A,通用)— 设计 spec

> **目标是通用 OpenAI 工具调用规范,不是 OwlCoda 专用。** 任何满足 OpenAI tool-calling 规范的 agent 客户端(OwlCoda、Codex、经 bridge 的 Claude Code、Cline、Continue…)都应能用;OwlCoda 只是**参考一致性消费者(conformance validator)**。符合 owlmlx 身份:OwlCoda 是消费者,非身份组成。

- **Status**: Phase 1 **LANDED** in `cb0bd7cd`(pushed origin/main,experimental);本 spec 现为已实现记录 + Phase 2 待办。(原 grade:design — plan+design 会话产出,代码已在后续会话落地)
- **Date**: 2026-06-02
- **Capability label**: `experimental`(借来的机制按 adoption 规矩先入 experimental;`supported` 不在任何地方声称)
- **决定的路线**: 路线 1 —— 复用已装 mlx_lm 的工具机制 + 照 oMLX 模式
- **关联记忆**: 工具调用可行性与路线已写入 auto-memory;与 F-4 grammar、strategic-pivot、module-as-spec 规则交叉

---

## 1. 背景与目标

owlmlx 的 `/v1/chat/completions` 要成为**符合 OpenAI 工具调用规范的通用端点**,让任意符合规范的 agent 客户端都能驱动工具循环(循环由客户端驱动,不在 owlmlx 内)。OwlCoda 是其中一个消费者(Anthropic⇄OpenAI 单轮翻译代理),本文以它做**参考一致性投影**;同类客户端(Codex、经 bridge 的 Claude Code、Cline、Continue 等)只要遵循同一 OpenAI 规范即应工作。具体地,owlmlx 的 OpenAI 路由必须:

1. **接受**完整 OpenAI 消息形状(含 `role:tool`、`content:null`、`tool_calls`、`tool_call_id`),不再 422;
2. 把 `tools`/`tool_choice` 注入模型,并把模型产出**解析成结构化 `tool_calls`**;
3. 返回 `finish_reason="tool_calls"`(非流式 + 流式)。

**当前真实状态(已核实)**:owlmlx 真后端**完全没有工具调用** —— 只有 `FakeBackend` 测试桩会产 `tool_uses`(硬编码 `toolu_fake_001`);Anthropic 路由里那套 `result.detail["tool_uses"]` 消费逻辑对真模型是**死线**。`docs/source-of-truth/runtime5-entrypoint-and-compat.md` 明确写 "tools / function calling — future work"。所以 A 是**扩范围的真功能**,不是接线。

---

## 2. 已验证的事实(证据)

### 2.1 安装的 mlx_lm(0.31.3)自带完整工具机制
- `TokenizerWrapper.apply_chat_template(..., tools=...)` 会把 tools 透传进 Jinja 模板(`tokenizer_utils.py`)。
- `mlx_lm/tool_parsers/`:`qwen3_coder`、`gemma4`、`mistral`、`json_tools`… 每个导出 `tool_call_start` / `tool_call_end` / `parse_tool_call`。
- `_infer_tool_parser(chat_template)` 按模板子串自动选解析器;**未命中返回 None → tool_calls 静默为空(必须 log 警告)**。
- mlx_lm 自带 server 端到端可跑,但:**不支持 `tool_choice`**;流式是"整段攒齐再发"。
- owlmlx 不走 mlx_lm 的 server;它把 mlx_lm 当库用(tokenizer + generate)。`mlx_lm_runner.apply_chat_template` 当前**没传 `tools=`**;`backends.py` 工具路径是假桩。

### 2.2 Qwen3.6 模型模板(磁盘静态读出,无需加载)
- 模板有 `{% if tools %}` 分支,把 tools 以 `<tools>{json}</tools>` 注入 system。
- **工具调用 wire 格式是 XML(非 JSON、非 ✿)**:
  ```
  <tool_call>
  <function=NAME>
  <parameter=ARG>
  VALUE
  </parameter>
  </function>
  </tool_call>
  ```
- `_infer_tool_parser` 对该模板返回 **`qwen3_coder`**(实测)。模板亦支持回填 assistant `tool_calls` 与 `role:tool`(`<tool_response>`)。
- 思考:`add_generation_prompt` 时模板在 **prompt 里**预置 `<think>\n`(或 `enable_thinking=false` 时预置空 `<think>\n\n</think>`)。

### 2.3 真模型实测(probe,Qwen3.6-35B-A3B-4bit,19.5GB,载入 9.9s)
喂 `run_bash` 工具 + "列出 /tmp":
- **思考默认开**:模型先想一段 →(模型输出里**只有 `</think>`、没有 `<think>`**,因为开头在 prompt 里)→ 干净的 `<tool_call><function=run_bash><parameter=command>ls -la /tmp</parameter></function></tool_call>`。`qwen3_coder.parse_tool_call` → `{'name':'run_bash','arguments':{'command':'ls -la /tmp'}}` ✅
- **思考关**:0.7s,直接吐工具调用,解析成功 ✅

**结论:端到端可行(注入→产出→解析三段全通),高把握。** Probe 脚本临时放在 `/tmp/owlmlx_toolcall_probe.py`(待正式化为回归测试)。

### 2.4 think 泄漏根因(顺带实锤,即原问题 4)
模型输出常**只含 `</think>` 不含 `<think>`**(开头被模板放进了 prompt)。`owlmlx/reasoning_trace_policy.py` 的 `_analyze_think_trace` 现逻辑:找不到 `<think>` 开头就 `return None` → 不剥离 → 思考正文原样泄漏到 `content`。**这是 Qwen 泄漏的真因。**

### 2.5 本地参考实现(可照抄思路)
- oMLX:`/Users/yeemio/AI/gitrep/omlx-upstream/omlx/api/tool_calling.py`(用 mlx_lm 解析器 + `extract_tool_calls_with_thinking` 处理"先思考再工具")。
- vMLX:`/Users/yeemio/AI/gitrep/vmlx/vmlx_engine/tool_parsers/`(自建 13+ 解析器 + 真增量流式 + MCP)—— 路线 2 的参考。

---

## 3. 要满足的契约(= OpenAI 工具调用规范;下列以 OwlCoda 为一致性投影核对,非 OwlCoda 专属)

**请求要接受**(`../owlcoda/src/translate/request.ts`、`types.ts`):
- `messages[].role ∈ {system,user,assistant,tool}`;`content: string | 数组 | null`;
- assistant 携带 `tool_calls:[{id, type:"function", function:{name, arguments:<JSON 字符串>}}]` 及可选 `reasoning_content`(容忍即可);
- tool 消息 `{role:"tool", content, tool_call_id}`;
- 顶层 `tools:[{type:"function",function:{name, description?, parameters:<JSON Schema>}}]`、`tool_choice: "auto"|"none"|"required"|{type:"function",function:{name}}`、`top_p`、`stop`(数组)、`max_tokens`、`temperature`、`stream`。

**响应要产出**(非流式,`response.ts`):
- `choices[0].message.{content:可为null, tool_calls?, reasoning_content?}`,`finish_reason="tool_calls"`(工具轮);`arguments` 是 **JSON 字符串**;参数 JSON 坏了 OwlCoda 会兜底 `{_raw}`,不崩。

**流式硬要求**(`../owlcoda/src/translate/stream.ts`):
- 每个 `delta.tool_calls[]` 必带 `index`;**该 index 的首个 delta 必须同时带 `id` 和 `function.name`**(否则块永不开、参数被丢);
- 参数走 `function.arguments` 片段累加;**一整个调用一次性给(index+id+name+完整 arguments 同一 delta)是被支持的**;
- 收尾必须有 `finish_reason="tool_calls"` 和/或 `[DONE]`,否则 OwlCoda 抛 stream-interrupted。

**附注**:OwlCoda 默认上游是 `127.0.0.1:8009`,自身监听 8019;你的 8066 是配置项。自动探测要 `/v1/openai/models`(owlmlx 已有)。OwlCoda **不发** `x-owlmlx-session-id`(影响 D,本期不处理)。

---

## 4. 设计(路线 1:复用 mlx_lm + 照 oMLX)

### 4.0 实现前置(必须先确认)
**8066 实际走哪个 backend**:疑似 `runtime_native_preview_server.py` → `mlx_native_backend`(其 `generate` 调 `mlx_lm.generate(...)`,只传 prompt/max_tokens/prompt_cache,**不传 tools、不解析**)。工具抽取必须接到**这条真实生成路径**上,而非只改 `mlx_lm_runner`。fresh 会话第一步:核实活跃 backend 与其生成函数。

### 4.1 接口 schema(`owlmlx/runtime/server_routes_openai.py`)
- `ChatMessage`:`content: str | list | None`;新增 `tool_calls`、`tool_call_id`、`name`、`reasoning_content`(可选)。
- `ChatCompletionRequest`:新增 `tools`、`tool_choice`、`top_p`。
- 把 `tools`/`tool_choice` 经 `params` 传到 `runtime.generate_messages(...)`(Anthropic 路由已有同款写法可参照)。

### 4.2 消息→模板的结构保真(关键)
- 现 `_messages_to_turns` 压成 `ChatTurn(role, content)`,会丢工具结构 → 多轮工具循环失上下文。
- 让喂给 `apply_chat_template` 的消息**保留** `tool_calls` / `tool_call_id` / `role:tool`,使 Qwen 模板的对应分支触发(模板已支持)。最小改法:扩展 `ChatTurn`(`owlmlx/runtime/types.py`)或在 runner 处直接用 dict 列表传模板。

### 4.3 模板注入
- `mlx_lm_runner.apply_chat_template`(及活跃 backend 的等价处)加 `tools=tools`;`enable_thinking` 经 `chat_template_kwargs` 透传。

### 4.4 抽取(post-hoc,复用 mlx_lm 解析器)
- 真 backend 调 `mlx_lm.generate` 拿到**整段文本**后:
  1. **先按思考边界切**:取 `</think>` 之后的文本(probe 用 `out.split("</think>")[-1]` 已验证)——**绝不在思考内扫工具**;
  2. 用 `_infer_tool_parser(chat_template)` 选解析器(Qwen→`qwen3_coder`);**None 分支必须 log 警告**;
  3. 提取 `tool_call_start`…`tool_call_end` 区间(可多个),逐个 `parse_tool_call(inner, tools)`;
  4. 组装 `{"id":"call_"+uuid, "type":"function", "function":{"name", "arguments": json.dumps(args, ensure_ascii=False)}}`;
  5. 有工具调用则 `finish_reason="tool_calls"`,否则维持 `stop`。
- 产出形态对齐既有 `result.detail["tool_uses"]` 约定或直接产 OpenAI 形态(二选一,fresh 会话定;倾向直接产 OpenAI `tool_calls`,在路由整形)。

### 4.5 思考隔离(修 2.4,本期一并做)
- `reasoning_trace_policy.py`:处理"只有 `</think>` 无 `<think>`"的悬挂闭合 —— 把 `</think>` 前的全当思考剥掉(给定一个"thinking 已在 prompt 开启"的信号,或直接对悬挂 `</think>` 兜底)。
- `_openai_reasoning_trace_policy`:让 Qwen profile 默认走剥离(改判定:profile 声明了 `reasoning_trace_policy` / qwen family 即默认 `final_answer_content`),不再只认 `parser_cleanup_required`。
- 可选(加分,不阻塞):把剥下来的思考作为 `choice.message.reasoning_content` 回吐(OwlCoda 能消费)。

### 4.6 响应整形
- 非流式:`message.tool_calls` + `finish_reason="tool_calls"`;无工具则原样文本(经思考剥离)。
- 流式(本期"攒齐发单 delta"):在生成流里**缓冲工具区间**,闭合后**一次性**发一个 delta(带 `index=0/1…`、`id`、`function.name`、完整 `function.arguments`),再发 `finish_reason="tool_calls"` 的收尾 chunk + `[DONE]`。OwlCoda 接受此形态。

### 4.7 tool_choice(本期最小)
- `"auto"`(默认)/省略:正常注入 tools。
- `"none"`:不注入 tools(或注入但不解析),保证不触发工具。
- `"required"` / 具名:**本期 best-effort**(prompt 提示),真正强制留二期(用 F-4 grammar 约束解码逼出合法工具调用 → 复用现有 F-4 资产)。

---

## 5. 范围与诚实标注
- **本期(Phase 1)= 规范合规核心**:全 OpenAI schema;**多模型家族**(走 mlx_lm `_infer_tool_parser` 自动识别:qwen3_coder/gemma4/mistral/json_tools…;**Qwen 已实测,其余 load-path-compatible、逐家族验证待补**,None 分支必须告警);auto/none;规范合规的(粗粒度)流式;任意合规客户端可端到端跑(OwlCoda 做参考验证);capability = `experimental`。
- **Phase 2(延后,补规范完整度/UX,非补合规漏洞)**:`tool_choice` required/具名强制(复用 F-4 grammar);真 OpenAI 逐 token 增量流式 delta(照 vLLM hermes / vMLX);更多家族逐一验证;可选 `reasoning_content` 回吐。注:Phase 1 的粗粒度流式 + auto/none **本身已是规范合规**。
- **不在本 campaign**:C(切模型 auto-unload/清晰错误)、D(工具循环缓存命中,需 OwlCoda 传 session id 或 owlmlx 派生)。
- **文档同步**:更新 `runtime5-entrypoint-and-compat.md`(去掉"tools=future work"的绝对措辞,改 `experimental`)、`reference-runtime-comparison-matrix.md`(更新相对 vMLX/oMLX 的工具轴位置)。**按 sweep 规矩,把全文相关陈旧措辞一并刷新。**

## 6. 验证计划(符合 module-as-spec 规矩)
- **验证目标 = OpenAI 规范一致性**(不是"OwlCoda 能用就行"):建 OpenAI tool-calling 一致性用例集(schema 接受面、`tool_calls` 形态、`finish_reason`、流式 index/id/name、多并行调用),再以**多客户端冒烟**(OwlCoda + 至少一个其它 OpenAI 工具客户端)佐证。
- 校验器放 **`tests/` 或 `scripts/`**,**不在 `owlmlx/` 下新建规格模块**。
- 把 `/tmp/owlmlx_toolcall_probe.py` 正式化为:`tests/`(或 `scripts/bench/`)下的工具调用回归(注入→解析→OpenAI 形态),含真模型小样 + 离线 fixture(用 probe 抓的原始输出)单测解析器接入。
- 路由层测试:用既有 `FakeBackend` 工具路径覆盖 OpenAI schema/响应/流式形状(不需真模型)。
- N 与机器成本:真模型样本小跑即可(format 是模板属性,不需大 N);任何长 bench 先报成本。

## 7. 可能改动的文件
- `owlmlx/runtime/server_routes_openai.py`(schema、handler、整形、流式)
- `owlmlx/runtime/types.py`(`ChatTurn` 携带工具结构)
- `owlmlx/runtime/kernel.py`(确认 tools 透传)
- `owlmlx/runtime/mlx_lm_runner.py` + **活跃 backend(疑似 `mlx_native_backend.py`)**(注入 + 抽取 + finish_reason)
- `owlmlx/reasoning_trace_policy.py`(悬挂 `</think>` 修复)
- `owlmlx/model_profile.py`(Qwen 默认剥离判定,如走 profile)
- `tests/` 或 `scripts/`(校验器)
- `docs/source-of-truth/runtime5-entrypoint-and-compat.md`、`reference-runtime-comparison-matrix.md`(范围/措辞)

## 8. 给 fresh 实现会话的 handoff
1. 先确认 8066 活跃 backend 与其生成函数(§4.0)。
2. 按 §4 顺序落地:schema → 结构保真 → 注入 → 抽取(post-hoc)→ 思考隔离 → 响应/流式 → tool_choice 最小。
3. 全程 `experimental` 标注;借来机制不自动升 `supported`。
4. 用 §6 校验器证据驱动;成本敏感操作先报。
5. 参考源:oMLX `tool_calling.py`、mlx_lm `tool_parsers/qwen3_coder.py` + `server.py` 抽取状态机、vMLX(二期)。

## 9. 待定/可在实现期再决
- 抽取产物形态:沿用 `tool_uses` detail 约定 vs 直接产 OpenAI `tool_calls`(倾向后者)。
- 思考剥离信号的传递方式(profile 字段 vs route 推断 vs 直接兜底悬挂闭合)。
- `reasoning_content` 是否本期回吐(加分项)。
