# owlmlx Release Floor 3.6B / 3.7B Final Closeout Ledger Sync

> Date: 2026-04-28
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Executor: single executor only
> Objective: independently close out release floors `3.6 External Customer Evidence` and `3.7 Public Surface Discipline`

## 1. Role

You are the final closeout executor for the last two open release floors.

This is not a feature round. Do not implement runtime behavior. Do not widen
the public surface. Do not touch OwlOps, OwlCoda, `/Users/yeemio/AI/Agent`, or
any external repository.

Your job is to verify the already-produced `3.6A` and `3.7A` evidence, decide
whether each row may honestly close, update the release ledgers if warranted,
and write a handoff.

## 2. Current State

The release readiness backlog currently has:

- `3.1` closed
- `3.2` closed
- `3.3` closed
- `3.4` closed
- `3.5` closed
- `3.6` open, with `3.6A` closeout-recommended
- `3.7` open, with `3.7A` closeout-recommended

If both `3.6A` and `3.7A` pass your closeout review, move the floor count from
`5 / 7` to `7 / 7`.

If one floor fails review, close only the floor that passes and leave the other
open with a precise blocker. Do not mark a floor closed on incomplete evidence.

## 3. Required Inputs

Review these files before making any ledger change:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
- `docs/source-of-truth/public-surface.md`
- `tests/test_public_surface_contract.py`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-6A-external-customer-evidence-minimum-record-handoff.md`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-7A-public-surface-freeze-handoff.md`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/external-run-notes.md`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stdout.json`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stderr.txt`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.exit-status`

## 4. 3.6 Closeout Questions

Answer every question explicitly in the handoff.

1. Does `phase45-customer-runtime-evidence-ledger.md` contain a `3.6A`
   release-floor candidate record with verdict `pass`?
2. Was the consumer boundary outside the `owlmlx` repo, specifically from
   `/Users/yeemio/AI/gitrep/owlops`?
3. Did the probe fetch both `/v1/runtime/status` and `/healthz` from an
   `owlmlx` runtime service over HTTP?
4. Were both HTTP responses `200`?
5. Was the probe exit status `0`?
6. Was probe stderr empty?
7. Was the uvicorn process cleaned up and was port `8065` no longer listening
   at the end of the run?
8. Did the lane avoid promoting a local-only sanity run as external customer
   evidence?
9. Did the lane avoid release, parity, replacement, production-grade,
   superiority, wins, beats, equivalent, or matches claims?

If every answer is yes, row `3.6 external customer evidence` may close as:

`closed (via OwlOps-boundary external runtime-truth consumer evidence)`

Use date `2026-04-28`.

## 5. 3.7 Closeout Questions

Answer every question explicitly in the handoff.

1. Does `docs/source-of-truth/public-surface.md` exist and identify itself as
   authoritative?
2. Does it freeze the public technical-preview boundary by listing supported
   HTTP routes, supported runtime modules, supported operator scripts, and
   supported source-of-truth contracts?
3. Does it declare the label vocabulary
   `supported / partial / experimental / internal / not in scope`?
4. Does it state that anything not listed is `internal` by default?
5. Does it keep phase45 cache/exactness machinery internal instead of exposing
   it as public API?
6. Does it reference existing source-of-truth documents instead of duplicating
   their truth?
7. Does `tests/test_public_surface_contract.py` validate the boundary,
   referenced docs, referenced scripts, route listing, banned-vocabulary
   discipline, and floor `3.6` caveat?
8. Does `master-outline.md` include `public-surface.md` in the source-of-truth
   index?
9. Did the lane avoid release, parity, replacement, production-grade,
   superiority, wins, beats, equivalent, or matches claims?

If every answer is yes, row `3.7 public surface` may close as:

`closed (via runtime-owned public-surface freeze)`

Use date `2026-04-28`.

## 6. Required Verification Commands

Run exactly these minimum checks:

```bash
pytest -q tests/test_customer_runtime_evidence.py
pytest -q tests/test_public_surface_contract.py
python3 -m py_compile owlmlx/customer_runtime_evidence.py scripts/runtime_customer_runtime_evidence.py owlmlx/runtime/server.py
git diff --check
```

Optional but useful if something looks stale:

```bash
python3 scripts/runtime_customer_runtime_evidence.py --help
```

Do not rerun the live external HTTP probe unless the evidence files are missing
or internally inconsistent. This is a closeout review, not a new evidence
generation lane.

## 7. Allowed Edits

You may edit only:

- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/comparative-evidence-harness-contract.md` only if a
  stale cross-reference blocks the final floor count
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-6B-3-7B-final-closeout-ledger-sync-handoff.md`

You may not edit runtime code, tests, public-surface content, customer evidence
ledger content, comparative evidence artifacts, or external repositories in
this round.

## 8. Ledger Update Rules

If both floors pass:

- update `release-readiness-backlog.md` row `3.6 external customer evidence`
  from `open` to
  `closed (via OwlOps-boundary external runtime-truth consumer evidence)`
- update `release-readiness-backlog.md` row `3.7 public surface` from `open`
  to `closed (via runtime-owned public-surface freeze)`
- add references for `3.6`: the customer runtime evidence ledger, the `3.6A`
  handoff, and the `20260428T025051Z` evidence directory
- add references for `3.7`: `public-surface.md`,
  `tests/test_public_surface_contract.py`, and the `3.7A` handoff
- update `release-readiness-execution-plan.md` from `5 / 7` to `7 / 7`
- record the outcome label
  `owlmlx_release_floor_3_6B_3_7B_final_closeout_closed`

If only one floor passes:

- close only that row
- keep the failed row open
- update the execution plan with the precise blocker
- use outcome label
  `owlmlx_release_floor_3_6B_3_7B_partial_closeout_needs_fix`

If neither passes:

- do not move backlog rows
- update the execution plan with exact blockers
- use outcome label
  `owlmlx_release_floor_3_6B_3_7B_closeout_blocked`

## 9. Handoff Requirements

Write:

`files/execution-prompts/owlmlx/owlmlx-release-floor-3-6B-3-7B-final-closeout-ledger-sync-handoff.md`

The handoff must include:

- outcome label
- verdict: `closed`, `partial`, or `blocked`
- answers to every closeout question in §4 and §5
- exact commands run and results
- exact files changed
- whether backlog rows `3.6` and `3.7` moved
- final floor count
- explicit statement that no runtime code, external repo, or public-surface
  widening occurred
- explicit statement that no release / parity / replacement /
  production-grade claim was made

## 10. Hard Stops

Stop and report `blocked` if:

- the evidence directory is missing
- `3.6A` evidence cannot prove an external consumer boundary
- `/v1/runtime/status` or `/healthz` was not actually fetched over HTTP
- `public-surface.md` is missing or does not enforce internal-by-default
- `tests/test_public_surface_contract.py` is missing or failing
- any required verification command fails
- completing the closeout would require editing runtime behavior

