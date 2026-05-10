from __future__ import annotations

import math

import pytest

from owlmlx.repeatability_statistics import (
    RepeatRunSample,
    compute_repeatability_statistics,
    repeatability_statistics_to_dict,
)


def _sample(ttft: float | None, tps: float | None, rss: int | None = None) -> RepeatRunSample:
    return RepeatRunSample(ttft_ms=ttft, decode_tps=tps, wall_ms=None, rss_bytes=rss)


# --- insufficient samples ---

def test_zero_samples_yields_insufficient():
    stats = compute_repeatability_statistics([])
    assert stats.n == 0
    assert stats.stability_label == "insufficient_samples"
    assert stats.ttft_ms_mean is None
    assert stats.decode_tps_mean is None


def test_four_samples_yields_insufficient():
    samples = [_sample(100.0, 5.0) for _ in range(4)]
    stats = compute_repeatability_statistics(samples)
    assert stats.stability_label == "insufficient_samples"


# --- stable: low CV ---

def test_five_identical_samples_yield_stable():
    samples = [_sample(100.0, 5.0) for _ in range(5)]
    stats = compute_repeatability_statistics(samples)
    assert stats.stability_label == "stable"
    assert stats.ttft_ms_stddev == pytest.approx(0.0, abs=1e-9)
    assert stats.decode_tps_stddev == pytest.approx(0.0, abs=1e-9)
    assert stats.ttft_ms_mean == pytest.approx(100.0)
    assert stats.decode_tps_mean == pytest.approx(5.0)


def test_stable_label_when_cv_below_10_percent():
    # CV = 0.05/1.0 = 5% for both
    samples = [_sample(1000.0 + 5 * i, 10.0 + 0.05 * i) for i in range(10)]
    stats = compute_repeatability_statistics(samples)
    assert stats.stability_label == "stable"


# --- unstable: high CV ---

def test_unstable_when_ttft_cv_exceeds_30_percent():
    # ttft varies wildly: 100, 500, 200, 800, 150 → large CV
    samples = [_sample(t, 5.0) for t in [100.0, 500.0, 200.0, 800.0, 150.0]]
    stats = compute_repeatability_statistics(samples)
    assert stats.stability_label == "unstable"


def test_unstable_when_tps_cv_exceeds_20_percent():
    # tps: 1.0, 4.0, 1.5, 5.0, 1.2 → CV well above 0.20
    samples = [_sample(100.0, t) for t in [1.0, 4.0, 1.5, 5.0, 1.2]]
    stats = compute_repeatability_statistics(samples)
    assert stats.stability_label == "unstable"


# --- min / max / stddev correctness ---

def test_ttft_min_max_computed_correctly():
    samples = [_sample(t, 5.0) for t in [100.0, 200.0, 150.0, 120.0, 180.0]]
    stats = compute_repeatability_statistics(samples)
    assert stats.ttft_ms_min == pytest.approx(100.0)
    assert stats.ttft_ms_max == pytest.approx(200.0)


def test_rss_max_computed_from_samples():
    samples = [_sample(100.0, 5.0, rss=i * 1024**3) for i in [4, 6, 5, 5, 6]]
    stats = compute_repeatability_statistics(samples)
    assert stats.rss_bytes_max == 6 * 1024**3


def test_stddev_matches_manual_calculation():
    values = [100.0, 110.0, 90.0, 105.0, 95.0]
    samples = [_sample(v, 5.0) for v in values]
    stats = compute_repeatability_statistics(samples)
    mean = sum(values) / len(values)
    expected = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
    assert stats.ttft_ms_stddev == pytest.approx(expected, rel=1e-6)


# --- none-handling ---

def test_samples_with_none_ttft_excluded_from_stats():
    samples = [_sample(None, 5.0), _sample(100.0, 5.0), _sample(200.0, 5.0),
               _sample(None, 5.0), _sample(150.0, 5.0)]
    stats = compute_repeatability_statistics(samples)
    assert stats.n == 5
    assert stats.ttft_ms_mean == pytest.approx((100.0 + 200.0 + 150.0) / 3)
    assert stats.ttft_ms_min == pytest.approx(100.0)


# --- serialization ---

def test_to_dict_structure():
    samples = [_sample(100.0, 5.0, rss=4 * 1024**3) for _ in range(5)]
    d = repeatability_statistics_to_dict(compute_repeatability_statistics(samples))
    assert d["contract"]["surface"] == "owlmlx.repeatability_statistics"
    assert d["contract"]["version"] == "v1"
    assert d["n"] == 5
    assert "mean" in d["ttft_ms"]
    assert "stddev" in d["ttft_ms"]
    assert "min" in d["ttft_ms"]
    assert "max" in d["ttft_ms"]
    assert d["rss_bytes_max"] == 4 * 1024**3
    assert d["stability_label"] == "stable"
