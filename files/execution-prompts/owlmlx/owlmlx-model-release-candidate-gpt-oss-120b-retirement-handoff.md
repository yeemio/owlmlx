# owlmlx Model RC gpt-oss-120b Retirement Handoff

> Status: completed
> Date: 2026-05-05
> Outcome: `owlmlx_model_rc_gpt_oss_120b_retired_and_deleted`
> Scope: remove `gpt-oss-120b-MXFP4-Q4` from the active owlmlx Model RC gate,
> runtime visibility registry, and local model assets

## 1. Decision

`gpt-oss-120b-MXFP4-Q4` is no longer part of the active owlmlx Model RC
program.

It is:

- not a mainline release-candidate model
- not a heavyweight pressure canary
- not runtime-visible
- deleted from the local base-model asset root

The replacement pressure/adaptation split is:

- `DeepSeek-V4-Flash-2bit-DQ`: pressure and adapter optimization lane
- `DeepSeek-V4-Flash-4bit`: experimental-only lane

## 2. Local Asset Result

Deleted path:

```text
/Users/yeemio/AI/Agent/models/gpt-oss-120b-MXFP4-Q4
```

Pre-delete observed size:

```text
58G
```

Post-delete check:

```text
local_asset_deleted=true
```

## 3. Runtime Visibility Result

`owlmlx.runtime_model_visibility.DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS`
no longer contains `gpt-oss-120b-MXFP4-Q4`.

Live `127.0.0.1:8066` was restarted in tmux session
`owlmlx-8066-preview` so the diagnostic surface uses the updated registry.

Observed live result:

```text
openai_model_ids ['Qwen3.6-27B', 'Qwen3.6-35B-A3B', 'gemma-4-31B-it']
openai_contains_gpt_oss_120b False
visibility_model_ids ['Qwen3.6-27B', 'Qwen3.6-35B-A3B', 'gemma-4-31B-it']
visibility_contains_gpt_oss_120b_entry False
model_count 3
```

## 4. Model RC Matrix Result

A0 dry-run matrix now emits exactly four active records:

```text
Qwen3.6-27B
Qwen3.6-35B-A3B
gemma-4-31B-it
DeepSeek-V4-Flash-2bit-DQ
```

`gpt-oss-120b-MXFP4-Q4` is not emitted.

## 5. Files Updated

- `owlmlx/runtime_model_visibility.py`
- `tests/test_runtime_model_visibility.py`
- `docs/source-of-truth/runtime-model-visibility-contract.md`
- `docs/source-of-truth/model-release-candidate-program.md`
- `docs/source-of-truth/deepseek-v4-flash-adapter-optimization-candidate.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/ownership-boundary.md`
- `docs/source-of-truth/model-line-placement.md`
- `docs/source-of-truth/roadmap.md`
- `docs/source-of-truth/capability-absorption-inventory.md`
- `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-goal-contract.md`
- `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a0-evidence-schema-and-runner.md`
- `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a0-evidence-schema-and-runner-handoff.md`
- `files/execution-prompts/owlmlx/owlmlx-owlcoda-model-visibility-truth-cutover-contract.md`
- `files/execution-prompts/owlmlx/owlcoda-direct-owlmlx-model-visibility-cutover.md`

Historical evidence files were not rewritten.

## 6. Verification

```text
pytest -q tests/test_runtime_model_visibility.py
5 passed

pytest -q tests/test_model_release_candidate_surface.py
13 passed

pytest -q tests/test_runtime_server.py -k "model_visibility or model_release_candidate or runtime_status"
1 passed, 40 deselected

python3 -m py_compile owlmlx/runtime_model_visibility.py owlmlx/model_release_candidate_schema.py owlmlx/model_release_candidate_record.py scripts/runtime_model_release_candidate.py owlmlx/runtime/server.py
OK
```

Live checks:

```text
GET /v1/openai/models
gpt-oss-120b-MXFP4-Q4 absent

GET /v1/runtime/model-visibility
gpt-oss-120b-MXFP4-Q4 absent
```

## 7. Non-Goals

This round did not:

- delete `gpt-oss-20b-MXFP4-Q4`
- delete historical evidence mentioning `gpt-oss-120b-MXFP4-Q4`
- make DeepSeek 2bit-DQ supported
- promote DeepSeek 4bit beyond experimental-only
- touch legacy ports `8001` or `8009`
