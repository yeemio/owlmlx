# owlmlx Execution Prompt: Repeatability Harness Scaffold Landing (C-2)

> Date: 2026-05-08
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Round identity: `C-2 scaffold landing` for `owlmlx.repeatability_harness`
> Single executor: one owlmlx executor only
> Required verdict: `scaffold_landed` or `still_blocked`
> Round budget: scaffold-grade only; no measurement loop, no model load

## 1. Mission

Land a brand-new `owlmlx/repeatability_harness.py` scaffold module
plus its source-of-truth architecture doc, tests, prompt, and
checkpoint. The scaffold defines the contract types for a multi-axis
randomized-load repeatability harness; it does **not** actually run
model loads or measurement loops.

The scaffold is the surface a follow-up C-2.1 round will build on. It
freezes:

- the public dataclass shapes (`RepeatabilityRunRecord`,
  `RepeatabilityRunSpec`, `RepeatabilityVerdict`)
- the abstract collaborators (`LoadShapeGenerator`,
  `DegradationDiscriminator`)
- the placeholder concrete subclasses (`DeterministicLoadShape`,
  `BaselineFloorDiscriminator`)
- the placeholder runner `RepeatabilityHarness.run(...)` that produces
  one placeholder record per spec and an `inconclusive:` verdict

This round does **not** advance any rung in
`heavy_weight_repeatability_status.py`, does **not** promote any row
in `native-mlx-backend-capability-matrix.md`, does **not** edit
`reference-runtime-comparison-matrix.md`, and does **not** close any
release-readiness floor. It is a contract-landing round only.

## 2. Fact Base (DO NOT Re-Run Subagent B Research)

The following are research outputs already produced. Treat them as
the fact base for this round; do not re-derive.

### 2.1 Existing primitives — read-only

| File | Why it is read-only this round |
|---|---|
| `owlmlx/heavy_weight_repeatability_status.py` | owns the 5-rung enum; current host reports `supported_host_repeatability_visible` with `repeat_runs=2` on `gemma-4-31B-it`; no measurement loop |
| `owlmlx/host_pressure.py` | `sample_host_pressure(...)` returns a single `HostPressureSnapshot`; not a time series |
| `owlmlx/cache_repeatability_evidence.py` | aggregates per-run `CacheResidencyEvidence` into a 5-rung cache-only repeatability ladder |
| `owlmlx/cache_runtime_observation_harness.py` | `run_cache_runtime_observation_harness` does `load → "warm-1" → "warm-2" → status → unload` against two literal prompts; no randomization, no time series |
| `owlmlx/comparative_evidence_*.py` | implements the cross-runtime comparative harness; key shape includes the 6 measurement fields this scaffold mirrors |
| `tests/test_mlx_native_backend_real_smoke.py` | env-gated single-shot real-model smoke; B-1.2 passed two tests on `Qwen3.6-35B-A3B` |

### 2.2 Required field set

`docs/source-of-truth/comparative-evidence-harness-contract.md` §3.3
requires 6 measurement fields per runtime per run:

- `throughput_tokens_per_second`
- `first_token_latency_ms`
- `peak_resident_set_bytes`
- `wall_clock_ms`
- `completed_request_count`
- `failure_count`

Repeatability requires (contract §4) "at least two repeat runs per
runtime exist with consistent verdict_grade".

### 2.3 Banned vocabulary (verdict text + doc)

Banned in `verdict_text`, the architecture doc, the module docstring,
the test names, and module comments:

- `parity`, `equivalent`, `replaces`, `replacement`,
  `production-ready`, `superior`, `wins`, `beats`, `matches`

The banned-vocab list itself may be enumerated verbatim in the
architecture doc when copying the rule from
`comparative-evidence-harness-contract.md` §5.1; that is the only
place those tokens appear.

`verdict_text` must always begin with `measured:`, `inconclusive:`,
or `rejected:`.

### 2.4 Minimum harness shape

Per research §6, the harness:

- iterates `(run_index ∈ {1..N}, prompt_class ∈ {short, long, …},
  specimen_path)`
- records per run: 6 standard fields + host_pressure snapshot +
  host_forensics delta + backend identity + run_id + recorded_at +
  evidence_pointer
- asserts host-stable via 5 conditions: every run
  `failure_count = 0`, throughput non-degradation,
  `peak_resident_set_bytes` non-monotonic-growth, no new crash
  reports, host_pressure stays out of `host_pressure_block`
- surfaces verdict as a new boolean
  `host_stable_under_repeated_load` embedded in the existing 5-rung
  output, **not** a new rung

