# Gemma Production Mainline

> Status: **authoritative — production mainline frozen**
> Updated: 2026-04-10
> Frozen by: owlmlx-gemma-training-and-production-mainline Round 5

## 1. Role — Frozen

`gemma-4-31B-it` is the **production mainline model** for the owlmlx training
and serving substrate.

- It is NOT a candidate, experiment, or teacher model
- It is the first model to run end-to-end through the owlmlx training substrate
- It is the first model with a verified LoRA pilot through owlmlx artifact
  registration

Target domain: short drama / screen-cut scripts (短剧 / 切屏剧本).

## 2. Training Viability — Verified And Piloted

### 2.1 Initial Viability (pre-substrate)

Local LoRA fine-tuning was end-to-end verified on 2026-04-10 as a standalone
capability check.

### 2.2 Substrate Pilot (through owlmlx contracts)

The minimal LoRA pilot (Round 4) exercised the full owlmlx training substrate:

| Check | Result |
|-------|--------|
| Training substrate contract compliance | PASS |
| Artifact layout contract compliance | PASS |
| Artifact registration (metadata.json) | PASS |
| Serving feasibility validation | PASS |
| Load verification (adapter re-entry) | PASS |
| Inference delta detection | PASS |

Pilot run ID: `pilot-lora-20260410-01`
Feasibility note: `files/pilot-results/gemma-pilot-lora-20260410-feasibility-note.md`

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

### Pilot Training Results

| Metric | Value |
|--------|-------|
| LoRA trainable params | 4.094M (0.013%, last 4 layers) |
| Peak memory | 61.8 GB |
| Memory headroom | 66 GB remaining |
| Training throughput | 65 tokens/sec (pilot), 180–254 tokens/sec (viability test) |
| Loss trajectory | 10.5 → 6.5 (5 steps) |
| Adapter size | 16 MB |

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

## 4. Training Stack Decision — Frozen

**Primary: MLX native (confirmed)**

Per owlmlx training substrate contract (`training-substrate-contract.md`).

**Backup: PyTorch + PEFT/TRL**

Only if MLX hits an architectural blocker per fallback trigger rules.

## 5. Current Capabilities (can do now)

1. LoRA fine-tuning on gemma-4-31B-it via mlx-lm
2. Artifact saving to owlmlx contract-compliant directory layout
3. Artifact registration with metadata.json via owlmlx.training module
4. Serving feasibility validation via owlmlx.training module
5. Adapter load and inference through mlx_lm.load(adapter_path=...)
6. Sequential model switching (base ↔ tuned, with unload between)

## 6. Current Limitations (cannot do yet)

1. **No production training data** — pilot used 4 synthetic samples
2. **No evaluation framework** — no quality metrics for script output
3. **No data engineering pipeline** — 200+ episode corpus not yet processed
4. **No hot-swap serving** — must unload base to load tuned (62 GB each)
5. **No task-head-specific adapters** — only one undifferentiated pilot exists
6. **No RLHF / DPO / reward modeling** — not in current substrate scope
7. **No multi-adapter routing** — cannot serve different adapters per request
8. **No automated training pipeline** — manual CLI invocation only

## 7. owlcoda Boundary — Defined

`owlcoda` is the downstream consumer of Gemma production mainline outputs.

### 7.1 What owlcoda May Do

- Consume tuned Gemma models for task execution
- Present task-head selection UI (premise, scene, dialogue, etc.)
- Orchestrate human review and rewrite workflows
- Manage content production pipelines
- Route requests to the appropriate tuned adapter

### 7.2 What owlcoda Must NOT Do

- Define training substrate contracts (owlmlx owns these)
- Define artifact layout or naming (owlmlx owns these)
- Override serving feasibility decisions (owlmlx runtime enforces)
- Modify adapter artifacts directly (immutable after training)
- Bypass the owlmlx training-to-serving load path

### 7.3 Boundary Rule

owlcoda consumes what owlmlx produces. It does not reverse-engineer the
training or serving substrate. If owlcoda needs a new capability from the
substrate, it must be requested as an owlmlx contract extension, not built
as owlcoda-private scaffolding.

## 8. What Comes Next (outside this program)

1. **Data engineering** — process 200+ episode corpus into training JSONL
2. **Task head design** — define JSONL schema per task head
3. **Evaluation criteria** — quality metrics for generated scripts
4. **Production training** — real data, proper hyperparameters, systematic runs
5. **Serving integration** — tuned model serving through owlmlx runtime path
6. **owlcoda integration** — task workflow consuming production mainline

## 9. Manifest Update

`manifest.json` entry for `gemma-4-31B-it` should be updated:
- `lifecycle_status`: `preview` → `active`
- `role`: `high_fidelity_teacher_candidate` → `production_finetune_mainline`
- `required`: `false` → `true`

This update should happen when the platform shell is ready to reference the
owlmlx training contracts.
