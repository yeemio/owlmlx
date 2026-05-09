# owlmlx Gemma4 MTP A/B Timing And Lifecycle Round

## Context

Gemma4 MTP now has two owlmlx-owned experimental layers:

- wrapper/contract:
  `owlmlx/gemma4_mtp_drafter.py`
- selectable child runner:
  `owlmlx/runtime/mlx_vlm_mtp_runner.py`

Local assets:

- target:
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- drafter:
  `/Users/yeemio/AI/Agent/model-candidates/mlx-community/gemma-4-31B-it-assistant-bf16`
- runtime python:
  `/Users/yeemio/AI/gitrep/runtime-probes/mlx-vlm-mtp-probe/.venv/bin/python`

Verified evidence:

- external MTP probe:
  `files/evidence/owlmlx/gemma-mtp-draft-probe/20260506T132604Z/manifest.json`
- backend bridge smoke:
  `files/evidence/owlmlx/gemma-mtp-backend-bridge/20260506T134444Z/manifest.json`

The bridge is still `experimental` and currently uses
`deferred_cli_per_request`, not a resident `mlx-vlm` backend.

Adapter boundary:

- `mlx-lm adapter` remains the text LLM mainline for Qwen, DeepSeek text
  paths, GPT-OSS-style text generation, and similar pure text models.
- `mlx-vlm adapter` is the Gemma4 / multimodal / MTP drafter mainline. Gemma4
  may be used text-only, but its architecture and current MTP assistant route
  belong to the `mlx-vlm` ecosystem.
- The A/B round should preserve these names exactly: `mlx-lm` and `mlx-vlm`.

## Objective

Produce honest same-host A/B evidence for Gemma4 with and without MTP under the
same prompt, token budget, and lifecycle checks.

## Hard Rules

- Keep the capability label `experimental`.
- Do not claim speedup unless the measured A/B supports it.
- Do not compare a dirty post-run state against a clean one as if it were a
  win.
- Do not call this supported serving or resident backend behavior.
- Keep 8066 post-run `/healthz` clean if HTTP is involved.
- Capture enough stdout/stderr to explain failures without hiding lifecycle
  problems.

## Suggested Commands

Inspect current readiness first:

```bash
python3 scripts/runtime_gemma4_mtp_drafter.py inspect
```

Run the MTP side through the child-runner bridge:

```bash
OWLMLX_RUNTIME_PYTHON=/Users/yeemio/AI/gitrep/runtime-probes/mlx-vlm-mtp-probe/.venv/bin/python \
OWLMLX_BACKEND_RUNNER_MODULE=owlmlx.runtime.mlx_vlm_mtp_runner \
OWLMLX_GEMMA4_MTP_DRAFT_MODEL=/Users/yeemio/AI/Agent/model-candidates/mlx-community/gemma-4-31B-it-assistant-bf16 \
OWLMLX_GEMMA4_MTP_DRAFT_BLOCK_SIZE=6 \
python3 <small backend-smoke-or-rc-runner>
```

Run the non-MTP reference side with the same `mlx-vlm` target and no
`--draft-model`, or explicitly record why the current wrapper lacks that
operator path and add it before measuring.

## Acceptance Criteria

- Evidence directory contains:
  - MTP run manifest/logs
  - non-MTP run manifest/logs
  - post-run health/lifecycle checks
  - parsed timing and speculative summary
- The source-of-truth note states one of:
  - `mtp_measured_faster`
  - `mtp_measured_neutral`
  - `mtp_measured_slower`
  - `mtp_ab_rejected`
- The verdict remains narrow to this prompt/workload.