The scaffold round implements only the contract types and the
placeholder runner. Real measurement is C-2.1.

## 3. Required Read Order

Before any edit:

1. `docs/source-of-truth/comparative-evidence-harness-contract.md`
2. `docs/source-of-truth/phase45-heavy-weight-repeatability-status.md`
3. `docs/source-of-truth/native-mlx-backend-capability-matrix.md`
4. `docs/source-of-truth/native-mlx-backend-local-candidate-admissibility.md`
5. `docs/source-of-truth/reference-runtime-comparison-matrix.md`
6. `owlmlx/heavy_weight_repeatability_status.py`
7. `owlmlx/host_pressure.py`
8. `owlmlx/cache_repeatability_evidence.py`
9. `owlmlx/cache_runtime_observation_harness.py`
10. `owlmlx/comparative_evidence_record.py`
11. `owlmlx/comparative_evidence_schema.py`

## 4. Deliverables (5 file paths)

### 4.1 `owlmlx/repeatability_harness.py`

Scaffold module. Required content shape:

- module docstring stating: this is the scaffold; ownership boundary
  vs `heavy_weight_repeatability_status.py` (rung enum) and
  `comparative_evidence_runner.py` (single-shot comparative); real
  implementation deferred; banned-vocabulary rule cited
- frozen dataclass `RepeatabilityRunRecord` with the 6 standard
  fields (measurement fields typed `... | None` so the scaffold can
  return `None` while a real round populates real values),
  `failure_count: int`, plus `host_pressure_snapshot: dict | None`,
  `host_forensics_crash_count_delta: int | None`, `backend_identity:
  str`, `run_id: str`, `recorded_at: float`, `prompt_class: str`,
  `specimen_path: str`, `evidence_pointer: str | None`; `to_dict()`
  method
- frozen dataclass `RepeatabilityRunSpec` with `run_index: int`,
  `prompt_class: str`, `specimen_path: str`, `max_tokens: int`,
  `arrival_jitter_s: float`; `to_dict()` method
- frozen dataclass `RepeatabilityVerdict` with
  `host_stable_under_repeated_load: bool`,
  `rejection_reasons: tuple[str, ...]`,
  `verdict_text: str` (begins with `measured:`/`inconclusive:`/
  `rejected:`), `runs_observed: int`, `runs_required: int`;
  `to_dict()` method
- abstract class `LoadShapeGenerator(abc.ABC)` with abstract
  `iter_specs(*, total_runs, classes)`; one concrete subclass
  `DeterministicLoadShape` that produces specs without randomization
- abstract class `DegradationDiscriminator(abc.ABC)` with abstract
  `evaluate(records)`; one concrete subclass
  `BaselineFloorDiscriminator` whose `evaluate` returns
  `verdict_text="inconclusive: scaffold; no real records to evaluate"`
- class `RepeatabilityHarness` with `__init__`,
  `run(*, total_runs, classes)`, `_record_placeholder(spec)`; the
  `run` method iterates `generator.iter_specs(...)` and appends one
  placeholder `RepeatabilityRunRecord` per spec
  (`failure_count = 0`, all measurement fields `None`,
  `evidence_pointer = "scaffold:not_executed"`), then calls
  `discriminator.evaluate(records)` and returns the verdict
- explicit "future extension points" comment block: real backend
  integration, real `host_pressure.sample_host_pressure` integration,
  real `host_forensics` delta, statistical thresholds — comments only

### 4.2 `docs/source-of-truth/repeatability-harness-architecture.md`

Architecture doc, 1500-2000 words, sections:

1. Status / scope / authorship line
2. Why this module exists (Line 6 of the architectural assessment is
   `behind`; existing primitives lack this shape; cite banned vocab)
3. Ownership boundaries (table comparing this module vs existing
   modules)
4. Scaffold contract (public API)
5. Three orthogonal axes (run_index, prompt_class, specimen_path)
6. Per-run record contract (6 fields + provenance)
7. Assertion shape that proves "host-stable" (5 conditions)
8. Promotion-gate coupling (future C-2.1 + real run = Line 6 partial;
   not auto-promote any §3 row)
9. Banned-vocabulary contract (copied from
   `comparative-evidence-harness-contract.md` §5.1)
10. Extension points (not implemented in this scaffold)
11. What this doc does not claim

### 4.3 `tests/test_repeatability_harness.py`

7-10 tests covering:

- `test_run_record_carries_all_six_standard_fields`
- `test_run_record_to_dict_shape_matches_comparative_harness_contract`
- `test_run_spec_carries_run_index_and_prompt_class`
- `test_deterministic_load_shape_yields_total_runs_specs`
- `test_deterministic_load_shape_cycles_through_classes_in_order`
- `test_baseline_floor_discriminator_returns_inconclusive_on_empty_records`
- `test_repeatability_harness_run_returns_inconclusive_verdict_text`
- `test_repeatability_harness_appends_one_placeholder_record_per_spec`
- `test_repeatability_harness_run_does_not_import_mlx_lm`
- `test_verdict_text_must_start_with_measured_inconclusive_or_rejected`

Tests must NOT import `mlx_lm`, NOT import the native backend, NOT
load any model. Pure dataclass + abstract class behavior.

### 4.4 `files/execution-prompts/owlmlx/owlmlx-repeatability-harness-scaffold-landing.md`

This file. Round prompt.

### 4.5 `files/execution-prompts/owlmlx/coordinator-checkpoint-repeatability-harness-scaffold-landed.md`

Coordinator checkpoint. Match the structure of existing
`coordinator-checkpoint-*.md` files in this directory.

## 5. Strict Boundary

### 5.1 Read-only outside the 5 deliverable paths

Do **not** modify:

- `owlmlx/heavy_weight_repeatability_status.py`
- `owlmlx/cache_repeatability_evidence.py`
- `owlmlx/cache_runtime_observation_harness.py`
- `owlmlx/comparative_evidence_*.py`
- `owlmlx/host_pressure.py`
- `owlmlx/runtime/*.py`
- `owlmlx/serving.py`
- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `conftest.py`
- `README.md`
- any existing test file

### 5.2 No real backend invocation

The scaffold module must not import `mlx_lm`. It must not import
`MlxNativeBackend`. It must not load any model. The placeholder
runner is the boundary that holds in this round; tests assert it
directly.

### 5.3 No new dependencies

No `pyproject.toml` edits. No `uv.lock` edits. The scaffold uses
only the standard library (`abc`, `dataclasses`, `time`, `uuid`,
`collections.abc`, `typing`).

### 5.4 No staging, no pytest run

Do not run `git add`. The user stages.
Do not invoke `pytest`. Author tests but do not run them.

### 5.5 Evidence-language calibration

No "is supported" / "is loadable" / "production-ready" / "complete"
language. Always "scaffold contract" / "extension point" /
"not yet bound to backend".

### 5.6 Banned-vocabulary contract

The architecture doc, the module docstring, test names, and module
comments must not use `parity`, `equivalent`, `replaces`,
`replacement`, `production-ready`, `superior`, `wins`, `beats`,
`matches`. Architecture-doc §9 may enumerate them verbatim while
copying the rule from
`comparative-evidence-harness-contract.md` §5.1; that is the only
allowed appearance.

`verdict_text` must always begin with `measured:`, `inconclusive:`,
or `rejected:`.

### 5.7 Run `git status --short` after edits

Confirm round-scope before reporting.

## 6. Acceptance Criteria

Round is `scaffold_landed` when all of the following hold:

1. five deliverable files exist at the exact paths above
2. `python3 -m py_compile owlmlx/repeatability_harness.py
   tests/test_repeatability_harness.py` returns clean
3. the new module does not import `mlx_lm` and does not import
   `MlxNativeBackend`; tests assert this
4. the architecture doc word count is in the `1500..2000` range
5. no banned-vocabulary token appears in `verdict_text` or anywhere
   in the module / tests / doc except the §9 enumeration of the rule
6. `git status --short` reports only the 5 deliverable paths plus the
   directories needed to host them; no edit to any read-only path
7. no `git add` was run; no `pytest` was invoked

If any of those criteria cannot be met, the round closes with
`still_blocked` and the failing criterion frozen exact in the
checkpoint.

## 7. Out of Scope

Explicitly out of scope for this round:

- real model load
- real measurement loop
- real `host_pressure.sample_host_pressure(...)` integration
- real host-forensics delta
- statistical degradation thresholds
- a randomized `LoadShapeGenerator` subclass
- a JSONL ledger for `RepeatabilityRunRecord`
- an HTTP surface
- any modification to `HeavyWeightRuntimeRepeatabilityStatus`
- any promotion of any capability-matrix row
- any update to `reference-runtime-comparison-matrix.md`
- closing any release-readiness backlog floor

These are governed by future rounds (C-2.1 and beyond). This round is
the scaffold contract only.
