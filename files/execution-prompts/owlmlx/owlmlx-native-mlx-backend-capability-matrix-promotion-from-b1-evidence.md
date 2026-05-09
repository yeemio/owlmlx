# owlmlx Native MLX Backend — Capability Matrix Promotion from B-1 Evidence (B-1.1)

## 你是谁

你是 `owlmlx` 这一轮的执行者。这是 redirected main line 的第五轮，也是 **第一次正式动 capability matrix 行状态字段**。本轮基于上一轮 B-1
（`coordinator-checkpoint-native-mlx-backend-local-candidate-real-load-admissible.md`）
产出的 declared-provenance real-candidate evidence，按 capability matrix
§1a "Promotion Gate" 的硬条款，对若干 native 行从 `experimental` 升 `partial`。

**不是落地轮，是判定轮**。本轮没有 runtime 代码改动、没有新测试、没有
模型操作。产物是 capability matrix 的最小切口编辑 + 本轮 checkpoint。

## 这一轮的边界

- **零 runtime 改动**——`owlmlx/runtime/mlx_native_backend.py` 不动
- **零模型操作**——不 load、不 stream、不下载、不转换
- **零新测试**——不增加 / 不修改任何 `tests/`
- **零环境改动**——`pyproject.toml`、`uv.lock`、`.python-version`、
  `conftest.py` 不动
- **不动 phase45**——active seam / sentinel chain 不动
- **不动 admissibility doc**——B-1 已写好的 §3 行 + §3.2 notes 是本轮
  evidence 来源，本轮不再编辑它
- **不动 input contract / conversion ownership**——这两份在
  `d1f5130` 已 frozen，本轮不再编辑
- **每行促升必须独立走 §1a 四条 gate**——任何一条不满足就拒绝促升，
  即便上一行已经促升

## §1a Promotion Gate 复述（不要照抄，按下面四条逐行 walkthrough）

每个候选行须同时满足：

1. 实证候选已在 `native-mlx-backend-local-candidate-admissibility.md`
   §3 中列名，且 verdict 已是 `admissible`
2. provenance 在促升轮的 checkpoint 中可被 cite（HF revision SHA 等）
3. 促升轮的 row Notes 列必须更新，写进 load+lifecycle 证据 + 测试文件
   或脚本引用
4. 不依赖 runtime 不可区分的 quantization 子分类（4bit-DWQ vs affine
   4bit 是同一证据点，不能拆两次促升）

## 候选行（按本轮预期）

下列各行从 §3 现状，按 B-1 evidence 评估是否满足 §1a：

| Row | Current | Proposed | Justification basis |
|---|---|---|---|
| In-process model handle | `experimental` | `partial` | B-1 真实 load 返回 `mlx_lm.models.qwen3_5_moe.Model` 实例 |
| In-process tokenizer handle | `experimental` | `partial` | B-1 真实 load 返回 `mlx_lm.tokenizer_utils.TokenizerWrapper` 实例 |
| Token-level `decode_step` iterator | `experimental` | `partial` | B-1 真实 `mlx_lm.stream_generate` 在该候选上 yield 8 chunks |
| Per-step finish-reason inspection | `experimental` | `partial` | B-1 chunks 携带 `finish_reason` 字段（`None` for in-progress, terminal value at last chunk） |

**显式不促升的行**（必须在 checkpoint 中说明拒绝理由）：

| Row | Why not |
|---|---|
| KV cache handle (`make_prompt_cache`) | 当前 `partial`；升 `supported` 要 adapter 自身的 `_make_fresh_prompt_cache` 绑定真实命中——B-1 smoke 直接跑 mlx_lm，**未穿过 adapter**。这要 B-1.2 |
| Sampler injection | 当前 `experimental`；B-1 用了**默认** sampler，没 inject `make_sampler`，无新证据 |
| Speculative drafter slot | 当前 `experimental`；B-1 不涉及 draft model |
| Scheduler admission hook | 当前 `partial`；B-1 单请求，未触发 admission 排队 |
| In-process model residency / pinning | 当前 `experimental`；session 在 smoke 期间持有 model 是必然现象，不构成"pinning capability" 的额外证据 |
| Cooperative token-level cancellation | 当前 `partial`；B-1 走完了 max_tokens=8，未中途取消 |
| Logits hook | 当前 `partial`；B-1 chunks 带 `logprobs` 数组，但这是 `mlx_lm` 默认输出，不是 owlmlx 的 logits hook 实现 |
| Prefill / decode separation | 当前 `partial`；B-1 不把 prefill 和 decode 分开调用 |
| Structured output / multi-stream / KV reuse | 当前 `not_in_scope`；本轮无新证据，不动 |

