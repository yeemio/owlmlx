# owlmlx Serving Hardening D-6 — Structured Request Logging

## 你是谁

D-x serving hardening 链的下一格：装一个 inline `@app.middleware("http")`
的 request lifecycle logger，每请求 emit 结构化 INFO `request.start` /
`request.finish` 或 WARNING `request.exception` 日志，关联 D-1 设的
`request.state.request_id`。

**不动 scaffold**——logging middleware inline 在 server.py 内（不是
`serving_hardening.py` scaffold 的一员）。理由：scaffold 当时没立 logging
primitive；新加 scaffold 类是 scaffold 扩展不是 wiring round。

## 这一轮的边界

- **零新 scaffold**——logging middleware 直接定义在 server.py 内
- **零新依赖**——只用 stdlib `logging`
- **零 capability matrix 改动**
- **零 native backend 改动**
- **不动其它 D-x middleware / 处理器**

## 关键设计细节

**Middleware 顺序坑**：Starlette 的中间件 stacking 模型是"晚注册 = outer
= 入站先 run"。D-1 的 `app.add_middleware(RequestIdMiddleware)` 在 D-6
之前注册时，logging middleware（晚） 是 outer，会在 RequestIdMiddleware
之前 run，导致 `request.state.request_id` 还没被置位就读到 None。

**修法**：把 `app.add_middleware(RequestIdMiddleware)` 移到 D-6
`@app.middleware` 定义**之后**——RequestIdMiddleware 变 outer，先 run
置位 state；logging middleware 变 inner，后 run 读到正确 id。这是
D-6 唯一对 D-1 wiring 的 line-shuffle，文档清楚记录。

## 编辑要点（owlmlx/runtime/server.py）

1. import 加 `import logging`
2. 在 `app = FastAPI(...)` 之后、`add_middleware(RequestIdMiddleware)`
   原位置之前：
   - 删除原 `app.add_middleware(RequestIdMiddleware)` 行
   - 加结构化日志说明注释
   - 创建 `_request_logger = logging.getLogger("owlmlx.runtime.server.request")`
   - 用 `@app.middleware("http")` 定义 `_request_lifecycle_log_middleware(request, call_next)`
     - 读 method / path / `request.state.request_id`
     - 记录 `time.monotonic()` start
     - try/except 包裹 `await call_next(request)`：
       - 异常路径：log WARNING `request.exception`（含 exception_class），re-raise
       - 正常路径：log INFO `request.finish`（含 status / duration_ms）
     - start 路径：log INFO `request.start`
   - log 字段 prefix 统一 `owlmlx_*`（`owlmlx_event` / `owlmlx_request_id`
     / `owlmlx_http_method` / `owlmlx_http_path` / `owlmlx_http_status` /
     `owlmlx_duration_ms` / `owlmlx_exception_class`）
3. 在 logging middleware 定义之后加 `app.add_middleware(RequestIdMiddleware)`
   带说明注释解释顺序意义

## 测试（tests/test_serving_hardening_request_logging_wired.py，6 tests）

用 pytest `caplog` fixture 抓 `owlmlx.runtime.server.request` logger 的
record，filter `owlmlx_event`：

- `test_healthz_emits_request_start_and_request_finish_records`
- `test_request_finish_record_carries_method_path_status_duration`
- `test_request_records_carry_inbound_request_id`（关键：验证 inbound
  `x-request-id` header 一路传到日志）
- `test_request_records_carry_middleware_generated_id_when_no_inbound`
- `test_404_path_still_emits_lifecycle_records`
- `test_lifecycle_records_use_owlmlx_runtime_server_request_logger`

## 守则提醒

- evidence-language calibration：写 "structured request lifecycle logger
  installed on owlmlx.runtime.server.request"，不写 "production logging
  complete"
- staging：4 文件（M server.py、?? test_*.py、?? prompt、?? checkpoint）
- 跑全套测试 verify 全 pass

## 下一轮候选（暂停决策）

D-6 是 D-x 链当前能想到的最后一格简单 wiring。后续候选都需要明确决策：

- **C-2.1** real harness implementation（需要 67 GB RAM 跑多轮）
- **B-1.3** matrix promotion 收尾（unstaged，1 commit 即收）
- **B-2** 27B / gemma-4 sibling admissibility（需要 ~50/65 GB load）
- **C-1.3** session field deprecation（破 B-1.2 smoke 公共契约，需要
  scope-up）
- **C-3.4** pressure subscription wiring（actuator scaffold 是空壳，wiring
  价值有限）

完成后建议**主动暂停**等操作员决定方向。
