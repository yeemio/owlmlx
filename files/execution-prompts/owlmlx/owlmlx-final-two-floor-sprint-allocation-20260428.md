# owlmlx Final Two-Floor Sprint Allocation

> Date: 2026-04-28
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Coordinator packet: final release-floor sprint after 3.5F closeout

## Current State

`3.5F` closed comparative evidence. Current release-floor position is:

- closed: `3.1`, `3.2`, `3.3`, `3.4`, `3.5`
- open: `3.6 External Customer Evidence`, `3.7 Public Surface Discipline`

No release-ready, parity, replacement, production-grade, or superiority claim
is allowed until both remaining floors close.

## Executor A: Codex Desktop + Computer Use

Prompt:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-6A-external-customer-evidence-minimum-record.md`

Purpose:

- find or run one real external deployment / consumer boundary outside the
  `owlmlx` repo
- record host class, workload class, frozen pass/fail/blocker verdict, and one
  external blocker or success
- write evidence to `phase45-customer-runtime-evidence-ledger.md` or a narrow
  successor evidence path

Boundary:

- no external repo edits
- no fake external customer evidence
- no `release-readiness-backlog.md` flip in this lane

## Executor B: ClaudeCode

Prompt:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-7A-public-surface-freeze.md`

Purpose:

- create `docs/source-of-truth/public-surface.md`
- name exactly supported routes, modules, contracts, scripts, and internal-only
  surfaces
- add a narrow validation test
- recommend closeout if the public surface is complete

Boundary:

- no external deployment work
- no release-ready claim while `3.6` remains open
- preferred: no `release-readiness-backlog.md` flip in this lane; return
  `closed_recommended_pending_closeout`

## Coordination Rule

The two lanes may run in parallel because their write sets are disjoint except
for `release-readiness-execution-plan.md`, where each lane must add only a
narrow result block. If both return closeout-recommended, the coordinator can
run one final closeout / ledger-sync round for `3.6` and `3.7`.

If `3.6A` blocks on missing external deployment ownership, do not let `3.7A`
claim release readiness. Public surface can still become ready for technical
preview, but full release floor remains blocked on `3.6`.
