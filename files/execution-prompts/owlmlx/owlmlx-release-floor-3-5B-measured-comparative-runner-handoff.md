# owlmlx Execution Handoff 3.5B: Measured Comparative Runner

> Date: 2026-04-27
> Lane: single ClaudeCode executor (release floor 3.5 sub-round 3.5B)
> Active release floor: `3.5 Comparative Evidence Against Reference Runtimes` — **open**
> Role: implementation, tests, docs, and code-lane handoff

## 1. Outcome Label

`owlmlx_release_floor_3_5B_measured_runner_introduced_pending_live_review`

The runtime-owned measured comparative runner is implemented, tested,
and exposed through a new CLI subcommand. No real same-host
`verdict_grade = "measured"` record was emitted in this round; the
live 58G `gemma-4-31B-it` run is left to a downstream Codex desktop
review lane with process/port monitoring (3.5A0 already proved the
owlmlx first-smoke path on this host can hang past ~133s without
returning generated output, so a live attempt without supervision
risks blocking the code lane). Floor `3.5` stays `open`.

## 2. Verdict

The dominant 3.5 blocker is no longer `harness_runner_missing` and is
now exactly `live_same_host_measured_record_missing`. The runner is
ready; only the supervised live invocation remains.

## 3. Changed Files

New runtime modules / scripts:

- `owlmlx/comparative_evidence_runner.py` — measured-runner primitives:
  `RuntimeRunnerConfig`, `WorkloadInputs`, `AttemptResult`,
  `RuntimeAggregate`, `execute_attempt(...)` (subprocess with first-
  token detection + `psutil`-based child RSS sampler, deterministic
  failure causes for spawn / non-zero exit / timeout / silent-stdout),
  `aggregate_runtime(...)` (mean of successes for latency / throughput /
  wall-clock; max for peak RSS; sum for completed / failure counts),
  `compute_verdict(...)` (`measured` / `inconclusive` / `rejected` per
  the harness contract), `aggregate_to_record_runtime(...)`,
  `attempt_to_dict(...)`, `write_run_artifacts(...)`,
  `load_runner_config_file(...)`. No imports from `owlops` /
  `owlcoda` / `/Users/yeemio/AI/Agent`; verified by AST test
- `scripts/runtime_comparative_evidence.py` — new
  `run-measured-short-prompt` subcommand wired through
  `_run_measured_short_prompt(...)` orchestrator; original
  `append-rejected-record` / `latest` / `history` paths preserved

Tests:

- `tests/test_runtime_comparative_evidence_measured_runner.py` — 28
  new tests using deterministic fake `python3 -c "..."` commands

Docs:

- `docs/source-of-truth/release-readiness-execution-plan.md` — §6
  records the 3.5B runner introduction outcome; the recommended
  next-allocation block now points at a Codex desktop live
  measured-run review with explicit process/port supervision

This handoff:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5B-measured-comparative-runner-handoff.md`

`docs/source-of-truth/release-readiness-backlog.md` was **not**
modified per §9 / §12 of the 3.5B prompt — no real same-host
`verdict_grade = "measured"` record exists yet.

## 4. Commands And Results

```text
$ pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
...........................                                              [100%]
27 passed in 0.10s

$ pytest -q tests/test_runtime_comparative_evidence_measured_runner.py
............................                                             [100%]
28 passed in 2.30s

$ pytest -q tests/test_runtime_server.py -k "comparative_evidence"
....                                                                     [100%]
4 passed, 37 deselected in 0.23s

$ python3 -m py_compile \
    owlmlx/comparative_evidence_schema.py \
    owlmlx/comparative_evidence_record.py \
    owlmlx/comparative_evidence_ledger.py \
    owlmlx/comparative_evidence_runner.py \
    scripts/runtime_comparative_evidence.py \
    owlmlx/runtime/server.py
COMPILE_OK

$ python3 scripts/runtime_comparative_evidence.py --help
usage: runtime_comparative_evidence.py [-h] [--ledger-path LEDGER_PATH]
                                       {append-rejected-record,run-measured-short-prompt,latest,history} ...
...
    run-measured-short-prompt
                        Run two repeat short-prompt attempts each against
                        owlmlx and one reference runtime, collect raw
                        measurements/artifacts, and append one validated
                        comparative_evidence_record (measured / inconclusive /
                        rejected)

