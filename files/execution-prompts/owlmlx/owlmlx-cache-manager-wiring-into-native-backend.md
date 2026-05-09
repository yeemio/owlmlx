# owlmlx Cache Manager Wiring into Native MLX Backend (C-1.1)

## 你是谁

你是 `owlmlx` 这一轮的执行者。这是 C-1 cache_manager scaffold 之后的第一
条 wiring round——把 scaffold 真正接入 production runtime path
（`MlxNativeBackend`），让 `cache_manager` 从"独立 ownership domain"
变成"native backend 的 KV cache 实际经手者"。

**不是新增能力，不是促升 capability matrix，是 refactor。** 行为应与
C-1 之前完全一致：fresh per-request cache、单请求语义、零跨请求复用。
区别只在 *谁负责*：原来 `_make_fresh_prompt_cache` 内联调用
`make_prompt_cache`；现在它委托给 `CacheManager`。

## 这一轮的边界

- **零新能力**——cache_manager 仍是 scaffold，无 eviction、无 reuse、无
  prefix lookup
- **零新测试场景**——只更新既有测试以匹配新的 API；不增加 capability
  断言
- **零 capability matrix 改动**——`docs/source-of-truth/native-mlx-backend-capability-matrix.md`
  不动；wiring 不构成 promotion 证据
- **零环境改动**——`pyproject.toml` 等不动
- **零 admissibility / input-contract / conversion-ownership 改动**
- **零 phase45 改动**

## 为什么这一轮存在

C-1 把 `cache_manager.py` 立成独立 ownership domain（committed in 808dd99），
checkpoint 明确说"NOT yet bound into MlxNativeBackend; wiring is a follow-
up round." 这就是那个 follow-up round。不 wire 的话，scaffold 永远是
观察对象不是参与者，C-1 的工程价值无法兑现。

wiring 的关键约束：必须保住 23 个 native test + 9 个 cache_manager test
+ B-1.2 env-gated smoke 的 contract——任何 behavior 变化都意味着引入了
新能力（违反"零新能力"边界）。

## 这一轮要做的最小切口

### 编辑 1：`owlmlx/cache_manager.py` API 扩展

`acquire_for_request` 从返回 `CachedRequestHandle` 改成返回
`tuple[CachedRequestHandle, Any]`——同时返回 handle + cache_object。
caller 持 cache_object 强引用；manager 仍不持（单请求语义不变）。

理由：scaffold 设计期为了强调 manager 不持引用，让 caller "拿不到"
cache_object——这在独立 ownership 场景下逻辑自洽，但 wiring 时 caller
（native backend）必须把 cache_object 喂给 `mlx_lm.stream_generate(...,
prompt_cache=cache, ...)`，所以必须能拿到。

### 编辑 2：`tests/test_cache_manager.py` 适配新 API

将所有 `manager.acquire_for_request(...)` 的返回拆包成 `(handle, cache)`。
新增一个 test（`test_acquire_returns_handle_and_cache_object_tuple`）
锁住"cache_object 是 upstream 返回值的同一对象引用"这条契约。

### 编辑 3：`owlmlx/runtime/mlx_native_backend.py` wiring

- 新增 import：`from owlmlx.cache_manager import CacheManager`
- `MlxNativeBackend.__init__` 增加 `self._cache_manager = CacheManager()`
- `_make_fresh_prompt_cache` 函数体改写：先用既有 `_resolve_make_prompt_cache`
  探测 upstream 可达性（None 时静默 skip 保持 defensive contract），
  然后委托给 `self._cache_manager.acquire_for_request(model_id=
  session.info.model_id, mlx_lm_module=mlx_lm_module, model=session.model)`
  拿 `(handle, cache)`，把 cache 镜像到 `session.last_prompt_cache`/
  `session.last_prompt_cache_id` 保 backward compat
- 不删除 `_resolve_make_prompt_cache`（manager 内部也用同样模式，但
  adapter 仍需要它做 None-skip 路径）
- 不删除 `session.last_prompt_cache*` 字段（既有测试读它们）
- handle 不暴露给 session（`del handle`）——session 仍是 backward-compat
  mirror，manager 是 canonical ledger

## 这一轮**不**做的事

- **不**移除 `session.last_prompt_cache*` 字段——既有测试 + 外部观察
  者仍读它们；删除是 C-1.2 的事
- **不**调整 `session.last_prompt_cache_id` 的语义——继续用 `id(cache)`
  Python 内置 id（与 manager 的 monotonic counter 是两个独立的标识符；
  任何"统一"动作是后续轮）
- **不**在 wiring 路径上调用 manager 的 `release_for_request`——
  release 触发点（generator close / unload）需要单独设计；C-1.1 只做
  acquire 接管
- **不**改 capability matrix 任何 row state 或 Notes 列
- **不**触发 env-gated B-1.2 smoke 作为强制证据；`test_mlx_native_backend_real_upstream_binding.py`
  已对 `mlx_lm 0.31.2` 验证 cache 绑定，wiring 是纯 refactor，单元层
  证据足够

## 守则提醒

- **evidence-language calibration**：写 "cache_manager wired"，不写
  "cache_manager production-ready" / "cache eviction enabled"
- **staging discipline**：本轮 staged 仅含
  - `M  owlmlx/cache_manager.py`
  - `M  tests/test_cache_manager.py`
  - `M  owlmlx/runtime/mlx_native_backend.py`
  - `??  files/execution-prompts/owlmlx/owlmlx-cache-manager-wiring-into-native-backend.md`
  - `??  files/execution-prompts/owlmlx/coordinator-checkpoint-cache-manager-wired-into-native-backend.md`
  共 5 文件
- **不**在 wiring 同时做 release 接管、id 统一、字段移除等"顺手"动作
- **跑全套测试** verify 33 个 native + cache_manager 测试维持 pass
- **不**触发 env-gated smoke——如果操作员选择跑，那是 C-1.2 round 的
  promotion 证据收集，不是 C-1.1 的强制条件

## 第一组命令

```bash
# 候选 import 点
grep -nE "^from|^import" owlmlx/runtime/mlx_native_backend.py | head

# 既有 _make_fresh_prompt_cache 调用点
grep -n "_make_fresh_prompt_cache" owlmlx/runtime/mlx_native_backend.py

# session.info.model_id 可达性
grep -nE "session\\.info|info: " owlmlx/runtime/mlx_native_backend.py | head
```

## 交付格式

1. `cache_manager.py` API 扩展 diff
2. `tests/test_cache_manager.py` 适配 + 新增 tuple 契约测试 diff
3. `mlx_native_backend.py` wiring diff（import + __init__ + _make_fresh_prompt_cache）
4. checkpoint 全文
5. 全套 native + cache_manager pytest 结果（必须全 pass）

## 下一轮候选（不在此轮范围）

- **C-1.2** release 接管：让 generator close / unload 触发
  `cache_manager.release_for_request`；session.last_prompt_cache 字段
  逐步退役
- **C-3.1** memory_actuator wiring into native backend.unload（同样
  touch `mlx_native_backend.py`，必须串行 after C-1.1）
- **D-1** RequestIdMiddleware wiring into server.py（独立文件，可并行）
- **D-2** GracefulShutdown wiring into server.py lifespan（同 server.py，
  必须串行 after D-1）
