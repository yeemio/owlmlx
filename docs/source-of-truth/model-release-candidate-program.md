# owlmlx Model Release Candidate Program

> Status: authoritative
> Updated: 2026-05-06
> Scope: post-technical-preview model adaptation, performance validation, and
> OwlOps-assisted release gating before any user-facing owlmlx-powered
> application release

## 1. Purpose

This document freezes the next phase after `release-readiness-backlog.md`
reached `7 / 7`.

The closed release floors allow `technical preview` operation. They do not
prove that the main local model set is ready for a user-facing application
release.

The next phase is therefore:

**model release-candidate adaptation and performance validation, coordinated
between `owlmlx` and OwlOps.**

## 2. Release Gate

No user-facing release should be promoted beyond technical preview until the
model release-candidate matrix has a pass record for the selected mainline
models.

This gate is intentionally narrower than a general parity claim:

- it does not claim `owlmlx` is equivalent to `oMLX` or `vMLX`
- it does not claim every downloaded model is supported
- it does not claim every workload class is ready
- it only answers whether the selected local model set has enough measured
  stability and performance evidence to be shipped through an upper-layer
  application such as OwlCoda

## 3. Ownership

`owlmlx` owns:

- model registration and visibility truth
- model path resolution
- load / generate / unload / reload runtime behavior
- runtime-owned memory pressure, residency, and recovery signals
- model-specific adapter or backend integration work
- runtime evidence records emitted over supported surfaces
- `GET /v1/runtime/model-release-candidates`
- `GET /v1/runtime/model-release-candidates/history`

OwlOps owns:

- performance observation workspace
- repeated same-host runs
- charts and regressions over TTFT, throughput, wall time, RSS, and failures
- pass / fail rendering for the model release-candidate matrix
- operator-facing bottleneck diagnosis

OwlCoda owns no runtime truth in this phase. It should wait until `owlmlx` and
OwlOps agree that the model matrix is release-candidate passable, then consume
the frozen runtime URL and model visibility surface as an application entry.

## 4. Candidate Model Matrix

### 4.1 Mainline Release-Candidate Lane

Observed on 2026-05-05, the `owlmlx` technical-preview server at
`http://127.0.0.1:8066` exposed these model ids through
`GET /v1/openai/models`:

| Model id | Current lane | Required release-candidate evidence |
|---|---|---|
| `Qwen3.6-27B` | mainline | repeated load / generate / unload / reload, short and medium prompts, TTFT, throughput, peak RSS, wall time, failure count, OwlOps rendering |
| `Qwen3.6-35B-A3B` | mainline | repeated load / generate / unload / reload, short and medium prompts, TTFT, throughput, peak RSS, wall time, failure count, OwlOps rendering |
| `gemma-4-31B-it` | mainline | repeated load / generate / unload / reload, short and medium prompts, TTFT, throughput, peak RSS, wall time, failure count, OwlOps rendering |

`gpt-oss-120b-MXFP4-Q4` is intentionally removed from the active RC gate. It
is also removed from the runtime visibility registry and its local base
artifact has been deleted from `/Users/yeemio/AI/Agent/models`. It is not a
release blocker and no longer serves as the heavy pressure canary now that the
DeepSeek V4 lane exists.

### 4.2 Flagship Experimental Lane

`DeepSeek-V4-Flash-2bit-DQ` is included as the flagship pressure and adapter
optimization lane, not a mainline release-candidate model.

`DeepSeek-V4-Flash-4bit` remains an experimental-only line. It is not part of
the active pressure gate or the mainline release-candidate gate until a
separate host-fit proof exists.

Current known local fact:

- artifact path:
  `/Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ`
- local directory size observed: about `90G`
- `model.safetensors.index.json` metadata:
  - `total_parameters = 284333146519`
  - `total_size = 96520315996`
- shard count: `19`
- current `owlmlx` technical-preview visibility: not exposed through
  `GET /v1/openai/models` on `127.0.0.1:8066`
- current runtime label: `experimental adapter optimization candidate`

This model must not be mixed into the mainline release gate. Its acceptance
target is a separate adapter-optimization record:

- repeatable load and short generation through an explicit DeepSeek V4 runtime
  environment
