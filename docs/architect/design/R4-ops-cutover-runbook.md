# R4 Phase-1 Controlled-Smoke Operator Runbook

> Operator procedure for the ONE controlled non-default OwlCoda agentic smoke.
> Pairs with the harness `scripts/replacement/r4_ops_cutover_pilot.py` and the
> design spec [`R4-ops-cutover-spec.md`](R4-ops-cutover-spec.md).
> **Non-default, single session.** Does NOT flip OwlCoda/OwlCC defaults, does NOT
> remove `:8009` globally, claims NO replacement-complete, promotes NO capability.

## 0. Variables (port is NOT a contract — set per host)

```bash
export OWLMLX_PILOT_BASE_URL="http://127.0.0.1:8066"   # default example only
export OWLMLX_PILOT_MODEL_ID="<the Qwen pilot model id, e.g. Qwen3.6-27B>"
export OWLMLX_COMMIT="$(git -C /Users/yeemio/AI/gitrep/owlmlx rev-parse HEAD)"
export PILOT_SESSION_ID="pilot-001"
```

## 1. Launch owlmlx (native backend) and capture its request log

Start the runtime so the Qwen pilot model is loadable on the native backend, and
**redirect the request log to a file** (there is no ledger endpoint — owlmlx logs
inbound requests via the `owlmlx.runtime.server.request` logger as
`request.start` / `request.finish` with `owlmlx_request_id` / `owlmlx_http_path`).

Record the exact launch command into the capture's `reproduction.launch_command`.

## 2. Probe readiness (harness)

```bash
uv run python -m scripts.replacement.r4_ops_cutover_pilot probe-readiness \
  --base-url "$OWLMLX_PILOT_BASE_URL" \
  --model-id "$OWLMLX_PILOT_MODEL_ID" \
  --owlmlx-commit "$OWLMLX_COMMIT"
```

- Writes `files/evidence/owlmlx/replacement/r4-ops-cutover/<ts>-readiness-<verdict>-<model>.json`.
- If `pilot_readiness_failed`: STOP. That artifact IS the deliverable for this run
  (feed it to R1/R4 blocker). Do not run the smoke.

## 3. Configure a NON-DEFAULT OwlCoda pilot pointing at owlmlx

- In a throwaway/non-default OwlCoda profile (NOT the committed default), set the
  provider base URL to `$OWLMLX_PILOT_BASE_URL` and the model to `$OWLMLX_PILOT_MODEL_ID`.
- Disable `:8009` legacy fallback **for this session** (the point under test).
- **Commit no OwlCoda repo file.** Snapshot the effective config (base_url, provider,
  fallback_enabled) into the capture's `fallback.config_snapshot`.

## 4. Run ONE real agentic tool loop

Drive a real task that forces at least one tool call → execution → result round-trip
→ final answer. As it runs, record the four sub-gates HONESTLY (each independent):

| Sub-gate | How to confirm |
|---|---|
| `tool_call_emitted` | owlmlx response had `choices[0].message.tool_calls[]` non-empty (`finish_reason == "tool_calls"`) |
| `tool_call_executed` | OwlCoda actually ran the named tool |
| `tool_result_roundtrip` | the tool result was posted back to owlmlx as a `tool` message |
| `final_answer_after_tool` | owlmlx produced a final assistant answer after the tool result |

## 5. Capture the fallback double-proof + watermark health

- `fallback.consumer_outbound`: from OwlCoda's side — `fallback_count` (must be 0)
  and the set of outbound hosts (must be only the pilot host). owlmlx never calls
  `:8009`, so this no-`:8009` proof is necessarily consumer-side.
- `fallback.owlmlx_inbound.served_request_ids`: grep the captured owlmlx request log
  for `owlmlx_request_id` values; every pilot request-id must appear (inbound coverage).
- `reproduction.request_ids`: the `x-request-id` values from the session.
- `watermark_classifications`: sample `GET $OWLMLX_PILOT_BASE_URL/v1/runtime/monitor/snapshot`
  during the run; collect each `resources.host_pressure.classification`.

## 6. Assemble the verdict

Fill `capture.json` (schema in the plan, Task 8) and run:

```bash
uv run python -m scripts.replacement.r4_ops_cutover_pilot assemble-evidence \
  --capture capture.json \
  --readiness-artifact files/evidence/owlmlx/replacement/r4-ops-cutover/<readiness-artifact>.json \
  --base-url "$OWLMLX_PILOT_BASE_URL"
```

- Writes `<ts>-pilot-<verdict>-<session>.json` + appends `pilot-ledger.jsonl`.
- `passed` = this ONE session's gates met. NOT replacement-complete. Promotes nothing.

## 7. What this run feeds

- `passed` / `loop_failed` / `pilot_readiness_failed` → blocker ④ + gap 5 evidence,
  plus any tool-lane shortfall → R1 findings. The replacement verdict stays
  `not yet replaceable` regardless.
