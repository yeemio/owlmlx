# owlmlx Serving Hardening — D-2 Graceful Shutdown Drain Wiring

## 你是谁

你是 `owlmlx` 主线执行者，落地 **D-2 serving hardening wiring round —
GracefulShutdown lifespan drain**。

本轮属于 §7 七行架构评估中明确为 **Line 4 — Serving surface
(`partial`)** 的关闭路径上的**第二项 wiring 工作**：把 C-4 scaffold
（`owlmlx/runtime/serving_hardening.py`）里已经定义好的
`GracefulShutdown` / `GracefulShutdownConfig` 真正接到
`owlmlx/runtime/server.py` 的 FastAPI app 的 `on_shutdown` 生命周期
钩子上。本轮**不**接 timeout / metrics / error envelope / idempotent
load —— 那些是各自独立的 D-3 / D-4 / D-5 wiring round。

D-2 从 D-1 RequestIdMiddleware wired 之后的 serving surface 状态开始，
**单项**接入 GracefulShutdown；不依赖任何 native-backend capability
promotion 是否已经收口；本轮在 `create_app(...)` 内既有的
`app.router.on_shutdown.append(_stop_runtime_monitor_sampler)`
注册之后，**追加**第二个 on_shutdown handler，使其在 sampler 停止
之后再驱动 gate drain 与 model unload。

## 本轮唯一目标

落地以下四个交付物：

1. `owlmlx/runtime/server.py` —— **修改**：在顶部 import 行追加
   `GracefulShutdown, GracefulShutdownConfig`；在
   `create_app(...)` 内已有的 `_stop_runtime_monitor_sampler`
   on_shutdown 注册之后，追加第二个 on_shutdown handler 块（包含
   构造 `GracefulShutdown(config=GracefulShutdownConfig())`、
   `gate_status_callable`、`unload_models_callable`、
   `_graceful_shutdown_drain` async 函数 + 注册）
2. `tests/test_serving_hardening_graceful_shutdown_wired.py` ——
   **新增** integration 测试，对真实 `create_app()` 构造的 owlmlx app
   用 `fastapi.testclient.TestClient` 检查 on_shutdown 注册顺序与
   handler 形态
3. `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d2-graceful-shutdown-wiring.md`
   —— **新增** 本轮 round prompt（即本文件）
4. `files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-d2-graceful-shutdown-wired.md`
   —— **新增** 本轮 checkpoint

## 本轮**不**做的事（硬规则）

- **不**修改 `owlmlx/runtime/serving_hardening.py`（C-4 scaffold 已冻结）
- **不**修改 `tests/test_serving_hardening.py`（C-4 scaffold 测试已冻结）
- **不**修改 `tests/test_serving_hardening_wired.py`（D-1 wiring 测试已冻结）
- **不**修改 `owlmlx/serving.py`，**不**改 `GenerationGate`
- **不**修改 `owlmlx/runtime/kernel.py`、`runtime/types.py`、
  `mlx_native_backend.py`、`scripts/runtime_technical_preview_server.py`
- **不**修改 `pyproject.toml` 与 `uv.lock` —— 不引入新依赖
- **不**修改 `conftest.py`、`README.md`、`.python-version`
- **不**修改任何 `docs/` 下的文件
- **不**修改 / 移除 `_stop_runtime_monitor_sampler` 的函数体或注册行
- **不**为 `GracefulShutdownConfig` 引入任何新的可调参数 —— 使用
  scaffold 默认值（`gate_idle_timeout_s=30.0`、
  `unload_models_on_shutdown=True`、`poll_interval_s=0.05`）
- **不**接 timeout / metrics / error envelope / idempotent load ——
  各自独立的 wiring round
- **不**真实启动 uvicorn / 真实加载模型 / 真实驱动一次完整的
  `await graceful_shutdown.on_shutdown(...)` 对真实
  `GenerationGate` —— `TestClient` 即可观察 `on_shutdown` 注册侧
  效应；行为 unit 测试由 C-4 scaffold 测试覆盖
- **不**新增任何 dependency

## 本轮**要**做的事

### 1. 修改 `owlmlx/runtime/server.py`

两处改动：

(a) 顶部相对路径 import block 由
```python
from .serving_hardening import RequestIdMiddleware
```
改为
```python
from .serving_hardening import GracefulShutdown, GracefulShutdownConfig, RequestIdMiddleware
```

