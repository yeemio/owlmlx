# owlmlx Release Floor 3.5F Comparative Evidence Closeout Review Handoff

> Date: 2026-04-28
> Outcome label: `owlmlx_release_floor_3_5F_closeout_closed`
> Verdict: `closed`
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Evidence directory: `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/`

## Verdict

Floor `3.5 Comparative Evidence Against Reference Runtimes` is closed via one
fresh same-host measured comparative-evidence record for `owlmlx` and `omlx`.

The closeout review did not perform a new measured-run implementation and did
not start floors `3.6` or `3.7`.

This closure does not make release, parity, replacement, production-grade,
superiority, wins, beats, or equivalent claims.

## Evidence Reviewed

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/comparative-evidence-harness-contract.md`
- `docs/source-of-truth/comparative-evidence-schema-stub.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5E-codex-live-measured-run-rerun-handoff.md`
- `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-run-notes.md`
- `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl`
- `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-latest.txt`
- `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-history.txt`
- `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/manifest.json`
- `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/commands.json`
- `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/summary.md`
- `owlmlx/comparative_evidence_record.py`
- `owlmlx/comparative_evidence_ledger.py`
- `owlmlx/comparative_evidence_runner.py`
- `scripts/runtime_comparative_evidence.py`
- `owlmlx/runtime/server.py`

## Review Answers

1. yes - 3.5E satisfies harness-contract section 8: record builder module,
   operator entry, one measured ledger record, and stable HTTP consumption all
   exist.
2. yes - `owlmlx/comparative_evidence_record.py` owns
   `build_comparative_evidence_record(...)` and
   `comparative_evidence_record_to_dict(...)`.
3. yes - `scripts/runtime_comparative_evidence.py` is the runtime-owned
   operator entry and exposes `run-measured-short-prompt`, `latest`, and
   `history`.
4. yes - `live-ledger.jsonl` contains one record for
   `host_class = "Mac17,6-arm64-macOS-26.4.1-128GB"` and
   `workload_class = "single_prompt_short"` with
   `verdict_grade = "measured"`.
5. yes - `http-latest.txt` and `http-history.txt` both captured `HTTP/1.1 200
   OK` from the fresh ledger.
6. yes - both runtimes used the same workload and invariants:
   `gemma-4-31B-it`, `full_precision_unquantized`, max tokens `2`,
   temperature `0.0`, prompt hash
   `sha256:b4d50a67a784a449e0c763c401bb9f95fb37804dff5765d8b4f95fd202eb7d77`,
   and serving budget `85899345920`.
7. yes - the manifest records two attempts for `owlmlx` and two attempts for
   `omlx`.
8. yes - both runtime measurements include throughput, first-token latency,
   peak resident set, wall clock, completed count, failure count, and failure
   causes where needed.
9. yes - both runtimes have `completed_request_count = 2` and
   `failure_count = 0`.
10. yes - the evidence pointer resolves to `run/manifest.json`; raw stdout,
    stderr, RSS samples, `commands.json`, and `summary.md` are present.
11. yes - `omlx.peak_resident_set_bytes = 53823569920`; RSS samples include
    external server PID `84730` plus the HTTP client wrapper, not only the
    client process.
12. yes - `owlmlx.peak_resident_set_bytes = 59764850688`; RSS samples include
    the wrapper PID plus the MLX child process tree.
13. yes - `owlmlx.first_token_strategy = regex:"text":\s*"[^"]+"` and stdout
    contains generated output `"text": " OK."`, so TTFT is not taken from the
    diagnostic preamble.
14. yes - latest and history HTTP captures agree with the fresh ledger record.
15. yes - 3.5E cleanup evidence shows ports `8063` and `8064` released with no
    lane-owned process left listening.
16. yes - `verdict_text` uses the allowed `measured:` shape and avoids banned
    parity / replacement / superiority vocabulary.
17. yes - the closeout review stayed inside
    `/Users/yeemio/AI/gitrep/owlmlx`; it did not edit OwlOps, OwlCoda, desktop
    UI, or `/Users/yeemio/AI/Agent`.
18. yes - stale source-of-truth text was found and corrected: the backlog no
    longer says there is zero head-to-head measurement, and the harness
    contract now records the 2026-04-28 measured-record closure.

## Command Verification

```bash
pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
# 27 passed in 0.13s

pytest -q tests/test_runtime_comparative_evidence_measured_runner.py
# 37 passed in 3.59s

pytest -q tests/test_runtime_server.py -k "comparative_evidence"
# 4 passed, 37 deselected in 0.31s

python3 -m py_compile \
  owlmlx/comparative_evidence_schema.py \
  owlmlx/comparative_evidence_record.py \
  owlmlx/comparative_evidence_ledger.py \
  owlmlx/comparative_evidence_runner.py \
  scripts/runtime_comparative_evidence.py \
  owlmlx/runtime/server.py
# passed with no output

python3 scripts/runtime_comparative_evidence.py \
  --ledger-path files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl \
  latest
# returned the measured `owlmlx.comparative_evidence_record` for owlmlx + omlx

python3 scripts/runtime_comparative_evidence.py \
  --ledger-path files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl \
  history
# returned `owlmlx.comparative_evidence_record_history` with ledger_status=available

python3 - <<'PY'
import json
from pathlib import Path
base = Path("files/evidence/owlmlx/comparative-evidence/20260428T004500Z")
record = json.loads(base.joinpath("live-ledger.jsonl").read_text().splitlines()[-1])
print(record["verdict_grade"])
for runtime in record["runtimes"]:
    print(runtime["runtime_id"], runtime["measurement"])
print(base.joinpath("run/commands.json").exists())
print(base.joinpath("run/manifest.json").exists())
PY
# measured
# owlmlx {'completed_request_count': 2, 'failure_count': 0, ...}
# omlx {'completed_request_count': 2, 'failure_count': 0, ...}
# True
# True

git diff --check
# passed with no output
```

## Ledger Decision

`docs/source-of-truth/release-readiness-backlog.md` section 5 row
`3.5 comparative evidence` was moved from `open (contract surface)` to
`closed (via same-host measured comparative evidence)` with close date
`2026-04-28`.

`docs/source-of-truth/release-readiness-execution-plan.md` was updated from
`4 / 7` to `5 / 7` closed floor items.

## Files Changed

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/comparative-evidence-harness-contract.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5F-comparative-evidence-closeout-review-handoff.md`

## Next Active Floor

Next active floor: `3.6 External Customer Evidence`.

The next round should not reopen 3.5 unless a later consumer finds record,
ledger, or HTTP drift. The next prompt should target one external deployment
evidence record with host class, workload class, frozen pass/fail verdict, and
one tracked blocker or success outcome.
