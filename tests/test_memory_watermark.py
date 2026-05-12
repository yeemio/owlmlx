"""Tests for owlmlx.memory_watermark — the PR #649 public landmark types."""

from __future__ import annotations

import pytest

from owlmlx.memory_watermark import (
    GREEN_CEILING,
    MemoryWatermark,
    RED_CEILING,
    WATERMARK_THRESHOLDS,
    WatermarkAction,
    YELLOW_CEILING,
)


class TestThresholds:
    def test_threshold_values_match_pr_649(self) -> None:
        assert GREEN_CEILING == 0.65
        assert YELLOW_CEILING == 0.80
        assert RED_CEILING == 0.90

    def test_thresholds_strictly_increasing(self) -> None:
        assert GREEN_CEILING < YELLOW_CEILING < RED_CEILING


class TestFromUtilization:
    @pytest.mark.parametrize(
        "u, expected",
        [
            (0.0, MemoryWatermark.GREEN),
            (0.30, MemoryWatermark.GREEN),
            (0.649, MemoryWatermark.GREEN),
            (0.65, MemoryWatermark.YELLOW),
            (0.799, MemoryWatermark.YELLOW),
            (0.80, MemoryWatermark.RED),
            (0.899, MemoryWatermark.RED),
            (0.90, MemoryWatermark.FATAL),
            (1.0, MemoryWatermark.FATAL),
            (1.2, MemoryWatermark.FATAL),
        ],
    )
    def test_boundary_mapping(self, u: float, expected: MemoryWatermark) -> None:
        assert MemoryWatermark.from_utilization(u) is expected

    def test_none_returns_unknown(self) -> None:
        assert MemoryWatermark.from_utilization(None) is MemoryWatermark.UNKNOWN

    def test_nan_returns_unknown(self) -> None:
        assert MemoryWatermark.from_utilization(float("nan")) is MemoryWatermark.UNKNOWN

    def test_non_numeric_returns_unknown(self) -> None:
        assert MemoryWatermark.from_utilization("not a number") is MemoryWatermark.UNKNOWN  # type: ignore[arg-type]


class TestFromClassification:
    @pytest.mark.parametrize(
        "classification, expected",
        [
            ("within_budget", MemoryWatermark.GREEN),
            ("near_budget", MemoryWatermark.YELLOW),
            ("over_budget", MemoryWatermark.RED),
            ("cooldown_barrier", MemoryWatermark.FATAL),
            ("host_pressure_barrier", MemoryWatermark.FATAL),
            ("unknown", MemoryWatermark.UNKNOWN),
            ("insufficient_signal", MemoryWatermark.UNKNOWN),
        ],
    )
    def test_owlmlx_classification_maps_to_watermark(
        self, classification: str, expected: MemoryWatermark
    ) -> None:
        assert MemoryWatermark.from_classification(classification) is expected

    def test_unknown_classification_falls_back_to_unknown(self) -> None:
        assert (
            MemoryWatermark.from_classification("totally_made_up_label")
            is MemoryWatermark.UNKNOWN
        )

    def test_none_returns_unknown(self) -> None:
        assert MemoryWatermark.from_classification(None) is MemoryWatermark.UNKNOWN


class TestWatermarkAction:
    @pytest.mark.parametrize(
        "watermark, expected",
        [
            (MemoryWatermark.GREEN, WatermarkAction.PROCEED),
            (MemoryWatermark.YELLOW, WatermarkAction.EVICT_LRU),
            (MemoryWatermark.RED, WatermarkAction.AGGRESSIVE_EVICT),
            (MemoryWatermark.FATAL, WatermarkAction.REFUSE_LOAD),
            (MemoryWatermark.UNKNOWN, WatermarkAction.DEFER),
        ],
    )
    def test_action_for_each_watermark(
        self, watermark: MemoryWatermark, expected: WatermarkAction
    ) -> None:
        assert WatermarkAction.for_watermark(watermark) is expected

    def test_every_watermark_has_an_action(self) -> None:
        # Total mapping — no watermark left unhandled.
        for w in MemoryWatermark:
            assert WatermarkAction.for_watermark(w) in WatermarkAction


class TestThresholdsTable:
    def test_thresholds_table_covers_all_watermarks(self) -> None:
        for w in MemoryWatermark:
            assert w in WATERMARK_THRESHOLDS

    def test_terminal_levels_have_none_ceiling(self) -> None:
        assert WATERMARK_THRESHOLDS[MemoryWatermark.FATAL] is None
        assert WATERMARK_THRESHOLDS[MemoryWatermark.UNKNOWN] is None
