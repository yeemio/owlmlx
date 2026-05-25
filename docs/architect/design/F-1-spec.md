# F-1 · Design-Grade Spec

> **Gate**: Campaign F · F-1 — runtime-owned `speculative_execution_status` contract surface
> **Layer**: design-grade, downstream of [`../06-campaign-F1-plan.md`](../06-campaign-F1-plan.md), upstream of code-grade (F-1.2 endpoint stub + F-1.3 wired-to-runner)
> **Plan-grade source**: [`../06-campaign-F1-plan.md`](../06-campaign-F1-plan.md) (which derives from [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Part V · Campaign F · F1)
> **Status**: design-grade draft pending review
> **Prerequisite**: F-1 plan-grade reviewed; B-1c §2 closure is **not** a prerequisite for F-1.1/F-1.2/F-1.3 (per plan §2)
> **Non-goal**: this spec does not promote `assistant_drafter` / `native_mtp` / any spec method to `supported`. It only specifies the endpoint contract by which their honest capability is surfaced.

## 1. Purpose

F-1 wires a runtime-owned status surface that lets upper layers (OwlOps, OwlCoda, debuggers) read four answers from one stable field set, without inferring from generation success/failure:

```text
Q1 which speculative method is currently active on this runtime
Q2 what honest capability_label that method carries (disabled / not_implemented /
   scaffold_only / experimental / partial / supported)
Q3 what the runner is doing right now (unloaded / loaded /
   deferred_cli_per_request / error)
Q4 what other methods this runtime knows about (so consumers can orthogonally
   compare spec capability across runtimes)
```

The endpoint itself is the F-1 deliverable. It does not change any module's
capability — it surfaces what each module already declares. Endpoint-self
promotion to `supported` (via §1a Promotion Gate) is allowed and does **not**
promote any method behind it.

## 2. Prerequisites

F-1.2 (endpoint stub) and F-1.3 (wired-to-runner) may proceed when all of these hold:

- F-1 plan-grade has been reviewed and signed off
- this design-grade spec has been reviewed and signed off
- Track 1 (B-1c §2) still owns the cache/memory/allocator editing surface; this spec lands in **non-overlapping** files (per plan §8.1 forbidden-edit list)
- the existing `GEMMA4_MTP_CAPABILITY_LABEL` constant in [`owlmlx/gemma4_mtp_drafter.py`](../../../owlmlx/gemma4_mtp_drafter.py) line 23 remains the source of truth for the `assistant_drafter` method's honest label

F-1.3 additionally requires F-1.2 endpoint contract test landed and green.

## 3. Scope

### In scope (F-1.1 → F-1.2 → F-1.3)

- a new top-level diagnostic section `speculative_execution_status` inside `runtime.status_dict()` returning the shape defined in §4
- a new HTTP route `GET /v1/runtime/speculative-execution-status` that mirrors the same payload (with a graceful fallback when the section is missing, modelled on the existing `/v1/runtime/session-kv-cache` route at [`owlmlx/runtime/server.py:1284`](../../../owlmlx/runtime/server.py))
- registration of the new section name in the `contract.diagnostic_sections` list emitted by `RuntimeKernel.status_dict()` (currently at [`owlmlx/runtime/kernel.py:1649`](../../../owlmlx/runtime/kernel.py))
- a contract test fixture suite under `tests/test_runtime_speculative_execution_status_route.py`
- evidence ledger of the contract test payloads under `files/evidence/owlmlx/runtime/f1-speculative-execution-status/`
- F-1.3: kernel-side `observe_*` APIs that accept the response shapes emitted by `MlxVlmMtpChildRunner` ([`mlx_vlm_mtp_runner.py`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py) `_load` / `_generate` / unload returns) and update the surface accordingly. The runner itself is **not** edited. **F-1.3 does not introduce a parent-side spawn/supervision site for the MTP runner** — see §6.2 integration-reality note for the honest scope boundary.

### Out of scope (explicitly **not** F-1)

- any edit to [`owlmlx/session_kv_cache.py`](../../../owlmlx/session_kv_cache.py), [`owlmlx/cache_manager.py`](../../../owlmlx/cache_manager.py), [`owlmlx/scheduler_admission.py`](../../../owlmlx/scheduler_admission.py), [`owlmlx/memory_pressure_eviction_policy.py`](../../../owlmlx/memory_pressure_eviction_policy.py), [`owlmlx/memory_watermark.py`](../../../owlmlx/memory_watermark.py) (Track 1 owns these)
- any edit to [`owlmlx/runtime/mlx_vlm_mtp_runner.py`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py) internal logic; F-1 only observes its emitted records via the kernel
- any change to `GEMMA4_MTP_CAPABILITY_LABEL` constant value or location
- proposer / drafter implementation work (n-gram, EAGLE, resident MTP runner — each is a separate gate)
- DS4 native MTP weights probing
- the spec × structured-output × tool-calling orthogonal matrix (Campaign F-4)
- promotion of any method to `supported`
- `/v1/runtime/status` stable-section additions (F-1 stays diagnostic-only by default; the optional `summary` window described in plan §7.2 is **deferred** out of F-1.2/F-1.3 — re-evaluation lives in a separate post-F-1.3 round)
- the eventual Wave H2 move of the F-1 route from `server.py` to `server_routes_runtime.py` (mechanical sweep; F-1.2 PR description must declare this)

## 4. Surface Shape

### 4.1 Identity and placement

| Property | Value |
|---|---|
| Surface name (JSON) | `owlmlx.speculative_execution_status` |
| Version (JSON) | `v1` |
| Placement inside `runtime.status_dict()` | top-level key `speculative_execution_status`, peer of `reclaim_barrier` / `governance_observations` / `host_pressure` (**not** nested under `backend.detail`) |
| `contract.diagnostic_sections` registration | string `"speculative_execution_status"` appended to the existing list at [`owlmlx/runtime/kernel.py:1649`](../../../owlmlx/runtime/kernel.py) |
| Independent HTTP route | `GET /v1/runtime/speculative-execution-status` (hyphenated URL, snake_case body, mirroring `/v1/runtime/session-kv-cache`) |
| JSON field casing | snake_case throughout (matches every existing owlmlx surface) |
| Timestamp serialization | ISO 8601 UTC with `Z` suffix, second precision (`2026-05-25T07:14:22Z`); generated via `time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())` for parity with existing emitters such as the runtime monitor envelope |

**Rationale for top-level placement** (vs nesting under `backend.detail` like `session_kv_cache`): `session_kv_cache` is genuinely backend-internal — only the native backend can know its KV cache state. Spec method ownership is a kernel-level concept (the kernel knows which spec runner was loaded), and the F-1 surface must remain readable even when the active backend is `FakeBackend` or when no model is loaded. Top-level placement also mirrors `reclaim_barrier`, which is the closest existing analogue (kernel-owned event log queryable independent of backend identity).

### 4.2 Required semantic fields

| Field | Type | Meaning |
|---|---|---|
| `surface` | string | literal `"owlmlx.speculative_execution_status"` |
| `version` | string | literal `"v1"` |
| `method` | string \| null | currently active spec method; `null` means spec not enabled or no runner loaded. Allowed string values: see §4.5 vocabulary |
| `capability_label` | string | honest capability of the currently active method. Allowed values: see §4.6 |
| `runner_status` | string | health/state of the runner backing the active method. Allowed values: see §4.7 |
| `available_methods` | array[MethodEntry] | every method this runtime knows about, including those with `status=not_implemented`. Day-one entries enumerated in §4.5 |

### 4.3 Required `MethodEntry` shape

| Field | Type | Meaning |
|---|---|---|
| `method` | string | one of the §4.5 vocabulary values |
| `status` | string | one of the §4.6 vocabulary values (capability_label minus `disabled`) |
| `notes` | string \| null | short human-readable explanation (e.g. `"deferred_cli_per_request via mlx_vlm"`); `null` when there is nothing useful to say |

### 4.4 Optional semantic fields

These are populated when the runtime can answer them honestly. **A missing or null optional field MUST NOT be read as "method supports this".**

| Field | Type | Source | Semantics |
|---|---|---|---|
| `drafter_id` | string \| null | runner `_load` response `draft_model_path` ([`mlx_vlm_mtp_runner.py:215`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py)) | filesystem path or model id of the drafter weights, when the active method has one |
| `accepted_tokens` | int | running sum of `floor(mean_accepted_tokens × rounds)` taken from each `speculative_summary` ([`gemma4_mtp_drafter.py:341`](../../../owlmlx/gemma4_mtp_drafter.py)) since `runner_started_at` | cumulative accepted tokens **since the current runner load**; resets to 0 on unload / reload |
| `rejected_tokens` | int \| null | **MUST be `null`** while upstream mlx-vlm summary does not expose reject counts; do NOT fabricate by `rounds - accepted_rounds` arithmetic | placeholder that becomes populated only after the producing runner exposes a direct counter |
| `accepted_rounds` | int | running sum of `rounds` from each `speculative_summary` since `runner_started_at` | cumulative speculative rounds **since the current runner load** |
| `last_request_at` | timestamp \| null | wall-clock timestamp captured by the kernel observer after a successful generate event | freshness signal; `null` until the first generate after load |
| `runner_started_at` | timestamp \| null | wall-clock timestamp captured when the kernel observed the runner enter `loaded` / `deferred_cli_per_request` state | reset on each load; `null` while `runner_status ∈ {unloaded}` |
| `fallback` | FallbackEntry \| null | populated by the kernel observer on error transitions (see §4.8) | most recent fallback transition since `runner_started_at`; `null` if no fallback has been observed |
| `cache_sharing` | CacheSharingEntry \| null | declarative shape; values are **constants** derived from the active method's known behaviour, not live measurement (see §4.9) | read-only declaration; F-1 never writes the session KV cache |
| `missing_reason` | string \| null | populated when `runner_status=error` or `capability_label ∈ {not_implemented, scaffold_only}` | canonical machine-readable code; vocabulary in §4.10 |

### 4.5 `method` vocabulary (v1, locked)

| Value | Day-one `status` | Day-one `notes` |
|---|---|---|
| `native_mtp` | `not_implemented` | `"DS4 MTP weights absent or stripped (see D3)"` |
| `assistant_drafter` | `experimental` | `"deferred_cli_per_request via mlx_vlm"` |
| `draft_model` | `not_implemented` | `null` |
| `eagle` | `not_implemented` | `null` |
| `ngram` | `not_implemented` | `"F-2 candidate"` |

**Vocabulary discipline** (mirrors plan §5.2):

- new method value added to `available_methods` is schema-additive within v1
- vocabulary extension beyond the day-one five (e.g. a future `medusa` or `mtp_v2`) requires a minor version bump emitted in the `version` field's history but does **not** break v1 schema
- vocabulary contraction (renaming or removing an existing value) requires a major bump
- `disabled` is **never** a `method` value; spec-off is expressed as `method=null, capability_label="disabled"` (plan §5.1 footnote)

### 4.6 `capability_label` vocabulary (v1, locked)

Top-level `capability_label` ∈ { `not_implemented`, `scaffold_only`, `experimental`, `partial`, `supported`, `disabled` } (6 values).
`available_methods[*].status` ∈ the same set **minus** `disabled` (5 values).

Semantics inherited verbatim from plan §5.3.

| Value | Meaning | Allowed at top level | Allowed in `MethodEntry.status` |
|---|---|---|---|
| `not_implemented` | runtime knows the method name, has no runner / scaffold | yes | yes |
| `scaffold_only` | module-level scaffold (inspection, types) exists; no serving path | yes | yes |
| `experimental` | runner exists, capability honesty is experimental | yes | yes |
| `partial` | runner passes N≥20 repeatability but not the full 4-gate promote path | yes | yes |
| `supported` | passed [`§1a Promotion Gate`](../../source-of-truth/extraction-inventory.md) | yes | yes |
| `disabled` | spec explicitly off; pairs with `method=null` | yes | **no** |

Invariant: when `capability_label = disabled`, `method` MUST be `null`. When `capability_label ∈ {not_implemented, scaffold_only, experimental, partial, supported}`, `method` MUST be a non-null vocabulary value.

**`capability_label` vs `runner_status` separation**: `capability_label` always reflects the **static honest label of the method named in `method`** (sourced from module constants — currently `GEMMA4_MTP_CAPABILITY_LABEL` for `assistant_drafter`). It does NOT degrade when the runner enters `error` state. Runner health is carried separately by `runner_status`. A consumer reading `method=assistant_drafter, capability_label=experimental, runner_status=error` learns: "this runtime knows assistant_drafter is experimental, and right now its runner is broken" — both signals are honest and independent.

### 4.7 `runner_status` vocabulary (v1, locked)

| Value | Meaning |
|---|---|
| `unloaded` | no spec runner has been instantiated, OR an explicit unload has occurred |
| `loaded` | spec runner is alive in-process and ready to serve (e.g. future resident MTP) |
| `deferred_cli_per_request` | spec runner is registered but each request shells out to a fresh subprocess (current Gemma4 path) |
| `error` | spec runner attempted to load and failed, OR crashed during a generate request and has not been re-loaded |

Invariants:

- `method = null` ⇒ `runner_status ∈ {unloaded, deferred_cli_per_request, error}`. The combination `method=null, runner_status=loaded` is **forbidden**.
- `runner_status = error` ⇒ `missing_reason` MUST be non-null (so consumers can disambiguate failure modes).

### 4.8 `FallbackEntry` shape

| Field | Type | Meaning |
|---|---|---|
| `from_method` | string | the method value that was active immediately before the fallback transition |
| `to_method` | string \| null | the method active after fallback; `null` means "no spec, the runtime fell back to plain generate" |
| `reason_code` | string | canonical code from §4.10 vocabulary |
| `observed_at` | timestamp | wall-clock UTC ISO-8601 when the kernel observer recorded the transition |
| `transition_count` | int | number of fallback transitions observed since the current `runner_started_at`; resets on load |

**Lifetime rule**: `fallback` carries the **most recent** fallback only. A successful re-load that returns `method` to a non-null vocabulary value MUST set `fallback = null` (the recovery itself is observable via `runner_started_at` advancing).

### 4.9 `CacheSharingEntry` shape

This entry is a **read-only declaration**, computed from the active method's known design properties — not from a live measurement of the session KV cache.

| Field | Type | Meaning |
|---|---|---|
| `reads_session_kv_cache` | bool | whether the active method's runner reads session_kv_cache prefix matches when serving |
| `writes_session_kv_cache` | bool | **MUST always be `false` in F-1** (F-1 explicitly does not modify any cache path; surface honesty rule) |
| `shares_target_kv` | bool | whether drafter shares the target model's KV cache (true for in-process resident MTP; false for `deferred_cli_per_request`) |
| `scope` | string | one of `"deferred_cli_per_request"`, `"in_process_resident"`, `"none"` |

Day-one values per method:

| Active `method` | `reads_session_kv_cache` | `writes_session_kv_cache` | `shares_target_kv` | `scope` |
|---|---|---|---|---|
| `assistant_drafter` (current) | `false` | `false` | `false` | `deferred_cli_per_request` |
| `native_mtp` (future) | `false` | `false` | `true` | `in_process_resident` |
| `draft_model` (future) | `false` | `false` | `true` | `in_process_resident` |
| `eagle` (future) | `false` | `false` | `true` | `in_process_resident` |
| `ngram` (future) | `false` | `false` | `false` | `none` |

When `method = null`, `cache_sharing = null`.

### 4.10 `missing_reason` and `reason_code` vocabulary (v1)

This vocabulary is shared by `missing_reason` (top-level when the active method is unavailable) and `FallbackEntry.reason_code`.

| Value | Meaning |
|---|---|
| `spec_explicitly_disabled` | top-level disable; not a fallback (so this value only appears as `missing_reason`, never as `reason_code`) |
| `method_not_implemented` | method has no runner registered |
| `runner_not_loaded` | runner is registered but no `load` has succeeded |
| `runner_load_failed` | a `load` attempt returned `ok=false` (pair inspection blocked, env vars missing, etc.) |
| `mlx_vlm_toolchain_missing` | `inspect_mlx_vlm_toolchain` returned `ok=false` (subset of `runner_load_failed` but useful enough to surface as its own code) |
| `runner_crash` | runner emitted a non-zero returncode during a generate call without an explicit unload |
| `mtp_weights_absent_or_stripped` | `native_mtp` specific; sourced from [`D3-spec.md`](D3-spec.md) inspection conclusion |
| `target_draft_pair_blocked` | `assistant_drafter` pair inspection returned blockers (subset of `runner_load_failed`) |

Vocabulary discipline matches §4.5: additive within v1, removal/rename is major bump.

### 4.11 Two canonical payload shapes

#### 4.11.1 Spec disabled (owlmlx default, F-1.2 always returns this)

```json
{
  "surface": "owlmlx.speculative_execution_status",
  "version": "v1",
  "method": null,
  "capability_label": "disabled",
  "runner_status": "unloaded",
  "missing_reason": "spec_explicitly_disabled",
  "available_methods": [
    {"method": "native_mtp", "status": "not_implemented", "notes": "DS4 MTP weights absent or stripped (see D3)"},
    {"method": "assistant_drafter", "status": "experimental", "notes": "deferred_cli_per_request via mlx_vlm"},
    {"method": "draft_model", "status": "not_implemented", "notes": null},
    {"method": "eagle", "status": "not_implemented", "notes": null},
    {"method": "ngram", "status": "not_implemented", "notes": "F-2 candidate"}
  ]
}
```

#### 4.11.2 `assistant_drafter` actively loaded (F-1.3)

```json
{
  "surface": "owlmlx.speculative_execution_status",
  "version": "v1",
  "method": "assistant_drafter",
  "capability_label": "experimental",
  "runner_status": "deferred_cli_per_request",
  "drafter_id": "/Users/yeemio/AI/models/gemma-4-31B-it-assistant-bf16",
  "runner_started_at": "2026-05-25T07:10:11Z",
  "last_request_at": "2026-05-25T07:14:22Z",
  "accepted_tokens": 142,
  "accepted_rounds": 11,
  "rejected_tokens": null,
  "cache_sharing": {
    "reads_session_kv_cache": false,
    "writes_session_kv_cache": false,
    "shares_target_kv": false,
    "scope": "deferred_cli_per_request"
  },
  "available_methods": [
    {"method": "native_mtp", "status": "not_implemented", "notes": "DS4 MTP weights absent or stripped (see D3)"},
    {"method": "assistant_drafter", "status": "experimental", "notes": "deferred_cli_per_request via mlx_vlm"},
    {"method": "draft_model", "status": "not_implemented", "notes": null},
    {"method": "eagle", "status": "not_implemented", "notes": null},
    {"method": "ngram", "status": "not_implemented", "notes": "F-2 candidate"}
  ]
}
```

## 5. Verification Contract

F-1 verification is contract-shape conformance, not bench evidence (this is a status surface, not a workload). Pass criteria are graded per slice.

### 5.1 F-1.2 (endpoint stub) pass criteria

`F1_2_endpoint_stub_contract`:

- `GET /v1/runtime/speculative-execution-status` returns HTTP 200 on a fresh `RuntimeKernel` with `FakeBackend` and no model loaded
- response body matches §4.11.1 verbatim (every field present, exact vocabulary values)
- `status_dict()["speculative_execution_status"]` produces the same payload
- `status_dict()["contract"]["diagnostic_sections"]` contains the string `"speculative_execution_status"` after F-1.2 lands
- when the runtime is started with no native backend, the route still returns the §4.11.1 payload (does not 503)
- module constant `GEMMA4_MTP_CAPABILITY_LABEL` is read at runtime (not hardcoded in the endpoint module); changing the constant in a test fixture and re-querying the endpoint MUST reflect the change in `available_methods[method=assistant_drafter].status`

### 5.2 F-1.3 (wired-to-runner) pass criteria

`F1_3_runner_observation_contract` (on top of F-1.2 criteria):

- simulating a successful `MlxVlmMtpChildRunner._load` response in the kernel observer MUST flip the surface from the §4.11.1 shape to a shape matching §4.11.2 within the same synchronous call (no async settle window)
- a successful generate response with `parsed.speculative_summary = {mean_accepted_tokens: 1.5, rounds: 8}` MUST increment `accepted_tokens` by `floor(1.5 * 8) = 12` and `accepted_rounds` by `8`
- `rejected_tokens` MUST remain `null` regardless of how many generates have occurred (no fabrication rule, §4.4)
- a runner unload event MUST set `method=null`, `capability_label=disabled`, `runner_status=unloaded`, and reset all cumulative counters to `0` / `null`
- a synthetic runner crash (returncode != 0 in a generate response) MUST set `runner_status=error`, populate `missing_reason="runner_crash"`, populate `fallback.from_method`/`reason_code`/`observed_at`, AND keep `method` non-null at its last-loaded value (so consumers can still see "the runtime was trying to run assistant_drafter but it crashed")
- a re-load after crash MUST clear `fallback` to `null` (§4.8 lifetime rule)

### 5.3 Endpoint self-promotion criteria (separate from method capability)

F-1 endpoint itself may pursue `supported` promotion via §1a Promotion Gate after the F-1.3 contract test is green and N≥20 repeated round-trips against a fresh kernel all return contract-conformant payloads. Endpoint self-promotion does **not** promote any method (plan §6.3 invariant); a `supported` endpoint may still report `capability_label=experimental` for `assistant_drafter`.

## 6. Harness Changes

### 6.1 New code-grade additions (F-1.2)

- new module: `owlmlx/runtime/speculative_execution_status.py` containing:
  - `SPECULATIVE_EXECUTION_STATUS_SURFACE = "owlmlx.speculative_execution_status"`
  - `SPECULATIVE_EXECUTION_STATUS_VERSION = "v1"`
  - `DAY_ONE_METHOD_VOCABULARY` tuple of `MethodEntry`-shaped dicts (read by both `status_dict()` and the endpoint module)
  - `build_speculative_execution_status_payload(...)` pure function taking module-constant reads + optional live state and returning the §4.11 shape
- edit to `owlmlx/runtime/kernel.py`:
  - import `build_speculative_execution_status_payload`
  - add `"speculative_execution_status"` to the `contract.diagnostic_sections` list (currently at line 1649)
  - add `"speculative_execution_status": build_speculative_execution_status_payload(...)` at the same level as `reclaim_barrier` in the dict returned by `status_dict()`
  - F-1.2 calls it with no live runner state → returns §4.11.1
- edit to `owlmlx/runtime/server.py`:
  - register `@app.get("/v1/runtime/speculative-execution-status")` route that reads `runtime.status_dict()["speculative_execution_status"]` with the same graceful-fallback pattern used at [line 1284–1296](../../../owlmlx/runtime/server.py) for `/v1/runtime/session-kv-cache`
  - PR description MUST declare "this route will be moved to `server_routes_runtime.py` by Wave H2" (plan §8.4)
- new test file: `tests/test_runtime_speculative_execution_status_route.py`, modelled on [`tests/test_runtime_session_kv_cache_route.py`](../../../tests/test_runtime_session_kv_cache_route.py)

### 6.2 Additional code-grade work (F-1.3)

- new kernel attribute (no constructor signature change): `RuntimeKernel._speculative_execution_state: dict[str, Any]` initialized to "no runner observed yet" shape
- new kernel methods:
  - `observe_speculative_runner_load(payload: dict[str, Any]) -> None` — consumes an `MlxVlmMtpChildRunner._load` response dict ([`mlx_vlm_mtp_runner.py:207–219`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py)) and updates internal state
  - `observe_speculative_runner_generate(payload: dict[str, Any]) -> None` — consumes a `_generate` response dict (specifically the `speculative_summary` / `returncode` keys) and updates counters / `last_request_at`
  - `observe_speculative_runner_unload() -> None` — resets state
- the `MlxVlmMtpChildRunner` itself is **not** edited; F-1.3 only adds the kernel-side observe APIs above

**Integration reality** (honest framing — failure to state this drifts F-1.3 into Track-1-adjacent scope):

The `MlxVlmMtpChildRunner` in [`owlmlx/runtime/mlx_vlm_mtp_runner.py`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py) is **not currently spawned or supervised by `RuntimeKernel`**. Its parallel `mlx_lm_runner` has a parent-side wrapper `MlxLmSubprocessBackend` at [`owlmlx/runtime/mlx_lm_subprocess_backend.py:779`](../../../owlmlx/runtime/mlx_lm_subprocess_backend.py); the MTP variant has no equivalent parent-side wrapper as of this design-grade round.

Consequences for F-1.3 scope:

- F-1.3 lands the kernel `observe_*` APIs and proves them correct against **contract test fixtures** (synthesized `_load` / `_generate` / `_unload` payloads matching the exact shapes emitted by [`mlx_vlm_mtp_runner.py`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py)). This is fully shippable as a v1 contract.
- F-1.3 does **NOT** introduce a parent-side `MlxVlmMtpSubprocessBackend` (or any analogous spawn/supervise site). That work is out of F-1 entirely — it is a precursor or component of a future Gemma 4 resident MTP / spawned-MTP gate (overlaps with plan §9 F-3 "Gemma 4 resident MTP A/B").
- Until such a spawn site exists, the F-1 surface reports the §4.11.1 "spec disabled" shape during ordinary serving. The §4.11.2 "actively loaded" shape is only observable in tests that drive the observe APIs directly, or in any future gate that wires a real spawn site through them.
- This honesty is itself part of the F-1.3 verification contract — the contract test suite MUST include a "no live caller" fixture confirming the surface stays in §4.11.1 shape on a kernel that has never had `observe_speculative_runner_load` invoked.

- extension of `test_runtime_speculative_execution_status_route.py` to drive `observe_*` calls and assert §5.2 contract

### 6.3 Forbidden edits (Track 1 / Stage 1 boundary)

F-1 PRs MUST NOT touch:

- [`owlmlx/session_kv_cache.py`](../../../owlmlx/session_kv_cache.py)
- [`owlmlx/cache_manager.py`](../../../owlmlx/cache_manager.py)
- [`owlmlx/scheduler_admission.py`](../../../owlmlx/scheduler_admission.py)
- [`owlmlx/memory_pressure_eviction_policy.py`](../../../owlmlx/memory_pressure_eviction_policy.py)
- [`owlmlx/memory_watermark.py`](../../../owlmlx/memory_watermark.py)
- any file under [`bench/`](../../../bench/) or [`files/evidence/`](../../../files/evidence/) **except** the new F-1 evidence directory in §7
- [`owlmlx/runtime/mlx_vlm_mtp_runner.py`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py) internal logic (F-1 only observes its emitted JSONL records via the kernel; observation is one-directional)
- the `GEMMA4_MTP_CAPABILITY_LABEL` constant value (stays `"experimental"` until a future capability gate promotes it)

PRs touching any forbidden path are out-of-scope for F-1 even if they would shorten the diff.

## 7. Evidence

Evidence layout (created by F-1.2 PR, extended by F-1.3 PR):

```text
files/evidence/owlmlx/runtime/f1-speculative-execution-status/
  <YYYYMMDDTHHMMSSZ>-f1-contract-fixtures.jsonl
  <YYYYMMDDTHHMMSSZ>-f1-contract-fixtures-rollup.jsonl
```

Each ledger row:

```yaml
schema_version: f1.contract_fixture.v1
record_type: speculative_execution_status_contract_fixture
gate: F-1
fixture_label: spec_disabled | assistant_drafter_loaded | assistant_drafter_crashed | runner_unloaded | re_loaded_after_crash
payload: <verbatim JSON returned by /v1/runtime/speculative-execution-status>
contract_assertions:
  surface_matches: true
  version_matches: true
  vocabulary_conformant: true
  invariants_hold: true
verdict: passed | failed
```

Rollup row:

```yaml
schema_version: f1.contract_rollup.v1
gate: F-1
slice: F1.2 | F1.3
fixture_count: <int>
all_fixtures_passed: true | false
endpoint_self_promotion_eligible: true | false
graduates:
  endpoint_supported: false  # F-1 design-grade explicitly does not graduate here
  any_method_supported: false  # F-1 NEVER graduates a method
```

`endpoint_self_promotion_eligible = true` is the **only** field that becomes true at F-1.3 close; it is an eligibility flag, not the promotion itself (§1a Gate is a separate round).

## 8. Failure Handling

| Condition | `runner_status` | `method` | `capability_label` | `missing_reason` | `fallback` |
|---|---|---|---|---|---|
| spec explicitly off (default) | `unloaded` | `null` | `disabled` | `spec_explicitly_disabled` | `null` |
| load attempted, pair inspection blocked | `error` | `null` | `disabled` | `target_draft_pair_blocked` | `from_method=<requested>`, `to_method=null`, `reason_code=target_draft_pair_blocked` |
| load attempted, mlx-vlm toolchain missing | `error` | `null` | `disabled` | `mlx_vlm_toolchain_missing` | `from_method=<requested>`, `to_method=null`, `reason_code=mlx_vlm_toolchain_missing` |
| load attempted, env var `OWLMLX_GEMMA4_MTP_DRAFT_MODEL` missing | `error` | `null` | `disabled` | `runner_load_failed` | `from_method=<requested>`, `to_method=null`, `reason_code=runner_load_failed` |
| load succeeded, no generate yet | `deferred_cli_per_request` (Gemma4) or `loaded` (future resident) | `<method>` | static label of `<method>` (e.g. `experimental`) | `null` | `null` |
| generate succeeded | unchanged | unchanged | unchanged | `null` | unchanged |
| generate failed (returncode != 0) without explicit unload | `error` | **kept** at last-loaded value | static label of `<method>` (unchanged from pre-crash) | `runner_crash` | `from_method=<last>`, `to_method=null`, `reason_code=runner_crash`, `transition_count` incremented |
| explicit unload | `unloaded` | `null` | `disabled` | `spec_explicitly_disabled` | `null` (cleared on unload) |
| re-load after crash succeeds | `deferred_cli_per_request` or `loaded` | `<method>` | static label of `<method>` | `null` | `null` (cleared per §4.8 lifetime rule) |

**Honesty rules** (also enforced by §5 contract tests):

- `runner_status=error` with `method=null` AND `fallback=null` is **forbidden** (the consumer cannot tell what failed). When the kernel detects an error without an active method (e.g. load failed on first attempt), `fallback.from_method` records the requested method and `fallback.to_method=null`.
- `rejected_tokens` is `null` in **all** failure modes until upstream mlx-vlm exposes a direct reject count. Synthesizing `rejected = rounds × avg_block_size - accepted` is **forbidden**.
- A generate returncode of 0 with an unparseable `speculative_summary` (regex miss in [`gemma4_mtp_drafter.py:31-36`](../../../owlmlx/gemma4_mtp_drafter.py)) MUST NOT increment counters and MUST NOT set `runner_status=error`. This is "spec ran without producing a summary" and is observable only via `last_request_at` advancing while counters do not — that is the honest signal.

## 9. Out-of-scope reminders

To prevent scope creep into adjacent gates during F-1.2 / F-1.3 implementation:

- F-1 does not adopt or vendor any spec method's drafter weights. `assistant_drafter` continues to depend on the operator-provided `OWLMLX_GEMMA4_MTP_DRAFT_MODEL` env var; F-1 surfaces this path as `drafter_id` but does not validate or fetch it.
- F-1 does not change the existing `/v1/runtime/status` `summary` section. The optional `spec_enabled` / `spec_method_count_available` `summary` window described in plan §7.2 is **deferred to a separate post-F-1.3 round** and is **not** part of F-1.2 or F-1.3 pass criteria.
- F-1 does not register a `/healthz` field. The `/healthz` liveness contract (frozen at [runtime-status-schema.md §6](../../source-of-truth/runtime-status-schema.md)) is untouched.
- F-1 does not consume the [`B-1c §2`](B-1c-section-2-spec.md) session_kv_cache evidence ledger. `cache_sharing.reads_session_kv_cache` is a **declarative constant** per active method (see §4.9 table), not a live cache-counter read.
- F-1.3 does not subscribe to the runner's standard error stream for counter recovery. Counter losses across runner restarts are acceptable and are signalled by `runner_started_at` advancing (consumers reset their own baselines).
- F-1 does not assert anything about Campaign F-2 / F-3 / F-4 / F-5 / F-6 / F-7 implementation. Cross-gate linkage from [plan §9](../06-campaign-F1-plan.md) is informational — those gates will land additive changes (new vocabulary values, populated counters, `cache_sharing` updates) without breaking F-1's v1 contract.

## 10. Status / Next Step

- **Current state**: design-grade draft pending user review
- **On approval**:
  - **F-1.2** code-grade session: implement the new module + kernel diagnostic registration + endpoint + contract test suite for the spec-disabled fixture set (§4.11.1 + §5.1 + §6.1). Ledger first fixture pass to `files/evidence/owlmlx/runtime/f1-speculative-execution-status/`.
  - **F-1.3** code-grade session (after F-1.2 review): land kernel `observe_*` methods, wire to runner return paths, extend the contract test suite to cover §5.2 fixtures (`assistant_drafter_loaded`, `assistant_drafter_crashed`, `runner_unloaded`, `re_loaded_after_crash`).
  - **§1a Gate** for endpoint self-promotion: only after F-1.3 evidence shows `endpoint_self_promotion_eligible=true` for ≥20 fresh runs.
- **Hand-off discipline** (per [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Part VIII.3 layered handoff): design-grade → user review → revisions → code-grade. F-1.2 PR does not start until this spec is signed off.

## 11. References

### Plan-grade lineage

- Plan-grade source: [`../06-campaign-F1-plan.md`](../06-campaign-F1-plan.md)
- Plan-grade lineage: [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Part V · Campaign F · F1
- Master-outline dual-track context: [`../../source-of-truth/master-outline.md §8.4`](../../source-of-truth/master-outline.md)
- 12-d framework slot: [`../02-state-vs-market-gap.md`](../02-state-vs-market-gap.md) #9 Speculative Path Safety / #10 Structured-Output Invariance

### Code surfaces F-1 reads

- Module constants (source of truth for `assistant_drafter` capability): [`owlmlx/gemma4_mtp_drafter.py`](../../../owlmlx/gemma4_mtp_drafter.py) lines 21–23
- Spec summary parser (source of `mean_accepted_tokens` / `rounds`): [`owlmlx/gemma4_mtp_drafter.py`](../../../owlmlx/gemma4_mtp_drafter.py) `_SPECULATIVE_SUMMARY_RE` and `parse_speculative_summary`
- Runner load / generate response shapes: [`owlmlx/runtime/mlx_vlm_mtp_runner.py`](../../../owlmlx/runtime/mlx_vlm_mtp_runner.py) `_load` and `_generate`
- Existing runtime status dict construction: [`owlmlx/runtime/kernel.py`](../../../owlmlx/runtime/kernel.py) `status_dict()` (anchor for the new top-level key)
- Existing route pattern (template for F-1 route): [`owlmlx/runtime/server.py`](../../../owlmlx/runtime/server.py) `/v1/runtime/session-kv-cache` and `/v1/runtime/status`
- Existing route contract-test pattern: [`tests/test_runtime_session_kv_cache_route.py`](../../../tests/test_runtime_session_kv_cache_route.py)

### Cross-gate refs

- [`D3-spec.md`](D3-spec.md) — `mtp_weights_absent_or_stripped` missingReason vocabulary (re-used as F-1 `missing_reason` value for `native_mtp`)
- [`D4-spec.md`](D4-spec.md) — clean pre-load reject pattern (the F-1 `runner_status=error` + `missing_reason` shape is the surface-side analogue)
- [Runtime status schema](../../source-of-truth/runtime-status-schema.md) §6 / §9 — stable vs diagnostic partition that places F-1 in diagnostic

### External anchors (informational, not committed source)

- vLLM speculative decoding: <https://docs.vllm.ai/en/latest/features/speculative_decoding/>
- SGLang speculative decoding: <https://docs.sglang.ai/advanced_features/speculative_decoding.html>

## 12. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-25 | design-grade draft (fresh-context derivation from plan-grade) | architect session (this round) |
