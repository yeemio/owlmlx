# owlmlx Serving Hardening — D-5 Per-Route Request-Id Deduplication

## 你是谁

你是 `owlmlx` 主线执行者，落地 **D-5 serving hardening cleanup round —
per-route `request_id` 本地生成去重，统一改走 D-1
`RequestIdMiddleware` 注入的 `request.state.request_id`**。

本轮属于 §7 七行架构评估中明确为 **Line 4 — Serving surface
(`partial`)** 的关闭路径上的**第五项 wiring/cleanup 工作**：在 D-1
RequestIdMiddleware wired + D-2 GracefulShutdown drain wired + D-3
UnifiedErrorEnvelope wired + D-4 metrics endpoint wired 之后，把
`owlmlx/runtime/server.py` 各 compat 路由（`/v1/chat/completions`、
`/v1/messages`、`/v1/completions`、`/v1/openai/models`）里**冗余**的
`request_id = f"req_{uuid.uuid4().hex}"` 本地生成行删除，统一改读
middleware 已经写入 `request.state.request_id` 的值。

D-1 已经保证 `RequestIdMiddleware.dispatch` 对**每**条进站请求都会调用
`derive_request_id_context(...)` 并把结果同时写到
`request.state.request_id_context` 与 `request.state.request_id`：

- 入站 `x-request-id` header 存在 → 直接复用（lossless 透传）
- 入站缺失 → 生成 `req_<uuid4hex>`（32 hex 字符）并回写 outbound header

也就是说每条 compat 路由当前在路由 handler 内再写一次
`request_id = f"req_{uuid.uuid4().hex}"` 是**双重生成**——并且它和
middleware 自己生成的那个不是同一个 id，这导致：

- response body 的 `id` 字段（`_compat_error_response` /
  `_openai_response_dict` 的 wrapper 引用）和 outbound `x-request-id`
  header 在 happy path 上是 handler 自己生成的同一个值，但**和**
  middleware 已经写过的 `request.state.request_id` 不一致
- 入站带 `x-request-id` 时，outbound header 是入站值（middleware
  honored），但 body 的 `id` 仍然是 handler 自己生成的新值 —— 也就是
  现在客户端无法把入站 trace id 关联到响应体

D-5 的修法是把 handler 内的本地生成行**直接删掉**，改成
`request_id = request.state.request_id`，这样 outbound header / body
`id` / 错误 envelope `request_id` 字段三处指向**同一个**
middleware-set id；并且当入站带 `x-request-id` 时该值会原样落到
response body。

## 本轮唯一目标

落地以下四个交付物：

1. `owlmlx/runtime/server.py` —— **修改**：在四条 compat 路由内把
   `request_id = f"req_{uuid.uuid4().hex}"` 替换为
   `request_id = request.state.request_id`；这四条路由原本不带
   `request: Request` 参数，需要在 handler 签名里追加。具体五处
   （含 `/v1/openai/models`）落点见下文 §1
2. `tests/test_serving_hardening_request_id_dedup.py` —— **新增**
   integration 测试，对真实 `create_app()` 构造的 owlmlx app 用
   `fastapi.testclient.TestClient` 检查入站 `x-request-id` 透传到
   compat response body `id` 字段、autogen 路径下 body `id` 等于
   outbound header、错误 envelope 的 `request_id` 字段等于入站 id
3. `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d5-per-route-request-id-deduplication.md`
   —— **新增** 本轮 round prompt（即本文件）
4. `files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-d5-per-route-request-id-deduplicated.md`
   —— **新增** 本轮 checkpoint，verdict 为
   `serving_hardening_d5_per_route_request_id_deduplicated_middleware_sole_source`

## 本轮**不**做的事（硬规则）

- **不**修改 `owlmlx/runtime/serving_hardening.py`（C-4 scaffold 已冻结）
- **不**修改 `tests/test_serving_hardening.py`（C-4 scaffold 测试已冻结）
- **不**修改 `tests/test_serving_hardening_wired.py`（D-1 wiring 测试已冻结）
- **不**修改
  `tests/test_serving_hardening_graceful_shutdown_wired.py`（D-2 wiring 测试已冻结）
- **不**修改
  `tests/test_serving_hardening_error_envelope_wired.py`（D-3 wiring 测试已冻结）
- **不**修改
  `tests/test_serving_hardening_metrics_wired.py`（D-4 wiring 测试已冻结）
