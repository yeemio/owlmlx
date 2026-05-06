# owlmlx Model RC Post-Run Health Handoff

> Status: continuation handoff, refreshed after live profile-control proof
> Updated: 2026-05-06
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Scope: Model RC admission rerun, post-run health gate, and next continuation

## Purpose

Continue the owlmlx Model Release Candidate gate without inheriting the old
chat window. The active objective is not release. It is to make the mainline
model matrix observable, honest, and safe enough for OwlOps / OwlCoda to
consume later.

The immediate dominant gap is now:

`gemma_final_channel_template_or_serving_boundary_and_ttft_repro`

## Current Verified Truth

Verified from repo files and live commands in this window:

- `Qwen3.6-35B-A3B` completed a supervised admission rerun:
  `files/evidence/owlmlx/model-release-candidates/20260505T162118Z-qwen36-35b-a3b-supervised-admission-rerun/record.json`
- Qwen35 record values:
  `verdict=needs_optimization`, `failure_count=0`, `repeat_count=2`,
  `output_sanity_label=valid_text`, `ttft_ms=1763.931`,
  `decode_tokens_per_second=31.1`,
  `peak_resident_set_bytes=62626299904`.
- The Qwen35 record was appended to
  `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`.
  The mounted history capture showed `record_count=9` and Qwen35 as latest:
  `files/evidence/owlmlx/model-release-candidates/20260505T162923Z-post-run-health-gate-and-8066-restart/http-history-after-append-compact.json`.
- `gemma-4-31B-it` completed two supervised repeats, but the post-run runtime
  health was dirty:
  `files/evidence/owlmlx/model-release-candidates/20260505T162236Z-gemma-4-31b-it-supervised-admission-rerun/`.
- Gemma record values before the new post-run gate:
  `verdict=needs_optimization`, `failure_count=0`, `repeat_count=2`,
  `output_sanity_label=reasoning_trace_truncated`,
  `decode_tokens_per_second=2.757`,
  `peak_resident_set_bytes=59347599360`.
- Gemma post-run `healthz` was not clean:
  `backend_error = "Expecting ':' delimiter: line 1 column 37 (char 36)"`.
- Because that Gemma record was generated before the post-run health gate, it
  was not appended to the cumulative ledger as a clean row.

Continuation update from 2026-05-06 10:08-10:14 Asia/Shanghai:

- `8066` was restarted persistently in tmux session
  `owlmlx-8066-model-rc-20260506` and verified clean before the Gemma rerun:
  `healthz.ok=true`, `backend_error=null`, `active_model_id=null`.
- Host pressure was normal and Gemma model-load admission returned `admit`.
- Two early local attempts are preserved as evidence directories but are not
  part of the cumulative ledger:
  `20260506T020854Z-gemma-4-31b-it-post-run-health-rerun` and
  `20260506T020855Z-gemma-4-31b-it-post-run-health-gate-rerun`. The first
  omitted `memory_gb`; the second requested `128G` and correctly exceeded the
  `116G` serving budget.
- The runner was tightened so, when `--memory-gb` is absent, it derives
  `memory_gb` from admission `known_peak_resident_set_bytes` and records the
  exact `/v1/load` request payload in `repeat-XX-load.json`.
- A transient blocked Gemma row is also preserved at
  `20260506T021034Z-gemma-4-31b-it-post-run-health-gate-rerun`: first repeat
  succeeded, second unload returned `model_not_loaded`, and post-run health
  remained `ok=true` with `backend_error=null`.
- The previous clean Gemma row was
  `files/evidence/owlmlx/model-release-candidates/20260506T021105Z-gemma-4-31b-it-post-run-health-gate-rerun/record.json`.
  It used explicit `--memory-gb 60`, recorded `memory_gb=60.0` in the load
  request payload, completed two repeat cycles, appended to
  `cumulative-ledger.jsonl`, and left post-run health clean.
