# owlmlx Model RC Gemma Chat Template Probe Handoff

> Outcome:
> `owlmlx_model_release_candidate_gemma_chat_template_probe_narrowed`
> Date: 2026-05-05
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`

## 1. Scope

This round returned from OwlOps R166 to the owlmlx mainline.

It did not modify OwlOps, OwlCoda, `/Users/yeemio/AI/Agent`, or legacy
listeners on `8001` / `8009`.

The round targeted the Gemma mainline blocker because
`gemma-4-31B-it` had the strongest current output-quality blocker:
`repetitive_output` under raw `/v1/generate/stream` evidence.

## 2. Code Change

`scripts/runtime_model_release_candidate.py` now supports:

- `--request-mode raw_generate_stream`
- `--request-mode openai_chat_stream`
- `--prompt-template-id <label>`

`openai_chat_stream` routes Model RC live evidence through
`/v1/chat/completions` with:

- `messages = [{"role": "user", "content": prompt}]`
- `stream = true`
- runner-normalized token and done events written to the existing NDJSON
  artifact path

This does not change the runtime server hot path. It lets the operator runner
measure the already-supported chat-template route as a model-family profile
candidate.

The output sanity classifier was also tightened:

- visible or truncated `<think>` traces are no longer classified as healthy
  text
- visible or truncated `<|channel>thought` traces are no longer classified as
  healthy text

## 3. Live Evidence

Corrected live evidence:

- directory:
  `files/evidence/owlmlx/model-release-candidates/20260505T-mainline-gemma-chat-template-classifier-rerun/`
- record:
  `files/evidence/owlmlx/model-release-candidates/20260505T-mainline-gemma-chat-template-classifier-rerun/record.json`
- local ledger:
  `files/evidence/owlmlx/model-release-candidates/20260505T-mainline-gemma-chat-template-classifier-rerun/ledger.jsonl`

Result:

- `model_id = gemma-4-31B-it`
- `repeat_count = 2`
- `failure_count = 0`
- `prompt_template_id = gemma_openai_chat_template_v1`
- `output_sanity_label = reasoning_trace_truncated`
- `ttft_ms = 12294.993`
- `decode_tokens_per_second = 2.309`
- `end_to_end_tokens_per_second = 1.617`
- `peak_resident_set_bytes = 35297640448`
- `memory_peak_source = process_tree_rss`
- `verdict = needs_optimization`

The earlier chat-template probe directory
`files/evidence/owlmlx/model-release-candidates/20260505T-mainline-gemma-chat-template-rerun/`
is preserved as local forensic evidence, but its `valid_text` classification
was produced before the classifier fix and is not included in the cumulative
ledger.

## 4. Runtime Surface State

`files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl` now
contains eight records.

`GET /v1/runtime/model-release-candidates/history` on `127.0.0.1:8066`
returns those eight records.

The current latest record is the corrected Gemma chat-template record:

- `model_id = gemma-4-31B-it`
- `prompt_template_id = gemma_openai_chat_template_v1`
- `output_sanity_label = reasoning_trace_truncated`
- `verdict = needs_optimization`

## 5. Honest Interpretation

This round narrowed Gemma:

- old blocker: raw-prompt `repetitive_output`
- new blocker: chat-template `reasoning_trace_truncated` plus high TTFT /
  low throughput

It did not make Gemma pass.

It did not prove model quality.

It did not compare against oMLX or vMLX.

It did not change the DeepSeek experimental lane.

## 6. Verification

Commands run:

```bash
.venv/bin/python -m pytest -q tests/test_model_release_candidate_surface.py
.venv/bin/python -m py_compile scripts/runtime_model_release_candidate.py
git diff --check -- scripts/runtime_model_release_candidate.py tests/test_model_release_candidate_surface.py
.venv/bin/python scripts/runtime_model_release_candidate.py --ledger-path files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl history
curl -s http://127.0.0.1:8066/v1/runtime/model-release-candidates/history
curl -s http://127.0.0.1:8066/v1/runtime/model-release-candidates
curl -s http://127.0.0.1:8066/healthz
```

Observed results:

- `tests/test_model_release_candidate_surface.py`: 23 passed
- py_compile: OK
- targeted `git diff --check`: clean
- cumulative ledger history: 8 records
- 8066 history: 8 records
- 8066 latest: corrected Gemma chat-template record
- 8066 healthz after run: `ok = true`, `active_model_id = null`,
  `model_count = 0`

## 7. Next Step

Next owlmlx mainline round should stay on the template/thinking-control layer
before touching lower-level speed work:

1. Add a narrow family-profile experiment for Gemma final-answer-only behavior.
2. If Gemma still exposes reasoning/channel traces, classify it as a profile
   blocker rather than a runtime pass.
3. Reuse the same profile investigation shape for `Qwen3.6-35B-A3B`, which
   already shows a reasoning-trace / TTFT shape.
4. Keep `Qwen3.6-27B` as the separate decode-speed lane after output-quality
   blockers are narrower.
