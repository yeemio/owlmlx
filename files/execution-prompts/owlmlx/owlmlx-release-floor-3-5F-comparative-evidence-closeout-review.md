# owlmlx Execution Prompt 3.5F: Comparative Evidence Closeout Review

> Date: 2026-04-28
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.5 Comparative Evidence Against Reference Runtimes`
> Assigned executor: independent closeout reviewer
> Role: review / verification / ledger decision
> Scope: closeout review only; no new measured-run implementation

## 1. Mission

Perform the independent closeout review for release floor `3.5 Comparative
Evidence Against Reference Runtimes`.

This round decides whether the combined `3.5A0` through `3.5E` evidence
honestly satisfies the literal `release-readiness-backlog.md` section `3.5`
requirement and `comparative-evidence-harness-contract.md` section `8`
closure criteria.

If and only if the evidence passes, move the section-5 ledger row for `3.5`
from `open (contract surface)` to
`closed (via same-host measured comparative evidence)`.

Do not start floor `3.6`.
Do not start floor `3.7`.
Do not make release, parity, replacement, production-grade, or superiority
claims.

## 2. Coordination Truth

Current frozen position:

- `3.1 Cache Scheduler Closure` is closed.
- `3.2 Memory-Pressure Decision Closure` is closed.
- `3.3 Model Residency Non-Resident Path` is closed.
- `3.4 Recovery Policy Closure` is closed.
- `3.5 Comparative Evidence` is closeout-recommended, not ledger-closed.

Important prior results:

- `3.5A0` proved `omlx` and `vmlx` are available on this host and
  `gemma-4-31B-it` local weights exist.
- `3.5B` introduced the measured runner.
- `3.5C` produced a schema-valid measured record but was rejected because RSS
  and first-token timing were not closeout-grade.
- `3.5D` fixed process-tree / external PID RSS sampling and token-aware
  first-token detection.
- `3.5E` produced a fresh closeout-recommended measured record under:
  `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/`

The reported 3.5E measured record:

- `verdict_grade = "measured"`
- `runtime_id` list: `owlmlx`, `omlx`
- both runtimes completed `2` repeats
- both runtimes have `failure_count = 0`
- `owlmlx.peak_resident_set_bytes = 59764850688`
- `omlx.peak_resident_set_bytes = 53823569920`
- `owlmlx.first_token_latency_ms = 12562.1948960179`
- `omlx.first_token_latency_ms = 6643.867458493332`
- latest and history HTTP routes returned `200 OK` from the fresh ledger
- ports `8063` and `8064` were released and no lane-owned processes remained

Treat those as claims to reproduce or falsify.

## 3. Required Read Order

Read before deciding:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/comparative-evidence-harness-contract.md`
5. `docs/source-of-truth/comparative-evidence-schema-stub.md`
6. `docs/source-of-truth/runtime-status-schema.md`
7. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5A0-codex-live-comparative-evidence-preflight-handoff.md`
8. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5B-measured-comparative-runner-handoff.md`
9. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5C-codex-live-measured-run-review-handoff.md`
10. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5D-measured-runner-process-tree-and-token-detection-fix-handoff.md`
11. `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5E-codex-live-measured-run-rerun-handoff.md`
12. `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-run-notes.md`
13. `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl`
14. `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-latest.txt`
15. `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-history.txt`
16. `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/manifest.json`
17. `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/commands.json`
18. `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/summary.md`
19. `owlmlx/comparative_evidence_schema.py`
20. `owlmlx/comparative_evidence_record.py`
21. `owlmlx/comparative_evidence_ledger.py`
22. `owlmlx/comparative_evidence_runner.py`
23. `scripts/runtime_comparative_evidence.py`
24. related tests:
    `tests/test_comparative_evidence_schema.py`,
    `tests/test_comparative_evidence_record.py`,
    `tests/test_runtime_comparative_evidence_measured_runner.py`,
    `tests/test_runtime_server.py`

## 4. Review Questions

Answer each question with `yes`, `no`, or `not proven`, and cite file paths
plus line numbers where possible.

1. Does the 3.5E record satisfy `comparative-evidence-harness-contract.md`
   section `8` closure criteria?
2. Does a runtime-owned module own `build_comparative_evidence_record(...)`
   and `comparative_evidence_record_to_dict(...)`?
3. Does a runtime-owned operator entry exist at
   `scripts/runtime_comparative_evidence.py`?
4. Does at least one ledger record exist for one `(host_class, workload_class)`
   pair with `verdict_grade = "measured"`?
5. Is the measured record consumable through stable HTTP latest and history
   surfaces?
6. Did the same `workload_class` and `workload_invariants` run against both
   `owlmlx` and `omlx` on the same `host_class`?
