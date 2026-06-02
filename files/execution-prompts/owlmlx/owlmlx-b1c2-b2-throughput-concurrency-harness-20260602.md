# OwlMLX Round: B-1c §2 Throughput / Cache-Breadth Harness

> Created: 2026-06-02
> Goal: `owlmlx-runtime-acceleration-substrate-b1c2-b2`
> Target duration: 2-3 hours

## Mission

Make the existing B-1c section-2 runner capable of measuring and judging the
two missing axes: throughput decay and cache-breadth/concurrency pressure. This
round does not run a long native soak and does not promote any capability.

## Must Read

1. `AGENTS.md`
2. `files/goals/owlmlx/runtime-acceleration-substrate-goal-contract.md`
3. `files/goals/owlmlx/mainstream-prefix-cache-compatibility-closure-goal-contract.md`
4. `docs/architect/design/B-1c-section-2-spec.md`
5. `docs/architect/design/B-2-mainstream-prefix-cache-compatibility-spec.md`
6. `scripts/bench/eviction_soak.py`
7. `tests/test_eviction_soak_bench.py`

## Hard Rules

- Keep session KV and no-header automatic prefix cache `experimental`.
- Do not claim B-1c §2 pass unless all four axes pass.
- If throughput or breadth thresholds are not configured, the axis may be
  measured but must remain `blocked`.
- Do not create new banned spec-as-code modules.
- Leave unrelated dirty files untouched.

## Wave Plan

### Wave 1: Goal Freeze

Confirm the active goal, current B-1c/B-2 truth, and dominant missing axes.

Acceptance: goal contract and this prompt are archived under project-local
paths.

### Wave 2: Runner Instrumentation

Extend `scripts/bench/eviction_soak.py` so B-1c §2 generation records include
per-sample generation duration, token counts, and throughput when available.

Acceptance: ledger rows contain a `performance` block for warmup/measurement
records.

### Wave 3: Breadth Driver

Add a controlled way to increase session/prompt entry breadth without changing
the canonical three prompt families.

Acceptance: the rollup reports both canonical family balance and distinct
entry breadth.

### Wave 4: Axis Verdicts

Make throughput/concurrency verdicts data-driven:

- throughput can pass only when enough samples exist and an explicit decay
  threshold is supplied;
- cache-breadth/concurrency can pass only when enough distinct entries are
  observed and the explicit breadth floor is supplied;
- otherwise the axis remains `blocked` with a precise reason.

Acceptance: rollup records observed values, configured thresholds, and reason
codes.

### Wave 5: Verification

Add focused tests for the new measurable axes and run the narrow test set.

Acceptance: `uv run pytest tests/test_eviction_soak_bench.py -q` passes or any
blocker is recorded precisely.

## Required Final Report

- Modified files
- Wave-by-wave outcomes
- New/updated APIs or CLI flags
- Tests run
- Capability-label status
- Remaining blocker before real native B-1c §2 evidence
