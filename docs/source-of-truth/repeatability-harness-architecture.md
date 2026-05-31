# owlmlx Repeatability Harness Architecture

> Status: archived scaffold
> Updated: 2026-05-12
> Authorship: runtime-owned (`owlmlx`)
> Scope: contract types and ownership boundaries for a multi-axis
>        randomized-load repeatability harness; this round freezes the
>        scaffold contract only, not a measurement loop

## 1. Status / Scope / Authorship

This document preserves the archived scaffold contract for the former
``owlmlx.repeatability_harness`` module. The Python module was moved out of
the importable package during the Stage 1 anti-regression cleanup because it
was contract-shaped scaffold code with no runtime consumer.

The archived contract types remain useful as history
(`RepeatabilityRunRecord`, `RepeatabilityRunSpec`, `RepeatabilityVerdict`,
`LoadShapeGenerator`, `DegradationDiscriminator`, `RepeatabilityHarness`), but
they are not an active owlmlx runtime API.

The archived Python module is:

- `archive/spec-layer-v0/owlmlx/repeatability_harness.py`

That archived module was governed by this doc, and by
`docs/source-of-truth/comparative-evidence-harness-contract.md` for the
six standard measurement field names and the verdict-text vocabulary.

This doc does not move any rung in
`owlmlx/heavy_weight_repeatability_status.py`; it does not promote any
row in `docs/source-of-truth/native-mlx-backend-capability-matrix.md`;
it does not edit
`docs/source-of-truth/reference-runtime-comparison-matrix.md`. It
only freezes the scaffold contract.

## 2. Why This Module Exists

`docs/source-of-truth/reference-runtime-comparison-matrix.md` records,
in §8, that `owlmlx`'s closest remaining gaps concentrate in:

- host-stable execution confidence
- heavy-weight repeatability
- deeper cache/scheduler closure

Of these, the seven-line architectural assessment Line 6 — host-stable
execution confidence — is presently labelled `behind`. To honestly move
that label from `behind` to `partial`, `owlmlx` needs a runtime-owned
multi-axis harness that demonstrates the runtime survives a randomized
sequence of prompts on an admitted candidate without:

- introducing a new failure
- regressing throughput across the run window
- monotonically growing peak resident set
- producing new crash reports
- entering host-pressure block mid-run

None of the existing primitives owns that shape:

> **Update (2026-05-30)**: three modules referenced below and in the §3
> table — `heavy_weight_repeatability_status.py`,
> `cache_repeatability_evidence.py`, and
> `cache_runtime_observation_harness.py` — were since moved to
> `archive/spec-layer-v0/owlmlx/` in the Stage-1 spec-layer archival
> (`1475e339`); their `owlmlx/...` paths here are historical.
> `host_pressure.py` and `comparative_evidence_*.py` remain live in
> `owlmlx/`. This is an archived-scaffold doc; module descriptions are
> retained as the as-authored record.

- `owlmlx/heavy_weight_repeatability_status.py` is a rung-state machine
  over **declared** inputs (`supported_host_proof_visible`,
  `supported_host_repeat_runs`); it does not run a measurement loop.
- `owlmlx/host_pressure.py` exposes
  `sample_host_pressure(...)` which returns a single snapshot, not a
  time series across N runs.
- `owlmlx/cache_repeatability_evidence.py` aggregates per-run
  `CacheResidencyEvidence` records into a 5-rung cache-repeatability
  ladder; its scope is cache, not whole-runtime stability.
- `owlmlx/cache_runtime_observation_harness.py`
  (`run_cache_runtime_observation_harness`) does
  `load → "warm-1" → "warm-2" → status → unload` against two literal
  prompts, with no randomization, no time series, and no host-pressure
  integration.
- `owlmlx/comparative_evidence_*.py` implements the **single-shot**
  cross-runtime comparative harness defined by
  `docs/source-of-truth/comparative-evidence-harness-contract.md`; it
  is contract-shaped for `(host_class, workload_class)` pairs but is
  not multi-axis randomized within one runtime.

