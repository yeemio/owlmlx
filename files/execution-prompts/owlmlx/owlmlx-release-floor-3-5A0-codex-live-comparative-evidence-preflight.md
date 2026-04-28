# owlmlx Execution Prompt 3.5A0: Codex Live Comparative Evidence Preflight

> Date: 2026-04-27
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.5 Comparative Evidence Against Reference Runtimes`
> Assigned executor: Codex desktop
> Required capability: Computer Use is allowed for live terminal / process /
> screen monitoring when useful
> Role: live same-host preflight, reference-runtime availability check, and
> first honest measured-run attempt
> Scope: runtime evidence only; do not close floor `3.5` unless the measured
> record criteria are actually met

## 1. Mission

Move release floor `3.5` from contract-only surface toward real same-host
comparative evidence against `oMLX` or `vMLX`.

The required question is:

**Can this host produce one honest `comparative_evidence_record` with
`verdict_grade = "measured"` by running the same workload against `owlmlx`
and at least one reference runtime (`omlx` or `vmlx`) on the same host?**

Use Codex desktop's monitoring advantage for live process visibility:

- monitor terminal panes / long-running commands when useful
- watch for hung runs, memory pressure, runaway server processes, or port
  leaks
- record exact process / port / command evidence
- prefer real command output and runtime artifacts over inferred status

Do not fake a measured record. If the reference runtime is unavailable,
weights are missing, or the runner path is incomplete, emit an honest
`rejected` or `inconclusive` record and write the exact blocker.

## 2. Coordination Truth

Current release state:

- `3.1`, `3.2`, and `3.3` are closed in the release ledger.
- `3.4` is being reviewed by the separate ClaudeCode `3.4B` closeout lane.
- `3.5` has the HTTP surface mounted:
  - `GET /v1/runtime/comparative-evidence`
  - `GET /v1/runtime/comparative-evidence/history`
- `owlmlx.comparative_evidence_record` v1 exists.
- `scripts/runtime_comparative_evidence.py` exists and can append / read
  records.
- The only known live record so far is `verdict_grade = "rejected"` because
  the reference runtime was unavailable.
- Floor `3.5` remains open until at least one same-host measured record exists
  and is served by the stable HTTP surface.

This lane may run in parallel with `3.4B` because it must not edit the `3.4`
ledger row and must not claim release progress before measured evidence
exists.

## 3. Required Read Order

Read before running commands:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/comparative-evidence-harness-contract.md`
5. `docs/source-of-truth/comparative-evidence-schema-stub.md`
6. `docs/source-of-truth/reference-runtime-comparison-matrix.md`
7. `docs/source-of-truth/runtime-status-schema.md`
8. `owlmlx/comparative_evidence_schema.py`
9. `owlmlx/comparative_evidence_record.py`
10. `owlmlx/comparative_evidence_ledger.py`
11. `scripts/runtime_comparative_evidence.py`
12. `owlmlx/runtime/server.py`
13. Related tests:
    `tests/test_comparative_evidence_schema.py`,
    `tests/test_comparative_evidence_record.py`,
    `tests/test_runtime_server.py`

## 4. Required Preflight

Create a same-host preflight report that answers:

1. What exact host class is being used?
2. Which Python / environment is used for `owlmlx`?
3. Is `omlx` available as a command, Python module, repo checkout, or
   runnable script?
4. Is `vmlx` available as a command, Python module, repo checkout, or
   runnable script?
5. Which model id and quantization can all participating runtimes use without
   changing the workload invariants?
6. Are weights present locally, or does the run require network / download?
7. Can `owlmlx` produce the selected workload output locally?
8. Can at least one reference runtime produce the same workload output locally?
9. Can peak resident set / wall-clock / first-token latency / throughput be
   measured from the available runner path?
10. Is the comparative evidence HTTP surface serving the latest ledger record
    from a real `uvicorn` process?

Use concrete commands. If a command is missing, record the missing command and
path searched. Do not infer availability from docs alone.

## 5. Preferred Workload

Start with the smallest honest workload:

- `workload_class = "single_prompt_short"`
- one prompt
- low `decode_max_tokens` sufficient to measure first token and throughput
- `decode_temperature = 0` or the nearest deterministic equivalent
- same model id / quantization / budget across runtimes
- two repeat runs per runtime if both runtimes are available

If the same model cannot be used across `owlmlx` and a reference runtime, do
not emit `measured`. Emit `rejected` or `inconclusive` with the exact reason.

