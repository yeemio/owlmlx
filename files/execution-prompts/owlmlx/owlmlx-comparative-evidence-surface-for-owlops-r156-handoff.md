# owlmlx Execution Handoff: Comparative Evidence Surface For OwlOps R156

> Lane: single owlmlx executor (external blocker round)
> Updated: 2026-04-26
> Active external blocker: OwlOps R156 live upstream proof
> Active release floor (this round): does **not** advance floor `3.5`

## 1. Final Verdict

`surface_closed`

Both `GET /v1/runtime/comparative-evidence` and
`GET /v1/runtime/comparative-evidence/history` are mounted, tested, and
live-curl verified against a real `uvicorn` process serving a real
`comparative_evidence_record` v1 record. The honest harness-failure
record (`verdict_grade = "rejected"`,
`failure_causes = ["reference_runtime_unavailable"]`) was emitted via
the runtime-owned operator entry, not synthesised by hand.

OwlOps R156 may now be unblocked. Release floor `3.5` is **not** closed
by this round.

## 2. Changed Files

New runtime modules:

- `owlmlx/comparative_evidence_schema.py` — single authority for surface
  identity, version, enumerations (`WORKLOAD_CLASSES`, `RUNTIME_IDS`,
  `VERDICT_GRADES`), required field sets, banned verdict vocabulary,
  and `validate_comparative_evidence_record(...)`
- `owlmlx/comparative_evidence_record.py` — frozen dataclasses
  (`ComparativeEvidenceMeasurement`, `ComparativeEvidenceRuntime`,
  `ComparativeEvidenceRecord`), `build_comparative_evidence_record(...)`,
  `comparative_evidence_record_to_dict(...)`
- `owlmlx/comparative_evidence_ledger.py` — append-only JSONL ledger
  (`ComparativeEvidenceLedger`), plus the `still_blocked` payload and
  `history` envelope helpers used by the HTTP routes

Modified runtime module (integration only):

- `owlmlx/runtime/server.py`
  - new imports for the ledger + helpers
  - new `comparative_evidence_ledger_path` parameter on `create_app(...)`
  - `create_fake_app()` honors `OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH`
    so live `uvicorn --factory` runs can attach a ledger without code
    changes
  - new route `GET /v1/runtime/comparative-evidence`
  - new route `GET /v1/runtime/comparative-evidence/history`

New operator entry:

- `scripts/runtime_comparative_evidence.py` with subcommands
  `append-rejected-record`, `latest`, `history`, plus `--ledger-path`

New tests:

- `tests/test_comparative_evidence_schema.py` (19 tests)
- `tests/test_comparative_evidence_record.py` (8 tests)
- 4 new tests appended to `tests/test_runtime_server.py` covering the
  two endpoints in `still_blocked` (no ledger) / `still_blocked` (empty
  ledger) / `surface_closed` (seeded ledger, both endpoints) modes

Updated source-of-truth docs:

- `docs/source-of-truth/comparative-evidence-harness-contract.md` —
  added §8.1 "HTTP Surface Sub-Closure (2026-04-26)" recording that
  the HTTP surface exists while keeping section 8 closure pending
- `docs/source-of-truth/comparative-evidence-schema-stub.md` — added
  §7.1 "Authoritative Module (2026-04-26)" naming
  `owlmlx/comparative_evidence_schema.py` as the single Python authority
- `docs/source-of-truth/runtime-status-schema.md` — added §16
  "Comparative Evidence Record Surface" describing the two routes,
  the ledger backing them, and the env-var connection point
- `docs/source-of-truth/release-readiness-execution-plan.md` — header
  date and §6 updated to record the OwlOps R156 closeout outcome and
  preserve the 3.4A0 next allocation

This handoff:

- `files/execution-prompts/owlmlx/owlmlx-comparative-evidence-surface-for-owlops-r156-handoff.md`

`docs/source-of-truth/release-readiness-backlog.md` was **not** modified;
floor `3.5` row stays `open` because the third closure bullet (a
`measured` record) is still missing.
`docs/source-of-truth/master-outline.md` was **not** modified; no new
markdown ledger doc was added in this round, so the index needs no row.

## 3. Pytest Results

```text
$ pytest -q tests/test_comparative_evidence_schema.py tests/test_comparative_evidence_record.py
...........................                                              [100%]
27 passed in 0.14s

$ pytest -q tests/test_runtime_server.py -k "comparative_evidence"
....                                                                     [100%]
4 passed, 37 deselected in 0.34s

$ pytest -q tests/test_runtime_server.py
.........................................                                [100%]
41 passed in 1.12s
```

The full `test_runtime_server.py` was also run (41 pass, including the
4 new comparative-evidence tests on top of the prior 37) to catch any
regression from the new imports / route mounts.

