"""Runtime-owned host memory-pressure sampling for load admission.

This module intentionally samples only host-visible macOS memory pressure. It
does not claim to expose private Metal allocator state or GPU residency truth.
"""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import asdict, dataclass
from typing import Any


HOST_PRESSURE_BLOCK_FREE_PERCENT = 10.0
HOST_PRESSURE_WARN_FREE_PERCENT = 20.0
_BYTES_PER_GB = 1024.0 ** 3


@dataclass(frozen=True, slots=True)
class HostPressureSnapshot:
    """A conservative host-pressure snapshot for runtime admission."""

    available: bool
    source: str
    classification: str
    reason_code: str
    reason_message: str
    free_percent: float | None = None
    free_gb: float | None = None
    wired_gb: float | None = None
    compressor_gb: float | None = None
    total_gb: float | None = None
    sampled_at_s: float | None = None
    block_free_percent: float = HOST_PRESSURE_BLOCK_FREE_PERCENT
    warn_free_percent: float = HOST_PRESSURE_WARN_FREE_PERCENT
    raw_excerpt: str = ""


def host_pressure_not_sampled_snapshot() -> HostPressureSnapshot:
    """Return the status payload used before the first load-time sample."""

    return HostPressureSnapshot(
        available=False,
        source="not_sampled",
        classification="unknown",
        reason_code="not_sampled",
        reason_message="Host pressure is sampled at load admission, not on status reads.",
    )


def host_pressure_snapshot_to_dict(snapshot: HostPressureSnapshot | dict[str, Any]) -> dict[str, Any]:
    """Serialize a host-pressure snapshot without leaking implementation types."""

    if isinstance(snapshot, HostPressureSnapshot):
        return asdict(snapshot)
    return dict(snapshot)


def _number_from_line(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _page_count(label: str, text: str) -> int | None:
    pattern = rf"{re.escape(label)}:\s+([0-9,]+)"
    return _number_from_line(pattern, text)


def _gb_from_pages(pages: int | None, page_size: int | None) -> float | None:
    if pages is None or page_size is None:
        return None
    return round((float(pages) * float(page_size)) / _BYTES_PER_GB, 6)


def classify_host_pressure(
    *,
    free_percent: float | None,
    block_free_percent: float = HOST_PRESSURE_BLOCK_FREE_PERCENT,
    warn_free_percent: float = HOST_PRESSURE_WARN_FREE_PERCENT,
) -> tuple[str, str, str]:
    """Classify a free-percent reading into conservative admission states."""

    if free_percent is None:
        return (
            "unknown",
            "free_percent_missing",
            "Host pressure output did not include a free-percent signal.",
        )
    if free_percent <= block_free_percent:
        return (
            "host_pressure_block",
            "free_percent_at_or_below_block_threshold",
            "Host free memory is below the runtime-owned load-admission threshold.",
        )
    if free_percent <= warn_free_percent:
        return (
            "host_pressure_warn",
            "free_percent_at_or_below_warning_threshold",
            "Host free memory is near the runtime-owned warning threshold.",
        )
    return (
        "normal",
        "free_percent_above_warning_threshold",
        "Host free memory is above the runtime-owned warning threshold.",
    )


def parse_memory_pressure_output(
    text: str,
    *,
    source: str = "memory_pressure",
    sampled_at_s: float | None = None,
    block_free_percent: float = HOST_PRESSURE_BLOCK_FREE_PERCENT,
    warn_free_percent: float = HOST_PRESSURE_WARN_FREE_PERCENT,
) -> HostPressureSnapshot:
    """Parse macOS ``memory_pressure`` output into a stable snapshot."""

    total_bytes = _number_from_line(r"The system has\s+([0-9,]+)", text)
    page_size = _number_from_line(r"page size of\s+([0-9,]+)", text)
    free_percent_raw = _number_from_line(
        r"System-wide memory free percentage:\s+([0-9,]+)%",
        text,
    )
    free_percent = float(free_percent_raw) if free_percent_raw is not None else None
    pages_free = _page_count("Pages free", text)
    pages_wired = _page_count("Pages wired down", text)
    pages_compressor = _page_count("Pages used by compressor", text)

    classification, reason_code, reason_message = classify_host_pressure(
        free_percent=free_percent,
        block_free_percent=block_free_percent,
        warn_free_percent=warn_free_percent,
    )
    return HostPressureSnapshot(
        available=free_percent is not None,
        source=source,
        classification=classification,
        reason_code=reason_code,
        reason_message=reason_message,
        free_percent=free_percent,
        free_gb=_gb_from_pages(pages_free, page_size),
        wired_gb=_gb_from_pages(pages_wired, page_size),
        compressor_gb=_gb_from_pages(pages_compressor, page_size),
        total_gb=round(float(total_bytes) / _BYTES_PER_GB, 6)
        if total_bytes is not None
        else None,
        sampled_at_s=round(float(sampled_at_s), 6) if sampled_at_s is not None else None,
        block_free_percent=float(block_free_percent),
        warn_free_percent=float(warn_free_percent),
        raw_excerpt=text[:1000],
    )


def sample_host_pressure(
    *,
    timeout_s: float = 2.0,
    block_free_percent: float = HOST_PRESSURE_BLOCK_FREE_PERCENT,
    warn_free_percent: float = HOST_PRESSURE_WARN_FREE_PERCENT,
) -> HostPressureSnapshot:
    """Sample host memory pressure for a load-admission decision."""

    sampled_at_s = time.monotonic()
    try:
        completed = subprocess.run(
            ["memory_pressure"],
            check=False,
            capture_output=True,
            text=True,
            timeout=float(timeout_s),
        )
    except (FileNotFoundError, OSError) as exc:
        return HostPressureSnapshot(
            available=False,
            source="memory_pressure",
            classification="unknown",
            reason_code="memory_pressure_command_unavailable",
            reason_message=f"Unable to run memory_pressure: {exc}",
            sampled_at_s=round(sampled_at_s, 6),
        )
    except subprocess.TimeoutExpired:
        return HostPressureSnapshot(
            available=False,
            source="memory_pressure",
            classification="unknown",
            reason_code="memory_pressure_command_timeout",
            reason_message="memory_pressure did not return before the runtime timeout.",
            sampled_at_s=round(sampled_at_s, 6),
        )

    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    if completed.returncode != 0:
        return HostPressureSnapshot(
            available=False,
            source="memory_pressure",
            classification="unknown",
            reason_code="memory_pressure_command_failed",
            reason_message=f"memory_pressure exited with code {completed.returncode}.",
            sampled_at_s=round(sampled_at_s, 6),
            raw_excerpt=output[:1000],
        )
    return parse_memory_pressure_output(
        output,
        sampled_at_s=sampled_at_s,
        block_free_percent=block_free_percent,
        warn_free_percent=warn_free_percent,
    )