- coherent output beyond the initial tiny smoke
- explicit RSS and memory-headroom record on the 128 GB host
- unload / restart / reload behavior recorded without hiding failed reclaim
  events
- OwlOps can render it as `experimental`, not as `supported`

## 5. Evidence Contract

Each model release-candidate record should include:

- `model_id`
- `lane`
- `runtime_url`
- `host_class`
- `artifact_path`
- `visibility_status`
- `load_result`
- `generation_result`
- `unload_result`
- `reload_result`
- `repeat_count`
- `failure_count`
- `first_token_latency_ms`
- `tokens_per_second`
- `wall_clock_ms`
- `peak_resident_set_bytes`
- `memory_headroom_bytes`
- `output_sanity_label`
- `owlops_observation_url_or_path`
- `verdict`

Optional observability v2 fields are runtime-owned extensions on the same
record surface. They are stable for new records but remain optional so older
v1 cumulative-ledger rows stay readable:

- `load_time_ms`: elapsed time for the first load request
- `reload_time_ms`: aggregate elapsed time for later load requests in repeated
  runs
- `unload_time_ms`: aggregate elapsed time for unload requests
- `queue_wait_ms`: aggregate stream `done.wait_time_s`, converted to
  milliseconds when the runtime reports it
- `ttft_ms`: explicit time-to-first-token field; currently same source as
  `first_token_latency_ms`
- `decode_tokens_per_second`: post-first-token decode speed, excluding TTFT
- `end_to_end_tokens_per_second`: explicit name for the existing
  `tokens_per_second` meaning, including TTFT and full stream wall time
- `resident_mode`: residency/test mode label such as
  `load_unload_per_repeat`; dry-run records may use `unknown`
- `prompt_template_id`: prompt/template provenance label; dry-run records may
  use `unknown`
- `quality_caveats`: structured caveats derived from blockers and
  `output_sanity_label`; these are not model-quality claims
- `memory_peak_source`: memory measurement provenance such as
  `process_tree_rss`; future isolated DeepSeek records may use
  `mlx_reported_peak` or `mixed` only when actually measured that way
- `runtime_stream_wall_ms`, `runtime_first_response_ms`,
  `runtime_first_visible_token_ms`, `runtime_prompt_render_ms`,
  `runtime_timing_repeat_count`, and `runtime_timing_gate_status`:
  runtime-owned stream timing diagnostics when the generation path exposes
  `detail.timing.surface = owlmlx.child_stream_timing`
- `experimental_prefill_warmup_status`,
  `experimental_prefill_warmup_mode`, `experimental_prefill_warmup_ms`, and
  `experimental_prefill_warmup_included_in_metrics`: Model RC-only evidence
  for an explicitly requested post-load, pre-measured warmup generation;
  warmup generations are excluded from primary TTFT/TPS and lifecycle repeat
  metrics
- `reference_comparison_status`, `reference_comparison_evidence_pointer`, and
  `reference_comparison_runtime_ids`: optional consumption of the
  runtime-owned comparative-evidence ledger. A Model RC row may clear
  `reference_runtime_comparison_missing` only when the referenced ledger has a
  same-model `measured` record where both `owlmlx` and at least one reference
  runtime completed cleanly.
- `owlops_observation_status` and `owlops_observation_evidence_pointer`:
  optional consumer-observation handshake fields. A row may clear
  `owlops_observation_pending` only when status is `observed` and the pointer
  names a concrete OwlOps-side consumption proof. This does not change
  runtime optimization verdicts.

Missing or unmeasured v2 signals must be represented as absent, `null`, or by
a blocking/caveat string such as `process_tree_rss_missing`. They must not be
synthesized from another source. Existing historical v1 rows without these
optional fields remain valid.

The live runner also writes post-run runtime-health artifacts:

- `post-run-healthz.json`
- `post-run-runtime-status.json`

If the repeated load / generate / unload operations pass but the runtime is
left with unhealthy backend state, the record must carry
`post_run_backend_unhealthy` and cannot be treated as a clean
`needs_optimization` row.

Allowed verdicts:

- `pass`
- `needs_optimization`
- `blocked`
- `experimental_only`

Forbidden verdicts:

