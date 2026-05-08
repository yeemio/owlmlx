# owlmlx Native MLX Backend — Input Contract & Local-Candidate Admissibility (Documentation-Only Round)

## 你是谁

你是 `owlmlx` 这一轮的执行者。**这一轮是 source-of-truth 文档轮，不是能力开发轮**：
没有 runtime 代码改动、没有 capability 促升、没有模型下载、没有转换执行、没
有 pytest 跑 mlx 模型。产物全部是 `docs/source-of-truth/` 下的文档。

这一轮是 redirected main line（native MLX backend）的"反污染地基"——把"什么
权重算合法输入"的契约立起来，避免后续轮被玩具级 4bit smoke 漂亮数据撬动
capability matrix。

## 为什么这一轮存在

上一轮 `coordinator-checkpoint-native-mlx-backend-lifecycle-smoke-and-kv-cache-handle-owned-partial-promoted.md`
把 KV cache handle 行从 `experimental` 升到 `partial`，依据是 real-installed
`mlx_lm 0.31.2` 的 upstream binding。下一步本来候选是 B-1（real-model smoke
on CI lane）和 B-2（sampler injection binding）。

但项目所有者明确指出：

> "我不想拿所谓的冒烟漂亮数据来污染环境。"

如果用一个 sub-2B 的 4bit 玩具去跑 smoke 把 partial 升 supported，证据强度
和真实负载（如本机已有的 Qwen3.6-35B-A3B Transformers 全权重）之间完全脱
钩——这正是"漂亮数据污染"。

正确的反污染策略不是再跑一次更大的 smoke，而是**先立 input contract**，让
matrix 的促升与 real-candidate provenance 绑定，而不是与"跑通了 mlx_lm.load"
绑定。

## 本机已知事实（factual snapshot, 2026-05-08）

- 本机有 `/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`（约 67G，**Transformers
  全权重**，README 声明对 Transformers/vLLM/SGLang/KTransformers 兼容）
- 本机有 `/Users/yeemio/AI/Agent/models/Qwen3.6-27B`（约 52G，同上）
- HuggingFace `mlx-community` 已经发布 Qwen3.6-35B-A3B 的多档 MLX 转换：
  `4bit`、`6bit`、`8bit`、`bf16`、`mxfp4`、`nvfp4`、`4bit-DWQ`，部分 model
  card 写明"converted using mlx-vlm 0.4.4"（暗示可能带 VL 成分，需核实）
- 项目 native backend (`owlmlx/runtime/mlx_native_backend.py`) 当前依赖
  `mlx_lm.load` / `mlx_lm.generate` / `mlx_lm.stream_generate` /
  `mlx_lm.models.cache.make_prompt_cache`
- 项目当前 `pyproject.toml` 声明 `mlx-lm>=0.22.0`；`.venv` 里实装 `mlx_lm 0.31.2`
- owlmlx 身份契约（README）：
  - "what `owlmlx` owns is identity, principles, governance, truth contracts,
    and path semantics — not necessarily every line of execution code"
  - "Not a thin wrapper around vMLX"

## 这一轮**不**做的事（硬规则）

- **不**改 `owlmlx/runtime/mlx_native_backend.py` 任何函数体
- **不**改 phase45 active seam / sentinel chain / capability matrix 的现有行
  （只在 matrix 顶部加 promotion gate 文本，不动行）
- **不**改 `pyproject.toml`、`uv.lock`、`.python-version`、`conftest.py`
- **不**下载任何模型（含 mlx-community 的 4bit、bf16、任意档）
- **不**执行 `mlx_lm.convert` 或 `mlx_lm.load`
- **不**跑任何 mlx 相关 pytest（`tests/test_mlx_native_backend_real_*.py`
  保持原有 skip 行为）
- **不**重写 mlx_lm 的转换内核——owlmlx 不是 mlx-lm 的影子重实现
- **不**预设结论：如果 (a) 调研发现 mlx_lm 对某档 quantization 不是 first-class，
  如实写 `not_in_scope`，不为了好看放进 supported 列

## 这一轮**要**输出的产物

落到 `docs/source-of-truth/`，**只写文档**：

### (a) Native Backend Input Contract

**文件**：`docs/source-of-truth/native-mlx-backend-input-contract.md`

读 `.venv/lib/python3.11/site-packages/mlx_lm/utils.py` 的 `load()` 源码，
回答下列问题，每个回答带文件路径 + 行号 + 代码节选：

