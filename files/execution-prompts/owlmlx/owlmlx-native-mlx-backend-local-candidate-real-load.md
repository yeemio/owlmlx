# owlmlx Native MLX Backend — Local-Candidate Real Load (B-1)

## 你是谁

你是 `owlmlx` 这一轮的执行者。这是 redirected main line 在
`native-mlx-backend-input-contract-and-local-candidate-admissibility-frozen`
checkpoint 之后的下一步：**用本机已有的真实候选跑一次 `mlx_lm.load()`**，
把候选表里的 verdict 从 `likely-admissible-pending-load` 推进到具体结果
（`admissible` 或某个 `inadmissible-*` 类别），并据此决定是否申报 capability
matrix promotion。

## 这一轮的边界（硬约束）

- **零下载**——不从 HuggingFace 拉任何模型、tokenizer 或权重
- **零转换**——不调用 `mlx_lm.convert`、不调用 `mlx-vlm`、不写任何 weights
- **零代码重写**——`owlmlx/runtime/mlx_native_backend.py` 函数体不动；本轮
  只调用既有 API
- **零 capability promotion**——本轮不会写"`partial → supported`"的状态字
  段变更。promotion 由后续轮根据本轮证据 + Promotion Gate §1a 单独决定
- **单候选**——本轮只验 `/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`，
  不顺手验 27B / gemma-4。它们各自独立成轮
- **二元结果**——load 要么成功（继续做最小烟）要么报错（记录分类后停止），
  不在本轮里做"修改 sanitize 让它过"的诱惑路径

## 候选与依据

候选：`/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`

依据见 `docs/source-of-truth/native-mlx-backend-local-candidate-admissibility.md`
§3：

- `model_type: "qwen3_5_moe"` 命中 `mlx_lm/models/qwen3_5_moe.py`
- bf16，无 `quantization` 块
- 26-shard `model*.safetensors` + index 文件齐
- residual unknown：HF 原版 tensor naming 是否与 `Model.sanitize` 期望
  完全匹配（sanitize 是针对 mlx-vlm-converted 布局写的）

载入选 bf16 全权重（67 GB on disk），需要的物理 RAM headroom 约 70 GB+；
本轮**首先**是资源前置检查，再决定是否真触发 load。如果资源不足，**不要
强行 load**——记为 `pending-resource-blocker`，转去 B-2（mlx-community
artifact 真载）讨论选档（4bit ≈ 17 GB / 6bit ≈ 25 GB / 8bit ≈ 34 GB），
但选档与下载是 B-2 的事，不是本轮。

## 执行步骤

### Step 1：资源前置检查（read-only）

```bash
# 物理 RAM
sysctl hw.memsize | awk '{ printf "physical_ram_gb=%.1f\n", $2/1024/1024/1024 }'

# 当前可用（free + inactive）
vm_stat | head -5

# .venv mlx_lm 版本与 cache 模块就位
.venv/bin/python -c "import mlx_lm; print(mlx_lm.__version__)"
.venv/bin/python -c "from mlx_lm.models.cache import make_prompt_cache; print('ok')"
```

判定规则：
- 物理 RAM ≥ 96 GB 且当前 free ≥ 70 GB → 进入 Step 2
- 物理 RAM 64–96 GB → 进入 Step 2，但 load 调用前必须 `MLX_METAL_DEBUG=0`
  且关闭其他大内存进程；任何 OOM 都直接停止本轮
- 物理 RAM < 64 GB → 不进入 Step 2，记 `pending-resource-blocker`，
  写 checkpoint 后停止

### Step 2：单次 `mlx_lm.load()` 调用

写一个**临时脚本**到 `/tmp/`（不进 git）：

```python
# /tmp/owlmlx_local_candidate_load_attempt.py
import json, os, time, traceback, sys
import mlx_lm

PATH = "/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B"

t0 = time.monotonic()
try:
    model, tokenizer = mlx_lm.load(PATH)
    elapsed = time.monotonic() - t0
    out = {
        "verdict": "load_succeeded",
        "elapsed_s": round(elapsed, 2),
        "model_type": type(model).__name__,
        "tokenizer_type": type(tokenizer).__name__,
    }
except Exception as e:
    out = {
        "verdict": "load_failed",
        "exception_class": type(e).__name__,
        "exception_module": type(e).__module__,
        "message": str(e)[:2000],
        "traceback_tail": traceback.format_exc().splitlines()[-12:],
    }
print(json.dumps(out, indent=2))
```

执行：
```bash
.venv/bin/python /tmp/owlmlx_local_candidate_load_attempt.py 2>&1 | tee /tmp/owlmlx_local_candidate_load_attempt.out
```

**重要**：load 调用是**单次的、阻塞的**。不要在 pytest 内驱动；不要并发；
不要 retry。失败一次就是失败。

### Step 3：失败分类（仅在 Step 2 报错时）

按 exception_class + message 划入下列类别之一，写进 admissibility 表：

| 类别 verdict | 触发特征 |
|---|---|
| `inadmissible-sanitize-shape-mismatch` | `KeyError`/`ValueError` on `experts.gate_up_proj` 或类似的 weight tensor naming |
| `inadmissible-arch-import-error` | `ImportError` / `ModuleNotFoundError` on `mlx_lm.models.qwen3_5_moe` 或其依赖 |
| `inadmissible-config-key-missing` | `KeyError` on 标准 config 字段（如 `hidden_size` / `num_attention_heads` 等） |
| `inadmissible-tokenizer-incompatible` | `tokenizer_utils.load` 路径上的错误 |
| `inadmissible-resource` | `MLX` / `metal` / 内核级 OOM / allocation 失败 |
| `inadmissible-other` | 上述都不命中，写 exception 全文 |

