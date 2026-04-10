# owlmlx Autonomous Loop Discipline

> Status: authoritative
> Updated: 2026-04-10

## 1. Purpose

This document defines how `owlmlx` progresses through self-directed iteration
rounds rather than requiring a human prompt for each step.

The autonomous loop is the mechanism by which `owlmlx` truth becomes
self-growing: gaps are identified, rounds are generated, execution happens,
and the system decides whether to continue or stop.

## 2. Loop Cycle

Each round follows this cycle:

1. **Freeze** — restate goal contract and verified truth
2. **Assess** — list remaining gaps, select the dominant next gap
3. **Select** — generate next round (only fork if result genuinely uncertain)
4. **Generate** — write round prompt, archive to execution-prompts
5. **Execute** — modify docs, code, tests, inventory, contracts
6. **Verify** — produce delivery summary, update honest claims
7. **Decide** — `continue` / `branch` / `blocked` / `success`

Default after each round: **continue autonomously**.

## 3. Gap Selection Priority

When choosing the next dominant gap, use this priority order:

1. Fix false claims or truth drift in existing source-of-truth
2. Close adoption model or boundary ambiguity
3. Turn extraction inventory into executable migration rules
4. Formalize runtime governance and contracts
5. Only then: extend new paths or directories

## 4. Round Constraints

Each round must:

- have exactly one dominant delivery objective
- advance at least one of: boundary hardness, extraction executability,
  contract formality, capability honesty, adoption clarity
- leave reviewable assets (files committed, not just chat completions)
- update the capability matrix if any claim changed
- archive a round prompt to `files/execution-prompts/owlmlx/`

## 5. Fork Rules

Forking into parallel rounds (A/B) is allowed only when the next step
genuinely depends on an uncertain outcome.

Not allowed: forking "to be comprehensive" without a real decision point.

## 6. Stop Rules

### 6.1 Success Stop

Only when the goal contract's success definition is fully satisfied.

### 6.2 Blocked Stop

Only when:

- an irreconcilable conflict exists between truth and evidence
- a decision requires user choice between significantly different directions
- a required resource is unreachable
- current truth is too thin to generate an honest next round

### 6.3 Bad Stop (Prohibited)

- "looks good enough"
- "docs are already extensive"
- "wait for next user prompt"

## 7. Delivery Summary Format

Each round must output:

- goal status (one sentence)
- dominant gap addressed (one sentence)
- decision: `continue | branch | blocked | success`
- modified files
- wave-by-wave outcomes
- new source-of-truth closures
- checks run
- remaining truth gaps
- next dominant gap
- why this round materially advances owlmlx

## 8. Four Standing Questions

Every delivery summary must answer:

1. What new formal boundary did `owlmlx` gain this round?
2. What misleading claim was removed or corrected?
3. What new executable basis does extraction now have?
4. What still separates `owlmlx` from runtime truth closure?

## 9. Commit Discipline

Commit messages must reflect the dominant gap addressed, not generic labels.

Good: `owlmlx: freeze open-source adoption model`
Bad: `owlmlx: update docs`
