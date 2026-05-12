# owlmlx Public Surface

> Status: authoritative
> Updated: 2026-05-05
> Scope: which modules, contracts, HTTP routes, and operator scripts are part
> of the supported public technical-preview surface, and which surfaces remain
> internal

## 1. Purpose

This document freezes the public technical-preview boundary for `owlmlx` so
upper layers (notably the desktop product shell, OwlOps, OwlCoda, and other
external consumers) know exactly which surfaces they may depend on and which
surfaces may change without notice.

It exists to satisfy `release-readiness-backlog.md` section `3.7`. It is a
boundary document, not marketing. It references existing source-of-truth
documents instead of duplicating their content.

This document does **not** make any claim of release readiness, parity,
replacement, production-grade capability, or any banned-vocabulary verdict
about owlmlx. The release-readiness floors are closed at `7 / 7` in
`release-readiness-backlog.md`, including floor `3.6 External Customer
Evidence` and floor `3.7 Public Surface Freeze`; that closure permits the
technical-preview boundary below, not a stronger public claim.

## 2. Support Label Vocabulary

Per `AGENTS.md` writing rules, capability and surface labels are exactly:

- `supported` — runtime-owned, frozen contract; upper layers may depend on
  the named shape and behavior across releases until the change rule in §11
  triggers
- `partial` — runtime-owned, but the surface is narrower than its eventual
  scope; consumers should expect the shape to extend additively
- `experimental` — runtime-owned but not frozen; shape and behavior may
  change between releases without a deprecation cycle
- `internal` — owlmlx-owned implementation detail; **not** part of the public
  surface; may change at any time
- `not in scope` — explicitly outside owlmlx ownership; see
  `repository-boundaries.md`

Anything not listed in this document is `internal` by default. See §10.

## 3. Supported HTTP Routes

The runtime exposes the following stable HTTP routes through
`owlmlx.runtime.server.create_app(...)`. The full request/response shape and
section freezes live in `runtime-status-schema.md` and the per-contract
documents linked below.

### 3.1 Liveness And Status

- `GET /healthz` — `supported` — frozen liveness/readiness contract
  (Stabilization-1); see `runtime-status-schema.md` §6
- `GET /v1/runtime/status` — `supported` — core runtime status with stable
  sections (`contract`, `summary`, `health`, `inventory`, `budget`, `restart`)
  plus diagnostic sections that are best-effort detail; see
  `runtime-status-schema.md` §6

### 3.2 Generation And Compatibility Surfaces

- `POST /v1/generate` — `supported` — runtime-native generation
- `POST /v1/generate/stream` — `supported` — runtime-native streaming (NDJSON)
- `POST /v1/chat/completions` — `supported` — OpenAI-style chat compatibility,
  with `stream=true` SSE
- `POST /v1/completions` — `supported` — OpenAI-style completions compatibility
- `POST /v1/messages` — `supported` — Anthropic-style messages compatibility
- `POST /v1/messages/count_tokens` — `supported` — Anthropic-style token count

### 3.3 Lifecycle And Inventory

- `POST /v1/load` — `supported` — load a model under runtime memory budget
- `POST /v1/unload` — `supported` — unload a model
- `POST /v1/runtime/restart` — `supported` — restart-action result contract
  (frozen `stage` / `retryable` fields; see runtime-capability-matrix entries
  for restartability truth)
- `GET /v1/openai/models` — `supported` — runtime-gated visibility list
- `GET /v1/models` — `supported` — loaded inventory with embedded
  `visibility_contract` block; see `runtime-model-visibility-contract.md`
- `GET /v1/runtime/model-visibility` — `supported` — diagnostic visibility
  contract surface
- `GET /v1/runtime/model-load-admission` — `supported` — model-specific
  load-admission projection; see `model-load-admission.md`
- `POST /v1/runtime/host-pressure-sample` — `supported` — explicit
  operator action that refreshes cached host-pressure admission truth without
  loading a model; see `model-load-admission.md`

### 3.4 Release-Floor Contract Surfaces

These read-only routes back the runtime-owned closure of release floors `3.2`,
`3.3`, `3.4`, and `3.5`. Each route returns the v1 contract serialization
documented in its source-of-truth file.

- `GET /v1/runtime/orchestration-status` — `supported` — see
  `orchestration-status-surface.md`
- `GET /v1/runtime/scheduler-admission-contract` — `supported` — see
  `scheduler-admission-contract.md`
- `GET /v1/runtime/request-context-length-truth` — `supported`
- `GET /v1/runtime/model-residency-policy` — `supported` — see
  `model-residency-policy.md`
- `GET /v1/runtime/memory-pressure-contract` — `supported` — see
  `memory-pressure-contract.md`
