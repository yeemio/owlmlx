# owlmlx Runtime Capability Matrix

> Status: authoritative
> Updated: 2026-04-25

Capability labels:

- `supported`
- `partial`
- `experimental`
- `not in scope`

## 1. owlmlx Core Supported Capabilities

| Capability | Label | Notes |
|---|---|---|
| Runtime identity as self-owned project | supported | This repository exists to freeze that boundary |
| Runtime architecture truth | supported | Core documents define the architecture boundary |
| Executable runtime kernel MVP | supported | Runtime-0 established `RuntimeKernel`, `RuntimeBackend`, `FakeBackend`, `MlxLmBackend`, and minimal HTTP app; Runtime-2 extends this to persistent child MLX sessions |
| Memory governance under multi-model switching | supported | Formal runtime principle |
| Switch safety and active-request protection | supported | Formal runtime principle |
| Runtime truth exposure as owned requirement | supported | Upper layers should consume runtime truth rather than invent it |
| Background-heavy serving as a runtime class | supported | Formal runtime principle, even though path maturity differs |
| Hazardous-operation governance | supported | Runtime-risking work belongs to runtime governance |
| Safe-resume contract as runtime governance | supported | Controlled re-entry is part of runtime truth |
| Training-to-serving contract (load path, feasibility, truth surfaces) | supported | Frozen in training-to-serving-contract.md; feasibility checklist, runtime status extension |
| Artifact layout contract (tuned artifact paths, naming, registration) | supported | Frozen in artifact-layout-contract.md; run-id naming, metadata.json registration |
| Training substrate contract (environment, stack, boundary) | supported | Frozen in training-substrate-contract.md; MLX native primary, PyTorch fallback |
| Training architecture verification rule | supported | Model must pass 5-step LoRA pilot before entering substrate |
| Serving-path memory budget truth | supported | `owlmlx/memory_budget.py` — MachineMemoryProfile, evaluate_model_fit, budget_snapshot with 32 tests; **platform consumes** via `control_service.py` |
| Serving-path context concurrency truth | supported | `owlmlx/context_concurrency.py` — CONCURRENCY_GATE, max_concurrency_for_context, gate_entry_for_context, is_high_context, concurrency_gate_snapshot with 34 tests; **platform consumes** via `context_concurrency_policy.py` |
| Serving-path abort recovery state machine | supported | `owlmlx/abort_recovery.py` — SubstrateState, AbortEvent, AbortRecoveryTracker with 31 tests; **platform consumes** via `abort_recovery.py` delegating to `AbortRecoveryTracker` |
| Serving-path runtime health semantics | supported | `owlmlx/runtime_health.py` — LoadState, InferenceHealth, WaitTier, TruthLevel, RuntimeReadiness, PlatformStatus enums + derive_wait_tier, derive_runtime_readiness, derive_platform_status, derive_block_reason, is_model_ready, runtime_health_snapshot with 85 tests; **platform consumes** via `metrics.py` using `model_inventory.inventory_health_snapshot()` and importing `derive_platform_status()` |
| Serving-path model inventory registry | supported | `owlmlx/model_inventory.py` — LoadedModelEntry, ModelInventorySnapshot, loaded-memory aggregation, budget integration, runtime-health integration with 18 tests; **platform consumes** via `metrics.py` and `control_service.py` building inventory snapshots |
| Served-model lineage schema | supported | `owlmlx/model_lineage.py` — ModelLineage, validation, truth inheritance derivation, training-artifact bridge with 20 tests; **platform consumes** via `primary_line_status.py` normalizing and validating catalog lineage |
| Cache truth contract | supported | `owlmlx/cache_truth.py` — cache profile labels, flag schema, restart-required derivation, and TurboQuant cache-safety rules with 22 tests; **platform consumes** via `distilled_cache_substrate.py` and `primary_line_status.py` |
| Fully self-owned implementation stack | partial | Eleven truth modules plus Runtime-3 executable kernel exist; persistent child MLX sessions and streamed kernel serving are real, but production serving, eviction/reclaim, and platform migration remain open |
| Queue-based generation gate (owlmlx-owned) | supported | `owlmlx/serving.py` — GenerationGate class with 11 tests; enforces validated concurrency boundary |
| Single-host orchestration status surface | supported | `owlmlx/orchestration_status.py` plus `GET /v1/runtime/orchestration-status` now freeze one runtime-owned layer-assessment contract for admission / generation gate / stream hold / model residency / memory pressure / recovery without inflating the weaker layers past `partial` or `insufficient_signal` |
| Single-host recovery supervisor contract | supported | `owlmlx/recovery_supervisor_contract.py` plus `GET /v1/runtime/recovery-supervisor-contract` now freeze recovery barrier classification from backend health, restart exhaustion, and abort-recovery substrate state without claiming an automatic recovery loop or pressure eviction policy |
| Request context-length truth for admission | supported | `owlmlx/request_context_length_truth.py` plus `GET /v1/runtime/request-context-length-truth` classify explicit context-token truth as `high_context`, `non_high_context`, or `unknown` for admission support without claiming tokenizer parity or generation enforcement |
| Formal adoption model (reuse open-source, own truth layer) | supported | Adoption rule frozen in product-definition section 6 |
| Extraction discipline with wave ordering | supported | Discipline rules frozen in extraction-inventory section 3 |
| Autonomous loop discipline for self-iteration | supported | Loop discipline frozen in autonomous-loop-discipline.md |