$ git diff --check
DIFF_CHECK_CLEAN
```

Aggregate: 27 + 28 + 4 = 59 passes across the touched surfaces.

The optional live measured run was **not** attempted in this round
per §8 of the 3.5B prompt: the 3.5A0 evidence already showed an
owlmlx first-smoke against `gemma-4-31B-it` running past ~133s
without returning generated output. Running it unattended from the
code lane would block the test result; the supervised live attempt
belongs to Codex with Computer Use.

## 5. CLI Shape

```text
runtime_comparative_evidence.py [--ledger-path LEDGER_PATH]
                                run-measured-short-prompt
                                --evidence-dir EVIDENCE_DIR
                                --runner-config RUNNER_CONFIG
                                --host-class HOST_CLASS
                                [--workload-class WORKLOAD_CLASS]
                                --model-id MODEL_ID
                                --model-path MODEL_PATH
                                [--model-quantization MODEL_QUANTIZATION]
                                --prompt PROMPT
                                --prompt-set-hash PROMPT_SET_HASH
                                [--decode-max-tokens DECODE_MAX_TOKENS]
                                [--decode-temperature DECODE_TEMPERATURE]
                                [--serving-budget-bytes SERVING_BUDGET_BYTES]
                                [--repeats REPEATS]
                                [--evidence-pointer EVIDENCE_POINTER]
```

The runner-config JSON shape (passed via `--runner-config`):

```json
{
  "owlmlx": {
    "runtime_version": "0.0.0-runtime7",
    "argv": ["...", "...", "{prompt}", "--max-tokens", "{max_tokens}"],
    "env": {},
    "cwd": null,
    "tokens_method": "max_tokens",
    "first_token_strategy": "first_nonempty_chunk",
    "timeout_s": 60.0
  },
  "reference": {
    "runtime_id": "omlx",
    "runtime_version": "0.3.5",
    "argv": ["...", "..."],
    "env": {},
    "cwd": null,
    "tokens_method": "max_tokens",
    "timeout_s": 60.0
  }
}
```

Supported placeholders inside any `argv` token: `{prompt}`,
`{max_tokens}`, `{temperature}`, `{model_id}`, `{model_path}`.
`runtime_id` for the reference entry must be one of the frozen
`RUNTIME_IDS`: `omlx` or `vmlx`.

Supported `tokens_method` values:

- `max_tokens` — assume completed attempts produced exactly
  `decode_max_tokens` tokens (conservative; suitable for the
  short-prompt workload)
- `stdout_word_count` — split stdout on whitespace
- `stdout_line_count` — count non-empty stdout lines
- `json_field:<name>` — parse the last JSON object on stdout and read
  an integer/float field

## 6. Artifact Directory Shape

For one `run-measured-short-prompt` invocation with `--evidence-dir
<dir>` and `--repeats 2`:

```text
<dir>/
  manifest.json            # workload, repeats, verdict, per-runtime aggregates
  commands.json            # rerun command lines per runtime, with placeholders resolved
  summary.md               # operator-facing summary
  owlmlx_attempt1.stdout.txt
  owlmlx_attempt1.stderr.txt
  owlmlx_attempt1.rss.jsonl   # one JSON line per ~50ms RSS sample
  owlmlx_attempt2.stdout.txt
  owlmlx_attempt2.stderr.txt
  owlmlx_attempt2.rss.jsonl
  <reference_id>_attempt1.stdout.txt
  <reference_id>_attempt1.stderr.txt
  <reference_id>_attempt1.rss.jsonl
  <reference_id>_attempt2.stdout.txt
  <reference_id>_attempt2.stderr.txt
  <reference_id>_attempt2.rss.jsonl
```

`evidence_pointer` in the appended record defaults to
`<dir>/manifest.json` (overridable via `--evidence-pointer`). The
ledger path is whatever `--ledger-path` points at; it is opened in
append mode by `ComparativeEvidenceLedger`.

## 7. Verdict Policy

Per the harness contract §4 and §5:

- `measured` — every configured runtime has every repeat succeed
  (`completed_request_count >= repeats` and `failure_count == 0`).
  `verdict_text` is shaped
  `"measured: <owlmlx_id> tokens_per_second X.XXXX vs <reference_id>
  tokens_per_second Y.YYYY on host_class=<...>, workload_class=<...>"`
- `inconclusive` — at least one runtime has at least one success and
  at least one failure (or fewer repeats than expected). `verdict_text`
  is `"inconclusive: <comma_separated_failure_causes> on
  host_class=<...>, workload_class=<...>"`
- `rejected` — at least one runtime has zero successful attempts.
  `verdict_text` is `"rejected: <runtime_id>_runtime_invocation_failed:<cause>
  on host_class=<...>, workload_class=<...>"`. Honest `5.4` harness
  failure truth, not silent skipping

The `BANNED_VERDICT_VOCABULARY` enforcement remains in
`owlmlx.comparative_evidence_schema.validate_comparative_evidence_record`;
a parametrized test asserts every banned word still triggers
`SchemaValidationError`.

## 8. Unit-Test Strategy

Unit tests use deterministic fake `python3 -c "..."` argv:

- success command emits `"OK\n"` after `time.sleep(0.02)` so first-token
  latency is measurable (>0)
- failure command writes to stderr and exits non-zero
- silent command exits 0 without emitting stdout (forces
  `first_token_latency_unobservable`)
