"""Runtime-owned ``comparative_evidence_record`` v1 builder and serializer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .comparative_evidence_schema import (
    COMPARATIVE_EVIDENCE_RECORD_SURFACE,
    COMPARATIVE_EVIDENCE_RECORD_VERSION,
    validate_comparative_evidence_record,
)


@dataclass(frozen=True, slots=True)
class ComparativeEvidenceMeasurement:
    """Per-runtime measurement block for one comparative-evidence record."""

    throughput_tokens_per_second: float
    first_token_latency_ms: float
    peak_resident_set_bytes: int
    wall_clock_ms: float
    completed_request_count: int
    failure_count: int
    failure_causes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ComparativeEvidenceRuntime:
    """One runtime entry inside the ordered ``runtimes`` list."""

    runtime_id: str
    runtime_version: str
    measurement: ComparativeEvidenceMeasurement


@dataclass(frozen=True, slots=True)
class ComparativeEvidenceRecord:
    """Frozen ``comparative_evidence_record`` v1 record."""

    surface: str
    version: str
    recorded_at: str
    evidence_pointer: str
    host_class: str
    workload_class: str
    workload_invariants: dict[str, Any]
    runtimes: tuple[ComparativeEvidenceRuntime, ...]
    verdict_text: str
    verdict_grade: str


def _measurement_to_dict(measurement: ComparativeEvidenceMeasurement) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "throughput_tokens_per_second": float(measurement.throughput_tokens_per_second),
        "first_token_latency_ms": float(measurement.first_token_latency_ms),
        "peak_resident_set_bytes": int(measurement.peak_resident_set_bytes),
        "wall_clock_ms": float(measurement.wall_clock_ms),
        "completed_request_count": int(measurement.completed_request_count),
        "failure_count": int(measurement.failure_count),
    }
    if measurement.failure_count > 0 or measurement.failure_causes:
        payload["failure_causes"] = list(measurement.failure_causes)
    return payload


def _runtime_to_dict(runtime: ComparativeEvidenceRuntime) -> dict[str, Any]:
    return {
        "runtime_id": runtime.runtime_id,
        "runtime_version": runtime.runtime_version,
        "measurement": _measurement_to_dict(runtime.measurement),
    }


def comparative_evidence_record_to_dict(
    record: ComparativeEvidenceRecord,
) -> dict[str, Any]:
    """Serialize the record to a JSON-ready dict."""

    return {
        "surface": record.surface,
        "version": record.version,
        "recorded_at": record.recorded_at,
        "evidence_pointer": record.evidence_pointer,
        "host_class": record.host_class,
        "workload_class": record.workload_class,
        "workload_invariants": dict(record.workload_invariants),
        "runtimes": [_runtime_to_dict(runtime) for runtime in record.runtimes],
        "verdict_text": record.verdict_text,
        "verdict_grade": record.verdict_grade,
    }


def _runtimes_from_input(
    runtimes: Any,
) -> tuple[ComparativeEvidenceRuntime, ...]:
    if isinstance(runtimes, ComparativeEvidenceRuntime):
        return (runtimes,)
    if isinstance(runtimes, (list, tuple)):
        result: list[ComparativeEvidenceRuntime] = []
        for entry in runtimes:
            if isinstance(entry, ComparativeEvidenceRuntime):
                result.append(entry)
                continue
            if isinstance(entry, Mapping):
                measurement_payload = entry.get("measurement") or {}
                measurement = ComparativeEvidenceMeasurement(
                    throughput_tokens_per_second=float(
                        measurement_payload.get("throughput_tokens_per_second", 0.0)
                    ),
                    first_token_latency_ms=float(
                        measurement_payload.get("first_token_latency_ms", 0.0)
                    ),
                    peak_resident_set_bytes=int(
                        measurement_payload.get("peak_resident_set_bytes", 0)
                    ),
                    wall_clock_ms=float(
                        measurement_payload.get("wall_clock_ms", 0.0)
                    ),
                    completed_request_count=int(
                        measurement_payload.get("completed_request_count", 0)
                    ),
                    failure_count=int(measurement_payload.get("failure_count", 0)),
                    failure_causes=tuple(
                        str(cause)
                        for cause in measurement_payload.get("failure_causes", [])
                    ),
                )
                result.append(
                    ComparativeEvidenceRuntime(
                        runtime_id=str(entry.get("runtime_id")),
                        runtime_version=str(entry.get("runtime_version")),
                        measurement=measurement,
                    )
                )
                continue
            raise TypeError(
                f"runtimes entry must be ComparativeEvidenceRuntime or mapping, got {type(entry)!r}"
            )
        return tuple(result)
    raise TypeError(
        "runtimes must be an iterable of ComparativeEvidenceRuntime or mappings"
    )


def build_comparative_evidence_record(
    *,
    recorded_at: str,
    evidence_pointer: str,
    host_class: str,
    workload_class: str,
    workload_invariants: Mapping[str, Any],
    runtimes: Any,
    verdict_text: str,
    verdict_grade: str,
) -> ComparativeEvidenceRecord:
    """Build, validate, and return a ``comparative_evidence_record`` v1 record."""

    runtime_tuple = _runtimes_from_input(runtimes)
    record = ComparativeEvidenceRecord(
        surface=COMPARATIVE_EVIDENCE_RECORD_SURFACE,
        version=COMPARATIVE_EVIDENCE_RECORD_VERSION,
        recorded_at=recorded_at,
        evidence_pointer=evidence_pointer,
        host_class=host_class,
        workload_class=workload_class,
        workload_invariants=dict(workload_invariants),
        runtimes=runtime_tuple,
        verdict_text=verdict_text,
        verdict_grade=verdict_grade,
    )

    validate_comparative_evidence_record(comparative_evidence_record_to_dict(record))
    return record


__all__ = [
    "ComparativeEvidenceMeasurement",
    "ComparativeEvidenceRecord",
    "ComparativeEvidenceRuntime",
    "build_comparative_evidence_record",
    "comparative_evidence_record_to_dict",
]
