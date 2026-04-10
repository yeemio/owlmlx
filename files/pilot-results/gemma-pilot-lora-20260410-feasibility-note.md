# Gemma Pilot LoRA — Feasibility Note

> Date: 2026-04-10
> Run ID: `pilot-lora-20260410-01`
> Verdict: **PASS — minimal LoRA pilot completes end-to-end through owlmlx substrate**

## What Was Validated

| Check | Result |
|-------|--------|
| LoRA training (5 steps) | PASS — loss 10.5 → 6.5 |
| Adapter save | PASS — `adapters.safetensors` (16 MB) |
| Artifact layout compliance | PASS — saved to `$MODELS_ROOT/gemma-4-31B-it/tuned/pilot-lora-20260410-01/` |
| metadata.json registration | PASS — owlmlx `build_artifact_metadata()` produced valid metadata |
| Serving feasibility check | PASS — owlmlx `validate_artifact_for_serving()` returned pass |
| Load verification | PASS — adapter loaded via `mlx_lm.load(adapter_path=...)` |
| Inference delta | PASS — tuned model output differs from base model |

## Training Details

| Metric | Value |
|--------|-------|
| Base model | `gemma-4-31B-it` (BF16, 30.7B params) |
| Training stack | `mlx-lm 0.31.2` |
| Method | LoRA (last 4 layers) |
| Trainable params | 4.094M / 30,697M (0.013%) |
| Training data | 4 samples (minimal pilot) |
| Steps | 5 |
| Loss trajectory | 10.506 → 6.480 |
| Peak memory | 61.792 GB |
| Throughput | 65 tokens/sec (low due to short sequences) |
| Adapter size | 16 MB |

## owlmlx Substrate Exercised

This pilot exercised the following owlmlx contracts:

1. **Training substrate** — venv, MLX native stack, Gemma architecture verified
2. **Artifact layout** — `tuned/{run-id}/` directory with adapters + metadata
3. **Artifact registration** — `owlmlx.training.build_artifact_metadata()` + `write_artifact_metadata()`
4. **Serving feasibility** — `owlmlx.training.validate_artifact_for_serving()` passed all checks
5. **Training-to-serving load path** — `mlx_lm.load(adapter_path=...)` confirmed working

## Inference Delta

Base model output was degenerate (`<start_of_turn>model` repeated — expected
for raw BF16 without proper generation config). Tuned model output diverged
after adapter application, confirming gradient flow affected the model.

**Note:** 5 steps on 4 samples is not production training. The delta confirms
mechanical correctness, not quality. Production training requires real data
scale, proper hyperparameters, and evaluation criteria.

## What This Proves

1. The owlmlx training substrate contracts (environment, artifact, serving) work end-to-end
2. `gemma-4-31B-it` LoRA training through `mlx-lm` produces valid artifacts
3. owlmlx artifact registration (`training.py`) correctly discovers and validates artifacts
4. The load path from saved adapter back to inference works without manual intervention
5. Memory management requires sequential load/unload for 31B model on 128 GB (cannot dual-load)

## What This Does Not Prove

1. Production-quality training output (need real data + evaluation)
2. Optimal hyperparameters (need systematic tuning)
3. Long-sequence training feasibility (pilot used max_seq_length=256)
4. Multi-adapter serving or hot-swapping
5. Scaled data pipeline integration
