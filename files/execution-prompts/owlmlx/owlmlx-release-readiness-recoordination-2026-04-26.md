# owlmlx Release-Readiness Recoordination

> Date: 2026-04-26
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Role: coordinator freeze and next-round selection
> Scope: release-readiness floors only; no runtime implementation in this
> packet

## 1. Current Verified Position

Current release ledger truth remains:

- closed: `3.1 Cache Scheduler Closure`
- closed: `3.3 Model Residency Non-Resident Path`
- open: `3.2 Memory-Pressure Decision Closure`
- open: `3.4 Recovery Policy Closure`
- open: `3.5 Comparative Evidence`
- open: `3.6 External Customer Evidence`
- open: `3.7 Public Surface Discipline`

That is still `2 / 7` release-floor items closed.

The current active floor is still `3.2`, not `3.4`.

## 2. What Changed Since The Last Coordinator Packet

Floor `3.2` has progressed:

- A produced
  `owlmlx_release_floor_3_2A_memory_pressure_eviction_candidate_closed_pending_review`
  with `owlmlx.memory_pressure_eviction_policy`, a decision endpoint, an
  execution endpoint, tests, and docs.
- B produced
  `owlmlx_release_floor_3_2B_review_pass_closed_recommended`.
- B also disclosed it was a self-audit by the same Opus executor that authored
  A. Therefore B is useful evidence, not an independent closure gate.

No `3.2C` handoff was found in the worktree during this recoordination pass.
`release-readiness-backlog.md` section 5 still shows `3.2` as `open`.

Floor `3.4` has also been pre-read:

- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-4-pre-flight-notes.md`
  exists as read-only pre-flight notes.
- It confirms that `restart_exhausted_models` is real but
  session-death-specific, not a general load-failure signal.
- It confirms the parked failed-unload/reclaim prompt is a sub-component of
  `3.4`, not a competing lane.

Those notes do not authorize `3.4` implementation while `3.2` is still open.

## 3. Next Active Round

Run exactly one active executor round:

- executor: `gpt-5.4`
- prompt:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-2C-independent-closure-review-and-ledger-decision.md`

Do not assign a second executor in parallel. Do not start `3.4` in parallel.
This is a single-executor closure-review round.

The `3.2C` reviewer must:

- independently rerun the focused 3.2 tests
- check the decision surface, execution path, after-state atomicity, and
  repeated-pressure evidence
- resolve the B self-audit caveat
- move `release-readiness-backlog.md` section 5 only if closure is genuinely
  confirmed

If `3.2C` returns `needs_fix`, do not start `3.4`; assign a narrow `3.2D` fix
round against the exact blocker.

If `3.2C` returns `closed`, update the active floor to `3.4 Recovery Policy
Closure`.

## 4. Provisional 3.4 Sequencing Decision

Once `3.2` is actually closed, the coordinator should issue only one next
prompt, not a pre-split A/B package.

Preferred next prompt:

- `3.4A0`: failed-unload/reclaim barrier event sub-round, using the parked
  prompt as the seed

This selects the pre-flight notes' Option B.

Reason:

- it avoids a too-large first 3.4 round that combines operation-boundary event recording
  with policy closure
- it keeps the release ledger honest: event surface progress is not yet full
  `3.4` closure
- it keeps execution allocation simple: one executor per round, then
  re-coordinate from the result

## 5. Parked / Not Active

Do not run these until the active floor permits it:

- `3.4` implementation before `3.2C` completes
- `3.5` comparative evidence closure before the current scheduling/recovery
  floors stop blocking release-readiness truth
- any `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent` work from this
  `owlmlx` coordinator lane

## 6. Coordinator Verdict

`owlmlx_release_readiness_recoordination_active_floor_3_2C`

The next real work is not another broad planning round. It is:

1. execute `3.2C` with the single assigned executor `gpt-5.4`
2. if closed, flip `3.2` ledger and then issue one new prompt for `3.4A0`
3. if not closed, issue one narrow `3.2D` fix prompt for the exact blocker
