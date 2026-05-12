# Runtime Spine Stage 1 To 3.1 Closeout Handoff — 2026-05-12

## Purpose

This handoff freezes the local `owlmlx` runtime-spine refactor milestone after
Stage 1, Stage 2, Stage 2.1, and Stage 3.1.

The milestone goal is to preserve the work as a reviewable branch before any
cross-repository Stage 3.2 work begins.

## Current Verified Truth

- Repository: `/Users/yeemio/AI/gitrep/owlmlx`
- Milestone branch: `refactor/runtime-spine-stage-1-to-3.1`
- Base remote: `origin/main` at `d27269f1`
- Runtime-spine HEAD before this handoff file: `e2bf9eda`
- Local delta at closeout: 42 commits ahead of `origin/main` before this
  handoff commit.
- Scope size before this handoff commit: 461 files changed,
  19034 insertions, 9272 deletions.
- Stage 1 archived the spec-as-code layer and added the AGENTS anti-regression
  rule.
- Stage 2 added the PR #649-shaped vocabulary: `MemoryWatermark`,
  `WatermarkAction`, `pre_load_check`, and `settle_barrier_event`.
- Stage 2.1 closed the two merge gates:
  - 35 broken root `scripts/runtime_*.py` entries were moved under archive.
  - `MemoryWatermark` entered real runtime consumer paths.
- Stage 3.1 completed the first true contract migration:
  `Quantization metadata truth` moved from `owned but still shell-hosted` to
  `owned now` through `owlmlx/quantization_metadata.py` and
  `GET /v1/runtime/quantization-metadata`.
- Latest full regression on the runtime-enabled local checkout:
  `991 passed, 3 skipped, 4 warnings`.
- Clean-worktree default validation initially caught an optional-runtime-extra
  leak in `tests/test_mlx_lm_runner_params.py`; the milestone includes the fix
  so default tests do not require `mlx_lm` just to validate sampler parameter
  conversion.
- Clean-worktree default validation after the fix:
  `988 passed, 6 skipped, 1 warning`.
- Clean-worktree server smoke requires the `runtime` optional dependency set;
  verified with `uv run --extra runtime ...` against temporary port `8078`.
- Latest whitespace check: `git diff --check` clean.
- Root archived-script residual check:
  `git ls-files 'scripts/runtime_cache_pre_claim_*.py' 'scripts/runtime_cache_stream_*.py' 'scripts/runtime_*exactness*.py'`
  returns `0`.

## What Not To Reopen

- Do not reopen Stage 1 archive decisions unless a live runtime consumer is
  missing because of the archive.
- Do not recreate module-as-spec Python files. New package modules still need
  a real `owlmlx/runtime/` consumer or a documented exception.
- Do not batch-rename remaining `reclaim_barrier_event` internal names. Stage 2
  intentionally preserved route URLs, kernel internals, compound payload fields,
  and test-facing method names where compatibility mattered.
- Do not start Stage 3.2 as a drive-by continuation. It crosses into
  `/Users/yeemio/AI/Agent/runtime_patches/omlx/` and needs its own audit.
- Do not stage `files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl`
  as part of this milestone. It is runtime-generated local evidence.

## Current Runtime / Deployment

Observed during closeout:

- `127.0.0.1:8066` was listening.
- `/healthz` returned `ok=true`, `readiness=ready`,
  `active_model_id=Qwen3.6-27B-4bit`, `model_count=1`.
- The running server was not restarted or modified during this handoff.

The Stage 3.1 smoke used a temporary `8077` server and stopped it after
verification.

## Important Files

- `AGENTS.md` — Stage 1 anti-regression rule.
- `archive/MANIFEST.md` — archive rationale and final accounting.
- `docs/source-of-truth/runtime-capability-matrix.md` — post-Stage 3.1
  capability state.
- `docs/source-of-truth/contract-mapping.md` — remaining migration candidates.
- `docs/source-of-truth/extraction-inventory.md` — Wave A/B/C extraction state.
- `owlmlx/memory_watermark.py` — public watermark vocabulary with runtime
  consumers.
