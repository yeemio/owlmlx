"""Scaffold tests for ``owlmlx.repeatability_harness``.

These tests exercise only the contract types, the deterministic load
shape, the placeholder discriminator, and the placeholder harness
runner. They explicitly do NOT import ``mlx_lm``, do NOT import
``MlxNativeBackend``, and do NOT load any model. The scaffold module
under test is required to honor that boundary as well, and the test
``test_repeatability_harness_run_does_not_import_mlx_lm`` enforces it.
"""

from __future__ import annotations

import sys

from owlmlx.repeatability_harness import (
    BaselineFloorDiscriminator,
    DeterministicLoadShape,
    RepeatabilityHarness,
    RepeatabilityRunRecord,
    RepeatabilityRunSpec,
    RepeatabilityVerdict,
)


# ---------------------------------------------------------------------------
# Per-run record contract
# ---------------------------------------------------------------------------


def _make_record(**overrides: object) -> RepeatabilityRunRecord:
    base: dict[str, object] = {
        "throughput_tokens_per_second": None,
        "first_token_latency_ms": None,
        "peak_resident_set_bytes": None,
        "wall_clock_ms": None,
        "completed_request_count": None,
        "failure_count": 0,
        "host_pressure_snapshot": None,
        "host_forensics_crash_count_delta": None,
        "backend_identity": "scaffold:not_bound",
        "run_id": "test-run-id",
        "recorded_at": 0.0,
        "prompt_class": "single_prompt_short",
        "specimen_path": "/tmp/specimen",
        "evidence_pointer": None,
    }
    base.update(overrides)
    return RepeatabilityRunRecord(**base)  # type: ignore[arg-type]


def test_run_record_carries_all_six_standard_fields() -> None:
    """The 6 standard measurement fields exist on the dataclass."""

    record = _make_record()

    expected_fields = {
        "throughput_tokens_per_second",
        "first_token_latency_ms",
        "peak_resident_set_bytes",
        "wall_clock_ms",
        "completed_request_count",
        "failure_count",
    }

    for name in expected_fields:
        assert hasattr(record, name), f"missing measurement field: {name}"

    # the scaffold leaves measurement fields None except failure_count
    assert record.throughput_tokens_per_second is None
    assert record.first_token_latency_ms is None
    assert record.peak_resident_set_bytes is None
    assert record.wall_clock_ms is None
    assert record.completed_request_count is None
    assert record.failure_count == 0


def test_run_record_to_dict_shape_matches_comparative_harness_contract() -> None:
    """``to_dict()`` exposes the six standard measurement field names.

    The names must exactly match
    ``comparative-evidence-harness-contract.md`` §3.3 so a future real
    record can flow into the comparative ledger without re-keying.
    """

    record = _make_record(
        throughput_tokens_per_second=1.0,
        first_token_latency_ms=2.0,
        peak_resident_set_bytes=3,
        wall_clock_ms=4.0,
        completed_request_count=5,
        failure_count=0,
    )

    payload = record.to_dict()

    required_measurement_keys = {
        "throughput_tokens_per_second",
        "first_token_latency_ms",
        "peak_resident_set_bytes",
        "wall_clock_ms",
        "completed_request_count",
        "failure_count",
    }
    assert required_measurement_keys.issubset(payload.keys())

    additive_keys = {
        "host_pressure_snapshot",
        "host_forensics_crash_count_delta",
        "backend_identity",
        "run_id",
        "recorded_at",
        "prompt_class",
        "specimen_path",
        "evidence_pointer",
    }
    assert additive_keys.issubset(payload.keys())


