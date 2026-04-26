# owlmlx Delivery Discipline

> Status: frozen
> Updated: 2026-04-16

## 1. Why This Exists

`owlmlx` is now deep enough into Phase 45 that active runtime truth must be
frozen in repository materials, not only described in chat.

This matters most when coordinator choices depend on:

- the active dominant gap
- the active seam
- the active checkpoint
- the active authorized round

## 2. Hard Rules

### 2.1 Active Runtime Truth Must Be Versioned

If a file changes any of the following, it must be tracked in version control:

- active dominant gap truth
- active seam truth
- active checkpoint
- active authorized prompt
- active customer evidence / replacement-gap sync
- active implementation or tests required by the current verdict

Current runtime truth cannot live only in chat.

### 2.2 One Round Is Only Deliverable When Four Things Match

A round only counts as deliverable when these four line up:

- implementation or truth files changed
- tests or live/runtime checks ran
- an honest verdict is stated
- deferred / blocked scope is stated

If one is missing, the result is in-flight, not closed.

### 2.3 Untracked Files Cannot Carry the Active Seam

The following must not remain `??` if they are part of the current mainline:

- active seam truth
- active checkpoint
- active authorized prompt
- newly added runtime surfaces used by the verdict
- newly added tests used by the verdict

If an untracked file remains, closeout must explain why it is not required by
the active path.

### 2.4 Scope Must Freeze Before Widening

Correct order:

1. freeze the exact seam / blocker / invariant boundary
2. implement inside that boundary
3. verify with tests and live/runtime evidence
4. sync higher-level truth
5. close out

Runtime widening is not allowed to outrun the frozen seam contract.

## 3. Allowed Exceptions

The following may remain outside version control temporarily if they are not
active-path dependencies:

- scratch notes
- transient logs
- exploratory helper outputs
- historical prompt drafts
- non-authoritative helper material

These cannot carry the active verdict.

## 4. Dirty Worktree Rule

A dirty worktree is tolerated.

What is not tolerated is active-phase truth drifting inside that dirty
worktree.

Older unrelated modifications may remain.
Current seam, checkpoint, prompt, implementation, and tests may not float.

## 5. Required Closeout Packet

Every accepted round should report:

- `Modified files`
- `Tests run / live/runtime checks`
- `Current honest verdict`
- `What remains deferred / blocked`
- exact live/runtime truth when the round depends on it
- whether active-path truth / prompt files are now tracked

## 6. Repository-Specific Application

For `owlmlx`, versioning discipline applies most strongly to:

- `docs/source-of-truth/*` for the current dominant gap
- `files/execution-prompts/owlmlx/*` for the active checkpoint or authorized round
- `owlmlx/*` runtime surfaces that changed the active verdict
- `tests/*` that prove seam truth or higher-level evidence carriage
- `replacement-grade-stability-gaps.md`
- `phase45-customer-runtime-evidence-ledger.md`
- `phase45-dominant-gap-reselection.md`

## 7. Enforcement Standard

A delivery should be rejected when any of the following is true:

- the verdict depends on untracked truth or prompt files
- the active seam changed but higher-level truth did not sync
- tests or live/runtime evidence are missing for a claimed seam shift
- scope widened beyond the frozen dependency boundary

The purpose of this discipline is not cosmetic cleanliness.
It is to keep Phase 45 coordinator decisions grounded in repository truth.
