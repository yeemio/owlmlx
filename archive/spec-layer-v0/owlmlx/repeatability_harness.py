"""owlmlx repeatability harness scaffold.

Defines the contract types for a multi-prompt randomized-load
repeatability harness that, when implemented end-to-end, would let the
seven-line architectural assessment Line 6 (host-stable execution
confidence) move from ``behind`` to ``partial``. This scaffold module
defines only the contract types and a placeholder runner that produces
``inconclusive`` verdicts; it does NOT actually load any model, run
``mlx_lm.stream_generate``, or sample host pressure during execution.

Distinct from ``heavy_weight_repeatability_status.py`` (rung-state
machine over declared inputs) and from ``comparative_evidence_runner.py``
(single-shot comparative harness). Real measurement-loop implementation
is a follow-up round and is governed by the comparative-evidence-harness
banned-vocabulary contract: verdict text must begin with ``measured:``,
``inconclusive:``, or ``rejected:``.
"""

from __future__ import annotations

import abc
import time
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Frozen record shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RepeatabilityRunRecord:
    """One per-run record of a repeatability harness run.

    The 6 standard measurement fields exactly mirror the
    ``comparative-evidence-harness-contract.md`` §3.3 measurement surface so
    that a real implementation can emit a contract-shaped record without
    re-keying. Additional fields (``host_pressure_snapshot``,
    ``host_forensics_crash_count_delta``, ``backend_identity``,
    ``run_id``, ``recorded_at``, ``prompt_class``, ``specimen_path``,
    ``evidence_pointer``) are additive provenance fields specific to the
    repeatability surface.

    All measurement fields are ``None`` in the scaffold runner; a real
    runner would populate them from an actual ``MlxNativeBackend`` /
    ``MlxLmSubprocessBackend`` pass.
    """

    # Six standard measurement fields (None in scaffold; real values later)
    throughput_tokens_per_second: float | None
    first_token_latency_ms: float | None
    peak_resident_set_bytes: int | None
    wall_clock_ms: float | None
    completed_request_count: int | None
    failure_count: int

    # Additive provenance / context
    host_pressure_snapshot: dict[str, Any] | None
    host_forensics_crash_count_delta: int | None
    backend_identity: str
    run_id: str
    recorded_at: float
    prompt_class: str
    specimen_path: str
    evidence_pointer: str | None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-ready dict.

        Key set is: the 6 standard measurement fields (per the
        comparative-evidence-harness-contract.md §3.3 vocabulary) plus
        the additive provenance fields. No banned-vocabulary verdict
        terms appear in this surface.
        """

        return {
            "throughput_tokens_per_second": self.throughput_tokens_per_second,
            "first_token_latency_ms": self.first_token_latency_ms,
            "peak_resident_set_bytes": self.peak_resident_set_bytes,
            "wall_clock_ms": self.wall_clock_ms,
            "completed_request_count": self.completed_request_count,
            "failure_count": int(self.failure_count),
            "host_pressure_snapshot": (
                dict(self.host_pressure_snapshot)
                if self.host_pressure_snapshot is not None
                else None
            ),
            "host_forensics_crash_count_delta": self.host_forensics_crash_count_delta,
            "backend_identity": self.backend_identity,
            "run_id": self.run_id,
            "recorded_at": float(self.recorded_at),
            "prompt_class": self.prompt_class,
            "specimen_path": self.specimen_path,
            "evidence_pointer": self.evidence_pointer,
        }


@dataclass(frozen=True, slots=True)
class RepeatabilityRunSpec:
    """Declarative specification of one run before it is executed.

    A ``LoadShapeGenerator`` emits these; the harness consumes them. The
    ``prompt_class`` vocabulary intentionally mirrors the
    comparative-evidence-harness-contract.md workload-class vocabulary
    (``single_prompt_short``, ``single_prompt_long``, ``multi_prompt_serial``,
    ``multi_prompt_aggregated``).
    """

    run_index: int
    prompt_class: str
    specimen_path: str
    max_tokens: int
    arrival_jitter_s: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_index": int(self.run_index),
            "prompt_class": self.prompt_class,
            "specimen_path": self.specimen_path,
            "max_tokens": int(self.max_tokens),
            "arrival_jitter_s": float(self.arrival_jitter_s),
        }


@dataclass(frozen=True, slots=True)
class RepeatabilityVerdict:
    """Aggregated verdict over a set of ``RepeatabilityRunRecord``s.

    ``host_stable_under_repeated_load`` is the new boolean that, in a
    fully implemented harness, would surface inside the existing 5-rung
    ``HeavyWeightRuntimeRepeatabilityStatus`` output as an additive
    field; it is **not** a new rung. ``verdict_text`` must always begin
    with ``measured:``, ``inconclusive:``, or ``rejected:`` per the
    comparative-evidence-harness-contract.md §5.1 banned vocabulary.
    """

    host_stable_under_repeated_load: bool
    rejection_reasons: tuple[str, ...]
    verdict_text: str
    runs_observed: int
    runs_required: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "host_stable_under_repeated_load": bool(
                self.host_stable_under_repeated_load
            ),
            "rejection_reasons": list(self.rejection_reasons),
            "verdict_text": self.verdict_text,
            "runs_observed": int(self.runs_observed),
            "runs_required": int(self.runs_required),
        }


# ---------------------------------------------------------------------------
# Abstract collaborators + scaffold concrete subclasses
# ---------------------------------------------------------------------------


class LoadShapeGenerator(abc.ABC):
    """Produces the (run_index, prompt_class, specimen_path) sequence.

    Subclasses must implement ``iter_specs`` to return an iterable of
    ``RepeatabilityRunSpec``. The scaffold ``DeterministicLoadShape``
    cycles classes in declared order so tests can assert the sequence
    without RNG noise. A future randomized subclass would honor an
    arrival-jitter distribution; that is not built here.
    """

    @abc.abstractmethod
    def iter_specs(
        self,
        *,
        total_runs: int,
        classes: tuple[str, ...],
    ) -> Iterable[RepeatabilityRunSpec]:
        """Yield one spec per planned run."""


@dataclass(frozen=True, slots=True)
class DeterministicLoadShape(LoadShapeGenerator):
    """Scaffold concrete generator: cycles classes deterministically.

    Not randomized. Intended for shape testing and for the placeholder
    ``RepeatabilityHarness.run`` path; a real randomized subclass is a
    follow-up extension point.
    """

    specimen_path: str
    max_tokens: int = 16
    arrival_jitter_s: float = 0.0

    def iter_specs(
        self,
        *,
        total_runs: int,
        classes: tuple[str, ...],
    ) -> Iterable[RepeatabilityRunSpec]:
        if total_runs <= 0:
            return iter(())
        if not classes:
            raise ValueError("classes tuple must be non-empty")
        specs: list[RepeatabilityRunSpec] = []
        for i in range(int(total_runs)):
            cls = classes[i % len(classes)]
            specs.append(
                RepeatabilityRunSpec(
                    run_index=i,
                    prompt_class=cls,
                    specimen_path=self.specimen_path,
                    max_tokens=int(self.max_tokens),
                    arrival_jitter_s=float(self.arrival_jitter_s),
                )
            )
        return iter(specs)


class DegradationDiscriminator(abc.ABC):
    """Evaluates a sequence of records into a frozen verdict.

    A real implementation would assert all five host-stability conditions
    listed in the architecture doc (§7) — ``failure_count == 0`` for
    every run, throughput non-degradation, ``peak_resident_set_bytes``
    non-monotonic-growth, no new crash reports, host_pressure remains
    out of ``host_pressure_block``. The scaffold subclass below returns
    an honest ``inconclusive`` because no real records exist.
    """

    @abc.abstractmethod
    def evaluate(
        self, records: Sequence[RepeatabilityRunRecord]
    ) -> RepeatabilityVerdict:
        """Aggregate records into a verdict."""


@dataclass(frozen=True, slots=True)
class BaselineFloorDiscriminator(DegradationDiscriminator):
    """Scaffold discriminator: returns ``inconclusive`` unconditionally.

    The placeholder verdict text begins with ``inconclusive:`` so that
    even the scaffold complies with the comparative-evidence-harness-
    contract.md §5.1 verdict-vocabulary rule.
    """

    runs_required: int = 20

    def evaluate(
        self, records: Sequence[RepeatabilityRunRecord]
    ) -> RepeatabilityVerdict:
        observed = len(records)
        if observed == 0:
            return RepeatabilityVerdict(
                host_stable_under_repeated_load=False,
                rejection_reasons=("scaffold_no_records",),
                verdict_text=(
                    "inconclusive: scaffold; no real records to evaluate"
                ),
                runs_observed=0,
                runs_required=int(self.runs_required),
            )
        # Even with placeholder records we refuse to claim host-stable; the
        # measurement fields are None and no real backend ran.
        return RepeatabilityVerdict(
            host_stable_under_repeated_load=False,
            rejection_reasons=("scaffold_placeholder_records",),
            verdict_text=(
                "inconclusive: scaffold placeholder records; "
                "real backend not invoked"
            ),
            runs_observed=int(observed),
            runs_required=int(self.runs_required),
        )


# ---------------------------------------------------------------------------
# Scaffold harness
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _HarnessRunOutcome:
    """Internal carrier for ``RepeatabilityHarness.run`` returning both the
    placeholder records and the discriminator verdict. Not part of the
    public surface — the public ``run`` method returns only the verdict.
    """

    records: tuple[RepeatabilityRunRecord, ...]
    verdict: RepeatabilityVerdict


class RepeatabilityHarness:
    """Scaffold runner.

    This class is intentionally **not** wired to any real backend. Its
    only job in the C-2 scaffold round is to prove the contract types
    compose end to end:

    - the generator yields specs
    - the harness produces one ``RepeatabilityRunRecord`` per spec
      (placeholder, ``failure_count = 0``, all measurement fields
      ``None``, ``evidence_pointer = "scaffold:not_executed"``)
    - the discriminator returns an ``inconclusive`` verdict

    A real implementation (future C-2.1 round) would replace
    ``_record_placeholder`` with a code path that:

    - acquires an admitted candidate via
      ``native-mlx-backend-local-candidate-admissibility.md`` rules
    - constructs a ``MlxNativeBackend`` (or comparable) and runs
      ``load -> stream_generate -> unload``
    - samples ``owlmlx.host_pressure.sample_host_pressure(...)`` before
      and after each run, plus a host-forensics crash-count delta
    - records 6 real measurement fields plus the additive provenance

    This module does NOT import ``MlxNativeBackend`` or ``mlx_lm`` and
    does NOT touch process state of any kind.
    """

    def __init__(
        self,
        *,
        generator: LoadShapeGenerator,
        discriminator: DegradationDiscriminator,
        backend_identity: str = "scaffold:not_bound",
    ) -> None:
        self._generator = generator
        self._discriminator = discriminator
        self._backend_identity = str(backend_identity)
        self._records: list[RepeatabilityRunRecord] = []

    @property
    def records(self) -> tuple[RepeatabilityRunRecord, ...]:
        """Snapshot of placeholder records appended during the last ``run``."""

        return tuple(self._records)

    def _record_placeholder(
        self, spec: RepeatabilityRunSpec
    ) -> RepeatabilityRunRecord:
        """Build a placeholder ``RepeatabilityRunRecord`` for one spec.

        Internal helper; intentionally side-effect-free apart from
        constructing a record with ``failure_count = 0`` and
        ``evidence_pointer = "scaffold:not_executed"``. All real
        measurement fields are ``None`` so consumers cannot mistake
        them for evidence.
        """

        return RepeatabilityRunRecord(
            throughput_tokens_per_second=None,
            first_token_latency_ms=None,
            peak_resident_set_bytes=None,
            wall_clock_ms=None,
            completed_request_count=None,
            failure_count=0,
            host_pressure_snapshot=None,
            host_forensics_crash_count_delta=None,
            backend_identity=self._backend_identity,
            run_id=str(uuid.uuid4()),
            recorded_at=time.time(),
            prompt_class=spec.prompt_class,
            specimen_path=spec.specimen_path,
            evidence_pointer="scaffold:not_executed",
        )

    def run(
        self,
        *,
        total_runs: int,
        classes: tuple[str, ...],
    ) -> RepeatabilityVerdict:
        """Iterate specs, append placeholder records, return verdict.

        Scaffold-grade: this method does not load any model, does not
        import ``mlx_lm``, does not call any backend ``stream_generate``,
        does not sample ``host_pressure``, and does not read crash
        reports. It simply walks ``self._generator.iter_specs(...)``
        and accumulates one placeholder record per yielded spec, then
        delegates to ``self._discriminator.evaluate(...)``.

        Returns the discriminator's verdict, which (because there are
        no real measurements) will be ``inconclusive``.
        """

        self._records = []
        for spec in self._generator.iter_specs(
            total_runs=int(total_runs),
            classes=tuple(classes),
        ):
            self._records.append(self._record_placeholder(spec))
        return self._discriminator.evaluate(tuple(self._records))


# ---------------------------------------------------------------------------
# Future extension points (NOT implemented in this scaffold round)
# ---------------------------------------------------------------------------
#
# 1. Real backend integration:
#    - import owlmlx.runtime.mlx_native_backend.MlxNativeBackend lazily
#      inside a future ``RealBackendHarness`` subclass; do **not** import
#      it at module top-level — this scaffold is required to remain
#      free of any mlx_lm / native-backend import side effects.
#
# 2. Real measurement collection:
#    - record ``throughput_tokens_per_second``,
#      ``first_token_latency_ms``, ``peak_resident_set_bytes``,
#      ``wall_clock_ms``, ``completed_request_count``, ``failure_count``
#      from the actual stream_generate event flow; key shape must match
#      ``ComparativeEvidenceMeasurement``.
#
# 3. Real host-pressure integration:
#    - call ``owlmlx.host_pressure.sample_host_pressure(...)`` before
#      and after each spec; serialize the resulting snapshot dict into
#      ``host_pressure_snapshot``; reject any run where the snapshot
#      enters ``host_pressure_block`` mid-run.
#
# 4. Real host-forensics delta:
#    - compute crash-count delta around the run window via the existing
#      crash-report directory; populate
#      ``host_forensics_crash_count_delta``.
#
# 5. Statistical degradation thresholds:
#    - implement ``DegradationDiscriminator.evaluate`` to assert all
#      five host-stability conditions from the architecture doc §7.
#    - thresholds must be published in the architecture doc before code
#      is written, per existing source-of-truth discipline.
#
# 6. Wire-up to ``HeavyWeightRuntimeRepeatabilityStatus``:
#    - extend that dataclass with an additive
#      ``host_stable_under_repeated_load`` boolean; do not introduce a
#      new rung. The 5-rung enum stays frozen.

__all__ = [
    "BaselineFloorDiscriminator",
    "DegradationDiscriminator",
    "DeterministicLoadShape",
    "LoadShapeGenerator",
    "RepeatabilityHarness",
    "RepeatabilityRunRecord",
    "RepeatabilityRunSpec",
    "RepeatabilityVerdict",
]