(b) 在 `create_app(...)` 内、已有的两行
```python
app.router.on_startup.append(_start_runtime_monitor_sampler)
app.router.on_shutdown.append(_stop_runtime_monitor_sampler)
```
之后（保留这两行不动），追加一个 handler 块：构造
`GracefulShutdown(config=GracefulShutdownConfig())`，定义
`_graceful_shutdown_gate_status()`（读
`runtime.status_dict()["generation_gate"]` 并以 dict 返回）、
`_graceful_shutdown_unload_models()`（读
`runtime.status_dict()["backend"]["loaded_models"]` 列表，按
`model_id` 调用 `runtime.unload_model(model_id)`，按 ok / 非 ok 分桶
返回 `{"unloaded_model_ids": [...], "failed": [...]}`）、然后是
`async def _graceful_shutdown_drain()` 内部
`await graceful_shutdown.on_shutdown(...)`，最后
`app.router.on_shutdown.append(_graceful_shutdown_drain)`。

**没有别的改动**。`_stop_runtime_monitor_sampler` 不动；FIFO 顺序由
`app.router.on_shutdown` 是 list、`.append` 是 O(1) tail-insertion
保证：lifespan-shutdown 时 sampler 先停，drain 再发生。

### 2. 新增 `tests/test_serving_hardening_graceful_shutdown_wired.py`

针对**真实** owlmlx app 的 integration 测试，用
`fastapi.testclient.TestClient`：

- create_app 构造成功并能服务 `/healthz`（smoke）
- `_graceful_shutdown_drain` 在 `app.router.on_shutdown` 列表里出现，
  且是 coroutine function
- FIFO 顺序：`_stop_runtime_monitor_sampler` 的 index 严格小于
  `_graceful_shutdown_drain` 的 index
- 在 patch 掉 `GracefulShutdown.on_shutdown` 的前提下，
  `with TestClient(app):` 进 / 出 lifespan 时该 patched 协程被 await
  一次；patched 协程内调用 gate_status_callable 取一次 snapshot，
  observe 默认 FakeBackend 下 `is_active` 为 False（不严格断言每个
  字段，但断言形态是 dict）
- 一个独立的 wiring-shape 测试：用 stub kernel 替身验证 unload
  callable 的迭代逻辑（按 `model_id` 调 `unload_model`，按 ok 状态
  分桶返回报告），**不**依赖真实 backend

不 spawn uvicorn，不加载模型，不依赖任何 ledger / runtime extra。

### 3. 新增 round prompt

路径：`files/execution-prompts/owlmlx/owlmlx-serving-hardening-d2-graceful-shutdown-wiring.md`

即本文件本身。

### 4. 新增 checkpoint

路径：`files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-d2-graceful-shutdown-wired.md`

verdict line：`serving_hardening_d2_graceful_shutdown_lifespan_wired`

记录什么被冻结、为什么 capability matrix 不动、FIFO 顺序如何在
`app.router.on_shutdown` 上实际生效、下一轮（D-3：unified error
envelope wiring；D-4：metrics endpoint wiring）。

## 守则与 evidence-language calibration

- 写 "GracefulShutdown lifespan handler installed; drain target is
  GenerationGate; sampler stop is preserved as first handler in FIFO
  order"
- **不**写 "graceful shutdown is supported" / "production-ready"
- 不要假装 `GracefulShutdown.on_shutdown` 的行为已被 wiring round
  端到端验证；行为正确性属于 C-4 scaffold 测试的责任，本轮只证明
  wiring 入位

## 第一组命令（read-only）

```
git status -s
grep -n "create_app\|on_shutdown\|GracefulShutdown" owlmlx/runtime/server.py | head -20
grep -n "GracefulShutdown\|GracefulShutdownConfig" owlmlx/runtime/serving_hardening.py | head -10
```

## 验证

运行：

```
.venv/bin/python -m pytest tests/test_serving_hardening.py tests/test_serving_hardening_wired.py tests/test_serving_hardening_graceful_shutdown_wired.py -q
```

确认新测试通过 + 已有 C-4 scaffold + D-1 wired 测试不回归。如果
`tests/` 之外其它测试失败，**不**修，照实报告。

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`d2_wired` / `partial` / `blocked`
2. 四个交付物路径清单（1 个 modified + 3 个 new）
3. `git status --short` 输出，证明 round scope
4. pytest 输出（`tests/test_serving_hardening.py` +
   `tests/test_serving_hardening_wired.py` +
   `tests/test_serving_hardening_graceful_shutdown_wired.py`）
5. `server.py` 改动的 diff 摘要
6. 已知风险 / 后续 wiring round 必须知道的细节（FIFO 顺序的实际
   依赖、unload 在真实 backend 失败时的可观测性、drain timeout
   默认值是否需要在 D-2.1 round 提升）

## 守则提醒

- 保持 owlmlx 现有 dirty tree 不动（Gemma MTP probe / runtime monitor
  / heavy 等旁支不在本轮 scope）
- **不** stage（用户负责 stage）
- 只 round-scope 的 4 个文件
