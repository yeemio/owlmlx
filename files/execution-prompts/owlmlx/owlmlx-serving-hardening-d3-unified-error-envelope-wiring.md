# owlmlx Serving Hardening — D-3 Unified Error Envelope Wiring

## 你是谁

你是 `owlmlx` 主线执行者，落地 **D-3 serving hardening wiring round —
UnifiedErrorEnvelope + ErrorEnvelopeBuilder lifespan/route wiring**。

本轮属于 §7 七行架构评估中明确为 **Line 4 — Serving surface
(`partial`)** 的关闭路径上的**第三项 wiring 工作**：把 C-4 scaffold
（`owlmlx/runtime/serving_hardening.py`）里已经定义好的
`UnifiedErrorEnvelope` / `ErrorEnvelopeBuilder` 真正接到
`owlmlx/runtime/server.py` 的 FastAPI app 上：

1. 注册一个通用 `Exception` handler，使任何未捕获异常返回统一的
   `UnifiedErrorEnvelope` shape，HTTP 500，不泄漏原始异常的类名/消息
2. 把 `/v1/load`、`/v1/generate`、`/v1/unload` 三条 native 路径上
   `ok=False` 时的响应从 HTTP 200 + body.ok=false 提升为按 typed
   `error_code` 映射的真正 HTTP status（400/404/500），同时
   返回 `UnifiedErrorEnvelope` shape

本轮**不**接 timeout / metrics / idempotent load —— 那些是各自独立的
D-4 / D-5 / D-6 wiring round。本轮也**不**改任何 compat 路由
（`/v1/chat/completions`、`/v1/messages`、`/v1/completions`、OpenAI
compat surface）—— 这些路由有自己的 `_compat_error_response` /
`_anthropic_error_response`，OpenAI / Anthropic SDK 客户端依赖现存形状。

D-3 从 D-1 RequestIdMiddleware wired + D-2 GracefulShutdown drain
wired 之后的 serving surface 状态开始，**单项**接入 unified error
envelope；不依赖任何 native-backend capability promotion 是否已经收口。

## 本轮唯一目标

落地以下四个交付物：

1. `owlmlx/runtime/server.py` —— **修改**：在顶部 import 行追加
   `ErrorEnvelopeBuilder, UnifiedErrorEnvelope`；在 `create_app(...)`
   内 `_graceful_shutdown_drain` 注册之后追加一个 D-3 wiring 块
   （包含构造 `error_envelope_builder = ErrorEnvelopeBuilder(...)`、
   定义 `_request_id_from_request(...)`、定义
   `_unhandled_exception_handler(request, exc)` async 函数、调用
   `app.add_exception_handler(Exception, _unhandled_exception_handler)`、
   定义 native 错误码到 HTTP status 的映射、定义
   `_native_runtime_response(...)` 适配器）；并把 `/v1/load`、
   `/v1/generate`、`/v1/unload` 三条路径的 return 改为通过
   `_native_runtime_response(...)` 渲染
2. `tests/test_serving_hardening_error_envelope_wired.py` ——
   **新增** integration 测试，对真实 `create_app()` 构造的 owlmlx app
   用 `fastapi.testclient.TestClient` 检查 envelope shape、状态码映射、
   request_id 透传、未处理异常回退、以及 compat 路径形状未被波及
3. `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d3-unified-error-envelope-wiring.md`
   —— **新增** 本轮 round prompt（即本文件）
4. `files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-d3-unified-error-envelope-wired.md`
   —— **新增** 本轮 checkpoint

## 本轮**不**做的事（硬规则）

- **不**修改 `owlmlx/runtime/serving_hardening.py`（C-4 scaffold 已冻结）
- **不**修改 `tests/test_serving_hardening.py`（C-4 scaffold 测试已冻结）
- **不**修改 `tests/test_serving_hardening_wired.py`（D-1 wiring 测试已冻结）
- **不**修改
  `tests/test_serving_hardening_graceful_shutdown_wired.py`（D-2 wiring 测试已冻结）
- **不**修改 `owlmlx/serving.py`，**不**改 `GenerationGate`
- **不**修改 `owlmlx/runtime/kernel.py`、`owlmlx/runtime/types.py`、
  `owlmlx/runtime/mlx_native_backend.py`、`scripts/runtime_technical_preview_server.py`