### Step 4：成功分支的最小烟

仅在 Step 2 `load_succeeded` 时执行。**不**追加新测试文件；用同一临时脚
本扩写：

```python
# 续上文
import mlx_lm
prompt = "hello"
gen = mlx_lm.stream_generate(model, tokenizer, prompt, max_tokens=8)
tokens = []
for chunk in gen:
    tokens.append(chunk)
    if len(tokens) >= 8:
        break
print(json.dumps({
    "stream_generate_tokens_observed": len(tokens),
    "first_chunk_repr": repr(tokens[0])[:200] if tokens else None,
}, indent=2))
```

输出与 Step 2 一并 tee 到 `/tmp/owlmlx_local_candidate_load_attempt.out`。

**烟的目的**：确认 model + tokenizer 可以走通一次最小生成，**不是**做
质量评估。max_tokens=8 是上限，不是要求；前 1 token 就有也算成功。

### Step 5：清理

```bash
# 删除临时脚本（不进 git）
rm -f /tmp/owlmlx_local_candidate_load_attempt.py
# 输出文件保留作 checkpoint 的引用证据，commit 时**不要**把 /tmp 的内容
# 进 repo——证据通过 checkpoint 的 inline 节录入 git
```

## 这一轮**要**输出的产物

### Doc 更新（最小切口）

`docs/source-of-truth/native-mlx-backend-local-candidate-admissibility.md`
§3 中 Qwen3.6-35B-A3B 行的 `Admissibility` 列从
`likely-admissible-pending-load` 改成具体 verdict（成功 = `admissible`；
失败 = 上面表格里的对应类别）。§3.2 的 Per-Candidate Notes 增补：

- 实际 load 时间（秒）
- exception 全文（仅失败时）
- provenance line（成功时）：mirror of upstream HF repo + revision（如能
  从本地 README / hash 对应到 HF revision；不能则记 `unverified-mirror`
  并明确这阻塞 §4.1 first-class 提级）

### Capability Matrix 不动

§3 行状态、§3a 行不修改。任何 promotion 由独立轮做，本轮只产出"是否够
资格申报 promotion"的判定，不申报本身。

### Checkpoint

写 `files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-local-candidate-real-load.md`
（成功 / 失败两种命名后缀都可以选；失败时建议
`...-blocked-<verdict>.md`，成功时建议 `...-admissible.md`）

包含：
1. Verdict（一行结论）
2. 资源前置检查的实际数字
3. Step 2 的 JSON 输出 inline
4. 如成功：Step 4 的 token 观察 inline
5. 如失败：分类 verdict + 下一轮候选（B-2 / sanitize 分析独立轮 / 等）
6. provenance line（成功时）
7. 不动了什么（capability matrix / runtime code / pyproject / etc.）

## 守则提醒

- **evidence-language calibration**：不要写"loaded successfully"；写
  "load returned without exception" + 实测 elapsed。不要写"this proves
  the candidate is admissible"；写"verdict advanced from
  likely-admissible-pending-load to admissible per §3.1 vocabulary"。
- **staging discipline**：本轮 staged 文件应只包括 admissibility doc 的
  这一行修改 + checkpoint + 本 prompt。不要顺手 stage 工作区里的旁支
  dirty 文件
- **失败不是失败**：load_failed 是合法且有价值的本轮结果，写 checkpoint
  时不必把它包装成"几乎成功"。失败的 exception 全文是 B-2 是否可以预先
  规避同类问题的关键证据
- **资源 blocker 不丢面子**：如果 Step 1 判定不进 Step 2，照实记录、推
  到 B-2。不为了"跑出结果"在不安全的资源条件下硬上
- **不动 prior 已 committed 文档**：input-contract / conversion-path /
  promotion gate / matrix 行状态全部保持 `d1f5130` 时的形态
- **不增加测试文件**：`tests/test_mlx_native_backend_real_smoke.py` 仍
  保持 env-gated；本轮的 load 不通过 pytest，通过临时脚本，证据落进
  checkpoint 即可

## 第一组命令

```bash
# 资源前置检查
sysctl hw.memsize | awk '{ printf "physical_ram_gb=%.1f\n", $2/1024/1024/1024 }'
vm_stat | head -5
df -h /Users/yeemio/AI/Agent/models | tail -1

# 候选体量复核
du -sh /Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B

# mlx_lm 就位复核
.venv/bin/python -c "import mlx_lm; print(mlx_lm.__version__, mlx_lm.__file__)"
```

## 下一轮候选（不在此轮范围）

- **如果本轮 admissible**：B-1.1 = capability matrix promotion 申报轮（专
  门走 Promotion Gate §1a 流程），把哪些行从 `partial → supported` 列
  出、绑定 provenance line、更新 §3a "Verified Rows in This Round"
- **如果本轮 inadmissible-sanitize-***：B-2 = mlx-community artifact 真
  载（preferred fallback per §3.2 upgrade path），需要下载——这是下载授
  权的合法时刻
- **如果本轮 inadmissible-arch-***：B-3 = 上游 mlx_lm issue / wait-for-
  upstream，不在 owlmlx 范围内
- **如果本轮 pending-resource-blocker**：直接转 B-2 选小档（4bit / 6bit）
  讨论
