# owlmlx Memory Actuator Wiring into Native Unload (C-3.1)

## 你是谁

你是 `owlmlx` 这一轮的执行者。这是 C-3 memory_actuator scaffold 之后的
follow-up：把 `memory_actuator.release_single_model(...)` 接入
`MlxNativeBackend.unload`。**第一次**让 owlmlx 在产品 unload 路径上真正
调用 `mx.clear_cache()`——之前 unload 只是 drop Python 引用让 GC 处理。

**不是新增能力**，是把 C-3 已经写好的 actuator 产品化。运行特征对外仍
保持："unload 后内存释放回 OS"——但现在有**测量证据**而不是仅依赖
GC。

## 这一轮的边界

- **零新能力**——actuator 仍是 scaffold，pinned-model invariant 维持，
  no_automatic_background_eviction_loop 维持
- **零 capability matrix 改动**
- **零 pyproject 改动**——`mlx.core` 是惰性 import，`runtime` extra 缺失
  时 actuator 走 no-op 分支
- **零 actuator API 修改**——release_single_model 签名不动；只是开始调
  用它
- **零 unload 行为外部变化**——`UnloadResult.ok / freed_gb` 仍同口径
  返回；新增的 receipt 通过 `backend._last_unload_receipt` 内部观察，
  不进 UnloadResult

## 为什么这一轮存在

C-3 checkpoint 明确写了"the native backend's existing unload is NOT
modified to call this in this round; integration is a follow-up
extension point". 这就是那个 follow-up。不做这一轮的话：

- `mx.clear_cache()` 永远不会被 owlmlx 主动调用——只能等 macOS unified
  memory 自然 reclaim
- C-3 的工程价值（actuator 是唯一 sanctioned `mx.clear_cache()` 调用点）
  没兑现
- B-1.2 的 "unload 后 65 GB 回流"实际是 OS 而不是 owlmlx 在控制——
  这一轮把控制权拿回 owlmlx

## 这一轮要做的最小切口

### 编辑 1：`owlmlx/runtime/mlx_native_backend.py`

四处增量：

1. **import**：在 C-1.x 的
   `from owlmlx.cache_manager import ...` 之后增加
   `from owlmlx.memory_actuator import MemoryActuator, ReclaimReceipt`
2. **`MlxNativeBackend.__init__`** 增加
   `self._last_unload_receipt: ReclaimReceipt | None = None` 字段
3. **新静态方法** `_try_import_mlx_core()`：
   - `try: import mlx.core as mx_core` 成功返回 module
   - `except ImportError: return None`
4. **`unload()` body** 在 `freed = float(...)` 之后、return 之前注入：
   ```python
   mlx_core_module = self._try_import_mlx_core()
   actuator = MemoryActuator(mlx_module=mlx_core_module)
   self._last_unload_receipt = actuator.release_single_model(
       model_id=model_id,
       declared_freed_gb=freed,
   )
   ```

actuator 是**每次 unload 一个新实例**——open ownership state（pressure
listeners 等）目前没人 wire，所以 throw-away 实例是干净选择。
未来如有需要，可以改成 backend lifetime owned。

### 编辑 2：新测试文件
`tests/test_mlx_native_backend_memory_actuator_release.py`

6 个测试：
- `test_unload_invokes_memory_actuator_and_persists_receipt`
- `test_unload_with_real_mlx_invokes_clear_cache_via_actuator`
- `test_unload_with_no_mlx_module_returns_noop_receipt`
- `test_unload_receipt_carries_declared_freed_gb`
- `test_unload_actuator_runs_after_release_active_cache`（顺序断言）
- `test_unload_unknown_model_does_not_overwrite_last_receipt`

测试技巧：用 `monkeypatch.setattr(backend, "_try_import_mlx_core", ...)`
切换 mlx.core 是否可用，避免污染 sys.modules。`_FakeMlxCore` 类带
`clear_cache_call_count` 计数器和 `get_active_memory` /
`get_cache_memory` 合成读数器，让 receipt 字段全部可断言。

### **不**改的部分

- **不**改 `UnloadResult` 类型（types.py）——freed_gb 仍是 declared，
  measured 字段未引入；想让 measured 进 UnloadResult 是 C-3.2 的事
- **不**改 mlx_lm_subprocess_backend 的 unload——subprocess 通过 process
  exit 已经获得真实回收；它不需要 actuator
- **不**改 capability matrix
- **不**改 server.py 或 D-x 文件
- **不**改 cache_manager 或 cache_manager 的 release wiring（C-1.2 已
  完成）
- **不**新增 actuator 方法或修改 actuator 实现

## 守则提醒

- **evidence-language calibration**：写 "actuator wired; mlx.clear_cache
  fires on every successful unload when mlx.core is importable"，不写
  "memory governance complete" / "production-ready"
- **staging discipline**：本轮 staged 仅含
  - `M  owlmlx/runtime/mlx_native_backend.py`
  - `??  tests/test_mlx_native_backend_memory_actuator_release.py`
  - `??  files/execution-prompts/owlmlx/owlmlx-memory-actuator-wiring-into-native-unload.md`
  - `??  files/execution-prompts/owlmlx/coordinator-checkpoint-memory-actuator-wired-into-native-unload.md`
  共 4 文件
- **顺序约束**：actuator 必须在 `_release_active_cache(session)` 之后、
  在 `freed_gb` 计算之后调用——cache release 先于 actuator clear，避免
  在 cache 仍持有引用时清 allocator
- **跑全套测试** verify regression 100%+ pass（106 passed + 3 skipped
  期望）

## 第一组命令

```bash
# 现有 unload body
grep -nA20 "def unload" owlmlx/runtime/mlx_native_backend.py | head -30

# memory_actuator API
grep -nE "def release_single_model|def __init__" owlmlx/memory_actuator.py
```

## 交付格式

1. `mlx_native_backend.py` 四处增量 diff
2. `tests/test_mlx_native_backend_memory_actuator_release.py` 全文
3. checkpoint
4. focused regression 结果

## 下一轮候选（不在此轮范围）

- **C-3.2** measured-freed-bytes 进 UnloadResult：把 receipt 的
  `active_memory_before/after` 暴露到 UnloadResult 让 caller 能区分
  measured vs declared freed memory
- **C-3.3** allocator floor configuration wiring——在 backend init 时
  调 `actuator.configure_allocator_floor(...)` 设 `mx.set_cache_limit`
  避免 cache pool 无限增长
- **C-1.3** session field deprecation（cosmetic）
- **D-3 / D-4** server.py 上的剩余 hardening（与本轮独立）
- **C-2.1** repeatability harness real implementation（杠杆最大但
  最重）
