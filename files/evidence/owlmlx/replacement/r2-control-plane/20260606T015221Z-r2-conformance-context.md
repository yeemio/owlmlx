# R2 consumer-contract conformance — run context (20260606T015221Z)

> Companion to `20260606T015221Z-r2-conformance.json`. Promotes nothing. Read-only run.

## Repro
- **cmd:** `.venv/bin/python scripts/replacement/r2_control_plane_conformance.py probe-contracts --base-url http://127.0.0.1:8066 --out files/evidence/owlmlx/replacement/r2-control-plane/20260606T015221Z-r2-conformance.json`
- **probe client commit:** `r2-control-plane-closure` @ `50d7f76e` (this repo)
- **server under probe:** the operator's live default daemon at `http://127.0.0.1:8066` (separate process; `/healthz` reports `contract.version="stabilization1"`). Server code version not introspected by the probe.
- **probe type:** read-only (HTTP GET only); no runtime state mutated.

## Server state at probe time (`/healthz`)
`{"ok": true, "readiness": "degraded", "active_model_id": null, "model_count": 0, "backend_name": "mlx-native"}` — daemon **idle** (no model loaded).

## Verdict
`contract_gap_found` (exit 2), **gap_count = 1**.

| contract | endpoint | status |
|---|---|---|
| owlcc_preflight_healthz | /healthz | pass |
| **owlcc_preflight_v1_models** | /v1/models | **gap** |
| owlcc_resolution_openai_models | /v1/openai/models | pass |
| owlcoda_gate_openai_models | /v1/openai/models | pass |
| owlcoda_gate_model_visibility | /v1/runtime/model-visibility | pass |
| owlcoda_gate_loaded_inventory | /v1/models | pass |
| owlcoda_gate_runtime_status | /v1/runtime/status | pass |

## Interpretation (honest)
- The single gap is **not an owlmlx defect**: OwlCC preflight reads `/v1/models` → `data[].id` (`owlcc/src/preflight.ts:119-120`), but owlmlx serves the OpenAI-list `data[].id` shape at `/v1/openai/models` (which **passed**). **Resolution = consumer-side**: OwlCC must read `/v1/openai/models` for availability after repointing `routerUrl` to owlmlx. This is the frozen last-mile contract (see `docs/architect/design/R2-control-plane-runbook.md` §2).
- OwlCoda's owlmlx-gate (`owlcoda/src/runtime-probe.ts`) already reads owlmlx's surfaces correctly — all 4 OwlCoda contracts pass.

## Caveat (idle-state coverage)
The daemon had `model_count=0` at probe time, so the per-element list checks for `backend.loaded_models[].model_id` and the loaded-inventory `inventory.entries[].model_id` were satisfied against **empty lists** (list-presence verified; element shape not exercised). The model-visibility `entries[].{model_id,visible,block_reason}` checks WERE exercised (registry entries are non-empty regardless of load state). Populated-list element coverage belongs to the cost-gated operability rehearsal (a loaded model). This does not affect the single gap finding, which is structural and model-count-independent.
