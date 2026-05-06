# owlmlx Model Release Candidate D1 - DeepSeek V4 Flash 2bit-DQ Pressure Adapter

Repo: `/Users/yeemio/AI/gitrep/owlmlx`

Date: 2026-05-05

## Objective

Run the first isolated pressure/adaptation lane for
`DeepSeek-V4-Flash-2bit-DQ`.

Target model:

- `DeepSeek-V4-Flash-2bit-DQ`

Expected outcome:

`owlmlx_model_release_candidate_d1_deepseek_v4_flash_2bit_dq_pressure_record_introduced`

## Required Context

Read first:

1. `docs/source-of-truth/model-release-candidate-program.md`
2. `docs/source-of-truth/deepseek-v4-flash-adapter-optimization-candidate.md`
3. `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-gpt-oss-120b-retirement-handoff.md`
4. `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-a1-qwen36-27b-live-record-handoff.md`
5. `docs/source-of-truth/release-readiness-execution-plan.md`

## Coordination Gate

Do not start D1 until all active mainline memory-exclusive lanes are idle.

D1 may run after A2/A3 if the coordinator wants the mainline loop first, or
between mainline lanes only when no OwlOps/live-model consumer depends on a
stable `8066` latest view.

## Scope

This is not a mainline pass/fail lane. It is the pressure and adapter
optimization lane.

The target record must preserve:

- visibility status remains `not_registered` unless a separate registration
  round explicitly changes it
- lane remains `flagship_experimental`
- verdict may be `experimental_only`, `needs_optimization`, or `blocked`
- never use verdict `pass`

## Runtime

Use the isolated DeepSeek runtime already documented:

```text
/Users/yeemio/AI/gitrep/owlmlx/.runtime-deepseek-v4-mlx/bin/python
```

Artifact:

```text
/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ
```

Do not use the 4bit artifact as the pressure line. The 4bit artifact remains
experimental-only until a separate host-fit proof replaces the current exit-137
truth.

## Required Evidence

Capture and preserve:

- load/start result
- short generation result
- repeat count
- failure count
- wall-clock time
- process-tree peak RSS
- memory headroom
- output sanity label
- adapter/runtime blockers
- unload/reclaim result if the runtime exposes one
- artifact directory under `files/evidence/owlmlx/model-release-candidates/`

## Suggested Command Shape

If no HTTP adapter exists yet, use the isolated `mlx_lm.generate` command and
record the result as an experimental Model RC record without pretending it came
from the mainline HTTP surface:

```bash
EVIDENCE_DIR="files/evidence/owlmlx/model-release-candidates/<timestamp>-deepseek-v4-flash-2bit-dq"

/Users/yeemio/AI/gitrep/owlmlx/.runtime-deepseek-v4-mlx/bin/python -m mlx_lm.generate \
  --model /Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ \
  --prompt "Write one short sentence about local AI." \
  --max-tokens 64 \
  --temp 0.0 \
  --max-kv-size 512 \
  --kv-bits 4 \
  --kv-group-size 64
```

If a narrow operator subcommand is added for DeepSeek, it must write a
schema-valid `owlmlx.model_release_candidate_record` with:

```text
model_id = DeepSeek-V4-Flash-2bit-DQ
lane = flagship_experimental
visibility_status = not_registered
verdict != pass
```

## Tests And Verification

Run any new tests for the DeepSeek operator path, plus:

```bash
pytest -q tests/test_model_release_candidate_surface.py
python3 -m py_compile scripts/runtime_model_release_candidate.py
git diff --check
```

Live verification:

- process-tree RSS is GB-scale and matches the pressure-lane expectation
- no stale DeepSeek process remains after completion
- `8001` and `8009` remain untouched
- `8066` is not remounted as supported DeepSeek visibility

## Out Of Scope

Do not:

- register DeepSeek as supported
- mark DeepSeek `pass`
- run DeepSeek 4bit as the pressure line
- reintroduce `gpt-oss-120b-MXFP4-Q4`
- touch OwlOps / OwlCoda / `/Users/yeemio/AI/Agent` beyond reading the existing
  model artifact
- kill `8001` or `8009`
- claim release-ready, parity, replacement, equivalent, or production-grade

## Final Report

Report:

- outcome label
- changed files
- artifact directory
- runtime command used
- appended record verdict
- measured RSS / headroom / wall-clock
- output sanity label
- adapter blockers
- stale-process cleanup result
- tests and command results
- whether D2 should build a real HTTP adapter or stay isolated
