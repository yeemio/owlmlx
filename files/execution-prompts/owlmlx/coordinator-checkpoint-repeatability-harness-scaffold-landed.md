# owlmlx Coordinator Checkpoint — Repeatability Harness Scaffold: scaffold_landed

## Verdict

- `repeatability_harness_scaffold_landed`

This checkpoint records the close of the C-2 round on the runtime-
owned multi-axis randomized-load repeatability harness. The contract
types are now landed as a runtime-owned module
(`owlmlx/repeatability_harness.py`), the architecture doc is frozen
(`docs/source-of-truth/repeatability-harness-architecture.md`), and a
focused test file asserts the scaffold boundary
(`tests/test_repeatability_harness.py`). Every contract type is
**scaffold-grade** until a follow-up C-2.1 round binds the harness to
a real backend and runs an actual measurement loop.

## What This Checkpoint Is

This is a contract-landing marker, not a capability-claim marker. It
says: the public shape of the repeatability harness holds; the
generator / discriminator / harness composition runs end-to-end on
placeholder data; and the boundary against `mlx_lm` import is asserted
by a test. It does **not** say the runtime is host-stable under
randomized load on any host. It does **not** advance any rung in the
existing 5-rung repeatability ladder.

## What Is Now Frozen Exact

- a runtime-owned scaffold module
  `owlmlx/repeatability_harness.py` with:
  - frozen dataclass `RepeatabilityRunRecord` carrying the 6 standard
    measurement fields (`throughput_tokens_per_second`,
    `first_token_latency_ms`, `peak_resident_set_bytes`,
    `wall_clock_ms`, `completed_request_count`, `failure_count`) plus
    8 additive provenance fields (`host_pressure_snapshot`,
    `host_forensics_crash_count_delta`, `backend_identity`,
    `run_id`, `recorded_at`, `prompt_class`, `specimen_path`,
    `evidence_pointer`); `to_dict()` method exposes JSON-ready keys
    that exactly match the
    `comparative-evidence-harness-contract.md` §3.3 vocabulary
  - frozen dataclass `RepeatabilityRunSpec` with `run_index`,
    `prompt_class`, `specimen_path`, `max_tokens`,
    `arrival_jitter_s`; `to_dict()` method
  - frozen dataclass `RepeatabilityVerdict` with
    `host_stable_under_repeated_load: bool`,
    `rejection_reasons`, `verdict_text`, `runs_observed`,
    `runs_required`; `to_dict()` method; `verdict_text` is required
    to begin with `measured:`, `inconclusive:`, or `rejected:` per
    the comparative-evidence-harness-contract.md §5.1 rule
  - abstract class `LoadShapeGenerator(abc.ABC)` with abstract
    `iter_specs(*, total_runs, classes)`
  - concrete subclass `DeterministicLoadShape` that cycles classes
    deterministically (not randomized; randomization is a future
    extension point)
  - abstract class `DegradationDiscriminator(abc.ABC)` with abstract
    `evaluate(records)`
  - concrete subclass `BaselineFloorDiscriminator` whose `evaluate`
    returns `verdict_text="inconclusive: scaffold; no real records to
    evaluate"` for an empty record set, and an `inconclusive:` verdict
    for any populated set as well (no real measurements are present)
  - class `RepeatabilityHarness` whose
    `run(*, total_runs, classes)` iterates the generator, appends one
    placeholder `RepeatabilityRunRecord` per spec
    (`failure_count = 0`, all measurement fields `None`,
    `evidence_pointer = "scaffold:not_executed"`), then delegates to
    `discriminator.evaluate(records)` and returns the verdict
  - explicit "future extension points" comment block enumerating real
    backend integration, real measurement collection, real host-
    pressure integration, real host-forensics delta, statistical
    thresholds, wire-up to `HeavyWeightRuntimeRepeatabilityStatus`,
    and optional schema validation
- `mlx_lm` is **not** imported by the scaffold module; the native
  backend is **not** imported; no model is loaded; this boundary is
  asserted directly by the test
  `test_repeatability_harness_run_does_not_import_mlx_lm`
- a runtime-owned source-of-truth doc
  `docs/source-of-truth/repeatability-harness-architecture.md`
  (1500-2000 words) covering: status / scope / authorship; why this
  module exists; ownership boundaries; scaffold contract; three
  orthogonal axes; per-run record contract; assertion shape that
  proves "host-stable" (5 conditions); promotion-gate coupling;
  banned-vocabulary contract copied from
  `comparative-evidence-harness-contract.md` §5.1; extension points;
  what this doc does not claim

### New tests

- `tests/test_repeatability_harness.py` — 10 scaffold tests:
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

### Test invocation

The executor phase treated this as a scaffold-landing round and
authored tests without using the scaffold itself as promotion
evidence. Coordinator review later ran:

```bash
.venv/bin/python -m pytest \
  tests/test_cache_manager.py \
  tests/test_repeatability_harness.py \
  tests/test_memory_actuator.py \
  tests/test_serving_hardening.py \
  tests/test_mlx_native_backend.py \
  tests/test_mlx_native_backend_post_claim_invariants.py \
  tests/test_mlx_native_backend_real_upstream_binding.py \
  tests/test_mlx_native_backend_real_smoke.py -q
```

