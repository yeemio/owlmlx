# owlmlx Execution Prompt 3.5E: Codex Live Measured Run Rerun

> Date: 2026-04-27
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.5 Comparative Evidence Against Reference Runtimes`
> Assigned executor: Codex desktop
> Required capability: Computer Use is allowed for terminal / process / port /
> screen monitoring
> Role: supervised live same-host measured-run rerun after 3.5D runner fix
> Scope: live evidence only; no broad runner redesign

## 1. Mission

Rerun the live `owlmlx` + `omlx` comparative workload using the fixed 3.5D
runner and decide whether the resulting record is now closeout-grade evidence.

The required question is:

**After process-tree RSS sampling and first-token detection were fixed, can this
host produce a real same-host `verdict_grade = "measured"` record whose metrics
are honest enough to support release floor `3.5` closeout?**

If yes, preserve the raw artifacts, serve the ledger over HTTP, and recommend
closeout. If no, keep floor `3.5` open and freeze the exact live blocker.

## 2. Coordination Truth

Current release state:

- `3.1`, `3.2`, `3.3`, and `3.4` are closed.
- `3.5` remains open.
- `3.5A0` proved `omlx` and `vmlx` are available on this host and the local
  `gemma-4-31B-it` weights exist.
- `3.5B` implemented `run-measured-short-prompt`.
- `3.5C` produced a schema-valid HTTP-served `measured` record, but the record
  was rejected as closeout evidence because:
  - RSS sampled only wrapper processes and missed the live `omlx serve` /
    MLX child process tree
  - first-token latency started at diagnostic JSON rather than generated-token
    output
- `3.5D` fixed both runner defects:
  - `RuntimeRunnerConfig.external_pids`
  - `RuntimeRunnerConfig.external_pid_file`
  - process-tree RSS with per-tick child recursion and per-tick RSS sums
  - `first_token_strategy` values:
    `first_nonempty_chunk`, `after_marker:<substring>`, and
    `regex:<python pattern>`

This 3.5E lane must use those new fields. A repeat of the 3.5C config without
external PID sampling and token-aware detection is invalid.

## 3. Required Read Order

Read before running commands:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/comparative-evidence-harness-contract.md`
5. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5C-codex-live-measured-run-review-handoff.md`
6. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5D-measured-runner-process-tree-and-token-detection-fix-handoff.md`
7. `owlmlx/comparative_evidence_runner.py`
8. `scripts/runtime_comparative_evidence.py`
9. `tests/test_runtime_comparative_evidence_measured_runner.py`
10. Prior rejected live evidence under
    `files/evidence/owlmlx/comparative-evidence/20260427T133443Z/`

## 4. Stable Checks

Run before live execution:

```bash
pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
pytest -q tests/test_runtime_comparative_evidence_measured_runner.py
pytest -q tests/test_runtime_server.py -k "comparative_evidence"
python3 -m py_compile \
  owlmlx/comparative_evidence_schema.py \
  owlmlx/comparative_evidence_record.py \
  owlmlx/comparative_evidence_ledger.py \
  owlmlx/comparative_evidence_runner.py \
  scripts/runtime_comparative_evidence.py \
  owlmlx/runtime/server.py
python3 scripts/runtime_comparative_evidence.py run-measured-short-prompt --help
```

If these fail, stop with
`owlmlx_release_floor_3_5E_measured_runner_needs_fix` and do not run the 58G
live workload.

## 5. Fresh Evidence Directory

Use a fresh UTC-stamped directory:

```text
files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/
```

Required files:

- `runner-config.json`
- `omlx-server.pid` or equivalent external PID file
- `live-ledger.jsonl`
- `live-run-notes.md`
- runner-generated `run/manifest.json`
- runner-generated `run/commands.json`
- runner-generated `run/summary.md`
- runner-generated stdout / stderr / RSS JSONL artifacts
- HTTP curl output captures for latest and history

Do not modify the 3.5C evidence directory. It remains the honest rejected trail.

## 6. Workload

Use the same workload and invariants as 3.5A0 / 3.5C:

- `workload_class = "single_prompt_short"`
- prompt: `Reply with exactly OK.`
- `prompt_set_hash`:
  `sha256:b4d50a67a784a449e0c763c401bb9f95fb37804dff5765d8b4f95fd202eb7d77`
