# owlmlx Release-Readiness Execution Plan

> Status: authoritative
> Updated: 2026-05-05 (post-7/7 release-floor closure now moves to the model
> release-candidate program before any user-facing application release)
> Scope: execution plan for closing `release-readiness-backlog.md` floors

## 1. Purpose

This document turns `release-readiness-backlog.md` into an executable
burn-down plan.

It answers:

**What is the order of attack, what counts as progress, who owns each lane, and
what is the honest time/risk estimate before `owlmlx` can meet the release
floor?**

It does not relax the release floor.
It does not turn execution estimates into readiness claims.

## 2. Current Release Position

Current floor status:

- `7 / 7` release-floor items are closed:
  - `3.1` closed 2026-04-25 via the non-stream main runtime path;
    stream-branch dispatch remains the active phase45 seam, preserved as
    secondary truth
  - `3.3` closed 2026-04-25 via the runtime-owned non-resident loadability
    lineage contract (`owlmlx.nonresident_loadability_lineage`) consumed by
    `owlmlx.nonresident_model_admission_policy`; B3 review
    `owlmlx_release_floor_3_3B3_closure_review_pass_closed_recommended`
    confirmed the lineage round trip
  - `3.2` closed 2026-04-26 via the runtime-owned memory-pressure eviction
    decision contract (`owlmlx.memory_pressure_eviction_policy`) and the
    runtime-owned execution path
    (`RuntimeKernel.execute_memory_pressure_eviction`); 3.2C independent
    closeout review
    `owlmlx_release_floor_3_2C_independent_closeout_closed`
    resolved the 3.2B self-audit caveat
  - `3.4` closed 2026-04-27 via the runtime-owned termination recovery
    policy (`owlmlx.termination_recovery_policy`) plus the cleanup-boundary
    event surface (`owlmlx.reclaim_barrier_event`); 3.4B independent
    closeout review
    `owlmlx_release_floor_3_4B_closeout_closed` verified the four required
    cause classes, the four-action vocabulary, runtime-owned event
    resolution semantics (final-status look-clean alone never resolves),
    and the read-only HTTP surfaces
  - `3.5` closed 2026-04-28 via same-host measured comparative evidence
    against `omlx` for `workload_class = "single_prompt_short"` on
    `host_class = "Mac17,6-arm64-macOS-26.4.1-128GB"`; 3.5F independent
    closeout review
    `owlmlx_release_floor_3_5F_closeout_closed` verified the fresh measured
    ledger, HTTP latest/history captures, process-tree / external-PID RSS,
    token-aware TTFT, artifact trail, and harness-contract section `8`
  - `3.6` closed 2026-04-28 via OwlOps-boundary external runtime-truth
    consumer evidence (host_class
    `Mac17,6-arm64-macOS-26.4.1-128GB`, workload_class
    `external_runtime_status_probe`, verdict `pass`); the live HTTP probe
    issued from `/Users/yeemio/AI/gitrep/owlops` fetched both
    `/v1/runtime/status` and `/healthz` over HTTP at exit-status 0 with
    empty stderr; 3.6B / 3.7B final closeout
    `owlmlx_release_floor_3_6B_3_7B_final_closeout_closed` verified the
    record and ledger
  - `3.7` closed 2026-04-28 via the runtime-owned `public-surface.md`
    freeze plus `tests/test_public_surface_contract.py` (12 cases); the
    supported HTTP routes, Python modules, operator scripts, and
    source-of-truth contracts are exactly enumerated, anything not listed
    is `internal` by default, and the schema-level
    `BANNED_VERDICT_VOCABULARY` enforcement is cross-referenced; 3.6B /
    3.7B final closeout `owlmlx_release_floor_3_6B_3_7B_final_closeout_closed`
    verified the freeze
- `owlmlx` remains `early_formal_runtime, below reference-grade stability`
- no external release, parity, replacement, or production-grade claim is honest;
  closure of all seven release floors does **not** by itself promote
  `owlmlx` to release-ready, and `release-readiness-backlog.md` §4.3 keeps
  the banned current-claim list in force
- with all seven release floors closed, the active interim claim moves
  from `early formal runtime` and `internal source-of-truth project`
  toward `technical preview`, governed by `public-surface.md` §2 and §10
- the comparative-evidence HTTP surface remains available for upper-layer
  consumers through `/v1/runtime/comparative-evidence` plus
  `/v1/runtime/comparative-evidence/history`
- the next active delivery phase is the model release-candidate program
  described in `model-release-candidate-program.md`; it must validate the
  selected mainline model set with OwlOps performance observation before
  OwlCoda or any other upper-layer application is treated as release-ready
- `DeepSeek-V4-Flash-2bit-DQ` is included only as the flagship experimental
  adapter-optimization lane; it is not part of the mainline release-candidate
  pass/fail gate

The immediate correction is:

- stop treating `7 / 7` release-floor closure as an application release
- require every active round to name one model release-candidate lane or the
  DeepSeek experimental lane
- require each round to either close, progress, or hard-block that lane with
  live runtime evidence and OwlOps-consumable observation data

Model RC A0 result (2026-05-05,
`owlmlx_model_release_candidate_a0_evidence_schema_introduced_pending_live_runs`):

- goal contract archived at
  `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-goal-contract.md`
- runtime-owned schema / record / ledger modules added:
  `owlmlx.model_release_candidate_schema`,
  `owlmlx.model_release_candidate_record`, and
  `owlmlx.model_release_candidate_ledger`
- operator entry added at `scripts/runtime_model_release_candidate.py` with
  `dry-run-matrix`, `append-dry-run-matrix`, `latest`, and `history`
- read-only HTTP surfaces added:
  `GET /v1/runtime/model-release-candidates` and
  `GET /v1/runtime/model-release-candidates/history`
- A0 dry-run matrix emits four records: three mainline candidates with
  `verdict = "needs_optimization"` and DeepSeek V4 with
  `verdict = "experimental_only"`; no model is marked `pass`
- `gpt-oss-120b-MXFP4-Q4` is deleted from local model assets, removed from
  runtime visibility, and outside the active Model RC gate; it no longer
  serves as the heavyweight pressure canary
- focused verification passed:
  `tests/test_model_release_candidate_surface.py` (13 passed),
  `tests/test_runtime_server.py -k "model_release_candidate or runtime_status"`
  (1 passed, 40 deselected), `tests/test_public_surface_contract.py`
  (12 passed), py_compile for new modules / script / server, operator
  append/latest/history smoke, and `git diff --check`

Interim next dominant gap at that point, later refined by the live
profile-control proof below:

- run the first live mainline Model RC candidate through repeated
  `load -> generate -> unload -> reload`, append a real record, and hand the
  same ledger surface to OwlOps for observation rendering

Parallel execution allocation (2026-05-05):

- Lane A is the only memory-exclusive lane. It runs `Qwen3.6-27B` live through
  repeated load / generate / unload / reload and appends the first non-dry-run
  Model RC record.
- Lane B is a non-loading consumer lane. It runs in OwlOps and builds the Model
  RC observation workspace against the current owlmlx latest/history surfaces
  and JSONL ledger. It must not start or load models.
- DeepSeek pressure work waits until Lane A finishes the first mainline live
  record. This prevents unified-memory pressure from being misread as a
  model-specific failure.
- The active prompt archive for this split is
  `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-parallel-a1-b1-coordinator-packet.md`.

Model RC A1 result (2026-05-05,
`owlmlx_model_release_candidate_a1_qwen36_27b_live_record_introduced`):

- `Qwen3.6-27B` completed two live repeated HTTP runs through
  `load -> stream generate -> unload -> reload -> stream generate -> unload`.
- A schema-valid `owlmlx.model_release_candidate_record` was appended at
  `files/evidence/owlmlx/model-release-candidates/20260505T071836Z-qwen36-27b/ledger.jsonl`.
- `GET /v1/runtime/model-release-candidates` and
  `GET /v1/runtime/model-release-candidates/history` on `127.0.0.1:8066`
  serve that live ledger.
- The record verdict is `needs_optimization`, not `pass`, because OwlOps
  observation and same-host reference comparison remain open.
- Measured values: `repeat_count = 2`, `failure_count = 0`,
  `first_token_latency_ms = 1145.8`, `tokens_per_second = 5.395`,
  `wall_clock_ms = 19759.742`,
  `peak_resident_set_bytes = 54348431360`, and
  `memory_headroom_bytes = 83090522112`.
- Output was valid text but short generation was length-truncated inside a
  reasoning trace, so no model-quality claim is made from this record.

Next dominant gap:

- let OwlOps B1 consume and render the A1 live record, then run the next
  memory-exclusive owlmlx mainline lane for `Qwen3.6-35B-A3B`.

Remaining lane packet (2026-05-05,
`owlmlx_model_release_candidate_remaining_lanes_packet_ready`):

- A2 prompt archived for `Qwen3.6-35B-A3B` live mainline evidence.
- A3 prompt archived for `gemma-4-31B-it` live mainline evidence.
- D1 prompt archived for `DeepSeek-V4-Flash-2bit-DQ` pressure/adaptation
  evidence.
- Coordinator packet archived at
  `files/execution-prompts/owlmlx/owlmlx-model-release-candidate-remaining-lanes-coordinator-packet.md`.
- Execution rule remains: one heavyweight live model lane at a time; OwlOps may
  run only read-only consumer work in parallel.

Model RC A2 / A3 / D1 integrated result (2026-05-05,
`owlmlx_model_release_candidate_a2_a3_d1_parallel_lanes_integrated`):

- A2 `Qwen3.6-35B-A3B` completed two live repeated HTTP runs through
  `load -> stream generate -> unload -> reload -> stream generate -> unload`.
  The schema-valid record lives at
  `files/evidence/owlmlx/model-release-candidates/20260505T073902Z-qwen36-35b-a3b/record.json`.
  Verdict remains `needs_optimization`, with `repeat_count = 2`,
  `failure_count = 0`, `first_token_latency_ms = 3315.486`,
  `tokens_per_second = 14.666`, `wall_clock_ms = 37299.247`,
  `peak_resident_set_bytes = 54570254336`, and
  `memory_headroom_bytes = 82868699136`. Output sanity is
  `reasoning_trace_truncated`, so short-generation quality remains
  inconclusive.
