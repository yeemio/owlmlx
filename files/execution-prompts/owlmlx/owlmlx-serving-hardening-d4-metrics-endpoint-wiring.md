# owlmlx Serving Hardening — D-4 Metrics Endpoint Wiring

## 你是谁

你是 `owlmlx` 主线执行者，落地 **D-4 serving hardening wiring round —
MetricsSnapshotExporter `/metrics` route wiring**。

本轮属于 §7 七行架构评估中明确为 **Line 4 — Serving surface
(`partial`)** 的关闭路径上的**第四项 wiring 工作**：把 C-4 scaffold
（`owlmlx/runtime/serving_hardening.py`）里已经定义好的
`MetricsSnapshotExporter` 真正接到 `owlmlx/runtime/server.py` 的
FastAPI app 上 —— 注册 `GET /metrics` 路由，从 `runtime.status_dict()`
读取 `generation_gate` 与可选的 `backend.detail.admission` 切片，
通过 `render_prometheus_text(...)` 渲染 Prometheus text-exposition
格式（line-based plain text），以 `text/plain; version=0.0.4`
content-type 返回。

D-4 从 D-1 RequestIdMiddleware wired + D-2 GracefulShutdown drain
wired + D-3 UnifiedErrorEnvelope wired 之后的 serving surface 状态开始，
**单项**接入 metrics endpoint；不依赖任何 native-backend capability
promotion 是否已经收口。

## 本轮唯一目标

落地以下四个交付物：

1. `owlmlx/runtime/server.py` —— **修改**：在顶部相对路径 import block
   追加 `MetricsSnapshotExporter`；在 `create_app(...)` 内的
   `error_envelope_builder = ErrorEnvelopeBuilder(...)` 旁边构造
   `_metrics_exporter = MetricsSnapshotExporter(namespace="owlmlx_native")`；
   在 `create_app(...)` 末尾、`return app` 之前注册一条
   `@app.get("/metrics")` 路由
2. `tests/test_serving_hardening_metrics_wired.py` —— **新增** integration
   测试，对真实 `create_app()` 构造的 owlmlx app 用
   `fastapi.testclient.TestClient` 检查 `/metrics` 路由的 200 状态、
   `text/plain` content-type、命名空间前缀、gate-counter metric 名、
   `# HELP` / `# TYPE` 行、idempotency、无 native admission 时的渲染、
   request-id 透传
3. `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d4-metrics-endpoint-wiring.md`
   —— **新增** 本轮 round prompt（即本文件）
4. `files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-d4-metrics-endpoint-wired.md`
   —— **新增** 本轮 checkpoint，verdict 为
   `serving_hardening_d4_metrics_endpoint_wired_prometheus_text`

## 本轮**不**做的事（硬规则）

- **不**修改 `owlmlx/runtime/serving_hardening.py`（C-4 scaffold 已冻结）
- **不**修改 `tests/test_serving_hardening.py`（C-4 scaffold 测试已冻结）
- **不**修改 `tests/test_serving_hardening_wired.py`（D-1 wiring 测试已冻结）
- **不**修改
  `tests/test_serving_hardening_graceful_shutdown_wired.py`（D-2 wiring 测试已冻结）
- **不**修改
  `tests/test_serving_hardening_error_envelope_wired.py`（D-3 wiring 测试已冻结）
- **不**修改 `owlmlx/serving.py`，**不**改 `GenerationGate`
- **不**修改 `owlmlx/runtime/kernel.py`、`owlmlx/runtime/types.py`、
  `owlmlx/runtime/mlx_native_backend.py`、`scripts/runtime_technical_preview_server.py`
- **不**修改 `pyproject.toml` / `uv.lock` —— **不**引入新依赖
  （特别是 `prometheus_client` 不引入）
- **不**修改 `conftest.py`、`README.md`、`.python-version`
- **不**修改任何 `docs/` 下的文件
- **不**改 D-1 `app.add_middleware(RequestIdMiddleware)` 注册行
- **不**改 D-2 `_graceful_shutdown_drain` 注册块
- **不**改 D-3 `_unhandled_exception_handler` /
  `app.add_exception_handler(Exception, ...)` 注册块、
  native error code -> HTTP status 映射、
  `_native_runtime_response(...)` 适配器