## 2. Large-Weight Path Supported Capabilities

| Capability | Label | Notes |
|---|---|---|
| Large-weight runtime path exists | supported | First mature path inside `owlmlx` |
| Background-heavy serving posture | supported | Honest current direction |
| Honest specimen-specific capability labels | supported | Path should not overclaim from a single specimen |
| Path naming independent of one model | supported | `Kimi` is not the permanent path name |
| Single-worker queue-based serving | supported | Validated through K-Q4c; generation lock serializes safely |
| Same-process parallel generation unsafe | supported | MLX/Metal substrate limitation; boundary = 1 |
| Linear memory scaling for layer loading | supported | Validated 1→61 layers; no superlinear accumulation |
| Heavy execution protocol field-validated | supported | K-Q3a→K-Q4d escalation proved the protocol |

## 3. Specialized-Only Capabilities

| Capability | Label | Notes |
|---|---|---|
| `Kimi` as first validated specimen | supported | Historical and architectural milestone |
| Specimen-specific runtime behavior | partial | Must not be confused with core runtime truth |
| Borrowed implementation auto-promoted to supported | not in scope | Adoption model explicitly rejects silent promotion |
| A specimen proving a path can exist | supported | Does not automatically generalize to other specimens |

## 4. Future Or Not Yet Established

