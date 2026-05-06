# owlmlx Model Profile Resolver P0 Handoff

> Executor: A
> Date: 2026-05-05
> Outcome label: `owlmlx_model_profile_resolver_p0_introduced`
> Scope: ModelProfile resolver P0 for Gemma/Qwen mainline and DeepSeek
> experimental pressure-lane labeling

## What Changed

- Added `owlmlx/model_profile.py` as the owlmlx-owned typed profile resolver.
- Added required profiles:
  - `qwen3_6_text`
  - `qwen3_6_moe`
  - `gemma4_text`
  - `deepseek_v4_experimental`
  - `unknown`
- Added `tests/test_model_profile.py` for serialization, deterministic
  resolution, conservative unknown fallback, Gemma/Qwen/DeepSeek caveats, and
  banned-current-claim wording in the new profile module.
- Added non-live Model RC runner-config serialization so future live evidence
  directories include the resolved `model_profile` payload. Historical records
  remain readable because no Model RC schema migration was introduced.

## Boundary Notes

- No peer-runtime code was vendored.
- No external repositories were edited.
- No heavy model load was run.
- DeepSeek V4 remains `deepseek_v4_experimental` and outside the mainline
  release-candidate gate.
- The resolver is profile/config only. It does not claim a live model fix or
  promote any model verdict.

## Verification

Required lightweight checks for this lane:

```bash
.venv/bin/python -m pytest -q tests/test_model_profile.py
.venv/bin/python -m pytest -q tests/test_model_release_candidate_surface.py
.venv/bin/python -m py_compile owlmlx/model_profile.py
git diff --check
```

## Next Recommended Live Evidence Lane

Use the profile payload in the next memory-exclusive Model RC evidence run:

1. Gemma: rerun through the chat-template path and record whether the Gemma
   profile stop/channel/cache caveats reduce repetitive output or only move the
   blocker.
2. Qwen3.6-35B-A3B: run a bounded-thinking/template experiment and record TTFT,
   generated content shape, and whether reasoning traces consume short outputs.
3. Qwen3.6-27B: compare the same prompt/profile against direct MLX-LM streaming
   to isolate wrapper/event overhead from model-side decode behavior.
