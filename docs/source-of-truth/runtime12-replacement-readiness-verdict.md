# Runtime-12 Replacement Readiness Verdict

> Status: Runtime-12 complete
> Updated: 2026-04-12
>
> **⚠️ Re-baselined 2026-06-03 — see [`runtime13-replacement-rebaseline-verdict.md`](runtime13-replacement-rebaseline-verdict.md).** 本文档的 blocker 分类为 2026-04 point-in-time；最新分类与每条 "是否阻断 owlmlx-only cutover" 判定以 Runtime-13 为准。本文档正文未改写。

## 1. Goal

Runtime-12 closes the last ambiguity in the replacement-grade loop:

- not by forcing a premature `replaceable` claim
- but by making the replacement verdict explicit, machine-visible, and tied to
  a concrete blocker list

Before Runtime-12, `owlmlx` and `owlcoda` had already accumulated the technical
proofs from Runtime-9 through Runtime-11. What was still missing was a
control-plane surface that could answer:

- are we replaceable yet?
- if not, why not?

Runtime-12 makes that answer explicit.

## 2. What Changed

### 2.1 Replacement readiness is now a first-class doctor output

`owlcoda` now computes a dedicated replacement-readiness verdict during
`doctor`.

New surface:

- verdict
- blocker list

This sits alongside launch readiness rather than replacing it.

That distinction matters:

- launch readiness answers: can this environment start and run?
- replacement readiness answers: can this stack replace the old platform yet?

Those are not the same question.

### 2.2 Replacement blockers are now frozen as explicit control-plane truth

Runtime-12 does not pretend that a single successful environment probe can
prove production replacement.

Instead it freezes the remaining blockers honestly:

1. full source-first parity is not yet frozen across all interaction shapes
2. full production control-plane closure is not yet frozen
3. production backend quality parity is not yet proven
4. operations-level replacement of the old platform is not yet verified

This turns the replacement verdict from a narrative statement into an explicit
operator-visible assessment.

## 3. Verification

### 3.1 Focused regression tests

Verified:

- `owlcoda`: `npm test -- tests/doctor.test.ts tests/runtime-probe.test.ts tests/model-registry.test.ts`
  - result: `54 passed`

These tests prove:

- `doctor` now emits a replacement verdict
- `doctor` now emits a blocker list
- prior runtime-probe and routing guarantees remain intact

### 3.2 Build verification

Verified:

- `owlcoda`: `npm run build`
  - result: success

## 4. Runtime-12 Verdict

### 4.1 Replacement readiness surface

**Verdict: complete**

The replacement decision is now surfaced as an explicit control-plane truth,
not only as a document conclusion.

### 4.2 Old platform replacement

**Verdict: still not yet replaceable**

Runtime-12 does not change that answer. It makes the answer operationally
visible and auditable.

This is the correct final closure for the current stage.

## 5. What Runtime-12 Proves

- replacement readiness is now an explicit operator-visible verdict
- blocker reasons are no longer implicit or scattered across multiple runtime
  stages
- the system can now distinguish:
  - launchable
  - operable
  - replaceable

## 6. Final Replacement-Grade Closure State

At the end of Runtime-12:

- degraded routing ambiguity: closed
- source-first cutover: proven
- source-first tool loop: proven
- direct OwlCoda cutover: proven
- control-plane operability: proven
- replacement verdict: explicit
- old platform replacement: not yet

## 7. Next Gap

Any Runtime-13 work should be treated as post-closure work, not another attempt
to reopen replacement-grade ambiguity.

If the team wants to move beyond Runtime-12, the next step is not another seam
proof. It is one of:

- actual production replacement work
- remaining parity implementation work
- explicit decision to keep the old platform in place longer