1. **接受形态**：`load()` 接受 HF repo id 还是本地路径？两者解析路径分别
   是什么？`utils.load_model` / `utils.load_config` 期望磁盘上有什么文件
   （`config.json` 的字段、`*.safetensors` 布局、tokenizer 文件、是否需要
   `model.safetensors.index.json`）？
2. **Quantization 谱系 first-class 状态**：对照 mlx_lm 0.31.2 的 quantize
   / dequantize 路径，逐项判定 `4bit / 6bit / 8bit / bf16 / mxfp4 / nvfp4 /
   4bit-DWQ` 中哪些是 first-class（`mlx_lm.load` 直接识别 `config.json` 中的
   `quantization` 字段并应用），哪些不是。`mxfp4 / nvfp4` 是较新的 micro-scaled
   FP 格式，DWQ 是 dynamic-weight-quantization——这两类要看是否在 mlx_lm 当前
   版本的 quantize map 里。
3. **mlx-vlm 转换 artifact 与 mlx_lm.load 的兼容性**：mlx-community 部分卡
   写明"converted using mlx-vlm"。读 `config.json` 字段差异（`model_type`、
   `architectures`、`vision_config`），判定 mlx-vlm 产物是否能被 `mlx_lm.load`
   作为纯文本 LM 加载，还是必须走 `mlx_vlm.load`。
4. **Architecture 注册表**：`mlx_lm` 内部对 `model_type` 的 dispatch（通常是
   `mlx_lm.models.<arch>`）。Qwen3.6 / Qwen3 MoE 是否有对应 `.py`？

**形式约束**：每个 claim 必须带 `path:line` 引用；不能引用得到的部分明
确写"未能在源码中确认"。

### (b) Local-Candidate Admissibility

**文件**：`docs/source-of-truth/native-mlx-backend-local-candidate-admissibility.md`

对本机 `/Users/yeemio/AI/Agent/models/` 下所有 owlmlx 目标范围模型，逐个判
定 admissibility：

| Model Path | Format | mlx_lm.load 直入? | 缺什么 | 状态 |
|---|---|---|---|---|
| Qwen3.6-35B-A3B | Transformers 全权重 | ? | ? | ? |
| Qwen3.6-27B | Transformers 全权重 | ? | ? | ? |

具体要做的：
- `ls -1 /Users/yeemio/AI/Agent/models/` 列全本机模型清单
- 对每个目录读 `config.json` 头部（不读权重），判定 model format
- 对照 (a) 的 input contract 写"是否可直入 native backend"判定
- 不可直入的，写明缺什么（mlx-format conversion / 走 mlx-vlm / 上游
  arch.py 不存在，等等）
- 给每行附"upgrade path"——例如 "needs `mlx-community/Qwen3.6-35B-A3B-bf16`
  本地 cache" 或 "wait for mlx-community DWQ artifact"

明确这一轮**不**触发任何 upgrade path——只列出来。

### (c) Capability Matrix 反污染条款

**文件**：在 `docs/source-of-truth/native-mlx-backend-capability-matrix.md`
顶部（紧接 status legend 之后）插入一节 **"Promotion Gate"**：

文字大意（请按文档现有语气重写，不要照抄）：

> Native rows are promoted from `partial` to `supported` only on **declared-
> provenance real-candidate evidence**. Toy-grade smoke runs (sub-2B 4bit
> models executed with no provenance trail) do **not** qualify, even if all
> assertions pass. Provenance must be declared in the promoting round's
> checkpoint and link to a row in `native-mlx-backend-local-candidate-
> admissibility.md`.

**不**动现有任何行的状态字段。

### (d) Conversion Path Ownership

**文件**：`docs/source-of-truth/native-mlx-backend-conversion-path-ownership.md`

明确分层：

- **执行层（borrow）**：owlmlx 不实现 weights → MLX 转换的内核，借用
  `mlx_lm.convert` / `mlx-vlm` / mlx-community 已发布 artifact