- **不**修改 `owlmlx/serving.py`，**不**改 `GenerationGate`
- **不**修改 `owlmlx/runtime/kernel.py`、`owlmlx/runtime/types.py`、
  `owlmlx/runtime/mlx_native_backend.py`、`scripts/runtime_technical_preview_server.py`
- **不**修改 `pyproject.toml` / `uv.lock` —— **不**引入新依赖
- **不**修改 `conftest.py`、`README.md`、`.python-version`
- **不**修改任何 `docs/` 下的文件
- **不**改 D-1 `app.add_middleware(RequestIdMiddleware)` 注册行
- **不**改 D-2 `_graceful_shutdown_drain` 注册块
- **不**改 D-3 `_unhandled_exception_handler` /
  `app.add_exception_handler(Exception, ...)` 注册块、native error code
  -> HTTP status 映射、`_native_runtime_response(...)` 适配器
- **不**改 D-4 `/metrics` 路由
- **不**改 `_compat_error_response` / `_anthropic_error_response`
  函数体（仍然以 `request_id` 关键字参数构造响应；只是它的来源换了）
- **不**改 compat / Anthropic response body 的形状 —— `id` / `request_id`
  字段位置和类型不变，只是值的**来源**从 handler 本地生成换成
  middleware-set
- **不**改 `/v1/generate/stream`、`/v1/messages/count_tokens` 或
  `/v1/runtime/*` 任何路由
- **不**真实启动 uvicorn / 真实加载模型；`TestClient` 即可观察
  request-id 流动
- **不**新增任何 dependency
- **不**删除 `import uuid` —— 经 `grep -n "uuid\\."
  owlmlx/runtime/server.py` 检查，`uuid.uuid4().hex` 仍被
  `completion_id`（`chatcmpl-`、`cmpl-`）和 `message_id`（`msg-`）继续
  使用；它们是别的标识符，不能误删
- **不**改 native 路由（`/v1/load`、`/v1/generate`、`/v1/unload`、
  `/v1/generate/stream`）—— D-3 已经把它们经
  `_native_runtime_response` 路由到 middleware id

## 本轮**要**做的事

### 1. 修改 `owlmlx/runtime/server.py`

按 grep 实证，`request_id = f"req_{uuid.uuid4().hex}"` 在 server.py
中的本地生成站点共有 **4** 处：`/v1/chat/completions`、
`/v1/messages`、`/v1/completions`、`/v1/openai/models`。每处的修改
都是同型：

- **路由签名追加 `request: Request` 参数**（这四条路由当前都没接受
  `Request`）。FastAPI 会自动注入。
- **删除**本地的 `request_id = f"req_{uuid.uuid4().hex}"` 行
- **新增**一行 `request_id = request.state.request_id` 并附 D-5 注释
  说明该值由 D-1 RequestIdMiddleware 写入

具体五处落点（按 `grep -n "request_id = f\"req_"
owlmlx/runtime/server.py` 实证、行号会随 D-2/D-3/D-4 wiring 滑动，以
grep 实证为准）：

- `/v1/chat/completions` 路由 handler `chat_completions(...)`
  开头：`payload: ChatCompletionRequest` → `payload:
  ChatCompletionRequest, request: Request`，删除生成行，改读
  `request.state.request_id`
- `/v1/messages` 路由 handler `anthropic_messages(...)` 开头：
  `payload: AnthropicMessagesRequest` → `payload:
  AnthropicMessagesRequest, request: Request`，删除生成行，改读
  `request.state.request_id`
- `/v1/completions` 路由 handler `completions(...)` 开头：`payload:
  CompletionRequest` → `payload: CompletionRequest, request: Request`，
  删除生成行，改读 `request.state.request_id`
- `/v1/openai/models` 路由 handler `openai_models()` 开头：`()` →
  `(request: Request)`，删除生成行，改读 `request.state.request_id`

`/v1/messages/count_tokens` 路由（不生成 request_id、也不返回
`x-request-id`）不改；`/v1/generate/stream` 路由（流式、整路不携带
单独 request_id 局部变量）不改。

`message_id = f"msg_{uuid.uuid4().hex[:24]}"`、`completion_id =
f"chatcmpl-{uuid.uuid4().hex}"`、`completion_id =
f"cmpl-{uuid.uuid4().hex}"` 是**别的**标识符（OpenAI/Anthropic SDK 协议
要求的 message id / completion id），**不**动。

**没有别的改动**。所有 D-1 / D-2 / D-3 / D-4 注册块、helper
函数、native 路由、`/v1/runtime/*` 路由不动。`_compat_error_response`
/ `_anthropic_error_response` 函数体不动；只是它们被调用时传入的
`request_id=` 实参的**来源**换了。

