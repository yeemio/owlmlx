from __future__ import annotations

from owlmlx.host_pressure import (
    classify_host_pressure,
    host_pressure_not_sampled_snapshot,
    host_pressure_snapshot_to_dict,
    parse_memory_pressure_output,
)


def test_parse_memory_pressure_output_classifies_normal_sample() -> None:
    output = """
The system has 137438953472 (8388608 pages with a page size of 16384).

Stats:
Pages free: 6907555
Pages wired down: 293158

Compressor Stats:
Pages used by compressor: 63515

System-wide memory free percentage: 95%
"""

    snapshot = parse_memory_pressure_output(output, sampled_at_s=123.456)

    assert snapshot.available is True
    assert snapshot.source == "memory_pressure"
    assert snapshot.classification == "normal"
    assert snapshot.reason_code == "free_percent_above_warning_threshold"
    assert snapshot.free_percent == 95.0
    assert snapshot.total_gb == 128.0
    assert snapshot.free_gb is not None
    assert snapshot.wired_gb is not None
    assert snapshot.compressor_gb is not None
    assert snapshot.sampled_at_s == 123.456


def test_parse_memory_pressure_output_classifies_block_threshold() -> None:
    output = """
The system has 137438953472 (8388608 pages with a page size of 16384).
Pages free: 680000
Pages wired down: 3900000
Pages used by compressor: 140000
System-wide memory free percentage: 8%
"""

    snapshot = parse_memory_pressure_output(output)

    assert snapshot.classification == "host_pressure_block"
    assert snapshot.reason_code == "free_percent_at_or_below_block_threshold"
    assert snapshot.free_percent == 8.0


def test_classify_host_pressure_warns_before_blocking() -> None:
    classification, reason_code, _ = classify_host_pressure(free_percent=17.0)

    assert classification == "host_pressure_warn"
    assert reason_code == "free_percent_at_or_below_warning_threshold"


def test_parse_memory_pressure_output_marks_missing_free_percent_unknown() -> None:
    snapshot = parse_memory_pressure_output("Stats:\nPages free: 12\n")

    assert snapshot.available is False
    assert snapshot.classification == "unknown"
    assert snapshot.reason_code == "free_percent_missing"


def test_not_sampled_snapshot_is_explicitly_unknown() -> None:
    payload = host_pressure_snapshot_to_dict(host_pressure_not_sampled_snapshot())

    assert payload["available"] is False
    assert payload["source"] == "not_sampled"
    assert payload["classification"] == "unknown"
    assert payload["reason_code"] == "not_sampled"
