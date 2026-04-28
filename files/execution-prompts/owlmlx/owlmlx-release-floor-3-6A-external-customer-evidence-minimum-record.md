# owlmlx Execution Prompt 3.6A: External Customer Evidence Minimum Record

> Date: 2026-04-28
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.6 External Customer Evidence`
> Assigned executor: Codex desktop with Computer Use
> Role: live external-deployment evidence collection and ledger update
> Scope: produce one honest external deployment evidence record or freeze the
> exact external blocker

## 1. Mission

Produce the smallest honest external deployment evidence record for `owlmlx`.

The required question is:

**Is there at least one deployment outside the `owlmlx` repo that consumes
`owlmlx` runtime truth or inference and can be recorded with host class,
workload class, frozen pass/fail verdict, and one tracked external blocker or
success outcome?**

This is not another internal benchmark. The 3.5 measured `owlmlx` vs `omlx`
record does not satisfy 3.6 by itself. The evidence must come from an external
consumer / deployment boundary.

## 2. Coordination Truth

Current release state:

- `3.1`, `3.2`, `3.3`, `3.4`, and `3.5` are closed.
- `3.6 External Customer Evidence` remains open.
- `3.7 Public Surface Discipline` remains open and is assigned to a separate
  ClaudeCode lane.
- `release-readiness-backlog.md` section `3.6` requires one external
  deployment record with:
  - host class
  - workload class
  - frozen pass/fail verdict
  - one tracked external blocker or one frozen external success

This lane may run in parallel with 3.7A because it owns external evidence,
while 3.7A owns public-surface freeze.

## 3. Required Read Order

Read before running or editing:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
5. `owlmlx/customer_runtime_evidence.py`
6. `scripts/runtime_customer_runtime_evidence.py`
7. `tests/test_customer_runtime_evidence.py`
8. `docs/source-of-truth/repository-boundaries.md`
9. `docs/source-of-truth/runtime-status-schema.md`
10. `docs/source-of-truth/comparative-evidence-harness-contract.md`

If you use an external consumer such as OwlCoda, OwlCC, OwlOps, or another
deployment, inspect and run it only as needed. Do not edit external repos.

## 4. What Counts As External

Acceptable external-deployment evidence:

- a real product or operator consumer outside the `owlmlx` repo invoking
  `owlmlx` runtime HTTP routes or inference routes
- a deployed external shell / CLI / service configured to use `owlmlx` as its
  runtime
- a remote or local environment that is not merely an `owlmlx` unit test or
  `owlmlx` internal script

Not acceptable:

- only `scripts/runtime_comparative_evidence.py`
- only `scripts/runtime_customer_runtime_evidence.py`
- only `pytest`
- only internal Gemma/Kimi evidence
- a simulated external record with no real external command / process / HTTP
  call

If no qualifying external deployment is available, do not fake it. Record
`external_deployment_owner_missing` or the exact blocker.

## 5. Evidence Record Shape

Append a narrow section or row to
`docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md` (or create
a clearly referenced successor ledger only if the existing doc is structurally
unusable).

The record must include:

- `record_id`
- `recorded_at`
- `deployment_owner_or_boundary`
- `repo_or_host_boundary`
- `host_class`
- `workload_class`
- `runtime_surface_used`
- `command_or_request`
- `verdict`: exactly one of `pass`, `fail`, `blocked`
- `external_blocker_or_success`
- `evidence_pointer`
- `not_release_claim`

Use `blocked` if the external deployment cannot honestly run yet. A blocked
external deployment can be useful evidence, but it does not close floor `3.6`
unless the backlog requirement is interpreted and reviewed as satisfied by a
tracked external blocker. Do not self-flip the release ledger in this lane.

## 6. Live Run Preference

Prefer one of these, in order:

1. a real OwlCoda / OwlCC / OwlOps consumer already configured for `owlmlx`
2. a minimal external CLI/service outside this repo that calls
   `owlmlx /v1/messages`, `/v1/chat/completions`, `/v1/runtime/status`, or
   another supported runtime route
3. a documented blocked attempt proving that no external deployment owner or
   runnable consumer exists yet

Use Computer Use when live terminal / process / port monitoring adds evidence.

## 7. Required Verification

Run at minimum:

```bash
pytest -q tests/test_customer_runtime_evidence.py
python3 scripts/runtime_customer_runtime_evidence.py --help
python3 -m py_compile owlmlx/customer_runtime_evidence.py scripts/runtime_customer_runtime_evidence.py
git diff --check
```

Also run the selected external deployment command or HTTP request and capture:

- command
- stdout/stderr or HTTP response
- exit status / HTTP status
- host class
- cleanup evidence if any process or port was started

If any command is impossible to run, record the exact reason.

## 8. Allowed Edits

Allowed:

- `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
- a new narrow evidence directory under
  `files/evidence/owlmlx/external-customer-evidence/<UTCSTAMP>/`
- `docs/source-of-truth/release-readiness-execution-plan.md` only to record
  the 3.6A result
- one handoff:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-6A-external-customer-evidence-minimum-record-handoff.md`

Do not edit:

- `docs/source-of-truth/release-readiness-backlog.md`
- floor `3.7` files
- OwlOps / OwlCoda / OwlCC / `/Users/yeemio/AI/Agent` source files
- unrelated runtime implementation

If instrumentation is missing inside `owlmlx`, stop with `needs_fix` and name
the exact next code-lane prompt.

## 9. Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_6A_external_customer_evidence_pass_candidate`
- `owlmlx_release_floor_3_6A_external_customer_evidence_blocker_recorded`
- `owlmlx_release_floor_3_6A_external_deployment_owner_missing`
- `owlmlx_release_floor_3_6A_customer_evidence_needs_fix`

## 10. Required Handoff

Create:

`files/execution-prompts/owlmlx/owlmlx-release-floor-3-6A-external-customer-evidence-minimum-record-handoff.md`

It must include:

- outcome label
- deployment boundary
- host class
- workload class
- command / HTTP request
- verdict
- external blocker or success
- evidence pointer
- files changed
- commands run and results
- whether floor `3.6` is closeout-recommended
- exact next prompt if not closeout-recommended
- confirmation that no release / parity / replacement / production-grade claim
  was made

## 11. Hard Rules

- Do not fake an external deployment.
- Do not count internal-only owlmlx tests or scripts as external evidence.
- Do not edit external repositories.
- Do not flip `release-readiness-backlog.md` in this lane.
- Do not start floor `3.7`.
- Preserve unrelated dirty/staged work.