- **不**改 `_compat_error_response` / `_anthropic_error_response`
  函数体或调用点
- **不**改任何 compat 路由（`/v1/chat/completions`、`/v1/messages`、
  `/v1/completions`）的 error 响应形状
- **不**改 `/v1/generate/stream`、`/v1/messages/count_tokens` 或其他非
  metrics 路由
- **不**改任何 `/v1/runtime/*` 路由
- **不**接 timeout / idempotent-load helper class —— 各自独立的 wiring round
- **不**真实启动 uvicorn / 真实加载模型；`TestClient` 即可观察
  `/metrics` 渲染侧效应；行为 unit 测试由 C-4 scaffold 测试覆盖
- **不**新增任何 dependency
- **不**为 `/metrics` 加任何鉴权 —— Prometheus scraper 默认不带 auth header；
  网络层访问控制由 operator 负责（在 checkpoint 的 Notable Implementation
  Choices 中显式记录）
- **不**把 `/metrics` 包进 unified error envelope —— Prometheus scraper
  期望 plain text，不接受 JSON envelope 形状；exporter 内部异常应回退到
  字面 `# owlmlx_metrics_render_error 1` 文本行 + status 200，让 scrape
  本身仍然成功

## 本轮**要**做的事

### 1. 修改 `owlmlx/runtime/server.py`

三处改动：

(a) 顶部相对路径 import block 由
```python
from .serving_hardening import (
    ErrorEnvelopeBuilder,
    GracefulShutdown,
    GracefulShutdownConfig,
    RequestIdMiddleware,
    UnifiedErrorEnvelope,
)
```
改为
```python
from .serving_hardening import (
    ErrorEnvelopeBuilder,
    GracefulShutdown,
    GracefulShutdownConfig,
    MetricsSnapshotExporter,
    RequestIdMiddleware,
    UnifiedErrorEnvelope,
)
```

只追加 `MetricsSnapshotExporter` 一行；其它 D-1 / D-2 / D-3 已经在线
的 import 不动。

(b) 在 `create_app(...)` 内、紧跟
`error_envelope_builder = ErrorEnvelopeBuilder(namespace="owlmlx_native")`
那一行之后，构造一个一次性的 exporter：
```python
_metrics_exporter = MetricsSnapshotExporter(namespace="owlmlx_native")
```
并在它前面挂 D-4 wiring 块的 docstring 注释（说明 exporter 是 pure、
每次 scrape 直接读 `runtime.status_dict()`、不缓存、不开 background sampler、
`/metrics` 不被 unified error envelope 包裹、route 默认不鉴权）。

(c) 在 `create_app(...)` 末尾、`return app` 之前、紧随 `/v1/unload`
路由之后，注册一条 `@app.get("/metrics")` 路由：
- 函数内部 function-local import `Response`：`from starlette.responses import Response`
  （以避免顶部 import block 被多扩一个外部 symbol；Starlette 已经被
  FastAPI 依赖，没有新依赖）
- `try` 块：调用 `runtime.status_dict()`，安全读 `generation_gate` /
  `backend.detail.admission`，调用
  `_metrics_exporter.render_prometheus_text(gate_status=...,
  native_admission_snapshot=...)` 渲染 text
- `except Exception` 兜底：回退到字面字符串
  `"# owlmlx_metrics_render_error 1\n"`（保持 200 让 scraper 不会硬失败）
- `return Response(content=text, media_type="text/plain; version=0.0.4")`

**没有别的改动**。`/v1/load` / `/v1/generate` / `/v1/unload` 等 native
路由不动。所有 compat 路由不动。所有 `/v1/runtime/*` 路由不动。
D-1 / D-2 / D-3 注册块不动。

### 2. 新增 `tests/test_serving_hardening_metrics_wired.py`

5 到 7 个 integration 测试用 `fastapi.testclient.TestClient` 对真实
`create_app()` 构造的 owlmlx app 执行：

