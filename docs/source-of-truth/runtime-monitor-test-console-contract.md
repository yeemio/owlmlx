# owlmlx Runtime Monitor And Test Console Contract

> Status: design source of truth
> Updated: 2026-05-06
> Scope: runtime-owned monitoring, test-run launch, live run observation, and
> OwlOps consumption boundaries for the 8066 technical-preview runtime

## 1. Purpose

The `8066` technical-preview runtime already exposes enough live truth for
operator inspection through `/healthz`, `/v1/runtime/status`,
`/v1/runtime/host-pressure-sample`, model-load admission, orchestration
contracts, and Model RC history. That is not yet a complete monitor.

This document freezes the complete runtime-side design for:

- live runtime monitoring that upper layers can consume without inventing
  runtime semantics
- a safe test-launch contract so OwlOps can initiate Model RC / optimization
  probes directly
- run-event and evidence indexing so test progress, blockers, and post-run
  health are observable in one operator workflow

The design is intentionally broader than a lightweight status page. It is the
runtime contract behind an OwlOps `Runtime Monitor + Test Console` workspace.

## 2. Ownership Boundary

`owlmlx` owns runtime truth:

- listener and backend health
- runtime readiness and degraded / unhealthy semantics
- loaded, active, visible, resident, and admissible model truth
- generation gate, queue, and active-run truth
- host-pressure, memory-budget, load-failure, cooldown, recovery, and reclaim
  barrier truth
- Model RC runner evidence, verdicts, caveats, and ledger/history surfaces
- test-run preflight, live-run lifecycle, event stream, and action audit

OwlOps owns operator rendering:

- monitor workspace layout
- current-versus-history presentation
- charts and regressions once repeated evidence exists
- operator confirmations and display affordances
- action rendering for load, unload, abort, restart, and test launch

OwlOps must not infer runtime meaning from missing or stale fields. When
runtime truth is absent, it should display `unknown`, `insufficient_signal`,
`stale`, or `unsupported` exactly as returned by `owlmlx`.

## 3. Existing Runtime Inputs

The monitor contract composes existing supported or diagnostic runtime surfaces
rather than replacing them.

| Input | Current role |
|---|---|
| `GET /healthz` | liveness, readiness, backend name, active model, loaded count |
| `GET /v1/runtime/status` | core status plus diagnostic sections for backend detail, inventory, budget, generation gate, load failure, cooldown, and cached host pressure |
| `POST /v1/runtime/host-pressure-sample` | explicit host-pressure refresh; not an implicit background sampler |
| `GET /v1/runtime/model-load-admission` | model-specific load/admission projection |
| `GET /v1/runtime/model-release-candidates/history` | authoritative Model RC history and latest-per-model input |
| `GET /v1/runtime/orchestration-status` | runtime-owned bottleneck layer assessment |
| recovery / scheduler / residency / memory-pressure contract routes | narrower truth contracts consumed by monitor details |

The complete monitor should preserve these sources and expose a normalized
operator snapshot so OwlOps does not have to stitch raw sections ad hoc.

## 4. Target Monitor Snapshot

Target route:

`GET /v1/runtime/monitor/snapshot`

This route is not part of the public technical-preview surface until it is
implemented and listed in `public-surface.md`.

The snapshot is a normalized aggregate. It should carry source and freshness
metadata for every derived section:

```json
{
  "contract": {
    "surface": "owlmlx.runtime.monitor.snapshot",
    "version": "v1"
  },
  "sampled_at": "2026-05-06T00:00:00Z",
  "runtime_url": "http://127.0.0.1:8066",
  "service": {},
  "backend": {},
  "models": {},
  "workload": {},
  "resources": {},
  "recovery": {},
  "release_candidates": {},
  "test_runs": {},
  "sources": []
}
```

Required sections:

- `service`: listener, liveness, readiness, `ok`, port, process identity when
  available, staleness, and whether the snapshot came from live HTTP or a
  fallback path
- `backend`: backend name, health, persistent child status, last subprocess
  summary, backend error, last failure class, and unsupported fields
- `models`: active model, loaded models, visible models, resident/admission
  summary, model count, and missing-truth markers
- `workload`: active run id if known, generation gate state, queue size, queue
  policy, longest execution, total served, current phase, and block reason
- `resources`: serving budget, loaded GB, available GB, host-pressure sample,
  RSS/peak source, cooldown, and pressure classification
- `recovery`: load-failure events, dead registered models, reclaim barrier,
  restartability, termination recovery, and abort-recovery truth
- `release_candidates`: latest row per model, history counts, latest evidence
  path, verdict, blockers, quality caveats, TTFT, decode speed, and post-run
  health gate result
- `test_runs`: known live or recent operator-launched runs, run status, audit
  pointer, event-stream URL, and evidence directory
- `sources`: per-source `name`, `route_or_file`, `sampled_at`, `status`,
  `staleness_ms`, and `truth_level`