| Capability | Label | Notes |
|---|---|---|
| Generalized foreground-interactive runtime | experimental | Not yet established as current truth |
| Additional runtime paths beyond large-weight | experimental | Future only when real capability truth exists |
| Real MLX model load/generate through owlmlx | supported | `MlxLmSubprocessBackend` has real successful local smokes through the clean `.runtime1-mlx` environment on `gpt-oss-20b-MXFP4-Q4`, `Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit`, and `Qwen3.5-35B-A3B-4bit`; Runtime-2 further proves persistent child reuse on `gpt-oss-20b` and `Qwen3.5-27B` and has a steady-state benchmark script |
| DeepSeek V4 Flash 2bit-DQ adapter optimization | experimental | `DeepSeek-V4-Flash-2bit-DQ` is a 284.3B-parameter, about-90G local MLX artifact with a first short generation smoke through an isolated DeepSeek V4 PR runtime; it is not yet visible on the technical-preview `GET /v1/openai/models` surface and is tracked by `deepseek-v4-flash-adapter-optimization-candidate.md` plus `model-release-candidate-program.md` |
| Persistent child health probe | supported | Backend `status()` actively issues `ping` to live child sessions and surfaces `child_health` in status detail |
| Dead child restart policy | supported | Registration survives child death; the next generation request can restart the child session within configured restart-attempt limits |
| Explicit runtime restart surface | supported | `POST /v1/runtime/restart` restarts one loaded model through `RuntimeKernel.restart_model()` |
| Serialized concurrent serving validation | supported | `scripts/runtime3_serialized_concurrency_check.py` proves `GenerationGate` remains serial under real concurrent requests against one persistent child session |
| Real streaming response path | supported | `POST /v1/generate/stream` streams NDJSON events through `RuntimeKernel.generate_stream()`; real local smoke verified on `gpt-oss-20b-MXFP4-Q4` |
| Same-model benchmark comparison against old platform | supported | `scripts/runtime3_platform_benchmark_compare.py` replays the old platform benchmark prompts through Runtime-3 and freezes same-model deltas |
| OpenAI-style migration seam | supported | `POST /v1/chat/completions` provides a minimal compatibility surface for upper-layer migration |
| SSE streaming compatibility surface | supported | `POST /v1/chat/completions` with `stream=true` emits `text/event-stream` chunks plus terminal `[DONE]` |
| Runtime-native chat message path | supported | Structured messages now flow through `RuntimeKernel.generate_messages()` and backend-native message handling instead of server-only prompt flattening |
| OpenAI-style completions compatibility surface | supported | `POST /v1/completions` now provides prompt-style non-stream and SSE streaming compatibility |
| Anthropic-style messages entrypoint | supported | `POST /v1/messages` now provides Anthropic-compatible non-stream and SSE event semantics for owlcoda/owlcc-style clients |
| Anthropic count-tokens entrypoint | supported | `POST /v1/messages/count_tokens` returns estimated `input_tokens` for Anthropic-compatible clients |
| First real Owl consumer cutover proof | supported | `owlcc run` now completes a real direct-endpoint tool loop against `owlmlx /v1/messages`; Runtime-7 freezes the first real consumer cutover verdict |
| First real OwlCoda cutover proof | supported | `owlcoda` native/headless and `owlcoda --native` REPL now both consume `owlmlx /v1/messages`; Runtime-8 adds resumed session continuation and first control-plane seam |
| Source-first OwlCoda cutover | supported | Runtime-9 proves the upstream source-first prompt path can execute through `owlcoda serve -> owlmlx /v1/messages` with local runtime protocol auto-detected as Anthropic Messages |
| Source-first OwlCoda tool-loop parity | partial | Runtime-10 proves a real source-first tool loop against `owlmlx`; stronger than prompt-only cutover, but still not full source-first parity |
| OwlCoda control-plane operability against direct owlmlx | supported | Runtime-9 promotes runtime probe, preflight, server health, and dry-run to consume `/v1/runtime/status` as first-class truth |
| Frozen upstream runtime status contract | supported | Stabilization-1 freezes `/v1/runtime/status` with explicit `contract.version`, stable sections (`summary`, `health`, `inventory`, `budget`, `restart`), and diagnostic-only sections for upper-layer consumers |
| Frozen healthz liveness contract | supported | Stabilization-1 also freezes `GET /healthz` as a small liveness/readiness contract with explicit `contract.version`, `runtime`, `backend_name`, `ok`, and `readiness` |
| Restartability truth for persistent-child failure modes | supported | Stabilization-1 promotes restartability into explicit runtime truth via `restart.restartable_models` and `restart.restart_exhausted_models`, backed by child-death / restart-budget tests |
| Stable restart action result contract | supported | Stabilization-1 freezes `POST /v1/runtime/restart` result semantics with explicit `stage` (`preflight` / `unload` / `load` / `completed`) and `retryable` fields |
| Runtime-only restart-cycle reliability harness | supported | Stabilization-1 adds repeated load -> generate -> restart -> unload cycle coverage plus structured `/v1/messages` streaming error verification |
| MLX environment readiness contract | supported | Stabilization-2 promotes `mlx_environment` into a stable runtime-owned contract with explicit readiness, selected executable, execution mode, quarantine count, and a verified-baseline registry; `runtime_mlx_environment_readiness.py` and `register_verified_mlx_baseline.py` are the operator entries |
| Large-weight specimen pre-smoke gate | supported | Stabilization-2 adds a stable runtime-owned gate that combines specimen-path truth with MLX environment readiness before first smoke; `scripts/runtime_large_weight_specimen_gate.py` is the operator entry |
| Large-weight first-smoke flow | supported | Stabilization-2 formalizes `scripts/runtime_large_weight_first_smoke.py` so future specimens enter validation through one gate-first flow instead of ad-hoc shell sequences |
| Machine-level MLX import blocker report | supported | Stabilization-2 adds `owlmlx.mlx_blocker_report` so operator-facing tooling can consume the current machine blocker as stable truth instead of scraping readiness scripts; `scripts/runtime_mlx_blocker_report.py` is the operator entry |
| Large-weight first-smoke locality decision | supported | Stabilization-3 adds `owlmlx.large_weight_first_smoke_decision`, combining default-Metal gate, force-CPU gate, and host forensics into one runtime-owned answer for whether local first smoke may proceed or should move to another host/system image |
| Host-stable execution status | supported | Phase 45 adds `owlmlx.host_stable_execution`, giving a direct host-level answer for whether this machine is a valid candidate for deeper replacement-grade runtime validation |
| Cache/scheduler depth status | supported | Phase 45 adds `owlmlx.cache_scheduler_status`, combining serialized scheduler truth, cache profile truth, and TurboQuant cache-safety truth into one honest runtime-owned contract for the current closure level |
| Cache residency/reuse evidence surface | supported | Phase 45 adds `owlmlx.cache_residency_evidence`, allowing the runtime to express whether cache evidence is absent, configuration-only, under-load, residency-visible, or reuse-visible without overclaiming parity |
| Cache repeatability evidence surface | supported | Phase 45 adds `owlmlx.cache_repeatability_evidence`, allowing the runtime to express whether cache evidence survives repeated serving as profile-only activity, residency, reuse, or eviction signals |
| TurboQuant readiness surface | supported | Phase 45 adds `owlmlx.turboquant_readiness`, separating cache-safety truth from repeated-serving evidence and making controlled TurboQuant validation an explicit runtime-owned readiness decision |
| Cache closure rung | supported | Phase 45 adds `owlmlx.cache_closure_rung`, combining scheduler truth, cache evidence, repeatability evidence, and TurboQuant readiness into one conservative partial-closure verdict |
| Cache counter gap | supported | Phase 45 adds `owlmlx.cache_counter_gap`, freezing when the remaining cache blocker is no longer observation-grade and has narrowed to exact missing runtime-owned counters plus serial-only scheduler depth |
| Cache counter feasibility | supported | Phase 45 adds `owlmlx.cache_counter_feasibility`, freezing which counters are actually runtime-owned on the active path and shifting the next cache closure step toward scheduler depth / TurboQuant when counter ownership is already exact |
| Cache scheduler/TurboQuant split | supported | Phase 45 adds `owlmlx.cache_scheduler_turboquant_split`, freezing the remaining cache work as an exact split between scheduler depth and TurboQuant preconditions once counter ownership is no longer the active blocker |
| Cache scheduler floor gap | supported | Phase 45 adds `owlmlx.cache_scheduler_floor_gap`, freezing the active-path scheduler branch as a serial single-worker floor (`queue_discipline=serial`, `max_concurrent=1`) so further cache closure can move from split truth to scheduler implementation truth |
| Cache scheduler implementation backlog | supported | Phase 45 adds `owlmlx.cache_scheduler_implementation_backlog`, freezing the exact scheduler-grade remaining work (`continuous_batching`, `multi_worker_scheduler_depth`) once the serial floor and ticketed FIFO queue policy are already exact |
| Cache scheduler branch selection | supported | Phase 45 adds `owlmlx.cache_scheduler_branch_selection`, freezing `continuous_batching` as the next locally reducible scheduler branch while `multi_worker_scheduler_depth` stays secondary until concurrency safety is revalidated |
| Cache continuous-batching feasibility | supported | Phase 45 adds `owlmlx.cache_continuous_batching_feasibility`, freezing continuous batching as exact-feasibility-blocked on the active path until request aggregation or interleaved scheduling exists |
| Cache batching mechanism subgap | supported | Phase 45 adds `owlmlx.cache_batching_mechanism_subgap`, freezing `request_aggregation_window` as the next exact local mechanism while shared prefill and decode interleaving stay secondary |
| Cache request-aggregation exactness | supported | Phase 45 adds `owlmlx.cache_request_aggregation_window_exactness`; current live truth is now post-ingress: a bounded pre-gate cohort window forms before whole-request gate claim, one non-stream child exchange can already carry multiple requests, and the remaining blocker is cohort-to-child handoff while stream hold stays secondary |
| Cache pre-gate cohort-window feasibility | supported | Phase 45 adds `owlmlx.cache_pre_gate_cohort_window_feasibility`, and current live truth now freezes that a bounded runtime-owned cohort/admission seam exists before `GenerationGate` claim on the active path |
| Cache pre-gate admission-hook exactness | supported | Phase 45 adds `owlmlx.cache_pre_gate_admission_hook_exactness`; current live truth now freezes that the bounded hook has widened into a real pre-claim cohort window while post-claim serial invariants remain frozen |
| Cache request-aggregation active seam | supported | Phase 45 adds `owlmlx.cache_request_aggregation_active_seam`; current live seam is now `cohort_to_child_exchange_handoff_dependency` after ingress and child-exchange capability have both narrowed |
| Cache child-exchange aggregated-dispatch exactness | supported | Phase 45 adds `owlmlx.cache_child_exchange_aggregated_dispatch_exactness`, freezing that one non-stream child exchange can already carry multiple requests while the main serving path still lacks cohort-to-child handoff |
| Cache admission-hook safety contract | supported | Phase 45 adds `owlmlx.cache_admission_hook_safety_contract`, freezing the exact post-claim invariants and forbidden bypasses any future pre-claim hook must preserve |
| Bounded pre-gate admission structural ingress seam | experimental | Phase 45 now introduces a real bounded pre-gate hook in `owlmlx/serving.py`; it stages only immutable metadata, ticket reservation, and pre-claim bookkeeping before gate claim and does not imply batching parity |
| Cache pre-claim admission contract | supported | Phase 45 adds `owlmlx.cache_pre_claim_admission_contract`, freezing that the only allowable future pre-claim seam is bounded metadata/ticket staging before whole-request gate claim, with no gate claim, child exchange, stream start, or model execution allowed there |
| Cache pre-claim staging seam exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_staging_seam_exactness`, freezing that only immutable request metadata plus ticket reservation may be staged pre-claim, while gate ownership transfer, child payload assembly, stream-handle allocation, and model state/prefill remain outside that seam |
| Cache pre-claim metadata/ticket ownership | supported | Phase 45 adds `owlmlx.cache_pre_claim_metadata_ticket_ownership`, freezing that ticket reservation is observational-only and immutable request metadata is read-only before gate claim, with no promotion into child, stream, or model-execution state |
| Cache pre-claim inert-state semantics | supported | Phase 45 adds `owlmlx.cache_pre_claim_inert_state_semantics`, freezing that the only allowed inert semantics before gate claim are drop/cancel markers, while cohort membership, execution priority, and prefill-batch membership remain unavailable |
| Cache pre-claim marker lifetime | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_lifetime`, freezing that inert drop/cancel markers may exist only until explicit pre-claim discard or whole-request gate claim, with no queue ownership or post-claim execution entitlement flowing from marker lifetime |
| Cache pre-claim marker visibility | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_visibility`, freezing that inert markers are visible only to pre-claim discard logic and gate-claim expiry logic, with no leakage into scheduler selection, child dispatch, stream handling, or execution-priority paths |
| Cache pre-claim marker trigger inputs | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_trigger_inputs`, freezing that inert markers may be cleared only by explicit pre-claim drop/cancel signals or gate-claim expiry, while scheduler pressure, child/backend, stream, and execution-priority inputs remain unavailable as pre-claim triggers |
| Cache pre-claim marker reader/writer ownership | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_reader_writer_ownership`, freezing that only explicit pre-claim drop/cancel logic and gate-claim expiry may author a marker, while pre-claim discard is observer-only and scheduler/child/stream/execution-priority paths remain ineligible as writers |
| Cache pre-claim marker state-carrier | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_state_carrier`, freezing that a marker may live only in one inert write-once/clear-only record before gate claim and that the carrier may not become queue slot identity, batch membership, child payload attachment, or stream/execution state |
| Cache pre-claim marker clear/observer boundary | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_clear_observer_boundary`, freezing that only explicit pre-claim drop/cancel logic and gate-claim expiry may clear the inert carrier, while pre-claim discard remains observer-only and scheduler/child/stream/execution-priority paths remain ineligible as clearers |
| Cache pre-claim marker immutability boundary | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_immutability_boundary`, freezing that pre-claim marker state may change only by clear-only semantics and may not rewrite payload, priority, queue membership, or child/stream/execution state before gate claim |
| Cache pre-claim marker payload-shape exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_payload_shape_exactness`, freezing that pre-claim marker state collapses to pure presence/absence only and may not carry reason-code, priority, queue-metadata, or child/stream/execution payload fields before gate claim |
| Cache pre-claim marker encoding-carrier exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_encoding_carrier_exactness`, freezing that pre-claim marker presence may live only in one inert boolean slot and that the slot may not encode queue identity, ticket identity, child payload, or stream/execution handles before gate claim |
| Cache pre-claim marker storage-locality exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_storage_locality_exactness`, freezing that the inert boolean marker slot may live only adjacent to staged metadata and outside ticket identity / immutable metadata payload, and may not occupy queue, scheduler, child, stream, or execution-local storage before gate claim |
| Cache pre-claim marker locality-access exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_locality_access_exactness`, freezing that only explicit pre-claim drop/cancel logic, gate-claim expiry, and pre-claim discard observation may reach the adjacent inert slot before gate claim, while scheduler, child/backend, stream, and execution-priority paths remain ineligible |
| Cache pre-claim marker locality-isolation exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_locality_isolation_exactness`, freezing that the adjacent inert marker slot is isolated per staged request and that no shared pending-state scheduler/backend/stream locality or cross-request marker merge may exist before gate claim |
| Cache pre-claim marker locality-lifetime coupling | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_locality_lifetime_coupling`, freezing that the isolated adjacent marker slot is coupled only to its own staged-request lifetime, reclaimed only by same-request pre-claim discard or gate-claim expiry, and may not survive into cross-request reuse or retained ownership |
| Cache pre-claim marker reclaim-reset exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_marker_reclaim_reset_exactness`, freezing that reclaim returns the adjacent marker slot to a fully empty inert state, leaves no prior request history visible, and permits later reuse only after a clean inert reset |
| Cache pre-claim admission-carrier construction | supported | Phase 45 adds `owlmlx.cache_pre_claim_admission_carrier_construction`, freezing that any bounded pre-claim carrier may be constructed only from immutable request metadata, observational ticket reservation, and a fully reset inert marker slot, with no queue-owned or execution-bearing carrier before gate claim |
| Cache pre-claim admission-carrier field exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_admission_carrier_field_exactness`, freezing that a bounded pre-claim carrier may hold only immutable request metadata, observational ticket reservation, and a fully reset inert marker presence bit, with no queue identity, scheduler priority, batch membership, child/stream attachment, or execution-bearing field before gate claim |
| Cache pre-claim admission-carrier encoding exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_admission_carrier_encoding_exactness`, freezing that those inert fields may be encoded only as one bounded inert pre-claim record, with no queue identity, scheduler priority, batch membership, child/stream attachment, or execution-bearing encoding before gate claim |
| Cache pre-claim admission-carrier locality exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_admission_carrier_locality_exactness`, freezing that the bounded inert pre-claim record may live only in single-request staged locality adjacent to metadata/ticket state before gate claim, and may not occupy queue, scheduler, child/stream, or execution-owned locality |
| Cache pre-claim admission-carrier locality-access exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_admission_carrier_locality_access_exactness`, freezing that only staged metadata snapshot building, observational ticket reservation, same-request pre-claim drop/cancel reset, and same-request pre-claim discard observation may reach the bounded inert pre-claim carrier before claim, while queue/cohort scheduler, child/backend payload, stream-handle, and execution-entitlement paths remain ineligible |
| Cache pre-claim admission-carrier locality-isolation exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_admission_carrier_locality_isolation_exactness`, freezing that the bounded inert pre-claim carrier remains isolated per staged request before claim and that no shared scheduler/backend/stream pending-state carrier locality or cross-request carrier merge may exist |
| Cache pre-claim admission-carrier locality-lifetime coupling | supported | Phase 45 adds `owlmlx.cache_pre_claim_admission_carrier_locality_lifetime_coupling`, freezing that the bounded inert pre-claim carrier is coupled only to its own staged-request lifetime before claim, reclaimed only by same-request pre-claim discard or gate-claim expiry transition, and may not survive into cross-request reuse or retained scheduler/backend/stream lifetime |
| Cache pre-claim admission-carrier reclaim-reset exactness | supported | Phase 45 adds `owlmlx.cache_pre_claim_admission_carrier_reclaim_reset_exactness`, freezing that reclaim returns the bounded inert pre-claim carrier to a fully empty inert state, leaves no prior request history or execution-bearing residue visible, and permits later staged reuse only after that clean reset |
| Cache pre-claim admission-carrier branch reselection | supported | Phase 45 adds `owlmlx.cache_pre_claim_admission_carrier_branch_reselection`, freezing that the admission-carrier exactness chain is complete on the current path and that the next honest cache reduction target moves back to scheduler-vs-TurboQuant branch reselection |
| Cache scheduler-vs-TurboQuant branch reselection | supported | Phase 45 adds `owlmlx.cache_scheduler_turboquant_branch_reselection`, freezing that scheduler depth is the selected next cache branch on the current path, that the selected scheduler sub-branch remains `continuous_batching`, and that TurboQuant stays exact-but-secondary |
| Cache continuous-batching branch reduction | supported | Phase 45 adds `owlmlx.cache_continuous_batching_branch_reduction`, freezing that scheduler depth remains the selected cache branch on the current path, that `continuous_batching` remains the selected scheduler sub-branch, and that `request_aggregation_window` is the next exact reduction target while other batching mechanisms stay secondary |
| Cache TurboQuant preconditions gap | supported | Phase 45 adds `owlmlx.cache_turboquant_preconditions_gap`, freezing the exact missing TurboQuant safe-activation requirements (`bits_in_cache_key`, `invalidates_on_config_toggle`, `runtime_verified`) instead of leaving the branch at a generic `safety_blocked` label |
| Dominant-gap reselection surface | supported | Phase 45 adds `owlmlx.dominant_gap_reselection`, freezing which locally reducible gap should be worked next once cache/gov/heavy-weight branches are already exact enough to compare honestly |
| Multi-model governance status | supported | Phase 45 adds `owlmlx.multi_model_governance_status`, exposing live resident-model count, active/default semantics, recoverability visibility, and absent controls such as pinning/TTL/eviction history |
| Multi-model governance controls | supported | Phase 45 adds `owlmlx.multi_model_governance_controls`, separating present controls from absent ones and making active-reassignment / explicit-targeting / restart-restore evidence runtime-owned via `runtime.status.governance_observations` when present |
| Multi-model governance transition ledger | supported | Phase 45 adds `owlmlx.multi_model_governance_transition_ledger`, freezing recent governance transitions and repeated transition evidence without inflating absent lifecycle controls into fake policy support; the current source is the active kernel's `governance_observations` when available |
| Multi-model governance policy gap | supported | Phase 45 adds `owlmlx.multi_model_governance_policy_gap`, freezing whether the remaining governance blocker is still observation-grade, still policy-grade exact, or now locally policy-closed on this host |
| Multi-model pinning control | supported | Phase 45 adds `owlmlx.multi_model_pinning_control`; `RuntimeKernel` owns `pin_model()` / `unpin_model()`, pinned unload is blocked on the runtime-owned path, and pin state survives restart |
| Multi-model TTL policy control | supported | Phase 45 now adds `owlmlx.multi_model_ttl_policy_control`; `RuntimeKernel` owns `set_model_ttl()` / `clear_model_ttl()` / `sweep_expired_models()`, TTL activity touches are runtime-owned, expired pinned models remain blocked, and unpinned expired models can be explicitly swept |
| Multi-model eviction-history governance | supported | Phase 45 adds `owlmlx.multi_model_eviction_history_governance`; runtime-owned eviction history now records both TTL unload and pinned-expiry skip events, closing the local governance fallback policy branch on this host |
| Heavy-weight repeatability status | supported | Phase 45 adds `owlmlx.heavy_weight_runtime_repeatability`, combining host stability, first-smoke locality, and supported-host repeatability proof into one exact blocker-aware status |
| Customer runtime evidence ledger | supported | Phase 45 adds `owlmlx.customer_runtime_evidence`, summarizing which replacement-grade gaps now have runtime-owned contracts, runnable verification, exact external blockers, and the next locally reducible dominant gap |
| Control-plane downgrade-path hardening | supported | Runtime-10 makes `healthz` a liveness-only fallback; it no longer fabricates `openai_chat` protocol when richer runtime truth is absent |
| Runtime model visibility contract | supported | `owlmlx/runtime_model_visibility.py` now freezes owlmlx-owned rule `runtime_gate_required_before_visible`: `GET /v1/openai/models` is the formal visibility list, `GET /v1/runtime/model-visibility` is the diagnostic contract surface, and `GET /v1/models` remains loaded inventory with an embedded `visibility_contract` block; the gate is owlmlx registry plus `$MODELS_ROOT/{model-id}/config.json` presence rather than router lifecycle curation; see `runtime-model-visibility-contract.md` |
| Degraded local routing now fails closed | supported | Runtime-11 blocks `localRuntimeProtocol=auto` when only `/healthz` is reachable; it no longer silently falls through to `/v1/chat/completions` for local models |
| Replacement readiness verdict surface | supported | Runtime-12 promotes replacement readiness into explicit `doctor` output with a blocker list; launch readiness and replacement readiness are now distinct control-plane truths |
| Old platform production replacement verdict | partial | Runtime-9 now freezes a real verdict: not yet replaceable; prompt-path cutover and first control-plane operability are proven, full parity and production closure are not |
| Overflow / NVMe-tier execution path | experimental | Future candidate only; Hypura recorded as external reference in `hypura-overflow-path-reference.md`, not adopted |
| High-fidelity teacher/reference runtime path | experimental | Candidate direction; Gemma has moved to production mainline instead |
| `gemma-4-31B-it` as production mainline | supported | Production mainline frozen; pilot LoRA PASS; substrate contracts exercised end-to-end |
| Platform capability absorption inventory | supported | Gap-driven inventory frozen; 8 gaps identified, 14 non-candidates excluded |
| Fully internalized replacements for all external runtime mechanisms | partial | Directional goal, not current fact |
| Full-rewrite of every execution layer | not in scope | Adoption model explicitly rejects this as unnecessary |
| External runtime features observed but not adopted | not in scope | External reference is not `owlmlx` support |
| Hypura as an adopted owlmlx backend | not in scope | Current label is external-reference / future-overflow-path-candidate |
| `Kimi` as permanent name for the whole path | not in scope | Explicitly rejected |

## 5. Product-Layer Relationship

| Capability | Label | Notes |
|---|---|---|
| Desktop product shell above `owlmlx` | supported | Frozen boundary; repository naming may change |
| Desktop shell defining runtime identity | not in scope | Runtime truth belongs here |
| Shared runtime truth consumed by upper layers | supported | Required architecture direction |

## 6. Label Promotion Rules

A capability may only move from `partial` or `experimental` to `supported`
when the promotion criteria in `extraction-inventory.md` section 8 are
satisfied: implementation evidence, test coverage, no false dependency,
governance compliance, and adoption label resolved.

No capability may be promoted based solely on documentation existing or a
feature working in an external runtime.
