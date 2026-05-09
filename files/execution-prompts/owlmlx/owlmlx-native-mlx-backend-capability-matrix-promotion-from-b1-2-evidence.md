# owlmlx Native MLX Backend — Capability Matrix Promotion from B-1.2 Evidence (B-1.3)

## 你是谁

你是 `owlmlx` 这一轮的执行者。这是 redirected main line 的第七轮，也是
**第一次在 native MLX backend capability matrix 上产出 `supported` 标签**。

本轮基于 B-1.2 的 declared-provenance real-candidate adapter-routed evidence，
按 §1a Promotion Gate 对 6 个候选行逐条 walkthrough，决定哪些升 `supported`、
哪些维持 `partial` 并写明 decline reason。

**不是落地轮，是判定轮**。零 runtime / 测试 / 环境改动。产物是 matrix
最小切口编辑（含 staleness-sweep）+ §3d 新节 + 本轮 prompt + checkpoint。

## 这一轮的边界

- **零 runtime 改动**——`owlmlx/runtime/` 不动
- **零模型 / 测试 / 环境改动**
- **零 admissibility / input-contract / conversion-ownership 改动**——
  那些已 frozen 在 d1f5130
- **不动 phase45**
- **每行升级独立走 §1a 四条 gate**——不满足就拒绝，写明拒绝理由

## §1a Promotion Gate 复述（按下面四条逐行 walkthrough）

每个候选行须同时满足：

1. 实证候选已在 `native-mlx-backend-local-candidate-admissibility.md`
   §3 中列名，且 verdict 已是 `admissible`
2. provenance 在促升轮 checkpoint 中可被 cite
3. 促升轮的 row Notes 列必须更新
4. 不依赖 runtime 不可区分的 quantization 子分类

**额外按 status legend 的硬约束：**

- `supported` 必须满足 "upstream library exposes the entry point via stable
  public API + native adapter can reach it without patching upstream"
- 任何 owlmlx-自有发明（无 upstream 对应）只能停在 `partial`——这是
  legend 的结构性上限，不是证据问题
- 任何依赖 defensive attribute walk / 版本锁定 / 版本漂移迹象的 entry
  point 也只能停在 `partial`

## 候选行（按本轮预期）

| Row | Current | Proposed | Justification basis |
|---|---|---|---|
| In-process model handle | `partial` | **`supported`** | `mlx_lm.load` 是 top-level stable public API；adapter 调用无 patch；B-1.2 真实 lifecycle 命中 |
| In-process tokenizer handle | `partial` | **`supported`** | `mlx_lm.load` 返回 tuple，tokenizer 是 `mlx_lm.tokenizer_utils.TokenizerWrapper` 公共类型 |
| Token-level `decode_step` iterator | `partial` | **`supported`** | `mlx_lm.stream_generate` 是公共 API，yield `GenerationResponse` 公共 dataclass |
| Per-step finish-reason inspection | `partial` | **`supported`** | `finish_reason` 是 `GenerationResponse` 字段，公共 surface |
| KV cache handle (`make_prompt_cache`) | `partial` | **stay `partial`** | submodule path `mlx_lm.models.cache.*`；adapter 用 defensive `_resolve_make_prompt_cache` attribute walk；description 已显式 version-pin 到 0.31.2——这是 legend `partial` 中"version drift / behavioral gaps"的精确触发点 |
| Scheduler admission hook | `partial` | **stay `partial`** | legend 结构性上限：upstream 没有 multi-request scheduler entry point，owlmlx 自有的 `_TicketedAdmission` 不能用 `supported` 表达。Notes 增 B-1.2 evidence，但 row state 不动 |

## 这一轮**要**输出的产物

### Edit 1：matrix §3 row state（4 升 2 守）

文件：`docs/source-of-truth/native-mlx-backend-capability-matrix.md`

- 4 行 `partial → supported`：In-process model handle、In-process
  tokenizer handle、Token-level `decode_step` iterator、Per-step
  finish-reason inspection
- 2 行保持 `partial`：KV cache handle、Scheduler admission hook
- 所有 6 行 Notes 列：删除 "until B-1.3 walks the `supported` gate"
  这种 stale 短语；replace 为 §3d 引用句

### Edit 2：matrix §3d 新节