- `test_metrics_endpoint_returns_200_with_prometheus_text_media_type` ——
  GET `/metrics` 返回 200，`content-type` 以 `text/plain` 开头且包含
  `version=0.0.4`
- `test_metrics_endpoint_includes_owlmlx_native_namespace_prefix` ——
  body 含 `owlmlx_native_` 前缀（来自 `MetricsSnapshotExporter` 的
  `namespace="owlmlx_native"` 构造参数）
- `test_metrics_endpoint_includes_gate_counters` —— body 含
  `owlmlx_native_waiters` / `owlmlx_native_total_served_total` /
  `owlmlx_native_total_queued_total` 等 gate-counter metric 名
- `test_metrics_endpoint_includes_TYPE_HELP_lines` —— body 含
  Prometheus 约定的 `# HELP` 与 `# TYPE` 注释行
- `test_metrics_endpoint_idempotent_on_repeated_get` —— 连续两次 GET
  都是 200，且 metric 名集合一致（exporter 是 pure 渲染）
- `test_metrics_endpoint_works_with_no_native_admission_snapshot` ——
  `FakeBackend` 不填 `backend.detail.admission`，验证 `/metrics` 仍能
  正常渲染、不抛、不出现 `native_max_observed_concurrency` /
  `native_in_critical_section` / `native_serving_ticket` 行
- `test_metrics_endpoint_carries_request_id_propagation` —— 入站
  `x-request-id` header 在 `/metrics` 响应 header 中原样回写（D-1
  middleware 对每条路由都生效）

`TestClient` only。**不**真实启动 uvicorn。**不**真实加载模型。

### 3. 新增 round prompt（即本文件）

### 4. 新增 D-4 checkpoint

`files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-d4-metrics-endpoint-wired.md`
verdict line 为
`serving_hardening_d4_metrics_endpoint_wired_prometheus_text`。
checkpoint 须含：

- **What This Checkpoint Is** —— 单项 wiring marker
- **What Is Now Frozen Exact** —— `server.py` 三处改动、`/metrics`
  路由 contract（路径、状态码、content-type、body 形状）
- **Test Counts** —— 五个 suites 总计
- **What This Checkpoint Closes**
- **What This Checkpoint Does Not Claim**
- **Side Effects** —— 新增 unauthenticated route，operator 负责网络
  层访问控制
- **Notable Implementation Choices** —— 函数内 `Response` import；
  `/metrics` 不被 unified error envelope 包裹；render 失败回退到
  `# owlmlx_metrics_render_error 1` 文本行而非 5xx；exporter 是 pure、
  不开 sampler 任务
- **Next Authorized Round** —— 指向 D-5 / D-6 候选

## 验收

- 修改后的 `owlmlx/runtime/server.py` 通过
  `.venv/bin/python -m pytest tests/test_serving_hardening.py
  tests/test_serving_hardening_wired.py
  tests/test_serving_hardening_graceful_shutdown_wired.py
  tests/test_serving_hardening_error_envelope_wired.py
  tests/test_serving_hardening_metrics_wired.py -q`
- 没有新增任何 stage 区域文件；`git status --short` 仅多出本轮直接
  涉及的 4 个交付路径
- checkpoint 措辞坚持 "/metrics endpoint installed; renders Prometheus
  text from current runtime status snapshot per scrape"，**不**写
  "production-ready monitoring" / "complete observability"
- checkpoint 明确记录 `/metrics` 默认不鉴权与不被 unified error envelope
  包裹这两项的依据

## 不在本轮范围

- D-5 per-route id 去重 / idempotent load helper class
- D-6 timeout 接入
- 流式 `/v1/generate/stream` 的 envelope 注入
- 422 (FastAPI 自身 validation 错误) 的 envelope 转译
- compat 路由的 envelope 切换（保持现状）
- 任何 background sampler / cache / aggregation —— exporter 仍是 pure
- 任何引入 `prometheus_client` / `psutil` / 其它新依赖的工作
- `docs/source-of-truth/serving-hardening-architecture.md` 刷新
- 任何 capability matrix 行的 promotion / demotion