- `parity`
- `replacement`
- `equivalent`
- `production_ready`
- `beats`
- `wins`

## 6. Pass Criteria

A mainline model may be marked `pass` only when:

- the model is visible through the runtime-owned model visibility surface
- at least two repeated runs complete without process restart unless the test
  is explicitly a restart test
- load, generate, unload, and reload all produce structured runtime evidence
- OwlOps records TTFT, throughput, wall time, and process-tree RSS
- no run depends on a manually edited transient path that is absent from source
  truth
- failures, warnings, and degraded readiness are preserved rather than hidden
- post-run `/healthz` and `/v1/runtime/status` show backend health after the
  final unload/reload cycle
- the result is compared against the reference runtime when a same-model
  reference path is available on the same host

DeepSeek V4 may not be marked `pass` in the mainline matrix in this phase. Its
honest terminal label is either `experimental_only`, `needs_optimization`, or
`blocked`.

## 7. Execution Order

1. `owlmlx` freezes a model release-candidate evidence schema and operator
   runner.
2. `owlmlx` registers or explicitly blocks each candidate model with a
   runtime-owned reason.
3. OwlOps consumes the schema and produces a model-matrix observation
   workspace.
4. `owlmlx` runs the three mainline candidates through repeated live tests.
5. `owlmlx` runs DeepSeek V4 only in the experimental lane, with isolated
   runtime and memory-pressure discipline.
6. The coordinator decides whether the mainline matrix is sufficient for an
   OwlCoda technical-preview application release.

## 8. Current Status

As of 2026-05-05, A0 introduced the runtime-owned schema, record builder,
JSONL ledger, operator script, and read-only latest/history HTTP surfaces.

The first live Model RC sweep has now produced four schema-valid records in
`files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`.
`history.records` is the authoritative matrix view.

| Model id | Lane | Current verdict | Evidence status |
|---|---|---|---|
| `Qwen3.6-27B` | mainline | `needs_optimization` | two live HTTP repeated runs completed; OwlOps observation and same-host reference comparison remain open |
| `Qwen3.6-35B-A3B` | mainline | `needs_optimization` | two live HTTP repeated runs completed; OwlOps observation, same-host reference comparison, and short-generation quality caveat remain open |
| `gemma-4-31B-it` | mainline | `needs_optimization` | two live HTTP repeated runs completed; OwlOps observation and same-host reference comparison remain open |
| `DeepSeek-V4-Flash-2bit-DQ` | flagship experimental | `experimental_only` | one isolated `.runtime-deepseek-v4-mlx` / `mlx_lm.generate` pressure run completed; no owlmlx HTTP adapter, visibility registration, unload/reload adapter, or repeat adapter evidence yet |

The cumulative ledger append order is A1, A2, A3, D1. Because D1 is newest,
`GET /v1/runtime/model-release-candidates` returns the DeepSeek experimental
record as `latest`. Consumers must use
`GET /v1/runtime/model-release-candidates/history` for the mainline matrix.

The cumulative ledger later advanced to eight records after OwlOps R166 and
the first Gemma profile probe:

- `Qwen3.6-27B` current mainline row remains `needs_optimization` with valid
  output and a decode-speed blocker.
- `Qwen3.6-35B-A3B` current mainline row remains `needs_optimization` with a
  high-TTFT / reasoning-trace blocker in the earlier thinking-enabled path.
- `gemma-4-31B-it` current mainline row moved from raw-prompt
  `repetitive_output` to chat-template `reasoning_trace_truncated`; the
  repetition blocker is narrowed, but final-answer quality and TTFT remain
  open.
- `DeepSeek-V4-Flash-2bit-DQ` remains `experimental_only` and outside the
  mainline pass/fail summary.

This still does not mark any mainline model `pass`. The remaining release gate
is not "can the models run once"; it is model-specific profile optimization,
OwlOps-observed matrix validation, and same-host reference comparison.

On 2026-05-06, the supervised admission rerun added two fresh evidence
directories:

- `20260505T162118Z-qwen36-35b-a3b-supervised-admission-rerun`:
  `Qwen3.6-35B-A3B` completed two repeat cycles with `failure_count = 0`,
  `output_sanity_label = valid_text`, decode speed around `31.1` tok/s, TTFT
  around `1.76s`, and clean post-run backend health.
