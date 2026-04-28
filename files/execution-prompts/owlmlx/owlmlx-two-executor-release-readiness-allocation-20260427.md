# owlmlx Two-Executor Release-Readiness Allocation

> Date: 2026-04-27
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Coordinator intent: use two available execution styles without creating
> overlapping ownership or false closure

## Allocation Summary

Two executors are assigned because the work now has two different shapes:

- one code/review-heavy ledger gate
- one live same-host evidence lane that benefits from screen / terminal /
  process monitoring

They must not edit the same truth row.

## Executor A: ClaudeCode

Prompt:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4B-termination-recovery-policy-closeout-review.md`

Why ClaudeCode:

- strong at codebase-wide review, line-level verification, and doc/test
  consistency
- the task is not visual; it is a disciplined ledger decision

Owned result:

- decide whether release floor `3.4 Recovery Policy Closure` can move from
  `open` to `closed (via runtime-owned termination recovery policy)`
- if closed, update `release-readiness-backlog.md` and
  `release-readiness-execution-plan.md`
- if not closed, return the exact blocker and smallest follow-up prompt

Hard boundary:

- no runtime implementation unless a blocking defect forces `needs_fix`
- no floor `3.5` implementation
- no OwlOps / OwlCoda / `/Users/yeemio/AI/Agent`

## Executor B: Codex Desktop + Computer Use

Prompt:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-5A0-codex-live-comparative-evidence-preflight.md`

Why Codex:

- can use Computer Use to watch live terminal/process/port behavior
- better suited for long-running local evidence checks, process cleanup, and
  screen-observed failures

Owned result:

- determine whether this host can produce the first honest same-host measured
  `comparative_evidence_record`
- check `omlx` / `vmlx` availability from real commands/imports, not docs
- attempt the smallest honest `single_prompt_short` comparative run if all
  prerequisites exist
- if measured evidence cannot be produced, freeze the exact blocker:
  reference runtime unavailable, missing weights, missing runner, or
  inconclusive live state

Hard boundary:

- prefer no code edits
- do not edit `release-readiness-backlog.md`
- do not edit `3.4` closeout docs
- do not fake `verdict_grade = "measured"`
- no OwlOps / OwlCoda / `/Users/yeemio/AI/Agent`

## Coordination Rule

Parallel execution is allowed only because ownership is disjoint:

- Executor A owns the `3.4` ledger decision.
- Executor B owns `3.5` live preflight and evidence discovery.

The next coordinator decision after both handoffs:

- if A closes `3.4` and B emits a measured record, review whether floor `3.5`
  can enter formal closeout
- if A closes `3.4` and B finds `harness_runner_missing`, assign a
  ClaudeCode implementation lane for measured-record runner support
- if A closes `3.4` and B finds `reference_runtime_unavailable` or
  `blocked_missing_weights`, decide whether to install/configure the reference
  runtime or freeze the blocker
- if A does not close `3.4`, keep release ledger at `3 / 7` and fix the 3.4
  blocker before any 3.5 ledger movement

## Non-Goals

- no release-ready claim
- no parity / replacement claim
- no third executor
- no broad refactor
- no public-surface work until 3.5 and 3.6 are no longer dominant blockers