7. Are there at least two repeat runs per runtime?
8. Do both runtime measurements include:
   `throughput_tokens_per_second`, `first_token_latency_ms`,
   `peak_resident_set_bytes`, `wall_clock_ms`,
   `completed_request_count`, `failure_count`, and failure causes when needed?
9. Are both runtime `completed_request_count` values equal to `2` and both
   `failure_count` values equal to `0`?
10. Does the evidence pointer resolve to artifacts with raw stdout/stderr,
    resource samples, and rerun commands?
11. Does `omlx.peak_resident_set_bytes` honestly include the live server PID
    / external PID tree and not only the HTTP client wrapper?
12. Does `owlmlx.peak_resident_set_bytes` honestly include wrapper plus child
    process tree?
13. Does `owlmlx.first_token_latency_ms` come from generated-token output,
    not from diagnostic JSON/status preamble?
14. Do latest and history HTTP captures agree with the fresh ledger?
15. Were ports and lane-owned processes cleaned up?
16. Does the record avoid banned verdict vocabulary and avoid parity /
    replacement / superiority claims?
17. Did the work stay inside `/Users/yeemio/AI/gitrep/owlmlx` without editing
    OwlOps, OwlCoda, desktop UI, or `/Users/yeemio/AI/Agent`?
18. Is there any stale source-of-truth text that still says floor `3.5` is
    blocked only on reference runtime availability or only on surface
    exposure, contradicting the measured-record evidence?

## 5. Required Verification

Run at minimum:

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
python3 scripts/runtime_comparative_evidence.py \
  --ledger-path files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl \
  latest
python3 scripts/runtime_comparative_evidence.py \
  --ledger-path files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl \
  history
git diff --check
```

Also inspect the fresh evidence artifacts directly:

```bash
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
```

If a command is impossible to run, record the exact reason and do not claim the
evidence exists.

## 6. Allowed Edits

This is a closeout-review round. Allowed edits are limited to:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- narrow source-of-truth wording fixes needed to remove stale contradiction
  discovered during review
- one handoff:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5F-comparative-evidence-closeout-review-handoff.md`

Do not edit runner code or tests unless the review finds a blocking defect. If
a blocking defect exists, stop with `needs_fix` and describe the exact
executor-owned follow-up instead of silently repairing it inside this review.

## 7. Ledger Decision Rule

If every required review question passes and verification is green:

- update `docs/source-of-truth/release-readiness-backlog.md` section 5 row
  `3.5 comparative evidence`:
  - status: `closed (via same-host measured comparative evidence)`
  - date: `2026-04-28`
  - references should include at least:
    `comparative-evidence-harness-contract.md`,
    `comparative-evidence-schema-stub.md`,
    `tests/test_runtime_comparative_evidence_measured_runner.py`,
    `scripts/runtime_comparative_evidence.py`,
    `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl`,
    `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/run/manifest.json`,
    `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-latest.txt`,
    `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-history.txt`,
    `owlmlx-release-floor-3-5E-codex-live-measured-run-rerun-handoff.md`,
    and this 3.5F handoff
- update `docs/source-of-truth/release-readiness-execution-plan.md`:
  - section 2 count: `4 / 7` -> `5 / 7`
  - record the 3.5F closeout outcome
  - set the next active floor to `3.6 External Customer Evidence`
    unless the review finds a reason that `3.7 Public Surface` must be
    sequenced first

If any required review question fails:

- do not move the backlog ledger
- write the exact blocker and the smallest next executor prompt needed
- use `needs_fix` or `still_blocked`, not `closed`

## 8. Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_5F_closeout_closed`
- `owlmlx_release_floor_3_5F_closeout_needs_fix`
- `owlmlx_release_floor_3_5F_closeout_still_blocked`
- `owlmlx_release_floor_3_5F_closeout_blocked_missing_evidence`

## 9. Required Handoff Shape

Create:

`files/execution-prompts/owlmlx/owlmlx-release-floor-3-5F-comparative-evidence-closeout-review-handoff.md`

It must contain:

- outcome label
- verdict: `closed`, `needs_fix`, `still_blocked`, or
  `blocked_missing_evidence`
- review answers for all questions in section 4
- exact commands run and results
- files changed
- ledger decision
- next active floor if closed
- exact next prompt recommendation if not closed
- explicit statement that no new measured-run implementation was performed
  unless a blocking defect forced a stop

## 10. Hard Rules

- Do not mark floor `3.5` closed without green verification and
  closeout-grade measured evidence.
- Do not treat 3.5E `closed_recommended` as final closure by itself.
- Do not start floor `3.6` or `3.7` implementation in this round.
- Do not create a second executor lane.
- Do not edit OwlOps, OwlCoda, desktop UI, or `/Users/yeemio/AI/Agent`.
- Do not promote release, parity, replacement, production-grade, superiority,
  wins, beats, or equivalent claims.
- Preserve unrelated dirty/staged work.
