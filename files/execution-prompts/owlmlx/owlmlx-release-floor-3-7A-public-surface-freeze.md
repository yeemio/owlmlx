# owlmlx Execution Prompt 3.7A: Public Surface Freeze

> Date: 2026-04-28
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Active release floor: `3.7 Public Surface Discipline`
> Assigned executor: ClaudeCode
> Role: public-surface source-of-truth, validation test, and closeout
> recommendation
> Scope: freeze supported/internal surface boundary; no external deployment work

## 1. Mission

Freeze the public technical-preview surface for `owlmlx`.

The required question is:

**Exactly which modules, contracts, HTTP routes, and CLIs are part of the
supported public surface, and which surfaces remain internal?**

This is a boundary document, not marketing. It must reference existing
source-of-truth docs and avoid duplicating their full content.

## 2. Coordination Truth

Current release state:

- `3.1`, `3.2`, `3.3`, `3.4`, and `3.5` are closed.
- `3.6 External Customer Evidence` remains open and is assigned to a separate
  Codex live evidence lane.
- `3.7 Public Surface Discipline` remains open.
- `release-readiness-backlog.md` section `3.7` requires:
  - one frozen `public-surface.md` or equivalent
  - exactly named supported modules, contracts, and CLIs
  - everything not listed is internal and may change without notice
  - references to existing source-of-truth documents instead of duplication

This lane may run in parallel with 3.6A because it owns public-surface truth,
not external deployment evidence.

## 3. Required Read Order

Read before editing:

1. `AGENTS.md`
2. `docs/source-of-truth/release-readiness-backlog.md`
3. `docs/source-of-truth/release-readiness-execution-plan.md`
4. `docs/source-of-truth/master-outline.md`
5. `docs/source-of-truth/product-definition.md`
6. `docs/source-of-truth/repository-boundaries.md`
7. `docs/source-of-truth/runtime-capability-matrix.md`
8. `docs/source-of-truth/runtime-contracts.md`
9. `docs/source-of-truth/runtime-status-schema.md`
10. `docs/source-of-truth/runtime-governance.md`
11. `docs/source-of-truth/hazardous-operations.md`
12. `docs/source-of-truth/comparative-evidence-harness-contract.md`
13. `docs/source-of-truth/release-readiness-backlog.md`

Inspect code only as needed to verify route / script names.

## 4. Required Output

Create:

`docs/source-of-truth/public-surface.md`

It must include:

- status and date
- purpose
- support label vocabulary:
  `supported`, `partial`, `experimental`, `internal`, `not in scope`
- supported HTTP routes
- supported runtime modules / Python APIs
- supported operator scripts / CLIs
- supported source-of-truth contracts
- public consumer rules
- internal-only surfaces
- explicitly unsupported claims:
  release-ready, parity, replacement, production-grade, superiority
- versioning / change rule
- restart condition

Keep it concise. Link to existing docs; do not paste their content.

## 5. Validation Test

Add a narrow validation test, suggested:

`tests/test_public_surface_contract.py`

The test should verify at least:

- `docs/source-of-truth/public-surface.md` exists
- every referenced local doc path exists
- every listed script path exists
- public surface text includes the internal-default rule
- public surface text rejects release/parity/replacement wording as current
  claims
- no banned claim appears as an allowed current claim

Do not overbuild a parser. A compact text/path validation test is enough.

## 6. Required Documentation Updates

Update:

- `docs/source-of-truth/master-outline.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`

Do **not** flip `docs/source-of-truth/release-readiness-backlog.md` in this
lane unless the prompt's deliverables, validation test, honest verdict, and
deferred scope are all complete and there is no conflict with parallel 3.6A.
Preferred output is `closed_recommended_pending_closeout`, with backlog flip
left to coordinator closeout.

## 7. Required Verification

Run at minimum:

```bash
pytest -q tests/test_public_surface_contract.py
python3 -m py_compile owlmlx/runtime/server.py
git diff --check
```

If you add no Python code beyond the test, do not invent broader runtime test
requirements. The release floor is about public surface truth.

## 8. Outcome Labels

Use exactly one:

- `owlmlx_release_floor_3_7A_public_surface_closed_recommended`
- `owlmlx_release_floor_3_7A_public_surface_needs_fix`
- `owlmlx_release_floor_3_7A_public_surface_still_blocked`

## 9. Required Handoff

Create:

`files/execution-prompts/owlmlx/owlmlx-release-floor-3-7A-public-surface-freeze-handoff.md`

It must include:

- outcome label
- changed files
- supported public surface summary
- internal-only rule summary
- tests run and results
- whether floor `3.7` is closeout-recommended
- exact blocker if not closeout-recommended
- confirmation that no release / parity / replacement / production-grade claim
  was made

## 10. Hard Rules

- Do not use public-surface freeze to claim release readiness while `3.6`
  remains open.
- Do not expose internal phase45 exactness docs as supported public API.
- Do not duplicate source-of-truth content; reference it.
- Do not edit external repos.
- Do not start floor `3.6`.
- Preserve unrelated dirty/staged work.
