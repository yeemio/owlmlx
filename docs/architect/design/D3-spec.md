# D3 · Design-Grade Spec

> **Gate**: Campaign D3 · DeepSeek V4 Flash MTP checkpoint inspection
> **Plan-grade source**: [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign D
> **Status**: inspection passed with explicit missing reason · 2026-05-17
> **Prerequisite**: D1 repeatability passed and D2 metrics ladder passed.
> **Non-goal**: this spec does not claim DeepSeek V4 MTP serving.

## 1. Purpose

D3 closes the checkpoint/MTP question for the isolated DeepSeek V4 lane without
running generation:

```text
read config.json
  -> read model.safetensors.index.json
  -> compare declared num_nextn_predict_layers with weight keys
  -> record whether MTP/draft/extra-layer weights are present
  -> write missingReason when absent
```

D3 is a metadata inspection gate. It does not register DeepSeek V4 in the
default model surface, does not adopt `ds4.c`, and does not promote the lane out
of `experimental_only`.

## 2. Scope

| Item | Requirement |
|---|---|
| Artifact | `DeepSeek-V4-Flash-2bit-DQ` local MLX checkpoint |
| Adapter reference | `.runtime-deepseek-v4-mlx` / `/tmp/mlx-lm-dsv4` fork used by D1/D2 |
| Files read | `config.json`, `model.safetensors.index.json`, top-level candidate filenames |
| Detection signals | explicit `mtp` / `draft` / speculative key names; extra layer keys with index >= `num_hidden_layers` |
| Evidence | JSONL under `files/evidence/owlmlx/deepseek-v4/d3-checkpoint-inspection/` |
| Capability label | `experimental_only` |

## 3. Ledger Shape

Each row is a D3 checkpoint inspection result:

```yaml
schema_version: d3.checkpoint_inspection.v1
record_type: mtp_checkpoint_inspection
gate: D3
model_id: DeepSeek-V4-Flash-2bit-DQ
config_summary:
  model_type: deepseek_v4
  architectures: [DeepseekV4ForCausalLM]
  num_hidden_layers: int
  num_nextn_predict_layers: int
weight_index_summary:
  weight_key_count: int
  safetensors_shard_count: int
  matched_mtp_weight_key_count: int
  extra_layer_key_count: int
inspection:
  config_declares_nextn_predict_layers: bool
  has_mtp_weight_candidates: bool
  mtp_weight_status: present | absent_or_stripped | not_configured
  missingReason: mtp_weights_absent_or_stripped | null
capability_conclusion: mtp_checkpoint_not_available | mtp_checkpoint_candidate_present | mtp_not_configured
verdict: passed | blocked
```

The expected absent/stripped patterns cover both common DeepSeek-family forms:

- `mtp.*`
- `model.layers.<index >= num_hidden_layers>.*`
- `layers.<index >= num_hidden_layers>.*`

## 4. Pass Criteria

```yaml
D3_mtp_checkpoint_inspection:
  metadata_readable:
    config_json: true
    safetensors_index: true
  if_mtp_weights_absent:
    missingReason: mtp_weights_absent_or_stripped
  default_model_surface_changed: false
  overall_conclusion: passed
```

D3 passes when the inspection itself is readable and explicit. If the checkpoint
lacks MTP weights, D3 still passes as an inspection gate, but the capability
conclusion must be `mtp_checkpoint_not_available`.

## 5. Current Evidence

```bash
uv run python scripts/bench/deepseek_v4_d1_repeatability.py checkpoint-inspect \
  --run-id 20260517T-d3-mtp-checkpoint-inspection \
  --adapter-path /tmp/mlx-lm-dsv4
```

| File | Verdict | Key conclusion |
|---|---|---|
| `files/evidence/owlmlx/deepseek-v4/d3-checkpoint-inspection/20260517T-d3-mtp-checkpoint-inspection.jsonl` | passed | `num_nextn_predict_layers=1`; 2610 weight keys / 19 shards; no MTP key candidates; no extra layer keys; `missingReason=mtp_weights_absent_or_stripped` |

Current D3 boundary: MTP checkpoint support is not available for this local
artifact. The DeepSeek lane remains `experimental_only`.

## 6. Next Debug Slice

D3 unlocks D4 clean pre-load rejection / failure isolation. A future D3 rerun is
only useful if a new DeepSeek artifact or adapter fork is introduced.