- `20260505T162236Z-gemma-4-31b-it-supervised-admission-rerun`:
  `gemma-4-31B-it` completed two repeat cycles with structured load /
  generation / unload success, but output remained
  `reasoning_trace_truncated` and post-run `/healthz` was blocked by a latched
  backend transport parse error. This row is not a clean optimization row until
  post-run backend health is represented in the record.

The runner was therefore tightened so post-run backend health is a record-level
gate. A normal successful subprocess unload also clears prior latched transport
errors when no models remain registered; force-unload and failed cleanup paths
continue to preserve the underlying failure.

Follow-up on 2026-05-06:

- `8066` was restarted in tmux session `owlmlx-8066-model-rc-20260506` and
  verified clean before the Gemma follow-up run.
- The first follow-up attempts exposed an operator-runner load-contract gap:
  `/v1/load` requires `memory_gb` when the backend has no default estimate.
  The runner now derives that value from model-load admission
  `known_peak_resident_set_bytes` when the operator does not provide
  `--memory-gb`, and records the actual load request payload in
  `repeat-XX-load.json`.
- A conservative Gemma follow-up with explicit `--memory-gb 60` appended a clean
  Gemma post-run-health row:
  `files/evidence/owlmlx/model-release-candidates/20260506T021105Z-gemma-4-31b-it-post-run-health-gate-rerun/record.json`.
  It completed two live HTTP repeat cycles with clean post-run backend health:
  `verdict = needs_optimization`, `failure_count = 0`,
  `repeat_count = 2`, `output_sanity_label = reasoning_trace_truncated`,
  `ttft_ms = 51229.148`, `decode_tokens_per_second = 14.744`, and
  `peak_resident_set_bytes = 50295062528`.
- This does not make Gemma `pass`. It only closes the immediate dirty
  post-run backend-health blocker. The active Gemma blocker is visible
  reasoning/channel trace output plus TTFT variance under the profile-default
  chat-completions path.

Parallel instrumentation follow-up on 2026-05-06:

- `owlmlx.reasoning_trace_policy:v1` now provides a runtime-owned policy for
  visible reasoning traces. It detects Gemma-style `<|channel>thought` /
  `<|channel>final` and `<think>` traces, keeps trace visibility explicit, and
  only returns a `final_text` candidate when that candidate is safely outside a
  visible reasoning boundary.
- The Gemma profile records this policy and keeps final-text extraction
  conservative: trace-only or truncated outputs remain
  `reasoning_trace_truncated` or `reasoning_trace_visible`, not `valid_text`.
- The live Model RC runner now writes `reasoning_trace_policy` and
  `timing_breakdown` into each repeat generation evidence file. The timing
  breakdown separates load elapsed time, stream wall time, first-token latency,
  post-first-token decode wall time, queue wait, and token counts.
- The first heavy Gemma row carrying these fields is
  `files/evidence/owlmlx/model-release-candidates/20260506T024418Z-gemma-4-31b-it-final-answer-control-rerun/record.json`.
  It completed two repeats with clean post-run backend health and appended to
  the cumulative ledger with `verdict = needs_optimization`,
  `failure_count = 0`, `repeat_count = 2`,
  `output_sanity_label = reasoning_trace_truncated`,
  `ttft_ms = 5104.511`, `decode_tokens_per_second = 7.203`, and
  `peak_resident_set_bytes = 38314049536`.
- That row applied the experimental Gemma final-answer-only prompt-control in
  the user message, but Gemma still emitted visible `<|channel>thought` with no
  safe final channel. The platform can no longer treat simple prompt wording as
  an untested fix; the next boundary is stronger chat-template / final-channel /
  stop-token control versus model behavior.
- Latest timing breakdown evidence does not root-cause the earlier `51.2s`
  average TTFT spike. In the profile-control run, repeat-level first-token
  latency was about `4.6s-5.6s`, while post-first-token decode wall time was
  about `8.5s-9.0s`.