- `owlmlx/quantization_metadata.py` — first Stage 3 true migrated contract.
- `owlmlx/runtime/server.py` — HTTP surfaces for memory watermark and
  quantization metadata.
- `scripts/bench/eviction_soak.py` — Stage 4 placeholder, intentionally exits
  `2`.

## Known Gaps

- `origin/main` has not been advanced in this closeout. The branch should be
  reviewed or pushed as a milestone before any mainline remote update.
- `files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl` remains
  dirty and should stay out of this milestone unless explicitly curated.
- `GET /v1/runtime/quantization-metadata?model_id=Qwen3.6-27B` can return
  `lineage_missing` when lineage is absent. That is an honest contract state,
  not a failure.
- Stage 3.2 swap-safe patch migration is not started.
- Public release remains a separate operator decision; this refactor milestone
  does not imply public release.

## Next Dominant Gap

Milestone handling gap:

1. Push `refactor/runtime-spine-stage-1-to-3.1` to `origin`.
2. Validate from a clean checkout or worktree.
3. Decide whether remote `main` should fast-forward with full commit history,
   be represented by a curated PR, or remain parked while Stage 3.2 is audited.

Runtime migration gap after this milestone:

`Stage 3.2 — swap-safe patch tooling migration audit`

This must begin with a read-only audit of
`/Users/yeemio/AI/Agent/runtime_patches/omlx/`, current consumers, and
retirement criteria for `patch-guard.sh`.

## Suggested First Commands

```bash
cd /Users/yeemio/AI/gitrep/owlmlx
git status --short --branch
git log --oneline origin/main..HEAD | sed -n '1,40p'
uv run pytest -q
git diff --check
git ls-files 'scripts/runtime_cache_pre_claim_*.py' 'scripts/runtime_cache_stream_*.py' 'scripts/runtime_*exactness*.py'
```

Optional server smoke:

```bash
mkdir -p /tmp/owlmlx-stage31-smoke
uv run --extra runtime python scripts/runtime_technical_preview_server.py \
  --host 127.0.0.1 \
  --port 8077 \
  --models-root /Users/yeemio/AI/Agent/models \
  --backend-timeout-s 30 \
  --model-release-candidate-ledger-path /tmp/owlmlx-stage31-smoke/model-rc.jsonl \
  --comparative-evidence-ledger-path /tmp/owlmlx-stage31-smoke/comparative.jsonl \
  --runtime-test-run-ledger-path /tmp/owlmlx-stage31-smoke/test-runs.jsonl \
  --runtime-monitor-trend-ledger-path /tmp/owlmlx-stage31-smoke/trends.jsonl \
  --runtime-monitor-sample-interval-s 0 \
  --log-level warning
```

Then in another shell:

```bash
curl -fsS http://127.0.0.1:8077/healthz
curl -fsS http://127.0.0.1:8077/metrics | head -20
curl -fsS http://127.0.0.1:8077/v1/runtime/memory-watermark | python3 -m json.tool
curl -fsS 'http://127.0.0.1:8077/v1/runtime/quantization-metadata?model_id=Qwen3.6-27B' | python3 -m json.tool
```

## Starter Prompt For New Window

```text
We are in /Users/yeemio/AI/gitrep/owlmlx. Continue from the milestone branch
refactor/runtime-spine-stage-1-to-3.1. First read
docs/handoff/runtime-spine-stage-1-to-3-1-closeout-handoff-20260512.md,
AGENTS.md, archive/MANIFEST.md, docs/source-of-truth/contract-mapping.md, and
docs/source-of-truth/extraction-inventory.md.

Do not start Stage 3.2 automatically. Preserve the dirty trend ledger boundary.
Verify the milestone branch with pytest, git diff --check, root script residual
check, and a small server smoke if needed. Then recommend whether to fast-forward
remote main, open a curated PR, or keep the milestone branch parked while Stage
3.2 receives a separate cross-repo audit.
```
