# owlmlx Technical Preview Active Client Retarget Prompt

> Date: 2026-05-05
> Goal ID: `owlmlx_technical_preview_cutover_delivery`
> Round: `active_client_retarget_to_owlmlx_8066`
> Repo of truth: `/Users/yeemio/AI/gitrep/owlmlx`

## Mission

Retarget exactly one active client boundary to the resident `owlmlx`
technical-preview server at `http://127.0.0.1:8066`, prove that the client can
complete its own health/model/generate probe, and decide whether the matching
legacy listener can be stopped in a later controlled round.

## Frozen Current Truth

- `owlmlx` release-floor readiness is sealed at `7 / 7`.
- `owlmlx` technical preview is running on `127.0.0.1:8066`.
- `GET /healthz` on `8066` returns HTTP 200 with
  `backend_name = "mlx-lm-subprocess"`.
- `gemma-4-31B-it` has completed real `load -> generate -> unload` through
  `8066`.
- an external probe from `/Users/yeemio/AI/gitrep/owlops` has completed
  health/model/load/generate/unload against `8066`.
- legacy `oMLX :8001` and router `:8009` are still running intentionally.

## Hard Rules

- Do not stop `:8001` or `:8009` until the active client retarget probe passes.
- Do not claim release-ready, parity, replacement-grade performance,
  production-grade, superiority, or equivalence.
- Do not edit unrelated dirty files.
- If working outside `owlmlx`, first name the repo and scope explicitly in the
  handoff.
- If the client cannot be retargeted without product/business choice, stop
  with an exact blocker rather than guessing.

## Required Work

1. Verify `127.0.0.1:8066` is still listening and healthy.
2. Identify one active client boundary that currently depends on legacy local
   runtime routing.
3. Retarget only that boundary to `http://127.0.0.1:8066`.
4. Run that client's own health/model/generate probe.
5. Archive evidence with exact commands, cwd, HTTP statuses, payload excerpts,
   and process state.
6. State whether legacy `:8001` can be scheduled for shutdown in the next
   round.

## Verification Matrix

Required:

- `curl http://127.0.0.1:8066/healthz` -> HTTP 200.
- client-native health/model/generate probe -> pass.
- `lsof -n -iTCP:8066 -sTCP:LISTEN` -> owlmlx listener present.
- `lsof -n -iTCP:8001 -sTCP:LISTEN` and `lsof -n -iTCP:8009 -sTCP:LISTEN`
  recorded before any shutdown decision.
- `git diff --check` in every edited repo -> clean.

Optional but recommended:

- one short `gemma-4-31B-it` generate through the client path.

## Deliverables

- Handoff under `files/execution-prompts/owlmlx/` or the edited repo's prompt
  archive, naming every touched repo.
- Evidence directory under
  `files/evidence/owlmlx/technical-preview-cutover/` or a linked consumer
  evidence path.
- Final verdict:
  - `active_client_retarget_passed_shutdown_ready`
  - `active_client_retarget_passed_shutdown_not_ready`
  - `active_client_retarget_blocked`

## Non-Goals

- Do not optimize throughput.
- Do not add a process supervisor.
- Do not replace the router.
- Do not close comparative `vMLX` measured gaps.