- `GET /v1/runtime/recovery-supervisor-contract` — `supported` — see
  `recovery-supervisor-contract.md`
- `GET /v1/runtime/nonresident-loadability-lineage` — `supported` — see
  `nonresident-loadability-lineage.md`
- `GET /v1/runtime/nonresident-model-admission-policy` — `supported` — see
  `nonresident-model-admission-policy.md`
- `GET /v1/runtime/memory-pressure-eviction-policy` — `supported` — see
  `memory-pressure-eviction-policy.md`
- `POST /v1/runtime/memory-pressure-eviction` — `supported` — runtime-owned
  execution path; refuses unless decision is `evict`
- `GET /v1/runtime/reclaim-barrier-event` — `supported` — see
  `reclaim-barrier-event.md`
- `GET /v1/runtime/termination-recovery-policy` — `supported` — see
  `termination-recovery-policy.md`
- `GET /v1/runtime/comparative-evidence` — `supported` — latest validated
  `comparative_evidence_record` v1 (or explicit `still_blocked` 503); see
  `comparative-evidence-harness-contract.md`
- `GET /v1/runtime/comparative-evidence/history` — `supported` — stable
  `comparative_evidence_record_history` v1 envelope
- `GET /v1/runtime/model-release-candidates` — `supported` — latest
  validated `model_release_candidate_record` v1 (or explicit
  `still_blocked` 503); see `model-release-candidate-program.md`
- `GET /v1/runtime/model-release-candidates/history` — `supported` — stable
  `model_release_candidate_record_history` v1 envelope

## 4. Supported Runtime Modules / Python APIs

The following Python modules are part of the supported surface for upper
layers that import `owlmlx` directly. Each module's public symbols are
documented in `runtime-capability-matrix.md`. Internal helper functions
(prefixed with `_`) are not part of the public surface even when they live
inside a supported module.

- `owlmlx.runtime` — `supported` — `RuntimeKernel`, `RuntimeBackend`,
  `FakeBackend`, `MlxLmBackend`/`MlxLmSubprocessBackend`
- `owlmlx.runtime.server` — `supported` — `create_app(...)`,
  `create_fake_app(...)`
- `owlmlx.runtime.technical_preview` — `supported` — side-by-side
  technical-preview app factory for the real `MlxLmSubprocessBackend`
  serving path; it does not stop or mutate legacy services
- `owlmlx.serving` — `supported` — `GenerationGate`
- `owlmlx.memory_budget` — `supported`
- `owlmlx.context_concurrency` — `supported`
- `owlmlx.abort_recovery` — `supported`
- `owlmlx.runtime_health` — `supported`
- `owlmlx.model_inventory` — `supported`
- `owlmlx.model_lineage` — `supported`
- `owlmlx.cache_truth` — `supported`
- `owlmlx.runtime_model_visibility` — `supported`
- `owlmlx.comparative_evidence_record` — `supported` —
  `build_comparative_evidence_record(...)`,
  `comparative_evidence_record_to_dict(...)`,
  `ComparativeEvidenceRecord`/`ComparativeEvidenceMeasurement`/`ComparativeEvidenceRuntime`
- `owlmlx.comparative_evidence_schema` — `supported` — frozen schema constants
  (`COMPARATIVE_EVIDENCE_RECORD_SURFACE`/`VERSION`, `WORKLOAD_CLASSES`,
  `RUNTIME_IDS`, `VERDICT_GRADES`, `BANNED_VERDICT_VOCABULARY`) and
  `validate_comparative_evidence_record(...)`
- `owlmlx.comparative_evidence_history` — `supported` —
  `ComparativeEvidenceLedger`, `still_blocked_payload(...)`,
  `history_envelope(...)`
- `owlmlx.comparative_evidence_runner` — `partial` — measured-runner
  primitives (`RuntimeRunnerConfig`, `WorkloadInputs`, `execute_attempt(...)`,
  `aggregate_runtime(...)`, `compute_verdict(...)`,
  `load_runner_config_file(...)`); the public shape is the JSON runner-config
  surface frozen in `comparative-evidence-harness-contract.md` §3 and the
  3.5D handoff
- `owlmlx.model_release_candidate_schema` — `supported` — frozen schema
  constants and `validate_model_release_candidate_record(...)`
- `owlmlx.model_release_candidate_record` — `supported` —
  `build_model_release_candidate_record(...)`,
  `build_dry_run_model_release_candidate_records(...)`, and
  `model_release_candidate_record_to_dict(...)`
- `owlmlx.model_release_candidate_history` — `supported` —
  `ModelReleaseCandidateLedger`, `model_release_candidate_still_blocked_payload(...)`,
  and `model_release_candidate_history_envelope(...)`