- spawn-failure command points at `/no/such/binary/...`
- a flaky reference command writes a marker file on the first run
  and exits 3 on subsequent runs (forces a per-attempt mix)

Tests do not require the 58G model on disk and run in ~2.3s.

## 9. Live Same-Host Measured Run

Not attempted in this round.

Reasons:

- 3.5A0 evidence shows `scripts/runtime_large_weight_first_smoke.py`
  on `gemma-4-31B-it` running past ~133s without returning generated
  output before operator stop
- the prompt §8 explicitly states the live run is optional in this
  lane and should be deferred to the Codex review lane when unsafe
- attempting the run unattended would block the code-lane test
  result and risk a hung process the lane cannot kill cleanly

`release-readiness-backlog.md` row `3.5` therefore remains
`open (contract surface)`.

## 10. Real `verdict_grade = "measured"` Record Status

None.

The repository has no real same-host measured record yet. The
`files/evidence/owlmlx/comparative-evidence/20260427T094224Z/`
preflight ledger from 3.5A0 still contains exactly one
`verdict_grade = "inconclusive"` record (`harness_runner_missing`).

## 11. Exact Blocker

`live_same_host_measured_record_missing`.

To unblock floor `3.5`:

- run a supervised invocation of
  `python3 scripts/runtime_comparative_evidence.py
  run-measured-short-prompt` on this host
- point `owlmlx.argv` at a real owlmlx generation entry that produces
  stdout-observable first-token output for a 2-token decode (e.g.
  `scripts/runtime_large_weight_first_smoke.py` with the probe venv
  and `--include-known-venvs`, supervised so the lane can kill the
  child if it hangs)
- point `reference.argv` at the `omlx` probe venv `omlx` CLI invoking
  `gemma-4-31B-it` for the same prompt and 2-token decode
- write artifacts under
  `files/evidence/owlmlx/comparative-evidence/<utc-stamp>/`
- append the record to that round's ledger
- live-curl-verify the HTTP surface against the new ledger
- only then move the backlog row

## 12. Confirmation Of Discipline

- **No release / parity / replacement / production-grade claim**:
  confirmed. The runner emits `measured` only when both runtimes
  succeed in every repeat; even then `verdict_text` is restricted to
  the throughput-comparison sentence and rejects the banned
  vocabulary in `owlmlx.comparative_evidence_schema`.
- **No fake measured evidence**: confirmed. The unit tests assert
  that flaky / silent / failing runtimes produce `inconclusive` or
  `rejected`, never `measured`. No code path constructs a record with
  `verdict_grade = "measured"` and a runtime that has
  `failure_count > 0`.
- **No silent skipping of failing runtimes**: confirmed. Every
  attempt failure is recorded with a precise `failure_cause`; the
  per-runtime aggregate sums failures and the verdict policy
  downgrades accordingly.
- **No workload invariant changes between runtimes**: confirmed. The
  same `WorkloadInputs` (prompt / max-tokens / temperature / model-id
  / model-path / prompt-set-hash / serving-budget-bytes) is passed
  into both runtime invocations, with placeholder substitution
  happening at argv render time only.
- **No edits to OwlOps / OwlCoda / desktop UI / `/Users/yeemio/AI/Agent`**:
  confirmed. `git status` shows only owlmlx-internal paths. The
  AST-level test
  `test_runner_module_does_not_import_forbidden_paths` enforces
  that the new module imports nothing from those packages.
- **Floor `3.6` and `3.7` not started**: confirmed. No edits to
  customer-evidence ledger or public-surface docs.
- **Unrelated dirty/staged work preserved**: confirmed.
  `git diff --check` is clean. Pre-existing dirty/untracked paths
  from session start were not modified.

## 13. Next Executor Recommendation

Codex desktop with Computer Use, single allocation:

- role: live measured-run review
- task: invoke
  `python3 scripts/runtime_comparative_evidence.py
  run-measured-short-prompt` against a fresh evidence directory under
  `files/evidence/owlmlx/comparative-evidence/<utc-stamp>/` with a
  runner-config JSON pointing at a real owlmlx generation argv and a
  real `omlx` argv on this host
- supervision: keep eyes on the child PIDs; if owlmlx first-smoke
  stalls past a configured `timeout_s`, let the runner record
  `harness_runtime_invocation_error_timeout` and emit `inconclusive`
  or `rejected` rather than block the lane
- closure rule: only if the resulting record has
  `verdict_grade = "measured"` and is served by both
  `GET /v1/runtime/comparative-evidence` and
  `GET /v1/runtime/comparative-evidence/history` may the coordinator
  consider flipping `release-readiness-backlog.md` row `3.5`

If Codex returns `inconclusive` or `rejected`, do **not** start
floor `3.6` or `3.7`. Instead either tune the `owlmlx` argv toward a
shorter, observable smoke path or freeze the live blocker for a
follow-up code lane.
