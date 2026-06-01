# F-3.1 Goal Loop Round Summary

> Date: 2026-06-01
> Goal: `owlmlx-f3-resident-mtp-feasibility`

## What Changed

- Created the F-3.1 goal contract:
  `files/goals/owlmlx/f3-resident-mtp-feasibility-goal-contract.md`.
- Archived the next execution prompt:
  `docs/phase-prompts/owlmlx-f3-resident-mtp-feasibility-probe-20260601.md`.
- Updated `docs/architect/design/F-3-resident-mtp-spec.md` because the live
  GitHub state for `mlx-lm #980` is now closed; F-3 is therefore no longer
  described as blocked merely by an open upstream issue. It remains blocked on
  local prerequisite verification.
- Added `blocked_on_local_runtime` as a valid F-3.1 verdict, separating a broken
  local probe environment from an upstream cache defect.
- Created a replacement isolated py311 runtime at
  `/Users/yeemio/AI/gitrep/runtime-probes/mlx-vlm-mtp-probe-py311/.venv` because
  the older Python 3.14 probe venv cannot import MLX under current macOS system
  policy.

## Verified This Round

- `mlx-lm #980` live GitHub issue state: closed.
- Main owlmlx env: `mlx-lm 0.31.3`, no `mlx-vlm` package.
- Old isolated probe env: `mlx-vlm 0.5.0`, `mlx-lm 0.31.3`, `mlx 0.31.2`, but
  `mlx_vlm` import fails with `library load denied by system policy`.
- New py311 isolated probe env: `mlx-vlm 0.5.0`, `mlx-lm 0.31.3`, `mlx 0.31.2`;
  `mlx.core` and `mlx_vlm` import successfully.
- `mlx_vlm generate --help` in the py311 env exposes `--draft-model`,
  `--draft-kind`, `--draft-block-size`, and `--prefill-step-size`.
- Programmatic API exists in the py311 env:
  `mlx_vlm.generate.load`, `mlx_vlm.generate.generate`,
  `mlx_vlm.generate.stream_generate`, and `PromptCacheState`.
- Focused tests still pass:
  `uv run pytest tests/test_gemma4_mtp_drafter.py tests/test_mlx_vlm_mtp_runner.py -q`
  → `12 passed`.

## Current Dominant Gap

`f3-1-real-resident-probe-run`

The local runtime can now import the relevant `mlx-vlm` stack and exposes a
candidate programmatic resident surface. The next round should run the minimal
Gemma4 target + assistant drafter probe only when host state is safe for a
large model load, then emit the F-3.1 JSONL verdict.

## Honest Claim Ceiling

F-3 remains `experimental`. No F-3.2 resident backend, F-3.3 A/B benchmark, or
`assistant_drafter` promotion has started.
