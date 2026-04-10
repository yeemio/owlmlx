# owlmlx Artifact Layout Contract

> Status: authoritative
> Updated: 2026-04-10
> Frozen by: owlmlx-gemma-training-and-production-mainline Round 2

## 1. Purpose

This document defines where trained model artifacts live, how they are named,
and how they are registered for consumption by the owlmlx runtime.

Without this contract, trained adapters, checkpoints, and metadata accumulate
in ad-hoc locations with no formal relationship to the runtime. This contract
makes trained artifacts first-class owlmlx citizens.

## 2. Scope

This contract covers:

1. **Base model path rules** — where original model weights live
2. **Tuned artifact layout** — adapter, checkpoint, eval, and metadata structure
3. **Naming and versioning** — how artifacts are identified
4. **Artifact registration** — how the runtime discovers trained artifacts

This contract does NOT cover:

- Training hyperparameters or training scripts
- Data engineering or dataset locations
- Serving configuration or deployment (see `training-to-serving-contract.md`)
- Product-level model selection UI

## 3. Directory Structure

### 3.1 Root

All model artifacts live under a single models root:

```
$MODELS_ROOT/
```

Default: `/Users/yeemio/AI/Agent/models/`

The models root is infrastructure. It is not owned by any single model or
training run.

### 3.2 Base Model Layout

Base models (original weights, not fine-tuned) follow the Hugging Face
directory convention:

```
$MODELS_ROOT/{model-id}/
  config.json
  tokenizer.json
  tokenizer_config.json
  model-*.safetensors
  model.safetensors.index.json
  generation_config.json
  chat_template.jinja
  README.md
  ...
```

**Rules:**

1. `{model-id}` is the canonical model name (e.g., `gemma-4-31B-it`)
2. Base model directories are read-only after initial download
3. Training MUST NOT write into base model directories
4. Base models may be BF16, quantized, or any format the training stack supports

### 3.3 Tuned Artifact Layout

Trained artifacts live in a `tuned/` subtree under the base model:

```
$MODELS_ROOT/{model-id}/tuned/{run-id}/
  adapters.safetensors          # LoRA/DoRA adapter weights
  adapter_config.json           # LoRA configuration (rank, alpha, target modules)
  training_args.json            # Training arguments used
  training_log.jsonl            # Per-step loss and metrics (optional)
  eval/                         # Evaluation outputs (optional)
    eval_results.json
    sample_outputs.jsonl
  metadata.json                 # owlmlx artifact registration metadata
```

**Rules:**

1. Each training run gets its own `{run-id}` directory — never overwrite
2. `adapters.safetensors` is the primary artifact for LoRA runs
3. `metadata.json` is required for artifact registration (see section 6)
4. The `eval/` subtree is optional but recommended
5. No files outside the `{run-id}` directory may be modified by a training run

### 3.4 Full Fine-Tune Layout

For full fine-tune (not LoRA), the tuned directory contains the full model:

```
$MODELS_ROOT/{model-id}/tuned/{run-id}/
  config.json
  model-*.safetensors
  model.safetensors.index.json
  tokenizer.json
  tokenizer_config.json
  training_args.json
  training_log.jsonl
  eval/
    ...
  metadata.json
```

Full fine-tune artifacts are self-contained and do not reference the base model
at inference time.

### 3.5 Checkpoint Layout

Training checkpoints (intermediate saves) live in a `checkpoints/` subtree:

```
$MODELS_ROOT/{model-id}/tuned/{run-id}/checkpoints/
  step-{N}/
    adapters.safetensors
    adapter_config.json
    optimizer.safetensors       # (optional, for training resume)
```

**Rules:**

1. Checkpoints are for training resume and debugging, not for serving
2. Checkpoints may be pruned after training completes
3. Only the final `{run-id}/adapters.safetensors` is the serving artifact

## 4. Naming Rules

### 4.1 Model ID

The model ID is the canonical name of the base model:

- Use the Hugging Face model name when applicable
- Lowercase with hyphens (e.g., `gemma-4-31B-it`)
- Do not rename base models locally

### 4.2 Run ID

The run ID uniquely identifies a training run:

```
{task}-{method}-{date}-{seq}
```

Components:

| Part | Format | Example |
|------|--------|---------|
| `{task}` | Short task identifier | `premise`, `scene`, `dialogue`, `general` |
| `{method}` | Training method | `lora`, `dora`, `full`, `qlora` |
| `{date}` | ISO date (YYYYMMDD) | `20260410` |
| `{seq}` | Two-digit sequence within that day | `01`, `02` |

