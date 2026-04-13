# owlmlx Stabilization-2: Large-Weight Specimen Gate

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only pre-smoke gate for large-weight local specimens

## 1. Purpose

This document freezes the runtime-owned gate that answers:

**Is a local large-weight specimen ready to enter first owlmlx smoke
validation?**

This is the step between:

- MLX environment readiness
- real model-specific `load -> generate` validation

It exists so upcoming work such as MiniMax-M2.7 does not start from ad-hoc
shell checks.

## 2. Owned Contract

`owlmlx/runtime/specimen_gate.py` now owns:

- `assess_specimen_path(...)`
- `build_large_weight_specimen_gate(...)`
- `specimen_gate_to_dict(...)`

Stable sections:

- `summary`
- `specimen_path`
- `mlx_environment`

Serialized contract:

```json
{
  "contract": {
    "surface": "owlmlx.large_weight_specimen_gate",
    "version": "stabilization2"
  },
  "summary": {
    "smoke_ready": false,
    "blocked_reason": "..."
  },
  "specimen_path": {
    "exists": true,
    "path": "/abs/path",
    "kind": "directory",
    "file_count": 130,
    "total_size_bytes": 246913578024,
    "has_config_json": true,
    "shard_count": 130,
    "expected_shard_count": 130,
    "aria2_in_progress": false,
    "blocked_reason": null
  },
  "mlx_environment": {
    "...": "see stabilization2-mlx-environment-readiness.md"
  }
}
```

## 3. Semantics

- `summary.smoke_ready = true` means both conditions are true:
  - the local specimen path is present enough to validate
  - the machine currently has a usable MLX subprocess environment for the
    requested execution mode
- `summary.blocked_reason` is fail-closed truth. It does not guess around a
  missing model path or missing MLX environment.
- `specimen_path.aria2_in_progress = true` is only a blocking signal when the
  indexed shard set is still incomplete. A stale `.aria2` file must not
  override a complete shard set.
- `specimen_path.shard_count < expected_shard_count` means the local shard set
  is incomplete and must not enter first smoke.
- `specimen_path.total_size_bytes` is informational runtime truth, not a
  replaceability claim.

## 4. Operator Entry

`scripts/runtime_large_weight_specimen_gate.py` is the operator entry:

```bash
python3 scripts/runtime_large_weight_specimen_gate.py \
  --specimen-path /path/to/local/model \
  --execution-mode force_cpu
```

The script exits `0` only when the specimen is ready for smoke.

The first smoke entrypoint is now also formalized:

```bash
python3 scripts/runtime_large_weight_first_smoke.py \
  --specimen-path /path/to/local/model \
  --memory-gb 122 \
  --execution-mode force_cpu \
  --prompt "Reply with exactly OK."
```

This flow always runs the specimen gate first. It must not bypass the gate.

## 5. What This Does Not Claim

- that the specimen will definitely load successfully
- that the quantization is correct
- that performance is acceptable
- that the model should be promoted to a supported owlmlx specimen

This gate only answers whether the runtime preconditions for first smoke are in
place.

## 6. Current MiniMax-M2.7 Truth

As of 2026-04-13, the local specimen at
`/Users/yeemio/AI/Agent/models/MiniMax-M2.7` is present at roughly `215G`. The
gate now uses `model.safetensors.index.json` as the shard truth source rather
than blindly trusting the `of-00130` suffix in filenames.

That means:

- the indexed shard set is `125`
- a leftover `.aria2` file alone does not prove the download is incomplete
- the remaining blocker can honestly be the MLX environment rather than the
  weight directory itself

The next honest split for this specimen is:

- `default_metal`: currently blocked on this machine
- `force_cpu`: a distinct path that must be validated separately

This keeps `owlmlx` from over-promoting a partially-downloaded large-weight
specimen into smoke readiness while also avoiding false blocking from stale
download metadata.

Stabilization-3 closes the follow-on locality question by adding
`owlmlx.large_weight_first_smoke_decision`, which now freezes whether local
first smoke may proceed or should move to another host/system image.
