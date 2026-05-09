# owlmlx Serving Hardening — Scaffold Landing Round (C-4)

## 你是谁

你是 `owlmlx` 主线执行者，落地 **C-4 serving hardening scaffold**。

本轮属于 §7 七行架构评估中明确为 **Line 4 — Serving surface (`partial`)**
的关闭路径上的**第一段 scaffold-grade 工作**：在不修改
`owlmlx/runtime/server.py`、不新增依赖、不开 batching 的前提下，
落一组**原语级别**的 hardening primitives，等后续 wiring round 一项一项
接到 FastAPI app 上。

C-4 从当前 serving surface `partial` 姿态开始，不依赖任何
native-backend capability promotion 是否已经收口；本轮只落
serving-hardening scaffold 地基，不改 capability matrix 行状态。

## 本轮唯一目标

落地以下五个交付物：

1. `owlmlx/runtime/serving_hardening.py` —— 模块骨架（middleware /
   helper / dataclass）
2. `docs/source-of-truth/serving-hardening-architecture.md` ——
   架构文档（owns 边界 + 六项 hardening 详情）
3. `tests/test_serving_hardening.py` —— scaffold 测试
4. `files/execution-prompts/owlmlx/owlmlx-serving-hardening-scaffold-landing.md`
   —— 本轮 round prompt
5. `files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-scaffold-landed.md`
   —— 本轮 checkpoint

## 本轮**不**做的事（硬规则）

- **不**修改 `owlmlx/runtime/server.py` —— wiring 是后续 round 的责任
- **不**修改 `owlmlx/serving.py`，**不**改 `GenerationGate` 的并发常量
  `MAX_GENERATION_CONCURRENCY = 1`
- **不**修改 `owlmlx/runtime/kernel.py`、`runtime/types.py`、
  `mlx_native_backend.py`、`scripts/runtime_technical_preview_server.py`
- **不**修改 `pyproject.toml` 与 `uv.lock` —— 不引入新依赖
- **不**新增 `prometheus_client`，**不**新增 `psutil`，**不**新增
  `httpx`/`requests`，**不**新增 `opentelemetry-*`
- **不**触碰
  `docs/source-of-truth/native-mlx-backend-capability-matrix.md` ——
  serving 不在 matrix 词汇里
- **不**修改 `docs/source-of-truth/single-host-orchestration-architecture.md`
- **不**修改 `conftest.py`、`README.md`、`.python-version`
- **不**改任何已存在的 test 文件
- **不**实际把 middleware 装到 app 上（任何 `app.add_middleware(...)`
  都属于 wiring round）
- **不**跑 pytest（per discipline 第 6 条）
- **不**用 thread / process spawn 实现 timeout（必须是
  `asyncio.wait_for`）
- **不**用 `prometheus_client`（必须是 `io.StringIO` 手写文本）

## 本轮**要**做的事

### 1. 新增 scaffold 模块

路径：`owlmlx/runtime/serving_hardening.py`

要求（精确对应 docs/source-of-truth/serving-hardening-architecture.md
第 5 节六项 hardening）：

#### Section 1 — Request-id propagation
- `REQUEST_ID_HEADER = "x-request-id"` 常量
- `RequestIdContext` frozen dataclass：`request_id: str`,
  `inbound: bool`，`to_dict()` 方法
- `RequestIdMiddleware(BaseHTTPMiddleware)`：
  - inbound: 读 `x-request-id`；缺失或空白则生成 `req_<uuid4hex>`
  - 把 `RequestIdContext` 挂到 `request.state.request_id_context`
  - 把裸 id 挂到 `request.state.request_id`
  - outbound: 仅当响应 header 缺失时写入；**永不覆盖** inbound id
- `derive_request_id_context(inbound_header_value)` 纯函数 helper
  （便于不依赖 Starlette `Request` 单测）

#### Section 2 — Per-request timeout + disconnect
- `RequestTimeoutPolicy` frozen dataclass：`default_timeout_s=60.0`,
  `streaming_timeout_s=600.0`, `disconnect_check_interval_s=0.5`
- `RequestTimeoutHelper`：
  - `await_with_timeout(awaitable, *, timeout_s=None)` ——
    `asyncio.wait_for` 包装；`timeout_s=None` 时退化为不计时
  - `poll_disconnect(request, *, interval_s=None)` —— async
    generator，定期 yield，检测到
    `await request.is_disconnected()` 为 True 时 raise
    `RequestDisconnectedError`
- `RequestDisconnectedError(Exception)` 异常类

#### Section 3 — Graceful shutdown
- `GracefulShutdownConfig` frozen dataclass：
  `gate_idle_timeout_s=30.0`, `unload_models_on_shutdown=True`,
  `poll_interval_s=0.05`
- `GracefulShutdown`：
  - `drain_gate(*, gate_status_callable)` —— 轮询
    `gate_status_callable()` 直到 `is_active=False` 或 timeout，
    返回 `{drained, elapsed_s, polls, final_status, timeout_s}`
  - `on_shutdown(*, gate_status_callable, unload_models_callable=None)`
    —— drain 之后可选 unload；接受同步或异步 unload callable

#### Section 4 — Unified error envelope
- `UnifiedErrorEnvelope` frozen dataclass：`id`, `error_code`,
  `message`, `request_id`, `http_status`, `object="error"`，
  `to_response_body()` 与 `to_json()` 方法
- `ErrorEnvelopeBuilder`：
  - `from_runtime_error_code(*, error_code, message, request_id,
    http_status=None)` —— 内部 static map 把
    `RuntimeErrorCode` 字符串映射到 HTTP 状态
  - `from_unexpected(exc, *, request_id)` —— **不**泄漏异常类名/消息

