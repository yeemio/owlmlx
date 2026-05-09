# owlmlx Memory Actuator Allocator Floor Configuration (C-3.3)

## 你是谁

C-3.x 三件套的最后一格：把 `actuator.configure_allocator_floor(...)`
接入 `MlxNativeBackend.load`，让 owlmlx 在第一次 load 时根据**操作员
opt-in env vars** 设 mlx 的 `set_cache_limit` / `set_wired_limit`，防
止 unified memory cache pool 长期不受界增长。

## 这一轮的边界

- **零默认行为变化**——env vars 不设 → 旧行为完全保留（不调
  configure_allocator_floor）
- **零 capability matrix 改动**
- **零 actuator API 修改**
- **零 unload 路径改动**——C-3.3 只改 load 路径
- **零 server.py 改动**

## 操作员 opt-in 契约

两个 env var：
- `OWLMLX_NATIVE_CACHE_LIMIT_BYTES`：设 `mx.set_cache_limit(N)`
- `OWLMLX_NATIVE_WIRED_LIMIT_BYTES`：设 `mx.set_wired_limit(N)`（macOS
  15+ only；fake module 缺该 attr 时 actuator 自动 skip）

任一设了就触发 configure；都没设跳过。

## 这一轮的 5 处增量（owlmlx/runtime/mlx_native_backend.py）

1. import：加 `os`；扩展 memory_actuator import 加 `AllocatorFloorConfig`
2. `__init__` 增加 `_allocator_floor_configured: bool = False` 和
   `_last_allocator_floor_config: AllocatorFloorConfig | None = None`
3. 新方法 `_maybe_configure_allocator_floor()`：先 set flag（防重入）
   → 读 env → 二者皆 None 则 return → lazy import mlx.core → actuator
   构造 → call configure_allocator_floor
4. 新静态方法 `_read_env_int(env_var)`：parse 失败/空/缺 → 返回 None
5. `load()` 在 `return LoadResult(ok=True,...)` 之前调
   `self._maybe_configure_allocator_floor()`——idempotent flag 保证只
   触发一次

## 测试（tests/test_mlx_native_backend_allocator_floor_config.py，7 tests）

- `test_load_does_not_configure_when_no_env_vars`
- `test_load_configures_when_cache_limit_env_set`
- `test_load_configures_when_wired_limit_env_set`
- `test_load_configures_only_once_across_multiple_loads`（idempotent）
- `test_load_with_no_mlx_returns_noop_config_when_env_set`
- `test_load_handles_invalid_env_var_value_gracefully`
- `test_load_skips_wired_limit_when_mlx_lacks_attribute`

## 守则提醒

- evidence-language calibration：写 "operator-opt-in floor wired"，不
  写 "memory governance complete"
- staging：5 文件（M mlx_native_backend.py、?? test_*.py、?? prompt、
  ?? checkpoint）
- 不动其它文件
- 跑全套测试 verify regression

## 下一轮候选

- **C-3.4** `actuator.notify_pressure` 接入 host_pressure（pressure
  event 真实触发点）
- **D-6** structured logging（每 request 一条结构化日志）
- **C-1.3** session field deprecation
- **C-2.1** real harness implementation（杠杆最大、最重）