- A3 `gemma-4-31B-it` completed two live repeated HTTP runs through the same
  mainline sequence. The schema-valid record lives at
  `files/evidence/owlmlx/model-release-candidates/20260505T074135Z-gemma-4-31b-it/record.json`.
  Verdict remains `needs_optimization`, with `repeat_count = 2`,
  `failure_count = 0`, `first_token_latency_ms = 2179.717`,
  `tokens_per_second = 6.178`, `wall_clock_ms = 36577.866`,
  `peak_resident_set_bytes = 56211668992`, and
  `memory_headroom_bytes = 81227284480`.
- D1 `DeepSeek-V4-Flash-2bit-DQ` completed one isolated
  `.runtime-deepseek-v4-mlx` / `mlx_lm.generate` pressure run, not an owlmlx
  HTTP adapter run. The schema-valid record lives at
  `files/evidence/owlmlx/model-release-candidates/20260505T073943Z-deepseek-v4-flash-2bit-dq/record.json`.
  Verdict is `experimental_only`, with `repeat_count = 1`,
  `failure_count = 0`, `tokens_per_second = 31.804`,
  `wall_clock_ms = 43665`, sampled `peak_resident_set_bytes = 58170621952`,
  and sampled `memory_headroom_bytes = 79268331520`. The runtime stdout also
  reported `96.574 GB` peak memory; this discrepancy is preserved as pressure
  lane evidence, not normalized away.
- The cumulative model RC ledger now has four records at
  `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`:
  A1, A2, A3, and D1. `history.records` is the authoritative matrix view.
  Because D1 is the newest appended record, `latest` now returns the
  experimental DeepSeek record; OwlOps and OwlCoda must not treat `latest` as
  the mainline matrix verdict.
- Current mainline status: all three selected mainline models have live
  repeated operation evidence and remain `needs_optimization`; none is
  `pass`. The common blockers are OwlOps matrix observation and same-host
  reference runtime comparison. `Qwen3.6-35B-A3B` also has the short generation
  quality caveat above.

Next dominant gap:

- OwlOps should consume the cumulative `history.records` matrix and render all
  three mainline records plus the DeepSeek experimental record without
  upgrading any verdict.
- The next owlmlx runtime-owned lane should reduce
  `reference_runtime_comparison_missing` for the mainline models, starting
  with the available same-host oMLX / vMLX comparison path that can be run
  without changing model visibility truth.

Model RC observability v2 result (2026-05-05,
`owlmlx_model_release_candidate_observability_v2_contract_introduced`):

- owlmlx now supports optional runtime-owned observability fields on
  `owlmlx.model_release_candidate_record` without requiring migration of old
  v1 rows: `load_time_ms`, `reload_time_ms`, `unload_time_ms`,
  `queue_wait_ms`, `ttft_ms`, `decode_tokens_per_second`,
  `end_to_end_tokens_per_second`, `resident_mode`, `prompt_template_id`,
  `quality_caveats`, and `memory_peak_source`
- the HTTP runner computes `decode_tokens_per_second` after first token and
  keeps `end_to_end_tokens_per_second` aligned with the legacy
  `tokens_per_second` meaning, so OwlOps can distinguish TTFT-heavy runs from
  genuinely slow decode
- memory peak provenance is explicit through `memory_peak_source`; missing
  sources remain absent or `null` and must not be synthesized
- output sanity caveats remain runtime-owned and are derived from
  `output_sanity_label` plus blockers, without creating model-quality claims
- DeepSeek remains `flagship_experimental` / `experimental_only`; isolated CLI
  pressure evidence must not be normalized into an owlmlx HTTP adapter pass
- legacy cumulative-ledger rows remain valid; no historical record is
  backfilled or normalized into a stronger claim
- OwlOps follow-up prompt archived at
  `files/execution-prompts/owlmlx/owlops-model-rc-observability-v2-consumer-workspace.md`

Next dominant gap:

- OwlOps consumes the optional observability v2 fields when present and labels
  them `upstream_missing` when absent; OwlOps must not compute decode speed or
  phase timings locally from legacy rows.
- After OwlOps renders the fields, owlmlx should rerun one mainline model with
  the v2 runner to prove the full ops-observable path before repeating the
  whole matrix.

Model RC v2 mainline rerun result (2026-05-05,
`owlmlx_model_release_candidate_v2_mainline_records_published`):

- three new mainline records with observability v2 fields were appended to the
  cumulative ledger; `GET /v1/runtime/model-release-candidates/history` now
  returns seven records: the original four baseline records plus v2 records
  for `Qwen3.6-27B`, `Qwen3.6-35B-A3B`, and `gemma-4-31B-it`
- `Qwen3.6-27B`: `needs_optimization`, `repeat_count = 2`,
  `failure_count = 0`, `load_time_ms = 10188.202`,
  `reload_time_ms = 9435.728`, `unload_time_ms = 530.493`,
  `ttft_ms = 2890.414`, `decode_tokens_per_second = 4.135`,
  `end_to_end_tokens_per_second = 3.105`,
  `memory_peak_source = process_tree_rss`, `output_sanity_label = valid_text`
- `Qwen3.6-35B-A3B`: `needs_optimization`, `repeat_count = 2`,
  `failure_count = 0`, `load_time_ms = 15680.213`,
  `reload_time_ms = 17496.333`, `unload_time_ms = 818.888`,
  `ttft_ms = 6187.685`, `decode_tokens_per_second = 29.941`,
  `end_to_end_tokens_per_second = 7.718`,
  `memory_peak_source = process_tree_rss`,
  `output_sanity_label = reasoning_trace_truncated`; this shows decode is
  materially faster than end-to-end throughput, while TTFT and reasoning-trace
  truncation remain the dominant visible bottlenecks
- `gemma-4-31B-it`: `needs_optimization`, `repeat_count = 2`,
  `failure_count = 0`, `load_time_ms = 10957.576`,
  `reload_time_ms = 10946.711`, `unload_time_ms = 705.492`,
  `ttft_ms = 4220.365`, `decode_tokens_per_second = 3.009`,
  `end_to_end_tokens_per_second = 2.544`,
  `memory_peak_source = process_tree_rss`,
  `output_sanity_label = repetitive_output`; the first Gemma v2 run exposed a
  prompt-echo repetition that the classifier initially missed, so the runner
  was narrowed and Gemma was rerun instead of mutating the old record
- the failed `Qwen3.6-27B` v2 preflight without `--memory-gb` is preserved as
  local evidence but is not included in the cumulative ledger
- all three v2 records keep `verdict = needs_optimization`; no `pass`,
  release-ready, parity, replacement, or production-grade claim is made

Next dominant gap:

- OwlOps R166 should render the seven-record history and confirm that v2
  fields appear for the three newest mainline rows while old rows remain
  `upstream_missing`.
- owlmlx should start model-specific optimization lanes from this evidence:
  Qwen3.6-27B decode speed, Qwen3.6-35B TTFT / reasoning-template behavior,
  and Gemma prompt-template repetition.

OwlOps R166 / owlmlx Gemma mainline return (2026-05-05,
`owlmlx_model_release_candidate_gemma_chat_template_probe_narrowed`):

- OwlOps R166 consumed the seven-record v2 history and confirmed that the
  current matrix uses the newest record per `model_id`, old v1 rows render as
  `upstream_missing`, and DeepSeek remains `experimental_only` /
  `not_registered` outside the mainline summary.
- owlmlx returned to the mainline by adding an `openai_chat_stream` request
  mode to `scripts/runtime_model_release_candidate.py`; this lets Model RC
  evidence route through `/v1/chat/completions` so tokenizer chat templates
  apply instead of forcing every model through raw `/v1/generate/stream`.
- The runner now records `request_mode` and `prompt_template_id` in
  `runner-config.json`; new records can distinguish `operator_prompt_raw`
  from `gemma_openai_chat_template_v1` or other family-profile paths.
- The output sanity classifier was tightened after a live Gemma probe exposed
  `<|channel>thought` content that the old classifier would have mislabeled as
  `valid_text`. Both `<think>` and `<|channel>thought` traces now map to
  `reasoning_trace_truncated` or `reasoning_trace_visible` instead of a
  healthy-text label.
- The corrected Gemma chat-template rerun appended the eighth cumulative
  record at
  `files/evidence/owlmlx/model-release-candidates/20260505T-mainline-gemma-chat-template-classifier-rerun/record.json`.
  It completed two live HTTP runs with `failure_count = 0`,
  `output_sanity_label = reasoning_trace_truncated`,
  `prompt_template_id = gemma_openai_chat_template_v1`,
  `ttft_ms = 12294.993`, `decode_tokens_per_second = 2.309`,
  `end_to_end_tokens_per_second = 1.617`,
  `peak_resident_set_bytes = 35297640448`, and
  `verdict = needs_optimization`.
- The previous chat-template probe that produced a `valid_text` label was
  excluded from the cumulative ledger after the classifier bug was found. Its
  evidence directory remains local forensic evidence, but `GET
  /v1/runtime/model-release-candidates/history` now exposes eight records and
  the current Gemma row is the corrected `reasoning_trace_truncated` record.

Next dominant gap:

- Gemma is no longer primarily a raw-prompt repetition problem. The next
  Gemma lane should test family-profile controls that suppress visible
  reasoning/channel traces or force final-answer-only output without hiding
  failures.
- Qwen3.6-35B-A3B shares a reasoning-trace / high-TTFT shape and should be
  paired with the same template/thinking-control investigation after Gemma's
  smallest profile experiment is selected.
- Qwen3.6-27B remains the decode-speed lane because its output is valid but
  its `decode_tokens_per_second` remains low.

