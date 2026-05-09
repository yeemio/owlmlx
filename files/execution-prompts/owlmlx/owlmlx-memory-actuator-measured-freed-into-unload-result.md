# owlmlx Memory Actuator Measured-Freed-Bytes into UnloadResult (C-3.2)

## 你是谁

你是 `owlmlx` 这一轮的执行者。这是 C-3.1 之后的 follow-up：把 actuator
receipt 里的 measured 字节读数（active / cache memory before-after）作
为新的可选字段暴露到 `UnloadResult` 上，让 HTTP 调用方和 OwlOps 能区分
"声明 freed_gb" 与 "测量 freed bytes"。

**这是公共类型扩展**——`UnloadResult` 是返回给所有 caller 的对象。两
个新字段都是 `int | None = None`，对既有 caller 完全 backward-compat
（不传不报错、不读不影响）。

## 这一轮的边界

- **零新能力**——actuator 仍只在 native unload 时被调用一次
- **零 HTTP API shape 改动**——`/v1/unload` 现有 JSON 响应自然多两个
  字段（HTTP API 不强制 schema 严格性，多余字段不破坏调用方）
- **零 capability matrix 改动**
- **零 actuator API 修改**
- **不动 subprocess backend**——它的 unload 走 process exit，不 invoke
  actuator，所以这两个新字段在 subprocess 路径上自然为 None
- **不动 kernel.py / backends.py 的 UnloadResult 构造点**——它们的
  返回路径不经 actuator，自然 default None
- **不动其他 RuntimeOperationResult 子类**（LoadResult / RestartResult
  等）

## 为什么这一轮存在

C-3.1 的 receipt 持久化在 `backend._last_unload_receipt` 上——内部可观
察、外部不可观察。HTTP `/v1/unload` 调用方要拿到 measured 释放字节得
绕弯（call /v1/runtime/status 查 backend detail，再 join model_id）。

C-3.2 把"声明 vs 测量"区分作为 first-class API 字段：

- `freed_gb` 是 declared（操作员宣称的 model 体量）
- `active_memory_freed_bytes` 是 measured（actuator 实测 active pool
  delta）
- `cache_memory_freed_bytes` 是 measured（actuator 实测 cache pool
  delta）

让 OwlOps 这种 dashboard 能展示"declared 12.5 GB / measured 8.2 GB"两
栏，体现 owlmlx 第一次有"测量诚实度"的工程证据。

## 这一轮要做的最小切口

### 编辑 1：`owlmlx/runtime/types.py`

在 `UnloadResult` 末尾追加两个字段：

```python
active_memory_freed_bytes: int | None = None
cache_memory_freed_bytes: int | None = None
```

带 docstring 说明：来源是 C-3.1 actuator receipt；None 表示
measurement 不可用（无 runtime extra / subprocess backend / 任何不调
actuator 的 backend）；`freed_gb` 仍是 declared，不被覆盖。

### 编辑 2：`owlmlx/runtime/mlx_native_backend.py` `unload` body 扩展

在 actuator 调用之后、return UnloadResult 之前：
1. 调 `self._compute_freed_bytes(before, after)` 算 active delta
2. 同样算 cache delta
3. 把两个 delta 传进 UnloadResult 构造

新增 `_compute_freed_bytes(before, after)` staticmethod：
- 任一为 None → 返回 None
- 否则返回 `max(0, before - after)`——**clamp 到 0** 防止 allocator
  增长被错误展示成"负释放"

### 编辑 3：`tests/test_mlx_native_backend_memory_actuator_release.py`

在既有 6 个 C-3.1 测试基础上扩 4 个 C-3.2 测试：

- `test_unload_result_carries_measured_active_freed_bytes_when_mlx_present` —
  fake_mx 的 clear_cache 减 200_000_000，断言字段 == 200_000_000
- `test_unload_result_measured_fields_are_none_without_mlx` — no-mlx
  路径下两个字段都为 None
- `test_unload_result_clamps_negative_deltas_to_zero` — 用 _GrowingMlx
  fake（clear_cache 后 active 增长）验证 clamp 到 0；同时验证 receipt
  本身仍带原始 before/after（clamp 在 UnloadResult 层不在 receipt 层）
- `test_unload_result_preserves_freed_gb_when_measurement_present` — 同
  时有 declared 12.5 GB 和 measured 200_000_000 bytes，两个字段独立
  不互相覆盖

## 这一轮**不**做的事

- **不**改 LoadResult、GenerateResult、RestartResult 等其它结果类
- **不**改 `/v1/unload` 路由代码——multipart fields 自然进 JSON 响应
- **不**给 subprocess backend 加测量字段（它没 actuator 触发点）
- **不**新增 actuator 方法或调整现有实现
- **不**触发 env-gated B-1.2 smoke
- **不**把 measured 字节用作 freed_gb 计算源——declared 仍是首要值

## 守则提醒

- **evidence-language calibration**：写"measured allocator deltas
  surfaced via UnloadResult; declared freed_gb unchanged"，不写
  "memory accounting now accurate" / "production memory metrics"
- **staging discipline**：本轮 staged 仅含
  - `M  owlmlx/runtime/types.py`
  - `M  owlmlx/runtime/mlx_native_backend.py`
  - `M  tests/test_mlx_native_backend_memory_actuator_release.py`
  - `??  files/execution-prompts/owlmlx/owlmlx-memory-actuator-measured-freed-into-unload-result.md`
  - `??  files/execution-prompts/owlmlx/coordinator-checkpoint-memory-actuator-measured-freed-into-unload-result.md`
  共 5 文件
- **跑全套测试** verify regression 全过（预期 119 passed + 3 skipped）

## 第一组命令

```bash
# UnloadResult 既有构造点
grep -rn "UnloadResult(" owlmlx/runtime/ | head

# 既有 actuator wiring
grep -nA20 "self._last_unload_receipt = " owlmlx/runtime/mlx_native_backend.py
```

## 交付格式

1. `types.py` 字段追加 diff
2. `mlx_native_backend.py` `unload` body 扩展 + `_compute_freed_bytes`
   helper diff
3. `test_mlx_native_backend_memory_actuator_release.py` 新增 4 个测试
4. checkpoint
5. focused regression 结果

## 下一轮候选（不在此轮范围）

- **C-3.3** allocator floor configuration（`actuator.configure_allocator_floor`
  调 `mx.set_cache_limit`，防止 cache pool 无限增长）
- **D-4** Prometheus `/metrics` endpoint wiring（独立文件，与本轮可并行）
- **D-5** per-route id 去重
- **C-2.1** real harness implementation
- **C-1.3** session field deprecation（cosmetic）
