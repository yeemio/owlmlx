# owlmlx Runtime Model Visibility Contract

> Status: authoritative
> Updated: 2026-05-05
> Scope: runtime-owned answer to "which local models should be visible?"
> Verdict: `owlmlx_visibility_truth_source_introduced`

## 1. Purpose

This document freezes the first owlmlx-owned contract for local model
visibility.

It exists to answer one narrow question honestly:

- which local models should appear in owlmlx's stable visibility list for
  downstream consumers such as the old router or OwlCoda

It does **not** answer:

- what is loaded right now
- what the product catalog should promote
- which lifecycle state a model should carry

Those are different layers.

## 2. Authoritative Surfaces

owlmlx now exposes three related but non-equivalent surfaces:

| Role | Surface | Meaning |
|---|---|---|
| formal visibility list | `GET /v1/openai/models` | models that pass the owlmlx visibility gate |
| diagnostic visibility contract | `GET /v1/runtime/model-visibility` | machine-readable rule, gate, coverage, and blockers |
| loaded inventory | `GET /v1/models` | current runtime inventory and status, plus embedded `visibility_contract` block |

The important freeze is:

- `GET /v1/openai/models` is the formal list-shaped visibility surface
- `GET /v1/models` is **not** the formal visibility surface; it remains loaded
  inventory

## 3. Runtime-Owned Visibility Rule

Rule identifier:

```text
runtime_gate_required_before_visible
```

A model is visibility-ready when **all** of the following hold:

1. the model is registered in owlmlx's visibility registry
2. its base-model directory exists under `$MODELS_ROOT/{model-id}/`
3. `config.json` exists in that base-model directory

Contract version: `runtime-owned-2`.

Default models root:

- `/Users/yeemio/AI/Agent/models`

This comes from the existing owlmlx artifact layout contract, where base models
already live under a shared `$MODELS_ROOT`.

## 4. Why This Is Different From Loaded Inventory

Loaded inventory and stable visibility are different contracts:

- loaded inventory answers: "what is active in the backend right now?"
- visibility answers: "what owlmlx-registered local models are loadable on
  demand?"

That is why owlmlx now freezes:

- `/v1/openai/models` for visibility
- `/v1/models` for loaded inventory

Any consumer that treats `/v1/models` as if it were the visibility truth is now
wrong.

## 5. Initial Registered Visibility Set

The initial owlmlx-owned visibility registry includes:

- `Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit`
- `Qwen3.5-35B-A3B-4bit`
- `Qwen3.6-27B`
- `Qwen3.6-35B-A3B`
- `gemma-4-31B-it`
- `gpt-oss-20b-MXFP4-Q4`
- `Qwen3-Embedding-8B-4bit-DWQ`

`gpt-oss-120b-MXFP4-Q4` was removed from this registry on 2026-05-05 after its
local base artifact was intentionally deleted from
`/Users/yeemio/AI/Agent/models`. It is no longer a runtime-visible model, a
Model RC gate member, or a heavyweight pressure canary.

The first six are the current OwlCoda-facing coverage set for this round.
The embedding model is included to preserve current local visibility behavior.

## 6. Relationship To The Old Platform Rule

The old platform contract remains frozen in:

- `/Users/yeemio/AI/Agent/docs/source-of-truth/local-llm-platform/phase44-owlcoda-v1-models-contract.md`

with:

- surface: `router :8009 /v1/models`
- rule: `gate_required_before_visible`

The owlmlx rule is now distinct:

| Dimension | Old router rule | owlmlx rule |
|---|---|---|
| identifier | `gate_required_before_visible` | `runtime_gate_required_before_visible` |
| truth owner | `llm_router` | `owlmlx` |
| depends on `model_fleet/status.json` | yes | no |
| depends on lifecycle curation | yes | no |
| depends on extreme-experiment filtering | yes | no |
| depends on owlmlx registry + base-model artifact presence | no | yes |
| formal list surface | `router /v1/models` | `owlmlx /v1/openai/models` |

The cutover target is:

- old router becomes a downstream consumer or proxy of owlmlx visibility truth
- old router stops being the only truth owner for OwlCoda model visibility

## 7. What This Contract Does NOT Own

This contract deliberately does **not** own:

- lifecycle state curation
- extreme-experiment filtering
- product catalog membership
- onboarding or provider policy
- "currently loaded" backend inventory

Those remain outside this runtime contract unless explicitly absorbed later.

## 8. Consumer Guidance

The honest consumer behavior is now:

1. use `GET /v1/openai/models` when you need owlmlx's stable visible-model list
2. use `GET /v1/runtime/model-visibility` when you need the rule, gate, and
   per-model blocker detail
3. use `GET /v1/models` only for current loaded runtime inventory and status

For the old router, the desired cutover is:

1. consume owlmlx `GET /v1/openai/models` as the formal visibility list
2. optionally consume owlmlx `GET /v1/runtime/model-visibility` for diagnostics
3. stop owning an independent visibility rule for the same OwlCoda dependency

## 9. Tests

Contract tests now cover:

- registry + base-model gate derivation
- formal-surface freeze at `GET /v1/openai/models`
- semantic distinction from loaded inventory
- embedded `visibility_contract` block inside `GET /v1/models`
