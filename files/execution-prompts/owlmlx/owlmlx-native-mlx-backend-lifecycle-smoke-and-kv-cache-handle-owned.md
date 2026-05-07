# owlmlx Native MLX Backend — Lifecycle Smoke + KV Cache Handle Owned

## 你是谁

你是 `owlmlx` 主线执行者。

上一轮（Native MLX Backend Feasibility / Scaffold）已收口为
**`feasible` (scaffold-grade)**，见
`files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-feasibility-scaffold-feasible.md`。

当前主线状态：

- 并行 adapter `owlmlx/runtime/mlx_native_backend.py` 已在场，接口形状对齐
  `MlxLmSubprocessBackend`
- 所有 `mlx_lm` 引用走 deferred import；缺 extra 时 graceful fallback
- capability matrix 在
  `docs/source-of-truth/native-mlx-backend-capability-matrix.md`：没有任何
  native 行被升级到 `supported`；部分行仍是 `experimental` / `partial`，
  部分行仍是 `not_in_scope`
- 14 个 scoped test 在没有 `mlx_lm` 的环境下通过
- phase45 subprocess sentinel chain 仍冻结在
  `earlier_earlier_boundary_dependency`，作为 baseline contract preserved
- 顶层 customer-runtime-evidence label 仍是 `early_formal_runtime`

## 本轮唯一目标

尝试把 capability matrix 上一组 `experimental` 行**靠真证据升级到
`supported`**，并尝试把 KV cache handle 从 "entry-point assumption" 提到
owlmlx-owned 一等属性。做不到就按本 prompt 的 `partial_promoted` /
`blocked` 出口如实收口。

具体三条：

1. CI lane 装上 `pip install -e .[runtime]`（或等价的 wheel 路径），让
   `mlx_lm` 在 native adapter 的 deferred import 路径下真可见
2. 用一个**最小可下载 / 最小可缓存的 mlx_lm 模型**（社区有 1-2B 量化版本可
   用；不要拉大模型；优先离线 fixture / 小 vocab 测试模型）走完整 lifecycle：
   `MlxNativeBackend.load → stream_generate → unload`
3. 把 KV cache handle 从 capability matrix 的"假设"提到 `_NativeSession`
   可观测的一等属性，并加一个**单请求内 cache 使用正确性 harness**（仅
   证：单个生成调用内部的 cache handle 可创建、可传递、不会改变同 seed
   输出；**不**证跨请求复用，也不默认在两个请求之间复用同一个 cache 对象）

## 本轮**不**做的事（硬规则）

- **不**主张 continuous batching / prefix cache reuse across requests / cache
  parity / stream interleaving
- **不**主张 speculative decoding（API 仍在 flux）
- **不**改 `MlxLmSubprocessBackend` 或 phase45 active seam（仍冻结）
- **不**碰 sentinel chain
- **不**改 post-claim `max_concurrent=1`、ticketed FIFO、serial safety
- **不**把 native adapter 接到 production serving path / OpenAI surface
- **不**重开 governance / host / heavy-weight / Gemma MTP / vision
- **不**把 capability matrix 上 `not_in_scope` 行（scheduler admission /
  structured output / multi-stream interleaving）改成别的状态——它们留给后
  续 round
- **不**升级 logits hook / prefill-decode 分离这两个 `partial` 行——本轮
  只升级 KV cache handle 和 lifecycle 路径上能直接证的几行
- 不允许"假升级"：任何从 `experimental` 提到 `supported` 的行必须有可重跑
  的 CI 证据（pytest 通过 + 实模型 lifecycle 输出片段）

## 本轮**要**做的事

### 1. CI lane 准备
- 选定一个能跑 `mlx_lm` 的 Python 版本（mlx-lm wheel 当前优先 3.11/3.12；
  如果项目主用 3.14，要先验证 wheel 是否存在；不存在就 pin CI 到能跑的
  Python，**不**改 owlmlx 自己的 `requires-python`）
- 在 pyproject 或 CI config 里明确这个 native-smoke lane 怎么装
- 加一份 `docs/source-of-truth/native-mlx-backend-ci-lane.md` 说明：哪个
  Python 版本、装法、用哪个 fixture model、跑哪些测试