owlmlx Gemma post-run health gate return (2026-05-06,
`owlmlx_model_rc_gemma_post_run_health_gate_clean_latest_row`):

- `8066` was restarted persistently in tmux session
  `owlmlx-8066-model-rc-20260506`; post-run `healthz` after the current
  latest Gemma row is clean (`ok=true`, `backend_error=null`,
  `active_model_id=null`, `model_count=0`).
- The runner now bridges model-load admission to `/v1/load` by deriving
  `memory_gb` from `known_peak_resident_set_bytes` when no explicit
  `--memory-gb` is provided, and writes the actual load request payload into
  repeat evidence.
- The previous clean Gemma row was
  `files/evidence/owlmlx/model-release-candidates/20260506T021105Z-gemma-4-31b-it-post-run-health-gate-rerun/record.json`.
  It used explicit `--memory-gb 60`, completed two repeats, and appended to
  `cumulative-ledger.jsonl` with `verdict = needs_optimization`,
  `failure_count = 0`, `repeat_count = 2`,
  `output_sanity_label = reasoning_trace_truncated`,
  `ttft_ms = 51229.148`, `decode_tokens_per_second = 14.744`, and
  `peak_resident_set_bytes = 50295062528`.
- Earlier 2026-05-06 Gemma blocked attempts remain honest local evidence; the
  cumulative ledger includes the unload-failed attempt before the latest clean
  row. The current latest-per-model truth is no longer
  `post_run_backend_unhealthy`.

Next dominant gap:

- Gemma post-run backend health should not be reopened unless a new row
  reproduces `post_run_backend_unhealthy`.
- The next owlmlx-owned closure round should target
  `gemma_reasoning_trace_profile_control_and_ttft_variance`: suppress or route
  visible `<|channel>thought` traces without hiding failures, and track TTFT
  variance separately from output-sanity labels.

Parallel closure setup (2026-05-06,
`owlmlx_model_rc_gemma_trace_policy_and_ttft_observability`):

- `owlmlx.reasoning_trace_policy:v1` now makes visible Gemma-style reasoning
  traces a runtime-owned evidence contract rather than an ad hoc classifier
  branch. It can expose a final-text candidate only when the candidate is
  safely outside the visible trace boundary.
- The Model RC runner now writes per-generation `reasoning_trace_policy` and
  `timing_breakdown` evidence. This prepares the next live Gemma proof to
  answer two separate questions: whether output control is platform-handled,
  and whether TTFT is concentrated before first token or after it.
- The current claim remains conservative: output dirtiness is now being handled
  as a platform profile/serving-contract gap first; model fine-tuning should
  not be blamed until the platform applies the family trace policy in live
  evidence and still fails to produce usable final-answer text.

Live profile-control return (2026-05-06,
`owlmlx_model_rc_gemma_final_answer_control_live_proof`):

- The first fresh heavy Gemma row with live `reasoning_trace_policy` and
  `timing_breakdown` evidence is
  `files/evidence/owlmlx/model-release-candidates/20260506T024418Z-gemma-4-31b-it-final-answer-control-rerun/record.json`.
- It applied `--apply-model-profile-defaults` plus Gemma's experimental
  final-answer-only user-message prompt-control, completed two repeats, appended
  to `cumulative-ledger.jsonl`, and left post-run health clean (`ok=true`,
  `backend_error=null`, `active_model_id=null`, `model_count=0`).
- Current latest Gemma values are `verdict = needs_optimization`,
  `failure_count = 0`, `repeat_count = 2`,
  `output_sanity_label = reasoning_trace_truncated`,
  `ttft_ms = 5104.511`, `decode_tokens_per_second = 7.203`, and
  `peak_resident_set_bytes = 38314049536`.
- The final-answer-only prompt-control did not suppress visible
  `<|channel>thought`; the trace policy recorded `trace_status=truncated`,
  `visible_reasoning_trace=true`, and `final_text=null`.
- TTFT remains not root-caused. The prior clean row averaged `51229.148ms`, but
  the latest row showed repeat-level first-token latencies around `4.6s-5.6s`
  and post-first-token decode wall time around `8.5s-9.0s`.

Next dominant gap:

- Retire the old dirty post-run backend gap unless a future row records
  `post_run_backend_unhealthy`.
- Do not repeat the same final-answer-only user-message prompt-control as if it
  were untested. The next closure round is
  `gemma_final_channel_template_control_and_ttft_repro_boundary`: test stronger
  template-level final-channel framing, stop-token application in the HTTP
  surface, or a serving path that can separate thought/final channels while
  preserving failure visibility.

Stop-token-control return (2026-05-06,
`owlmlx_model_rc_gemma_stop_token_control_live_proof`):

- `owlmlx` now accepts OpenAI-compatible `stop` on `/v1/chat/completions` and
  `/v1/completions`, forwards it into the child runner params, strips it before
  calling `mlx_lm`, and enforces stop strings on both non-streaming and
  streaming outputs.
- The Model RC runner now records the actual per-repeat generation
  `request_payload`, so profile-applied `stop` is visible in
  `repeat-XX-generation.json` instead of only inferred from runner config.
- The latest Gemma row is
  `files/evidence/owlmlx/model-release-candidates/20260506T-mainline-gemma-stop-request-payload-rerun/record.json`.
  It applied profile stop tokens as `stop = ["<eos>", "<turn|>"]`, completed
  two repeats, recorded the actual generation `request_payload`, appended to
  `cumulative-ledger.jsonl`, and left post-run health clean.
- Current latest Gemma values are `verdict = needs_optimization`,
  `failure_count = 0`, `repeat_count = 2`,
  `output_sanity_label = reasoning_trace_truncated`,
  `ttft_ms = 24322.913`, `decode_tokens_per_second = 7.688`, and
  `peak_resident_set_bytes = 33050263552`.
- Stop-token application did not suppress visible `<|channel>thought`; both
  repeats reached `finish_reason = length` with no safe final channel. That
  narrows the active output-cleanliness gap from "did the platform apply
  family controls?" to "which template/final-channel/serving control can
  produce or extract a safe final channel without hiding visible trace
  failures?"
- TTFT variance is now reproduced enough to separate the immediate spike from
  decode speed. The latest repeats showed first-token latency around `41.9s`
  and `6.7s`, while post-first-token decode wall time stayed near `8.2s-8.5s`.
  The current evidence therefore points at volatile pre-first-token work for
  the spike, plus a stable slower decode component around `7.7` tok/s.

Next dominant gap:

- Continue from
  `gemma_final_channel_template_or_serving_boundary_and_ttft_repro`: do not
  repeat final-answer-only prompt-control or stop-token-control as if either
  were untested.

## 3. Ownership Model

Coordinator:

- owns floor ordering
- freezes the active floor before each round
- rejects work that does not reduce the active floor
- updates `release-readiness-backlog.md` only when the evidence threshold is met

Executor:

- owns implementation, docs, tests, and command evidence for the active floor
- may not switch floors without coordinator approval
- must report changed files, tests/live checks, verdict, and deferred scope

Reviewer:

- verifies the executor's claims against code, docs, tests, and live output
- must reject exactness-only progress if the floor requires runtime capability
- must reject release/parity wording until all floors close

### 3.1 Multi-Model Compute Scheduling Mapping

The previously discussed multi-model compute-scheduling problem is included,
but it is not a single isolated floor. It is a cross-cutting release gate across
four floor items:

- request / dispatch scheduling
  - release floor: `3.1 Cache Scheduler Closure`
  - required answer: which request may run next, and whether bounded
    aggregation or dispatch-level scheduling exists beyond marker exactness
- model placement and residency
  - release floor: `3.3 Model Residency Non-Resident Path`
  - required answer: when a target model is not resident, should the runtime
    admit-and-load, defer, or reject under current budget and pressure truth
- memory / residency sacrifice under pressure
  - release floor: `3.2 Memory-Pressure Decision Closure`
  - required answer: which resident model or cache state is sacrificed first,
    and whether the eviction/reclaim action updates runtime truth atomically
- recovery after failed scheduling cleanup
  - release floor: `3.4 Recovery Policy Closure`
  - required answer: what happens when unload, reclaim, restart, or recovery
    leaves the runtime in an unsafe state

This means multi-model compute scheduling is not considered closed until:

- admission can explain why a request runs now, waits, or fails
- non-resident model targets have deterministic load/defer/reject semantics
- memory pressure can choose and execute a victim transition
- recovery policy can fail closed after cleanup or restart failures
- tests or live/runtime evidence show these decisions under repeated or
  competing workload conditions

Current limitation:

- `owlmlx` does not yet own a separate CPU/GPU/Metal compute-capacity contract
  with per-model cost accounting, active compute-slot accounting, or fairness
  weights. The current plan treats compute scheduling through admission,
  residency, memory pressure, and recovery surfaces. If a later release target
  requires explicit Metal/compute accounting, this plan must add a new floor or
  split one out from floors `3.1` and `3.2`.

## 4. Execution Order

### Stage 0: Coordination Reset

Status:

- active now

Required result:

- `release-readiness-backlog.md` governs the loop
- side prompts are parked unless they directly reduce an active floor
- the next active prompt is floor `3.1`

Current active prompt:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1-cache-scheduler-closure.md`

Parked prompt:

- `files/execution-prompts/owlmlx/owlmlx-failed-unload-reclaim-barrier-event.md`
  - useful later for floor `3.4`
  - not current active work

### Stage 1: Floor 3.1 Cache Scheduler Closure

Primary owner:

- executor

Reviewer owner:

- reviewer after executor produces changed files and verification output

Current A/B split:

- Executor A:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1A-pre-gate-test-truth-restoration.md`
  - owns the red pre-gate seam test family and any minimal implementation fix
    required to make that test truth honest
