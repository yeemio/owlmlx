# owlmlx Execution Prompt 3.5C: Codex Live Measured Run Review

> Date: 2026-04-27
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.5 Comparative Evidence Against Reference Runtimes`
> Assigned executor: Codex desktop
> Required capability: Computer Use is allowed for terminal / process / port /
> screen monitoring
> Role: supervised live same-host measured-run review
> Scope: live invocation and evidence only; no runner implementation unless the
> runner fails before a fair live attempt

## 1. Mission

Run the new `3.5B` measured comparative runner under supervision and determine
whether this host can produce the first real same-host
`verdict_grade = "measured"` comparative-evidence record.

The required question is:

**Can the new `run-measured-short-prompt` subcommand run two repeats of the
same short workload against `owlmlx` and `omlx`, append a valid measured record,
and serve it through `/v1/runtime/comparative-evidence` and `/history`?**

If not, do not hang and do not fake the record. Let the runner emit
`inconclusive` or `rejected`, preserve raw artifacts, clean up processes, and
return the exact live blocker.

## 2. Coordination Truth

Current release state:

- `3.1`, `3.2`, `3.3`, and `3.4` are closed.
- `3.5` remains open.
- `3.5A0` proved:
  - `omlx` can serve `gemma-4-31B-it` and return `OK`
  - `vmlx doctor` can pass inference on `gemma-4-31B-it`
  - local weights exist at
    `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
  - comparative-evidence HTTP can serve an isolated ledger
  - old blocker was `harness_runner_missing`
- `3.5B` introduced:
  - `owlmlx/comparative_evidence_runner.py`
  - `scripts/runtime_comparative_evidence.py run-measured-short-prompt`
  - fake-command test coverage for measured / inconclusive / rejected flows
  - outcome:
    `owlmlx_release_floor_3_5B_measured_runner_introduced_pending_live_review`
- exact blocker now:
  `live_same_host_measured_record_missing`

This lane owns the live attempt. It does not own new runner feature work unless
the runner crashes before a fair attempt can be made.

## 3. Required Read Order

Read before running commands:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/comparative-evidence-harness-contract.md`
5. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5A0-codex-live-comparative-evidence-preflight-handoff.md`
6. `files/evidence/owlmlx/comparative-evidence/20260427T094224Z/preflight-summary.md`
7. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5B-measured-comparative-runner-handoff.md`
8. `scripts/runtime_comparative_evidence.py`
9. `owlmlx/comparative_evidence_runner.py`
10. `owlmlx/comparative_evidence_record.py`
11. `owlmlx/comparative_evidence_ledger.py`
12. `owlmlx/runtime/server.py`

## 4. Stable Checks Before Live Run

Run:

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

If these fail, stop with `needs_fix` and do not attempt the live 58G model.

## 5. Live Evidence Directory

Use a fresh UTC-stamped directory:

```text
files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/
```

Inside it, create:

- `runner-config.json`
- `live-run-notes.md`
- the runner artifacts written by `run-measured-short-prompt`
- `live-ledger.jsonl`
- raw terminal / command transcripts if useful

Do not reuse the 3.5A0 preflight ledger as the live measured ledger.

## 6. Workload And Invariants

Use the same workload as 3.5A0:

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
- host class from 3.5A0:
  `Mac17,6-arm64-macOS-26.4.1-128GB`

Do not change these between `owlmlx` and `omlx`.

## 7. Reference Runtime Setup

Start `omlx` using the probe venv path already proven by 3.5A0:

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

Use an unused localhost port, record it, and prove it is released at the end.

The `reference.argv` in `runner-config.json` may be a small Python one-liner
or helper command that POSTs to the running `omlx` OpenAI-compatible endpoint
and prints only the assistant content to stdout. It must use the same prompt,
model id, max tokens, and temperature.

## 8. owlmlx Runtime Setup

Use the smallest real owlmlx generation path available in this repo. The
expected starting point is:

```bash
PYTHONPATH=. python3 scripts/runtime_large_weight_first_smoke.py \
  --specimen-path /Users/yeemio/AI/Agent/models/gemma-4-31B-it \
  --memory-gb 80 \
  --prompt "Reply with exactly OK." \
  --max-tokens 2 \
  --include-known-venvs