## 4. Compile Checks

```text
$ python3 -m py_compile \
    owlmlx/comparative_evidence_schema.py \
    owlmlx/comparative_evidence_record.py \
    owlmlx/comparative_evidence_ledger.py \
    owlmlx/runtime/server.py \
    scripts/runtime_comparative_evidence.py
compile OK
```

## 5. Live `uvicorn` + `curl` Proof

Seeded a temporary ledger via the operator entry, started `uvicorn` in
factory mode against the env-var ledger path, curled both endpoints,
stopped the process, confirmed the listener was released:

```text
$ mkdir -p /tmp/owlmlx-3-2C-r156
$ python3 scripts/runtime_comparative_evidence.py \
    --ledger-path /tmp/owlmlx-3-2C-r156/comparative-evidence-ledger.jsonl \
    append-rejected-record
{
  "evidence_pointer": "docs/source-of-truth/comparative-evidence-ledger.md#row-rejected",
  "host_class": "darwin-arm64-host",
  "recorded_at": "2026-04-26T15:01:56Z",
  "runtimes": [
    {"runtime_id": "owlmlx", "runtime_version": "0.0.0-runtime7", "measurement": {...failure_count: 1, failure_causes: ["reference_runtime_unavailable"]...}},
    {"runtime_id": "omlx",   "runtime_version": "unavailable",     "measurement": {...failure_count: 1, failure_causes: ["reference_runtime_unavailable"]...}}
  ],
  "surface": "owlmlx.comparative_evidence_record",
  "verdict_grade": "rejected",
  "verdict_text": "rejected: reference_runtime_unavailable on host_class=darwin-arm64-host, workload_class=single_prompt_short",
  "version": "v1",
  "workload_class": "single_prompt_short",
  "workload_invariants": {"decode_max_tokens": 16, "decode_temperature": 0.0, "model_id": "qwen3-0.6b", "model_quantization": "q4", "prompt_set_hash": "sha256:placeholder-prompt-set", "serving_budget_bytes": 6442450944}
}

$ OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH=/tmp/owlmlx-3-2C-r156/comparative-evidence-ledger.jsonl \
  python3 -m uvicorn owlmlx.runtime.server:create_fake_app \
    --factory --host 127.0.0.1 --port 8056 &
$ curl -sS http://127.0.0.1:8056/v1/runtime/comparative-evidence
HTTP_STATUS=200
{"surface":"owlmlx.comparative_evidence_record","version":"v1",
 "host_class":"darwin-arm64-host","workload_class":"single_prompt_short",
 "verdict_grade":"rejected",
 "verdict_text":"rejected: reference_runtime_unavailable on host_class=darwin-arm64-host, workload_class=single_prompt_short",
 ...}

$ curl -sS http://127.0.0.1:8056/v1/runtime/comparative-evidence/history
HTTP_STATUS=200
{"surface":"owlmlx.comparative_evidence_record_history","version":"v1",
 "ledger_status":"available","records":[ ...one full v1 record... ]}

$ kill <uvicorn-pid>
$ lsof -n -iTCP:8056 -sTCP:LISTEN
(no output, exit 1 — port released)

$ git diff --check
(clean, exit 0)
```

## 6. Endpoint Decisive Fields

`GET /v1/runtime/comparative-evidence` (HTTP 200):

| Field | Value |
| --- | --- |
| `surface` | `owlmlx.comparative_evidence_record` |
| `version` | `v1` |
| `verdict_grade` | `rejected` |
| `host_class` | `darwin-arm64-host` |
| `workload_class` | `single_prompt_short` |

`GET /v1/runtime/comparative-evidence/history` (HTTP 200):

| Field | Value |
| --- | --- |
| `surface` | `owlmlx.comparative_evidence_record_history` |
| `version` | `v1` |
| `ledger_status` | `available` |
| `records` count | `1` |

When the ledger is not connected or empty, both endpoints return HTTP
503 with the explicit `still_blocked` payload (verified by tests
`test_comparative_evidence_endpoint_still_blocked_when_ledger_not_connected`,
`test_comparative_evidence_history_endpoint_still_blocked_when_ledger_not_connected`,
`test_comparative_evidence_endpoint_still_blocked_when_ledger_empty`).

## 7. Real v1 Record vs Measured Record

- **Real v1 record exists**: yes. Validated by
  `validate_comparative_evidence_record(...)` at append time and again
  by the test
  `test_comparative_evidence_endpoint_returns_real_record_when_ledger_seeded`.
- **`verdict_grade = "measured"` record exists**: no. The current
  record is `verdict_grade = "rejected"` because no `oMLX` / `vMLX`
  binary was invoked on the host in this round; per
  `comparative-evidence-harness-contract.md` §5.4, harness failure is
  itself truth and is emitted as `rejected`, not silently skipped.