- 不动现有 CI lane 的 default scope

### 2. 真模型 lifecycle smoke
- 选一个**小且可重复的** mlx_lm 模型（建议：mlx-community 已发布的最小量化
  Qwen / Gemma / Llama 1-2B；4-bit 量化）
- 加一组 `tests/test_mlx_native_backend_real_smoke.py`，用 `pytest.mark`
  或环境变量门控（`OWLMLX_RUN_NATIVE_SMOKE=1` 才跑），默认本地不跑
- 测试覆盖：
  - `load(model_id)` 真返回 `LoadResult.ok=True` 且 `LoadedModelInfo` 字段齐
  - `stream_generate` 至少 yield 一个 `token` 事件再 yield `done`
  - `done` 事件的 `finish_reason` 非 None，`completion_tokens` 非 0
  - `unload` 后 `status().loaded_models` 不再包含该 model_id
  - 失败路径：`model_not_found` 仍走 `model_not_found` error_code（用一个
    显然不存在的 path 验）

### 3. KV cache handle 提一等
- 先检查当前 `mlx_lm` cache API：是否存在 `make_prompt_cache(model)` 或等价
  公共入口，以及 `stream_generate` / `generate` 是否接受外部 cache 参数
- 在 `_NativeSession` 上加可观测字段（例如 `kv_cache: Any = None` 或
  `last_kv_cache: Any = None`），用于保存**当前/最近一次单请求** cache
  handle 的对象身份和调试信息；不要把它解释成跨请求 prefix cache
- 在 `load` 时 init 为 None；在每次 `stream_generate` / `generate` 调用内
  如果上游 API 支持，就创建该请求自己的 prompt cache，并把该 cache handle
  传回 `mlx_lm`
- 如果上游 API 不接受外部传入 cache，**如实写到 capability matrix
  `partial` 注解，并标 blocker 为"upstream make_prompt_cache cannot be
  threaded through public stream_generate / generate surface"**
- 加一个 **single-request cache 使用正确性 harness**：用 fresh cache per
  run，验证 cache-enabled 与 cache-disabled 在同 seed / 同 prompt 下 token
  序列一致，并验证一次生成调用内记录到的 cache handle identity 稳定；
  **不**测跨请求，也不把第二次请求复用第一次请求 cache 当成通过条件

### 4. 把 native path 接到现有 post-claim invariant harness
- 现有 phase45 invariant harness（aggregation active seam、ticketed FIFO、
  serial safety）只跑 subprocess backend；**不要改它们**
- 新加 `tests/test_mlx_native_backend_post_claim_invariants.py`，用 native
  adapter 跑出等价的 invariant：
  - 第二个并发 stream 请求在第一个 stream 完成前**不能**进入 generate
    临界区（serial safety）
  - 多并发请求按 FIFO 顺序消费（ticketed FIFO，至少 2 个请求级别）
  - 这一组测试在 native 上**也必须 pass**——证明 native path 守住 baseline
    contract，没有 silent regression
- 这一步可以用 fake mlx_lm 注入（重点是 native adapter 自己的并发语义，不是
  mlx_lm 的），但不能只靠普通 `threading.Lock` 假装 FIFO：如果当前 native
  adapter 没有 ticketed admission，就实现 adapter-local ticketed FIFO，或
  如实报 blocker / `partial_promoted`

### 5. capability matrix 升级
- 凡是 step 2/3/4 真证过的行，从 `experimental` 升到 `supported`，并在
  注解里追加"verified by `tests/test_mlx_native_backend_real_smoke.py` /
  `test_mlx_native_backend_post_claim_invariants.py`"
- 凡是上游 API 卡死的行（KV cache handle 不能传回、speculative API 不稳定
  等），在注解里**如实标 blocker**，**不**升级
- matrix 里加一个新 section "Verified Rows in This Round"，列出这一轮升
  级的行 + 证据文件路径

### 6. 不动主线 phase45 docs
- `docs/source-of-truth/phase45-*` 系列继续保持当前内容
- `phase-45-coordinator-checkpoint-subprocess-transport-sentinel-chain-closed.md`
  保持原状
