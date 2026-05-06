# owlmlx Qwen35 And Gemma Direct MLX-LM Baseline

> Executor: C
> Date: 2026-05-05
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Outcome target: `owlmlx_qwen35_gemma_direct_mlx_lm_baseline_completed`

## 1. Goal

Run a memory-exclusive direct `mlx_lm` versus owlmlx HTTP baseline for:

- `Qwen3.6-35B-A3B`
- `gemma-4-31B-it`

This should determine whether the current TTFT/output-shape blockers are
visible in direct `mlx_lm` too, or whether owlmlx HTTP/generation wrapping is a
material contributor.

## 2. Heavy Lane Rules

- This is the only heavy live lane.
- Before any model load, acquire `/tmp/owlmlx-model-rc-heavy.lock`.
- If the lock exists, stop with a precise blocker.
- Run one model at a time.
- Do not kill legacy `8001` or `8009`.
- Clean up processes and any ports you start.
- Leave existing `8066` alone unless the prompt requires a read-only probe.

## 3. Model Inputs

Use the current local model paths if present:

- `/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B`
- `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`

If a path is missing, record `artifact_missing` for that model and continue to
the next model if safe.

## 4. Required Baseline Shape

For each model:

1. Record preflight:
   - Python executable
   - `mlx` and `mlx_lm` import availability
   - model path size
   - existing listeners on `8001`, `8009`, `8066`
   - host memory snapshot if easily available
2. Run direct `mlx_lm` with the same prompt, max tokens, temperature, and
   repeat count used for the owlmlx HTTP run.
3. Run owlmlx HTTP Model RC runner against `127.0.0.1:8066`.
4. Capture:
   - TTFT
   - decode tokens/s
   - end-to-end tokens/s
   - wall time
   - peak process-tree RSS
   - output sanity label
   - raw text preview
   - failure count
5. Write a comparison summary per model.

Suggested prompts:

- Qwen35: `In one short sentence, define local AI.`
- Gemma: `In one short sentence, define local AI.`

Suggested generation:

- repeats: `2`
- max tokens: `64` for Qwen35 and Gemma unless direct API fails
- temperature: `0`

For Gemma and Qwen direct baselines, attempt to apply the tokenizer chat
template if the installed `mlx_lm`/tokenizer exposes a clear safe path. If not,
record that direct template parity is missing rather than faking it.

## 5. Evidence Layout

Create:

`files/evidence/owlmlx/model-release-candidates/<timestamp>-qwen35-gemma-direct-mlx-lm-baseline/`

Include at minimum:

- `preflight.txt`
- per-model direct stream/summary artifacts
- per-model owlmlx HTTP runner artifacts or linked subdirectories
- `comparison-summary.json`
- `final-cleanup-check.txt`

Create handoff:

`files/execution-prompts/owlmlx/owlmlx-qwen35-gemma-direct-mlx-lm-baseline-handoff.md`

Do not update the cumulative Model RC ledger unless explicitly required by an
existing runner command. Evidence-dir local ledgers are fine.

## 6. Required Verification

Run after cleanup:

```bash
.venv/bin/python -m pytest -q tests/test_model_release_candidate_surface.py
.venv/bin/python -m py_compile scripts/runtime_model_release_candidate.py
git diff --check -- files/evidence/owlmlx/model-release-candidates/<evidence-dir> files/execution-prompts/owlmlx/owlmlx-qwen35-gemma-direct-mlx-lm-baseline-handoff.md
```

Also report:

- whether `/tmp/owlmlx-model-rc-heavy.lock` was removed
- whether any lane-owned direct `mlx_lm`, runner, uvicorn, or model process
  remains
- existing legacy listeners observed but not killed

## 7. Classification

Use one of these honest blocker classifications:

- `shared_mlx_lm_baseline_decode`
- `shared_mlx_lm_baseline_ttft`
- `owlmlx_http_generation_path_overhead`
- `profile_template_output_shape`
- `direct_template_parity_missing`
- `artifact_missing`
- `live_run_incomplete`

Do not force a pass/fail product conclusion from this lane.

## 8. Hard Rules

- Do not edit OwlOps/OwlCoda/AI/Agent.
- Do not edit peer runtime repos.
- Do not describe oMLX, vMLX, or vllm-mlx as upstreams.
- Do not make current release-ready, parity, production-grade, superior, or
  equivalent claims.
- Preserve unrelated dirty/staged work.
- Stage only lane-owned evidence and handoff files.

## 9. Final Response

Report:

- outcome label
- evidence dir
- per-model metrics and classification
- process/port cleanup status
- checks and results
- whether staged
- confirmation that no external repo edit occurred