- Previous clean Gemma record values:
  `verdict=needs_optimization`, `failure_count=0`, `repeat_count=2`,
  `output_sanity_label=reasoning_trace_truncated`, `ttft_ms=51229.148`,
  `decode_tokens_per_second=14.744`,
  `peak_resident_set_bytes=50295062528`.
- The old `gemma_post_run_backend_unhealthy_transport_capture` gap should not
  be reopened unless a new run reproduces `post_run_backend_unhealthy`.

Parallel follow-up from 2026-05-06:

- Gemma visible reasoning output now has a pure runtime-owned policy helper:
  `owlmlx.reasoning_trace_policy:v1`. It detects `<|channel>thought`,
  `<|channel>final`, and `<think>` traces, returns structured trace truth, and
  only exposes a `final_text` candidate when it is safely outside a visible
  reasoning boundary.
- The Model RC runner now writes `reasoning_trace_policy` into each
  `repeat-XX-generation.json` evidence file, so visible reasoning traces are
  not silently promoted to `valid_text`.
- The Model RC runner now writes a per-repeat `timing_breakdown` object with
  `load_elapsed_ms`, `stream_request_wall_ms`, `first_token_latency_ms`,
  `post_first_token_decode_wall_ms`, queue wait, and token counts.
- The first fresh heavy Gemma row with these fields is
  `files/evidence/owlmlx/model-release-candidates/20260506T024418Z-gemma-4-31b-it-final-answer-control-rerun/record.json`.
  It applied Gemma profile defaults plus experimental final-answer-only
  prompt-control, completed two repeats, appended to `cumulative-ledger.jsonl`,
  and left post-run health clean.
- The follow-up stop-request-payload row is now the latest Gemma truth:
  `files/evidence/owlmlx/model-release-candidates/20260506T-mainline-gemma-stop-request-payload-rerun/record.json`.
  It applied profile stop tokens through the HTTP generation payload as
  `stop=["<eos>", "<turn|>"]`, recorded the actual generation
  `request_payload` in repeat evidence, completed two repeats, appended to
  `cumulative-ledger.jsonl`, and left post-run health clean.
- Current latest Gemma record values:
  `verdict=needs_optimization`, `failure_count=0`, `repeat_count=2`,
  `output_sanity_label=reasoning_trace_truncated`, `ttft_ms=24322.913`,
  `decode_tokens_per_second=7.688`,
  `peak_resident_set_bytes=33050263552`.
- The live profile-control and stop-token-control proofs did not suppress Gemma's
  `<|channel>thought` output. `reasoning_trace_policy` correctly reports
  `trace_status=truncated`, `visible_reasoning_trace=true`, and
  `final_text=null`. This makes simple user-message prompt-control and profile
  stop-token application insufficient as platform fixes.
- Repeat-level timing now separates the latest stream path:
  repeat 1 first token `41946.062ms`, post-first-token decode wall
  `8198.837ms`; repeat 2 first token `6699.764ms`, post-first-token decode wall
  `8451.346ms`. The earlier `51.2s` average TTFT spike was not reproduced as an
  average, but the first repeat reproduced a large pre-first-token stall.

Code changes staged in this window:

- `scripts/runtime_model_release_candidate.py` now writes
  `post-run-healthz.json` and `post-run-runtime-status.json`, and records
  `post_run_backend_unhealthy` as a blocking signal. The follow-up patch also
  derives load `memory_gb` from model-load admission when the CLI does not
  provide one, stores the actual load request payload in evidence, records
  `reasoning_trace_policy`, records `timing_breakdown` per repeat, and adds an
  opt-in Gemma final-answer-only prompt-control experiment when profile defaults
  are applied. The latest patch records the actual generation `request_payload`
  per repeat and applies profile stop tokens through HTTP generation params.
- `owlmlx/reasoning_trace_policy.py` adds the runtime-owned trace-routing
  policy used by the runner and Gemma profile.
- `owlmlx/model_profile.py` points the Gemma profile at
  `owlmlx.reasoning_trace_policy:v1` and keeps final-text extraction
  conservative.
- `owlmlx/runtime/mlx_lm_subprocess_backend.py` records successful shutdown as
  the latest subprocess result and clears a prior latched transport error after
  a normal successful unload when no model remains registered.