- `owlmlx.model_load_admission` — `supported` —
  `build_model_load_admission(...)` and
  `model_load_admission_to_dict(...)`
- `owlmlx.memory_pressure_eviction_policy` — `supported` —
  `build_memory_pressure_eviction_policy(...)`
- `owlmlx.nonresident_model_admission_policy` — `supported`
- `owlmlx.nonresident_loadability_lineage` — `supported`
- `owlmlx.recovery_supervisor_contract` — `supported`
- `owlmlx.termination_recovery_policy` — `supported`
- `owlmlx.reclaim_barrier_event` — `supported`
- `owlmlx.scheduler_admission_contract` — `supported`
- `owlmlx.orchestration_status` — `supported`
- `owlmlx.model_residency_policy` — `supported`
- `owlmlx.memory_pressure_contract` — `supported`
- `owlmlx.runtime_status` — `supported`

The full list of every `owlmlx.*` symbol is **not** part of this surface.
Modules not listed here are `internal` by default.

## 5. Supported Operator Scripts / CLIs

The following operator-facing scripts are part of the supported surface.
Their CLIs are stable; their internal helpers are not.

- `scripts/runtime_comparative_evidence.py` — `supported` — operator entry
  for the comparative-evidence record surface; subcommands
  `append-rejected-record`, `run-measured-short-prompt`, `latest`,
  `history`. See `comparative-evidence-harness-contract.md`
- `scripts/runtime_model_release_candidate.py` — `supported` — operator entry
  for the model release-candidate evidence surface; subcommands
  `dry-run-matrix`, `append-dry-run-matrix`, `latest`, `history`. See
  `model-release-candidate-program.md`
- `scripts/runtime_mlx_environment_readiness.py` — `supported`
- `scripts/runtime_mlx_blocker_report.py` — `supported`
- `scripts/runtime_mlx_host_forensics.py` — `supported`
- `scripts/runtime_mlx_probe_matrix.py` — `supported`
- `scripts/runtime_technical_preview_server.py` — `supported` — operator
  entry for side-by-side owlmlx technical-preview serving with the real
  MLX subprocess backend; it does not stop legacy `oMLX` or router services
- `scripts/runtime_large_weight_specimen_gate.py` — `supported`
- `scripts/runtime_large_weight_first_smoke.py` — `supported`
- `scripts/runtime_large_weight_first_smoke_decision.py` — `supported`

## 6. Supported Source-Of-Truth Contracts

The following documents are part of the public truth surface. Other documents
under `docs/source-of-truth/` are owlmlx-internal truth and may change.

