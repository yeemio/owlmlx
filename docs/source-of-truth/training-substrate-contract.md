# owlmlx Training Substrate Contract

> Status: authoritative
> Updated: 2026-04-10
> Frozen by: owlmlx-gemma-training-and-production-mainline Round 1

## 1. Purpose

This document defines the training substrate that `owlmlx` owns.

`owlmlx` is not just a serving/inference runtime. It also owns the training
environment contract, artifact contract, and training-to-serving bridge for
models that run on its runtime paths.

Training infrastructure that lives outside this contract is scaffolding, not
production truth.

## 2. Scope

The training substrate covers:

1. **Training environment** — hardware, software stack, and venv contract
2. **Training stack selection** — primary and fallback stacks with decision rules
3. **Substrate boundary** — what owlmlx owns vs what the shell / product layer
   owns vs what remains external tooling

The training substrate does NOT cover:

- Artifact layout and naming (see `artifact-layout-contract.md`)
- Training-to-serving bridge (see `training-to-serving-contract.md`)
- Data engineering, dataset schema, or content pipelines
- Model selection or production mainline designation
- Task head design or evaluation criteria

## 3. Training Environment Contract

### 3.1 Hardware Baseline

| Item | Value | Notes |
|------|-------|-------|
| Platform | Apple Silicon | owlmlx's sole target platform |
| Reference machine | M5 Max, 128 GB unified memory, Metal 4 | Current development and training host |
| Memory model | Unified memory (CPU/GPU shared) | MLX's primary advantage on this platform |
| Minimum viable memory | 64 GB | Below this, large-weight model training is not feasible |
| Recommended memory | 128 GB+ | Enables full BF16 weight loading + LoRA + gradient checkpointing with headroom |

### 3.2 Software Environment

| Item | Value | Notes |
|------|-------|-------|
| Python version | 3.10+ | Must match MLX ecosystem compatibility |
| Training venv | `/Users/yeemio/AI/llm-infra/.venv` | Shared infrastructure venv for MLX training tools |
| owlmlx package | importable from training venv | Training scripts may import owlmlx for artifact registration, status, and contracts |

### 3.3 Environment Rules

1. Training MUST run inside the designated training venv, not in ad-hoc
   environments or system Python.
2. The training venv is infrastructure — it is not owned by any single model or
   experiment.
3. owlmlx does not own the venv itself, but it owns the contract that training
   must happen inside a managed venv.
4. Training scripts that bypass the managed venv are scaffolding, not production
   training.

## 4. Training Stack Contract

### 4.1 Primary Stack: MLX Native

| Item | Value |
|------|-------|
| Stack | `mlx-lm` (MLX native LoRA/fine-tune) |
| Minimum version | 0.31.2 |
| Key dependencies | `mlx >= 0.31.1`, `mlx-metal >= 0.31.1` |
| Training CLI | `mlx_lm lora` (LoRA), `mlx_lm full` (full fine-tune) |
| Training API | `mlx_lm.lora`, `mlx_lm.tuner` |
| Precision | BF16 (native on Apple Silicon) |
| Gradient checkpointing | Required for large-weight models |

**Why primary:** Apple Silicon unified memory is MLX's optimal substrate.
PyTorch/MPS offers no advantage on this hardware and adds framework overhead.

### 4.2 Fallback Stack: PyTorch + PEFT/TRL

| Item | Value |
|------|-------|
| Stack | PyTorch + Hugging Face PEFT + TRL |
| Key dependencies | `transformers >= 5.5`, `torch >= 2.11`, `peft`, `trl` |
| Device | MPS (Metal Performance Shaders) |
| When to use | Only when MLX hits an architectural blocker |

**Fallback trigger rules:**

1. MLX does not support the target model architecture at all
2. MLX training produces incorrect gradients or silent corruption
3. A required training technique (e.g., specific RLHF variant) has no MLX
   implementation and cannot be reasonably built

**Fallback does NOT trigger for:**

- Slower training speed on MLX (speed is not an architectural blocker)
- Missing convenience features (can be built)
- Preference for PyTorch ecosystem familiarity

### 4.3 Stack Decision Rule

```
IF mlx-lm supports the model architecture
AND gradient flow is verified correct
AND training produces valid adapter artifacts
THEN use MLX native (primary)
ELSE evaluate PyTorch fallback with explicit justification
```

No training run may use the fallback stack without a documented reason that
references one of the fallback trigger rules above.

## 5. Training Capabilities

### 5.1 Verified Training Methods