紧跟 §3c 之后插入 **§3d "Promotion-Gate-Compliant Promotions (B-1.3 Round)"**。
对每个候选行（4 升 2 守），按 §1a 四条 + legend 结构性约束逐条
walkthrough。包括：

- 每行 4-gate 满足情况
- 每个 promote 的 status legend 验证（"stable public API" + "no patching"）
- 每个 decline 的具体原因（version drift caveat / structural ceiling）
- 显式不在本轮范围的 row（cancellation / sampler / drafter / logits /
  prefill-decode / pinning / structured / multi-stream / KV reuse）

### Edit 3：staleness sweep（**不要忘**）

按 memory 中 `feedback-stale-language-sweep.md` 的纪律，全文 grep
"deferred / pending / cap / scaffold-grade only / fake-stub only /
real-model smoke is still pending / until B-1.3" 等过期框架，逐条
refresh。具体清扫点：

- §1 "every native row below is still scaffold-grade" → 改成"以前
  scaffold-grade，B-1.2/B-1.3 推进了若干行的 evidence-grade"
- §1 "It does not claim that owlmlx itself supports any of these
  capabilities yet" → 软化（`supported` per legend 是 entry-point
  reachable，不是 product-feature-complete；可加澄清句）
- §2 "until lifecycle smoke testing runs under an installed runtime
  extra" → 改成"B-1.2 已激活"
- §5 / §6 / §7 → 同步更新，§7 "Recommended Next Round" 改成 B-4
  / C-x 的真实下一步

### Edit 4：checkpoint

文件：
`files/execution-prompts/owlmlx/coordinator-checkpoint-native-mlx-backend-capability-matrix-promotion-from-b1-2-evidence.md`

包含：
1. Verdict（一行 + 4 升 2 守的简表）
2. 4-gate walkthrough 总结
3. legend 结构性约束（KV cache 的 version-drift / Scheduler 的
   upstream-absent）
4. provenance line cite
5. staleness sweep 命中的具体 §
6. 不动了什么
7. 下一轮候选

## 守则提醒

- **evidence-language calibration**：`supported` 的语义按 legend 严格
  解——"upstream API stable + adapter reaches without patching"，**不是**
  "owlmlx 已经在产品层完成此能力"。Notes 列、§5、§6 都要给这层语义
  留显式澄清空间
- **staging discipline**：本轮 staged 仅含 matrix diff + checkpoint +
  本 prompt 三个文件
- **不**顺手促升 KV cache handle / scheduler admission——legend 约束
  已写明
- **不**降级任何已升 `supported` 的行——legend 也允许它们停在那里
- **不**新增 row 或修改 row 名（matrix 行的 schema 不动，只动 status
  字段和 Notes）
- **不**改动 §3a / §3b / §3c 的历史内容——它们是历史轮的 audit trail
- **必须**做 staleness sweep——这是反"文档内部矛盾"的纪律

## 第一组命令

```bash
# 复核 B-1.2 evidence 在 §3c 中可被 cite
grep -nA3 "B-1.2.*Real Adapter" docs/source-of-truth/native-mlx-backend-capability-matrix.md | head -10

# staleness sweep 候选词
grep -nE "scaffold-grade|until B-1\.3|until.*walks.*gate|smoke is still pending|deferred to B-1" docs/source-of-truth/native-mlx-backend-capability-matrix.md
```

## 交付格式

1. matrix §3 4+2 行的 status / Notes diff
2. matrix §3d 全文
3. staleness sweep 命中点的 before/after diff
4. checkpoint 全文
5. 一句话本轮 verdict

## 下一轮候选（不在此轮范围）

- **B-4** Cooperative cancellation real-stream evidence（专门跑中途取消
  case）
- **B-2** sibling admissibility（27B、gemma-4 各自独立）
- **C-1** cache manager scaffold（动 Line 5）
- **C-2** repeatability harness（动 Line 6）
- **C-3** memory governance actuator（动 Line 3）
- **C-4** serving surface hardening（动 Line 4）

按七条主线评估，B-1.3 之后 B-x 系列的剩余杠杆都很小（cancellation 的
matrix 价值有限，sibling admissibility 是宽度不深度）。真实推进
owlmlx 替代 oMLX verdict 的杠杆在 C-1 / C-2 / C-3 / C-4 上。这一轮的
checkpoint 应明确给出这个判断。