```

It is acceptable to wrap this in the runner-config `owlmlx.argv` so the runner
controls timeout and artifact capture.

If a better existing owlmlx command produces stdout-observable generated text
for the same model and prompt, use it, but cite the file / command and keep the
same workload invariants.

Do not add a new generation implementation in this live lane.

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

Set runner timeouts deliberately. If `owlmlx` stalls, allow the runner to
record timeout failure instead of leaving the process hung.

## 10. HTTP Verification

After the runner appends a record, serve the isolated live ledger with a real
`uvicorn` process:

```bash
PYTHONPATH=. \
OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH=files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/live-ledger.jsonl \
python3 -m uvicorn owlmlx.runtime.server:create_fake_app \
  --factory --host 127.0.0.1 --port <OWLMLX_HTTP_PORT> --log-level warning
```

Then curl:

```bash
curl -sS http://127.0.0.1:<OWLMLX_HTTP_PORT>/v1/runtime/comparative-evidence
curl -sS http://127.0.0.1:<OWLMLX_HTTP_PORT>/v1/runtime/comparative-evidence/history
```

Record:

- HTTP status
- `surface`
- `version`
- `verdict_grade`
- `runtime_id` list
- metric fields for both runtimes

## 11. Process / Port Cleanup

At the end, prove all live ports are released:

```bash
lsof -n -iTCP:<OMLX_PORT> -sTCP:LISTEN || true
lsof -n -iTCP:<OWLMLX_HTTP_PORT> -sTCP:LISTEN || true
```

If any process remains, record PID / command and stop it if it belongs to this
lane.

Use Computer Use if terminal monitoring, process supervision, or screen
visibility makes the evidence clearer.

## 12. Ledger Decision Rule

If the live record has `verdict_grade = "measured"` and both HTTP routes serve
it from the isolated ledger:

- do **not** automatically mark floor `3.5` closed inside this live lane
  unless all closure criteria in
  `comparative-evidence-harness-contract.md` §8 are demonstrably satisfied
  and the handoff explicitly recommends closeout
- write the exact measured record path, HTTP output, and closeout
  recommendation

If the live record is `inconclusive` or `rejected`:

- keep `release-readiness-backlog.md` row `3.5` open
- write the exact blocker, for example:
  - `owlmlx_generation_timeout`
  - `first_token_latency_unobservable`
  - `reference_runtime_http_failure`
  - `measured_runner_live_config_invalid`
  - `rss_sampling_failed`

## 13. Allowed Edits

Allowed:

- new evidence directory under
  `files/evidence/owlmlx/comparative-evidence/<UTCSTAMP>/`
- one handoff:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5C-codex-live-measured-run-review-handoff.md`
- narrow `docs/source-of-truth/release-readiness-execution-plan.md` update
  recording the live result

Only if `verdict_grade = "measured"` is real and HTTP-served may you propose
or make a narrow `release-readiness-backlog.md` row update. If you do update
the backlog, include every reference needed by §4.2.

Do not edit:

- runner code unless the live attempt exposes a trivial wiring bug that can be
  fixed with tests inside this lane
- OwlOps
- OwlCoda
- `/Users/yeemio/AI/Agent`
- floor `3.6` or `3.7` docs

## 14. Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_5C_live_measured_record_emitted`
- `owlmlx_release_floor_3_5C_live_measured_record_closed_recommended`
- `owlmlx_release_floor_3_5C_live_run_inconclusive`
- `owlmlx_release_floor_3_5C_live_run_rejected`
- `owlmlx_release_floor_3_5C_measured_runner_needs_fix`

## 15. Required Handoff

Create:

`files/execution-prompts/owlmlx/owlmlx-release-floor-3-5C-codex-live-measured-run-review-handoff.md`

It must include:

- outcome label
- host class / ports / Python path
- evidence directory
- `runner-config.json`
- exact commands run and results
- process / port cleanup evidence
- ledger record summary
- HTTP curl summary
- whether a real `verdict_grade = "measured"` exists
- if measured exists, whether floor `3.5` closeout is recommended
- if not measured, exact blocker and next executor recommendation
- confirmation that no release/parity/replacement/production-grade claim was
  made

## 16. Hard Rules

- Do not fake measured evidence.
- Do not use fake-command unit-test records as live evidence.
- Do not change workload invariants between runtimes.
- Do not let a hung model process remain running.
- Do not silently skip `omlx` or `owlmlx`.
- Do not start floor `3.6` or `3.7`.
- Preserve unrelated dirty/staged work.
