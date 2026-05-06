# owlmlx Model Profile Resolver P0 For Gemma And Qwen Mainline

> Coordinator: owlmlx
> Date: 2026-05-05
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Outcome label: choose one of
> `owlmlx_model_profile_resolver_p0_introduced` or
> `owlmlx_model_profile_resolver_p0_still_blocked`

## 1. Goal

Implement a narrow owlmlx-owned `ModelProfile` resolver and typed profile
contract for the current Model RC mainline blockers.

This round should create the reusable profile layer. It should not run heavy
models and should not try to close live Gemma/Qwen records.

## 2. Required Reading

Read first:

1. `AGENTS.md`
2. `docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md`
3. `docs/source-of-truth/model-release-candidate-program.md`
4. `docs/source-of-truth/release-readiness-execution-plan.md`
5. current diffs for:
   - `scripts/runtime_model_release_candidate.py`
   - `owlmlx/runtime/server.py`
   - `owlmlx/runtime/technical_preview.py`
   - `owlmlx/serving.py`
   - `tests/test_model_release_candidate_surface.py`

## 3. Hard Boundaries

- Do not vendor peer-runtime code.
- Do not modify external repos.
- Do not stop or kill `8001`, `8009`, or the active `8066` preview server.
- Do not run heavy model loads.
- Do not broaden into DeepSeek V4 implementation.
- Preserve existing staged and dirty work; do not revert unrelated changes.
- Do not claim release-ready, parity, replacement, production-grade,
  equivalent, beats, wins, or matches.

## 4. Implementation Target

Add an owlmlx-owned profile module, preferably:

- `owlmlx/model_profile.py`
- `tests/test_model_profile.py`

The profile contract should include:

- `profile_id`
- `profile_family`
- `model_id_patterns`
- `chat_template_kwargs`
- `stop_token_strings`
- `sampler_defaults`
- `reasoning_parser_family`
- `thinking_policy`
- `cache_policy`
- `profile_caveats`
- `source_basis`

Required profile ids:

- `qwen3_6_text`
- `qwen3_6_moe`
- `gemma4_text`
- `deepseek_v4_experimental`
- `unknown`

Required resolver behavior:

- `Qwen3.6-27B` resolves to `qwen3_6_text`.
- `Qwen3.6-35B-A3B` resolves to `qwen3_6_moe`.
- `gemma-4-31B-it` resolves to `gemma4_text`.
- `DeepSeek-V4-Flash-2bit-DQ` resolves to `deepseek_v4_experimental`.
- Unknown model ids resolve conservatively to `unknown`.

Do not overfit to exact capitalization only. The resolver may use normalized
model ids and optional local config fields, but it must stay deterministic.

## 5. Optional Wiring

If safe within this round, add the smallest possible non-live wiring:

- expose profile serialization for Model RC records or runner config
- allow `scripts/runtime_model_release_candidate.py` to compute a default
  `prompt_template_id` / profile label from the resolver
- keep older records readable

If this wiring would touch too many surfaces, defer it and write the handoff.

## 6. Tests

Add focused tests that prove:

- all required profile ids serialize correctly
- known model ids resolve to the expected profiles
- unknown ids stay conservative
- profile fields include Gemma stop/channel/cache caveats
- Qwen MoE profile carries thinking/template caveats
- DeepSeek profile is experimental and not mainline
- no banned readiness/parity wording is introduced

Run:

```bash
.venv/bin/python -m pytest -q tests/test_model_profile.py
.venv/bin/python -m pytest -q tests/test_model_release_candidate_surface.py
.venv/bin/python -m py_compile owlmlx/model_profile.py
git diff --check
```

If optional runner/schema wiring is added, run the relevant existing tests too.

## 7. Deliverables

Create or update:

- profile module and tests
- handoff:
  `files/execution-prompts/owlmlx/owlmlx-model-profile-resolver-p0-gemma-qwen-mainline-handoff.md`

Optional:

- source-of-truth doc if the contract needs more than code constants
- execution-plan note if the profile surface is complete

## 8. Final Report

Return:

- outcome label
- files changed
- profile ids added
- optional wiring completed or deferred
- tests run and results
- next recommended live evidence lane
