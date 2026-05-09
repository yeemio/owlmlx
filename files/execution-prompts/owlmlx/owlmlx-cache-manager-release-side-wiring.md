# owlmlx Cache Manager Release-Side Wiring (C-1.2)

## 你是谁

你是 `owlmlx` 这一轮的执行者。这是 C-1.1 之后的 follow-up：把
`cache_manager.release_for_request(handle)` 真正接入 `MlxNativeBackend`
的 lifecycle 退出点（generate 返回、stream 终止、stream 早闭、unload）。

C-1.1 完成的是 acquire 接管；本轮完成 release 接管。两轮加起来，
acquire-release 配对真实闭环——manager 的 per-model 注册表不再因为
请求结束而残留 handle。

**不是新增能力。** 行为对外仍是 fresh per-request、单请求语义、零跨请求
复用。区别只在 manager 的内部 ledger 现在能反映 acquire-release 配对状态。

## 这一轮的边界

- **零新能力**——cache_manager 仍是 scaffold，无 eviction、无 reuse、无
  prefix lookup
- **零 capability matrix 改动**
- **零 session 字段移除**——`last_prompt_cache*` 字段保持原状（继续作
  backward-compat mirror）；只是新增 `active_cache_handle` 字段承载 release
  目标
- **零环境改动**
- **零 `_release_active_cache` 之外的新方法**——release 路径就是一个
  helper 加三个 finally 注入点
- **零 `cache_manager.release_for_request` 实现修改**——scaffold 已写好
  幂等 release 与不变 counter 的语义；本轮只是开始调用它

## 为什么这一轮存在

C-1.1 checkpoint 明确说"`release_for_request` is not yet called from the
native backend on generator close or unload — that is also C-1.2"。不做
这一轮的话：

- manager 的 `_handles_by_model[model_id]` 注册表会随每次 acquire 单调
  增长（因为永远没有 release）
- 未来的 eviction / residency tracker 一旦扩展上去，会读到一个永远不
  缩小的"假活"列表
- C-1.1 的工程价值（cache_manager 是 canonical ledger）会被这个泄漏抵消

## 这一轮要做的最小切口

### 编辑 1：`owlmlx/runtime/mlx_native_backend.py`

四处增量：

1. **import**：`from owlmlx.cache_manager import CacheManager, CachedRequestHandle`（C-1.1 已 import CacheManager；本轮加 CachedRequestHandle）
2. **`_NativeSession` dataclass**：新增字段
   `active_cache_handle: CachedRequestHandle | None = None`
3. **`_make_fresh_prompt_cache`**：原本 `del handle` 改为
   `session.active_cache_handle = handle`；失败路径同样把字段清回 None
4. **新方法 `_release_active_cache(self, session)`**：幂等地把 handle
   传给 `cache_manager.release_for_request(...)`，然后清字段
5. **wiring 三处 finally**：
   - `generate()` 的外层 `try/finally`：在 `self._admission.release()`
     **之前**调 `_release_active_cache(session)`（顺序意义：cache 释放
     在 gate 之内，避免下一个 admission 进入时上一个 handle 还没归还）
   - `stream_generate()` 的外层 `try/finally`：同样模式；Python 保证
     generator 的 `finally` 在 (a) 终端 yield、(b) 异常路径、(c) caller
     提早 close 三种情况下都会触发
   - `unload()`：在丢 session 引用之前调 `_release_active_cache(session)`，
     防止"病态 pending handle"在 unload 时残留

### 编辑 2：新测试文件 `tests/test_mlx_native_backend_cache_release.py`

6 个测试，全部用 fake `mlx_lm` 注入：

- `test_release_fires_after_generate_completion`
- `test_release_fires_after_stream_generate_completion`
- `test_release_fires_on_early_stream_close`
- `test_release_fires_on_unload_with_pending_handle`
- `test_release_idempotent_when_no_active_handle`
- `test_active_cache_handle_set_during_make_fresh_prompt_cache`

观察机制：通过 `backend._cache_manager._handles_by_model` 直接看注册
表是否在 release 后空。`counters().entries` 仍单调（release 不减计数，
scaffold 设计如此）。

### **不**改的部分

- **不**移除 `last_prompt_cache` / `last_prompt_cache_id` /
  `prompt_cache_call_count` 字段——backward-compat mirror 保留；字段
  退役是 C-1.3 的事
- **不**触碰 `cache_manager.release_for_request` 实现
- **不**触碰 `cache_manager.acquire_for_request` 接口
- **不**改既有 23 个 native test + 9 个 cache_manager test 的任何断言
- **不**改 capability matrix 任何 row 或 Notes
- **不**改 D-1 / D-2 / 任何 server.py 文件

## 守则提醒

- **evidence-language calibration**：写 "release wiring landed; acquire-
  release pair closed at lifecycle boundaries"，不写 "cache_manager is
  production-ready" / "eviction enabled"
- **staging discipline**：本轮 staged 仅含
  - `M  owlmlx/runtime/mlx_native_backend.py`
  - `??  tests/test_mlx_native_backend_cache_release.py`
  - `??  files/execution-prompts/owlmlx/owlmlx-cache-manager-release-side-wiring.md`
  - `??  files/execution-prompts/owlmlx/coordinator-checkpoint-cache-manager-release-side-wired.md`
  共 4 文件
- **跑全套测试**：所有 native + cache_manager + 新 release 测试维持
  pass（预期 95 passed + 3 skipped）

## 第一组命令

```bash
# 现有 finally 注入点
grep -nE "finally:" owlmlx/runtime/mlx_native_backend.py

# 现有 acquire 调用点
grep -n "_make_fresh_prompt_cache\|_admission" owlmlx/runtime/mlx_native_backend.py
```

## 交付格式

1. `mlx_native_backend.py` 四处增量 diff
2. `tests/test_mlx_native_backend_cache_release.py` 全文（6 测试）
3. checkpoint
4. 全套 focused regression 结果

## 下一轮候选（不在此轮范围）

- **C-1.3** session 字段退役：把 `last_prompt_cache_id` / `prompt_cache_call_count`
  改成 manager state 的 derived property，或者直接移除 + 更新所有 reader
- **C-3.1** memory_actuator wiring into unload（同样 touch
  `mlx_native_backend.py`，必须串行 after C-1.2）
- **D-3** unified error envelope wiring into server.py（与 D-1 / D-2
  在同 file）