#### Section 5 — Prometheus metrics exporter
- `MetricsSnapshotExporter(namespace="owlmlx_native")`：
  `render_prometheus_text(*, gate_status, native_admission_snapshot)`
  → 通过 `io.StringIO` 手写 `# HELP` / `# TYPE` / value 三行格式
- 暴露指标（counter `_total` 后缀，gauge 无后缀）：
  `*_waiters`, `*_total_served_total`, `*_total_queued_total`,
  `*_longest_wait_seconds`, `*_longest_exec_seconds`,
  `*_native_max_observed_concurrency`,
  `*_native_in_critical_section`, `*_native_serving_ticket`
- 输入字段缺失时**省略**对应 metric line（不要伪造 0）

#### Section 6 — Idempotent /v1/load
- `IdempotentLoadOutcome` frozen dataclass：`model_id`,
  `already_loaded`, `memory_gb`, `ok=True`，`to_response_body()` 方法
- `IdempotentLoadHelper.interpret_backend_result(*, backend_result_dict)`
  —— 把 `error_code == "model_already_loaded"` 改写为
  `already_loaded=True, ok=True`，其它失败码原样透传

#### 模块约束
- 仅 import：`asyncio`, `dataclasses`, `io`, `json`, `time`,
  `uuid`, `collections.abc`, `typing`, plus
  `starlette.middleware.base.BaseHTTPMiddleware`,
  `starlette.requests.Request`, `starlette.responses.Response`
- **不** import `fastapi`，**不** import `owlmlx.serving`，**不**
  import `owlmlx.runtime.server`，**不** import
  `owlmlx.runtime.mlx_native_backend`
- 模块顶端的 docstring 必须说明：scaffold-grade、wiring 推迟、
  no-new-dependency、与七行评估 Line 4 的关系

### 2. 新增架构文档

路径：`docs/source-of-truth/serving-hardening-architecture.md`

10 节，1500-2000 词：

1. Status / scope / authorship
2. Why this module exists（含七行评估 Line 4 引用）
3. Non-goals（不开 batching / 不改 GenerationGate / 不动
   single-host-orchestration-architecture / 不引入新依赖）
4. Ownership boundaries（六项 hardening 各自的 owns 表，对照
   `server.py` / `GenerationGate` / `_TicketedAdmission`）
5. Six hardenings 逐项详细
6. Wiring round responsibilities (deferred)
7. Promotion-gate coupling（明确不动 native-mlx-backend-capability-matrix）
8. No-new-dependency contract
9. Extension points (not implemented)：auth / CORS / body-size /
   rate limit / OTel / structured logging / force-cancel
10. What this doc does not claim

### 3. 新增 scaffold 测试

路径：`tests/test_serving_hardening.py`

约 15-20 个测试，覆盖：

- request-id middleware 四类行为（生成 / 透传 / state attach /
  outbound header）
- timeout helper（超时 raise / 未超时返回值）
- poll_disconnect（伪造 `Request.is_disconnected` 翻转）
- graceful shutdown drain（idle 立即返回 / 多轮 polling 后 idle /
  超时未 idle / on_shutdown 顺序）
- error envelope（response body 形状 / runtime error code 映射 /
  unexpected 不泄漏类名）
- metrics exporter（HELP/TYPE/value 三行 / native admission 可选 /
  缺失字段省略）
- idempotent load（已加载 → success-with-detail / 真实失败透传 /
  成功透传）

测试约束：

- **不** import `owlmlx.runtime.server`
- **不**真实启动 uvicorn
- middleware 测试可以用 `starlette.testclient.TestClient` 跑一个
  本测试内部构造的 minimal Starlette app，**不**触碰真实 owlmlx
  app
- async 测试用 `asyncio.run()` 在测试 body 内驱动；项目里没有
  `pytest-asyncio`，不要新增

### 4. 新增 round prompt

路径：`files/execution-prompts/owlmlx/owlmlx-serving-hardening-scaffold-landing.md`

即本文件本身。

### 5. 新增 checkpoint

路径：`files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-scaffold-landed.md`

记录 verdict、什么被冻结、capability matrix 不动的理由、下一轮
建议（wiring round on serving_hardening primitives，操作员对每一
项分别审）。

## 守则与 evidence-language calibration

- 永远不写 "production-ready" / "complete hardening" / "fully
  hardened"
- 永远写 "scaffold contract" / "primitives defined" / "wiring
  deferred" / "primitive ownership recorded"
- 任何对 `runtime/server.py` 的描述都是**只读**：可以引用行号、
  解释当前没装 middleware，但不能 propose 修改
- 任何对 `GenerationGate` 的描述都是**形状**层面：不可 import 它

## 第一组命令（read-only）

```
git status -s
ls owlmlx/runtime/
grep -n "^class \|^def " owlmlx/runtime/mlx_native_backend.py | head -20
grep -n "is_active\|^class GenerationGate" owlmlx/serving.py | head -10
grep -n "create_app\|FastAPI\|add_middleware\|on_shutdown" owlmlx/runtime/server.py | head -20
```

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`scaffold_landed` / `partial` / `blocked`
2. 五个交付物路径清单
3. `git status --short` 输出
4. 实际运行的命令与关键发现（read-only 的）
5. 已知风险 / 后续 wiring round 必须知道的细节
6. 下一轮主线建议（serving wiring round？或者继续 C-1 / C-2 / C-3？）

## 守则提醒

- 保持 owlmlx 现有 dirty tree 不动（Gemma MTP probe / runtime
  monitor / heavy 等旁支不在本轮 scope）
- 只 stage 本轮 scoped 文件（5 个）
- 如果发现 starlette 在 `.venv` 里没装（不太可能，FastAPI 自带），
  在交付报告里如实写明
- pytest **不要**跑（per discipline 第 6 条）
