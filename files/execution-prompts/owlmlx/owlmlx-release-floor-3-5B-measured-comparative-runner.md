# owlmlx Execution Prompt 3.5B: Measured Comparative Runner

> Date: 2026-04-27
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.5 Comparative Evidence Against Reference Runtimes`
> Assigned executor: ClaudeCode
> Role: implementation, tests, docs, and measured-run handoff
> Scope: smallest honest same-host measured comparative evidence runner

## 1. Mission

Implement the narrow runtime-owned measured runner that `3.5A0` proved is
missing.

The required question is:

**Can `scripts/runtime_comparative_evidence.py` run the same short workload
twice against `owlmlx` and at least one reference runtime (`omlx` first), collect
the required measurements/artifacts, append a valid
`verdict_grade = "measured"` record, and serve it through the existing HTTP
surface?**

This is not a broad benchmark suite. It is the minimum honest runner for one
shared local model and one short prompt.

## 2. Coordination Truth

Current release state:

- `3.1`, `3.2`, `3.3`, and `3.4` are closed in the release ledger.
- `3.5` remains open.
- `3.5A0` outcome:
  `owlmlx_release_floor_3_5A0_harness_runner_missing`.
- `3.5A0` proved this host can see and partly run the reference-runtime side:
  - `omlx` served `gemma-4-31B-it` and returned assistant content `OK`
  - `vmlx doctor` passed inference on `gemma-4-31B-it`
  - local model weights exist at
    `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
  - the comparative evidence HTTP surface can serve an isolated ledger
    through a real `uvicorn` process
- The blocker is no longer generic `reference_runtime_unavailable`; it is
  `harness_runner_missing`.

The current `scripts/runtime_comparative_evidence.py` supports only:

- `append-rejected-record`
- `latest`
- `history`

It does not run measured workloads, does not perform two repeat runs per
runtime, and does not collect first-token latency / throughput / peak RSS /
wall-clock / raw artifacts.

## 3. Required Read Order

Read before editing:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/comparative-evidence-harness-contract.md`
5. `docs/source-of-truth/comparative-evidence-schema-stub.md`
6. `docs/source-of-truth/runtime-status-schema.md`
7. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5A0-codex-live-comparative-evidence-preflight-handoff.md`
8. `files/evidence/owlmlx/comparative-evidence/20260427T094224Z/preflight-summary.md`
9. `scripts/runtime_comparative_evidence.py`
10. `owlmlx/comparative_evidence_schema.py`
11. `owlmlx/comparative_evidence_record.py`
12. `owlmlx/comparative_evidence_ledger.py`
13. `owlmlx/runtime/server.py`
14. `tests/test_comparative_evidence_schema.py`
15. `tests/test_comparative_evidence_record.py`
16. `tests/test_runtime_server.py`

## 4. Implementation Target

Add one narrow measured-run subcommand to:

`scripts/runtime_comparative_evidence.py`

Preferred subcommand name:

- `run-measured-short-prompt`

The subcommand should:

- accept a ledger path
- accept an evidence output directory
- accept `host_class`
- accept model id / model path / quantization / serving budget
- accept prompt text, prompt hash, max tokens, and temperature
- accept one `omlx` runner command or endpoint configuration
- accept one `owlmlx` runner command or endpoint configuration
- run two repeat attempts for each runtime
- collect raw stdout/stderr and re-run commands
- collect or compute:
  - `throughput_tokens_per_second`
  - `first_token_latency_ms`
  - `peak_resident_set_bytes`
  - `wall_clock_ms`
  - `completed_request_count`
  - `failure_count`
  - `failure_causes` when failures occur
- append a validated `comparative_evidence_record`
- print the appended record as JSON

If a fully live `owlmlx` generation runner cannot complete reliably yet, do
not fake it. Return `inconclusive` or `rejected` with a precise reason and keep
floor `3.5` open. However, still implement the runner structure and tests so
the remaining blocker is exact.

## 5. Measurement Semantics

For the first narrow runner:

- `first_token_latency_ms` may be measured as time until the first non-empty
  assistant/token output observed from the command or HTTP response stream.
- If the runner is non-streaming and cannot expose first-token time, do not
  invent it. Either:
  - add a documented `first_token_latency_ms = wall_clock_ms` fallback only if
    the doc and record clearly state `non_streaming_first_token_proxy`, or
  - mark the measured attempt inconclusive due to
    `first_token_latency_unobservable`.