- The follow-up stop-request-payload row is
  `files/evidence/owlmlx/model-release-candidates/20260506T-mainline-gemma-stop-request-payload-rerun/record.json`.
  It applied profile stop tokens through the HTTP generation params as
  `stop = ["<eos>", "<turn|>"]`, wrote the actual generation
  `request_payload` into each repeat evidence file, completed two repeats,
  appended to the cumulative ledger, and left post-run health clean.
- That row still returned `verdict = needs_optimization`,
  `output_sanity_label = reasoning_trace_truncated`, `ttft_ms = 24322.913`,
  `decode_tokens_per_second = 7.688`, and
  `peak_resident_set_bytes = 33050263552`. The two repeats still began with
  visible `<|channel>thought`, reached `finish_reason = length`, and produced
  no safe final channel, so stop-token application is proven insufficient by
  itself.
- The TTFT variance is now reproduced enough to localize the immediate spike to
  first-token latency, not post-first-token decode. In the latest row, repeat 1
  first token was about `41.9s` while repeat 2 was about `6.7s`; both repeats
  kept post-first-token decode wall time near `8.2s-8.5s`.

### 8.1 Profile-Aware Runner Defaults

The live Model RC runner has an opt-in profile application switch:
`--apply-model-profile-defaults`. When absent, the runner keeps the legacy
`raw_generate_stream` request path and does not write an
`effective_generation_policy` block.

When the switch is present, the runner resolves `owlmlx.model_profile` from
`model_id` and records the resulting effective policy in `runner-config.json`.
The initial operational policy is conservative:

- `Qwen3.6-27B` and `Qwen3.6-35B-A3B` select the OpenAI chat-completions stream
  path unless `--request-mode` is explicitly supplied, because template and
  reasoning behavior are part of the current blocker. Their default
  `chat_template_kwargs` now set `enable_thinking=false` for final-answer
  probes; reasoning diagnostics must opt in separately.
- `gemma-4-31B-it` selects the OpenAI chat-completions stream path unless
  overridden, records channel/reasoning cleanup caveats, applies
  `chat_template_kwargs.enable_thinking=false`, and still keeps the
  experimental final-answer-only user-message prompt-control. The live
  `20260506T024418Z` and stop-payload rows show prompt wording and stop strings
  alone are insufficient to suppress visible thought-channel output.
- `DeepSeek-V4-Flash-2bit-DQ` keeps its experimental profile label and is not
  routed into the mainline runner by profile defaults.
- unknown model ids keep the raw path and carry an explicit conservative
  profile caveat.

Explicit `--request-mode` and `--prompt-template-id` values win over profile
defaults. Profile stop-token strings now pass through the HTTP generation
params as `stop` when `--apply-model-profile-defaults` is used and the profile
declares stop-token strings. Profile `chat_template_kwargs` now pass through the
OpenAI chat-completions HTTP surface and the child `mlx_lm` runner instead of
staying as evidence-only metadata. This is still an experimental profile
control, not a supported replacement-grade quality claim; evidence records
`model_profile:profile_stop_tokens_applied_experimental`.

Parser replay follow-up on 2026-05-06:

- Evidence:
  `files/evidence/owlmlx/model-release-candidates/20260506T064509Z-final-answer-parser-replay/manifest.json`.
- This replay did not load models. It replayed existing live stream artifacts
  through `owlmlx.reasoning_trace_policy:v1`.
- `Qwen3.6-27B` closed `<think></think>` and left a final-text candidate, but
  `finish_reason=length` keeps it `reasoning_trace_final_length`, not
  `valid_text`.
- `Qwen3.6-35B-A3B` output beginning with prose "thinking process" is now
  classified as `reasoning_trace_truncated` instead of clean final text.
- Gemma remains `reasoning_trace_truncated` with no safe final candidate in the
  replay. The next live Gemma proof must test the newly wired
  `enable_thinking=false` template kwargs before any clean-output claim.

Gemma `enable_thinking=false` live proof on 2026-05-06:

- Evidence:
  `files/evidence/owlmlx/model-release-candidates/20260506T-gemma-enable-thinking-false-live-proof/record.json`.
- This is the first live Gemma row after profile `chat_template_kwargs` became
  an actual HTTP / child-runner control instead of metadata only.
- The request payload for both repeats included
  `chat_template_kwargs = {"enable_thinking": false}`,
  `stop = ["<eos>", "<turn|>"]`, and the OpenAI chat-completions template path.