- **路径层（own）**：owlmlx 拥有 conversion path semantics——
  - 哪些 provenance 的 artifact 算合格输入
    （e.g. `mlx-community/*` 官方转换 = 合格；`unsloth/*-MLX-*` 第三方 = 合格
    但需在 admissibility 表里单独标注；自行 `mlx_lm.convert` 产出 = 合格但
    必须记录 convert 命令与 mlx_lm 版本；`mlx-vlm` 产出 = 待 (a) 判定）
  - artifact 在本机的存储约定（`~/.cache/huggingface/hub/` 由 HF 默认管理，
    owlmlx 不另立目录）
  - capability matrix 促升时的 provenance 记录格式（commit message /
    checkpoint doc 中的 provenance line）
- **不属于这一轮**：是否真的为 Qwen3.6-35B-A3B 触发一次转换。这一轮只立
  契约，不执行。

### (e)（可选）更新 README "Document Map"

将上述 4 份新文档加入 `README.md` 的 Document Map 列表（README:62-78 段）。
**只加文件路径**，不写 narrative。

## 守则提醒

- 这是文档轮，不是落地轮——任何"为了未来某轮方便"在 runtime 代码、
  pyproject、conftest 里做的预先改动都禁止
- (a) 的所有 quantization first-class 判定必须有 mlx_lm 源码 path:line
  引用；不能引用清楚的部分如实写"未确认"
- (b) 不预设结论："Qwen3.6-35B-A3B Transformers 不可直入"是高概率结论但
  必须由 (a) 的 input contract 推出，不能拍脑袋写
- (c) 不动任何现有行，只加 promotion gate 文本——任何对现有行的状态
  调整属于另一轮
- (d) 不写"未来 owlmlx 自己实现 convert 的路线图"——owlmlx 不重写
  mlx_lm.convert，这是 README 身份契约
- 全部产物文档均不动 phase45 active seam / sentinel chain / 主线 capability
  rows / native backend adapter

## 第一组命令

```bash
# 1. native backend 当前依赖入口
.venv/bin/python -c "import mlx_lm; print(mlx_lm.__version__, mlx_lm.__file__)"

# 2. mlx_lm 源码定位
ls -1 .venv/lib/python3.11/site-packages/mlx_lm/

# 3. quantization 路径
grep -rn "quantization" .venv/lib/python3.11/site-packages/mlx_lm/utils.py | head -20
grep -rn "mxfp4\|nvfp4\|dwq" .venv/lib/python3.11/site-packages/mlx_lm/ | head -20

# 4. architecture 注册表
ls -1 .venv/lib/python3.11/site-packages/mlx_lm/models/ | head -40

# 5. 本机模型清单（read-only）
ls -1 /Users/yeemio/AI/Agent/models/

# 6. 任一本机模型 config.json 头部
ls -1 /Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B/ 2>/dev/null | head
head -30 /Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B/config.json 2>/dev/null
```

## 交付格式

按此顺序输出：

1. (a) `docs/source-of-truth/native-mlx-backend-input-contract.md`
2. (b) `docs/source-of-truth/native-mlx-backend-local-candidate-admissibility.md`
3. (c) `docs/source-of-truth/native-mlx-backend-capability-matrix.md` 仅
   "Promotion Gate" 节插入的 diff（不改任何行的状态）
4. (d) `docs/source-of-truth/native-mlx-backend-conversion-path-ownership.md`
5. (e) `README.md` Document Map 段的 diff（仅追加 4 行）
6. 一份本轮 checkpoint：
   `files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-input-contract-and-local-candidate-admissibility-frozen.md`
   记录：什么文档落地、capability matrix 哪些行被动了（应只有 promotion
   gate 节的新增）、什么没落地、下一轮候选

## 下一轮候选（不在此轮范围）

留给主线决策，不预定：

- **B-3a**：把 Qwen3.6-35B-A3B-bf16（或 4bit）通过 `huggingface-cli download`
  拉到本机 cache，记录 provenance，然后用 native backend 跑 real-candidate
  smoke——这是带 provenance 的促升路径
- **B-3b**：放弃促升，转回 B-2（sampler injection binding）扩面而不促升
- **B-3c**：在 owlmlx 内部立一个 `provenance-registry`（structured YAML
  list of admitted artifacts），把 (b) 的表升级为机读

## 这一轮的反污染本质

把"matrix 促升=跑通"换成"matrix 促升=有 declared provenance 的 real
candidate 跑通"。这不是延迟工作，是修地基——没有这个 gate，后续每一次
smoke 都在赌"是否被当作真实证据"，而仲裁权在记忆，不在文档。这一轮把仲
裁权写进 source-of-truth。
