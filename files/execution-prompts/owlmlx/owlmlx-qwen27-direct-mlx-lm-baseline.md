# owlmlx Qwen27 Direct MLX-LM Baseline

> Coordinator: owlmlx
> Date: 2026-05-05
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Outcome label: choose one of
> `owlmlx_qwen27_direct_mlx_lm_baseline_completed` or
> `owlmlx_qwen27_direct_mlx_lm_baseline_still_blocked`

## 1. Goal

Determine whether `Qwen3.6-27B` slow decode is caused by the shared MLX-LM
substrate/profile or by owlmlx wrapper/runtime streaming overhead.

This is a live evidence lane and is the only heavy model lane in the current
parallel packet.

## 2. Required Reading

Read first:

1. `AGENTS.md`
2. `docs/source-of-truth/model-release-candidate-program.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md`
5. current `scripts/runtime_model_release_candidate.py`

## 3. Hard Boundaries

- Do not modify runtime code.
- Do not modify external repos.
- Do not stop or kill `8001` or `8009`.
- Do not overlap with another heavy model load.
- Use `/tmp/owlmlx-model-rc-heavy.lock` or an equivalent lock discipline.
- Preserve existing staged and dirty work.
- Do not append a stronger Model RC verdict.
- Do not claim pass, release-ready, parity, replacement, equivalent, beats,
  wins, or matches.

## 4. Preflight

Before loading anything:

```bash
pwd
.venv/bin/python - <<'PY'
import importlib.util, sys
print(sys.executable)
print("mlx", importlib.util.find_spec("mlx") is not None)
print("mlx_lm", importlib.util.find_spec("mlx_lm") is not None)
PY
curl -s http://127.0.0.1:8066/healthz
curl -s http://127.0.0.1:8066/v1/openai/models
lsof -n -iTCP:8066 -sTCP:LISTEN
test ! -e /tmp/owlmlx-model-rc-heavy.lock
```

If the lock exists or the host is already running another heavy lane, stop and
return `still_blocked`.

## 5. Evidence Directory

Create one evidence directory under:

`files/evidence/owlmlx/model-release-candidates/`

Suggested name:

`<timestamp>-qwen36-27b-direct-mlx-lm-baseline`

Archive:

- preflight output
- direct MLX-LM command/config
- owlmlx HTTP command/config
- stdout/stderr
- RSS samples
- timing summary
- comparison summary
- post-run healthz and process cleanup checks

## 6. Required Comparison

Use the same:

- model path: `/Users/yeemio/AI/Agent/models/Qwen3.6-27B`
- prompt: `In one short sentence, define local AI.`
- max tokens: `32`
- temperature: `0`
- repeat count: at least `2` for each path if memory and runtime remain stable

Path A: direct `mlx_lm.stream_generate`

- use `.venv/bin/python`
- measure TTFT, decode tokens/s, wall time, peak process-tree RSS if possible
- capture generated text and finish reason if available

Path B: owlmlx HTTP streaming

- use `http://127.0.0.1:8066`
- use existing `scripts/runtime_model_release_candidate.py`
- keep `memory_gb = 56`
- produce Model RC-compatible evidence if possible

## 7. Decision Logic

If direct MLX-LM is materially faster while owlmlx HTTP remains slow:

- classify the next blocker as `owlmlx_wrapper_stream_overhead_or_runtime_path`

If direct MLX-LM is also slow:

- classify the next blocker as `model_profile_or_mlx_lm_baseline_decode`

If direct MLX-LM fails but owlmlx HTTP succeeds:

- classify as `direct_baseline_harness_incomplete`, not as owlmlx pass

If both fail:

- classify as `qwen27_live_baseline_blocked`

## 8. Deliverables

Create:

- evidence directory
- `files/execution-prompts/owlmlx/owlmlx-qwen27-direct-mlx-lm-baseline-handoff.md`

Optional:

- append a short execution-plan note only if the evidence is complete

Do not update the Model RC cumulative ledger unless you create a valid existing
schema record and the verdict remains honest.

## 9. Verification

Run:

```bash
.venv/bin/python -m pytest -q tests/test_model_release_candidate_surface.py
.venv/bin/python -m py_compile scripts/runtime_model_release_candidate.py
git diff --check
curl -s http://127.0.0.1:8066/healthz
lsof -n -iTCP:8066 -sTCP:LISTEN
```

Confirm no lane-owned direct MLX-LM process remains after the run.

## 10. Final Report

Return:

- outcome label
- direct MLX-LM TTFT / decode tokens/s / wall time / peak RSS
- owlmlx HTTP TTFT / decode tokens/s / wall time / peak RSS
- blocker classification from section 7
- files written
- verification results
