# D7 · Design-Grade Spec · Technical-Preview Visibility Registration

> **Gate**: Campaign D7 · DSV4-Flash 2bit-DQ promotion to `partial` capability label and registration on the `/v1/runtime/model-visibility` diagnostic surface at `technical_preview` tier
> **Plan-grade source**: [`../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md`](../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md)
> **Prerequisites**:
>   - D5 passed 2026-05-27 (sustained-load N≥20 through mainline backend; see [`D5-sustained-load-spec.md`](D5-sustained-load-spec.md))
>   - D6 passed 2026-05-27 under amended §7.1 item 7 (mainline backend lifecycle + intra-run RSS stability; see [`D6-mainline-backend-integration-spec.md`](D6-mainline-backend-integration-spec.md))
> **Status**: design-grade · 2026-05-27
> **Hard non-goal**: D7 does **not** promote DSV4 to `supported` (banned per plan §1 hard rule 1) and does **not** add DSV4 to the `/v1/models` default OpenAI-style surface (banned per plan §1 / §12).

---

## 1. Purpose

D7 closes the Campaign D upgrade by promoting DSV4-Flash 2bit-DQ from `experimental_only` to `partial` and registering it under the `technical_preview` tier of the runtime visibility diagnostic surface. D5 + D6 evidence is the input; D7 produces no new runtime measurement — it produces **documentation + data + schema enum + a runtime tier-aware registry**:

```text
inputs:
  D5 evidence: 20-round sustained-load passed (RSS range 0.012 GB / decode TPS CV 0.026)
  D6 evidence: mainline backend lifecycle passed (intra-run stable; 14 GB inter-path offset documented)

D7 outputs:
  - owlmlx/model_release_candidate_schema.py: extend enums (additive)
  - owlmlx/model_release_candidate_record.py: update DSV4 row data
  - owlmlx/runtime_model_visibility.py: add `tier` field; tier-aware registry split
  - owlmlx/runtime/server.py: route DSV4 to the diagnostic surface only (not /v1/models)
  - docs/source-of-truth/runtime-capability-matrix.md: DSV4 row promoted to `partial`
  - docs/source-of-truth/deepseek-v4-bring-up-status.md §4: visibility prohibition softened to "technical_preview allowed; supported still prohibited"
  - files/evidence/owlmlx/deepseek-v4/d7-technical-preview-visibility/: D7 decision JSONL
  - files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl: D7 row appended
  - tests: regression tests for the tier-aware visibility surface; existing tests adjusted only where directly affected
```

D7 is a **promotion + registration round**, not a measurement round. Acceptance is "the schema and code accept the new tier; the documents are amended; the runtime surfaces behave per the tier discipline; the cumulative ledger has a D7 row".

### 1.1 Why D7 must extend `owlmlx/` package (relaxing the D5/D6 "no owlmlx changes" rule)

D5 and D6 ran with a hard rule "no `owlmlx/` package change beyond data". D7 cannot honor that rule strictly because:

- The schema enum tuples `MODEL_RELEASE_CANDIDATE_LANES`, `MODEL_RELEASE_CANDIDATE_VISIBILITY_STATUSES`, `MODEL_RELEASE_CANDIDATE_VERDICTS` in [`owlmlx/model_release_candidate_schema.py`](../../../owlmlx/model_release_candidate_schema.py) (lines 14, 19, 26) **do not yet contain** `technical_preview`, `technical_preview_registered`, or `partial`. The plan-grade promotion wording cannot be schema-validated until those values are added.
- The `RegisteredRuntimeVisibleModel` dataclass in [`owlmlx/runtime_model_visibility.py`](../../../owlmlx/runtime_model_visibility.py) (line 43) does **not yet have** a `tier` field. Without it, the visibility derivation cannot distinguish "default-tier visible" (appears in `/v1/models`) from "technical-preview-tier visible" (only in `/v1/runtime/model-visibility`).
- The `DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS` tuple at the bottom of the same file is the source of registered models for the visibility endpoint; DSV4 must be added there at tier `technical_preview`.

[[project-owlmlx-agents-module-as-spec-rule]] forbids **creating new** modules under `owlmlx/`. Extending existing modules (additive enum values, additive optional dataclass field, extending an existing tuple) is allowed and is the intended path. D7 does not create any new module.

---

## 2. Scope

### 2.1 In