- `model_id = "gemma-4-31B-it"`
- `model_path = "/Users/yeemio/AI/Agent/models/gemma-4-31B-it"`
- `model_quantization = "full_precision_unquantized"`
- `decode_max_tokens = 2`
- `decode_temperature = 0.0`
- `serving_budget_bytes = 85899345920`
- `host_class = "Mac17,6-arm64-macOS-26.4.1-128GB"`

Do not change any invariant between `owlmlx` and `omlx`.

## 7. Start And Track `omlx`

Start `omlx serve` using the proven probe venv:

```bash
/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe/.venv/bin/omlx serve \
  --model-dir /Users/yeemio/AI/Agent/models \
  --host 127.0.0.1 \
  --port <OMLX_PORT> \
  --no-cache \
  --max-process-memory disabled \
  --max-model-memory disabled \
  --log-level warning
```

Record the live `omlx serve` PID in the fresh evidence directory:

```bash
printf '%s\n' "$OMLX_PID" > files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/omlx-server.pid
```

Then set the reference runner config to use:

```json
"external_pid_file": "files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/omlx-server.pid"
```

Do not rely on the wrapper HTTP-client PID for `omlx` RSS. The sanity check is
that `omlx.peak_resident_set_bytes` should be on the order of GB when the model
is resident. The 3.5C rejected run saw the live server around `47.9 GB`; a
record showing tens of MB is not closeout-grade.

## 8. Runner Config Requirements

The `runner-config.json` must include:

For `owlmlx`:

- `runtime_version`
- `argv` pointing at a real owlmlx generation command for the same model and
  prompt, starting from:

```text
PYTHONPATH=. python3 scripts/runtime_large_weight_first_smoke.py
  --specimen-path {model_path}
  --memory-gb 80
  --prompt {prompt}
  --max-tokens {max_tokens}
  --include-known-venvs
```

- `cwd` set to `/Users/yeemio/AI/gitrep/owlmlx` or equivalent
- `env` includes `PYTHONPATH=.` if needed
- `tokens_method = "max_tokens"` unless a better stdout token-count signal is
  proven
- `first_token_strategy` must be selected from actual stdout shape:
  - prefer `after_marker:<substring>` if generated output has a stable marker
  - otherwise use `regex:<pattern>` that matches generated-token output and
    skips leading JSON diagnostic lines
  - do not use plain `first_nonempty_chunk` for owlmlx if stdout begins with
    gate/status JSON
- `timeout_s` must be finite. If owlmlx stalls, let the runner record timeout
  rather than blocking the lane

For `reference`:

- `runtime_id = "omlx"`
- `runtime_version = "0.3.5"` unless live command reports another version
- `argv` should POST to the live `omlx` OpenAI-compatible endpoint and print
  only assistant content to stdout
- `tokens_method = "max_tokens"` for the 2-token workload unless a better
  signal is proven
- `first_token_strategy = "first_nonempty_chunk"` is acceptable if the helper
  prints only assistant content
- `external_pid_file` must point to the live `omlx serve` PID file

`commands.json` must show `external_pid_file` and `first_token_strategy` for
both runtimes after the run.

## 9. Runner Invocation

Run:

```bash
python3 scripts/runtime_comparative_evidence.py \
  --ledger-path files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/live-ledger.jsonl \
  run-measured-short-prompt \
  --evidence-dir files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/run \
  --runner-config files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/runner-config.json \
  --host-class Mac17,6-arm64-macOS-26.4.1-128GB \
  --workload-class single_prompt_short \
  --model-id gemma-4-31B-it \
  --model-path /Users/yeemio/AI/Agent/models/gemma-4-31B-it \
  --model-quantization full_precision_unquantized \
  --prompt "Reply with exactly OK." \
  --prompt-set-hash sha256:b4d50a67a784a449e0c763c401bb9f95fb37804dff5765d8b4f95fd202eb7d77 \
  --decode-max-tokens 2 \
  --decode-temperature 0.0 \
  --serving-budget-bytes 85899345920 \
  --repeats 2
```

Use Computer Use or terminal monitoring to watch long-running child processes.
If timeout occurs, preserve artifacts and continue to HTTP verification of the
resulting `inconclusive` / `rejected` record.

## 10. Sanity Checks On The Record

If the runner emits `verdict_grade = "measured"`, perform these sanity checks
before recommending closeout:

1. `omlx.peak_resident_set_bytes` is GB-scale and plausibly includes the live
   server process, not just a small HTTP client wrapper.
2. `owlmlx.peak_resident_set_bytes` includes the wrapper plus descendants.
3. `owlmlx.first_token_latency_ms` is not the timestamp of a leading diagnostic
   JSON/status line.
4. Each runtime has `completed_request_count = 2` and `failure_count = 0`.
5. `run/*.rss.jsonl` contains per-PID or tree sampling evidence.
6. `run/commands.json` records `external_pid_file` or `external_pids` for
   `omlx`.
7. `run/summary.md` states the verdict and measurement caveats.

If any sanity check fails, use
`owlmlx_release_floor_3_5E_live_run_needs_fix` or
`owlmlx_release_floor_3_5E_live_run_inconclusive`, not closeout.

## 11. HTTP Verification

Serve the fresh live ledger:

```bash
PYTHONPATH=. \
OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH=files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/live-ledger.jsonl \
python3 -m uvicorn owlmlx.runtime.server:create_fake_app \
  --factory --host 127.0.0.1 --port <OWLMLX_HTTP_PORT> --log-level warning
```

Curl both:

```bash
curl -sS http://127.0.0.1:<OWLMLX_HTTP_PORT>/v1/runtime/comparative-evidence
curl -sS http://127.0.0.1:<OWLMLX_HTTP_PORT>/v1/runtime/comparative-evidence/history
```

Record:

- HTTP status
- `surface`
- `version`
- `verdict_grade`
- `runtimes[*].runtime_id`
- metric fields for both runtimes
- whether latest and history agree

## 12. Cleanup

Prove all live ports are released:

```bash
lsof -n -iTCP:<OMLX_PORT> -sTCP:LISTEN || true
lsof -n -iTCP:<OWLMLX_HTTP_PORT> -sTCP:LISTEN || true
```

Also confirm no lane-owned `runtime_large_weight_first_smoke.py`,
`mlx_lm_runner`, `omlx serve`, or `uvicorn` process remains. If a process is
left over and belongs to this lane, stop it and record the PID.

## 13. Allowed Edits

Allowed:

- fresh evidence directory under
  `files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/`
- one handoff:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5E-codex-live-measured-run-rerun-handoff.md`
- narrow `docs/source-of-truth/release-readiness-execution-plan.md` update
  recording the 3.5E result
- `docs/source-of-truth/release-readiness-backlog.md` only if all floor `3.5`
  closure criteria are met and closeout is honestly justified

Do not edit runner code unless a trivial live wiring issue blocks the attempt
and can be fixed with tests in this same lane. If the issue is non-trivial,
stop with `needs_fix` and write the exact runner prompt for ClaudeCode.

Do not edit OwlOps, OwlCoda, `/Users/yeemio/AI/Agent`, floor `3.6`, or floor
`3.7`.

## 14. Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_5E_live_measured_record_closed_recommended`
- `owlmlx_release_floor_3_5E_live_measured_record_emitted_pending_closeout`
- `owlmlx_release_floor_3_5E_live_run_inconclusive`
- `owlmlx_release_floor_3_5E_live_run_rejected`
- `owlmlx_release_floor_3_5E_live_run_needs_fix`
- `owlmlx_release_floor_3_5E_measured_runner_needs_fix`

## 15. Required Handoff

Create:

`files/execution-prompts/owlmlx/owlmlx-release-floor-3-5E-codex-live-measured-run-rerun-handoff.md`

It must include:

- outcome label
- host class, ports, PIDs, Python path
- evidence directory
- full `runner-config.json`
- exact commands and results
- process / port cleanup evidence
- ledger record summary
- HTTP curl summary
- sanity-check answers from section 10
- whether a real closeout-grade `verdict_grade = "measured"` exists
- whether floor `3.5` closeout is recommended
- if not closeout, exact blocker and next executor recommendation
- confirmation that no release/parity/replacement/production-grade claim was
  made

## 16. Hard Rules

- Do not fake measured evidence.
- Do not reuse the rejected 3.5C evidence directory as new evidence.
- Do not accept wrapper-only RSS for a resident server workload.
- Do not accept first-token timing from diagnostic JSON.
- Do not change workload invariants between runtimes.
- Do not leave model/server/uvicorn processes running.
- Do not start floor `3.6` or `3.7`.
- Preserve unrelated dirty/staged work.
