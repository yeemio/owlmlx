"""Runtime-owned repeatability statistics for N-repeat Model RC runs.

Computes variance across repeated runs to distinguish one-shot lucky data
from genuine host-stable repeatability.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class RepeatRunSample:
    """Raw measurements from one Model RC repeat."""

    ttft_ms: float | None
    decode_tps: float | None
    wall_ms: float | None
    rss_bytes: int | None


@dataclass(frozen=True, slots=True)
class RepeatabilityStatistics:
    """Variance statistics derived from N repeated Model RC runs."""

    n: int
    ttft_ms_mean: float | None
    ttft_ms_stddev: float | None
    ttft_ms_min: float | None
    ttft_ms_max: float | None
    decode_tps_mean: float | None
    decode_tps_stddev: float | None
    decode_tps_min: float | None
    decode_tps_max: float | None
    rss_bytes_max: int | None
    stability_label: str
    stability_note: str


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _stddev(values: list[float]) -> float | None:
    """Sample standard deviation (n-1 denominator)."""
    if len(values) < 2:
        return None
    m = sum(values) / len(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


_INSUFFICIENT_SAMPLES_THRESHOLD = 5
_TTFT_UNSTABLE_CV = 0.30
_TPS_UNSTABLE_CV = 0.20
_STABLE_CV = 0.10


def _stability_label_and_note(
    n: int,
    ttft_stddev: float | None,
    ttft_mean: float | None,
    tps_stddev: float | None,
    tps_mean: float | None,
) -> tuple[str, str]:
    if n < _INSUFFICIENT_SAMPLES_THRESHOLD:
        return "insufficient_samples", f"n={n} below minimum of {_INSUFFICIENT_SAMPLES_THRESHOLD}"

    def _cv(stddev: float | None, mean: float | None) -> float | None:
        if stddev is not None and mean and mean > 0:
            return stddev / mean
        return None

    ttft_cv = _cv(ttft_stddev, ttft_mean)
    tps_cv = _cv(tps_stddev, tps_mean)

    def _fmt(v: float | None) -> str:
        return f"{v:.3f}" if v is not None else "n/a"

    note = f"n={n} ttft_cv={_fmt(ttft_cv)} tps_cv={_fmt(tps_cv)}"

    if (ttft_cv is not None and ttft_cv > _TTFT_UNSTABLE_CV) or (
        tps_cv is not None and tps_cv > _TPS_UNSTABLE_CV
    ):
        return "unstable", note

    if (ttft_cv is None or ttft_cv <= _STABLE_CV) and (
        tps_cv is None or tps_cv <= _STABLE_CV
    ):
        return "stable", note

    return "acceptable", note


def compute_repeatability_statistics(
    samples: Sequence[RepeatRunSample],
) -> RepeatabilityStatistics:
    """Compute variance statistics across N repeat-run samples.

    Fewer than 5 samples yields ``stability_label="insufficient_samples"``.
    """
    n = len(samples)
    ttft_values = [s.ttft_ms for s in samples if s.ttft_ms is not None]
    tps_values = [s.decode_tps for s in samples if s.decode_tps is not None]
    rss_values = [s.rss_bytes for s in samples if s.rss_bytes is not None]

    ttft_mean = _mean(ttft_values)
    ttft_stddev = _stddev(ttft_values)
    tps_mean = _mean(tps_values)
    tps_stddev = _stddev(tps_values)

    label, note = _stability_label_and_note(n, ttft_stddev, ttft_mean, tps_stddev, tps_mean)

    return RepeatabilityStatistics(
        n=n,
        ttft_ms_mean=ttft_mean,
        ttft_ms_stddev=ttft_stddev,
        ttft_ms_min=min(ttft_values) if ttft_values else None,
        ttft_ms_max=max(ttft_values) if ttft_values else None,
        decode_tps_mean=tps_mean,
        decode_tps_stddev=tps_stddev,
        decode_tps_min=min(tps_values) if tps_values else None,
        decode_tps_max=max(tps_values) if tps_values else None,
        rss_bytes_max=max(rss_values) if rss_values else None,
        stability_label=label,
        stability_note=note,
    )


def repeatability_statistics_to_dict(stats: RepeatabilityStatistics) -> dict[str, Any]:
    return {
        "contract": {
            "surface": "owlmlx.repeatability_statistics",
            "version": "v1",
        },
        "n": stats.n,
        "ttft_ms": {
            "mean": stats.ttft_ms_mean,
            "stddev": stats.ttft_ms_stddev,
            "min": stats.ttft_ms_min,
            "max": stats.ttft_ms_max,
        },
        "decode_tps": {
            "mean": stats.decode_tps_mean,
            "stddev": stats.decode_tps_stddev,
            "min": stats.decode_tps_min,
            "max": stats.decode_tps_max,
        },
        "rss_bytes_max": stats.rss_bytes_max,
        "stability_label": stats.stability_label,
        "stability_note": stats.stability_note,
    }


__all__ = [
    "RepeatRunSample",
    "RepeatabilityStatistics",
    "compute_repeatability_statistics",
    "repeatability_statistics_to_dict",
]
