# owlmlx Serving Hardening — D-1 Request-id Middleware Wiring

## 你是谁

你是 `owlmlx` 主线执行者，落地 **D-1 serving hardening wiring round —
RequestIdMiddleware**。

本轮属于 §7 七行架构评估中明确为 **Line 4 — Serving surface
(`partial`)** 的关闭路径上的**第一项 wiring 工作**：把 C-4 scaffold
（`owlmlx/runtime/serving_hardening.py`）里已经定义好的
`RequestIdMiddleware` 真正接到 `owlmlx/runtime/server.py` 的 FastAPI
app 上。本轮**不**接 timeout / shutdown drain / metrics / error
envelope / idempotent load — 那些是各自独立的 D-2 / D-3 / D-4 / D-5 /
D-6 wiring round。

D-1 从 C-4 scaffold landed 之后的 serving surface `partial` 姿态开始，
**单项**接入 RequestIdMiddleware；不依赖任何 native-backend capability
promotion 是否已经收口；本轮只增加一行
`app.add_middleware(RequestIdMiddleware)` 到 `create_app(...)`。

## 本轮唯一目标

落地以下四个交付物：

1. `owlmlx/runtime/server.py` —— **修改**：在 `create_app(...)` 顶部
   添加 `app.add_middleware(RequestIdMiddleware)` 一行 + 一行 import
2. `tests/test_serving_hardening_wired.py` —— **新增** integration
   测试，对真实 `create_app()` 构造的 owlmlx app 用
   `fastapi.testclient.TestClient` 跑 `/healthz` + 404 路径
3. `files/execution-prompts/owlmlx/owlmlx-serving-hardening-d1-request-id-wiring.md`
   —— **新增** 本轮 round prompt（即本文件）
4. `files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-d1-request-id-wired.md`
   —— **新增** 本轮 checkpoint

## 本轮**不**做的事（硬规则）

- **不**修改 `owlmlx/runtime/serving_hardening.py`（C-4 scaffold 已冻结）
- **不**修改 `tests/test_serving_hardening.py`（C-4 scaffold 测试已冻结）
- **不**修改 `owlmlx/serving.py`，**不**改 `GenerationGate`
- **不**修改 `owlmlx/runtime/kernel.py`、`runtime/types.py`、
  `mlx_native_backend.py`、`scripts/runtime_technical_preview_server.py`
- **不**修改 `pyproject.toml` 与 `uv.lock` —— 不引入新依赖
- **不**修改 `conftest.py`、`README.md`、`.python-version`
- **不**修改任何 `docs/` 下的文件（包括
  `docs/source-of-truth/serving-hardening-architecture.md` —— 该文档
  的 D-1 wiring status refresh 推迟到独立的 doc-cleanup round）
- **不**移除 / 修改 `server.py` lines 1258 / 1293 / 1445 / 1587 /
  1676 处的 per-route `req_<uuid4hex>` 生成代码 —— 那些 ad-hoc
  逻辑在 D-1 之后变成冗余但仍然 honored；去重是 **D-1.1** 的责任
- **不**接 timeout / shutdown drain / metrics / error envelope /
  idempotent load —— 各自独立的 wiring round
- **不**真实启动 uvicorn / 真实加载模型 —— `TestClient` 即可
- **不**新增任何 dependency

## 本轮**要**做的事

### 1. 修改 `owlmlx/runtime/server.py`

两处单行改动（整文件总共 +2 行）：

(a) 顶部 import block 增加：

```python
from .serving_hardening import RequestIdMiddleware
```

（与已有的 `from .backends import ...`, `from .kernel import ...`,
`from .types import ...` 同风格相对路径 import）

(b) 在 `create_app(...)` 内部、`FastAPI(...)` 构造之后、`app.state.*`
赋值之前，加一行：

```python
app.add_middleware(RequestIdMiddleware)
```

**没有别的改动**。`server.py` lines 1258 / 1293 / 1445 / 1587 / 1676
处的 per-route `req_<uuid4hex>` 不动；这些路由会自己写
`x-request-id` 响应头，因 `RequestIdMiddleware.dispatch` 只在响应缺失
该 header 时才写入，所以 per-route id 优先 honored，middleware-set id
只对没有自己写 header 的路由（例如 `/healthz`）生效。这是过渡形态；
D-1.1 round 负责把 per-route ad-hoc 生成统一改成读
`request.state.request_id`。

### 2. 新增 `tests/test_serving_hardening_wired.py`

针对**真实** owlmlx app 的 integration 测试，用
`fastapi.testclient.TestClient`：

- inbound `x-request-id` header 在 `/healthz` 响应里原样回传
- 缺失 inbound 时，`/healthz` 响应里出现自动生成的
  `req_<uuid4hex>`（32 hex chars 后缀）
- middleware **不**改 `/healthz` 响应 body 的 shape（带 / 不带 inbound
  header 时 body 一致）
- 404 路径（`/nonexistent`）也带 `x-request-id`，且 lossless 透传 inbound
- 不 spawn uvicorn，不加载模型，不依赖任何 ledger / runtime extra

### 3. 新增 round prompt

路径：`files/execution-prompts/owlmlx/owlmlx-serving-hardening-d1-request-id-wiring.md`

即本文件本身。

### 4. 新增 checkpoint

路径：`files/execution-prompts/owlmlx/coordinator-checkpoint-serving-hardening-d1-request-id-wired.md`

verdict line：`serving_hardening_d1_request_id_middleware_wired_lossless`

记录什么被冻结、为什么 capability matrix 不动、per-route id 仍并存的
过渡解释、下一轮（D-1.1: per-route id 去重；D-2: graceful shutdown
wiring）。

## 守则与 evidence-language calibration

- 写 "RequestIdMiddleware installed lossless on the real owlmlx app"
- **不**写 "request id propagation is supported" / "production-ready"
- per-route id 仍然并存的事实必须如实记录，不能掩盖

## 第一组命令（read-only）

```
git status -s
grep -n "create_app\|FastAPI\|add_middleware" owlmlx/runtime/server.py | head -20
grep -n "RequestIdMiddleware\|REQUEST_ID_HEADER" owlmlx/runtime/serving_hardening.py | head -10
```

## 验证

运行：

```
.venv/bin/python -m pytest tests/test_serving_hardening.py tests/test_serving_hardening_wired.py -q
```

确认新测试通过 + 已有 C-4 scaffold 测试不回归。如果 `tests/` 之外
其它测试失败，**不**修，照实报告。

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`d1_wired` / `partial` / `blocked`
2. 四个交付物路径清单（1 个 modified + 3 个 new）
3. `git status --short` 输出，证明 round scope
4. pytest 输出（`tests/test_serving_hardening.py` +
   `tests/test_serving_hardening_wired.py`）
5. `server.py` 改动的 diff 摘要（应当是 +2 -0）
6. 已知风险 / 后续 wiring round 必须知道的细节（per-route id 仍并存
   是否会导致任何路由响应被 middleware-set id 覆盖）

## 守则提醒

- 保持 owlmlx 现有 dirty tree 不动（Gemma MTP probe / runtime monitor
  / heavy 等旁支不在本轮 scope）
- **不** stage（用户负责 stage）
- 只 round-scope 的 4 个文件
