# owlmlx Non-Resident Loadability Lineage

> Status: authoritative
> Updated: 2026-04-25
> Scope: runtime-only loadability lineage classification for non-resident model targets

## 1. Purpose

This document freezes the runtime-owned answer to the next floor-`3.3`
sub-question:

**For a non-resident target model, does `owlmlx` own enough visibility,
artifact, and lineage truth to call the target loadable before whole-request
gate claim?**

It is a narrow lineage-classification contract. It does not implement an
automatic loader, perform a speculative load probe, or weaken the post-claim
`GenerationGate` invariants.

## 2. Owned Contract

`owlmlx/nonresident_loadability_lineage.py` now owns:

- `build_nonresident_loadability_lineage(...)`
- `nonresident_loadability_lineage_to_dict(...)`

Runtime transport surface:

- `GET /v1/runtime/nonresident-loadability-lineage`
  - query parameters:
    - `model_id` — target non-resident model id (required for non-`unknown`)

The loadability lineage registry is **not** a query parameter. It is connected
at `create_app(...)` construction time:

- `loadability_lineage_records: dict[str, ModelLineage | dict] | None`
- `visibility_models_root: str | None`
- `visibility_registry: list[RegisteredRuntimeVisibleModel] | None`

Contract:

- `surface = "owlmlx.nonresident_loadability_lineage"`
- `version = "v1"`

Stable sections:

- `summary`
- `reason`
- `visibility`
- `lineage`
- `blocking_signals`
- `decision_support`
- `inputs`
- `missing_signals`

## 3. Decision Vocabulary

Exactly one of:

- `known_loadable`
  - target is registered in the runtime-owned visibility registry
  - target's local artifact directory and `config.json` are present per
    `runtime_model_visibility`
  - lineage record exists in the loadability lineage registry
  - lineage record validates under `model_lineage.validate_model_lineage`
    for the requested lifecycle state
  - lineage record's `local_path` is aligned with the visibility entry's
    `local_model_dir`
- `not_loadable`
  - target is missing from the runtime-owned visibility registry
  - required local artifact or config truth is absent
  - lineage record is missing for a visible target
  - lineage record fails validation for the lifecycle state
  - lineage record's `local_path` does not match the visibility entry's
    `local_model_dir`
- `unknown`
  - no `model_id` was supplied
  - the runtime visibility gate was not connected
  - the loadability lineage source was not connected
  - `unknown` is never used to hide a deterministic `not_loadable`

## 4. Runtime-Owned Source Rule

Source of truth is runtime-owned, never per-request:

- visibility registry comes from `runtime_model_visibility`
  (`DEFAULT_REGISTERED_RUNTIME_VISIBLE_MODELS`, plus optional override at
  app construction time) and the artifact/config presence gate is owned by
  that module
- loadability lineage records are passed at `create_app(...)` construction
  time, not as a query hint
- lineage validation is delegated to `owlmlx.model_lineage`, which already
  owns the served-weight provenance schema

Not acceptable as closure evidence:

- `?known_loadable_model_ids=...` query hint as the only source
- deriving loadability from the literal value of `model_id`
- assuming every visible model is loadable without lineage validation
- executing a speculative load probe as the definition of lineage

## 5. Round-Trip Inputs

For every decision the contract reports both inputs and outputs of the round
trip:

- `visibility.registered`, `visibility.visible`, `visibility.block_reason`,
  `visibility.local_model_dir`, `visibility.config_path`,
  `visibility.models_root`
- `lineage.record_present`, `lineage.validation_valid`,
  `lineage.validation_missing_fields`, `lineage.validation_warnings`,
  `lineage.target_alignment`, `lineage.expected_local_path`,
  `lineage.actual_local_path`, `lineage.record`
- `inputs.visibility_truth_status` and
  `inputs.loadability_lineage_truth_status` describe whether each runtime-
  owned source is connected

## 6. Boundary With Other Contracts

This contract is intentionally bounded:

- it does not select pressure-eviction victims; that belongs to release
  floor `3.2`
- it does not run a recovery loop; that belongs to release floor `3.4`
- it does not implement an automatic non-resident loader; load remains
  explicit operator action through `/v1/load`
- it does not bypass `GenerationGate` post-claim invariants
- it does not mutate `model_lineage`, `runtime_model_visibility`, or any
  residency / pressure / recovery surface; it consumes them

## 7. Integration With Non-Resident Admission Policy

`owlmlx.nonresident_model_admission_policy` now consumes this contract
through a `loadability_lineage` parameter on its builder:

- when loadability lineage returns `known_loadable`, admission can return
  `admit_and_load` **without** any `known_loadable_model_ids` operator hint
- when loadability lineage returns `not_loadable`, admission rejects with
  reason code
  `runtime_owned_loadability_lineage_says_not_loadable`, even if the
  operator hint is supplied
- when loadability lineage returns `unknown` (source not connected), the
  policy falls back to the operator-supplied hint as a labeled legacy
  fallback only; the policy payload's
  `inputs.loadability_lineage.loadability_lineage_truth_status` is
  `missing` in that case

`missing_signals.runtime_owned_non_resident_loadability_lineage` is removed
from the admission policy payload only when this contract is connected and
returns `known_loadable` or `not_loadable`. While the contract returns
`unknown`, that signal stays present so future rounds can distinguish
"contract not connected" from "contract connected and decisive".

## 8. What This Does Not Claim

It does not claim:

- an automatic non-resident loader exists
- the loadability lineage registry is exhaustive across all hosts
- lineage validation is sufficient for runtime safety; it is one of several
  signals
- pressure-ranked eviction or recovery supervision are closed
- continuous batching, multi-worker scheduling, parity, replacement, or
  release readiness against `oMLX` or `vMLX`

It only claims:

- `owlmlx` now owns one runtime-owned classifier for non-resident
  loadability lineage
- the classification is deterministic given runtime-owned visibility and
  lineage inputs
- the classifier exposes its blockers and missing signals rather than hiding
  them as silent unknowns