- `tests/test_model_release_candidate_surface.py` covers dirty post-run health
  turning into `blocked`, trace policy evidence, timing evidence, and the Gemma
  prompt-control request shape.
- `tests/test_mlx_lm_subprocess_backend.py` covers successful unload clearing a
  prior latched error.
- `docs/source-of-truth/model-release-candidate-program.md` documents the
  post-run health gate.
- Detailed round handoff:
  `files/execution-prompts/owlmlx/owlmlx-model-rc-supervised-admission-rerun-and-post-run-health-gate-handoff.md`.

Verification commands already run:

```bash
pytest -q tests/test_model_release_candidate_surface.py -q
pytest -q tests/test_mlx_lm_subprocess_backend.py -k 'successful_unload_clears_prior_latched_error or unload_stops_persistent_child or unload_clears_stale_registration_after_dead_child or classifies_metal_oom_child_loss'
pytest -q tests/test_runtime_server.py -k 'healthz or model_release_candidate'
python3 -m py_compile scripts/runtime_model_release_candidate.py owlmlx/runtime/mlx_lm_subprocess_backend.py
git diff --check -- scripts/runtime_model_release_candidate.py owlmlx/runtime/mlx_lm_subprocess_backend.py tests/test_model_release_candidate_surface.py tests/test_mlx_lm_subprocess_backend.py docs/source-of-truth/model-release-candidate-program.md files/execution-prompts/owlmlx/owlmlx-model-rc-supervised-admission-rerun-and-post-run-health-gate-handoff.md
```

Observed results:

- Model RC surface tests: `30 passed`
- Subprocess backend narrow regression: `4 passed, 51 deselected`
- Runtime server health / Model RC narrow test: `1 passed, 42 deselected`
- `py_compile`: clean
- targeted `git diff --check`: clean

Verification after the live profile-control proof and doc refresh:

```bash
./.venv/bin/python -m pytest -q tests/test_reasoning_trace_policy.py tests/test_model_profile.py tests/test_model_release_candidate_surface.py -q
./.venv/bin/python -m pytest -q tests/test_mlx_lm_subprocess_backend.py -k 'successful_unload_clears_prior_latched_error or unload_stops_persistent_child or unload_clears_stale_registration_after_dead_child or classifies_metal_oom_child_loss'
./.venv/bin/python -m pytest -q tests/test_runtime_server.py -k 'healthz or model_release_candidate'
./.venv/bin/python -m py_compile scripts/runtime_model_release_candidate.py owlmlx/reasoning_trace_policy.py owlmlx/model_profile.py owlmlx/runtime/mlx_lm_subprocess_backend.py
git diff --check -- docs/handoff/owlmlx-model-rc-post-run-health-handoff-20260506.md docs/source-of-truth/model-release-candidate-program.md docs/source-of-truth/release-readiness-execution-plan.md scripts/runtime_model_release_candidate.py owlmlx/reasoning_trace_policy.py owlmlx/model_profile.py tests/test_reasoning_trace_policy.py tests/test_model_profile.py tests/test_model_release_candidate_surface.py files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl
curl -sS --max-time 10 http://127.0.0.1:8066/healthz
```

Observed results:

- Trace/profile/Model RC surface tests: `47 passed`
- Subprocess backend narrow regression: `4 passed, 51 deselected`
- Runtime server health / Model RC narrow test: `1 passed, 42 deselected`
- `py_compile`: clean
- targeted `git diff --check`: clean
- live `8066 /healthz`: `ok=true`, `backend_error=null`,
  `active_model_id=null`, `model_count=0`

## What Not To Reopen

- Do not re-argue whether owlmlx is merely an oMLX/vMLX patch stack. Project
  truth says owlmlx is its own runtime; oMLX/vMLX are peer reference inputs.
- Do not claim release-ready, parity, replacement, equivalent, production-grade,
  wins, beats, or matches.
