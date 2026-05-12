# Stage 3.2 Track A — owlmlx Independence Cleanup

## Role

You are the Track A executor for `owlmlx`.

Your job is to correct the architecture narrative after Stage 1 -> Stage 3.1:
`owlmlx` is an independent runtime. `oMLX`, `vMLX`, and Agent-side oMLX patch
tooling are references or legacy external context only. They are not migration
targets, identity sources, or dependencies to retire inside `owlmlx`.

This is a documentation / coordination track. Do not change runtime code.

## Starting Point

Repository:

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
```

Start from:

```bash
git switch refactor/runtime-spine-stage-1-to-3.1
git switch -c refactor/stage-3.2-independence-cleanup
```

Before editing, read:

- `AGENTS.md`
- `docs/handoff/runtime-spine-stage-1-to-3-1-closeout-handoff-20260512.md`
- `docs/source-of-truth/system-architecture.md`
- `docs/source-of-truth/contract-mapping.md`
- `docs/source-of-truth/extraction-inventory.md`
- `docs/source-of-truth/runtime-capability-matrix.md`

## Goal

Freeze the post-Stage-3.1 architecture boundary:

```text
owlmlx is an independent MLX runtime.
Agent-side oMLX patch tooling is external legacy reference only.
Stage 3.2 is not a patch-tooling migration.
```

The output should make it impossible for the next executor to interpret
`/Users/yeemio/AI/Agent/runtime_patches/omlx/` as an owlmlx migration target.

## Write Scope

Allowed files:

- `docs/source-of-truth/system-architecture.md`
- `docs/source-of-truth/contract-mapping.md`
- `docs/source-of-truth/extraction-inventory.md`
- `docs/source-of-truth/runtime-capability-matrix.md` only if wording needs a
  non-promotional clarification
- `docs/handoff/runtime-spine-stage-1-to-3-1-closeout-handoff-20260512.md`
- optional new checkpoint under `files/execution-prompts/owlmlx/`

Optional:

- Update PR #1 body with `gh pr edit` to replace any "swap-safe migration"
  wording with "external legacy reference / independence cleanup".

Forbidden files:

- Any `owlmlx/*.py`
- Any `owlmlx/runtime/*.py`
- Any tests
- Anything under `/Users/yeemio/AI/Agent`
- `files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl`

## Required Edits

1. In `contract-mapping.md`, reclassify the row currently describing
   `oMLX swap-safe patch scripts`.

   Desired category:

   ```text
   external legacy reference
   ```

   Desired meaning:

   - The runtime ideas are already owlmlx-owned where applicable.
   - The Agent-side patch scripts are not to be migrated.
   - They may remain useful as historical comparison material only.

2. In `extraction-inventory.md`, update every
   `/Users/yeemio/AI/Agent/runtime_patches/omlx/swap-safe/...` row.

   Replace `borrow and internalize` with `external legacy reference`.

   The reason must explicitly say:

   ```text
   not an owlmlx extraction target
   ```

3. In `system-architecture.md`, add or update an architecture diagram that
   makes these relationships clear:

   - OwlOps consumes `owlmlx` runtime truth.
   - Product shell may proxy or call `owlmlx`.
   - `owlmlx` owns runtime truth, serving, memory governance, cache/residency,
     model truth, and execution backends.
   - MLX / mlx-lm / mlx-vlm are substrate.
   - oMLX / vMLX / vLLM / SGLang are external references only.
   - Agent oMLX patch tooling is external legacy reference only.

4. In the handoff, replace any wording that implies Stage 3.2 should audit or
   migrate the Agent oMLX patch tooling. The next gap should become:

   ```text
   Stage 3.2 — independence cleanup and owned capability target selection
   ```

5. If you update PR #1 body, record the exact updated URL in the final report.

## Hard Rules

- Do not edit runtime code.
- Do not edit tests.
- Do not inspect or modify Agent-side patch files beyond string references
  already present in `owlmlx` docs.
- Do not claim a new runtime capability.
- Do not promote any capability label.
- Do not remove reference-runtime comparison language; oMLX/vMLX remain valid
  benchmarks and mechanism references.
- Do not say "oMLX patch retired" or "patch-guard obsolete". That is outside
  owlmlx's ownership.

## Verification

Run:

```bash
git diff --check
rg -n "runtime_patches/omlx|swap-safe|patch-guard|borrow and internalize|migration candidate" docs/source-of-truth docs/handoff files/execution-prompts/owlmlx | sed -n '1,200p'
```

The grep may still show references, but every remaining reference must be one
of:

- `external legacy reference`
- historical reference
- explicit "not an owlmlx extraction target"

Do not run heavy model tests. This is a docs-only track.

## Deliverables

- One or more documentation commits.
- A short final report containing:
  - files changed
  - exact wording changes for the oMLX patch rows
  - verification commands and results
  - whether PR #1 body was updated
  - confirmation that no runtime code was touched

## Final Status Wording

Use this verdict if successful:

```text
stage_3_2_independence_cleanup_ready_for_merge
```

Do not use:

```text
swap_safe_migration_complete
patch_guard_retired
omlx_dependency_removed
```
