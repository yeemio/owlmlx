# owlmlx Runtime Capability Matrix

> Status: authoritative
> Updated: 2026-05-30 (Campaign F-4.4 — grammar-constrained structured-output lane registered as `partial`, narrowly scoped to 4 families × 2 Qwen models; F-4 overall stays `experimental`, never `supported`)

Stage 1 (2026-05-11) archived 151 spec-as-code modules whose dataclasses
were never read by runtime decision code. This refresh removes capability
claims that cited those archived modules and consolidates surviving
multi-model lifecycle claims behind the real `RuntimeKernel` methods.
Stage 2 (2026-05-12) added `MemoryWatermark`, `SettleBarrierEvent`, and
`pre_load_check` as PR #649-aligned public landmark types; this refresh
adds the corresponding rows.

Stage 3.2 (2026-05-17 ~ 2026-05-23) records Wave H · H1 (HTTP routes
modular split: 5 OpenAI/Anthropic-compatible routes extracted from
`server.py` into `server_routes_openai.py`) and B-1c §1 prerequisite
met (current-Mac `interrupted_no_swap_rehearsal=passed` @ ≈24.69h
cumulative clean native segments per `20260521T064658Z`). Neither
constitutes a capability promotion: session KV cache remains
experimental until B-1a + B-1b + B-1c §1 + B-1c §2 all satisfy
§1a Promotion Gate together.

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
| Memory watermark (PR #649 four-level pressure summary) | supported | `owlmlx/memory_watermark.py` — `MemoryWatermark` (GREEN < 65% < YELLOW < 80% < RED < 90% < FATAL / UNKNOWN) + `WatermarkAction` enums with 32 tests. Consumed by `memory_pressure_contract_to_dict` (adds `summary.watermark` + `summary.watermark_action` fields) and `runtime/server.py` (`GET /v1/runtime/memory-watermark` headline endpoint). |
| Settle barrier event (PR #649 reclaim verification primitive) | supported | `owlmlx/settle_barrier_event.py` — `SettleBarrierEvent` contract for verifying observed memory release after unload. Wire surface `owlmlx.settle_barrier_event`. Exposed at `GET /v1/runtime/reclaim-barrier-event` (URL retained for backward compat; payload `contract.surface` carries the new vocabulary). |
| Reclaim barrier stats surface | supported | `RuntimeKernel.reclaim_barrier_stats()` plus `GET /v1/runtime/reclaim-barrier-event/stats` expose read-only unload-boundary duration and backend-reported reclaim distributions. This aggregates measurements without resolving events, retrying unload, or running eviction/recovery. |
| Non-resident admission via `pre_load_check` | supported | `from owlmlx import pre_load_check` — PR #649-shaped admission entrypoint, returns four-outcome `NonResidentModelAdmissionPolicy` verdict (`admit_and_load` / `defer` / `reject` / `unknown`). Thin alias over `build_nonresident_model_admission_policy`. |
| Fully self-owned implementation stack | partial | Eleven truth modules plus Runtime-3 executable kernel exist; persistent child MLX sessions and streamed kernel serving are real, but production serving, eviction/reclaim, and platform migration remain open |
| Queue-based generation gate (owlmlx-owned) | supported | `owlmlx/serving.py` — GenerationGate class with 11 tests; enforces validated concurrency boundary |
| Single-host orchestration status surface | supported | `owlmlx/orchestration_status.py` plus `GET /v1/runtime/orchestration-status` now freeze one runtime-owned layer-assessment contract for admission / generation gate / stream hold / model residency / memory pressure / recovery without inflating the weaker layers past `partial` or `insufficient_signal` |
| Single-host recovery supervisor contract | supported | `owlmlx/recovery_supervisor.py` plus `GET /v1/runtime/recovery-supervisor-contract` now freeze recovery barrier classification from backend health, restart exhaustion, and abort-recovery substrate state without claiming an automatic recovery loop or pressure eviction policy |
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
| DeepSeek V4 Flash 2bit-DQ adapter optimization | partial | `DeepSeek-V4-Flash-2bit-DQ` is a 284.3B-parameter, about-90G local MLX artifact. D6 (2026-05-27) proved one-shot lifecycle through `MlxLmSubprocessBackend` on the `.runtime-deepseek-experimental` venv (`mlx-lm` fork `5c10538136b9038b9626c134612b08afc18d697a`); D5 (2026-05-27) proved sustained N=20 same-prompt repeatability with RSS range 0.012 GB and decode TPS CV 0.026. Registered on `GET /v1/runtime/model-visibility` at `technical_preview` tier per D7; NOT on the `/v1/models` default surface or `/v1/openai/models`. `lane=technical_preview`, `visibility_status=technical_preview_registered`, and `verdict=partial` in `owlmlx/model_release_candidate_record.py`. |
| Persistent child health probe | supported | Backend `status()` actively issues `ping` to live child sessions and surfaces `child_health` in status detail |
| Dead child restart policy | supported | Registration survives child death; the next generation request can restart the child session within configured restart-attempt limits |
| Explicit runtime restart surface | supported | `POST /v1/runtime/restart` restarts one loaded model through `RuntimeKernel.restart_model()` |
| Serialized concurrent serving validation | supported | `scripts/runtime3_serialized_concurrency_check.py` proves `GenerationGate` remains serial under real concurrent requests against one persistent child session |
| Real streaming response path | supported | `POST /v1/generate/stream` streams NDJSON events through `RuntimeKernel.generate_stream()`; real local smoke verified on `gpt-oss-20b-MXFP4-Q4` |
| Same-model benchmark comparison against old platform | supported | `scripts/runtime3_platform_benchmark_compare.py` replays the old platform benchmark prompts through Runtime-3 and freezes same-model deltas |
| OpenAI-style migration seam | supported | `POST /v1/chat/completions` provides a minimal compatibility surface for upper-layer migration |
| SSE streaming compatibility surface | supported | `POST /v1/chat/completions` with `stream=true` emits `text/event-stream` chunks plus terminal `[DONE]` |
| HTTP routes modular split (Wave H · H1) | supported | 2026-05-17 拆出 `owlmlx/runtime/server_routes_openai.py`（829 LOC · 5 routes：`/v1/chat/completions` · `/v1/completions` · `/v1/messages[/count_tokens]` · `/v1/openai/models`）。HTTP / SSE / contract.version 行为 bit-for-bit 不变；H2（`/v1/runtime/*` 状态 routes）+ H3（dev/admin routes）拆分待 B-1c §2 settle 后启动。详见 `docs/architect/01-mainline-roadmap.md §V Wave H` 与 `docs/architect/design/README.md`。Wave H · H1 是代码组织里程碑，非新功能能力。 |
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
| Machine-level MLX import blocker report | supported | `owlmlx.runtime.mlx_environment.build_mlx_import_blocker_report` exposes the current machine blocker as stable runtime-owned truth; `scripts/runtime_mlx_blocker_report.py` is the operator entry. (Stage 3.1: namespace corrected from the pre-archive `owlmlx.mlx_blocker_report` claim.) |
| Large-weight first-smoke locality decision | supported | `owlmlx.runtime.first_smoke_decision.build_large_weight_first_smoke_decision` combines default-Metal gate, force-CPU gate, and host forensics into one runtime-owned answer for whether local first smoke may proceed or should move to another host/system image. (Stage 3.1: namespace corrected.) |
| Host-stable execution status | supported | `owlmlx.runtime.host_stability.build_host_stable_execution_status` answers whether this machine is a valid candidate for deeper replacement-grade runtime validation. (Stage 3.1: namespace corrected.) |
| Cache/scheduler depth status | supported | Phase 45 adds `owlmlx.cache_scheduler_status`, combining serialized scheduler truth, cache profile truth, and TurboQuant cache-safety truth into one honest runtime-owned contract for the current closure level |
| Cache residency/reuse evidence surface | not in scope | The former `owlmlx/cache_residency_evidence.py` scaffold was archived to `archive/spec-layer-v0/` because no runtime decision consumed it. Live cache counter truth remains in `owlmlx/cache_manager.py` and native-backend status. |
| Session-scoped native KV cache reuse | experimental | `owlmlx/session_kv_cache.py` plus `MlxNativeBackend` provide default-off stream reuse for explicit `X-Owlmlx-Session-Id` callers on the native backend, and a first opt-in no-header automatic prefix slice behind `OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1`. Non-trimmable upstream caches are append-only; tail-edit reuse requires `trim_prompt_cache` support. Real Qwen3.6-27B-4bit evidence in `files/evidence/owlmlx/bench/session-kv-cache/20260512T123316Z-owlmlx-native-session-kv-ttft-n4.jsonl` shows warm p50 TTFT 4026.099 ms -> 543.389 ms, 7.409x by `disabled.warm_p50_first_token_ms / enabled.warm_p50_first_token_ms`, 3 hits / 0 drops. B-1a Gemma 4-31B-it evidence in `files/evidence/owlmlx/bench/session-kv-cache/20260516T151100Z-b1a-gemma4-31b-it-session-kv-ttft.jsonl` shows RuntimeKernel native warm p50 TTFT 1542.972 ms -> 687.102 ms, 2.246x, 3 hits / 0 drops, with RuntimeKernel restart completed. B-1b cache-on no-regress evidence in `files/evidence/owlmlx/bench/cache-settle-no-regress/20260517T013342Z-b1b-gemma-4-31B-it-cache-on-no-regress-rollup.jsonl` shows native cache-off N=20 and cache-on N=20 completed with 20/20 warm hits, `failed_reclaim=0`, `failed_unload=0`, and settle p50/p99 within threshold. B-1c §1 prerequisite met evidence in `files/evidence/owlmlx/bench/session-kv-soak/20260521T064658Z-b1c1-interrupted-no-swap-rehearsal-rollup.jsonl` shows current-Mac `interrupted_no_swap_rehearsal=passed` with `aggregate_measurement_duration_s=88888.531` (≈24.69h) across 3 clean native segments and `current_mac_section_1_prerequisite_met=true` (continuous 24h `no_swap_soak_stability` remains `blocked`; either current-Mac interrupted-aggregate or stronger dedicated-host continuous route satisfies the §2 prerequisite per `docs/architect/design/B-1c-section-2-spec.md §2`). B-1c §2 (soak plus swap) is currently active: the 2026-05-22 boundary-safe 4h segment (`20260522T164506Z`) ran cache-clean / swap-boundary-clean / watermark-GREEN / reclaim-stats-clean but recorded `max_drift_bytes=352321536 > drift_budget_bytes=209715200`, so `soak_plus_swap_stability=failed`; the 2026-05-24 Qwen-only no-swap probe (`20260524T113306Z`) reproduced the same 352MB drift with `swap_count=0` and session cache drops/expirations/rejects all 0, narrowing the blocker to prompt/session growth allocator policy rather than swap-boundary cleanliness. The 2026-05-25 accounting probe (`20260525T040839Z`) records `session_kv_drift_accounting.mode=active_memory_minus_session_kv_positive_delta_upper_bound`, `max_session_cache_resident_bytes=1233125378`, `max_unaccounted_session_kv_drift_bytes=0`, and `used_for_promotion_gate=false`; this is diagnostic upper-bound triage only, not a pass criterion. Bounded-window probes show cache-only 1024-token bypass still drifts 293MB (`20260525T042215Z`), while 3000-char prompt freeze initially kept drift under budget at 150MB but hit one bounded-context cache drop (`20260525T045707Z`). Drop-reason evidence (`20260525T051225Z`) identifies that drop as reuse trim needing 2 tokens while upstream returned 0; the safe trim-bypass fix probe (`20260525T051719Z`) ran 720 samples with drops/expirations/rejects all 0, but 173 trim bypasses/fresh-cache fallbacks pushed drift back to 293MB. The prompt-reset window probe (`20260525T055831Z`) ran 720 Qwen-only samples with drops/expirations/rejects all 0, trim bypasses reduced to 3, and `max_drift_bytes=171704320 < 209715200`; the first swap-bearing prompt-reset segment (`20260525T061019Z`) preserved those functional subcriteria but was not aggregate-clean because `measurement_wall_clock_gap_free=false` with 6 measurement wall-clock gaps (max `7064.873s`). The 2026-06-01 repeat (`20260601T025321Z`) ran the same 4h / 1-swap policy with `measurement_wall_clock_gap_free=true`, max gap `60.642s`, ledger gap free, drops/expirations/rejects all 0, trim bypasses 3, `max_drift_bytes=171704320`, `swap_boundaries_clean=true`, and audit `clean_for_interrupted_aggregate=true`; it remains `blocked` because the base §2 gate now requires four count-based axes and throughput/concurrency are still under-measured. The 2026-06-01 fast forced-swap canary (`20260601T125751Z`) ran 20 minutes with 4 swaps at 5-minute cadence: all swap boundaries were clean and drops/expirations/rejects stayed 0, but same-model load-epoch re-audit found Gemma drift `751370240` bytes (legacy global rollup drift `46801784452` is a cross-model baseline artifact). The 2026-06-01 cache-object resident canary (`20260601T134131Z`) then ran 10 minutes / 2 swaps with all measurement rows using `resident_bytes_estimate_mode=cache_object_nbytes`; Gemma raw same-model drift remained `751370240` bytes, direct resident cache bytes reached `1054965760`, and same-model unaccounted drift stayed `0`. The reviewed B-1c §2 functional drift gate now accepts this narrow `cache_object_resident_accounted` case, so the raw-RSS false-fail is closed. The 2h / 24-swap high-frequency run (`20260601T141659Z`) then exposed resident pressure: Gemma cache-object resident bytes reached `2768240640`, over the `2147483648` budget, despite clean boundaries and zero drops / expirations / rejects. OwlMLX added opt-in LRU resident cap support (`OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES`); the 40m / 8-swap validation (`20260601T162203Z`) stayed clean with 4 evictions and `max_session_cache_resident_bytes=2144829440` within budget. B-2.3 unit coverage proves the no-header opt-in lane reuses only eligible prefix candidates, stays fresh when the flag is disabled, and falls back to fresh cache with an explicit ineligible reason for non-prefix prompts. The next blocker is four-axis evidence: keep the 5-minute switch cadence, but add run-internal throughput-decay sampling and breadth/concurrency pressure instead of passively waiting on wall-clock duration. This does not claim default-on prefix matching, paged KV, continuous batching, subprocess cache-handle transport, or B-1c §2 pass, and it remains experimental until B-1a + B-1b + B-1c §1 + B-1c §2 all satisfy §1a Promotion Gate together. |
| Bounded pre-gate admission structural ingress seam | experimental | `owlmlx/serving.py` introduces a bounded pre-gate hook that stages only immutable metadata, ticket reservation, and pre-claim bookkeeping before gate claim. Does not imply batching parity. |
| Multi-model lifecycle controls (pin / TTL / eviction history) | supported | `RuntimeKernel` owns `pin_model()` / `unpin_model()` (pinned unload blocked, pin state survives restart), `set_model_ttl()` / `clear_model_ttl()` / `sweep_expired_models()` (expired non-pinned models can be swept; pinned-expired stay blocked), and runtime-owned eviction history that records both TTL unload and pinned-expiry skip events. Validated by `tests/test_settle_barrier_event.py` and adjacent kernel tests. |
| Multi-model governance observation surface | partial | Resident-model count, active/default semantics, and recoverability visibility are exposed via `RuntimeKernel.status_dict()` and consumed by the `/v1/runtime/orchestration-status` endpoint. The dedicated `multi_model_governance_*` spec modules from earlier phases were retired in Stage 1 (2026-05-11) because their dataclass fields were never read by a runtime decision path; only the underlying kernel state remains as the governance source. |
| Control-plane downgrade-path hardening | supported | Runtime-10 makes `healthz` a liveness-only fallback; it no longer fabricates `openai_chat` protocol when richer runtime truth is absent |

Session KV B-2.3 note (2026-06-02): the no-header automatic prefix slice remains
`experimental`. The `20260601T172007Z` 20-minute / 4-swap run validates safe
fallback under 5-minute switch cadence (`swap_boundaries_clean=true`, drops /
expirations / rejects all `0`, resident working set within budget). The
`20260602T004000Z` Qwen3.6-27B-4bit hit probe first exposed
`auto_prefix_completion_trim_unavailable`; current code supersedes that blocker
with prompt-only refresh. The `20260602T011000Z` Qwen27 hit probe passed with
`usable_hit_count=1`, `hits_total=1`, drops / expirations / rejects all `0`, and
two safe non-prefix fallbacks. The `20260602T002448Z` 20-minute / 4-swap
current-code validation stayed cache-clean and boundary-clean under the same
5-minute cadence, with audit `clean_for_interrupted_aggregate=true`, but remains
blocked for canonical graduation because throughput/concurrency axes remain under-measured. The
`20260602T015245Z` Qwen27 compat-route probe passed through no-header OpenAI SSE
and Anthropic SSE, surfacing `cached_tokens=26` and
`cache_read_input_tokens=26` from runtime metadata with drops / expirations /
rejects all `0`; the `20260602T015559Z` Qwen35 and Gemma31 compat-route probes
also passed on both surfaces (`26` cached/read tokens on Qwen35, `25` on Gemma31)
with drops / expirations / rejects all `0`. OwlMLX must not claim default-on
mainstream prefix cache, subprocess cache reuse, or B-1c §2 pass from this
narrow evidence.
| Runtime model visibility contract | supported | `owlmlx/runtime_model_visibility.py` now freezes owlmlx-owned rule `runtime_gate_required_before_visible`: `GET /v1/openai/models` is the formal visibility list, `GET /v1/runtime/model-visibility` is the diagnostic contract surface, and `GET /v1/models` remains loaded inventory with an embedded `visibility_contract` block; the gate is owlmlx registry plus `$MODELS_ROOT/{model-id}/config.json` presence rather than router lifecycle curation; see `runtime-model-visibility-contract.md` |
| Degraded local routing now fails closed | supported | Runtime-11 blocks `localRuntimeProtocol=auto` when only `/healthz` is reachable; it no longer silently falls through to `/v1/chat/completions` for local models |
| Replacement readiness verdict surface | supported | Runtime-12 promotes replacement readiness into explicit `doctor` output with a blocker list; launch readiness and replacement readiness are now distinct control-plane truths |
| Speculative execution status surface | experimental | Campaign F-1 adds runtime-owned `speculative_execution_status` as a top-level diagnostic section plus `GET /v1/runtime/speculative-execution-status`. F-1.2 endpoint stub and F-1.3 kernel observe APIs are landed, and evidence `files/evidence/owlmlx/runtime/f1-speculative-execution-status/20260525T142617Z-f1-contract-fixtures-rollup.jsonl` records 5/5 fixtures passed plus 20 fresh round trips with `endpoint_self_promotion_eligible=true`. This is endpoint eligibility evidence only: `graduates.endpoint_supported=false`, `graduates.any_method_supported=false`, and `assistant_drafter` remains `experimental`; no speculative method is promoted by F-1. |
| Grammar-constrained structured-output lane | partial | Feature-lane label (NOT a model label, NOT F-4-wide). Child-side xgrammar JSON-schema constraint (via `mlx_lm` `logits_processors`, wired in `mlx_lm_runner.py`) covers families `json_schema_flat`, `enum_constrained`, `function_call_arguments`, `nested_object` on `qwen3.6-27b-4bit` + `qwen3.6-35b-a3b-4bit`, grammar-on, temp {0.0, 0.3}, reachable via direct backend and the OpenAI `response_format` surface. Evidence: json/enum 2× N=1024 @ 0 breaks + OpenAI-surface coverage (F-4.3 / #1); function_call+nested 1× N=1024 @ 0 breaks with bounded grammar (maxLength=120 + max_whitespace_cnt=4), F-4.4 `f8e0c6fc`, all 8 cells 128/0. Scope + exclusions frozen in `structured-output-grammar-lane.md`. NOT covered: `gemma-4-31b-it-4bit` (small-N fix only, unvalidated at N≥1000), `thinking_tag_closed` (residual — reasoning models don't close `<think>` in budget; family design mismatch, separate redesign), longer outputs, and any model/family/temperature/surface outside this scope. F-4 structured output overall stays `experimental`; `supported` claimed nowhere; the bench rollup auto-promote flag stays `False`. |
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
