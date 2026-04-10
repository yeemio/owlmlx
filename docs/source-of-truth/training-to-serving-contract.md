# owlmlx Training-To-Serving Contract

> Status: authoritative
> Updated: 2026-04-10
> Frozen by: owlmlx-gemma-training-and-production-mainline Round 3

## 1. Purpose

This document defines how trained artifacts re-enter the owlmlx runtime for
inference (serving). Without this contract, the gap between "adapter saved" and
"model serving with adapter" is bridged by ad-hoc scripts with no runtime
truth.

## 2. Scope

This contract covers:

1. **Load path** — how the runtime loads a tuned artifact for inference
2. **Serving feasibility** — what must be true before a tuned artifact can serve
3. **Truth surfaces** — how the runtime exposes tuned artifact identity and status
4. **Responsibility boundary** — what owlmlx owns vs what the shell owns

This contract does NOT cover:

- Training process or environment (see `training-substrate-contract.md`)
- Artifact storage or naming (see `artifact-layout-contract.md`)
- Product-level deployment decisions or UI
- Data engineering or evaluation criteria

## 3. Load Path

### 3.1 LoRA Adapter Loading

For LoRA/DoRA tuned artifacts, the load path is:

1. Load base model from `$MODELS_ROOT/{model-id}/`
2. Load adapter weights from `$MODELS_ROOT/{model-id}/tuned/{run-id}/adapters.safetensors`
3. Apply adapter to base model using `mlx_lm.load()` with `adapter_path`
4. Verify generation produces coherent output (inference delta check)

The runtime does not merge adapters into base weights. The adapter is applied
at load time and remains a separate artifact.

### 3.2 Full Fine-Tune Loading

For full fine-tune artifacts, the load path is:

1. Load the complete model from `$MODELS_ROOT/{model-id}/tuned/{run-id}/`
2. This directory is self-contained — no reference to the base model needed
3. Verify generation produces coherent output

### 3.3 Load Path Rules

1. The runtime MUST read `metadata.json` before loading any tuned artifact
2. If `metadata.json` is missing or `status` < `completed`, the artifact MUST
   NOT be loaded for serving
3. The runtime MUST verify that referenced files (adapter weights, model weights)
   actually exist before attempting load
4. Load failures MUST be reported as runtime status, not silently ignored

## 4. Serving Feasibility

A tuned artifact is feasible for serving only when ALL of the following are true:

### 4.1 Artifact Feasibility Checklist

| Check | Requirement |
|-------|-------------|
| Registration | `metadata.json` exists with `status` ≥ `completed` |
| File integrity | `adapter_path` or model weights exist at declared paths |
| Load verification | Artifact has been loaded at least once without error |
| Inference delta | Generated output differs meaningfully from base model |
| Memory budget | Peak serving memory fits within available unified memory |
| Path compliance | Artifact complies with serving path rules (e.g., large-weight path concurrency = 1) |

### 4.2 Feasibility Status

After verification, `metadata.json` should be updated:

| Field | Value |
|-------|-------|
| `serving_feasibility` | `"pass"` or `"fail"` or `"pending"` |
| `serving_feasibility_note` | Human-readable explanation |
| `load_verified_at` | ISO timestamp of last successful load |
| `inference_delta_verified` | `true` / `false` |

### 4.3 Feasibility Rule

No tuned artifact may enter a serving configuration until its
`serving_feasibility` is `"pass"`. This is a runtime contract, not a product
policy — the runtime itself must enforce it.

## 5. Truth Surfaces

### 5.1 Runtime Status Extension

When serving a tuned artifact, the runtime status (as defined in
`runtime-contracts.md`) must expose:

| Field | Value | Notes |
|-------|-------|-------|
| `tuned_artifact.run_id` | e.g., `"premise-lora-20260410-01"` | Which training run produced the active artifact |
| `tuned_artifact.method` | e.g., `"lora"` | Training method |
| `tuned_artifact.model_id` | e.g., `"gemma-4-31B-it"` | Base model |
| `tuned_artifact.status` | e.g., `"serving"` | Current artifact lifecycle status |
| `tuned_artifact.trainable_params` | e.g., `4090000` | LoRA parameter count |
| `tuned_artifact.created_at` | ISO timestamp | When the artifact was trained |