| Method | Stack | Status | Notes |
|--------|-------|--------|-------|
| LoRA fine-tune | MLX native | verified | 4-layer LoRA on 30B+ model validated |
| DoRA fine-tune | MLX native | available | Supported by mlx-lm, not yet exercised |
| Full fine-tune | MLX native | available | Supported by mlx-lm, memory-constrained at 30B+ |
| QLoRA | MLX native | available | Quantized base + LoRA adapters |

### 5.2 Verified Performance Envelope

Measured on M5 Max 128 GB with gemma-4-31B-it (BF16, 30.7B params):

| Metric | Value |
|--------|-------|
| LoRA trainable params | 4.09M (0.013%, last 4 layers) |
| Peak memory | 62 GB |
| Memory headroom | 66 GB remaining |
| Training throughput | 180–254 tokens/sec |
| Loss trajectory | 10.7 → 6.1 (5 steps, gradient flowing correctly) |

### 5.3 Scaling Potential

With 66 GB headroom on the reference machine:

- `--num-layers`: 4 → 16+ (more LoRA layers = more model capacity)
- `--max-seq-length`: 256 → 1024+ (longer training sequences)
- `--batch-size`: 1 → 2–4 (with gradient accumulation)

These are estimates. Actual scaling must be validated per model.

## 6. Substrate Boundary

### 6.1 What owlmlx Owns

| Responsibility | Owned by |
|----------------|----------|
| Training environment contract (this document) | owlmlx |
| Training stack selection rules | owlmlx |
| Artifact layout contract | owlmlx |
| Training-to-serving contract | owlmlx |
| Artifact registration truth | owlmlx |
| Training capability labels and honesty | owlmlx |

### 6.2 What The Platform Shell / Product Layer Owns

| Responsibility | Owned by |
|----------------|----------|
| Training job orchestration UI | platform shell |
| Training progress dashboard | platform shell |
| Data pipeline and dataset preparation | platform shell / external tooling |
| Evaluation UI and human review workflows | platform shell |
| Model selection and deployment decisions (product-level) | platform shell |

### 6.3 What Remains External Tooling

| Responsibility | Owned by |
|----------------|----------|
| `mlx-lm` training implementation | external (open-source) |
| `mlx` / `mlx-metal` substrate | external (Apple) |
| PyTorch / PEFT / TRL (fallback) | external (open-source) |
| Hugging Face model hub and format conventions | external |

### 6.4 Boundary Rule

Training scripts may call `mlx-lm` directly. owlmlx does not wrap the training
loop itself. What owlmlx owns is:

1. The contract that says where training happens (environment)
2. The contract that says what stack to use (stack selection)
3. The contract that says where artifacts go (artifact layout)
4. The contract that says how artifacts come back into runtime (training-to-serving)

owlmlx is NOT a training orchestration platform. It is the truth authority for
how training relates to the runtime it operates.

## 7. Model Architecture Support

### 7.1 Verified Architectures

| Architecture | mlx-lm ID | Verified | Notes |
|-------------|-----------|----------|-------|
| Gemma 4 | `gemma4` / `gemma4_text` | yes | PR #1093, merged 2026-04-04 |

### 7.2 Architecture Verification Rule

Before any model is trained through the owlmlx substrate:

1. Confirm `mlx-lm` supports the architecture (check `mlx_lm/tuner/`)
2. Run a minimal 5-step LoRA pilot to verify gradient flow
3. Confirm adapter checkpoint saves successfully
4. Record peak memory and throughput

If verification fails, the model architecture is NOT part of the owlmlx
training substrate until the blocker is resolved.

## 8. Relationship To Other Contracts

- **Runtime contracts** (`runtime-contracts.md`): Training substrate is a new
  contract family alongside core runtime status and large-weight path status.
- **Large-weight path truth** (`large-weight-path-truth.md`): Models trained
  through this substrate may serve on the large-weight path. The serving
  posture and concurrency rules of that path apply regardless of training
  method.
- **Gemma production mainline** (`gemma-high-fidelity-role.md`): Gemma is the
  first model to exercise this training substrate. The substrate is not
  Gemma-private.
- **Artifact layout** (to be frozen in Round 2): Where trained artifacts are
  stored, named, and registered.
- **Training-to-serving** (to be frozen in Round 3): How trained artifacts
  re-enter the owlmlx runtime for inference.

## 9. What This Contract Does Not Cover

1. Specific training hyperparameters (per-model, per-task)
2. Dataset schema or data engineering pipelines
3. Evaluation criteria or quality metrics
4. RLHF / DPO / reward modeling (future, not current substrate)
5. Multi-node or distributed training (not applicable to Apple Silicon)
6. Training job scheduling or queuing (product layer responsibility)