Result: `83 passed, 3 skipped` (plus upstream warnings). C-2's scoped
file contributed 10 passed tests.

### Existing primitives left untouched

- `owlmlx/heavy_weight_repeatability_status.py` — read-only this
  round; the 5-rung enum
  (`local_blocked`, `local_preconditions_incomplete`,
  `budget_fit_heavy_boundary_entered`,
  `host_ready_not_repeated`, `supported_host_repeatability_visible`)
  is unchanged; current host still reports
  `supported_host_repeatability_visible` with `repeat_runs=2` on
  `gemma-4-31B-it`
- `owlmlx/host_pressure.py` — read-only this round
- `owlmlx/cache_repeatability_evidence.py` — read-only this round
- `owlmlx/cache_runtime_observation_harness.py` — read-only this round
- `owlmlx/comparative_evidence_*.py` — read-only this round
- `owlmlx/runtime/*.py` — read-only this round
- `owlmlx/serving.py` — read-only this round
- `pyproject.toml`, `uv.lock`, `.python-version`, `conftest.py`,
  `README.md` — all read-only this round; no new dependency
- every existing test file — read-only this round

## Current Frozen Active Seam

This checkpoint does not move the active phase45 seam. The
repeatability harness scaffold is parallel and is not invoked by any
published serving path or by any rung-evaluation flow.

## What This Checkpoint Closes

The repeatability harness scaffold round (C-2) is closed in
contract-landed form:

- the public contract types exist as a runtime-owned module
- the scaffold runner produces a placeholder record per spec and an
  honest `inconclusive:` verdict without invoking any backend
- the architecture doc freezes the surface a future C-2.1 round
  builds on
- the boundary against `mlx_lm` import is asserted by a test, not
  just by convention

## What This Checkpoint Does Not Claim

- the runtime is host-stable under randomized load on any host
- a measurement loop exists
- any real backend is bound to the harness
- any rung in `heavy_weight_repeatability_status.py` has moved
- any row in `native-mlx-backend-capability-matrix.md` has been
  promoted
- Line 6 of the seven-line architectural assessment in
  `reference-runtime-comparison-matrix.md` has moved from `behind` to
  any other label
- any release-readiness backlog floor has been closed
- the scaffold has been bound to `MlxNativeBackend` or
  `MlxLmSubprocessBackend`
- a randomized `LoadShapeGenerator` subclass exists; the only
  shipped concrete subclass is intentionally deterministic so tests
  can assert spec ordering
- a JSONL ledger or HTTP surface exists for the new record shape

## What Crossed The Threshold

The runtime-owned source-of-truth surface
`docs/source-of-truth/repeatability-harness-architecture.md` is now
the published contract for a multi-axis randomized-load
repeatability harness. Before this round, that surface did not exist
in the repository: research §6 named the required shape, but no doc
or module owned it. After this round, the contract is frozen and a
follow-up round can build the measurement loop on a stable surface
without re-deriving the field set.

## Notable Implementation Choice

`DeterministicLoadShape` is intentionally **not** randomized in this
round, even though the architecture doc names randomization as the
real-world load-shape requirement. The reason is testability: the
scaffold tests assert the exact class-cycling order, which would be
unstable under any RNG seed handling discipline. A randomized
subclass is enumerated as extension point §10.1 / §10.5 of the
architecture doc; it must be added in the C-2.1 round alongside the
real measurement collection so RNG seed handling and reproducibility
can be designed together.

## Next Authorized Round

The next authorized round is:

- **C-2.1: Repeatability Harness — Real Backend Binding + One
  Measured Run On An Admitted Candidate**

That round will:

- add a `RealBackendHarness(RepeatabilityHarness)` subclass that
  binds lazily to `owlmlx.runtime.mlx_native_backend.MlxNativeBackend`
  inside the subclass body (the base scaffold module continues to be
  free of `mlx_lm` import side effects)
- replace `_record_placeholder` with a code path that runs
  `load → stream_generate → unload` on an admitted candidate per
  `docs/source-of-truth/native-mlx-backend-local-candidate-admissibility.md`,
  populates the 6 measurement fields from real backend telemetry,
  and samples `owlmlx.host_pressure.sample_host_pressure(...)` before
  and after each run
- implement a real `DegradationDiscriminator` subclass that asserts
  the 5 host-stability conditions named in
  `docs/source-of-truth/repeatability-harness-architecture.md` §7
- publish the statistical thresholds (throughput non-degradation
  delta, peak-RSS non-monotonic-growth bound) in the architecture
  doc **before** writing the discriminator code, per existing
  source-of-truth discipline
- env-gate the real-backend smoke (parallel to
  `tests/test_mlx_native_backend_real_smoke.py`) so CI default lanes
  do not download or load models
- on a successful run, append a `host_stable_under_repeated_load:
  bool` field to `HeavyWeightRuntimeRepeatabilityStatus` (additive;
  the 5-rung enum stays frozen)
- on a successful run, allow Line 6 of the seven-line architectural
  assessment in `reference-runtime-comparison-matrix.md` to move
  from `behind` to `partial`
- explicitly **not** promote any
  `native-mlx-backend-capability-matrix.md` §3 row; capability-row
  promotions still require the existing per-row §1a walkthrough
- explicitly **not** close any release-readiness backlog floor on
  its own