- 本轮所有变更只落到 native-mlx 命名空间下

### 7. 交付一份本轮的 coordinator checkpoint
- `files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-lifecycle-smoke-and-kv-cache-handle-owned-{verdict}.md`
- 写明：哪些行升级了、哪些被 blocker 卡死、KV cache handle 是否真 owned、
  native adapter 是否守住 post-claim invariants、下一轮主线建议

## 最小入口

先对齐这些 surfaces：

1. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-feasibility-scaffold-feasible.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/native-mlx-backend-capability-matrix.md`
3. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_native_backend.py`
4. `/Users/yeemio/AI/gitrep/owlmlx/tests/test_mlx_native_backend.py`
5. `/Users/yeemio/AI/gitrep/owlmlx/pyproject.toml`（确认 runtime extra 当前
   pin 的 mlx-lm 版本）
6. mlx-lm 上游 cache API 的当前 surface（`mlx_lm.models.cache` 或等价路径）

## 第一组命令

```
git status -s
python3 -c "import sys; print(sys.version)"
python3 -m pip show mlx-lm 2>&1 | head -5
python3 -c "import mlx_lm; print('mlx_lm at:', mlx_lm.__file__); print([x for x in dir(mlx_lm) if not x.startswith('_')])" 2>&1 | head -10
python3 -c "from mlx_lm.models import cache as _c; print([x for x in dir(_c) if 'cache' in x.lower() or 'prompt' in x.lower()])" 2>&1 | head
python3 -m pytest tests/test_mlx_native_backend.py -q
```

如果 `mlx_lm` 在当前 Python 装不上（例如 wheel 还没出 3.14 的 Python ABI），
**先**把 CI lane 文档（step 1）落实，**然后**在那条 lane 上跑 step 2/3/4，
不要把 native-smoke 测试加入 default test 路径。

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`promoted` / `partial_promoted` / `blocked`
2. CI lane 是否就位（Python 版本、mlx-lm 版本、装法）
3. 真模型 lifecycle smoke 是否通过；用了哪个 fixture model；总耗时
4. KV cache handle 是否提到 `_NativeSession` 一等属性；是否能传回 mlx_lm
   stream_generate；within-request reuse 正确性 harness 是否通过
5. native path 是否守住 post-claim invariants（serial safety / ticketed
   FIFO）；测试通过数
6. capability matrix 升级了哪些行（从 `experimental` → `supported`），
   被 blocker 卡死的行各自的 blocker 一句话
7. 实际新增/修改的文件清单（明确区分新增 vs 修改）
8. 下一轮主线建议：在 KV cache handle owned 的基础上，做哪个？
   候选：
   - prefix cache reuse（across-request）
   - 真 continuous batching scaffold
   - sampler injection / structured output 入口
   - speculative drafter（API 稳定后）
   并给出推荐顺序与依赖

## 守则提醒

- 保持现有 dirty tree 不动（Gemma MTP / runtime monitor / single-host /
  host-heavy / `uv.lock` 等旁支不在本轮 scope）
- 只 stage 本轮 scoped 文件：
  - `owlmlx/runtime/mlx_native_backend.py`（修改）
  - `tests/test_mlx_native_backend.py`（如需补 within-request reuse 测试）
  - `tests/test_mlx_native_backend_real_smoke.py`（新增，门控）
  - `tests/test_mlx_native_backend_post_claim_invariants.py`（新增）
  - `docs/source-of-truth/native-mlx-backend-capability-matrix.md`（修改）
  - `docs/source-of-truth/native-mlx-backend-ci-lane.md`（新增）
  - `files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-lifecycle-smoke-and-kv-cache-handle-owned-{verdict}.md`（新增）
- 不写 `scripts/runtime_*.py` —— native adapter 仍是 experimental，不给操
  作员入口
- 如果上游 API 不允许 KV cache handle 提一等（cache 不能从外部传入
  stream_generate），如实报 `partial_promoted`，**不**强升 matrix 行
- 如果 native-smoke 在所有可用 Python 版本下都装不上 mlx-lm，如实报
  `blocked`，并把 CI lane 文档作为唯一交付，下一轮重排