- Do not kill old services on `8001` or `8009`.
- Do not run Qwen35 / Gemma / DeepSeek concurrently.
- Do not append the dirty Gemma record as a clean cumulative-ledger row.
- Do not let OwlCoda own runtime truth; OwlCoda should consume owlmlx/OwlOps
  truth only after the Model RC gate is honestly passable.

## Current Runtime / Deployment

Last live check in this continuation:

- `8066` is listening from tmux session `owlmlx-8066-model-rc-20260506`.
- `8001` is still listening and was not killed.
- `8009` is still listening and was not killed.

Current `8066` health after the latest Gemma run is clean:
`healthz.ok=true`, `backend_error=null`, `active_model_id=null`,
`model_count=0`.

Suggested 8066 start command:

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
mkdir -p /Users/yeemio/AI/gitrep/owlmlx/files/evidence/owlmlx/runtime-test-runs
./.venv/bin/python scripts/runtime_technical_preview_server.py \
  --host 127.0.0.1 \
  --port 8066 \
  --models-root /Users/yeemio/AI/Agent/models \
  --backend-timeout-s 900 \
  --model-release-candidate-ledger-path /Users/yeemio/AI/gitrep/owlmlx/files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl \
  --runtime-test-run-ledger-path /Users/yeemio/AI/gitrep/owlmlx/files/evidence/owlmlx/runtime-test-runs/audit-ledger.jsonl \
  --log-level warning
```

Run it in a persistent terminal/session if the next work needs live HTTP.

## Important Files

- `docs/source-of-truth/model-release-candidate-program.md`
- `scripts/runtime_model_release_candidate.py`
- `owlmlx/runtime/mlx_lm_subprocess_backend.py`
- `tests/test_model_release_candidate_surface.py`
- `tests/test_mlx_lm_subprocess_backend.py`
- `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`
- `files/evidence/owlmlx/model-release-candidates/20260505T162118Z-qwen36-35b-a3b-supervised-admission-rerun/`
- `files/evidence/owlmlx/model-release-candidates/20260505T162236Z-gemma-4-31b-it-supervised-admission-rerun/`
- `files/evidence/owlmlx/model-release-candidates/20260505T162923Z-post-run-health-gate-and-8066-restart/`
- `files/evidence/owlmlx/model-release-candidates/20260506T021034Z-gemma-4-31b-it-post-run-health-gate-rerun/`
- `files/evidence/owlmlx/model-release-candidates/20260506T021105Z-gemma-4-31b-it-post-run-health-gate-rerun/`
- `files/evidence/owlmlx/model-release-candidates/20260506T024418Z-gemma-4-31b-it-final-answer-control-rerun/`
- `files/evidence/owlmlx/model-release-candidates/20260506T-mainline-gemma-stop-token-control-rerun/`
- `files/evidence/owlmlx/model-release-candidates/20260506T-mainline-gemma-stop-request-payload-rerun/`
- `files/execution-prompts/owlmlx/owlmlx-model-rc-supervised-admission-rerun-and-post-run-health-gate-handoff.md`

## Known Gaps

- Gemma's latest post-run backend health is clean, so the prior dirty transport
  gap is no longer the active blocker unless it reproduces.
- Gemma still emits visible `<|channel>thought` reasoning traces and truncates
  at length under the profile-default OpenAI chat stream path even after the
  experimental final-answer-only user-message prompt-control and profile
  stop-token application.
- The output-cleanliness root cause is no longer "we never asked the platform to
  suppress thoughts" or "we never passed stop tokens." The platform applied
  both controls and they were insufficient. The next boundary is stronger
  chat-template / final-channel / serving control versus true model behavior
  requiring a different model path.
- Gemma TTFT remains volatile across rows. The latest stop-request-payload run
  averaged `ttft_ms=24322.913`; the prior clean rows averaged `2824.079`,
  `5104.511`, and `51229.148`. The latest row shows repeat 1 first token at
  `41.9s` and repeat 2 at `6.7s`, while post-first-token decode stayed around
  `8.2s-8.5s`.
- The cumulative ledger now contains one honest blocked Gemma attempt before
  the latest clean Gemma row; consumers should use latest-per-model policy,
  not assume every historical row is clean.
- The worktree is very dirty and heavily staged from many prior Model RC /
  Phase45 lanes. Do not use `git add .`. Stage only explicit files.
- `README.md`, several Phase45 docs/modules, and other unrelated dirty files
  existed before this handoff and should not be swept into the next narrow
  commit unless separately reviewed.

## Next Dominant Gap

`gemma_final_channel_template_or_serving_boundary_and_ttft_repro`

Recommended order:

1. Keep `8066` live only if the next work needs HTTP; otherwise do not broaden
   lifecycle work.
2. Do not rerun heavy Gemma just to reproduce the clean post-run health row.
3. Do not repeat the same final-answer-only user-message prompt-control or
   profile stop-token-control as if either were untested. Both have live
   evidence and are insufficient.
4. Select the smallest stronger Gemma control: template-level final-channel
   framing or a serving path that can separate thought/final channels without
   hiding failures.
5. Use `request_payload` and `timing_breakdown` evidence to reproduce or falsify
   the earlier `51.2s` average TTFT spike. Current latest evidence shows a
   repeat-level first-token spread from `6.7s` to `41.9s` with a steadier
   post-first-token decode wall component around `8.2s-8.5s`.
6. Only return to raw child transport capture if a new row records
   `post_run_backend_unhealthy`.

## Suggested First Commands

```bash
cd /Users/yeemio/AI/gitrep/owlmlx