Examples:

- `premise-lora-20260410-01`
- `dialogue-dora-20260415-03`
- `general-lora-20260410-01`

### 4.3 Versioning

There is no abstract version number. The run ID IS the version.

If a run supersedes a previous one, the metadata.json should reference the
predecessor run ID, but both directories coexist.

## 5. What Lives Where — Summary

| Artifact | Location | Mutable? |
|----------|----------|----------|
| Base model weights | `$MODELS_ROOT/{model-id}/` | No (read-only after download) |
| LoRA adapters | `$MODELS_ROOT/{model-id}/tuned/{run-id}/adapters.safetensors` | No (immutable after training) |
| Full fine-tune weights | `$MODELS_ROOT/{model-id}/tuned/{run-id}/model-*.safetensors` | No (immutable after training) |
| Training args | `$MODELS_ROOT/{model-id}/tuned/{run-id}/training_args.json` | No |
| Training log | `$MODELS_ROOT/{model-id}/tuned/{run-id}/training_log.jsonl` | Append-only during training |
| Checkpoints | `$MODELS_ROOT/{model-id}/tuned/{run-id}/checkpoints/step-{N}/` | Prunable after training |
| Evaluation results | `$MODELS_ROOT/{model-id}/tuned/{run-id}/eval/` | Append-only |
| Artifact metadata | `$MODELS_ROOT/{model-id}/tuned/{run-id}/metadata.json` | No (immutable after registration) |

## 6. Artifact Registration — metadata.json

Every tuned artifact directory MUST contain a `metadata.json` that serves as
the artifact's registration record with the owlmlx runtime.

### 6.1 Required Fields

```json
{
  "owlmlx_artifact_version": "1",
  "model_id": "gemma-4-31B-it",
  "run_id": "premise-lora-20260410-01",
  "method": "lora",
  "base_model_path": "../..",
  "adapter_path": "adapters.safetensors",
  "created_at": "2026-04-10T12:00:00Z",
  "training_stack": "mlx-lm",
  "training_stack_version": "0.31.2",
  "status": "completed",
  "trainable_params": 4090000,
  "total_params": 30697000000,
  "peak_memory_gb": 62,
  "training_tokens_per_sec": 220,
  "final_loss": 6.1,
  "training_steps": 5,
  "lora_config": {
    "rank": 8,
    "alpha": 16,
    "num_layers": 4,
    "target_modules": ["q_proj", "v_proj"]
  }
}
```

### 6.2 Optional Fields

```json
{
  "predecessor_run_id": null,
  "task_head": "premise",
  "dataset_description": "200-episode short drama corpus, premise extraction",
  "eval_summary": "See eval/eval_results.json",
  "serving_feasibility": "pending",
  "notes": "First pilot run, minimal data"
}
```

### 6.3 Status Values

| Status | Meaning |
|--------|---------|
| `training` | Training in progress, artifact incomplete |
| `completed` | Training finished, artifact saved |
| `verified` | Load verification passed (can be loaded for inference) |
| `serving` | Actively used in a serving configuration |
| `superseded` | Replaced by a newer run |
| `failed` | Training failed, artifact may be partial |

### 6.4 Registration Rule

An artifact is considered registered with the owlmlx runtime when:

1. `metadata.json` exists in the run directory
2. `status` is `completed` or later
3. `adapter_path` (or full-model path) points to an existing file

The runtime discovers artifacts by scanning
`$MODELS_ROOT/{model-id}/tuned/*/metadata.json`.

## 7. Relationship To Other Contracts

- **Training substrate** (`training-substrate-contract.md`): Defines the
  environment in which training happens. This contract defines where the
  outputs go.
- **Training-to-serving** (to be frozen in Round 3): Defines how artifacts
  registered here re-enter the runtime for inference.
- **Large-weight path truth** (`large-weight-path-truth.md`): Models served
  through this path must comply with serving posture and concurrency rules
  regardless of training method.

## 8. What This Contract Does Not Cover

1. How to run training (training-substrate-contract.md handles stack selection)
2. How to serve a trained model (training-to-serving-contract.md)
3. Dataset schema or data engineering locations
4. Model evaluation criteria or quality thresholds
5. Product-level model selection or deployment policies