## 8. Release Floor 3.5 Status

Floor `3.5` of `release-readiness-backlog.md` remains **open**.

Closure of floor `3.5` requires
`comparative-evidence-harness-contract.md` §8 to be fully satisfied —
including the third bullet, which mandates "at least one record in the
ledger for at least one `(host_class, workload_class)` pair, with
`verdict_grade = "measured"`". This round produced only a `rejected`
record. Honest measurement against `omlx` / `vmlx` on a same-host run
remains future work; it cannot be back-filled by the HTTP surface
existing.

The ledger row in `release-readiness-backlog.md` section 5 was **not**
moved.

## 9. Remaining Blocker (Reason Floor 3.5 Still Open)

`measured_record_against_reference_runtime_on_same_host`

Specifically: a follow-up round must invoke at least one of `oMLX` or
`vMLX` on the same host as `owlmlx`, capture the six required
measurement fields per runtime, and append a record with
`verdict_grade = "measured"`. The harness contract §5.5 freezes the
reference runtimes; §5.4 forbids silent skipping; §5.1 forbids
`parity` / `equivalent` / `replaces` / `replacement` /
`production-ready` / `superior` / `wins` / `beats` / `matches` in the
verdict text.

## 10. Lane Constraints Confirmation

- **No OwlOps edits**: confirmed. `git status -uno` shows only
  `owlmlx`-internal paths. No file under `owlops`, `owlcoda`, or
  `/Users/yeemio/AI/Agent` was opened, read, or written in this round.
- **No second executor**: confirmed. This round is a single owlmlx
  executor (`claude-opus-4-7`, fresh instance, distinct from the
  3.2A/3.2B author and the 3.2C reviewer instances; same Opus family).
  No parallel allocation to OwlOps, no parallel allocation to 3.4A0.
- **No synthetic `measured` data**: confirmed. The only emitted record
  has `verdict_grade = "rejected"` and `failure_count = 1` per
  runtime. The schema validator and the build-time validator both
  enforce that `failure_count > 0` requires `failure_causes`, so the
  `rejected` record cannot be quietly upgraded to `measured` without
  removing the failures, which would itself fail validation against
  the next layer of evidence.
- **No banned verdict vocabulary**: confirmed. The verdict text is
  `"rejected: reference_runtime_unavailable on host_class=..., workload_class=..."`.
  `verdict_text_uses_banned_vocabulary(...)` returns `False` for it.
  Tested via `test_validate_rejects_record_with_banned_verdict_vocabulary`
  and `test_verdict_text_banned_vocabulary_detector`.
- **No OwlOps UI rendering in owlmlx**: confirmed. The new modules
  return runtime-owned record dicts; no operator-app rendering, theme
  state, or UI fragments live in `owlmlx/`.
- **No release / replacement / production-grade claim**: confirmed.
  All three new doc sections (8.1, 7.1, §16) explicitly disclaim
  release-readiness and floor-3.5 closure. The execution-plan §6
  edit also keeps the `does not close release floor 3.5` language.
- **No unrelated dirty files touched**: confirmed. `git diff --check`
  is clean; the staged-from-prior-rounds file set seen at session
  start is preserved. The only newly-created paths in this round are
  the five new module/test files, the operator script, the four doc
  edits listed in §2, and this handoff.
- **No 3.2 / 3.4 scheduling/recovery work**: confirmed. The new code
  does not touch `serving.py`, `runtime/kernel.py`, or any recovery
  module. Floor `3.4` work (3.4A0) remains the next active prompt
  per the execution plan.

## 11. Module / Surface Summary

| Surface | Mounted | Backed by |
| --- | --- | --- |
| `owlmlx.comparative_evidence_record` v1 | `GET /v1/runtime/comparative-evidence` | JSONL ledger via `ComparativeEvidenceLedger.latest()` |
| `owlmlx.comparative_evidence_record_history` v1 | `GET /v1/runtime/comparative-evidence/history` | JSONL ledger via `ComparativeEvidenceLedger.history()` |
| `owlmlx.comparative_evidence_schema` (constants + validator) | imported by record / ledger / server modules | single Python authority |
| Operator entry | `scripts/runtime_comparative_evidence.py` | `append-rejected-record / latest / history` |
| Live-mount env var | `OWLMLX_COMPARATIVE_EVIDENCE_LEDGER_PATH` | honored by `create_fake_app()` |

## 12. Next Step

Per the updated execution plan §6, the next active prompt is
`files/execution-prompts/owlmlx/owlmlx-release-floor-3-4A0-reclaim-barrier-event.md`,
not a 3.5 follow-up. Floor `3.5` measured-record work is queued behind
3.4A0 unless the coordinator explicitly reorders.