| Item | Requirement |
|---|---|
| Schema enums extended | `LANES += ("technical_preview",)`; `VISIBILITY_STATUSES += ("technical_preview_registered",)`; `VERDICTS += ("partial",)` (additive only; existing values unchanged) |
| Schema validation rule | `lane=flagship_experimental` cannot use `verdict=pass` rule extended: `lane=technical_preview` cannot use `verdict=pass` either (only `partial` or `experimental_only`); ensures the new tier doesn't sneak into the `pass` semantics |
| Banned vocabulary | `BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY` unchanged (D7 does NOT introduce or claim `parity` / `replacement` / `equivalent` / `production_ready` / `beats` / `wins` / `matches`) |
| DSV4 data row | [`owlmlx/model_release_candidate_record.py:39-47`](../../../owlmlx/model_release_candidate_record.py:39) DSV4 entry updated to `lane=technical_preview`, `visibility_status=technical_preview_registered`, `verdict=partial` |
| Runtime visibility tier | `RegisteredRuntimeVisibleModel` gains optional `tier: str = "default"` field; values `{"default", "technical_preview"}` |
| Visibility derivation split | `RuntimeModelVisibilityGate.visible_model_ids` (default tier only, unchanged backward semantics) + new `technical_preview_visible_model_ids` field |
| `/v1/models` surface | continues to read `visible_model_ids` (default tier only) → DSV4 NOT included |
| `/v1/runtime/model-visibility` surface | exposes both tiers explicitly; DSV4 visible here at `technical_preview` tier |
| DSV4 in default registry | DSV4 added to `DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS` with `tier="technical_preview"` |
| Capability matrix row | DSV4 row in [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) line 96 promoted from `experimental` to `partial`; row text updated to reference D5/D6/D7 evidence + `technical_preview` tier |
| bring-up-status §4 Blocked Scope | softened: "no visibility on `/v1/openai/models` / `/v1/models`" stays prohibited; "visibility on `/v1/runtime/model-visibility` at `technical_preview` tier" is now allowed |
| D7 evidence file | one JSONL decision record under `files/evidence/owlmlx/deepseek-v4/d7-technical-preview-visibility/` referencing D5 + D6 evidence + the spec amendments |
| Model RC cumulative ledger | append one row with `lane=technical_preview`, `visibility_status=technical_preview_registered`, `verdict=partial` |
| Tests | additive: tier-aware visibility derivation tests; schema enum extension tests; existing D6/D5 tests stay green (no behavioral break) |

### 2.2 Out

- Promotion to `supported` (plan §1 hard rule 1; spec §6 banned per [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) §6 Label Promotion Rules)
- Adding DSV4 to `/v1/models` default surface, including but not limited to `visibility_contract.visible_model_ids` (must NOT include DSV4)
- DSV4-Pro / 4bit / 8bit / FP16 variants
- MTP speculative path (D8 far term)
- Multi-prompt / multi-stratified evidence beyond D5's single-prompt N=20
- Modification of mlx-lm upstream or transformers upstream
- Adding new HTTP endpoints (D7 reuses existing `/v1/runtime/model-visibility`)
- Adding new modules to `owlmlx/` (D7 only **extends** existing modules)
- Adding new banned-vocabulary entries to `BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY` (the existing list is sufficient)
- Re-running D5 / D6 / D1-D4 (their evidence is the input to D7)
- Cross-runtime measured comparison against oMLX / vMLX (banned per [`public-claim-matrix.md`](../../source-of-truth/public-claim-matrix.md) §3)

---

## 3. Prerequisites

### 3.1 Evidence already gathered

| Stage | Evidence | Path |
|---|---|---|
| D1 | 15-row ladder passed | `files/evidence/owlmlx/deepseek-v4/d1-isolated-repeatability/20260517T-d1-full-ladder-adopted-messages-policy.jsonl` |
| D2 | 6-row metrics ledger passed | `files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl` |
| D3 | MTP checkpoint missing verified | `files/evidence/owlmlx/deepseek-v4/d3-checkpoint-inspection/20260517T-d3-mtp-checkpoint-inspection.jsonl` |
| D4 | Clean pre-load reject verified | `files/evidence/owlmlx/deepseek-v4/d4-preload-reject/20260517T-d4-mtp-clean-preload-reject.jsonl` |
| D6 | Mainline backend lifecycle passed (amended §7.1) | `files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/20260527T072206Z-d6-mainline-backend-lifecycle.jsonl` + `.summary.json` |
| D5 | Sustained-load N=20 passed | `files/evidence/owlmlx/deepseek-v4/d5-sustained-load/20260527T084115Z-d5-sustained-load.jsonl` + `.summary.json` |

D7 references these by exact filename in its decision record. The references are "evidence pointers", not "include by value" — D7 does not re-derive or re-summarize them.

### 3.2 Configuration carry-over from D6

D7 inherits the D6 backend configuration without modification (`.runtime-deepseek-experimental/`, Blaizzy fork commit pin, `MlxLmSubprocessBackend` etc.). D7 does not load the model or run any generation; it does not need a venv configured. The `model_artifact_path` field in the D7 decision record is for evidence-pointer continuity, not for runtime invocation.

---

## 4. Schema and Enum Extensions

### 4.1 `owlmlx/model_release_candidate_schema.py` (additive)

```python
MODEL_RELEASE_CANDIDATE_LANES: tuple[str, ...] = (
    "mainline",
    "flagship_experimental",
    "technical_preview",                  # NEW (D7)
)

MODEL_RELEASE_CANDIDATE_VISIBILITY_STATUSES: tuple[str, ...] = (
    "visible",
    "blocked",
    "not_registered",
    "unknown",
    "technical_preview_registered",       # NEW (D7)
)

MODEL_RELEASE_CANDIDATE_VERDICTS: tuple[str, ...] = (
    "pass",
    "needs_optimization",
    "blocked",
    "experimental_only",
    "partial",                            # NEW (D7)
)
```

Constraint additions (extends existing rule at [`model_release_candidate_schema.py:390-392`](../../../owlmlx/model_release_candidate_schema.py:390)):

```python
# Existing rule (line 390-392):
if record["lane"] == "flagship_experimental" and record["verdict"] == "pass":
    errors.append("flagship_experimental lane cannot use verdict='pass'")

# NEW rule (D7):
if record["lane"] == "technical_preview" and record["verdict"] == "pass":
    errors.append("technical_preview lane cannot use verdict='pass'; allowed: partial | experimental_only | blocked")
```

No `BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY` change. The existing 8 banned strings (`parity` / `replacement` / `equivalent` / `production_ready` / `production-ready` / `beats` / `wins` / `matches`) cover what D7 must not claim.

### 4.2 `owlmlx/runtime_model_visibility.py` tier field

