# owlmlx Technical Preview Cutover Goal Contract

> Date: 2026-05-05
> Goal ID: `owlmlx_technical_preview_cutover_delivery`
> Status: `deliverable_after_local_and_external_boundary_probe`

## 1. Title

Deliver an `owlmlx` technical-preview serving path that can run side-by-side
with legacy services and survive a real load/generate/unload probe.

## 2. Success Definition

This goal is satisfied when all of the following are true:

- `owlmlx` exposes a supported technical-preview server entrypoint.
- the server can be started on `127.0.0.1:8066` without stopping legacy
  `oMLX :8001` or router `:8009`.
- at least one locally visible model can be loaded, generated through, and
  unloaded via the real `mlx-lm-subprocess` backend.
- at least one external consumer-boundary probe can call `8066` and complete
  health/model/load/generate/unload checks.
- evidence, handoff, tests, and staged source changes are archived in this
  repo.
- no release-ready, parity, replacement-grade performance, production-grade,
  or superiority claim is made.

## 3. Blocked Definition

This goal is blocked only if:

- `8066` cannot start with the repo `.venv/bin/python`;
- `mlx_lm` cannot load a visible local model through the subprocess backend;
- generation fails after API-parameter adaptation;
- the service cannot be probed from an external working directory; or
- a required cutover action needs edits outside `owlmlx`.

## 4. Hard Rules

- Use `/Users/yeemio/AI/gitrep/owlmlx/.venv/bin/python`, not bare
  `python3`.
- Do not stop legacy `oMLX :8001` or router `:8009` before an active client
  has been retargeted and probed.
- Do not edit `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent` from this
  owlmlx-owned round.
- Archive evidence under
  `files/evidence/owlmlx/technical-preview-cutover/`.
- Archive handoffs/prompts under `files/execution-prompts/owlmlx/`.
- Keep `oMLX` and `vMLX` as reference runtimes, not identity sources.

## 5. Out Of Scope

- production supervisor / daemon management
- router replacement
- OwlCoda or OwlOps configuration edits
- performance optimization versus `oMLX` / `vMLX`
- stopping legacy services without a retargeted active-client probe

## 6. Current Truth

- release-floor readiness is sealed at `7 / 7` in commit `759365d`.
- the supported technical-preview boundary is documented in
  `docs/source-of-truth/public-surface.md`.
- `scripts/runtime_technical_preview_server.py` starts a real
  `RuntimeKernel(MlxLmSubprocessBackend(...))` path on `127.0.0.1:8066`.
- `gemma-4-31B-it` was loaded, generated through, and unloaded successfully
  from both the owlmlx repo and an external `owlops` working directory.
- a resident empty preview server is running on `127.0.0.1:8066` with
  `GET /healthz` returning HTTP 200.
- legacy `oMLX :8001` and router `:8009` are still running by design.

## 7. Remaining Gaps

- an active client configuration has not yet been retargeted to
  `http://127.0.0.1:8066`;
- the legacy listener shutdown has not yet been scheduled or executed;
- comparative performance remains behind `oMLX` on the measured short prompt;
- no closeout-grade `vMLX` same-host measured record exists yet.

## 8. Dominant Next Gap

`active_client_retarget_to_owlmlx_8066_missing`

The next round should retarget exactly one active client boundary to
`http://127.0.0.1:8066`, run that client's own health/model/generate probe,
and only then decide whether a controlled shutdown of the corresponding legacy
listener is safe.