- Executor B:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B-cache-scheduler-capability-audit.md`
  - owns independent non-exactness scheduler capability audit and evidence
    mapping, without editing A-owned code/tests
- Coordinator:
  - merges A's green/red gate result with B's capability audit before deciding
    whether floor `3.1` is closed, progressed, or still blocked

Next A/B split after the first A/B results:

- Executor A2:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1A2-repeated-dispatch-proof.md`
  - owns the smallest implementation/test proof for repeated-load
    non-exactness scheduler behavior, but only after A1 restores the red
    pre-gate test truth
- Executor B2:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1B2-floor-verdict-review.md`
  - owns read-only merge review of A1/A2/B1 evidence and the floor `3.1`
    verdict recommendation
- Coordinator:
  - does not mark floor `3.1` closed until A2 implementation evidence and B2
    review both satisfy the release-floor criteria

Closeout split after A2 evidence appears:

- Coordinator / Reviewer C:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-closeout-review-and-ledger-decision.md`
  - owns final floor `3.1` closure/progress/still-blocked decision
  - may update `release-readiness-backlog.md` only if the full section-3.1
    release-floor requirement is met
- Executor C-A:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-A-verification-runner.md`
  - owns command verification and a read-only evidence handoff
  - must not edit release ledger docs
- Executor C-B:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-1C-B-ledger-truth-decision.md`
  - owns truth/ledger decision after C-A evidence exists
  - must not edit runtime code or tests

Why first:

- `phase45-dominant-gap-reselection.md` already selects
  `cache_scheduler_depth`
- active seam is `owlmlx.cache_request_aggregation_active_seam`
- current test gate is red:
  `pytest -q tests/test_cache_pre_gate_admission_window_seam.py` reports
  `3 failed, 2 passed`

Required deliverables:

- restore the `test_cache_pre_gate_admission_window_seam_*` family to truthful
  green or document a hard downgrade
- prove one non-exactness scheduler capability on the active runtime path, or
  identify the smallest missing runtime capability
- update release truth without marking floor closed unless section 3.1 of
  `release-readiness-backlog.md` is fully met

Expected effort:

- minimum: 1 round to restore test truth and produce a hard floor verdict
- likely: 2-4 rounds if observable aggregated dispatch under repeated load can
  be reached from existing runtime surfaces
- high-risk path: 5+ rounds if actual dispatch-level scheduler work is missing

Exit criteria:

- floor `3.1` closed, or
- an exact blocker exists in floor language with tests proving the blocker

Closeout (2026-04-25, Round C `owlmlx_release_floor_3_1C_closeout_closed`):

- floor `3.1` is closed via the non-stream main runtime path
  (`RuntimeKernel.generate` → `GenerationGate.execute_async_cohort_with_admission`
  → `backend.generate_cohort`) with repeated-load proof in
  `tests/test_runtime_kernel.py::test_repeated_concurrent_generations_show_aggregated_dispatch_under_repeated_load`
  and the bounded pre-gate cohort/aggregated child-exchange capability already
  proven by the existing harness tests
- stream-branch dispatch-level closure is **not** required for floor `3.1`
  closure under the backlog's literal "one closed non-exactness scheduler
  capability" language, but the stream-hold seam blocker
  `backend_stream_exchange_holds_serial_boundary_until_terminal_notice_leading_discriminator_marker_earlier_runtime_owned_boundary_stem_detection`
  remains the active phase45 seam and stays preserved as secondary truth in
  `phase45-request-aggregation-active-seam.md`
- this closure does **not** imply release readiness, parity, replacement, or
  production-grade; floors `3.2`, `3.3`, `3.4`, `3.5`, `3.6`, `3.7` remain open

### Stage 2: Floors 3.3 Then 3.2

Order:

1. `3.3 Model Residency Non-Resident Path`
2. `3.2 Memory-Pressure Decision Closure`

Why this order:

- eviction decisions need a governed answer for non-resident targets and
  residency transitions
- pressure classification without residency action remains observability, not
  release behavior

Required deliverables for `3.3`:

- deterministic `admit_and_load / defer / reject` policy for non-resident
  target models under budget and pressure inputs
- round-trip through residency, lineage, and pressure surfaces

Current A/B split for `3.3`:

- Executor A:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A-nonresident-admission-policy.md`
  - owns the implementation, tests, runtime endpoint, source-of-truth doc, and
    handoff for the non-resident admission policy
- Executor B:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B-residency-pressure-review.md`
  - owns scoped review of A's policy and evidence, with particular attention to
    residency/pressure/recovery boundaries and preventing accidental floor
    `3.2` eviction claims from being smuggled into `3.3`
- Coordinator:
  - may mark floor `3.3` closed only after A returns implementation evidence
    and B returns `pass`; otherwise record `progressed` or `still_blocked`
    with the exact missing runtime signal

Current post-A review step:

- Executor A returned
  `owlmlx_release_floor_3_3A_nonresident_admission_policy_progressed`
  after introducing `owlmlx.nonresident_model_admission_policy`,
  `GET /v1/runtime/nonresident-model-admission-policy`, docs, tests, and a
  handoff
- B's first handoff was a Pre-A audit map with
  `blocked_waiting_for_A`; it does not review A's implementation and must not
  be treated as the current floor verdict
- Reviewer B2:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B2-post-A-nonresident-policy-review.md`
  - owns post-A review and must decide whether A's `progressed` verdict is
    valid, whether any needs-fix findings block it, and whether the next
    exact blocker is
    `runtime_owned_non_resident_loadability_lineage`

B2 result:

- B2 returned
  `owlmlx_release_floor_3_3B2_post_A_review_pass_progressed_confirmed`
- no blocking findings
- floor `3.3` remains `progressed`, not `closed`
- the confirmed next blocker is exactly
  `runtime_owned_non_resident_loadability_lineage`

Current A2 implementation step:

- Executor A2:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3A2-nonresident-loadability-lineage.md`
  - owns the runtime-owned non-resident loadability lineage contract and its
    integration into `owlmlx.nonresident_model_admission_policy`
  - must not implement automatic loading, pressure eviction, or any other floor

A2 round result (2026-04-25,
`owlmlx_release_floor_3_3A2_loadability_lineage_candidate_closed_pending_review`):

- new contract `owlmlx.nonresident_loadability_lineage` lives at
  `owlmlx/nonresident_loadability_lineage.py`, transport at
  `GET /v1/runtime/nonresident-loadability-lineage`, docs at
  `docs/source-of-truth/nonresident-loadability-lineage.md`,
  tests at `tests/test_nonresident_loadability_lineage.py`
- the contract returns exactly one of `known_loadable / not_loadable /
  unknown`, consumes `runtime_model_visibility` (registry + artifact gate)
  and `model_lineage` (validation + alignment), and rejects request-level
  hints as the source of truth
- `nonresident_model_admission_policy` now consumes the new contract; when
  `loadability_lineage` returns `known_loadable`, admission can produce
  `admit_and_load` without any `known_loadable_model_ids` hint, proven by an
  HTTP integration test
- `release-readiness-backlog.md` section 5 is **not** moved by A2; the row
  for `3.3` stays `open` until the next B review confirms closure

Current B3 closure-review step:

- Reviewer B3:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B3-loadability-lineage-closure-review.md`
  - should be run by an executor that did not author A2, to avoid self-review
  - owns independent verification of the loadability-lineage round trip and
    ledger recommendation
- if B3 confirms closure, the coordinator may flip
  `release-readiness-backlog.md` section 5 row `3.3` from `open` to
  `closed (via runtime-owned loadability lineage)`

B3 closeout (2026-04-25,
`owlmlx_release_floor_3_3B3_closure_review_pass_closed_recommended`):

- B3 ran via an independent reviewer context (not the A2 author) and
  produced
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-3B3-loadability-lineage-closure-review-handoff.md`
- B3 verdict: `pass`; recommendation: `closed_recommended`; aggregate
  123 tests pass, py_compile clean, `git diff --check` clean; all eight
  blocking-finding tripwires from B3 §4 held
- coordinator action applied 2026-04-25: section 5 row for `3.3` flipped
  from `open` to `closed (via runtime-owned loadability lineage)` with
  references to the lineage contract docs, the two test files, the A2
  handoff, and the B3 handoff; section 2 floor count moved from `1/7` to
  `2/7`
- this closure does **not** imply replacement-grade scheduler/cache
  closure or release readiness; floors `3.2`, `3.4`, `3.5`, `3.6`, `3.7`
  remain open

Required deliverables for `3.2`:

- deterministic eviction-candidate ordering under pressure
- runtime-owned execution path that updates residency and eviction history
- repeated-load test showing pressure causes observable residency change

Current A/B split for `3.2`:

- Executor A:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution.md`
  - owns the decision surface, runtime execution path, docs, tests, and handoff
  - must preserve `GenerationGate` invariants and must not implement broad
    reclaim or automatic background eviction
- Reviewer B:
  - prompt:
    `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2B-memory-pressure-eviction-review.md`
  - should be run by an executor that did not author A
  - owns scoped review of whether A really closed both decision and execution
    requirements, rather than merely improving pressure observability
- Coordinator:
  - may move floor `3.2` to `closed` only after A reaches candidate closure and
    B returns `pass_closed_recommended`

Expected effort:

- floor `3.3`: 2-4 rounds
- floor `3.2`: 3-6 rounds

Exit criteria:

- non-resident switching is governed
- pressure no longer stops at classification-only truth

### Stage 3: Floor 3.4 Recovery Policy Closure

Primary owner:

- executor

Inputs:

- existing `recovery_supervisor_contract`
- later use of the parked failed-unload/reclaim prompt if it still matches
  current truth
- pre-flight notes:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4-pre-flight-notes.md`

Required deliverables:

- frozen policy per termination cause class:
  `retry / quarantine / surface_to_coordinator / drop`
- coverage for load failure, OOM-class failure, host forensics anomaly, and
  graceful unload
- tests exercising the policy, not only docs

Sequencing decision after the 2026-04-26 recoordination pass:

- do not pre-split or pre-assign multiple 3.4 executors
- after `3.2C` closes, issue exactly one next prompt
- preferred next prompt: `3.4A0` as a failed-unload/reclaim barrier event
  sub-round, seeded by
  `files/execution-prompts/owlmlx/owlmlx-failed-unload-reclaim-barrier-event.md`
- only after `3.4A0` returns should the coordinator decide whether the next
  single prompt is full four-class termination-cause policy work
- do not start any `3.4` implementation before the `3.2` ledger row closes

Expected effort:

- 3-5 rounds

Exit criteria:

- upper layers can trust runtime recovery posture across failures they did not
  cause

### Stage 4: Floor 3.5 Comparative Evidence

Primary owner:

- executor

Current parallel status:

- this stage may start as a schema/surface preparation lane while floor `3.1`
  remains the main release burn-down lane
- it must not mark floor `3.5` closed until the measured-record closure criteria
  in `comparative-evidence-harness-contract.md` section 8 are satisfied
- active prompt:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5-comparative-evidence-schema-and-record-surface.md`
- external-blocker prompt for OwlOps R156:
  `files/execution-prompts/owlmlx/owlmlx-comparative-evidence-surface-for-owlops-r156.md`

Required deliverables:

- in-repo benchmark harness with identical workload against `owlmlx` and at
  least one reference runtime on the same host
- throughput, first-token latency, peak resident set, and frozen verdict
- verdict must not auto-promote to parity or replacement

Expected effort:

- 2-4 rounds if reference runtime invocation is already stable
- longer if the host/runtime setup is not reproducible

Exit criteria:

- replacement discussion is evidence-based, not rhetorical

### Stage 5: Floor 3.7 Public Surface

Primary owner:

- coordinator plus executor

Required deliverables:

- frozen `public-surface.md` or equivalent
- supported modules, contracts, and CLIs named exactly
- all non-listed surfaces explicitly internal

Expected effort:

- 1-2 rounds

Exit criteria:

- a technical-preview surface can be discussed without exposing internal seams

### Stage 6: Floor 3.6 External Customer Evidence

Primary owner:

- coordinator for evidence requirement
- external deployment owner for real-world run
- executor only for instrumentation/supporting fixes

Required deliverables:

- at least one external deployment evidence record with host class, workload
  class, frozen pass/fail verdict, and blocker/success outcome

Expected effort:

- cannot be honestly estimated from repo-only work
- earliest start should be after floors `3.1`, `3.3`, and `3.4` have enough
  closure to make an external run meaningful

Exit criteria:

- external evidence exists in the ledger

## 5. Time Estimate

These are round estimates, not readiness promises.

Assuming one focused executor round is about 2-3 hours:

- fastest meaningful internal technical-preview floor burn-down:
  12-20 focused rounds
- realistic internal release-floor burn-down:
  18-30 focused rounds
- full release floor including external evidence:
  cannot be promised until an external deployment owner and host are assigned

Calendar estimate if execution is continuous:

- internal floor closure: roughly 1-3 focused weeks depending on whether floor
  `3.1` and floor `3.2` require new runtime implementation
- external release claim: gated by floor `3.6`; no honest date yet

The main schedule risks are:

- `3.1` may reveal that observable aggregated dispatch does not exist yet
- `3.2` may require real eviction execution, not only ordering
- `3.6` depends on non-repo external deployment evidence

## 6. Immediate Next Step

OwlOps R156 external dependency surface (2026-04-26 closeout):

- OwlOps R156 was blocked on a live upstream `owlmlx` comparative evidence
  endpoint, not on OwlOps local wiring
- owlmlx-side prompt:
  `files/execution-prompts/owlmlx/owlmlx-comparative-evidence-surface-for-owlops-r156.md`
- 2026-04-26 outcome:
  `owlmlx_release_floor_3_5_owlops_r156_surface_closed`
  - both `GET /v1/runtime/comparative-evidence` and
    `GET /v1/runtime/comparative-evidence/history` are mounted, tested,
    and live-curl verified against a real `uvicorn` process on
    `127.0.0.1:8056`
  - the runtime-owned record contract
    (`owlmlx.comparative_evidence_record` v1), schema authority
    (`owlmlx.comparative_evidence_schema`), JSONL ledger
    (`owlmlx.comparative_evidence_ledger`), and operator entry
    (`scripts/runtime_comparative_evidence.py`) all exist
  - one real `verdict_grade = "rejected"` record (reason
    `reference_runtime_unavailable`) was emitted and served by both
    endpoints; this is honest harness-failure evidence per
    `comparative-evidence-harness-contract.md` §5.4
- this does **not** close release floor `3.5`; measured same-host
  evidence (`verdict_grade = "measured"`) is still required for floor
  closure per `comparative-evidence-harness-contract.md` §8 third
  bullet
- OwlOps R156 may now be unblocked: the live upstream surface exists
  and is consumable

Floors `3.1` and `3.3` closed on 2026-04-25. Floor `3.2` closed on
2026-04-26 via the 3.2C independent closeout review
(`owlmlx_release_floor_3_2C_independent_closeout_closed`). The
release-readiness burn-down active floor is now
`3.4 Recovery Policy Closure` per Stage 3 of this plan.

3.4A0 closeout (2026-04-26,
`owlmlx_release_floor_3_4A0_reclaim_barrier_event_introduced`):

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A0-reclaim-barrier-event.md`
  ran as a single owlmlx executor allocation
- new contract `owlmlx.reclaim_barrier_event` lives at
  `owlmlx/reclaim_barrier_event.py`, transport at
  `GET /v1/runtime/reclaim-barrier-event`, docs at
  `docs/source-of-truth/reclaim-barrier-event.md`, tests at
  `tests/test_reclaim_barrier_event.py`
- `RuntimeKernel` now records cleanup-boundary failure events at the
  exact operation boundary for explicit unload, TTL sweep reclaim, and
  restart unload stage; `status_dict()` exposes them as the diagnostic
  section `reclaim_barrier`
- `recovery_supervisor_contract` now reports
  `recovery_state = "failed_reclaim_barrier"` with hard recovery barrier
  whenever an unresolved event is visible
- `scheduler_admission_contract` rejects via the existing recovery
  hard-barrier path (no duplicated lifecycle logic)
- `orchestration_status` reports
  `summary.bottleneck_layer = "recovery"` when the barrier is active
- `memory_pressure_contract` records that reclaim attempt-result
  visibility now exists, but still keeps reclaim engine, pressure-ranked
  eviction, and recovery loops out of scope
- this round does **not** close release floor `3.4`; the four-class
  termination-cause recovery policy
  (`retry / quarantine / surface_to_coordinator / drop`) and frozen event
  resolution semantics remain future 3.4 work

The next active executor allocation after 3.4A0 closeout is the
follow-on `3.4A` round, which authors the four-class
termination-cause → action policy on top of the cleanup-boundary event
truth introduced here. The coordinator should issue exactly one next
prompt at that time per the single-active-executor rule. Do not run
another executor in parallel before the 3.4A prompt is authored.

3.4A closeout (2026-04-27,
`owlmlx_release_floor_3_4A_termination_recovery_policy_candidate_closed_pending_review`):

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A-termination-recovery-policy.md`
  ran as a single owlmlx executor allocation
- new contract `owlmlx.termination_recovery_policy` lives at
  `owlmlx/termination_recovery_policy.py`, transport at
  `GET /v1/runtime/termination-recovery-policy`, docs at
  `docs/source-of-truth/termination-recovery-policy.md`, tests at
  `tests/test_termination_recovery_policy.py`
- the four required termination cause classes
  (`load_failure / oom_class_failure / host_forensics_anomaly /
  graceful_unload_failure`) plus the fail-safe `unknown` map
  deterministically to one action each:
  retry / surface_to_coordinator / surface_to_coordinator / quarantine
  / surface_to_coordinator
- `drop` remains in the frozen vocabulary but no required cause maps
  to it in this round; the gap is recorded explicitly in
  `missing_signals`
- `RuntimeKernel.load_model` now records a runtime-owned
  `load_failure` event at the operation boundary (excluding
  `invalid_request` preflight and `model_already_loaded` redundant
  paths); budget-preflight failures classify as `oom_class_failure`,
  backend failures classify as generic `load_failure`
- event resolution semantics are runtime-owned: successful follow-up
  `unload_model` / `restart_model` / `load_model` for the same model
  id auto-resolves matching unresolved events; explicit override path
  is `RuntimeKernel.resolve_reclaim_barrier_event(event_id)`;
  final-status look-clean alone never resolves an event
- recovery / admission / orchestration consumption is unchanged from
  3.4A0: the `failed_reclaim_barrier` recovery state continues to
  drive admission rejection and `orchestration_status.bottleneck_layer
  = "recovery"`
- this round produced `candidate_closed_pending_review`; coordinator
  / reviewer must confirm before flipping
  `release-readiness-backlog.md` section 5 row `3.4` from `open` to
  `closed (via runtime-owned termination recovery policy)`
- floor `3.4` row in `release-readiness-backlog.md` is **not** moved
  by this round

Next active executor allocation (issued 2026-04-27):

- prompt:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4B-termination-recovery-policy-closeout-review.md`
- assigned executor: ClaudeCode
- role: independent closeout reviewer and ledger decision
- scope: review / verification / truth update only; no new runtime
  implementation and no floor `3.5` implementation
- ledger rule: only if 3.4B verifies the combined `3.4A0 + 3.4A`
  evidence against `release-readiness-backlog.md` section `3.4`, move
  section-5 row `3.4 recovery policy` from `open` to
  `closed (via runtime-owned termination recovery policy)`

Parallel live-evidence preparation allocation (issued 2026-04-27):

- coordinator packet:
  `files/execution-prompts/owlmlx/owlmlx-two-executor-release-readiness-allocation-20260427.md`