The `RegisteredRuntimeVisibleModel` dataclass at [`runtime_model_visibility.py:43`](../../../owlmlx/runtime_model_visibility.py:43) gains one optional field:

```python
@dataclass(frozen=True, slots=True)
class RegisteredRuntimeVisibleModel:
    model_id: str
    local_dir_name: str | None = None
    tier: str = "default"                  # NEW (D7); allowed: {"default", "technical_preview"}
```

The `tier` default of `"default"` preserves backward compatibility for every existing registration including the 7 entries in `DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS`.

The `RuntimeModelVisibilityGate` dataclass at [`runtime_model_visibility.py:78`](../../../owlmlx/runtime_model_visibility.py:78) gains one new field:

```python
@dataclass(frozen=True, slots=True)
class RuntimeModelVisibilityGate:
    rule: str
    contract_version: str
    models_root: str
    entries: tuple[RuntimeVisibleModelState, ...]
    visible_model_ids: tuple[str, ...]                  # default tier only (unchanged semantics)
    technical_preview_visible_model_ids: tuple[str, ...]  # NEW (D7); tier="technical_preview" only
    loaded_model_ids: tuple[str, ...]
```

`RuntimeVisibleModelState` also gains a `tier: str` field (mirrors the registration's tier):

```python
@dataclass(frozen=True, slots=True)
class RuntimeVisibleModelState:
    model_id: str
    local_model_dir: str
    config_path: str
    local_model_dir_present: bool
    config_present: bool
    visible: bool
    block_reason: str | None = None
    tier: str = "default"                  # NEW (D7)
```

The `build_runtime_model_visibility` function at [`runtime_model_visibility.py:139`](../../../owlmlx/runtime_model_visibility.py:139) is amended so the per-entry tier is propagated to the per-entry state, and the gate aggregates two id tuples:

```python
visible_model_ids: list[str] = []                          # default tier
technical_preview_visible_model_ids: list[str] = []        # technical_preview tier
for entry in normalize_registered_runtime_visible_models(registry):
    # ... existing per-entry derivation ...
    state = RuntimeVisibleModelState(
        model_id=entry.model_id,
        ...,
        visible=visible,
        block_reason=block_reason,
        tier=entry.tier,                                   # NEW
    )
    entries.append(state)
    if visible:
        if entry.tier == "technical_preview":
            technical_preview_visible_model_ids.append(entry.model_id)
        else:
            visible_model_ids.append(entry.model_id)
```

`normalize_registered_runtime_visible_models` is amended so dict-form inputs that omit `tier` keep the default `"default"`.

### 4.3 `DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS` extension

```python
DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS: tuple[RegisteredRuntimeVisibleModel, ...] = (
    RegisteredRuntimeVisibleModel("Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit"),  # existing
    RegisteredRuntimeVisibleModel("Qwen3.5-35B-A3B-4bit"),                            # existing
    RegisteredRuntimeVisibleModel("Qwen3.6-27B"),                                     # existing
    RegisteredRuntimeVisibleModel("Qwen3.6-35B-A3B"),                                 # existing
    RegisteredRuntimeVisibleModel("gemma-4-31B-it"),                                  # existing
    RegisteredRuntimeVisibleModel("gpt-oss-20b-MXFP4-Q4"),                            # existing
    RegisteredRuntimeVisibleModel("Qwen3-Embedding-8B-4bit-DWQ"),                     # existing
    RegisteredRuntimeVisibleModel(                                                    # NEW (D7)
        "DeepSeek-V4-Flash-2bit-DQ",
        tier="technical_preview",
    ),
)
```

### 4.4 `owlmlx/runtime/server.py` surface routing

The existing `/v1/runtime/model-visibility` endpoint at [`server.py:1259`](../../../owlmlx/runtime/server.py:1259) needs no behavioral change in route or contract function — it already returns the full `runtime_model_visibility_contract(gate)` payload. The payload is extended automatically once `RuntimeModelVisibilityGate` has the new `technical_preview_visible_model_ids` field, because `runtime_model_visibility_contract` serializes the gate.

The `/v1/models` endpoint at [`server.py:1241`](../../../owlmlx/runtime/server.py:1241) needs **one explicit change**: when including the visibility contract, it must NOT expose `technical_preview_visible_model_ids` (so that a default-surface consumer reading `/v1/models` cannot accidentally see DSV4). The cleanest way:

```python
@app.get("/v1/models")
def models() -> dict[str, Any]:
    status = runtime.status_dict()
    visibility_contract = derive_runtime_model_visibility_contract(
        runtime.inventory_snapshot(),
        models_root=visibility_models_root,
        registry=visibility_registry,
    )
    # D7: scrub technical_preview tier from the default-surface payload.
    default_surface_contract = {
        k: v for k, v in visibility_contract.items()
        if k != "technical_preview_visible_model_ids"
    }
    return {
        "active_model_id": status["active_model_id"],
        ...,
        "visibility_contract": default_surface_contract,
    }
```

The same scrubbing is applied to the WebSocket `models` push payload at [`server.py:1145-1158`](../../../owlmlx/runtime/server.py:1145) if that route also exposes `visibility_contract` on the default surface.

The contract function `runtime_model_visibility_contract` itself returns the full payload including `technical_preview_visible_model_ids`. Only the `/v1/models` consumer scrubs it. The `/v1/runtime/model-visibility` endpoint receives the full payload.

---

## 5. `model_release_candidate_record.py` Data Update

Current state at [`model_release_candidate_record.py:39-47`](../../../owlmlx/model_release_candidate_record.py:39):

```python
{
    "model_id": "DeepSeek-V4-Flash-2bit-DQ",
    "lane": "flagship_experimental",
    "artifact_path": (
        "/Users/yeemio/AI/Agent/model-candidates/mlx-community/"
        "DeepSeek-V4-Flash-2bit-DQ"
    ),
    "visibility_status": "not_registered",
    "verdict": "experimental_only",
},
```

D7 amended state:

```python
{
    "model_id": "DeepSeek-V4-Flash-2bit-DQ",
    "lane": "technical_preview",                             # was flagship_experimental
    "artifact_path": (
        "/Users/yeemio/AI/Agent/model-candidates/mlx-community/"
        "DeepSeek-V4-Flash-2bit-DQ"
    ),
    "visibility_status": "technical_preview_registered",     # was not_registered
    "verdict": "partial",                                    # was experimental_only
},
```

The `build_dry_run_model_release_candidate_records` helper at the same file derives blockers from `lane`. After D7, the `lane=="technical_preview"` case needs its own blocker list. The blockers list at [`model_release_candidate_record.py:376-390`](../../../owlmlx/model_release_candidate_record.py:376) currently distinguishes `flagship_experimental` vs everything else; D7 adds a third branch:

```python
if lane == "technical_preview":
    blockers = (
        "technical_preview_visibility_only",      # informational: not on /v1/models
        "owlops_observation_missing",
    )
elif lane == "flagship_experimental":
    blockers = (
        "deepseek_runtime_adapter_not_integrated",
        "technical_preview_visibility_not_registered",
        "repeated_live_run_missing",
        "owlops_observation_missing",
    )
else:
    blockers = (
        "repeated_live_run_missing",
        "owlops_observation_missing",
        "reference_runtime_comparison_missing",
    )
```

---

## 6. Documentation Changes

### 6.1 `docs/source-of-truth/runtime-capability-matrix.md` DSV4 row

Current line 96 (block in §4 "Future Or Not Yet Established"):

```text
| DeepSeek V4 Flash 2bit-DQ adapter optimization | experimental | `DeepSeek-V4-Flash-2bit-DQ` is a 284.3B-parameter, about-90G local MLX artifact with a first short generation smoke through an isolated DeepSeek V4 PR runtime; it is not yet visible on the technical-preview `GET /v1/openai/models` surface and is tracked by `deepseek-v4-flash-adapter-optimization-candidate.md` plus `model-release-candidate-program.md` |
```

D7 amended row (move from §4 to a new placement that reflects `partial` capability; either in §2 or a new §5 "Technical-Preview-Tier Capabilities" subsection — code-grade picks based on existing section semantics; design-spec freezes the row TEXT):

```text
| DeepSeek V4 Flash 2bit-DQ adapter optimization | partial | `DeepSeek-V4-Flash-2bit-DQ` is a 284.3B-parameter, about-90G local MLX artifact. D6 (2026-05-27) proved one-shot lifecycle through `MlxLmSubprocessBackend` on the `.runtime-deepseek-experimental` venv (`mlx-lm` fork `5c10538136b9038b9626c134612b08afc18d697a`); D5 (2026-05-27) proved sustained N=20 same-prompt repeatability with RSS range 0.012 GB and decode TPS CV 0.026. Registered on `GET /v1/runtime/model-visibility` at `technical_preview` tier per D7 design-spec; NOT on the `/v1/models` default surface. `lane=technical_preview`, `visibility_status=technical_preview_registered`, `verdict=partial` in `owlmlx/model_release_candidate_record.py`. |
```

### 6.2 `docs/source-of-truth/deepseek-v4-bring-up-status.md` §4 Blocked Scope

Current text at [`deepseek-v4-bring-up-status.md` §4](../../source-of-truth/deepseek-v4-bring-up-status.md):

```text
Until upstream merges, the following are explicitly deferred:

- Any measured TPS comparison against reference runtimes for DeepSeek
- Any visibility registration on `GET /v1/openai/models`
- Any claim of DeepSeek support in external communication
```

D7 amended §4:

```text
Until upstream merges, the following are explicitly deferred:

- Any measured TPS comparison against reference runtimes for DeepSeek (unchanged; banned per public-claim-matrix.md §3)
- Visibility registration on `GET /v1/openai/models` / `GET /v1/models` default surface (unchanged: NOT allowed)
- Any claim of DeepSeek `supported` capability label (unchanged: NOT allowed; `partial` is the ceiling until upstream merges)
- D7 SOFTENS this clause: visibility registration on `GET /v1/runtime/model-visibility` at `technical_preview` tier is NOW ALLOWED, with the DSV4-Flash 2bit-DQ entry having `lane=technical_preview`, `visibility_status=technical_preview_registered`, `verdict=partial` per D5 + D6 + D7 evidence.
```

### 6.3 Other documents

- [`02-state-vs-market-gap.md`](../02-state-vs-market-gap.md) §3.5 — update DSV4 from "刻意不追" to "L1 必追，Campaign D upgrade in flight; D5+D6+D7 passed; technical_preview registered" per [plan §13](../09-campaign-D-upgrade-ds4-flash-2bit-128g-integration-plan.md#13-status--next-step) sweep follow-up. Code-grade applies the wording change.
- [`reference-runtime-comparison-matrix.md`](../../source-of-truth/reference-runtime-comparison-matrix.md) §8 "新出现的硬差距" block — update to "active Campaign D upgrade target → resolved at technical_preview tier 2026-05-27". Code-grade applies.

These two are part of the plan-grade §13 sweep follow-up but spec-grade ownership belongs to D7 because D7 is the round that creates the state transition they reflect. Code-grade may choose to defer them to a separate "sweep" commit; either way is acceptable, as long as the wording change is applied before the next campaign starts.

---

## 7. Evidence and Decision Artifact

### 7.1 D7 decision record (`<run_id>.jsonl`)

```yaml
schema_version: d7.technical-preview-visibility.v1
record_type: technical_preview_visibility_promotion_decision
gate: D7
run_id: <ts>-d7-technical-preview-visibility
created_at_utc: <ISO-8601 Z>
model_id: DeepSeek-V4-Flash-2bit-DQ
decision:
  promoted_from:
    lane: flagship_experimental
    visibility_status: not_registered
    verdict: experimental_only
  promoted_to:
    lane: technical_preview
    visibility_status: technical_preview_registered
    verdict: partial
  promotion_authority: D5 + D6 evidence + D7 design-spec
evidence_pointers:
  d1: files/evidence/owlmlx/deepseek-v4/d1-isolated-repeatability/20260517T-d1-full-ladder-adopted-messages-policy.jsonl
  d2: files/evidence/owlmlx/deepseek-v4/d2-metrics-ledger/20260517T-d2-p1-p2-p4-128-512-metrics-v2.jsonl
  d3: files/evidence/owlmlx/deepseek-v4/d3-checkpoint-inspection/20260517T-d3-mtp-checkpoint-inspection.jsonl
  d4: files/evidence/owlmlx/deepseek-v4/d4-preload-reject/20260517T-d4-mtp-clean-preload-reject.jsonl
  d6: files/evidence/owlmlx/deepseek-v4/d6-mainline-backend-integration/20260527T072206Z-d6-mainline-backend-lifecycle.summary.json
  d5: files/evidence/owlmlx/deepseek-v4/d5-sustained-load/20260527T084115Z-d5-sustained-load.summary.json
spec_amendments_applied:
  schema_enum_extensions:
    lanes_added: ["technical_preview"]
    visibility_statuses_added: ["technical_preview_registered"]
    verdicts_added: ["partial"]
  data_block_updated: owlmlx/model_release_candidate_record.py:39-47
  runtime_visibility_tier_extension: owlmlx/runtime_model_visibility.py (RegisteredRuntimeVisibleModel.tier, RuntimeModelVisibilityGate.technical_preview_visible_model_ids)
  surface_routing_scrubbed:
    - /v1/models excludes technical_preview_visible_model_ids
docs_amendments_applied:
  - docs/source-of-truth/runtime-capability-matrix.md DSV4 row → partial
  - docs/source-of-truth/deepseek-v4-bring-up-status.md §4 Blocked Scope softened
  - docs/architect/02-state-vs-market-gap.md §3.5 updated
  - docs/source-of-truth/reference-runtime-comparison-matrix.md §8 updated
surface_state_after_D7:
  GET /v1/models:
    visibility_contract.visible_model_ids: [<7 default-tier models, no DSV4>]
    visibility_contract.technical_preview_visible_model_ids: <KEY ABSENT in /v1/models response>
  GET /v1/runtime/model-visibility:
    visible_model_ids: [<7 default-tier models, no DSV4>]
    technical_preview_visible_model_ids: ["DeepSeek-V4-Flash-2bit-DQ"]
ledger_row_appended_to: files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl
verdict: passed | blocked | failed
verdict_reason: <string, optional; populated on non-passed>
```

### 7.2 Cumulative ledger row

A model_release_candidate_record JSONL row (validated via the amended schema) is appended to `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl`:

```yaml
surface: owlmlx.model_release_candidate
version: <current MODEL_RELEASE_CANDIDATE_RECORD_VERSION>
created_at: <ISO-8601 Z>
model_id: DeepSeek-V4-Flash-2bit-DQ
lane: technical_preview
artifact_path: /Users/yeemio/AI/Agent/model-candidates/mlx-community/DeepSeek-V4-Flash-2bit-DQ
visibility_status: technical_preview_registered
load_result: {status: pass, detail: "D6 + D5 evidence"}
generation_result: {status: pass, detail: "D5 N=20 sustained-load passed"}
unload_result: {status: pass, detail: "D6 freed 100.0 GB; D5 freed 100.0 GB"}
reload_result: {status: not_applicable, detail: "D7 is a promotion round; no fresh load executed"}
repeat_count: 20                  # D5 N=20
failure_count: 0
output_sanity_label: pass
owlops_observation_path: not_applicable
verdict: partial
blockers: ["technical_preview_visibility_only"]
quality_caveats:
  - "Visibility is technical_preview tier only; NOT on /v1/models default surface"
  - "decode_tps comparison against oMLX / vMLX not measured; banned per public-claim-matrix §3"
```

The `repeat_count: 20` and `verdict: partial` cells reflect plan-grade §6 acceptance wording.

### 7.3 Evidence directory layout

```text
files/evidence/owlmlx/deepseek-v4/d7-technical-preview-visibility/
  <ts>-d7-technical-preview-visibility.jsonl
```

Plan-grade §10 names `<ts>-d7-visibility-surface-registration.jsonl`; this design-spec adopts the shorter `<ts>-d7-technical-preview-visibility.jsonl` for naming consistency with D5/D6 (`<ts>-d{N}-<descriptor>.jsonl`). Plan-grade §10 reads as a target path, not a fixed filename.

---

## 8. Acceptance / Pass Criteria

D7 hard gates (every one is necessary):

1. **Schema enum extensions applied and validated**: importing [`owlmlx.model_release_candidate_schema`](../../../owlmlx/model_release_candidate_schema.py) exposes `"technical_preview" in MODEL_RELEASE_CANDIDATE_LANES`, `"technical_preview_registered" in MODEL_RELEASE_CANDIDATE_VISIBILITY_STATUSES`, `"partial" in MODEL_RELEASE_CANDIDATE_VERDICTS`.
2. **Schema validation accepts the new triple** for the DSV4 record (no schema error on `lane=technical_preview / visibility_status=technical_preview_registered / verdict=partial`).
3. **Schema validation rejects `lane=technical_preview, verdict=pass`** (the new constraint from §4.1).
4. **`DEFAULT_MODEL_RELEASE_CANDIDATES` DSV4 entry** matches the §5 amended state (byte-identical to the spec's amended block).
5. **`RegisteredRuntimeVisibleModel` accepts `tier=technical_preview`** without TypeError; default remains `"default"` for backward compatibility.
6. **`build_runtime_model_visibility`** splits registered models into `visible_model_ids` (default tier) and `technical_preview_visible_model_ids` (technical_preview tier); the union of the two preserves the legacy "all visible" semantics.
7. **DSV4 appears in `technical_preview_visible_model_ids`** when the local model dir + config.json are present at `models_root`.
8. **DSV4 does NOT appear in `visible_model_ids`** (default tier list) regardless of artifact presence.
9. **`GET /v1/models`** response's `visibility_contract` does NOT contain the key `technical_preview_visible_model_ids` AND does NOT list `DeepSeek-V4-Flash-2bit-DQ` anywhere in `visible_model_ids`.
10. **`GET /v1/runtime/model-visibility`** response contains `technical_preview_visible_model_ids=["DeepSeek-V4-Flash-2bit-DQ"]` (when the local artifact is present) AND keeps `visible_model_ids` showing the 7 existing default-tier models.
11. **Capability matrix DSV4 row** is updated to `partial` with the §6.1 text (or semantically equivalent text covering D5/D6/D7 evidence pointers + the tier marker).
12. **bring-up-status §4** is softened per §6.2; `supported` and `/v1/models default surface` remain explicitly prohibited.
13. **D7 evidence file** is written at `files/evidence/owlmlx/deepseek-v4/d7-technical-preview-visibility/<ts>-d7-technical-preview-visibility.jsonl` and contains every required field from §7.1.
14. **Cumulative ledger row** is appended per §7.2; the row passes schema validation.
15. **No banned vocabulary** appears in any of the new strings (matrix row, bring-up-status text, evidence record, ledger row). The 8 banned strings in `BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY` are the authoritative list.
16. **D5 + D6 tests stay green**: extending the schema and the visibility dataclasses is additive; no existing test should break. Code-grade verifies via full `pytest` run.

### 8.1 Capability-label invariants after D7 passes

After D7, the DSV4 row in [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) is `partial`. This is the **ceiling** until upstream `mlx-lm` mainline merges DSV4 support (per plan §1 hard rule 1). `supported` promotion is explicitly out of scope until that upstream condition holds, at which point a separate Campaign-D-follow-up round (not D7) would decide promotion.

After D7:
- `lane=technical_preview` (was `flagship_experimental`)
- `visibility_status=technical_preview_registered` (was `not_registered`)
- `verdict=partial` (was `experimental_only`)
- `/v1/runtime/model-visibility` exposes DSV4 at `technical_preview` tier
- `/v1/models` does NOT expose DSV4 (neither in default-tier `visible_model_ids` nor anywhere in the response payload)

### 8.2 What happens if D7 fails

A D7 failure does NOT invalidate D5 or D6. The schema and code changes are revert-only in scope (the schema enum extensions are additive; reverting them leaves D5/D6 evidence intact). If the runtime visibility extension breaks an existing default-tier behavior, the fix lands in a follow-up round, not a D5/D6 redo.

---

## 9. Failure Semantics

| # | Failure | Classification | Where surfaced | Next action |
|---|---|---|---|---|
| 1 | Schema validation rejects the amended DSV4 row | `failed` | §8 gate 2 | re-check the `MODEL_RELEASE_CANDIDATE_LANES` / `_VISIBILITY_STATUSES` / `_VERDICTS` tuples in `model_release_candidate_schema.py`; confirm the additions match the strings in §4.1 byte-for-byte |
| 2 | `lane=technical_preview, verdict=pass` is NOT rejected by the validator | `failed` | §8 gate 3 | the new validation rule in §4.1 was not applied; check the `validate_model_release_candidate_record` function |
| 3 | `RegisteredRuntimeVisibleModel("...", tier="technical_preview")` raises `TypeError` | `failed` | §8 gate 5 | the dataclass extension was not applied or has a typo |
| 4 | DSV4 appears in `visible_model_ids` (default tier list) | `failed` | §8 gate 8 | check the `build_runtime_model_visibility` derivation; the tier branch logic in §4.2 was misapplied |
| 5 | `GET /v1/models` response includes `technical_preview_visible_model_ids` key OR mentions `DeepSeek-V4-Flash-2bit-DQ` | `failed` | §8 gate 9 | the `/v1/models` scrubbing in §4.4 was not applied or has a bug |
| 6 | Capability matrix row still reads `experimental` | `failed` | §8 gate 11 | the doc amendment in §6.1 was not applied; check `runtime-capability-matrix.md` line 96 |
| 7 | `BANNED_MODEL_RELEASE_CANDIDATE_VERDICT_VOCABULARY` triggers on the new ledger row | `failed` | §8 gate 15 | the new strings introduced something forbidden; rewrite to use neutral language |
| 8 | An existing D5 or D6 test fails after the changes | `failed` | §8 gate 16 | the schema or visibility extension is not strictly additive; backward-incompatible breakage must be fixed before D7 lands |
| 9 | Plan §1 hard rule 1 (`supported` tier prohibition) violated | `failed` | gate-internal | revert the verdict back from any `supported`-equivalent string to `partial` |

`blocked` vs `failed` for D7:
- `blocked` = an external dependency missing (e.g., D5 evidence file not present, can't compute pointers). Resolve dependency and retry.
- `failed` = D7's own work product does not satisfy a gate. Fix the work product.

---

## 10. Code-Grade Work and Test Changes

### 10.1 owlmlx/ package edits (extending existing modules only)

| File | Change |
|---|---|
| [`owlmlx/model_release_candidate_schema.py`](../../../owlmlx/model_release_candidate_schema.py) | Add 3 enum values per §4.1; add one validation rule for `technical_preview` lane |
| [`owlmlx/model_release_candidate_record.py`](../../../owlmlx/model_release_candidate_record.py) | Update the DSV4 entry in `DEFAULT_MODEL_RELEASE_CANDIDATES` (lines 39-47); add the `technical_preview` blocker branch per §5 |
| [`owlmlx/runtime_model_visibility.py`](../../../owlmlx/runtime_model_visibility.py) | Add `tier` field to `RegisteredRuntimeVisibleModel`; add `tier` field to `RuntimeVisibleModelState`; add `technical_preview_visible_model_ids` field to `RuntimeModelVisibilityGate`; amend `build_runtime_model_visibility` to populate the new id tuple; amend `normalize_registered_runtime_visible_models` to preserve tier from dict form; add DSV4 to `DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS` with `tier="technical_preview"` |
| [`owlmlx/runtime/server.py`](../../../owlmlx/runtime/server.py) | Scrub `technical_preview_visible_model_ids` from `/v1/models` and the WebSocket `models` payload; pass through unchanged on `/v1/runtime/model-visibility` |

No new module under `owlmlx/`. Per [[project-owlmlx-agents-module-as-spec-rule]].

### 10.2 Test changes (extend existing files; no new test files)

The following existing test files are extended:

- [`tests/test_model_release_candidate_schema.py`](../../../tests/test_model_release_candidate_schema.py) (assuming it exists; if not, code-grade extends the closest related file):
  - Test that `"technical_preview" in MODEL_RELEASE_CANDIDATE_LANES`.
  - Test that `"technical_preview_registered" in MODEL_RELEASE_CANDIDATE_VISIBILITY_STATUSES`.
  - Test that `"partial" in MODEL_RELEASE_CANDIDATE_VERDICTS`.
  - Test that a record with `lane=technical_preview, verdict=pass` is rejected.
  - Test that a record with `lane=technical_preview, verdict=partial, visibility_status=technical_preview_registered` validates.
- [`tests/test_runtime_model_visibility.py`](../../../tests/test_runtime_model_visibility.py) (assuming it exists; if not, code-grade extends the closest related file):
  - Test that `RegisteredRuntimeVisibleModel("foo", tier="technical_preview")` constructs.
  - Test that `build_runtime_model_visibility` populates both `visible_model_ids` and `technical_preview_visible_model_ids`.
  - Test that DSV4 in the default registry appears in `technical_preview_visible_model_ids` only when artifact is present.
  - Test that an entry without a `tier` defaults to `"default"` (backward compatibility for existing 7 entries).
- [`tests/test_runtime_server.py`](../../../tests/test_runtime_server.py) (or equivalent existing server test):
  - Test that `GET /v1/models` response's `visibility_contract` does NOT have the key `technical_preview_visible_model_ids`.
  - Test that `GET /v1/runtime/model-visibility` response includes `technical_preview_visible_model_ids`.

Code-grade discovers the actual test file names via `ls tests/` and extends the most relevant ones. If a tier-aware visibility test surface does not exist anywhere, a single new test functions block is added to the most-related existing file (e.g., `test_runtime_model_visibility.py`); the rule against new files stands.

### 10.3 Harness changes

No `scripts/bench/` changes. D7 is not a measurement round; the D6/D5 `mainline` and `sustained` subcommands stay as-is.

The model RC ledger row (§7.2) is appended either by:
- the existing `scripts/runtime_model_release_candidate.py` if it accepts manual D7 input, OR
- a one-shot Python script invocation (no new committed script needed; an inline `python -c` or `uv run python -c` invocation in the commit message is acceptable for D7's promotion event)

### 10.4 No new files of any kind

Code-grade MUST NOT create:
- New files under `owlmlx/`
- New `*.py` files under `tests/`
- New `*.py` files under `scripts/`
- New `*.md` files under `docs/` (the D7 spec itself is the only new doc; everything else is an edit to existing docs)

The single allowed new file is the D7 evidence JSONL at `files/evidence/owlmlx/deepseek-v4/d7-technical-preview-visibility/<ts>-d7-technical-preview-visibility.jsonl`.

---

## 11. Review Checklist

Code-grade review MUST verify each box:

- [ ] [`owlmlx/model_release_candidate_schema.py`](../../../owlmlx/model_release_candidate_schema.py) enum tuples have exactly the strings added per §4.1; no extra values added; existing values unchanged.
- [ ] The `lane=technical_preview, verdict=pass` rejection rule is implemented and triggers in `validate_model_release_candidate_record`.
- [ ] [`owlmlx/model_release_candidate_record.py:39-47`](../../../owlmlx/model_release_candidate_record.py:39) DSV4 entry is byte-identical to §5 amended block.
- [ ] `build_dry_run_model_release_candidate_records` blockers branch for `lane=technical_preview` matches §5.
- [ ] [`owlmlx/runtime_model_visibility.py`](../../../owlmlx/runtime_model_visibility.py) `RegisteredRuntimeVisibleModel` has new optional `tier: str = "default"` field; existing 7 entries in `DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS` remain at default tier.
- [ ] DSV4 is added to `DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS` with `tier="technical_preview"`.
- [ ] `RuntimeModelVisibilityGate` has new `technical_preview_visible_model_ids` field after `visible_model_ids`; existing tuple types are preserved.
- [ ] `build_runtime_model_visibility` populates both id tuples; tier-aware branching matches §4.2.
- [ ] `normalize_registered_runtime_visible_models` preserves `tier` from dict-form inputs (default `"default"` when absent).
- [ ] `/v1/models` response excludes `technical_preview_visible_model_ids` key AND excludes DSV4 from any list.
- [ ] `/v1/runtime/model-visibility` response includes both id tuples (the diagnostic surface is intentionally the only place DSV4 appears).
- [ ] [`runtime-capability-matrix.md`](../../source-of-truth/runtime-capability-matrix.md) DSV4 row reads `partial` and has the §6.1 text (or equivalent that names D5 / D6 / D7 evidence + `technical_preview` tier).
- [ ] [`deepseek-v4-bring-up-status.md`](../../source-of-truth/deepseek-v4-bring-up-status.md) §4 is amended per §6.2 (visibility on `/v1/runtime/model-visibility` tier `technical_preview` is now allowed; everything else stays prohibited).
- [ ] D7 decision JSONL at `files/evidence/owlmlx/deepseek-v4/d7-technical-preview-visibility/<ts>-d7-technical-preview-visibility.jsonl` is written and contains every required field from §7.1.
- [ ] `files/evidence/owlmlx/model-release-candidates/cumulative-ledger.jsonl` has a new row passing schema validation with the §7.2 shape.
- [ ] Banned vocabulary scan (`grep -E "parity|replacement|equivalent|production[ _-]?ready|beats|wins|matches" <new files>`) returns no hit in any new string.
- [ ] Full `pytest` run is green; D5 / D6 / D1-D4 related tests all pass without modification.
- [ ] No file under `owlmlx/` is **created** (only existing files are extended); no new test file is created; no new `scripts/bench/*` file is created.
- [ ] [[runtime-capability-matrix.md §6 Label Promotion Rules]] is not bypassed: the row now reads `partial` with explicit evidence pointers; no `supported` label appears for DSV4 anywhere.

---

## 12. Next Round

After D7 design-spec landed (this document):

1. **D7 code-grade in a fresh session** (or current session if user directs `直接干`). Deliverables:
   - Schema enum extensions (~10 LOC)
   - DSV4 data row update (~6 LOC)
   - Runtime visibility tier field + derivation (~40 LOC across 1 file)
   - Server `/v1/models` scrubbing (~10 LOC)
   - Test extensions across 2-3 existing test files (~50 LOC)
   - Doc edits (capability matrix line 96 + bring-up-status §4 + 2 sweep docs)
   - D7 decision JSONL + cumulative ledger row append

2. **Sweep follow-up** (independent of D7 closing): apply the [`02-state-vs-market-gap.md`](../02-state-vs-market-gap.md) §3.5 and [`reference-runtime-comparison-matrix.md`](../../source-of-truth/reference-runtime-comparison-matrix.md) §8 updates that plan-grade §13 listed. These can land in the D7 commit or a follow-up sweep commit.

3. **mlx-lm upstream watch ledger** (per plan §9.3): add [`docs/source-of-truth/mlx-lm-upstream-watch.md`](../../source-of-truth/mlx-lm-upstream-watch.md) as a separate round; not part of D7. When upstream merges DSV4, a separate (post-D7) campaign decides whether to attempt `supported` promotion — that decision is OUT of D7 scope.

This D7 design-spec is **self-contained**: a fresh code-grade session reading only this file, the D5 / D6 specs, the plan-grade doc, and the linked source-of-truth + code files should be able to produce the D7 code-grade artifacts without additional clarification.

---

## 13. Change Log

| Date | Change | By |
|---|---|---|
| 2026-05-27 | Initial D7 design-grade spec, written same day as D5 + D6 passed. Trigger: D5 passed (commit `eda3f0dd`) closed the last evidence prerequisite for the technical_preview promotion. Scope: extend `owlmlx/model_release_candidate_schema.py` enums (`technical_preview` lane, `technical_preview_registered` visibility status, `partial` verdict); add `tier` field to `RegisteredRuntimeVisibleModel` + `RuntimeModelVisibilityGate.technical_preview_visible_model_ids`; route DSV4 to `/v1/runtime/model-visibility` only (not `/v1/models`); update DSV4 row in `DEFAULT_MODEL_RELEASE_CANDIDATES`; update capability matrix DSV4 row to `partial`; soften bring-up-status §4 to allow `technical_preview` visibility tier (keep `supported` and default surface prohibited); write D7 evidence + cumulative ledger row. Relaxes the D5/D6 "no `owlmlx/` package change" rule because the existing schema enums cannot represent the promotion's target values; per [[project-owlmlx-agents-module-as-spec-rule]] extension of existing modules is allowed (only **creation** of new modules is forbidden). | Codex architect loop (with user direction) |
