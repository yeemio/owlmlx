# owlmlx Native MLX Backend — Feasibility / Scaffold Round

## 你是谁

你是 `owlmlx` 主线执行者。

phase45 subprocess-transport sentinel chain 已在当前 packaging paradigm 内**收口**（见
`phase-45-coordinator-checkpoint-subprocess-transport-sentinel-chain-closed.md`）。
当前 active seam 仍冻结在
`backend_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_earlier_earlier_boundary_dependency`，
作为 subprocess-wrap 范式下的 baseline 真值。

主线已切换：cache_scheduler_depth 的下一前置依赖**不再是**继续在 stdout
transport 上切片，而是**脱离 subprocess-wrap 范式，进入 native MLX backend**。

本轮是这个新主线的**第一轮**：feasibility + scaffold，不解锁能力。

## 本轮唯一目标

证明 owlmlx 能在**不替换**现有 subprocess backend 的前提下，并行落一个
**experimental native MLX backend adapter**，并能在进程内拿到完整的
load / generate / stream / unload 生命周期钩子。

最终交付一份 capability matrix，标明 native path 能暴露的未来能力入口。

## 本轮**不**做的事（硬规则）

- **不**替换 `owlmlx/runtime/mlx_lm_subprocess_backend.py`
- **不**改 phase45 active seam（仍冻结在 earlier_earlier_boundary_dependency）
- **不**碰 sentinel chain（不删、不改、不加 rung）
- **不**声明 continuous batching、cache parity、stream interleaving、prefix cache、speculative decoding、KV reuse —— 本轮**只证可行**，能力解封是后续 round
- **不**改 post-claim `max_concurrent=1`、ticketed FIFO、serial safety —— 即便 native path 理论上能放宽，本轮也不放宽
- **不**重开 Gemma MTP / reference comparison / governance / host / heavy-weight
- **不**声明 OpenAI API 兼容、tool calling、vision —— 这是后续 round
- 不写 production-grade 适配；experimental + scaffold 即可
- 不要把实验性 backend 接到任何已发布的 serving 路径
- 不要把这一轮宣称为"已经替换 subprocess"——它是**并行存在**

## 本轮**要**做的事

### 1. 新增 experimental native adapter
路径：`owlmlx/runtime/mlx_native_backend.py`

- 类名：`MlxNativeBackend`
- 与 `MlxLmSubprocessBackend` **接口同构**（同名方法 `load / generate / stream_generate / unload`，同形 dataclass 返回）
- 内部直接 import `mlx_lm`（或 `mlx`）作为库使用，**不**起 subprocess
- 仅支持小模型 / lightweight MLX path（如可加载的最小 mlx_lm 模型）
- 失败要 graceful：load 失败、模型不可用、平台不支持时返回明确 error，不抛裸异常

### 2. 证明进程内生命周期钩子
最少要在 native adapter 上跑通：

- `load(model_id)` → 进程内加载、可拿到 model handle
- `stream_generate(model_id, prompt)` → 逐 token yield，能在 generation step
  之间观察到状态（哪怕只是计数）
- `unload(model_id)` → 释放 model handle、内存可见回收
- 至少一个 sanity test：相同 prompt 两次，第二次延迟应受 model already loaded
  影响（证明 load 真的进了内存，不是每次重启）

### 3. 列出 native path 暴露的能力入口
不要做这些能力，只**证明能拿到**入口。在
`docs/source-of-truth/native-mlx-backend-capability-matrix.md` 里写出每一项的
当前可达性：

| 能力入口 | 状态 |
|---|---|
| KV cache handle | `supported / partial / experimental / not in scope` |
| prefill step hook | 同上 |
| decode step hook | 同上 |
| logits / sampler injection | 同上 |
| scheduler admission hook | 同上 |
| speculative drafter slot | 同上 |
| prefix cache reuse 入口 | 同上 |
| KV cache 跨 request 共享入口 | 同上 |
| in-process model residency / pinning | 同上 |
| token-level cancellation | 同上 |
| structured output / grammar 入口 | 同上 |

