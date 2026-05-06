# owlmlx Model Profile Operational Wiring Handoff

> Date: 2026-05-05
> Outcome label: `owlmlx_model_profile_operational_wiring_introduced`

## What Changed

The Model RC live HTTP runner now has an opt-in
`--apply-model-profile-defaults` switch. Without the switch, the runner keeps
the legacy `raw_generate_stream` path and does not write an
`effective_generation_policy` block.

With the switch enabled:

- Qwen3.6 text and Qwen3.6 MoE profiles select `openai_chat_stream` unless
  `--request-mode` is explicitly supplied.
- Gemma4 text selects `openai_chat_stream` unless overridden and records
  profile caveats for channel/reasoning cleanup.
- DeepSeek V4 keeps the experimental profile caveat and is not promoted into a
  mainline route by profile defaults.
- unknown model ids stay conservative on `raw_generate_stream`.
- explicit `--request-mode` and `--prompt-template-id` values are preserved.
- profile stop-token strings are recorded as
  `model_profile:profile_stop_tokens_not_applied`; the current HTTP runner does
  not claim to pass them through.

## Verified

```bash
.venv/bin/python -m pytest -q tests/test_model_profile.py
.venv/bin/python -m pytest -q tests/test_model_release_candidate_surface.py
.venv/bin/python -m py_compile owlmlx/model_profile.py scripts/runtime_model_release_candidate.py
```

No heavy model load was run in this lane.

## Deferred

Live proof remains deferred to a model-owning run that can safely load the
candidate models and compare the profile-aware path against existing evidence.