- `AGENTS.md`
- `docs/source-of-truth/repository-boundaries.md`
- `docs/source-of-truth/runtime-capability-matrix.md`
- `docs/source-of-truth/runtime-contracts.md`
- `docs/source-of-truth/runtime-status-schema.md`
- `docs/source-of-truth/runtime-governance.md`
- `docs/source-of-truth/hazardous-operations.md`
- `docs/source-of-truth/comparative-evidence-harness-contract.md`
- `docs/source-of-truth/comparative-evidence-schema-stub.md`
- `docs/source-of-truth/model-release-candidate-program.md`
- `docs/source-of-truth/deepseek-v4-flash-adapter-optimization-candidate.md`
- `docs/source-of-truth/release-readiness-backlog.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `docs/source-of-truth/orchestration-status-surface.md`
- `docs/source-of-truth/scheduler-admission-contract.md`
- `docs/source-of-truth/model-residency-policy.md`
- `docs/source-of-truth/memory-pressure-contract.md`
- `docs/source-of-truth/model-load-admission.md`
- `docs/source-of-truth/memory-pressure-eviction-policy.md`
- `docs/source-of-truth/recovery-supervisor-contract.md`
- `docs/source-of-truth/termination-recovery-policy.md`
- `docs/source-of-truth/reclaim-barrier-event.md`
- `docs/source-of-truth/nonresident-model-admission-policy.md`
- `docs/source-of-truth/nonresident-loadability-lineage.md`
- `docs/source-of-truth/runtime-model-visibility-contract.md`
- `docs/source-of-truth/training-substrate-contract.md`
- `docs/source-of-truth/training-to-serving-contract.md`
- `docs/source-of-truth/artifact-layout-contract.md`
- `docs/source-of-truth/large-weight-path-truth.md`

## 7. Public Consumer Rules

Consumers of the supported surface must:

- consume runtime truth from the supported HTTP routes and modules; do not
  invent values that the runtime does not expose
- treat the `verdict_text` and `verdict_grade` of any comparative-evidence
  record as opaque; never re-render it under banned vocabulary (see §10)
- treat `summary` / stable-sections of `/v1/runtime/status` as
  field-stable; treat the diagnostic sections as best-effort detail and
  never fail closed on a missing diagnostic field
- pass model identity through `model_id` per
  `runtime-model-visibility-contract.md`; do not invent model ids that the
  visibility list does not expose

Consumers may not:

- bypass the `GenerationGate` boundary (single-worker, ticketed-FIFO)
- depend on internal cache phase45 exactness contracts (see §10)
- must not promote any `verdict_grade = "rejected"` or `"inconclusive"` record into a release / parity / replacement claim

## 8. Internal-Only Surfaces

Everything not listed in §3 / §4 / §5 / §6 is `internal` by default. The
following are explicitly internal at the time of this freeze:

- the entire `scripts/runtime_cache_*.py` family (≈80 phase45 exactness
  operator entries) — their underlying contracts are observation-grade
  internal phase45 truth tracking, not consumer-facing API
- the `scripts/runtime_multi_model_governance_*` family — `partial`
  observation surfaces for governance status, transition ledger, controls,
  and policy gap; usable for owlmlx-internal coordination but not part of
  the public surface in this freeze
- all `owlmlx.cache_*` modules (pre-claim marker exactness, admission carrier
  exactness, scheduler/TurboQuant split surfaces, request-aggregation
  exactness, etc.)
- all `phase45-*.md` source-of-truth files
- all `docs/source-of-truth/phase45-*` docs except those linked from §6
- the runtime kernel's `_*` private methods (`_record_*`, `_resolve_*`,
  `_ttl_*`, `_pinned_*`, etc.); only the public `RuntimeKernel.<method>` API
  is supported
- the comparative-evidence runner's per-attempt artifact internal layout
  beyond what `comparative-evidence-harness-contract.md` and the 3.5D
  handoff freeze

Internal surfaces may be exposed temporarily by tests or scripts. That does
not promote them to `supported`.

## 9. External Live Reference Runtimes

`omlx` and `vmlx` are reference runtimes per `repository-boundaries.md` §4.
They are `not in scope` for owlmlx ownership; the comparative-evidence
harness invokes them as caller-supplied subprocess argv (see
`comparative-evidence-harness-contract.md`). Their CLIs, packaging, and
capability surface are owned upstream, not by owlmlx.

## 10. Explicitly Unsupported Claims

The following claims are **never** part of the supported surface, regardless
of which floors are closed:

- `release-ready`
- `parity` (with `oMLX`, `vMLX`, or any other runtime)
- `replaces` / `replacement`
- `production-grade`
- `production-ready`
- `superior` / `wins` / `beats` / `matches`
- `equivalent`

These mirror `BANNED_VERDICT_VOCABULARY` in
`owlmlx.comparative_evidence_schema` and the §4.3 hard rule of
`release-readiness-backlog.md`. Both are enforced at runtime: any record whose
`verdict_text` matches a banned word fails schema validation.

The current honest interim claims are exactly:

- `early formal runtime`
- `internal source-of-truth project`
- `technical preview`

This document does not by itself promote owlmlx to release-ready. The 7 / 7
release-floor closure is a technical-preview signoff boundary, not a release,
parity, replacement, production-grade, or superiority verdict.

## 11. Versioning And Change Rule

This freeze is `v1`. The change rule:

- additive changes (new supported routes, new supported modules, new
  supported scripts) may land in any subsequent round, with the new entry
  added under §3 / §4 / §5 / §6 and the `Updated:` date bumped
- breaking changes (removal of a supported route, change of a frozen
  schema field, narrowing of a supported module's public API) require:
  - a new top-level §X "Breaking Change History" entry naming the change,
    the affected surface, and the migration target
  - a deprecation cycle of at least one release where both the old and
    new shapes are served, unless an existing source-of-truth document
    has already deprecated the surface
- `internal` surfaces may move to `partial` / `supported` in any round
  once they meet the promotion criteria in `extraction-inventory.md` §8
- `supported` surfaces may be downgraded to `partial` or `experimental`
  only with a frozen reason in this document and a backlog entry

## 12. Restart Condition

This document is reopened when:

- a new `supported` HTTP route, runtime module, or operator script is added
- an existing `supported` surface is downgraded or retired
- a new release floor closes (e.g. `3.6`) and that closure adds new
  consumer-facing truth that belongs on the public surface
- the `BANNED_VERDICT_VOCABULARY` enumeration changes (in
  `owlmlx.comparative_evidence_schema`) or an interim claim is added /
  retired

Schedule pressure is not a reopen reason.