- `throughput_tokens_per_second` may use generated token count divided by
  generation wall-clock, but the token-count method must be documented in raw
  artifacts.
- `peak_resident_set_bytes` may be collected by polling `ps` / `resource` /
  subprocess RSS samples. If using child processes, sample the child PID, not
  only the wrapper.
- `wall_clock_ms` must be monotonic-clock based.
- `completed_request_count` must count successful workload completions, not
  process starts.

The first implementation may use conservative, imperfect measurement if it is
explicit and repeatable. It may not silently omit required fields.

## 6. Artifact Requirements

For every run, write artifacts under the chosen evidence directory:

- `manifest.json`
- `commands.json`
- per-runtime repeat stdout / stderr files
- per-runtime repeat resource samples, preferably JSONL
- appended ledger JSONL path
- `summary.md`

`evidence_pointer` in the record must point to the artifact directory or
manifest.

## 7. Required Tests

Add or update tests for:

- CLI exposes `run-measured-short-prompt`
- measured runner rejects missing runtime commands / endpoints clearly
- measured runner writes raw artifact files
- measured runner appends a validated `verdict_grade = "measured"` record
  when given deterministic fake runtime commands that return valid output
- measured runner emits `inconclusive` or `rejected` when one runtime fails,
  without writing fake measured data
- measurement fields are present and numeric in the measured record
- banned verdict vocabulary remains rejected
- HTTP surface serves a measured record from an isolated ledger
- no OwlOps / OwlCoda / `/Users/yeemio/AI/Agent` imports enter the modules

Suggested new test file:

- `tests/test_runtime_comparative_evidence_measured_runner.py`

Use fake local commands for unit tests; do not require the 58G model in normal
pytest.

## 8. Required Verification

Run at minimum:

```bash
pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
pytest -q tests/test_runtime_comparative_evidence_measured_runner.py
pytest -q tests/test_runtime_server.py -k "comparative_evidence"
python3 -m py_compile \
  owlmlx/comparative_evidence_schema.py \
  owlmlx/comparative_evidence_record.py \
  owlmlx/comparative_evidence_ledger.py \
  scripts/runtime_comparative_evidence.py \
  owlmlx/runtime/server.py
python3 scripts/runtime_comparative_evidence.py --help
git diff --check
```

If the implementation can safely run the live model workload on this host,
also run a live measured attempt using:

- model path:
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- workload:
  `single_prompt_short`
- prompt:
  `Reply with exactly OK.`
- max tokens:
  `2`
- temperature:
  `0.0`
- reference runtime:
  `omlx` first, using the probe venv path recorded in the 3.5A0 handoff

If the live run is too slow or unsafe, do not block the code-lane test result;
record the live blocker and leave final floor closure for the Codex live
review lane.

## 9. Documentation Updates

Update narrowly:

- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/comparative-evidence-harness-contract.md` if the
  runner semantics need to be frozen
- `docs/source-of-truth/runtime-status-schema.md` only if the HTTP shape
  changes

Do not flip `release-readiness-backlog.md` row `3.5` unless a real same-host
measured record exists and is served by HTTP. A fake-command unit test measured
record is not a release-floor closure record.

## 10. Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_5B_measured_runner_introduced_pending_live_review`
- `owlmlx_release_floor_3_5B_measured_record_emitted_pending_closeout`
- `owlmlx_release_floor_3_5B_measured_runner_needs_fix`
- `owlmlx_release_floor_3_5B_measured_runner_still_blocked`

## 11. Required Handoff

Create:

`files/execution-prompts/owlmlx/owlmlx-release-floor-3-5B-measured-comparative-runner-handoff.md`

It must include:

- outcome label
- changed files
- exact commands and results
- CLI shape
- artifact directory shape
- whether unit tests used fake runtime commands
- whether a live same-host measured run was attempted
- whether a real `verdict_grade = "measured"` record exists
- ledger path and HTTP curl output if a real measured record exists
- exact blocker if no real measured record exists
- confirmation that no release/parity/replacement claim was made
- next executor recommendation:
  - Codex live measured-run review if runner is ready
  - needs-fix implementation prompt if runner fails tests

## 12. Hard Rules

- Do not fake measured evidence.
- Do not use fake-runtime unit-test records to close floor `3.5`.
- Do not silently skip a failing runtime.
- Do not change workload invariants between runtimes.
- Do not edit OwlOps, OwlCoda, or `/Users/yeemio/AI/Agent`.
- Do not start floor `3.6` or `3.7`.
- Preserve unrelated dirty/staged work.
