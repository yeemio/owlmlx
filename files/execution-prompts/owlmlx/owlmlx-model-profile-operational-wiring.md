# owlmlx Model Profile Operational Wiring

> Executor: A
> Date: 2026-05-05
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Outcome target: `owlmlx_model_profile_operational_wiring_introduced`

## 1. Goal

Make the existing `owlmlx.model_profile` resolver operational inside the Model
RC live runner, while keeping the change lightweight and testable without any
heavy model load.

The current P0 resolver is useful but mostly descriptive. This round should
turn it into an opt-in source of effective runner decisions and evidence
metadata.

## 2. Scope

Owned files may include:

- `scripts/runtime_model_release_candidate.py`
- `owlmlx/model_profile.py`
- `tests/test_model_profile.py`
- `tests/test_model_release_candidate_surface.py`
- `docs/source-of-truth/model-release-candidate-program.md`
- one handoff under `files/execution-prompts/owlmlx/`

Do not edit OwlOps, OwlCoda, `/Users/yeemio/AI/Agent`, or peer runtime repos.

## 3. Required Behavior

Add an opt-in profile application path to the live Model RC runner.

Minimum acceptable shape:

- Add a clear CLI switch such as `--apply-model-profile-defaults`.
- When the switch is off, preserve existing command behavior.
- When the switch is on:
  - resolve `ModelProfile` from `model_id`
  - select an effective request mode from profile policy where safe
  - preserve explicit CLI overrides
  - write an `effective_generation_policy` block into `runner-config.json`
  - include profile caveats in `quality_caveats` or an equivalent record field
    already allowed by the schema
  - keep unknown models conservative

Suggested initial policy:

- Qwen3.6 text and Qwen3.6 MoE: prefer chat-template HTTP path unless explicitly
  overridden, because reasoning/template behavior is part of the blocker.
- Gemma4 text: prefer chat-template HTTP path and mark channel/reasoning cleanup
  caveats explicitly.
- DeepSeek V4: keep experimental profile label; do not route it into mainline.
- Unknown: do not inherit mainline defaults.

If `stop_token_strings` cannot be passed through the current HTTP surface, do
not fake support. Record it as `profile_stop_tokens_not_applied` or equivalent
honest caveat.

## 4. Tests

Required:

```bash
.venv/bin/python -m pytest -q tests/test_model_profile.py
.venv/bin/python -m pytest -q tests/test_model_release_candidate_surface.py
.venv/bin/python -m py_compile owlmlx/model_profile.py scripts/runtime_model_release_candidate.py
git diff --check -- scripts/runtime_model_release_candidate.py owlmlx/model_profile.py tests/test_model_profile.py tests/test_model_release_candidate_surface.py docs/source-of-truth/model-release-candidate-program.md
```

Add tests for:

- default behavior unchanged when the opt-in switch is absent
- Qwen profile chooses effective chat-template path when opted in
- Gemma profile records channel/reasoning caveats when opted in
- explicit CLI `--request-mode` and `--prompt-template-id` are preserved
- unknown model stays conservative

## 5. Hard Rules

- No heavy model load.
- No external repo edit.
- No peer-runtime code vendoring.
- Do not describe oMLX, vMLX, or vllm-mlx as upstreams.
- Do not make current release-ready, parity, production-grade, superior, or
  equivalent claims.
- Preserve unrelated dirty/staged work.
- Stage only lane-owned files.

## 6. Final Response

Report:

- outcome label
- files changed
- tests/checks and results
- exact effective policy behavior added
- whether staged
- blockers or deferred live proof
- confirmation that no heavy model load or external repo edit occurred