- Both repeats emitted plain final text with
  `visible_reasoning_trace=false`, `trace_status=none`,
  `final_text_source=plain_text`, and `output_sanity_label=valid_text`.
- The row completed `load -> generate -> unload -> reload -> generate ->
  unload` with `failure_count=0`, `ttft_ms=2061.827`,
  `decode_tokens_per_second=8.11`, `peak_resident_set_bytes=62678777856`,
  and clean post-run health.
- This closes the short-prompt Gemma final-answer channel blocker as a
  platform/profile issue for this workload. It does not make Gemma `pass`:
  OwlOps observation, same-host reference comparison closure, longer prompts,
  multi-turn behavior, and cache safety remain separate gates.

Gemma runtime-owned final-answer default follow-up on 2026-05-06:

- Evidence:
  `files/evidence/owlmlx/model-release-candidates/20260506T-gemma-final-answer-parser-live-proof/record.json`
  (superseded diagnostic row),
  `files/evidence/owlmlx/model-release-candidates/20260506T-gemma-final-answer-parser-live-proof-v2/record.json`
  (accepted explicit-parser row), and
  `files/evidence/owlmlx/model-release-candidates/20260506T-gemma-runtime-profile-default-live-proof/record.json`.
- The first diagnostic row removed visible thought-channel output but exposed
  a literal `\final` duplicate in the returned text, so it is not the
  acceptance proof. The v2 row is the first clean explicit-parser proof after
  escaped final-channel handling landed.
- `owlmlx.reasoning_trace_policy:v1` now recognizes Gemma escaped
  `\final` channel markers in addition to `<|channel>final`, and routes only
  the safe post-marker final candidate when the OpenAI surface asks for
  `final_answer_content`.
- `/v1/chat/completions` now resolves known model profiles directly. For
  `gemma-4-31B-it`, a direct OpenAI chat request that does not supply profile
  kwargs receives runtime defaults for `chat_template_kwargs.enable_thinking`,
  stop strings, and final-answer parser routing; explicit caller-provided
  stop/template kwargs remain overrides.
- The explicit-parser live row returned clean final text with
  `output_sanity_label=valid_text`, `ttft_ms=10349.52`,
  `tokens_per_second=0.097`, load/generate/unload `pass`, and post-run health
  clean idle. Its low TPS is not a decode-speed claim because final-answer
  parser routing buffers trace-shaped content and emits one visible final
  chunk.
- The direct-runtime-default live row sent no `chat_template_kwargs`, `stop`,
  or `extra_body` in the client request payload, yet returned plain final text
  with `visible_reasoning_trace=false`, `trace_status=none`,
  `final_text_source=plain_text`, `output_sanity_label=valid_text`,
  `ttft_ms=5239.115`, and clean post-run health.
- This moves Gemma final-answer cleanup from runner-only evidence into the
  runtime-owned OpenAI chat default path. The row still remains
  `needs_optimization` because OwlOps observation and same-model reference
  comparison consumption are separate gates.

Gemma comparative-ledger consumption proof on 2026-05-06:

- Evidence:
  `files/evidence/owlmlx/model-release-candidates/20260506T-gemma-reference-comparison-consumption-live-proof/record.json`.
- The existing Gemma vMLX reasoning-aware measured manifest was imported into
  the cumulative comparative ledger through
  `scripts/runtime_comparative_evidence.py import-manifest-record`, preserving
  the original evidence pointer:
  `files/evidence/owlmlx/comparative-evidence/20260506T030122Z-gemma-current-reference-comparison/vmlx-reasoning-aware-run/run/manifest.json`.
- The imported comparison is still narrow: short prompt, `max_tokens=64`,
  `temperature=0`, same host, and reasoning-aware vMLX stream consumption.
  It records `owlmlx` TPS `3.7468` / TTFT `8225.989ms` versus `vmlx` TPS
  `3.8304` / TTFT `8306.498ms`.
- The latest Gemma Model RC row now writes
  `reference_comparison_status=measured`,
  `reference_comparison_runtime_ids=["owlmlx", "vmlx"]`, and removes
  `reference_runtime_comparison_missing` from blockers.
