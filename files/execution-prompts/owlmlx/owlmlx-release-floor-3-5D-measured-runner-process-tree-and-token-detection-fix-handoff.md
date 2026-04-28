# owlmlx Execution Handoff 3.5D: Measured Runner Process-Tree + Token-Detection Fix

> Date: 2026-04-27
> Lane: single ClaudeCode executor (release floor 3.5 sub-round 3.5D)
> Active release floor: `3.5 Comparative Evidence Against Reference Runtimes` — **open**
> Role: code-lane runner fix triggered by the 3.5C live-review needs-fix outcome

## 1. Outcome Label

`owlmlx_release_floor_3_5D_measured_runner_process_tree_and_token_detection_fix`

The two defects Codex named in the 3.5C live-review handoff are now fixed
in the runner and covered by tests. No live 58G `gemma-4-31B-it` run was
attempted in this round; per the user's lane discipline
(`runner 自己坏了 → 回 ClaudeCode 修 runner，不再继续盲跑`), the next
allocation goes back to Codex desktop with Computer Use to retry the
live measured run with the fixed runner. Floor `3.5` stays `open`.

## 2. Verdict

The two defects from
`owlmlx-release-floor-3-5C-codex-live-measured-run-review-handoff.md` are
addressed:

- `peak_resident_set_bytes` now samples the wrapper PID **plus** all
  descendant processes (`psutil.Process(...).children(recursive=True)`)
  **plus** any caller-declared `external_pids` (or PIDs read from
  `external_pid_file`); the per-tick aggregate is the **sum** across the
  live tree, the reported `peak` is the max-over-ticks of that sum.
- `first_token_latency_ms` is computed by a new `_FirstTokenDetector`
  that respects `first_token_strategy`:
  - `first_nonempty_chunk` (default, back-compat with 3.5B)
  - `after_marker:<substring>` (defers first-token until a stdout line
    contains the substring; intended for runtimes whose first stdout
    chunk is diagnostic preamble, e.g. `runtime_large_weight_first_smoke.py`)
  - `regex:<python pattern>` (matches each non-empty line; first match
    is the first-token mark)

The runner does not yet have a real same-host `verdict_grade = "measured"`
record on file from this round; that requires another supervised Codex
live run.

## 3. Changed Files

Modified runtime / scripts:

- `owlmlx/comparative_evidence_runner.py`:
  - `RuntimeRunnerConfig`: new fields `external_pids: tuple[int, ...]`
    and `external_pid_file: str | None`
  - new module-level `_resolve_external_pids(...)` helper that combines
    the static list with PIDs read from the optional pid file (one PID
    per line; `#` comment lines and blank lines ignored; missing files
    silently treated as empty so the operator can write the file
    after starting the server)
  - `_RssSampler` rewritten to take `root_pids: Sequence[int]`; on each
    tick walks every root + descendants and writes per-PID RSS plus the
    per-tick sum to the JSONL artifact
  - new `_FirstTokenDetector` class implementing all three strategies;
    invalid runtime states fall back to the safe default rather than
    crashing mid-run
  - `execute_attempt(...)` now resolves external PIDs at attempt start,
    constructs the sampler with `[wrapper_pid, *external_pids]`, and
    drives the detector per stdout line
  - `_runner_from_payload(...)` parses `external_pids`,
    `external_pid_file`, and validates `first_token_strategy` (with a
    new `_validate_first_token_strategy(...)` helper that compiles
    `regex:` patterns at config-load time)
  - `commands.json` artifact records `external_pids`, `external_pid_file`,
    and `first_token_strategy` per runtime so re-runs are reproducible
  - `summary.md` peak-RSS line now documents the
    `max-per-tick sum across wrapper PID + descendants + external PIDs`
    aggregation explicitly

Tests:

- `tests/test_runtime_comparative_evidence_measured_runner.py`:
  9 new tests added (28 → 37 total, +32% coverage). New tests:
  - `test_rss_sampler_observes_child_process_in_wrapper_tree`
  - `test_rss_sampler_includes_external_pid`
  - `test_external_pid_file_resolves_pids`
  - `test_after_marker_first_token_strategy_skips_diagnostic_lines`
  - `test_regex_first_token_strategy_matches_generation_pattern`
  - `test_first_nonempty_chunk_back_compat_still_observes_first_line`
  - `test_load_runner_config_rejects_unsupported_first_token_strategy`
  - `test_load_runner_config_rejects_invalid_regex_strategy`
  - `test_load_runner_config_accepts_external_pids_and_pid_file`

Docs:

- `docs/source-of-truth/release-readiness-execution-plan.md` §6 now
  records both the 3.5C live review outcome and the 3.5D code-lane
  fix outcome, and names a follow-up Codex live measured-run as the
  next allocation

This handoff:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5D-measured-runner-process-tree-and-token-detection-fix-handoff.md`

`docs/source-of-truth/release-readiness-backlog.md` was **not**
modified — no real same-host `verdict_grade = "measured"` record exists
yet, so floor `3.5` remains `open (contract surface)`.

## 4. Commands And Results

```text
$ pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
...........................                                              [100%]
27 passed in 0.14s

$ pytest -q tests/test_runtime_comparative_evidence_measured_runner.py
.....................................                                    [100%]
37 passed in 4.01s

$ pytest -q tests/test_runtime_server.py -k "comparative_evidence"
....                                                                     [100%]
4 passed, 37 deselected in 0.33s

$ python3 -m py_compile \
    owlmlx/comparative_evidence_schema.py \
    owlmlx/comparative_evidence_record.py \
    owlmlx/comparative_evidence_ledger.py \
    owlmlx/comparative_evidence_runner.py \
    scripts/runtime_comparative_evidence.py \
    owlmlx/runtime/server.py
COMPILE_OK

$ python3 scripts/runtime_comparative_evidence.py run-measured-short-prompt --help
... (subcommand flags listed)

