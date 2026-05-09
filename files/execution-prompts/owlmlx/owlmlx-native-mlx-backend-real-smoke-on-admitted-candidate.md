# owlmlx Native MLX Backend — Real Adapter Smoke on Admitted Candidate (B-1.2)

## 你是谁

你是 `owlmlx` 这一轮的执行者。这是 redirected main line 的第六轮：第一次
让 `MlxNativeBackend` 对真实候选跑完整 lifecycle，并把"adapter 自身在真
实大模型上是否兑现 §3 描述"这件事变成可被引用的硬证据。

**这一轮是 evidence-collection 轮，不是 promotion 轮**。row state 字段
留给 B-1.3 独立走 §1a Promotion Gate；本轮只产出 test 运行结果与 §3c
新节，不改任何 row 的 `partial` / `experimental` / `not_in_scope`。

## 这一轮的边界

- **零 runtime 改动**——`owlmlx/runtime/mlx_native_backend.py` 不动
- **零新测试**——只触发既有 env-gated
  `tests/test_mlx_native_backend_real_smoke.py`；不改它，不增加 case
- **零模型操作**——既有候选 `Qwen3.6-35B-A3B` 已 admitted，无需下载或
  转换
- **零环境改动**——`pyproject.toml`、`uv.lock`、`.python-version`、
  `conftest.py` 不动
- **零 row state 编辑**——§3 现状保持本轮起点，无 row 在本轮被升级
  （包括 KV cache handle 仍是 `partial`，由 B-1.3 决定是否升 `supported`）
- **不动 §3a / §3b**——它们记录的是历史轮证据
- **不动 admissibility doc**——B-1 已写完
- **不动 phase45**——active seam / sentinel chain 不动

## 候选与依据

候选：`/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`（B-1 admitted，
provenance HF `Qwen/Qwen3.6-35B-A3B@53c43178507d69762986fbfa314f6e8d4d859409`）

测试入口：既有 `tests/test_mlx_native_backend_real_smoke.py`，两 case
（`test_real_model_lifecycle_load_stream_unload` +
`test_real_model_two_streams_serialize_under_admission`），由
`OWLMLX_NATIVE_SMOKE_MODEL_PATH` env 触发。

## 资源前置（同 B-1）

- 物理 RAM ≥ 96 GB **且** 当前 free + reclaimable ≥ 70 GB → 进入 Step 2
- 否则按 B-1 prompt 的处置：识别占 RAM 的进程，操作员决定是否释放，或
  转 `pending-resource-blocker`
- 注意：`omlx.cli serve` 由 Platform Bootstrap Supervisor（uvicorn at
  `127.0.0.1:3011`，跑在 `supervisor` tmux session）自动重启。本轮**不
  必再次 SIGTERM** 它，**只要它的 RSS 处于 idle（≤ 200 MB）**——supervisor
  会立刻把它再拉起来，本轮的 67 GB 工作集与 idle 的 oMLX 不冲突
- 若 oMLX 已 load 模型（RSS 数十 GB），照 B-1 的方式与操作员协商

## 执行步骤

```bash
# Step 1: 资源
vm_stat | head -5
pgrep -af "omlx.cli serve" | head

# Step 2: env-gated smoke
OWLMLX_NATIVE_SMOKE_MODEL_PATH=/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B \
OWLMLX_NATIVE_SMOKE_MAX_TOKENS=8 \
caffeinate -i .venv/bin/python -m pytest \
  tests/test_mlx_native_backend_real_smoke.py -v -s \
  2>&1 | tee /tmp/owlmlx_b12_smoke.out
```

## 这一轮**要**输出的产物

### Edit 1：capability matrix §3c 新节

文件：`docs/source-of-truth/native-mlx-backend-capability-matrix.md`

紧接 §3b 之后插入 §3c "B-1.2 Real Adapter Lifecycle Evidence"，记录：

- 测试驱动：`OWLMLX_NATIVE_SMOKE_MODEL_PATH=<本地路径>`
- 候选 + provenance（cite admissibility §3）
- 两 case 的实测数字（load / stream / completion_tokens / events /
  finish_reason / 并发 admission snapshot）
- 这些证据将在 B-1.3 中被用于哪些 row 的促升候选（KV cache handle、
  Scheduler admission hook、In-process model/tokenizer handle、
  decode_step iterator、per-step finish_reason 都成为 partial→supported
  候选；Cooperative cancellation 不在候选内，因 B-1.2 未触发取消路径）
- 明确"§3 row state 在本轮不动"

**不**修改 §3 row state、Notes 列或既有 §3a / §3b。

### Edit 2：matrix header `Updated:` 日期

如本轮日期不同于 d1f5130 提交日期，更新；同日则保持。

### Edit 3：checkpoint

文件：
`files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-real-smoke-on-admitted-candidate.md`

包含：
1. Verdict
2. Step 1 资源数字 + Supervisor 自动重启的处置
3. Step 2 完整 pytest 输出 + 关键断言命中
4. KV cache binding 三条断言（status / count / cross_request_reuse）
5. 并发 admission 三条断言（max_observed_concurrency / next_ticket /
   serving / in_critical_section）
6. provenance line
7. 不动了什么（特别是 §3 row state）
8. 下一轮候选（B-1.3 = promotion-walkthrough）

## 守则提醒

- **evidence-language calibration**：写 "test passed"，不写 "row is
  supported"。row 是否 supported 由 B-1.3 走 §1a Gate 决定
- **staging discipline**：本轮 staged 仅含 §3c diff + checkpoint + 本
  prompt（如果之前未写）
- **不**顺手促升：B-1.2 的存在意义就是把 evidence 与 promotion 分开；
  把它们合并是回到 B-1 之前的"跑通=升级"反污染陷阱
- **不**新增测试 case：既有两 case 已覆盖 lifecycle + 并发 admission；
  cancellation / sampler / drafter / structured 是各自独立轮的事

## 第一组命令

```bash
vm_stat | head -5 | awk 'NR==2{free=$3} NR==4{inactive=$3} NR==5{spec=$3} END {gsub(/\./,"",free); gsub(/\./,"",inactive); gsub(/\./,"",spec); printf "reclaimable_total_gb=%.1f\n", (free+inactive+spec)*16384/1024/1024/1024 }'
pgrep -af "omlx.cli serve"
ls tests/test_mlx_native_backend_real_smoke.py
```

## 下一轮候选（不在此轮范围）

- **B-1.3**（推荐）：用本轮 evidence 走 §1a Promotion Gate，把若干
  partial 升 supported（候选：In-process model/tokenizer handle、
  decode_step iterator、per-step finish_reason、KV cache handle、
  Scheduler admission hook）
- **B-2**：27B / gemma-4 各自独立 admissibility round
- **B-3**：Sampler injection binding（独立轮）
- **B-4**（新）：Cooperative token-level cancellation real-stream evidence
  ——专门跑一次中途取消的 case，因为 B-1.2 没覆盖