## 6. Measured Record Rule

You may emit `verdict_grade = "measured"` only if all are true:

- the same workload and workload invariants ran against `owlmlx`
- the same workload and workload invariants ran against `omlx` or `vmlx`
- both ran on the same `host_class`
- at least two repeat runs per runtime exist
- raw artifacts include stdout/stderr, resource samples, and re-run commands
- measurement fields exist for each runtime:
  - `throughput_tokens_per_second`
  - `first_token_latency_ms`
  - `peak_resident_set_bytes`
  - `wall_clock_ms`
  - `completed_request_count`
  - `failure_count`
  - `failure_causes` when failures occur
- the record is appended to the runtime-owned ledger and served by
  `/v1/runtime/comparative-evidence`

If any condition fails, do not emit `measured`.

## 7. Allowed Edits

Prefer no code edits in this preflight lane.

Allowed edits:

- raw evidence artifacts under a repo-local evidence directory if one already
  exists, or under a new narrow path such as
  `files/evidence/owlmlx/comparative-evidence/<timestamp>/`
- one handoff:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5A0-codex-live-comparative-evidence-preflight-handoff.md`
- only if unavoidable, a tiny documentation note in
  `docs/source-of-truth/release-readiness-execution-plan.md` that records an
  exact external/runtime blocker discovered by the live run

Do not edit:

- `docs/source-of-truth/release-readiness-backlog.md`
- `3.4` closeout docs
- OwlOps
- OwlCoda
- `/Users/yeemio/AI/Agent`

If you discover that `scripts/runtime_comparative_evidence.py` cannot produce
measured records because it only supports rejected/latest/history operations,
do not silently expand the script in this lane. Record that as the exact
ClaudeCode/code-lane follow-up unless the change is truly trivial and fully
tested.

## 8. Required Commands

Run the stable unit checks first:

```bash
pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
pytest -q tests/test_runtime_server.py -k "comparative_evidence"
python3 -m py_compile \
  owlmlx/comparative_evidence_schema.py \
  owlmlx/comparative_evidence_record.py \
  owlmlx/comparative_evidence_ledger.py \
  scripts/runtime_comparative_evidence.py \
  owlmlx/runtime/server.py
```

Then run live checks:

```bash
python3 scripts/runtime_comparative_evidence.py --help
python3 - <<'PY'
import platform, sys
print("python", sys.executable)
print("platform", platform.platform())
print("machine", platform.machine())
PY
command -v omlx || true
command -v vmlx || true
python3 - <<'PY'
for name in ("omlx", "vmlx", "mlx_lm"):
    try:
        __import__(name)
        print(name, "import_ok")
    except Exception as exc:
        print(name, "import_failed", type(exc).__name__, str(exc))
PY
```

If starting a server, use an isolated temporary ledger and an unused localhost
port. After the run, prove the port is released or record the process that
remains:

```bash
lsof -n -iTCP:<port> -sTCP:LISTEN || true
```

Use Computer Use if terminal or system monitoring makes the live state clearer.

## 9. Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_5A0_measured_record_emitted`
- `owlmlx_release_floor_3_5A0_reference_runtime_unavailable`
- `owlmlx_release_floor_3_5A0_harness_runner_missing`
- `owlmlx_release_floor_3_5A0_inconclusive_live_preflight`
- `owlmlx_release_floor_3_5A0_blocked_missing_weights`

## 10. Required Handoff

Create:

`files/execution-prompts/owlmlx/owlmlx-release-floor-3-5A0-codex-live-comparative-evidence-preflight-handoff.md`

It must include:

- outcome label
- exact host class / Python / repo path
- reference runtime availability matrix for `omlx` and `vmlx`
- selected workload and workload invariants
- commands run and key output
- whether a `measured` record exists
- if measured exists, ledger path and HTTP curl output
- if measured does not exist, exact blocker and smallest next executor
  recommendation
- process / port cleanup evidence
- explicit statement that no parity, replacement, release-ready, or
  production-grade claim was made

## 11. Hard Rules

- Do not fake measured data.
- Do not use one-sided `owlmlx` data as comparative evidence.
- Do not change workload invariants between runtimes.
- Do not promote rejected or inconclusive records to release progress.
- Do not edit the 3.4 ledger row.
- Do not touch OwlOps, OwlCoda, or `/Users/yeemio/AI/Agent`.
- Preserve unrelated dirty/staged work.