### 5.2 Status Source

These fields come from `metadata.json`. The runtime reads metadata at load time
and exposes it through the existing runtime status contract.

### 5.3 Base vs Tuned Distinction

The runtime status MUST distinguish between:

- Serving the **base model** (no tuned artifact loaded)
- Serving a **tuned artifact** (adapter or full fine-tune applied)

This is not cosmetic. Upper layers need this distinction for:

- Correctness (knowing which model variant is producing output)
- Audit trail (which training run generated a response)
- Rollback (ability to fall back to base model)

## 6. Responsibility Boundary

### 6.1 owlmlx Owns

| Responsibility | Details |
|----------------|---------|
| Load path contract | How to load a tuned artifact (this document) |
| Serving feasibility rules | What must be true before serving |
| Truth surfaces for tuned artifacts | Runtime status fields for active artifact |
| Feasibility enforcement | Runtime rejects artifacts that haven't passed checks |
| `metadata.json` contract | Schema and required fields |

### 6.2 Platform Shell / Product Layer Owns

| Responsibility | Details |
|----------------|---------|
| Model selection UI | Which model/artifact to load (product decision) |
| Deployment workflow | When and how to switch from base to tuned |
| A/B testing or rollout | Gradual deployment of tuned models |
| User-facing artifact browsing | Dashboard showing available artifacts |
| Evaluation-driven promotion | Deciding which artifact becomes primary |

### 6.3 Shared Concern: Model Switching

Switching from base model to tuned artifact (or between artifacts) is a runtime
operation governed by existing owlmlx switching safety rules:

1. Must drain active generation before switching (GenerationGate)
2. Must report memory impact of the new configuration
3. Must update runtime status after switch completes
4. Must follow the heavy execution protocol if the switch is hazardous

The product layer decides WHEN to switch. The runtime governs HOW.

## 7. Serving Configuration

### 7.1 Minimal Serving Configuration

To serve a tuned artifact, the runtime needs:

```json
{
  "model_id": "gemma-4-31B-it",
  "run_id": "premise-lora-20260410-01",
  "models_root": "/Users/yeemio/AI/Agent/models"
}
```

From this, the runtime can derive:

- Base model path: `{models_root}/{model_id}/`
- Artifact path: `{models_root}/{model_id}/tuned/{run_id}/`
- Metadata: `{models_root}/{model_id}/tuned/{run_id}/metadata.json`

### 7.2 Configuration Rules

1. Serving configuration is declarative, not imperative
2. The runtime resolves paths from configuration, not from hardcoded values
3. If `run_id` is omitted, serve the base model without any adapter
4. If `run_id` points to a non-existent or non-feasible artifact, refuse to load

## 8. Relationship To Other Contracts

- **Training substrate** (`training-substrate-contract.md`): Upstream — defines
  where and how training happens.
- **Artifact layout** (`artifact-layout-contract.md`): Upstream — defines where
  artifacts are stored and how they are registered.
- **Runtime contracts** (`runtime-contracts.md`): Peer — training-to-serving
  extends the runtime contract surface with tuned artifact identity.
- **Large-weight path truth** (`large-weight-path-truth.md`): Constraint —
  tuned artifacts served on this path must comply with its serving posture
  (single-worker, queue-based, concurrency = 1).
- **Gemma production mainline** (`gemma-high-fidelity-role.md`): First
  consumer — Gemma is the first model whose tuned artifacts will flow through
  this contract.

## 9. What This Contract Does Not Cover

1. Training execution (training-substrate-contract.md)
2. Artifact naming and storage (artifact-layout-contract.md)
3. Quality evaluation or human review
4. Automatic training-to-serving promotion pipelines
5. Multi-model serving or model routing