### 2. 新增 `tests/test_serving_hardening_request_id_dedup.py`

4 到 6 个 integration 测试用 `fastapi.testclient.TestClient` 对真实
`create_app()` 构造的 owlmlx app 执行：

- `test_inbound_request_id_propagates_to_chat_completions_response_id`
  —— POST `/v1/chat/completions`（指定不存在的 `model`，触发
  `model_not_loaded` 错误路径），带入站 `x-request-id:
  req_test-inbound-123`，断言响应 body `id` == `req_test-inbound-123`、
  outbound header `x-request-id` == `req_test-inbound-123`
- `test_inbound_request_id_propagates_to_messages_response_id` ——
  POST `/v1/messages` 同型；Anthropic envelope body 不带
  `request_id` 字段，但 outbound header 必须 echo 入站 id
- `test_inbound_request_id_propagates_to_completions_response_id` ——
  POST `/v1/completions` 同型；body `id` == 入站 id
- `test_no_inbound_id_uses_middleware_generated_id_in_compat_response`
  —— 不带入站 header，触发 `model_not_loaded` 错误路径，断言
  outbound header `x-request-id` 形如 `req_<32hex>` 且 body `id`
  与 outbound header **完全一致**（证明只剩一个 id 来源）
- `test_compat_error_response_carries_inbound_request_id` —— 通过
  POST `/v1/completions` + 不存在 model 触发错误路径，断言 compat
  错误 envelope body `id` == 入站 `x-request-id`
- `test_openai_models_route_uses_middleware_request_id` —— GET
  `/v1/openai/models` 带入站 header，断言 outbound header
  `x-request-id` 原样回写（happy path 上 D-5 也生效）

`TestClient` only。**不**真实启动 uvicorn。**不**真实加载模型；
`FakeBackend` 默认未 load 任何 model，`generate_messages` 会返回
`model_not_loaded` 错误，handler 走 `_compat_error_response` /
`_anthropic_error_response` 分支。

### 3. 新增 round prompt（即本文件）

### 4. 新增 D-5 checkpoint

`files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-d5-per-route-request-id-deduplicated.md`
verdict line 为
`serving_hardening_d5_per_route_request_id_deduplicated_middleware_sole_source`。
checkpoint 须含：

- **What This Checkpoint Is** —— 单项 cleanup wiring marker
- **What Is Now Frozen Exact** —— `server.py` 内 4 个签名扩参 + 4 个
  生成行替换 + middleware-sole-source 关系
- **Test Counts** —— 六个 suites 总计
- **What This Checkpoint Closes**
- **What This Checkpoint Does Not Claim**
- **Side Effects** —— 对客户端零可观察行为变化（id 格式不变；只是
  入站 `x-request-id` 现在会落到 body `id` 字段）
- **Notable Implementation Choices** —— 不删 `import uuid`（仍被
  `completion_id`/`message_id` 用）；compat error envelope 仍按原型构
  造、只是 `request_id` 实参来源换了；handler 签名扩 `request: Request`
  是 FastAPI 自动注入路径，不引入额外解析成本
- **Next Authorized Round** —— 指向 D-6 候选（timeout helper 接入 /
  idempotent load helper class / streaming envelope 等）

## 验收

- 修改后的 `owlmlx/runtime/server.py` 通过
  `.venv/bin/python -m pytest tests/test_serving_hardening.py
  tests/test_serving_hardening_wired.py
  tests/test_serving_hardening_graceful_shutdown_wired.py
  tests/test_serving_hardening_error_envelope_wired.py
  tests/test_serving_hardening_metrics_wired.py
  tests/test_serving_hardening_request_id_dedup.py -q`
- 没有新增任何 stage 区域文件；`git status --short` 仅多出本轮直接
  涉及的 4 个交付路径
- checkpoint 措辞坚持 "per-route id generation removed; middleware is
  sole source"，**不**写 "production-grade tracing" / "complete
  observability"
- checkpoint 明确记录 4 个 handler 签名扩参与不删 `import uuid` 的
  依据

## 不在本轮范围

- D-6 timeout 接入 / idempotent load helper class wiring
- 流式 `/v1/generate/stream` 的 envelope 注入
- 422（FastAPI 自身 validation 错误）的 envelope 转译
- compat 路由的 envelope 切换（保持现状）
- 任何 trace span / structured logging 接入
- 任何引入新依赖的工作
- `docs/source-of-truth/serving-hardening-architecture.md` 刷新
- 任何 capability matrix 行的 promotion / demotion