每一项要给出：
- 当前在 mlx_lm / mlx 库 API 上**能不能拿到**（直接、间接、或要 fork 才行）
- 如果是 partial / experimental，说明 partial 在哪
- 如果是 not in scope，说明被什么排除（库 API 缺失、需要 patch mlx-lm、需要重写 sampler 等）

这份 matrix 是后续 round 的路标——不是文档练笔。

### 4. 与 subprocess backend 的 baseline 对照
在同一份 matrix 末尾追加：

- 同样的能力入口在 **subprocess backend** 上的状态
- 一句话结论：哪些能力入口 native 能拿到而 subprocess 拿不到（这就是为什么主线要切换的硬证据）

### 5. 测试
新增 `tests/test_mlx_native_backend.py`：

- 加载/卸载 lifecycle 测试
- stream_generate 至少 yield 一个 token 事件再 yield done
- model-already-loaded 路径测试
- 失败路径：不存在的 model_id、不支持的平台 graceful 返回 error
- 不需要跑真大模型 —— 用 fake / minimal MLX path 即可
- 测试不依赖网络、不依赖外部 model download

### 6. 不写 entry script
本轮**不**新增 `scripts/runtime_mlx_native_backend.py`。这是 experimental，
不要给操作员入口。等后续 round 决定提主线再加。

## 最小入口

先对齐这些 surfaces：

1. `/Users/yeemio/AI/gitrep/owlmlx/files/execution-prompts/owlmlx/phase-45-coordinator-checkpoint-subprocess-transport-sentinel-chain-closed.md`
2. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_lm_subprocess_backend.py`（看接口形状，不要改它）
3. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_lm_runner.py`
4. `/Users/yeemio/AI/gitrep/owlmlx/owlmlx/runtime/mlx_environment.py`
5. mlx_lm 上游 API（`generate` / `stream_generate` / `load`）
6. `/Users/yeemio/AI/gitrep/owlmlx/docs/source-of-truth/replacement-grade-stability-gaps.md`

## 第一组命令

```
git status -s
python3 -c "import mlx_lm; print(dir(mlx_lm))"
python3 -c "from mlx_lm import load, generate, stream_generate; print('ok')"
ls owlmlx/runtime/
grep -n "^class \|^def " owlmlx/runtime/mlx_lm_subprocess_backend.py | head -40
```

## 交付格式

请按下面顺序输出：

1. 一句最终结论：`feasible` / `partial` / `not_feasible`
2. native adapter 是否落地（是 / 否 / 部分）
3. 新增/修改的文件清单（明确区分新增 vs 修改）
4. capability matrix 关键结论（哪些入口 supported、哪些 partial、哪些 not in scope）
5. 与 subprocess backend 的能力差对照
6. 实际运行的命令与关键结果（test 通过数量、py_compile、git diff --check）
7. 已知风险 / 后续 round 必须处理的 blocker
8. 下一轮主线建议（如果 feasible：选择 C2 真 batching / C3 prefix cache / 或先做 scheduler admission；如果 partial / not_feasible：blocker 在哪、要不要 fork mlx-lm）

## 守则提醒

- 保持 owlmlx 现有 dirty tree 不动（Gemma MTP probe、runtime monitor、host
  heavy 等旁支不在本轮 scope）
- 只 stage 本轮 scoped 文件：`owlmlx/runtime/mlx_native_backend.py`、
  `tests/test_mlx_native_backend.py`、
  `docs/source-of-truth/native-mlx-backend-capability-matrix.md`、
  `owlmlx/__init__.py`（如果需要 export）
- 如果 mlx_lm API 不允许进程内拿到 KV cache handle / step hook，**如实写
  not in scope 并标明需要的 mlx-lm patch / fork 范围**——不要伪报 partial
- capability matrix 写完后，如果 native vs subprocess 的差**不显著**，明确
  报 `not_feasible` 并停在这一轮——不要硬推后续 round