$ git diff --check
DIFF_CHECK_CLEAN
```

Aggregate: 27 + 37 + 4 = 68 passes across the touched surfaces.

The optional live measured run was **not** attempted in this round.
3.5C already produced live evidence at
`files/evidence/owlmlx/comparative-evidence/20260427T133443Z/` and a
follow-up live attempt belongs to Codex with process/port supervision.

## 5. New Runner-Config JSON Surface

The runner-config JSON shape is extended (back-compatible):

```json
{
  "owlmlx": {
    "runtime_version": "0.0.0-runtime7",
    "argv": ["python3", "scripts/runtime_large_weight_first_smoke.py", "...", "{prompt}", "--max-tokens", "{max_tokens}", "--include-known-venvs"],
    "env": {},
    "cwd": null,
    "tokens_method": "max_tokens",
    "first_token_strategy": "after_marker:Generated",
    "timeout_s": 600.0,
    "external_pids": [],
    "external_pid_file": null
  },
  "reference": {
    "runtime_id": "omlx",
    "runtime_version": "0.3.5",
    "argv": ["python3", "-c", "import json,urllib.request; ..."],
    "env": {},
    "cwd": null,
    "tokens_method": "max_tokens",
    "first_token_strategy": "first_nonempty_chunk",
    "timeout_s": 60.0,
    "external_pids": [59803],
    "external_pid_file": null
  }
}
```

Notes for Codex when authoring the next live runner-config:

- declare the live `omlx serve` PID (e.g. `59803` from the 3.5C run)
  via `external_pids` so its server tree is measured. If the PID is
  not known until after `omlx serve` starts, write it to a file and
  declare `external_pid_file` instead — the file is read each
  attempt so the runner picks up later writes
- pick a `first_token_strategy` that matches the actual stdout shape:
  - for `runtime_large_weight_first_smoke.py`: a marker like
    `after_marker:Generated` or `regex:^[^\\{].*` (a line not starting
    with `{`) defers first-token past gate JSON
  - for the `omlx` HTTP client used in 3.5C, the only stdout line is
    the assistant content, so `first_nonempty_chunk` remains correct
- `first_token_strategy` invalid values are rejected at config-load
  time, not silently downgraded (regex validity included)

## 6. Live Measured Record Status

None from this round.

The `files/evidence/owlmlx/comparative-evidence/20260427T133443Z/`
ledger from 3.5C still contains the schema-valid measured record that
the 3.5C reviewer rejected as closeout-grade. New live runs after the
3.5D runner fix should append into a fresh dated evidence directory
(e.g. `<utc-stamp>/`) so the 3.5C record stays intact as the honest
trail of the prior misclassification.

## 7. Exact Blocker

`live_same_host_measured_record_missing_after_runner_process_tree_and_token_detection_fix`.

To unblock floor `3.5`:

- Codex desktop runs `python3 scripts/runtime_comparative_evidence.py
  run-measured-short-prompt` against a fresh evidence directory under
  `files/evidence/owlmlx/comparative-evidence/<utc-stamp>/`
- the runner-config JSON declares the live `omlx serve` PID via
  `external_pids` (or `external_pid_file`) and uses
  `after_marker:` / `regex:` for `owlmlx.first_token_strategy`
- after the run, sanity-check the appended record:
  - `peak_resident_set_bytes` for `omlx` should be on the order of GB
    (live `omlx serve` was ~47.9 GB in 3.5C), not the ~28 MB the
    pre-fix runner reported
  - `first_token_latency_ms` for `owlmlx` should reflect token output,
    not diagnostic JSON timing
- live-curl-verify both comparative-evidence HTTP routes against the
  new ledger
- only then move the backlog row

## 8. Confirmation Of Discipline

- **No release / parity / replacement / production-grade claim**:
  confirmed. The runner still emits `measured` only when both runtimes
  succeed in every repeat; the banned-vocabulary parametrized test
  remains green for every banned word.
- **No fake measured evidence**: confirmed. The fix tightens the
  honesty of `peak_resident_set_bytes` and `first_token_latency_ms`;
  it does not relax any verdict policy.
- **No silent skipping of failing runtimes**: confirmed. Failure paths
  in `execute_attempt` and the `compute_verdict` policy are unchanged
  (still emit precise `failure_cause` strings; still demote to
  `inconclusive` / `rejected`).
- **No edits to OwlOps / OwlCoda / desktop UI / `/Users/yeemio/AI/Agent`**:
  confirmed. `git status` shows only owlmlx-internal paths. The
  AST-level `test_runner_module_does_not_import_forbidden_paths`
  test stays green.
- **Floor `3.6` and `3.7` not started**: confirmed.
- **Unrelated dirty/staged work preserved**: confirmed.
  `git diff --check` clean. The 3.5C evidence directory is untouched.

## 9. Next Executor Recommendation

Codex desktop with Computer Use, single allocation, `3.5E` live
measured-run review:

- task: invoke
  `python3 scripts/runtime_comparative_evidence.py
  run-measured-short-prompt` with the new runner-config fields
  populated:
  - `reference.external_pids` (or `external_pid_file`) pointing at the
    live `omlx serve` PID
  - `owlmlx.first_token_strategy` = `after_marker:<substring>` or
    `regex:<pattern>` chosen against the actual
    `runtime_large_weight_first_smoke.py` stdout shape
- supervision: keep eyes on PIDs and ports; if owlmlx first-smoke
  stalls past the configured `timeout_s`, let the runner record
  `harness_runtime_invocation_error_timeout` and emit `inconclusive`
  rather than block the lane
- closure rule: only if the resulting record has
  `verdict_grade = "measured"`, the per-runtime
  `peak_resident_set_bytes` reflects the actual server / child
  worker tree (not just the wrapper), and the `first_token_latency_ms`
  reflects generated-token output, may the coordinator consider
  flipping `release-readiness-backlog.md` row `3.5`

If the next live run still has a defect that cannot be authored away
in the runner-config, return another `needs_fix` with the exact
runner shortcoming — do not bend the verdict.