- That row still returns `verdict=needs_optimization` because
  `owlops_observation_pending` remains open. This is reference-comparison
  consumption closure, not parity or replacement-grade signoff.

OwlOps observation closure proof on 2026-05-06:

- OwlOps proof:
  `/Users/yeemio/AI/gitrep/owlops/docs/source-of-truth/generated/model-rc-live-consumption-proof-20260506T0927Z.json`.
  The proof was produced by the OwlOps `ModelReleaseCandidateLive8066SmokeTests`
  live path against `127.0.0.1:8066`; it fetched latest/history, normalized the
  payload, and built the app-facing matrix from cumulative history without
  changing upstream verdicts.
- The Model RC runner now accepts explicit
  `--owlops-observation-status {pending,observed,rejected}` and
  `--owlops-observation-evidence-pointer`. The default remains `pending`; only
  `observed` with a non-empty pointer clears `owlops_observation_pending`.
- New observed rows were appended for:
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen27-owlops-observed-live-proof/record.json`,
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-owlops-observed-live-proof/record.json`,
  and
  `files/evidence/owlmlx/model-release-candidates/20260506T-gemma-owlops-observed-live-proof/record.json`.
- The current 8066 Model RC history has `ledger_status=available` and `27`
  rows. The latest Qwen27, Qwen35, and Gemma rows all have
  `blockers=[]`, `owlops_observation_status=observed`,
  `reference_comparison_status=measured`, and `output_sanity_label=valid_text`.
- These rows still return `verdict=needs_optimization`. OwlOps observation
  closure means the consumer surface saw the upstream truth; it is not a
  performance, parity, batching, or replacement-grade release signoff.

Qwen35 `enable_thinking=false` live proof on 2026-05-06:

- Evidence:
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-enable-thinking-false-live-proof/record.json`.
- The request payload for both repeats included
  `chat_template_kwargs = {"enable_thinking": false}`,
  `stop = ["<|im_end|>"]`, and the OpenAI chat-completions template path.
- Both repeats emitted plain final text with
  `visible_reasoning_trace=false`, `trace_status=none`,
  `final_text_source=plain_text`, and `output_sanity_label=valid_text`.
- The row completed `load -> generate -> unload -> reload -> generate ->
  unload` with `failure_count=0`, `ttft_ms=3285.14`,
  `decode_tokens_per_second=61.434`, `peak_resident_set_bytes=52908916736`,
  and clean post-run health.
- This closes the short-prompt Qwen35 prose-reasoning output blocker as a
  template/profile issue for this workload. It leaves TTFT as a separate
  pre-first-token optimization line: per-repeat first-token latency was about
  `3.1s-3.5s`, while post-first-token decode took about `0.34s`.

Qwen35 TTFT root-cause decomposition on 2026-05-06:

- Evidence:
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-ttft-raw-template-decomposition/summary.json`
  and
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-child-stream-timing-live-proof/summary.json`.
- Offline tokenizer rendering for the same Qwen35 chat prompt took
  `10.219ms` for a `21` token rendered prompt, so template rendering is not the
  dominant source of the multi-second cold TTFT.
- In one resident session, the first raw rendered-template request had
  `first_token_latency_ms = 3636.59`, while immediately following OpenAI chat
  and raw repeat requests dropped to `335.949ms` and `316.898ms`. This points
  to cold first-generation backend warmup rather than OpenAI route framing.
- Runtime-owned child stream timing is now emitted on raw stream `done` events
  as `detail.timing.surface = owlmlx.child_stream_timing`. The live proof
  recorded `prompt_render_ms = 0.001`, `stream_call_start_ms = 0.02`,
  `first_response_ms = 2867.858`, `first_visible_token_ms = 2896.208`, and
  client `first_token_latency_ms = 2993.762`.
- The root-cause classification for this workload is therefore:
  Qwen35 cold TTFT is dominated by child `mlx_lm.stream_generate`
  first-response latency, not Python chat-template rendering, OpenAI HTTP
  framing, or parent process exchange. It remains `needs_optimization`, not a
  solved performance row.

Qwen35 Model RC timing gate on 2026-05-06:

- Evidence:
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-model-rc-timing-gate-live-proof/timing-gate-summary.json`
  and the appended cumulative ledger row at
  `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`.
