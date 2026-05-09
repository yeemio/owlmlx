# owlmlx Gemma4 MTP Resident VLM Adapter Contract

## Context

Gemma4 MTP now has verified experimental evidence:

- wrapper/contract:
  `owlmlx/gemma4_mtp_drafter.py`
- selectable child runner:
  `owlmlx/runtime/mlx_vlm_mtp_runner.py`
- A/B timing summary:
  `files/evidence/owlmlx/gemma-mtp-ab-timing/20260506T135656Z/summary.json`

The A/B verdict is:

`mtp_measured_faster`

But the claim boundary is strict: it measured fresh `mlx-vlm` CLI process
timing, including load and process startup. It is not resident decode speedup
and not supported serving.

## Objective

Define and implement the smallest honest resident `mlx-vlm adapter` contract
for Gemma4 MTP so owlmlx can separate:

- model load time
- drafter load / readiness
- first token / first visible token
- decode timing
- post-run health

## Hard Rules

- Keep capability label `experimental`.
- Preserve the adapter split:
  - `mlx-lm adapter` for text LLM paths
  - `mlx-vlm adapter` for Gemma4 / multimodal / MTP drafter paths
- Do not vendor unstable `mlx-vlm` internals as if they were stable API.
- Do not call fresh CLI timing a resident decode speedup.
- Do not change default 8066 behavior unless the caller explicitly selects the
  experimental runner / adapter.
- Keep unit tests free of live 50GB loads.

## Required Work

1. Inspect `mlx-vlm 0.5.0` resident server and programmatic generation seams
   again, but select only one minimal implementation path.
2. If programmatic API remains too unstable, freeze a resident-adapter blocker
   and expose the exact reason in source-of-truth.
3. If a resident adapter is feasible, add a small adapter contract that records:
   - target model path
   - drafter path
   - drafter kind / block size
   - adapter family: `mlx-vlm`
   - load mode
   - generation mode
   - MTP accepted-token summary, if available
4. Add tests for contract serialization, blocked-state honesty, and no
   supported-serving overclaim.
5. Run at most one small live smoke if the resident path is implemented.

## Acceptance Criteria

- Source-of-truth says one of:
  - `resident_vlm_adapter_feasible`
  - `resident_vlm_adapter_blocked`
- If feasible, a live smoke records clean load/generate/unload or explicitly
  records why unload is not supported yet.
- If blocked, the blocker is exact enough that the next executor knows whether
  to wait for upstream `mlx-vlm`, wrap its server, or implement an owned
  adapter over internal APIs.