- prompt:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5A0-codex-live-comparative-evidence-preflight.md`
- assigned executor: Codex desktop with Computer Use available for terminal,
  process, port, or screen monitoring
- role: live same-host comparative-evidence preflight and first honest
  measured-run attempt
- scope: no `3.4` ledger edits, no release ledger movement, and no fake
  `verdict_grade = "measured"`; if a same-host measured record is impossible,
  return the exact blocker (`reference_runtime_unavailable`,
  `blocked_missing_weights`, `harness_runner_missing`, or inconclusive live
  state)

These two lanes may proceed together because ownership is disjoint:
ClaudeCode owns the `3.4` closeout gate, while Codex owns `3.5` live
preflight only. After 3.4B confirms closure, the next active floor is
`3.5 Comparative Evidence` (measured-record sub-round on top of the
OwlOps R156 surface), then `3.6` and `3.7`.

3.4B closeout (2026-04-27, `owlmlx_release_floor_3_4B_closeout_closed`):

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4B-termination-recovery-policy-closeout-review.md`
  ran as a single independent ClaudeCode reviewer allocation (no second
  executor lane, no runtime code edits, no `3.5` implementation)
- the reviewer reproduced the full §11 verification matrix:
  `tests/test_termination_recovery_policy.py` 25 passed,
  `tests/test_reclaim_barrier_event.py` 17 passed,
  `tests/test_recovery_supervisor_contract.py +
  tests/test_scheduler_admission_contract.py +
  tests/test_orchestration_status.py` aggregate 28 passed,
  `tests/test_runtime_kernel.py -k "load or unload or reclaim or
  restart or recovery"` 17 passed (8 deselected),
  `tests/test_runtime_server.py -k "termination_recovery or
  reclaim_barrier or recovery_supervisor or orchestration_status"`
  3 passed (38 deselected; new HTTP coverage lives inside the two
  cross-surface test files), full `tests/test_runtime_server.py`
  41 passed; `py_compile` clean for the six modules; `git diff
  --check` clean
- the reviewer answered all 18 §4 closure questions in the affirmative,
  confirming: one frozen recovery policy per termination cause class;
  the four required cause classes
  (`load_failure / oom_class_failure / host_forensics_anomaly /
  graceful_unload_failure`) plus a fail-safe `unknown`; the action
  vocabulary is exactly
  `retry / quarantine / surface_to_coordinator / drop`; each active
  cause maps deterministically to one next action; `drop` being unused
  for a required cause is acceptable because it is in the frozen
  vocabulary and recorded in `missing_signals`; `load_failure` is
  recorded from the `RuntimeKernel.load_model` operation boundary and
  is not inferred from `restart_exhausted_models` alone;
  `oom_class_failure` is distinguished by
  `error_code = "memory_budget_exceeded"`; `host_forensics_anomaly`
  surfaces to coordinator/operator without auto-retry or auto-drop;
  `graceful_unload_failure` consumes unresolved
  `owlmlx.reclaim_barrier_event` truth; event resolution semantics
  are runtime-owned and operation-boundary based, with
  final-status look-clean alone never resolving an event
  (`test_resolution_does_not_happen_from_final_status_alone`);
  read-only routes are GET-only; forbidden automations are absent;
  recovery / admission / orchestration surfaces remain aligned; the
  round stayed inside `/Users/yeemio/AI/gitrep/owlmlx`; one stale
  contradiction in §3.4 "Current state" prose was repaired by the
  reviewer alongside the §5 row flip
- coordinator action applied 2026-04-27: section 5 row for `3.4`
  flipped from `open` to
  `closed (via runtime-owned termination recovery policy)` with
  references to `reclaim-barrier-event.md`,
  `termination-recovery-policy.md`,
  `recovery-supervisor-contract.md`,
  `tests/test_reclaim_barrier_event.py`,
  `tests/test_termination_recovery_policy.py`, the 3.4A0 / 3.4A /
  3.4B handoffs; section 2 floor count moved from `3/7` to `4/7`
- this closure does **not** imply replacement-grade or release
  readiness; floors `3.5`, `3.6`, `3.7` remain open

3.5A0 live preflight (2026-04-27,
`owlmlx_release_floor_3_5A0_harness_runner_missing`):

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5A0-codex-live-comparative-evidence-preflight.md`
  ran as the Codex desktop / Computer Use live preflight lane
- evidence lives under
  `files/evidence/owlmlx/comparative-evidence/20260427T094224Z/`
- `omlx` is available through the local probe venv and returned assistant
  content `OK` for `gemma-4-31B-it`
- `vmlx` is available through the local probe venv and `vmlx doctor`
  passed inference on `gemma-4-31B-it`
- local weights exist at
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- the comparative-evidence HTTP surface served an isolated
  `verdict_grade = "inconclusive"` ledger through a real `uvicorn`
  process, and ports `8059` / `8060` were released after cleanup
- no `verdict_grade = "measured"` record exists; floor `3.5` remains
  open
- exact blocker narrowed to `harness_runner_missing`: the current
  `scripts/runtime_comparative_evidence.py` has only
  `append-rejected-record`, `latest`, and `history`, with no measured
  runner for two repeat runs, metric collection, raw artifacts, or a
  measured ledger append

Next active executor allocation (issued 2026-04-27):

- prompt:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5B-measured-comparative-runner.md`
- assigned executor: ClaudeCode
- role: implement the smallest honest measured comparative runner for
  `single_prompt_short` using the existing schema and ledger
- scope: code/tests/docs/handoff for the runner; do not flip the
  `3.5` backlog row unless a real same-host `verdict_grade =
  "measured"` record exists and is served through HTTP
- expected follow-up: if the runner is introduced but no live measured
  record is produced, send Codex desktop back for live measured-run
  review with process/port monitoring

3.5B runner introduction (2026-04-27,
`owlmlx_release_floor_3_5B_measured_runner_introduced_pending_live_review`):

- new runtime-owned module
  `owlmlx/comparative_evidence_runner.py` owns the subprocess attempt
  executor, RSS sampler (via `psutil`), per-runtime aggregation across
  repeats (mean of successes for latency/throughput/wall-clock; max of
  attempts for peak RSS; sum for completed/failure counts), and the
  three-grade verdict computation: `measured` only when every runtime
  has all configured repeats successful; `inconclusive` on any partial
  failure; `rejected` when any runtime has zero successful attempts
- `scripts/runtime_comparative_evidence.py` exposes a new
  `run-measured-short-prompt` subcommand that takes a runner-config
  JSON (one `owlmlx` entry plus one `reference` entry whose
  `runtime_id` must be in the frozen `RUNTIME_IDS` enumeration),
  executes the configured argv with `{prompt}` / `{max_tokens}` /
  `{temperature}` / `{model_id}` / `{model_path}` placeholder
  substitution, writes per-attempt `*.stdout.txt` / `*.stderr.txt` /
  `*.rss.jsonl` plus `manifest.json` / `commands.json` / `summary.md`
  artifacts, appends exactly one validated v1 record to the supplied
  ledger, and prints the appended record as JSON
- new test file
  `tests/test_runtime_comparative_evidence_measured_runner.py` adds
  28 deterministic-fake-command tests covering CLI shape, attempt
  success / silent / non-zero-exit / spawn-failure paths, runtime
  aggregation, the three-grade verdict policy, banned-vocabulary
  rejection across the full vocabulary, runner-config JSON loading,
  end-to-end measured / inconclusive / rejected CLI flows, HTTP
  surface serving the measured ledger via `TestClient`, and an AST
  check that the runner module imports nothing from OwlOps / OwlCoda
- verification matrix this round: 27 passes
  (`test_comparative_evidence_schema.py` +
  `test_comparative_evidence_record.py`) + 28 passes
  (`test_runtime_comparative_evidence_measured_runner.py`) + 4 passes
  (`test_runtime_server.py -k comparative_evidence`); `py_compile`
  clean; `git diff --check` clean; `python3
  scripts/runtime_comparative_evidence.py --help` lists the new
  subcommand
- this round did **not** attempt the live 58G `gemma-4-31B-it` run on
  this host: 3.5A0 already proved the owlmlx first-smoke path can
  hang past ~133s without returning generated output. Per §8 of the
  3.5B prompt the live measured-run is left to the Codex desktop
  review lane with process/port monitoring; `release-readiness-backlog.md`
  row `3.5` therefore stays `open (contract surface)` until a real
  `verdict_grade = "measured"` record is appended and served by HTTP

Next active executor allocation (issued 2026-04-27):

