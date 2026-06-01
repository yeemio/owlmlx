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
- Added the operator probe script:
  `scripts/runtime_gemma4_mtp_resident_probe.py`.
- Added unit coverage for F-3.1 verdict classification and ledger fields:
  `tests/test_runtime_gemma4_mtp_resident_probe.py`.

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
- The committed probe script's API inspection path passes:
  `uv run python scripts/runtime_gemma4_mtp_resident_probe.py inspect-api`
  reports `resident_api_candidate=true` with `mlx-vlm 0.5.0`,
  `mlx-lm 0.31.3`, and `mlx 0.31.2`.
- Focused tests still pass:
  `uv run pytest tests/test_runtime_gemma4_mtp_resident_probe.py tests/test_gemma4_mtp_drafter.py tests/test_mlx_vlm_mtp_runner.py -q`
  → `16 passed`.
- Script compile check passes:
  `uv run python -m py_compile scripts/runtime_gemma4_mtp_resident_probe.py`.
- Host safety check: a B-1c native soak is currently running under
  `eviction_soak.py` with `caffeinate`; the heavy Gemma4 resident probe was
  not run in this round to avoid contaminating active memory evidence.

## Current Dominant Gap

`f3-1-resident-mtp-failed-followup`

The F-3.1 JSONL verdict now exists. The local runtime can load target + drafter
once and serve multiple requests in one resident process, but the first real
probe did not meet the resident-viable gate because request 2+ had no
non-trivial speculative acceptance and the run entered a trim regime. F-3.2
must not start from this evidence.

## Honest Claim Ceiling

F-3 remains `experimental`. No F-3.2 resident backend, F-3.3 A/B benchmark, or
`assistant_drafter` promotion has started.

## Continuation Check: 2026-06-01T08:43Z

- `mlx-lm #980` is still `CLOSED` as of a live `gh issue view` check, with
  `closedAt=2026-04-14T23:24:14Z`. The latest visible issue comment
  (2026-04-17) still reports a similar hybrid prefix-cache failure mode on a
  different model, so F-3 must continue to rely on its own local resident
  verdict rather than treating the closed issue as sufficient evidence.
- Local model artifacts are present:
  - target: `/Users/yeemio/AI/Agent/models/gemma-4-31B-it` (`58G`,
    two safetensor shards);
  - drafter:
    `/Users/yeemio/AI/Agent/model-candidates/mlx-community/gemma-4-31B-it-assistant-bf16`
    (`926M`, single safetensor file).
- The probe script's `inspect-api` path still reports
  `resident_api_candidate=true` in the py311 isolated env.
- Targeted tests still pass:
  `uv run pytest tests/test_runtime_gemma4_mtp_resident_probe.py tests/test_gemma4_mtp_drafter.py tests/test_mlx_vlm_mtp_runner.py -q`
  -> `16 passed`.
- The current B-1c native soak is still active (`eviction_soak.py` plus
  `caffeinate`). Its latest ledger sample at `2026-06-01T08:42Z` shows
  `elapsed_s=3353.233` of a `14400` second segment. The F-3 heavy resident
  probe therefore remains queued behind the host-safety gate.

## F-3.1 Verdict: 2026-06-01T12:44Z

Evidence:
`files/evidence/owlmlx/bench/f3-resident-mtp/20260601T124448Z-f3-1-resident-feasibility.jsonl`

- `verdict=failed`
- `failure_reasons=["non_trivial_speculative_summary_missing_after_first_request"]`
- `capability_label=experimental`
- `used_for_promotion_gate=false`
- `reloads_observed=0`, `requests_served=3`
- target + drafter loaded once: `target_load_count=1`, `draft_load_count=1`
- request speculative summaries:
  - request 0: `mean_accepted_tokens=1.0`, `rounds=4`
  - request 1: `mean_accepted_tokens=0.0`, `rounds=0`
  - request 2: `mean_accepted_tokens=0.0`, `rounds=0`
- `trim_attempted=true`, with 180 observed `KVCache` / `RotatingKVCache`
  `trim` calls
- versions: `mlx-vlm 0.5.0`, `mlx-lm 0.31.3`, `mlx 0.31.2`

Interpretation: F-3.1 produced an evidence-backed verdict, but it is a negative
verdict. The installed local pin does not clear the resident-viable
prerequisite for Gemma4 assistant-drafter MTP. F-3 remains design-ready and
code-grade-blocked; `assistant_drafter` remains `experimental`.
