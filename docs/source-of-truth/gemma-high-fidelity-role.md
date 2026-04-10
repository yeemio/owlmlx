# Gemma Production Mainline

> Status: working truth
> Updated: 2026-04-10

## 1. Role Change

`gemma-4-31B-it` is no longer a candidate or teacher/reference model.

It is the **production mainline**: the primary model to be fine-tuned and
deployed as the core content production engine.

Target domain: short drama / screen-cut scripts (短剧 / 切屏剧本).

## 2. Training Viability — Verified

Local LoRA fine-tuning has been end-to-end verified on 2026-04-10.

### Environment

| Item | Value |
|------|-------|
| Hardware | Apple M5 Max, 128 GB unified memory, Metal 4 |
| Training stack | `mlx-lm 0.31.2` (MLX native) |
| Python venv | `/Users/yeemio/AI/llm-infra/.venv` (Python 3.10) |
| Model path | `/Users/yeemio/AI/Agent/models/gemma-4-31B-it` |
| Model format | BF16 safetensors, 58 GB on disk |

### Model Spec

| Item | Value |
|------|-------|
| Architecture | `Gemma4ForConditionalGeneration` (gemma4_text) |
| Parameters | 30.7B |
| Layers | 60 (sliding + full attention, pattern 5:1) |
| Hidden size | 5376 |
| Vocab | 262,144 |
| Max context | 262,144 tokens |
| Precision | BF16 |

### LoRA Training Results

| Metric | Value |
|--------|-------|
| LoRA trainable params | 4.09M (0.013%, last 4 layers) |
| Peak memory | 62 GB |
| Memory headroom | 66 GB remaining |
| Training speed | 180–254 tokens/sec |
| Loss trajectory | 10.7 → 6.1 (5 steps, gradient flowing correctly) |
| Adapter output | `adapters.safetensors` saved successfully |

### Key Facts

- `mlx-lm 0.31.2` natively supports `gemma4` / `gemma4_text` (PR #1093, merged 2026-04-04)
- Zero local patches required
- Supports LoRA, DoRA, and full fine-tune via `mlx_lm lora` CLI
- Gradient checkpointing works, essential for memory management
- 128 GB machine has substantial headroom to scale up batch size, sequence length, and number of LoRA layers

## 3. Production Target

Gemma is the production workhorse, not a teacher or reference model.

Primary use case: fine-tune for short drama / screen-cut script generation.

Task heads under consideration:
- Premise generation (one-line hook)
- Scene breakdown (分场大纲)
- Screen-cut dialogue scripts (切屏对白)
- Weak-to-strong rewrite (弱稿重写)
- Style-conditioned generation (genre / character / mood)

### Upstream Data Asset

`/Users/yeemio/AI/Agent/docs/brand/gemini/sub-account/` contains 200+ episodes
of serialized content. This is not ready-made script data, but a high-value
upstream corpus that can be processed into training samples via data engineering
(long-form → premise, scene structure, dialogue, hook extraction).

## 4. Training Stack Decision

**Primary: MLX native (confirmed)**

Reason: M5 Max + 128 GB unified memory is the optimal scenario for MLX.
PyTorch/MPS is a viable fallback but offers no advantage on this hardware.

**Backup: PyTorch + PEFT/TRL**

Available in Agent venv (transformers 5.5, torch 2.11), but not recommended
unless MLX hits an architectural blocker.

## 5. What's Blocked On

Training infrastructure is proven. The following are needed before production
training begins:

1. **owlmlx platform readiness** — training workflow integration, model
   versioning, artifact management
2. **Data format specification** — jsonl schema for each task head
3. **Formal training project directory** — not /tmp, integrated into project
   structure
4. **Evaluation criteria** — quality metrics for script output

## 6. Manifest Update Needed

`manifest.json` entry for `gemma-4-31B-it` should be updated:
- `lifecycle_status`: `preview` → `active`
- `role`: `high_fidelity_teacher_candidate` → `production_finetune_mainline`
- `required`: `false` → `true`

This update is deferred until owlmlx platform sync is complete.