- prompt:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5C-codex-live-measured-run-review.md`
- assigned executor: Codex desktop with Computer Use
- role: live measured-run review using the new runner
- scope: owns the live invocation of
  `python3 scripts/runtime_comparative_evidence.py
  run-measured-short-prompt --runner-config <live.json> ...`,
  pointing the `owlmlx` argv at a real owlmlx generation entry and the
  `reference` argv at a live `omlx` probe-venv command / HTTP client,
  with process/port supervision so a hung first-smoke can be killed and
  recorded as `inconclusive` rather than blocking the lane
- ledger discipline: the live record must be appended to a dedicated
  evidence-directory ledger; only after one real
  `verdict_grade = "measured"` record exists and is served by both
  comparative-evidence HTTP routes may the coordinator consider
  flipping `release-readiness-backlog.md` row `3.5` to closed

3.5C live review (2026-04-27,
`owlmlx_release_floor_3_5C_measured_runner_needs_fix`):

- Codex desktop with Computer Use ran the live owlmlx + omlx workload
  through the 3.5B runner under
  `files/evidence/owlmlx/comparative-evidence/20260427T133443Z/`, with
  `omlx serve` on port 8061 and the HTTP-served measured ledger on
  port 8062
- the runner produced a schema-valid HTTP-served record with
  `verdict_grade = "measured"`, but the live review **rejected** it
  as closeout evidence because two runner defects make the measured
  fields untrue:
  1. `peak_resident_set_bytes` only sampled the immediate wrapper
     subprocess PID; the real owlmlx MLX child workers and the live
     `omlx serve` process (PID 59803, RSS ~47.9 GB) were not in the
     measurement
  2. `first_token_latency_ms` started at the first non-empty stdout
     line, which for `runtime_large_weight_first_smoke.py` is the
     gate diagnostic JSON, not generated-token output
- ports 8061 and 8062 were released after verification; no
  runner / first-smoke / MLX child / `omlx serve` / uvicorn process
  remained
- coordinator decision: `do_not_close_floor_3_5_yet`. Floor `3.5`
  remains open. The next allocation is a code-lane fix, not another
  blind live run

3.5D runner process-tree + token-detection fix (2026-04-27,
`owlmlx_release_floor_3_5D_measured_runner_process_tree_and_token_detection_fix`):

- `owlmlx/comparative_evidence_runner.py` updated:
  - `RuntimeRunnerConfig` now exposes `external_pids: tuple[int, ...]`
    and `external_pid_file: str | None`; the runner samples those
    PIDs alongside the wrapper PID, so a live `omlx serve` (or any
    long-running reference server) can be measured honestly
  - `_RssSampler` now walks every root PID plus
    `psutil.Process(...).children(recursive=True)` on each tick; the
    JSONL artifact records `per_pid_rss_bytes` and the
    `tick_total_rss_bytes`; reported `peak_resident_set_bytes` is the
    max-over-ticks of that per-tick sum (over-count of shared pages
    is acknowledged in the run summary)
  - `first_token_strategy` is now wired through a `_FirstTokenDetector`
    that supports `first_nonempty_chunk` (default; back-compat),
    `after_marker:<substring>` (defers first-token until a stdout line
    contains the substring), and `regex:<python pattern>` (matches
    each non-empty line); invalid strategies and invalid regex
    patterns are rejected at runner-config load
  - `commands.json` artifact now records `external_pids`,
    `external_pid_file`, and `first_token_strategy` per runtime
- `tests/test_runtime_comparative_evidence_measured_runner.py` adds
  9 new tests (28 → 37 total) covering: process-tree RSS observes a
  forked child; static `external_pids` are sampled; `external_pid_file`
  is read line-by-line; `after_marker:` defers first-token past a
  diagnostic JSON line; `regex:` matches the generation pattern;
  default `first_nonempty_chunk` back-compat preserved; load-time
  rejection of unsupported strategy and invalid regex; round-trip
  loading of `external_pids` and `external_pid_file` from JSON config
- §8 verification matrix: 27 passes
  (`test_comparative_evidence_schema.py` +
  `test_comparative_evidence_record.py`) + 37 passes
  (`test_runtime_comparative_evidence_measured_runner.py`) + 4 passes
  (`test_runtime_server.py -k comparative_evidence`); `py_compile`
  clean; `git diff --check` clean; subcommand `--help` lists the
  same flags
- this round did **not** attempt the live 58G `gemma-4-31B-it` run
  again; per the user's lane discipline (`runner 自己坏了 → 回
  ClaudeCode 修 runner，不再继续盲跑`), the next round must be
  another supervised Codex desktop live measured-run, this time with
  `external_pids` (or `external_pid_file`) pointing at the live
  `omlx serve` PID and `first_token_strategy = "after_marker:..."`
  or `"regex:..."` chosen against the actual owlmlx generation
  stdout shape
- `release-readiness-backlog.md` row `3.5` was **not** modified

Next active executor allocation (issued 2026-04-27):

- prompt:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5E-codex-live-measured-run-rerun.md`
- assigned executor: Codex desktop with Computer Use
- role: supervised live same-host measured-run rerun using the fixed
  3.5D runner
- required live config: the live `omlx serve` PID must be declared via
  `external_pids` or `external_pid_file`; `owlmlx.first_token_strategy`
  must use `after_marker:<substring>` or `regex:<pattern>` chosen from
  the actual stdout shape so first-token timing reflects generated
  output, not diagnostic preamble
- closure discipline: only if the fresh record is
  `verdict_grade = "measured"`, RSS reflects the server/child process
  tree, first-token timing reflects generated output, and both
  comparative-evidence HTTP routes serve the fresh ledger may the
  coordinator consider flipping `release-readiness-backlog.md` row
  `3.5`

3.5E live rerun (2026-04-28,
`owlmlx_release_floor_3_5E_live_measured_record_closed_recommended`):

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5E-codex-live-measured-run-rerun.md`
  ran as the supervised Codex desktop live-measurement lane
- evidence lives under
  `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/`
- fresh ledger contains a closeout-recommended
  `verdict_grade = "measured"` record for `owlmlx` and `omlx` on
  `host_class = "Mac17,6-arm64-macOS-26.4.1-128GB"` and
  `workload_class = "single_prompt_short"`
- both runtimes completed two repeats with `failure_count = 0`;
  `owlmlx.peak_resident_set_bytes = 59764850688`, and
  `omlx.peak_resident_set_bytes = 53823569920`
- `omlx serve` PID `84730` was declared through `external_pid_file`
  and sampled by the runner; `owlmlx.first_token_strategy` used
  `regex:"text":\s*"[^"]+"` and matched generated output `"text":
  " OK."`, not diagnostic JSON
- both comparative-evidence HTTP routes served the fresh ledger with
  `200 OK`; ports `8063` / `8064` were released and no lane-owned
  runner / `omlx serve` / uvicorn / MLX child process remained
- this round recommends closing floor `3.5` but does **not** move
  `release-readiness-backlog.md`; a closeout review must verify the
  evidence first

3.5F closeout review (2026-04-28,
`owlmlx_release_floor_3_5F_closeout_closed`):

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5F-comparative-evidence-closeout-review.md`
  ran as the independent closeout-review lane; no new measured-run
  implementation was performed
- reviewer verification passed:
  `tests/test_comparative_evidence_schema.py` plus
  `tests/test_comparative_evidence_record.py` 27 passed;
  `tests/test_runtime_comparative_evidence_measured_runner.py` 37 passed;
  `tests/test_runtime_server.py -k "comparative_evidence"` 4 passed
  (37 deselected); `py_compile` passed for the comparative-evidence modules,
  operator script, and runtime server; fresh-ledger `latest` and `history`
  CLI reads both returned the measured record; `git diff --check` was clean
- the reviewer answered all 18 closeout questions in the affirmative:
  harness-contract section `8` is satisfied; the runtime-owned record module
  and operator entry exist; the ledger contains a measured record; latest and
  history HTTP captures agree with the fresh ledger; both runtimes ran the
  same workload and invariants on the same host; both completed two repeats
  with `failure_count = 0`; raw stdout/stderr, resource samples, manifest,
  commands, and summary artifacts are present; `omlx` RSS includes external
  live server PID `84730`; `owlmlx` RSS includes wrapper plus child process
  tree; `owlmlx.first_token_strategy = regex:"text":\s*"[^"]+"` matched
  generated output `"text": " OK."`; cleanup released ports `8063` / `8064`;
  and the record avoids banned verdict vocabulary
- coordinator action applied 2026-04-28: `release-readiness-backlog.md`
  row `3.5 comparative evidence` flipped from `open (contract surface)` to
  `closed (via same-host measured comparative evidence)` with references to
  the harness contract, schema stub, measured runner test, operator script,
  fresh ledger, manifest, HTTP captures, the 3.5E handoff, and the 3.5F
  handoff
- this closure does **not** imply release readiness, parity, replacement,
  production-grade, or superiority; floors `3.6` and `3.7` remain open

Next active executor allocation (issued 2026-04-28):

- coordinator packet:
  `files/execution-prompts/owlmlx/owlmlx-final-two-floor-sprint-allocation-20260428.md`
- Executor A:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-6A-external-customer-evidence-minimum-record.md`
  - assigned executor: Codex desktop with Computer Use
  - role: acquire or freeze one external deployment evidence record with
    host class, workload class, frozen pass/fail/blocker verdict, and
    external blocker/success outcome
  - boundary: no external repo edits and no `release-readiness-backlog.md`
    flip in this lane
- Executor B:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-7A-public-surface-freeze.md`
  - assigned executor: ClaudeCode
  - role: freeze `docs/source-of-truth/public-surface.md`, add narrow
    validation, and return a closeout recommendation
  - boundary: no external deployment work and no release-ready claim while
    `3.6` remains open

These lanes may run in parallel because `3.6` owns external deployment
evidence while `3.7` owns public-surface boundary truth. If both return
closeout-recommended, the coordinator should run one final ledger-sync
closeout for the remaining release floors.

3.6A external customer evidence candidate (2026-04-28,
`owlmlx_release_floor_3_6A_external_customer_evidence_pass_candidate`):

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-6A-external-customer-evidence-minimum-record.md`
  ran as the Codex desktop external-evidence lane
- evidence lives under
  `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/`
- external deployment / consumer boundary:
  `/Users/yeemio/AI/gitrep/owlops` issuing live HTTP requests to an
  `owlmlx` runtime service on `127.0.0.1:8065`
- workload class: `external_runtime_status_probe`
- runtime surfaces used: `GET /v1/runtime/status` and `GET /healthz`
- verdict recorded in
  `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`:
  `pass`
- external success: OwlOps-boundary external consumer successfully fetched
  `owlmlx` runtime status and health truth over HTTP from outside the
  `owlmlx` repository
- verification: `tests/test_customer_runtime_evidence.py` 53 passed;
  `scripts/runtime_customer_runtime_evidence.py --help` printed help;
  `py_compile` passed for `owlmlx/customer_runtime_evidence.py` and
  `scripts/runtime_customer_runtime_evidence.py`; the external HTTP probe
  exited `0` with empty stderr; `git diff --check` was clean
- cleanup: uvicorn PID `67075` was terminated, and port `8065` had no
  remaining listener
- this is closeout-recommended for floor `3.6`, but this lane did **not**
  flip `release-readiness-backlog.md`; a closeout reviewer / coordinator
  should decide whether to move row `3.6` to closed after reviewing this
  record and the parallel `3.7A` result
- no release, parity, replacement, production-grade, superiority, wins, beats,
  or equivalent claim was made

3.7A public surface freeze (2026-04-28,
`owlmlx_release_floor_3_7A_public_surface_closed_recommended`):

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-7A-public-surface-freeze.md`
  ran as the ClaudeCode public-surface lane