The repeatability harness fills exactly that gap.

The repeatability harness is also bound by the comparative-evidence
banned-vocabulary contract: see §9 below. The verdict-text rule is the
only contract-text rule shared across both harnesses.

## 3. Ownership Boundaries

| Module / surface | Owns |
|---|---|
| `owlmlx/heavy_weight_repeatability_status.py` | the 5-rung enum (`local_blocked`, `local_preconditions_incomplete`, `budget_fit_heavy_boundary_entered`, `host_ready_not_repeated`, `supported_host_repeatability_visible`) over declared inputs; produces `HeavyWeightRuntimeRepeatabilityStatus` |
| `owlmlx/host_pressure.py` | one-shot `HostPressureSnapshot` |
| `owlmlx/cache_repeatability_evidence.py` | per-run `CacheResidencyEvidence` aggregation, cache-only repeatability ladder |
| `owlmlx/cache_runtime_observation_harness.py` | a fixed two-prompt warm-warm runner against the subprocess backend, used for cache-residency evidence only |
| `owlmlx/comparative_evidence_*.py` | single-shot cross-runtime comparative records, ledger, HTTP surface, schema validation |
| `archive/spec-layer-v0/owlmlx/repeatability_harness.py` | archived scaffold contract types for a multi-axis randomized-load repeatability harness; no measurement loop |

Non-duplication: this module is the only place where a `(run_index,
prompt_class, specimen_path)` triple is the unit of work. None of the
other modules above iterate that triple. None of the other modules
above carries `host_stable_under_repeated_load` as a verdict field.

This module deliberately does **not** duplicate:

- the 5-rung enum (it stays in
  `heavy_weight_repeatability_status.py`)
- the comparative-evidence record shape (this module's per-run record
  is parallel in the six measurement fields, but is a different
  surface; cross-runtime comparison is not in scope here)
- ledger / HTTP behavior (a future round can add a ledger if needed)

## 4. Scaffold Contract

The public API is:

- `RepeatabilityRunRecord` — frozen dataclass with the 6 standard
  measurement fields plus 8 additive provenance fields; `to_dict()`
  returns a JSON-ready mapping
- `RepeatabilityRunSpec` — frozen dataclass with `run_index`,
  `prompt_class`, `specimen_path`, `max_tokens`, `arrival_jitter_s`;
  `to_dict()` returns a JSON-ready mapping
- `RepeatabilityVerdict` — frozen dataclass with
  `host_stable_under_repeated_load: bool`,
  `rejection_reasons: tuple[str, ...]`, `verdict_text: str`,
  `runs_observed: int`, `runs_required: int`; `to_dict()` returns a
  JSON-ready mapping
- `LoadShapeGenerator` — `abc.ABC` with one abstract method,
  `iter_specs(*, total_runs, classes)` returning an iterable of
  `RepeatabilityRunSpec`
- `DeterministicLoadShape(LoadShapeGenerator)` — scaffold concrete
  subclass that cycles classes deterministically and emits exactly
  `total_runs` specs
- `DegradationDiscriminator` — `abc.ABC` with one abstract method,
  `evaluate(records)` returning a `RepeatabilityVerdict`
- `BaselineFloorDiscriminator(DegradationDiscriminator)` — scaffold
  concrete subclass that returns a `verdict_text` beginning with
  `inconclusive:` for any input
- `RepeatabilityHarness` — concrete runner with `generator`,
  `discriminator`, optional `backend_identity`; `run(*, total_runs,
  classes)` iterates specs, appends one placeholder
  `RepeatabilityRunRecord` per spec, calls
  `discriminator.evaluate(records)`, and returns the verdict

The placeholder runner is the boundary that holds in this round. It
intentionally does not import `mlx_lm`, does not touch
`MlxNativeBackend`, does not call `host_pressure.sample_host_pressure`,
does not read crash reports, and does not load any model. Tests assert
this directly.

## 5. Three Orthogonal Axes

A real implementation of this harness varies along three axes:

1. **`run_index`** ∈ {0..N-1}
   - N must be at least 20 to give the discriminator enough samples
     for non-degradation assertions; the scaffold accepts any non-
     negative integer for testability.
2. **`prompt_class`** drawn from a tuple of at least 2 classes
   - Vocabulary mirrors
     `comparative-evidence-harness-contract.md` §3.1:
     `single_prompt_short`, `single_prompt_long`,
     `multi_prompt_serial`, `multi_prompt_aggregated`.
   - The scaffold cycles classes in declared order; randomization is
     a future extension point (§10).
3. **`specimen_path`** drawn from at least 1 admitted candidate per
   `docs/source-of-truth/native-mlx-backend-local-candidate-admissibility.md`
   - The scaffold accepts any string; admissibility validation is a
     future extension point.

These three axes are deliberately orthogonal. A real run sweeps over
their cartesian product; the scaffold sweeps `run_index × classes` and
fixes one specimen.

## 6. Per-Run Record Contract

`RepeatabilityRunRecord` carries:

Six standard measurement fields (key names match
`comparative-evidence-harness-contract.md` §3.3 exactly):

- `throughput_tokens_per_second: float | None`
- `first_token_latency_ms: float | None`
- `peak_resident_set_bytes: int | None`
- `wall_clock_ms: float | None`
- `completed_request_count: int | None`
- `failure_count: int`

Eight additive provenance fields specific to repeatability:

- `host_pressure_snapshot: dict | None` — JSON-shaped snapshot from
  `owlmlx.host_pressure.sample_host_pressure(...)` at run start; the
  scaffold leaves this `None`
- `host_forensics_crash_count_delta: int | None` — delta in the
  configured crash-report directory across the run window; the
  scaffold leaves this `None`
- `backend_identity: str` — e.g. `"mlx-native"` or
  `"mlx-lm-subprocess"`; scaffold default is
  `"scaffold:not_bound"`
- `run_id: str` — UUID per record
- `recorded_at: float` — POSIX timestamp at record construction
- `prompt_class: str` — copy of the spec's prompt class
- `specimen_path: str` — copy of the spec's specimen path
- `evidence_pointer: str | None` — repo-relative path to raw
  artifacts; scaffold value is `"scaffold:not_executed"` so consumers
  cannot mistake a placeholder for evidence

In the scaffold, every measurement field is `None` and `failure_count`
is `0`; there is no path through `RepeatabilityHarness.run` that
populates real values. A real implementation would populate them from
backend telemetry.

The verdict-text-banned-vocabulary rule applies to
`RepeatabilityVerdict.verdict_text` (see §9). It does not apply to
`RepeatabilityRunRecord` because per-run records do not carry a
verdict.

## 7. Assertion Shape That Proves "Host-Stable"

A full implementation must assert all of the following before
`host_stable_under_repeated_load = True`:

1. every record has `failure_count == 0`
2. throughput shows no monotone degradation across `run_index` (a
   published threshold lives in this doc when implemented)
3. `peak_resident_set_bytes` does not grow monotonically across
   `run_index` (a published delta-bound lives in this doc when
   implemented)
4. `host_forensics_crash_count_delta == 0` for every record
5. no record carries a `host_pressure_snapshot` whose serialized state
   indicates `host_pressure_block`

If any one of those five conditions fails, the verdict must be
`rejected:` with the exact failed condition listed in
`rejection_reasons`. If too few runs were collected to evaluate the
five conditions, the verdict must be `inconclusive:` with a
`runs_observed < runs_required` reason.

This scaffold round does not implement those assertions; the placeholder
discriminator always returns `inconclusive:`.

## 8. Promotion-Gate Coupling

A future C-2.1 implementation round, once landed, would let:

- `docs/source-of-truth/reference-runtime-comparison-matrix.md`
  Line 6 (host-stable execution confidence) move from `behind` to
  `partial`
