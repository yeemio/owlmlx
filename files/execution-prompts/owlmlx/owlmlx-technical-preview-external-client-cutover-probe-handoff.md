# owlmlx Technical Preview External Client Cutover Probe Handoff

> Date: 2026-04-30
> Outcome: `owlmlx_technical_preview_external_client_probe_passed`
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`

## 1. Verdict

An external consumer-boundary probe passed against the `owlmlx` technical
preview server on `127.0.0.1:8066`.

The client process ran from:

- `/Users/yeemio/AI/gitrep/owlops`

The server process ran from:

- `/Users/yeemio/AI/gitrep/owlmlx`

No `owlops`, `owlcoda`, or `/Users/yeemio/AI/Agent` files were edited.

## 2. External Probe Evidence

Evidence directory:

- `files/evidence/owlmlx/technical-preview-cutover/20260430T030749Z-external-client/`

The external client used `curl` from the `owlops` working directory.

Observed:

- `GET /healthz`
  - HTTP 200
  - `runtime = "owlmlx"`
  - `backend_name = "mlx-lm-subprocess"`
  - `persistent_child = true`
- `GET /v1/runtime/status`
  - HTTP 200
- `GET /v1/runtime/model-visibility`
  - HTTP 200
  - visible models included `gemma-4-31B-it`
- `GET /v1/openai/models`
  - HTTP 200
- `POST /v1/load`
  - model: `gemma-4-31B-it`
  - HTTP 200
  - `ok = true`
  - duration: `6.1138s`
  - child pid: `40904`
  - runner path:
    `/Users/yeemio/AI/Agent/models/gemma-4-31B-it`
- `POST /v1/generate`
  - prompt: `Reply with exactly OK.`
  - params: `{"max_tokens": 2, "temperature": 0.0}`
  - HTTP 200
  - `ok = true`
  - text: ` OK.`
  - duration: `2.3971s`
  - execution time: `2.3603s`
- `POST /v1/unload`
  - HTTP 200
  - `ok = true`

Cleanup:

- the probe-owned preview server was terminated
- `lsof -n -iTCP:8066 -sTCP:LISTEN` returned no listener after cleanup

## 3. Resident Preview Service

After the external probe passed, an empty resident preview server was started
on `127.0.0.1:8066`.

Evidence directory:

- `files/evidence/owlmlx/technical-preview-cutover/20260430T030849Z-resident-8066/`

Observed:

- pid: `43243`
- `GET /healthz` returned HTTP 200
- `runtime = "owlmlx"`
- `backend_name = "mlx-lm-subprocess"`
- `active_model_id = null`
- `model_count = 0`
- `readiness = "degraded"` because no model is loaded yet

This resident service is a technical-preview endpoint, not a process-manager
or production supervisor.

## 4. Legacy Services

Legacy services were intentionally left running:

- `127.0.0.1:8001` still has the legacy `oMLX` service
- `:8009` still has the legacy router

Reason: `owlmlx` has now passed local and external-boundary probes, but the
active desktop/router client configuration has not been retargeted to `8066`.
Stopping legacy listeners before that retarget would risk breaking current
workflows without increasing evidence quality.

## 5. Next Operational Step

The next cutover round should retarget one active client configuration to
`http://127.0.0.1:8066`, run that client's own health/model/generate probe,
and only then schedule a controlled shutdown of the matching legacy listener.

Do not close `:8009` in the same step unless the router's replacement path is
explicitly configured and probed.

This handoff makes no release-ready, parity, replacement-grade performance, or
superiority claim against `oMLX` / `vMLX`.