- **不**修改 `pyproject.toml` 与 `uv.lock` —— 不引入新依赖
- **不**修改 `conftest.py`、`README.md`、`.python-version`
- **不**修改任何 `docs/` 下的文件
- **不**修改 / 移除 `_stop_runtime_monitor_sampler` 或
  `_graceful_shutdown_drain` 的函数体或注册行
- **不**改 `_compat_error_response` / `_anthropic_error_response`
  的实现或调用点 —— 这些是 OpenAI / Anthropic SDK 兼容层
- **不**改任何 compat 路由（`/v1/chat/completions`、`/v1/messages`、
  `/v1/completions`）的 error 响应形状
- **不**改 `/v1/generate/stream`、`/v1/messages/count_tokens` 或其他非
  native-lifecycle 路由 —— 流式响应的 error envelope 是另一轮工作
- **不**改任何 `/v1/runtime/*` 路由
- **不**接 timeout / metrics / idempotent load —— 各自独立的 wiring round
- **不**真实启动 uvicorn / 真实加载模型；`TestClient` 即可观察
  envelope 注入侧效应；行为 unit 测试由 C-4 scaffold 测试覆盖
- **不**新增任何 dependency

## 本轮**要**做的事

### 1. 修改 `owlmlx/runtime/server.py`

三处改动：

(a) 顶部相对路径 import block 由
```python
from .serving_hardening import GracefulShutdown, GracefulShutdownConfig, RequestIdMiddleware
```
改为
```python
from .serving_hardening import (
    ErrorEnvelopeBuilder,
    GracefulShutdown,
    GracefulShutdownConfig,
    RequestIdMiddleware,
    UnifiedErrorEnvelope,
)
```

(b) 在 `create_app(...)` 内、`_graceful_shutdown_drain` 注册行
（`app.router.on_shutdown.append(_graceful_shutdown_drain)`）之后、
`_store_runtime_test_run` 定义之前，追加一个 D-3 wiring 块：

- 构造 `error_envelope_builder = ErrorEnvelopeBuilder(namespace="owlmlx_native")`
- 定义闭包 `_request_id_from_request(request) -> str | None`：从
  `request.state.request_id`（D-1 RequestIdMiddleware 已写入）安全
  地读出；任何异常回退到 `None`
- 定义 async 函数 `_unhandled_exception_handler(request, exc)`：调用
  `error_envelope_builder.from_unexpected(exc, request_id=...)`；
  builder 自身失败时回退到一个字面 dict body + status 500；返回
  `JSONResponse(status_code=envelope.http_status,
  headers={"x-request-id": ...} if request_id else {},
  content=envelope.to_response_body())`。**handler 永远不抛**
- 调用 `app.add_exception_handler(Exception, _unhandled_exception_handler)`
- 定义 native 错误码到 HTTP status 的映射 `_NATIVE_ERROR_CODE_TO_HTTP_STATUS`：
  - `invalid_request` → 400
  - `model_not_loaded` → 404
  - `model_not_found` → 404
  - `unsupported_model_family` → 400
  - `memory_budget_exceeded` → 400
  - `backend_error` → 500
  - `model_pinned` → 409
- 定义闭包 `_native_runtime_response(result, *, request,
  success_status=200, idempotent_already_loaded=False)`：先调用
  `_result_to_dict(result)` 拿 dict body；ok=True 返回
  `JSONResponse(status_code=success_status, ...)`；
  `idempotent_already_loaded=True` 且
  `error_code=="model_already_loaded"` 时按 success-with-detail 返回
  原 body + HTTP 200；其余 ok=False 走
  `error_envelope_builder.from_runtime_error_code(...)` 构造 envelope，
  HTTP status 来自映射表（未知 code 默认 500），返回
  `JSONResponse(status_code=envelope.http_status, ...,
  content=envelope.to_response_body())`

(c) 把以下三条 native 路径的 return 改写：

- `/v1/load`：handler 签名追加 `request: Request` 参数；body 改为
  `return _native_runtime_response(result, request=request,
  idempotent_already_loaded=True)`
- `/v1/generate`：handler 签名追加 `request: Request` 参数；body 改为
  `return _native_runtime_response(result, request=request)`
- `/v1/unload`：handler 签名追加 `request: Request` 参数；body 改为
  `return _native_runtime_response(result, request=request)`

**没有别的改动**。`/v1/generate/stream` 不动。所有 compat 路由不动。
所有 `/v1/runtime/*` 路由不动。`_compat_error_response` /
`_anthropic_error_response` 函数体不动。