- new authoritative doc `docs/source-of-truth/public-surface.md` freezes the
  technical-preview boundary with stable label vocabulary
  (`supported / partial / experimental / internal / not in scope`),
  the supported HTTP routes (liveness, status, generation, OpenAI / Anthropic
  compatibility, lifecycle, model visibility, every release-floor contract
  surface, and both comparative-evidence routes), the supported runtime
  Python modules, the supported operator scripts, and the supported
  source-of-truth contracts
- §7 records the public consumer rules; §8 records the
  internal-only surfaces (the entire `scripts/runtime_cache_*` family,
  every `owlmlx.cache_*` module, every `phase45-*` doc except those
  explicitly linked, and the kernel's `_*` private methods); §10 ties the
  banned-vocabulary listing back to
  `owlmlx.comparative_evidence_schema.BANNED_VERDICT_VOCABULARY`; §11
  freezes the additive-change rule and the deprecation cycle for breaking
  changes; §12 records the restart condition
- new validation test `tests/test_public_surface_contract.py` (12 cases)
  asserts: doc exists, label vocabulary present, internal-default rule
  declared, banned-verdict vocabulary cross-reference present, "Explicitly
  Unsupported Claims" section present, every referenced
  `docs/source-of-truth/*.md` and `scripts/runtime_*.py` path resolves to
  a real file, the supported HTTP routes for the closed floors are listed,
  the comparative-evidence operator script is listed, no line outside the
  unsupported-claims section uses banned vocabulary as a current claim,
  no positive-assertion sentence claims owlmlx is release-ready / parity /
  replacement / equivalent / production-grade, and the floor 3.6 caveat is
  recorded
- master-outline gained entry 134 for `public-surface.md`; master-outline
  date bumped to `2026-04-28`
- verification: `pytest -q tests/test_public_surface_contract.py` 12 passed;
  `python3 -m py_compile owlmlx/runtime/server.py` clean; `git diff --check`
  clean
- this lane did **not** flip `release-readiness-backlog.md`; coordinator
  closeout decides whether row `3.7` and (if 3.6A is also accepted) row
  `3.6` may move
- no release, parity, replacement, production-grade, superiority, wins,
  beats, equivalent, or matches claim was made

3.6B / 3.7B final closeout ledger sync (2026-04-28,
`owlmlx_release_floor_3_6B_3_7B_final_closeout_closed`):

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-6B-3-7B-final-closeout-ledger-sync.md`
  ran as the single ClaudeCode closeout reviewer; no second executor
  was assigned and no live external HTTP probe was rerun
- 3.6 closeout questions (§4 of the prompt) all answered `yes`:
  the 3.6A record exists with verdict `pass` in
  `phase45-customer-runtime-evidence-ledger.md` §9; the consumer
  boundary was `/Users/yeemio/AI/gitrep/owlops`; both
  `/v1/runtime/status` and `/healthz` were fetched over HTTP and both
  returned `200`; probe exit-status was `0`; stderr was empty; port
  `8065` had no remaining listener after cleanup; the lane did not
  promote a local-only sanity run; no banned current-claim was made
- 3.7 closeout questions (§5 of the prompt) all answered `yes`:
  `public-surface.md` exists, identifies itself as authoritative,
  freezes the technical-preview boundary, declares the label
  vocabulary, states the internal-default rule, keeps phase45
  cache/exactness machinery internal, references existing
  source-of-truth docs instead of duplicating them;
  `tests/test_public_surface_contract.py` validates the boundary,
  referenced docs, referenced scripts, route listing,
  banned-vocabulary discipline, and the floor 3.6 caveat; the
  `master-outline.md` index includes `public-surface.md`; no banned
  current-claim was made
- §6 verification matrix this round:
  `tests/test_customer_runtime_evidence.py` 53 passed;
  `tests/test_public_surface_contract.py` 12 passed; `py_compile` clean
  for `owlmlx/customer_runtime_evidence.py`,
  `scripts/runtime_customer_runtime_evidence.py`, and
  `owlmlx/runtime/server.py`; `git diff --check` clean
- coordinator action applied 2026-04-28: section 5 row for `3.6`
  flipped from `open` to
  `closed (via OwlOps-boundary external runtime-truth consumer evidence)`
  with references to the customer runtime evidence ledger, the
  `20260428T025051Z` evidence directory, the 3.6A handoff, and this
  3.6B / 3.7B handoff; section 5 row for `3.7` flipped from `open`
  to `closed (via runtime-owned public-surface freeze)` with
  references to `public-surface.md`,
  `tests/test_public_surface_contract.py`, the 3.7A handoff, and
  this 3.6B / 3.7B handoff; the §3.6 and §3.7 "Current state" prose
  in the backlog were refreshed to reflect closure; section 2 floor
  count moved from `5/7` to `7/7`
- this closure does **not** promote `owlmlx` to release-ready,
  parity, replacement, or production-grade. It does open the
  `technical preview` interim claim (governed by
  `public-surface.md` §2 / §10), but only with the supported HTTP
  routes / modules / scripts / contracts named in the freeze
- no runtime code was edited; no external repository was touched;
  no public-surface widening occurred; no new evidence was generated

The `3.2` A/B prompts exist:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2A-memory-pressure-eviction-decision-and-execution.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2B-memory-pressure-eviction-review.md`

A round result (2026-04-26,
`owlmlx_release_floor_3_2A_memory_pressure_eviction_candidate_closed_pending_review`):

- new contract `owlmlx.memory_pressure_eviction_policy` lives at
  `owlmlx/memory_pressure_eviction_policy.py`, decision transport at
  `GET /v1/runtime/memory-pressure-eviction-policy`, execution transport at
  `POST /v1/runtime/memory-pressure-eviction`, docs at
  `docs/source-of-truth/memory-pressure-eviction-policy.md`, tests at
  `tests/test_memory_pressure_eviction_policy.py`
- the contract returns exactly one of `evict / defer / reject / unknown`,
  consumes `memory_pressure_contract` (pressure classification),
  `model_residency_policy` (resident inventory, active model id), and
  `recovery_supervisor_contract` (hard recovery barriers); it never
  invents OS-level pressure events
- candidate ordering is deterministic: unpinned-first → ttl-expired
  unpinned → non-active-protected → larger memory → lexical model_id
- new runtime-owned execution path
  `RuntimeKernel.execute_memory_pressure_eviction(...)` refuses execution
  unless `decision == "evict"`, unloads the selected victim through
  existing `unload_model` semantics, records an eviction-history event
  with `source = "memory_pressure_policy"`, returns a structured result
  with decision snapshot, victim, unload result, residency after-state,
  and the recorded event; pinned models remain double-protected by the
  unload-side pin check
- when the loadability lineage registry is connected at `create_app(...)`,
  the POST endpoint also includes `loadability_lineage_after` for the
  evicted model
- repeated-pressure scenario test
  (`tests/test_memory_pressure_eviction_policy.py
  ::test_runtime_kernel_pressure_eviction_repeated_pressure_observable_residency_change`)
  proves observable residency change across rounds with two
  `memory_pressure_policy` events accumulating in eviction history
- `release-readiness-backlog.md` section 5 is **not** moved by A; the
  `3.2` row stays `open` until B review confirms closure

B self-audit result (2026-04-26,
`owlmlx_release_floor_3_2B_review_pass_closed_recommended`):

- B confirmed the A implementation against the 3.2 review checklist and
  re-ran the focused suites, with all reported checks passing
- however, B disclosed that it was authored by the same Opus instance as A
  after an explicit one-round override; the B handoff therefore recommends a
  non-Opus second review before the coordinator flips the ledger

3.2C closeout (2026-04-26,
`owlmlx_release_floor_3_2C_independent_closeout_closed`):

- 3.2C ran via an independent fresh `claude-opus-4-7` instance that did not
  author 3.2A or the 3.2B self-audit; the prompt's recommended `gpt-5.4`
  was not used and the handoff records this as a cross-instance rather
  than cross-family independence guarantee
- 3.2C verified all 14 closure questions, ran the full verification matrix
  (16 + 16 + 28 + 8 + 37 tests pass; py_compile clean; `git diff --check`
  clean), and confirmed the implementation closes both decision and
  execution requirements without weakening serial runtime invariants
- coordinator action applied 2026-04-26: section 5 row for `3.2` flipped
  from `open` to
  `closed (runtime-owned pressure eviction decision and execution)`
  with references to the eviction policy contract, the four supporting
  source-of-truth docs, the test file, and the 3.2A / 3.2B / 3.2C
  handoffs; section 2 floor count moved from `2/7` to `3/7`
- this closure does **not** imply replacement-grade scheduler/cache
  closure or release readiness; floors `3.4`, `3.5`, `3.6`, `3.7`
  remain open

Recoordination packet:

- `files/execution-prompts/owlmlx/owlmlx-release-readiness-recoordination-2026-04-26.md`

Next active floor:

- `3.4 Recovery Policy Closure`

The coordinator should issue exactly one next prompt at this time per the
single-active-executor rule. The preferred next prompt is `3.4A0` as a
failed-unload/reclaim barrier event sub-round, seeded by
`files/execution-prompts/owlmlx/owlmlx-failed-unload-reclaim-barrier-event.md`.

The 3.4 pre-flight notes are accepted only as preparation. The 3.4A0 prompt
above is the actual implementation authorization.

## 7. Stop / Escalation Conditions

Stop and escalate when:

- a floor requires product/business priority rather than runtime truth
- external evidence is the only remaining blocker
- a runtime change would weaken serial safety invariants
- the executor cannot reduce a floor after one focused diagnosis round

Do not stop merely because a prompt was archived.
Prompt archival is coordination, not delivery.