git status --short

lsof -n -iTCP:8066 -sTCP:LISTEN || true
lsof -n -iTCP:8001 -sTCP:LISTEN || true
lsof -n -iTCP:8009 -sTCP:LISTEN || true

pytest -q tests/test_model_release_candidate_surface.py -q
pytest -q tests/test_mlx_lm_subprocess_backend.py -k 'successful_unload_clears_prior_latched_error or unload_stops_persistent_child or unload_clears_stale_registration_after_dead_child or classifies_metal_oom_child_loss'

python3 -m py_compile scripts/runtime_model_release_candidate.py owlmlx/runtime/mlx_lm_subprocess_backend.py
```

After 8066 is started:

```bash
curl -sS --max-time 10 http://127.0.0.1:8066/healthz | python3 -m json.tool
curl -sS --max-time 10 -X POST http://127.0.0.1:8066/v1/runtime/host-pressure-sample | python3 -m json.tool
curl -sS --max-time 10 'http://127.0.0.1:8066/v1/runtime/model-load-admission?model_id=gemma-4-31B-it' | python3 -m json.tool
```

## Starter Prompt For New Window

```text
You are in /Users/yeemio/AI/gitrep/owlmlx. Read AGENTS.md and docs/handoff/owlmlx-model-rc-post-run-health-handoff-20260506.md first. Continue the owlmlx Model RC loop from the dominant gap `gemma_final_channel_template_or_serving_boundary_and_ttft_repro`.

Rules: do not kill 8001/8009; do not run heavy models in parallel; do not claim release-ready/parity/replacement/equivalent/production-grade; do not use `git add .`; preserve unrelated dirty/staged work.

First verify git status and whether 8066 is listening. Treat the latest Gemma row at `20260506T-mainline-gemma-stop-request-payload-rerun` as the current runtime truth: post-run backend health is clean, final-answer-only profile prompt-control and profile stop tokens were applied through the HTTP generation payload, but output is still `reasoning_trace_truncated` with visible `<|channel>thought` and no safe `final_text`. The latest row carries live `request_payload`, `reasoning_trace_policy`, and `timing_breakdown`: first-token latency split from `41.9s` on repeat 1 to `6.7s` on repeat 2, while post-first-token decode wall time stayed around `8.2s-8.5s`. Do not repeat the same prompt-control or stop-token-control as if untested. The next closure round should test stronger template/final-channel/serving-channel control or establish the model-behavior boundary honestly; only reopen raw transport capture if a new run records `post_run_backend_unhealthy`.
```
