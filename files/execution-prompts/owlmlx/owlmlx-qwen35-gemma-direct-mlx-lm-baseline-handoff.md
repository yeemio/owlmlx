# owlmlx Qwen35 And Gemma Direct MLX-LM Baseline Handoff

> Executor: C
> Date: 2026-05-05
> Outcome label: `owlmlx_qwen35_gemma_direct_mlx_lm_baseline_live_run_incomplete`
> Evidence dir:
> `files/evidence/owlmlx/model-release-candidates/20260505T144321Z-qwen35-gemma-direct-mlx-lm-baseline`

## Scope

This lane ran the archived Qwen35/Gemma direct `mlx_lm` baseline prompt.

No runtime code was modified. No OwlOps, OwlCoda, AI/Agent, peer runtime, or
external repository was edited. Existing staged and dirty work was preserved.

The heavy lane lock `/tmp/owlmlx-model-rc-heavy.lock` was acquired before model
load and removed after cleanup evidence was captured.

## Direct MLX-LM Results

Direct generation used:

- API: `mlx_lm.load` plus `mlx_lm.stream_generate`
- prompt: `In one short sentence, define local AI.`
- repeats: `2`
- max tokens: `64`
- temperature: `0`, applied through `mlx_lm.sample_utils.make_sampler(temp=0.0)`
- chat template: applied through `apply_chat_template(tokenize=False, add_generation_prompt=True)` for both models

The first direct attempt recorded that this installed `mlx_lm` rejected the
legacy `temp` keyword. The successful direct summaries supersede that failed
attempt and preserve the API note in evidence.

| Model | Direct status | Mean TTFT | Decode tokens/s | E2E tokens/s | Mean wall | Peak RSS | Output sanity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `Qwen3.6-35B-A3B` | completed | `11944.939 ms` | `26.412` | `13.068` | `14301.007 ms` | `35254009856` | `valid_text` |
| `gemma-4-31B-it` | completed | `5750.583 ms` | `3.247` | `1.956` | `12882.066 ms` | `41497346048` | `valid_text` |

Qwen35 direct raw preview started with a visible planning-style answer
(`Here's a thinking process...`). Gemma direct answered the requested one
sentence cleanly.

## HTTP Results

Qwen35 HTTP was started through the existing `127.0.0.1:8066` listener using
the Model RC runner and model-profile defaults:

```bash
.venv/bin/python scripts/runtime_model_release_candidate.py \
  --ledger-path "$EVID/qwen35-http/ledger.jsonl" \
  run-live-http-mainline \
  --runtime-url http://127.0.0.1:8066 \
  --model-id Qwen3.6-35B-A3B \
  --artifact-path /Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B \
  --prompt 'In one short sentence, define local AI.' \
  --max-tokens 64 \
  --temperature 0 \
  --repeats 2 \
  --memory-gb 67 \
  --evidence-dir "$EVID/qwen35-http" \
  --http-timeout-s 1200 \
  --rss-sample-interval-s 0.5 \
  --apply-model-profile-defaults
```

Observed Qwen35 HTTP state:

- load succeeded in `22858.572 ms`
- first stream artifact stayed empty: `qwen35-http/repeat-01-stream.ndjson`
- runner exited with `TimeoutError` while reading the chunked SSE response
- final `healthz` reported `readiness=blocked`, `active_model_id=Qwen3.6-35B-A3B`, and `backend_error=[Errno 32] Broken pipe`

Gemma HTTP was not started. Starting another HTTP load against the shared
`8066` after the Qwen35 timeout would have violated the lane discipline because
the resident service was already blocked.

## Classification

`Qwen3.6-35B-A3B`: `live_run_incomplete`

Reason: direct `mlx_lm` completed with chat template, but owlmlx HTTP loaded
the model and then timed out without any stream events. There is no complete
direct-versus-HTTP metric delta to claim from this lane.

`gemma-4-31B-it`: `live_run_incomplete`

Reason: direct `mlx_lm` completed with chat template, but the Gemma HTTP run was
not safe to start after the prior Qwen35 HTTP run left shared `8066` blocked.

## Cleanup

Cleanup evidence is in `final-cleanup-check.txt`.

- `/tmp/owlmlx-model-rc-heavy.lock` was removed.
- No lane-owned direct `mlx_lm` or `runtime_model_release_candidate.py` process remained.
- Legacy `8001` and `8009` listeners were observed only and not killed.
- Pre-existing `8066` listener PID `4348` remained present and was not killed or restarted.
- Residual shared runtime state remained: `8066` reported blocked Qwen35 state after `/v1/unload` returned `model_not_loaded`.

## Verification

Required checks were run after cleanup and are recorded in `verification.txt`:

```bash
.venv/bin/python -m pytest -q tests/test_model_release_candidate_surface.py
.venv/bin/python -m py_compile scripts/runtime_model_release_candidate.py
git diff --check -- files/evidence/owlmlx/model-release-candidates/20260505T144321Z-qwen35-gemma-direct-mlx-lm-baseline files/execution-prompts/owlmlx/owlmlx-qwen35-gemma-direct-mlx-lm-baseline-handoff.md
```

The cumulative Model RC ledger was not updated.