The route must not hide clean idle `readiness=degraded` states. A clean idle
runtime can be healthy when `ok=true`, backend error is null, no model is
active, and no model is loaded.

## 5. Target Event Stream

Target route:

`GET /v1/runtime/monitor/events`

This route should stream Server-Sent Events for monitor and test-run consumers.
It is allowed to begin as `partial` after implementation: the first version may
emit runtime-owned run and lifecycle events without pretending to be a complete
system metrics stream.

Event envelope:

```json
{
  "event_id": "mon_000001",
  "run_id": "optional",
  "type": "test_run.phase_changed",
  "phase": "generate",
  "severity": "info",
  "sampled_at": "2026-05-06T00:00:00Z",
  "source": "runtime_model_release_candidate",
  "truth_level": "runtime_owned",
  "payload": {}
}
```

Initial event taxonomy:

- `service.snapshot`
- `service.health_changed`
- `backend.error_latched`
- `backend.error_cleared`
- `model.load_started`
- `model.load_completed`
- `model.load_failed`
- `model.unload_started`
- `model.unload_completed`
- `generation.queued`
- `generation.started`
- `generation.first_token`
- `generation.token_delta`
- `generation.completed`
- `generation.failed`
- `test_run.preflight_completed`
- `test_run.started`
- `test_run.phase_changed`
- `test_run.aborted`
- `test_run.completed`
- `test_run.blocked`
- `evidence.record_written`
- `post_run_health.completed`

Polling remains acceptable as a UI fallback, but polling is not the runtime
design target.

## 6. Runtime Trend History

Target route:

`GET /v1/runtime/monitor/history`

This route exposes runtime-owned long-run monitor history. It is backed by a
rolling JSONL ledger and contains compact samples derived from
`/v1/runtime/monitor/snapshot`. The history route exists so OwlOps can render
long-running curves and comparisons without becoming the source of runtime
truth.

Current ledger:

`files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl`

Sample contract:

```json
{
  "contract": {
    "surface": "owlmlx.runtime.monitor.sample",
    "version": "v1"
  },
  "sampled_at": "2026-05-06T00:00:00Z",
  "runtime_url": "http://127.0.0.1:8066",
  "source": "runtime_monitor_background_sampler",
  "truth_level": "runtime_owned",
  "service": {},
  "workload": {},
  "resources": {},
  "models": {},
  "test_runs": {},
  "release_candidates": {}
}
```

History envelope:

```json
{
  "contract": {
    "surface": "owlmlx.runtime.monitor.history",
    "version": "v1"
  },
  "status": "available",
  "ledger_status": "available",
  "ledger_path": "files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl",
  "history_count": 120,
  "samples": []
}
```

Trend history safety rules:

- The background sampler must not load models, generate text, abort runs, or
  mutate legacy listeners.
- Missing metrics remain absent; the sampler must not infer unavailable host,
  memory, queue, or test-run fields.
- Snapshot-route sampling may append a compact sample, but snapshot reads do
  not initiate model work.
- OwlOps may mirror this history locally for chart responsiveness, but
  `owlmlx` remains the owner of runtime history truth.

8066 should be started with both the trend ledger and a positive sample
interval when long-run monitoring is needed:

```bash
--runtime-monitor-trend-ledger-path /Users/yeemio/AI/gitrep/owlmlx/files/evidence/owlmlx/runtime-monitor-trends/trend-ledger.jsonl \
--runtime-monitor-sample-interval-s 15
```

## 7. Target Test-Run Launch Contract

OwlOps needs a direct entry point for runtime tests, but every action must be
runtime-owned, preflighted, serial, and auditable.

Target routes:

| Route | Purpose |
|---|---|
| `POST /v1/runtime/test-runs/preflight` | read-only check for readiness, active run, model visibility, admission, host pressure, budget, and selected profile |
| `POST /v1/runtime/test-runs` | explicit test-run launch; returns `run_id` and URLs instead of blocking the HTTP request |
| `GET /v1/runtime/test-runs` | recent run index with audit and evidence pointers |
| `GET /v1/runtime/test-runs/{run_id}` | current status, phase, metrics, blockers, and evidence path |
| `GET /v1/runtime/test-runs/{run_id}/events` | run-scoped SSE stream |
| `POST /v1/runtime/test-runs/{run_id}/abort` | explicit audited abort request |

Launch request shape:

```json
{
  "model_id": "gemma-4-31B-it",
  "test_profile_id": "gemma-repetitive-output-template",
  "mode": "live",
  "parameters": {
    "max_tokens": 256,
    "temperature": 0.2,
    "repeat_count": 2,
    "timeout_s": 900,
    "memory_gb": 60
  },
  "operator": {
    "surface": "owlops",
    "session_id": "optional",
    "requested_by": "local_operator"
  }
}
```

Required preflight outputs:

- `decision`: `admit`, `defer`, `reject`, or `unknown`
- `reason`
- `service_readiness`
- `active_run_state`
- `model_visibility`
- `model_load_admission`
- `host_pressure`
- `serving_budget`
- `generation_gate`
- `estimated_memory_gb`
- `selected_profile`
- `would_write_evidence_to`
- `required_operator_confirmation`

Live launch is allowed only when:

- preflight returns `admit`
- no active heavy test run is in progress
- host pressure is not abnormal
- the selected model/test profile is allowlisted
- the operator has explicitly requested `mode=live`
- an audit event can be written before the run starts

If any condition is not known, the launch result must be `blocked` or
`unknown`; it must not silently proceed.

## 8. Test Profiles

The first operator profiles map directly to the current Model RC optimization
lanes:

| Profile id | Model | Purpose |
|---|---|---|
| `qwen36-27b-decode` | `Qwen3.6-27B` | isolate decode throughput after TTFT and queue wait |
| `qwen36-35b-ttft-template` | `Qwen3.6-35B-A3B` | separate template/request mode from first-token latency |
| `gemma-repetitive-output-template` | `gemma-4-31B-it` | suppress or route repetitive/visible reasoning output without hiding failure |
| `post-run-health-gate` | any mainline model | prove repeated load/generate/unload leaves backend health clean |

Every profile must record:

- prompt/template provenance
- request mode
- effective model profile defaults
- memory-gb source
- timing breakdown
- output sanity label
- quality caveats
- post-run health artifacts
- evidence directory

## 9. Audit And Evidence

Runtime test launch must write an audit ledger separate from the Model RC
result ledger. The audit ledger answers who requested what and whether the
request was admitted, rejected, aborted, or completed.

Target audit directory:

`files/evidence/owlmlx/runtime-test-runs/`

Each audit row should include:

- `audit_id`
- `run_id`
- `requested_at`
- `operator.surface`
- `model_id`
- `test_profile_id`
- `mode`
- `parameters`
- `preflight_decision`
- `launch_decision`
- `abort_requested`
- `final_status`
- `evidence_path`
- `model_release_candidate_record_path`

The Model RC ledger remains the authoritative model verdict/history surface.
Audit rows do not replace Model RC records.

## 10. Safety Rules

- Do not run heavy models concurrently.
- Do not stop or mutate legacy listeners on `8001` or `8009`.
- Do not infer missing model truth from names or old records.
- Do not auto-kill backend processes from an OwlOps action.
- Do not treat UI-side abort as a successful cleanup unless runtime confirms
  cleanup and post-run health.
- Do not mark any mainline model `pass` without the Model RC pass criteria.
- Do not promote DeepSeek V4 into the mainline matrix.
- Do not describe this work as release-ready, production-ready, parity,
  replacement, equivalent, wins, or beats.

## 11. Implementation Order

1. Contract and schema slice:
   - add pure schema/builders for monitor snapshot, event envelope, test-run
     preflight, run status, and audit row
   - add fake-runtime tests
   - add source-of-truth docs and keep routes out of `public-surface.md` until
     implemented
2. Runtime endpoint slice:
   - expose `GET /v1/runtime/monitor/snapshot`
   - expose `GET /v1/runtime/monitor/history`
   - add runtime-owned rolling trend ledger and optional background sampler
   - expose read-only `POST /v1/runtime/test-runs/preflight`
   - expose run index/status as empty or audit-backed truth
   - return explicit `unsupported` for live launch until the launch worker is
     implemented
3. Event and launcher slice:
   - add monitor SSE and run-scoped SSE
   - add single-run lock and audited launch worker around the Model RC runner
   - add explicit audited abort request handling
4. Live proof slice:
   - verify 8066 with live `/healthz`, `/v1/runtime/status`, host pressure,
     preflight, and no active run
   - run only one selected mainline optimization profile serially
   - write evidence and verify post-run health
5. OwlOps consumption slice:
   - OwlOps consumes the normalized snapshot, trend history, events,
     preflight, run status, audit, and Model RC history without inventing
     runtime truth

## 12. Acceptance Criteria

The runtime monitor/test console contract is acceptable when an upper layer can
answer all of the following from runtime-owned fields:

- Is 8066 alive?
- Is the backend healthy, degraded clean-idle, or unhealthy?
- Is a model loaded or active?
- Is a generation/test run active or queued?
- Why can or cannot a selected model test run now?
- What memory budget and host-pressure state are relevant?
- Which preflight decision was made and from which sources?
- What test run is active, what phase is it in, and where is its event stream?
- What evidence directory and Model RC record were written?
- Did post-run health end clean?
- What is the latest Model RC row per model?
- What did host pressure, memory headroom, queue, and known-run counts do over
  the selected long-run window?
- Which fields are unknown, stale, unsupported, or insufficient signal?

The contract is not acceptable if OwlOps must guess runtime state by combining
unversioned fields, if live test launch can bypass preflight/audit, or if a
clean idle degraded state is rendered as a runtime failure.