- The Model RC runner now records per-generation
  `runtime_stream_timing`, per-repeat timing-breakdown fields, and record-level
  `runtime_stream_wall_ms`, `runtime_first_response_ms`,
  `runtime_first_visible_token_ms`, `runtime_prompt_render_ms`,
  `runtime_timing_repeat_count`, and `runtime_timing_gate_status`.
- With `--timing-gate-resident-repeat`, the runner keeps the normal lifecycle
  repeat semantics but adds one diagnostic same-resident generation before
  unload. That diagnostic generation does not count as an additional lifecycle
  repeat.
- The live Qwen35 timing gate status is `supported` with
  `runtime_timing_repeat_count = 2`. Cold first response was `3820.178ms`;
  same-resident first response was `235.366ms`; classification is
  `cold_first_response_dominant`.
- This converts TTFT root cause into an automated Model RC gate. It still does
  not claim a TTFT optimization: the next optimization work is warmup, prefill,
  cache, or scheduler mitigation against the cold first-response spike.

Qwen35 experimental prefill-warmup proof on 2026-05-06:

- Evidence:
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-experimental-prefill-warmup-live-proof/timing-gate-summary.json`
  and the appended cumulative ledger row at
  `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`.
- The Model RC runner now supports an explicit
  `--experimental-prefill-warmup` option. It runs one post-load,
  pre-measured stream generation before the measured request, writes
  `repeat-01-prefill-warmup-stream.ndjson` and
  `repeat-01-prefill-warmup.json`, and excludes that warmup from primary
  TTFT/TPS and lifecycle repeat metrics.
- In the live Qwen35 proof, warmup first response was `3198.552ms`; the
  immediately following measured first response was `210.355ms`; same-resident
  diagnostic first response was `214.895ms`; classification is
  `experimental_prefill_warmup_reduces_measured_first_response`.
- The measured primary row recorded `ttft_ms = 262.827`,
  `runtime_timing_gate_status = supported`,
  `runtime_timing_repeat_count = 2`, `failure_count = 0`,
  `peak_resident_set_bytes = 45992984576`, and clean post-run health.
- This is a bounded mitigation proof for this short Qwen35 workload, not a
  runtime default or a release-pass claim. Qwen35 remains
  `needs_optimization` because OwlOps observation, same-host reference
  comparison, broader workload coverage, and production warmup semantics remain
  separate gates.

Qwen27 / Qwen35 comparative-ledger consumption proof on 2026-05-06:

- Evidence:
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen27-reference-comparison-consumption-live-proof/record.json`
  and
  `files/evidence/owlmlx/model-release-candidates/20260506T-qwen35-reference-comparison-consumption-live-proof/record.json`.
- The live Model RC runner now accepts
  `--comparative-evidence-ledger-path`. When the comparative ledger contains a
  same-model clean `measured` record, the Model RC row writes
  `reference_comparison_status = measured`, preserves the referenced
  `evidence_pointer`, records `reference_comparison_runtime_ids`, and removes
  `reference_runtime_comparison_missing` from blockers.
- Qwen27 consumed the measured oMLX comparison at
  `files/evidence/owlmlx/comparative-evidence/20260506T040009Z-qwen27-qwen35-reference-closure/qwen27-omlx-run/run/manifest.json`.
  Its new blockers are only `owlops_observation_pending`.
- Qwen35 consumed the measured oMLX comparison at
  `files/evidence/owlmlx/comparative-evidence/20260506T040009Z-qwen27-qwen35-reference-closure/qwen35-omlx-run/run/manifest.json`.
  Its new blockers are only `owlops_observation_pending`.
- This closes the stale generic `reference_runtime_comparison_missing` blocker
  for Qwen27 and Qwen35 Model RC rows. It does not make either model `pass`,
  because OwlOps observation, broader workload coverage, and product-level
  release criteria remain open.

## 9. Non-Goals

This phase does not:

- require DeepSeek V4 to become supported
- require 4bit DeepSeek V4 to fit the current host
- require a public marketing release
- require OwlCoda to own runtime launch truth before the model matrix passes
- widen `technical preview` into release-ready wording