## 这一轮**要**输出的产物

### Edit 1：capability matrix §3 表

文件：`docs/source-of-truth/native-mlx-backend-capability-matrix.md`

对上面 4 个候选行，最小切口编辑：
- Native MLX backend 列：`experimental` → `partial`
- Notes 列：保留原文，**追加**一句 B-1 evidence 引用：
  例如 `B-1 (2026-05-08) confirmed real `mlx_lm` returns `Model` object on Qwen3.6-35B-A3B candidate (admissibility §3 row, provenance: HF Qwen/Qwen3.6-35B-A3B@53c43178).`
- 不动 Subprocess backend 列、不动其他 row

### Edit 2：matrix §3b 增节

紧跟 §3a 之后，新增 **§3b "Promotion-Gate-Compliant Rows from B-1.1"**，
按 §1a 四条 gate 逐行展示证据。这是 promotion 的可审计痕迹，未来 reviewer
可以走这条节省时间。

每行写：
- row name
- gate 1 satisfied: cite admissibility row
- gate 2 satisfied: cite provenance line（commit SHA + HF repo）
- gate 3 satisfied: 哪个 Notes 列被更新了
- gate 4 satisfied: 证据是否依赖 runtime-indistinguishable quantization
  子分类（本批均不依赖）

### Edit 3：matrix header `Updated`

`Updated: 2026-05-08`（保持，因 d1f5130 已是 2026-05-08；如再改一次记
日期 + 短理由）

### Edit 4：checkpoint

文件：
`files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-capability-matrix-promotion-from-b1-evidence.md`

包含：
1. Verdict（一行）
2. 哪 4 行被促升（before / after）
3. 哪些行被显式拒绝促升（with reasons）
4. §1a 四条 gate 对每行的满足情况
5. provenance line 引用
6. 不动了什么
7. 下一轮候选

## 守则提醒

- **evidence-language calibration**：写"Notes 列扩展为 ... evidence"，
  不写"row is now supported"。`partial` 是当前促升上限
- **staging discipline**：本轮 staged 仅含 capability matrix 的最小切
  口 + checkpoint + 本 prompt 三个文件
- **不**把 4 行的 Notes 列改成"completely new sentence"——保留原句
  ("Real mlx_lm smoke is still pending" 一类的描述要换掉，但其他描述
  保留作为"adapter 自身行为"证据，与 B-1 的"upstream 行为"证据并列)
- **不预设结论**：如果 walkthrough 中发现某行其实不满足 gate（例如
  finish_reason 实际是 None 没有 terminal value 触发），如实拒绝促升
- **不要顺手促升 KV cache row 到 supported**——本轮硬规则之一

## 第一组命令

```bash
# 复核 B-1 evidence 在 admissibility doc 中可被 cite
grep -nA5 "admissible.*B-1" docs/source-of-truth/native-mlx-backend-local-candidate-admissibility.md | head -20

# 当前 matrix native 列 experimental 行清单
grep -E "experimental.*partial|experimental.*not_in_scope|experimental " docs/source-of-truth/native-mlx-backend-capability-matrix.md | head
```

## 交付格式

按此顺序输出：

1. capability matrix §3 4 行的 before/after diff
2. capability matrix §3b 全文
3. checkpoint 全文
4. 一句话本轮 verdict

## 下一轮候选

- **B-1.2**（推荐）：把同样 load → stream → unload 通过 `MlxNativeBackend`
  跑一遍（即 set `OWLMLX_NATIVE_SMOKE_MODEL_PATH=/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`
  触发 env-gated `tests/test_mlx_native_backend_real_smoke.py`），产生
  "adapter 真实 lifecycle on admitted candidate" 证据，可促升 KV cache row
- **B-2**：27B / gemma-4 各自独立的 admissibility round
- **B-3**：sampler injection binding（不依赖 B-1.2）

推荐 B-1.2 first，因为它是唯一打通 adapter 真实大模型路径的轮，会同时
解锁 KV cache promotion + scheduler admission 的真实证据收集。