### 2. 新增 `tests/test_serving_hardening_error_envelope_wired.py`

5 到 8 个 integration 测试用 `fastapi.testclient.TestClient` 对真实
`create_app()` 构造的 owlmlx app 执行：

- `test_load_unknown_model_arg_returns_400_or_appropriate_status` ——
  `POST /v1/load` with `model_id=""`，验证状态码 + envelope 形状（注：
  `LoadRequest.model_id: str = Field(min_length=1)` 让 FastAPI/pydantic
  在 422 阶段就拦下，本测试 pin 这个事实）
- `test_load_unhealthy_backend_returns_500_with_unified_envelope` ——
  用 `FakeBackend(healthy=False)` 触发 `backend_error`，验证 500 + envelope
- `test_generate_unknown_model_returns_404` —— `POST /v1/generate`
  对未加载的 model_id，验证 404 + envelope，error_code=model_not_loaded
- `test_unload_unknown_model_returns_404` —— `POST /v1/unload`
  对未加载的 model_id，验证 404 + envelope
- `test_unhandled_exception_returns_500_with_clean_envelope` ——
  attach 一个 stub route 内部 `raise _SecretInternalProbeError(...)`，
  使用 `TestClient(..., raise_server_exceptions=False)`，验证 500、
  body.error_code == "unexpected_error"、body 不含 `_SecretInternalProbeError`
  类名也不含异常 message
- `test_envelope_carries_request_id_from_middleware` —— 入站
  `x-request-id: req_test123_*`，触发错误，断言 envelope.request_id
  与入站值相等
- `test_envelope_response_has_x_request_id_header` —— 同上，断言响应
  header 也带回入站值
- `test_envelope_shape_matches_unifiederrorenvelope_to_response_body`
  —— 把 envelope JSON keys 与 `UnifiedErrorEnvelope.to_response_body()`
  返回的 dict keys 做集合比对，结构对齐
- `test_compat_routes_keep_their_own_error_shape` —— `POST
  /v1/chat/completions` 用错误输入，断言响应仍是 `_compat_error_response`
  形状 `{id, object, error: {message, code}}`，**不包含**
  `error_code` / `http_status` 顶层 key

`TestClient` only。**不**真实启动 uvicorn。**不**真实加载模型。

### 3. 新增 round prompt（即本文件）

### 4. 新增 D-3 checkpoint

`files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-d3-unified-error-envelope-wired.md`
verdict line 为
`serving_hardening_d3_unified_error_envelope_wired_native_namespace`。
checkpoint 须含：

- **What This Checkpoint Is** —— 单项 wiring marker
- **What Is Now Frozen Exact** —— 含 HTTP status 映射表（before / after）
- **Test Counts** —— 四 suites 总计
- **What This Checkpoint Closes**
- **What This Checkpoint Does Not Claim**
- **Side Effects** —— 强调 native error path 的行为变化
- **Notable Implementation Choices**
- **Next Authorized Round** —— 指向 D-4（metrics endpoint wiring）/
  D-5（per-route id 去重 / idempotent load）

## 验收

- 修改后的 `owlmlx/runtime/server.py` 通过
  `.venv/bin/python -m pytest tests/test_serving_hardening.py
  tests/test_serving_hardening_wired.py
  tests/test_serving_hardening_graceful_shutdown_wired.py
  tests/test_serving_hardening_error_envelope_wired.py -q`
- 没有新增任何 stage 区域文件；`git status --short` 仅多出本轮直接
  涉及的 4 个交付路径
- checkpoint 措辞坚持 "native error namespace returns HTTP status
  codes matching the runtime error code; compat routes unchanged"，
  **不**写 "production-ready" / "complete error handling"
- checkpoint 明确记录后向兼容警告：仅看 `body.ok` 不看 HTTP status
  的现有 caller 仍然能跑（200 path 仍是成功）；同时检查 HTTP status
  的 caller 必须更新

## 不在本轮范围

- D-4 metrics endpoint wiring
- D-5 per-route id 去重 / idempotent load
- D-6 timeout 接入
- 流式 `/v1/generate/stream` 的 envelope 注入
- 422 (FastAPI 自身 validation 错误) 的 envelope 转译
- compat 路由的 envelope 切换（保持现状）
- docs/source-of-truth/serving-hardening-architecture.md 刷新
- 任何 capability matrix 行的 promotion / demotion