def test_run_spec_carries_run_index_and_prompt_class() -> None:
    """``RepeatabilityRunSpec`` exposes the three orthogonal axes."""

    spec = RepeatabilityRunSpec(
        run_index=7,
        prompt_class="single_prompt_long",
        specimen_path="/tmp/specimen-a",
        max_tokens=16,
        arrival_jitter_s=0.0,
    )

    assert spec.run_index == 7
    assert spec.prompt_class == "single_prompt_long"
    assert spec.specimen_path == "/tmp/specimen-a"
    payload = spec.to_dict()
    assert payload["run_index"] == 7
    assert payload["prompt_class"] == "single_prompt_long"
    assert payload["specimen_path"] == "/tmp/specimen-a"
    assert payload["max_tokens"] == 16


# ---------------------------------------------------------------------------
# Deterministic load shape
# ---------------------------------------------------------------------------


def test_deterministic_load_shape_yields_total_runs_specs() -> None:
    """The deterministic generator produces exactly ``total_runs`` specs."""

    gen = DeterministicLoadShape(specimen_path="/tmp/specimen-a", max_tokens=8)

    specs = list(
        gen.iter_specs(
            total_runs=6,
            classes=("single_prompt_short", "single_prompt_long"),
        )
    )
    assert len(specs) == 6
    assert all(isinstance(s, RepeatabilityRunSpec) for s in specs)
    assert all(s.specimen_path == "/tmp/specimen-a" for s in specs)
    assert all(s.max_tokens == 8 for s in specs)


def test_deterministic_load_shape_cycles_through_classes_in_order() -> None:
    """Class assignment cycles in declared order; not randomized."""

    gen = DeterministicLoadShape(specimen_path="/tmp/specimen-a")

    specs = list(
        gen.iter_specs(
            total_runs=5,
            classes=("single_prompt_short", "single_prompt_long"),
        )
    )

    classes_seen = [s.prompt_class for s in specs]
    assert classes_seen == [
        "single_prompt_short",
        "single_prompt_long",
        "single_prompt_short",
        "single_prompt_long",
        "single_prompt_short",
    ]
    indices_seen = [s.run_index for s in specs]
    assert indices_seen == [0, 1, 2, 3, 4]


# ---------------------------------------------------------------------------
# Placeholder discriminator
# ---------------------------------------------------------------------------


def test_baseline_floor_discriminator_returns_inconclusive_on_empty_records() -> None:
    """Empty record set yields a verdict beginning with ``inconclusive:``."""

    disc = BaselineFloorDiscriminator(runs_required=20)

    verdict = disc.evaluate(())

    assert isinstance(verdict, RepeatabilityVerdict)
    assert verdict.host_stable_under_repeated_load is False
    assert verdict.runs_observed == 0
    assert verdict.runs_required == 20
    assert verdict.verdict_text.startswith("inconclusive:")
    assert "scaffold" in verdict.verdict_text


# ---------------------------------------------------------------------------
# Harness scaffold runner
# ---------------------------------------------------------------------------


def test_repeatability_harness_run_returns_inconclusive_verdict_text() -> None:
    """Scaffold ``run`` returns an ``inconclusive:`` verdict (no real data)."""

    gen = DeterministicLoadShape(specimen_path="/tmp/specimen-a")
    disc = BaselineFloorDiscriminator(runs_required=4)
    harness = RepeatabilityHarness(generator=gen, discriminator=disc)

    verdict = harness.run(
        total_runs=4,
        classes=("single_prompt_short", "single_prompt_long"),
    )

    assert verdict.host_stable_under_repeated_load is False
    assert verdict.verdict_text.startswith("inconclusive:")