- `owlmlx/heavy_weight_repeatability_status.py` carry an additive
  boolean `host_stable_under_repeated_load` inside the existing
  `HeavyWeightRuntimeRepeatabilityStatus` output, **without**
  introducing a new rung

It would **not** auto-promote any
`docs/source-of-truth/native-mlx-backend-capability-matrix.md` §3 row.
Capability-matrix promotions still require an §1a walkthrough on the
specific row plus the existing per-row evidence rules; running this
harness is necessary but not sufficient.

It would **not** close `release-readiness-backlog.md` floor 3.5; that
floor is governed by the comparative-evidence harness contract, not
this one.

This scaffold round itself (the C-2 round) **does not** advance any
gate. It only lands the contract types so a follow-up round can build
the measurement loop on a frozen surface.

## 9. Banned-Vocabulary Contract

Copied here from
`docs/source-of-truth/comparative-evidence-harness-contract.md`
§5.1 because this doc inherits the same vocabulary rule.

`RepeatabilityVerdict.verdict_text` must follow the form:

- `"measured: <fact statement on the verdict>"`
- or `"inconclusive: <reason>"`
- or `"rejected: <reason>"`

The following words are banned from `verdict_text`, this document, the
module docstring, the test names, and any comment in the module:

- `parity`
- `equivalent`
- `replaces`
- `replacement`
- `production-ready`
- `superior`
- `wins`
- `beats`
- `matches`

This rule is enforced by `release-readiness-backlog.md` section 4.3.
It is enforced for this module on review, not (yet) by an automated
schema validator. A future round can wire validation into a schema
module parallel to `owlmlx/comparative_evidence_schema.py`.

## 10. Extension Points (Not Implemented in This Scaffold)

The module file ends with an explicit comment block listing the
extensions a real round must add. They are restated here so the doc
captures them too.

1. **Real backend integration.** A `RealBackendHarness` subclass binds
   to `owlmlx.runtime.mlx_native_backend.MlxNativeBackend` (or
   `MlxLmSubprocessBackend`) lazily inside the subclass; the base
   module must remain free of `mlx_lm` import side effects.
2. **Real measurement collection.** Populate the six standard fields
   from the actual `stream_generate` event flow, mirroring the key
   shape of `ComparativeEvidenceMeasurement`.
3. **Real host-pressure integration.** Call
   `owlmlx.host_pressure.sample_host_pressure(...)` before and after
   each spec; reject any record whose snapshot enters
   `host_pressure_block`.
4. **Real host-forensics delta.** Compute a crash-count delta around
   each run window from the configured crash-report directory.
5. **Statistical degradation thresholds.** Implement
   `DegradationDiscriminator.evaluate(...)` to assert all five
   conditions in §7. Thresholds must be published in this doc before
   the implementation round, per existing source-of-truth discipline.
6. **Wire-up to existing rung output.** Extend
   `HeavyWeightRuntimeRepeatabilityStatus` (in
   `heavy_weight_repeatability_status.py`) with an additive boolean
   `host_stable_under_repeated_load`. Do not introduce a new rung.
7. **Optional schema validation.** Add an
   `owlmlx/repeatability_harness_schema.py` parallel to
   `comparative_evidence_schema.py` if a public consumer ever needs
   to validate emitted records.

## 11. What This Doc Does Not Claim

- it does not claim host-stable execution has been demonstrated on
  any host
- it does not claim the runtime survives randomized load
- it does not claim Line 6 of the seven-line architectural assessment
  has moved
- it does not claim any native-mlx-backend capability-matrix row has
  been promoted
- it does not claim any release-readiness backlog floor has closed
- it does not claim a measurement loop exists
- it does not claim the harness has been bound to any backend
- it does not claim a randomized load shape has been implemented; the
  one shipped concrete `LoadShapeGenerator` is intentionally
  deterministic so tests can assert spec ordering

It only claims:

- the scaffold contract types now exist as a runtime-owned module
- the scaffold runner produces an honest `inconclusive:` verdict
  without invoking any backend
- a follow-up round has a frozen surface to build a real measurement
  loop on
