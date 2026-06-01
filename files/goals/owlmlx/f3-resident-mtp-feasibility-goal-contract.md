# Goal Contract

## Goal ID

`owlmlx-f3-resident-mtp-feasibility`

## Title

Close the F-3 prerequisite gate for Gemma4 resident MTP by producing an
evidence-backed F-3.1 feasibility verdict.

## Success Definition

- The current `mlx-lm #980` upstream state is verified and reflected honestly in
  the F-3 design spec.
- The local `mlx-lm` / `mlx-vlm` runtime pin is inspected enough to determine
  whether §2.1 route 1 is genuinely available for the Gemma4 resident-MTP lane.
- A minimal F-3.1 feasibility probe is implemented or run, producing a JSONL
  verdict under `files/evidence/owlmlx/bench/f3-resident-mtp/`.
- The verdict is one of the spec-defined outcomes:
  `resident_viable_append_only`, `resident_viable_with_trim`,
  `blocked_on_local_runtime`, `blocked_on_980`, or `failed`.
- If the probe passes, the next dominant gap becomes F-3.2 resident backend
  code-grade. If it does not pass, the blocker is written down precisely and
  F-3 remains design-ready but code-grade-blocked.
- `assistant_drafter` remains `experimental`; this goal does not promote any
  MTP capability.

## Blocked Definition

This goal is blocked only if all of the following are true:

- local models or the isolated `mlx-vlm` probe runtime required by the F-3 spec
  are unavailable or cannot be launched;
- no lightweight introspection can determine whether a resident API surface is
  present;
- a real F-3.1 verdict cannot be produced without upstream changes or user
  intervention.

If blocked, preserve the current F-3 design spec, write the exact missing
runtime primitive, and do not start F-3.2/F-3.3.

## Hard Rules

- Do not start F-3.2 resident backend code-grade until §2.1 route 1 or route 2
  is proven.
- Do not count the existing `MlxVlmMtpChildRunner` as resident if it shells out
  to `python -m mlx_vlm generate` per request.
- Do not edit `mlx-vlm`, vendor upstream, or change the F-1
  `speculative_execution_status` schema.
- Do not touch Track 1 cache/memory files.
- Do not promote `assistant_drafter`; keep `GEMMA4_MTP_CAPABILITY_LABEL` as
  `experimental`.
- Leave unrelated dirty and untracked files untouched.

## Out of Scope

- F-3.2 resident backend implementation.
- F-3.3 pure-decode A/B benchmark.
- DS4 MTP work.
- Qwen / text-line MTP work.
- Continuous batching or parallel generation.
- Source-of-truth promotion to `partial` or `supported`.

## Current Truth

- F-3 design-grade spec is landed and indexed in
  `docs/architect/design/README.md`.
- `mlx-lm #980` is closed on GitHub as of the 2026-06-01 live check, but this
  does not prove the local Gemma4 resident-MTP prerequisite.
- The main environment reports `mlx-lm 0.31.3` and no `mlx-vlm` package.
- The original isolated MTP probe runtime at
  `runtime-probes/mlx-vlm-mtp-probe/.venv` is Python 3.14 and currently cannot
  import `mlx_vlm` because `mlx/core.cpython-314-darwin.so` is rejected by
  macOS system policy.
- A replacement isolated probe runtime has been created at
  `runtime-probes/mlx-vlm-mtp-probe-py311/.venv`; it reports `mlx-vlm 0.5.0`,
  `mlx-lm 0.31.3`, and `mlx 0.31.2`, and imports `mlx.core` / `mlx_vlm`
  successfully.
- Local target and drafter model directories exist:
  `/Users/yeemio/AI/Agent/models/gemma-4-31B-it` and
  `/Users/yeemio/AI/Agent/model-candidates/mlx-community/gemma-4-31B-it-assistant-bf16`.
- The existing `owlmlx/runtime/mlx_vlm_mtp_runner.py` child runner is not
  resident in the F-3 sense: it keeps the child process alive, but each
  generation still shells out to the `mlx-vlm` CLI.

## Remaining Gaps

- Determine whether the installed py311 isolated `mlx-vlm` stack exposes a
  programmatic resident generation path that can load once and serve multiple
  requests.
- If such a path exists, run the minimal ≥3-request F-3.1 probe and write the
  verdict ledger.
- If such a path does not exist, record `blocked_on_local_runtime` with enough
  evidence to avoid guessing.
- Update F-3 docs/evidence honestly after the verdict.

## Dominant Next Gap

`f3-1-local-resident-mtp-feasibility-probe`

The next executable round is not F-3.2 code-grade. It is a narrow F-3.1 probe:
verify whether the current local `mlx-vlm` / `mlx-lm` runtime can support a
true resident Gemma4 MTP process, or prove that the current lane remains
blocked.