def test_repeatability_harness_appends_one_placeholder_record_per_spec() -> None:
    """One record per yielded spec; ``failure_count == 0`` for each."""

    gen = DeterministicLoadShape(specimen_path="/tmp/specimen-a")
    disc = BaselineFloorDiscriminator(runs_required=4)
    harness = RepeatabilityHarness(generator=gen, discriminator=disc)

    harness.run(
        total_runs=4,
        classes=("single_prompt_short", "single_prompt_long"),
    )

    records = harness.records
    assert len(records) == 4

    # Every record must carry the scaffold provenance, never claim
    # measurement results, and report failure_count == 0.
    for record in records:
        assert record.failure_count == 0
        assert record.evidence_pointer == "scaffold:not_executed"
        assert record.throughput_tokens_per_second is None
        assert record.first_token_latency_ms is None
        assert record.peak_resident_set_bytes is None
        assert record.wall_clock_ms is None
        assert record.completed_request_count is None
        assert record.host_pressure_snapshot is None
        assert record.host_forensics_crash_count_delta is None
        assert record.backend_identity == "scaffold:not_bound"

    # Class assignment in records mirrors the deterministic generator.
    assert [r.prompt_class for r in records] == [
        "single_prompt_short",
        "single_prompt_long",
        "single_prompt_short",
        "single_prompt_long",
    ]


def test_repeatability_harness_run_does_not_import_mlx_lm() -> None:
    """Scaffold execution must not pull ``mlx_lm`` into ``sys.modules``.

    This is the boundary that holds in this round. A real backend round
    will replace this assertion with a positive backend-binding check.

    Implementation note: we compare ``sys.modules`` snapshots before and
    after ``run()`` rather than asserting absolute absence. Earlier tests
    in the same pytest session may have legitimately imported ``mlx_lm``
    (e.g. real-upstream-binding tests); the assertion that holds is that
    *this scaffold's* run does not introduce new mlx_lm-related imports.
    """

    before = set(sys.modules.keys())

    gen = DeterministicLoadShape(specimen_path="/tmp/specimen-a")
    disc = BaselineFloorDiscriminator(runs_required=4)
    harness = RepeatabilityHarness(generator=gen, discriminator=disc)

    harness.run(
        total_runs=4,
        classes=("single_prompt_short", "single_prompt_long"),
    )

    after = set(sys.modules.keys())
    newly_imported = after - before

    mlx_lm_newly_imported = {
        name for name in newly_imported
        if name == "mlx_lm" or name.startswith("mlx_lm.")
    }
    assert mlx_lm_newly_imported == set(), (
        f"scaffold harness run() unexpectedly imported mlx_lm-related "
        f"modules: {sorted(mlx_lm_newly_imported)}"
    )

    native_backend_newly_imported = {
        name for name in newly_imported
        if name == "owlmlx.runtime.mlx_native_backend"
        or name.startswith("owlmlx.runtime.mlx_native_backend.")
    }
    assert native_backend_newly_imported == set(), (
        f"scaffold harness run() unexpectedly imported native backend "
        f"modules: {sorted(native_backend_newly_imported)}"
    )


def test_verdict_text_must_start_with_measured_inconclusive_or_rejected() -> None:
    """``verdict_text`` must follow the comparative-evidence vocabulary.

    Every verdict produced by every scaffold runner must begin with one
    of ``measured:``, ``inconclusive:``, ``rejected:``. No other prefix
    is allowed by the comparative-evidence-harness-contract.md §5.1.
    """

    allowed_prefixes = ("measured:", "inconclusive:", "rejected:")

    # Empty discriminator path
    empty_verdict = BaselineFloorDiscriminator(runs_required=2).evaluate(())
    assert any(empty_verdict.verdict_text.startswith(p) for p in allowed_prefixes)

    # Placeholder records path
    populated_verdict = BaselineFloorDiscriminator(runs_required=2).evaluate(
        (_make_record(prompt_class="single_prompt_short"),)
    )
    assert any(
        populated_verdict.verdict_text.startswith(p)
        for p in allowed_prefixes
    )

    # Full scaffold harness path
    gen = DeterministicLoadShape(specimen_path="/tmp/specimen-a")
    disc = BaselineFloorDiscriminator(runs_required=4)
    harness = RepeatabilityHarness(generator=gen, discriminator=disc)
    full_verdict = harness.run(
        total_runs=4,
        classes=("single_prompt_short", "single_prompt_long"),
    )
    assert any(full_verdict.verdict_text.startswith(p) for p in allowed_prefixes)
