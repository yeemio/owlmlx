"""Eviction soak runner for owlmlx memory-discipline baseline evidence.

The default ``fake`` backend is a smoke/control path: it proves the bench
ledger shape and RuntimeKernel load/generate/unload cleanup without claiming
allocator truth. Use ``--backend native`` for real MLX allocator evidence.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import gc
import json
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Protocol

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.memory_watermark import MemoryWatermark
from owlmlx.runtime import FakeBackend, RuntimeErrorCode, RuntimeKernel
from owlmlx.runtime.mlx_native_backend import MlxNativeBackend
from owlmlx.settle_barrier_event import build_settle_barrier_event, settle_barrier_event_to_dict


BYTES_PER_GB = 1024**3
DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "files"
    / "evidence"
    / "owlmlx"
    / "bench"
    / "eviction_soak"
)
B1B_GATE = "b1b-cache-on-no-regress"
B1C1_GATE = "b1c1-no-swap-soak"
B1C1_REHEARSAL_GATE = "b1c1-interrupted-rehearsal"
B1B_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "files"
    / "evidence"
    / "owlmlx"
    / "bench"
    / "cache-settle-no-regress"
)
B1C1_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "files"
    / "evidence"
    / "owlmlx"
    / "bench"
    / "session-kv-soak"
)
B1B_MODEL_ID = "gemma-4-31B-it"
B1B_MODEL_PATH = "/Users/yeemio/AI/Agent/models/gemma-4-31B-it"
DEFAULT_PROMPT = "Reply with exactly: owlmlx eviction soak"
B1C1_DURATION_S = 24 * 60 * 60
B1C1_SAMPLE_INTERVAL_S = 60.0
B1C1_DRIFT_BUDGET_BYTES = 200 * 1024 * 1024
B1C1_WARMUP_CYCLES = 1
B1C1_WALL_CLOCK_GAP_FACTOR = 3.0
B1C1_MIN_WALL_CLOCK_GAP_BUDGET_S = 10.0
B1C1_INTERRUPTION_REASONS = {
    "planned_stop",
    "host_sleep",
    "user_interrupt",
    "failure",
    "unknown",
}
B1B_SESSION_ID_PREFIX = "b1b-gemma4-31b"
B1C1_SESSION_ID_PREFIX = "b1c1-no-swap"
B1C1_PROMPTS: tuple[tuple[str, str], ...] = (
    ("short", "Reply with exactly: owlmlx session cache soak"),
    (
        "medium",
        "You are validating a local runtime soak. Return one concise sentence "
        "confirming that the session cache request completed.",
    ),
    (
        "long",
        "Summarize the runtime discipline in three short clauses: session reuse, "
        "memory watermark discipline, and reclaim-barrier observation. Keep it brief.",
    ),
)


@dataclass(frozen=True, slots=True)
class ModelSpec:
    model_id: str
    memory_gb: float


@dataclass(frozen=True, slots=True)
class SettleResult:
    active_memory_bytes: int | None
    iterations: int
    duration_ms: float


@dataclass(frozen=True, slots=True)
class StreamGenerationResult:
    ok: bool
    message: str
    error_code: Any | None
    model_id: str | None
    text: str = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    finish_reason: str | None = None


class MemorySampler(Protocol):
    measurement_mode: str

    def active_memory_bytes(self, kernel: RuntimeKernel) -> int | None:
        """Return the current active memory reading, or None when unavailable."""

    def settle(self, kernel: RuntimeKernel, *, max_iterations: int, sleep_s: float) -> SettleResult:
        """Wait for the memory reading to settle after unload."""


class InventoryMemorySampler:
    """Smoke-only sampler derived from RuntimeKernel loaded inventory.

    This does not measure MLX allocator state. It is deliberately labeled as a
    synthetic control so the JSONL shape can be exercised on hosts without MLX.
    """

    measurement_mode = "synthetic_runtime_inventory_smoke"

    def active_memory_bytes(self, kernel: RuntimeKernel) -> int:
        total_gb = float(kernel.status_dict()["inventory"].get("total_loaded_gb") or 0.0)
        return int(total_gb * BYTES_PER_GB)

    def settle(self, kernel: RuntimeKernel, *, max_iterations: int, sleep_s: float) -> SettleResult:
        started = time.monotonic()
        iterations = max(1, min(max_iterations, 1))
        value = self.active_memory_bytes(kernel)
        if sleep_s > 0:
            time.sleep(sleep_s)
        return SettleResult(
            active_memory_bytes=value,
            iterations=iterations,
            duration_ms=round((time.monotonic() - started) * 1000.0, 3),
        )


class MlxMemorySampler:
    """Real allocator sampler backed by ``mlx.core.get_active_memory``."""

    measurement_mode = "mlx_core_active_memory"

    def __init__(self, mx_module: object) -> None:
        self._mx = mx_module

    @classmethod
    def create(cls) -> "MlxMemorySampler":
        try:
            import mlx.core as mx  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "native eviction soak requires mlx.core in this environment"
            ) from exc
        get_active = getattr(mx, "get_active_memory", None)
        if not callable(get_active):
            raise RuntimeError("native eviction soak requires mlx.core.get_active_memory")
        return cls(mx)

    def active_memory_bytes(self, kernel: RuntimeKernel) -> int:
        _ = kernel
        return int(self._mx.get_active_memory())  # type: ignore[attr-defined]

    def settle(self, kernel: RuntimeKernel, *, max_iterations: int, sleep_s: float) -> SettleResult:
        _ = kernel
        started = time.monotonic()
        last: int | None = None
        stable_count = 0
        iterations = 0
        for idx in range(1, max_iterations + 1):
            iterations = idx
            gc.collect()
            value = self.active_memory_bytes(kernel)
            if value == last:
                stable_count += 1
            else:
                stable_count = 0
            last = value
            if stable_count >= 1:
                break
            if sleep_s > 0:
                time.sleep(sleep_s)
        return SettleResult(
            active_memory_bytes=last,
            iterations=iterations,
            duration_ms=round((time.monotonic() - started) * 1000.0, 3),
        )


def _now_compact_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso_utc(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _bytes_to_gb(value: int | None) -> float | None:
    if value is None:
        return None
    return round(value / BYTES_PER_GB, 6)


def _watermark(value_bytes: int | None, *, profile: MachineMemoryProfile) -> str:
    if value_bytes is None:
        return MemoryWatermark.UNKNOWN.name
    utilization = (value_bytes / BYTES_PER_GB) / profile.serving_budget_gb
    return MemoryWatermark.from_utilization(utilization).name


def _result_to_dict(result: Any) -> dict[str, Any]:
    return {
        "ok": bool(result.ok),
        "message": result.message,
        "error_code": result.error_code.value if result.error_code is not None else None,
        "model_id": getattr(result, "model_id", None),
        "freed_gb": getattr(result, "freed_gb", None),
        "active_memory_freed_bytes": getattr(result, "active_memory_freed_bytes", None),
        "cache_memory_freed_bytes": getattr(result, "cache_memory_freed_bytes", None),
    }


async def _stream_generate_once(
    kernel: RuntimeKernel,
    *,
    model_id: str,
    prompt: str,
    max_tokens: int,
    session_id: str | None = None,
) -> StreamGenerationResult:
    text_parts: list[str] = []
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    finish_reason: str | None = None
    saw_done = False
    async for event in kernel.generate_stream(
        prompt,
        model_id=model_id,
        max_tokens=max_tokens,
        session_id=session_id,
        temperature=0.0,
        seed=42,
    ):
        if event.prompt_tokens is not None:
            prompt_tokens = int(event.prompt_tokens)
        if event.completion_tokens is not None:
            completion_tokens = int(event.completion_tokens)
        if event.finish_reason:
            finish_reason = event.finish_reason
        if event.event == "token":
            text_parts.append(event.text)
            continue
        if event.event == "done":
            saw_done = True
            break
        if event.event == "error":
            return StreamGenerationResult(
                ok=False,
                message=str(event.detail.get("message", "stream generation failed")),
                error_code=event.error_code,
                model_id=event.model_id or model_id,
                text="".join(text_parts),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=finish_reason,
            )
    return StreamGenerationResult(
        ok=saw_done,
        message="stream generated" if saw_done else "stream ended before done",
        error_code=None if saw_done else RuntimeErrorCode.backend_error,
        model_id=model_id,
        text="".join(text_parts),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        finish_reason=finish_reason or "stop",
    )


def _make_kernel(*, backend: str, profile: MachineMemoryProfile) -> tuple[RuntimeKernel, MemorySampler]:
    if backend == "fake":
        return RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=profile), InventoryMemorySampler()
    if backend == "native":
        return RuntimeKernel(MlxNativeBackend(), profile=profile), MlxMemorySampler.create()
    raise ValueError(f"unsupported backend: {backend}")


@contextlib.contextmanager
def _session_cache_env(
    enabled: bool,
    *,
    ttl_s: float | None = None,
    max_entries: int | None = None,
) -> Iterator[None]:
    previous_enabled = os.environ.get("OWLMLX_SESSION_CACHE_ENABLED")
    previous_ttl = os.environ.get("OWLMLX_SESSION_CACHE_TTL_S")
    previous_max_entries = os.environ.get("OWLMLX_SESSION_CACHE_MAX_ENTRIES")
    os.environ["OWLMLX_SESSION_CACHE_ENABLED"] = "1" if enabled else "0"
    if ttl_s is not None:
        os.environ["OWLMLX_SESSION_CACHE_TTL_S"] = str(float(ttl_s))
    if max_entries is not None:
        os.environ["OWLMLX_SESSION_CACHE_MAX_ENTRIES"] = str(int(max_entries))
    try:
        yield
    finally:
        if previous_enabled is None:
            os.environ.pop("OWLMLX_SESSION_CACHE_ENABLED", None)
        else:
            os.environ["OWLMLX_SESSION_CACHE_ENABLED"] = previous_enabled
        if previous_ttl is None:
            os.environ.pop("OWLMLX_SESSION_CACHE_TTL_S", None)
        else:
            os.environ["OWLMLX_SESSION_CACHE_TTL_S"] = previous_ttl
        if previous_max_entries is None:
            os.environ.pop("OWLMLX_SESSION_CACHE_MAX_ENTRIES", None)
        else:
            os.environ["OWLMLX_SESSION_CACHE_MAX_ENTRIES"] = previous_max_entries


def _percentile(values: list[float | int], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return round(ordered[0], 3)
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return round(ordered[lower] * (1.0 - weight) + ordered[upper] * weight, 3)


def _counter_value(counters: dict[str, Any], key: str) -> int:
    try:
        return int(counters.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


def _counter_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, int]:
    keys = set(before) | set(after) | {"hits", "misses", "drops", "evictions", "rejects"}
    return {key: _counter_value(after, key) - _counter_value(before, key) for key in sorted(keys)}


def _session_cache_status(kernel: RuntimeKernel) -> dict[str, Any]:
    detail = kernel.status_dict().get("backend", {}).get("detail", {})
    if isinstance(detail, dict):
        status = detail.get("session_kv_cache", {})
        if isinstance(status, dict):
            return status
    return {}


def _session_cache_observation(
    *,
    backend: str,
    cache_enabled: bool,
    before: dict[str, Any],
    after_cold: dict[str, Any],
    after_warm: dict[str, Any] | None,
) -> dict[str, Any]:
    if not cache_enabled:
        return {
            "active_entries_before_unload": None,
            "active_entries_after_unload": None,
            "cold_request_hit": None,
            "warm_request_hit": None,
            "hits_delta": 0,
            "misses_delta": 0,
            "drops_delta": 0,
            "evictions_delta": 0,
            "rejects_delta": 0,
            "synthetic": backend == "fake",
            "allocator_truth": False,
        }
    if backend == "fake":
        return {
            "active_entries_before_unload": 1,
            "active_entries_after_unload": 0,
            "cold_request_hit": False,
            "warm_request_hit": True,
            "hits_delta": 1,
            "misses_delta": 1,
            "drops_delta": 0,
            "evictions_delta": 0,
            "rejects_delta": 0,
            "synthetic": True,
            "allocator_truth": False,
        }
    before_counters = dict(before.get("counters", {}))
    cold_counters = dict(after_cold.get("counters", {}))
    warm_counters = dict((after_warm or after_cold).get("counters", {}))
    cold_delta = _counter_delta(before_counters, cold_counters)
    total_delta = _counter_delta(before_counters, warm_counters)
    warm_delta = _counter_delta(cold_counters, warm_counters)
    return {
        "active_entries_before_unload": (after_warm or after_cold).get("active_entries"),
        "active_entries_after_unload": None,
        "cold_request_hit": _counter_value(cold_delta, "hits") > 0,
        "warm_request_hit": _counter_value(warm_delta, "hits") > 0,
        "hits_delta": _counter_value(total_delta, "hits"),
        "misses_delta": _counter_value(total_delta, "misses"),
        "drops_delta": _counter_value(total_delta, "drops"),
        "evictions_delta": _counter_value(total_delta, "evictions"),
        "rejects_delta": _counter_value(total_delta, "rejects"),
        "synthetic": False,
        "allocator_truth": True,
    }


def _reclaim_stats(kernel: RuntimeKernel) -> dict[str, Any]:
    stats = getattr(kernel, "reclaim_barrier_stats", None)
    if not callable(stats):
        return {
            "summary": {
                "measurement_count": 0,
                "failure_measurement_count": 0,
                "event_count": 0,
                "unresolved_event_count": 0,
            },
            "duration_ms": {},
            "observed_active_memory_freed_bytes": {},
            "observed_cache_memory_freed_bytes": {},
            "expected_minus_observed_active_bytes": {},
            "events": [],
            "missing_signals": [{"signal": "reclaim_barrier_stats", "reason_code": "not_available"}],
        }
    return stats()


def _settle_barrier_snapshot(kernel: RuntimeKernel) -> dict[str, Any]:
    return settle_barrier_event_to_dict(
        build_settle_barrier_event(runtime_status=kernel.status_dict())
    )


def _compact_settle_barrier(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "barrier_state": snapshot.get("summary", {}).get("barrier_state"),
        "unresolved_event_count": snapshot.get("barrier", {}).get("unresolved_event_count", 0),
        "total_event_count": snapshot.get("barrier", {}).get("total_event_count", 0),
    }


def _b1b_round_verdict(
    *,
    load: Any,
    generations: list[Any],
    unload: Any,
    session_cache: dict[str, Any],
    settle_barrier: dict[str, Any],
    reclaim_stats: dict[str, Any],
) -> str:
    failure_measurements = int(
        reclaim_stats.get("summary", {}).get("failure_measurement_count", 0) or 0
    )
    failed = (
        not bool(load.ok)
        or not all(bool(item.ok) for item in generations)
        or not bool(unload.ok)
        or int(session_cache.get("drops_delta") or 0) > 0
        or failure_measurements > 0
        or settle_barrier.get("barrier_state") in {"failed_unload", "failed_reclaim"}
        or int(settle_barrier.get("unresolved_event_count") or 0) > 0
    )
    return "failed" if failed else "passed"


def _mode_filename(timestamp: str, *, model_id: str, mode: str, rounds: int) -> str:
    cache_part = "cache-off" if mode == "cache_off_baseline" else "cache-on"
    safe_model = model_id.strip("/").replace("/", "-")
    return f"{timestamp}-b1b-{safe_model}-{cache_part}-n{rounds}.jsonl"


def _rollup_filename(timestamp: str, *, model_id: str) -> str:
    safe_model = model_id.strip("/").replace("/", "-")
    return f"{timestamp}-b1b-{safe_model}-cache-on-no-regress-rollup.jsonl"


def _b1c1_filename(timestamp: str, *, model_id: str) -> str:
    safe_model = model_id.strip("/").replace("/", "-")
    return f"{timestamp}-b1c1-{safe_model}-no-swap-soak.jsonl"


def _b1c1_rollup_filename(timestamp: str, *, model_id: str) -> str:
    safe_model = model_id.strip("/").replace("/", "-")
    return f"{timestamp}-b1c1-{safe_model}-no-swap-soak-rollup.jsonl"


def _b1c1_rehearsal_rollup_filename(timestamp: str) -> str:
    return f"{timestamp}-b1c1-interrupted-no-swap-rehearsal-rollup.jsonl"


def _b1c1_sample_interval_from_records(records: list[dict[str, Any]]) -> float:
    for record in records:
        value = record.get("config", {}).get("sample_interval_s")
        try:
            return max(float(value), 0.0)
        except (TypeError, ValueError):
            continue
    return float(B1C1_SAMPLE_INTERVAL_S)


def _b1c1_wall_clock_continuity(records: list[dict[str, Any]]) -> dict[str, Any]:
    sample_interval_s = _b1c1_sample_interval_from_records(records)
    gap_budget_s = max(
        sample_interval_s * B1C1_WALL_CLOCK_GAP_FACTOR,
        B1C1_MIN_WALL_CLOCK_GAP_BUDGET_S,
    )
    timestamped: list[tuple[dict[str, Any], datetime]] = []
    missing_timestamp_count = 0
    for record in records:
        timestamp = _parse_iso_utc(record.get("timestamp_utc"))
        if timestamp is None:
            missing_timestamp_count += 1
            continue
        timestamped.append((record, timestamp))

    sample_gaps: list[float] = []
    measurement_gaps: list[float] = []
    sample_gap_violations: list[dict[str, Any]] = []
    measurement_gap_violations: list[dict[str, Any]] = []
    for (previous_record, previous_ts), (record, timestamp) in zip(
        timestamped,
        timestamped[1:],
    ):
        gap_s = max((timestamp - previous_ts).total_seconds(), 0.0)
        sample_gaps.append(gap_s)
        violation = {
            "previous_sample_index": previous_record.get("sample_index"),
            "sample_index": record.get("sample_index"),
            "previous_phase": previous_record.get("phase"),
            "phase": record.get("phase"),
            "gap_s": round(gap_s, 3),
            "budget_s": round(gap_budget_s, 3),
        }
        if gap_s > gap_budget_s:
            sample_gap_violations.append(violation)
        if (
            previous_record.get("phase") == "measurement"
            and record.get("phase") == "measurement"
        ):
            measurement_gaps.append(gap_s)
            if gap_s > gap_budget_s:
                measurement_gap_violations.append(violation)

    measurement_record_count = sum(
        1 for record in records if record.get("phase") == "measurement"
    )
    timestamped_measurement_count = sum(
        1 for record, _timestamp in timestamped if record.get("phase") == "measurement"
    )
    measurement_observable = timestamped_measurement_count == measurement_record_count
    measurement_wall_clock_gap_free = (
        measurement_observable and not measurement_gap_violations
    )
    return {
        "sample_interval_s": sample_interval_s,
        "sample_wall_clock_gap_budget_s": round(gap_budget_s, 3),
        "timestamped_sample_count": len(timestamped),
        "missing_timestamp_count": missing_timestamp_count,
        "max_sample_wall_clock_gap_s": round(max(sample_gaps), 3) if sample_gaps else 0.0,
        "max_measurement_wall_clock_gap_s": (
            round(max(measurement_gaps), 3) if measurement_gaps else 0.0
        ),
        "sample_wall_clock_gap_free": missing_timestamp_count == 0
        and not sample_gap_violations,
        "measurement_wall_clock_gap_free": measurement_wall_clock_gap_free,
        "sample_wall_clock_gap_violation_count": len(sample_gap_violations),
        "measurement_wall_clock_gap_violation_count": len(
            measurement_gap_violations
        ),
        "sample_wall_clock_gap_violations": sample_gap_violations[:8],
        "measurement_wall_clock_gap_violations": measurement_gap_violations[:8],
    }


def _read_first_jsonl_record(path: Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path} first JSONL row is not an object")
                return value
    raise ValueError(f"{path} has no JSONL records")


def _missing_signal_names(record: dict[str, Any]) -> set[str]:
    return {
        str(item.get("signal"))
        for item in record.get("reclaim_barrier_stats_after_round", {}).get("missing_signals", [])
        if isinstance(item, dict)
    }


def _unresolved_reclaim_events(record: dict[str, Any], operation: str) -> int:
    events = record.get("reclaim_barrier_stats_after_round", {}).get("events", [])
    if not isinstance(events, list):
        return 0
    return sum(
        1
        for event in events
        if isinstance(event, dict)
        and event.get("operation") == operation
        and not event.get("resolved", False)
    )


def _b1b_mode_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    durations = [
        float(record["operation"]["settle_barrier_duration_ms"])
        for record in records
        if record.get("operation", {}).get("settle_barrier_duration_ms") is not None
    ]
    reclaim_stats = records[-1].get("reclaim_barrier_stats_after_round", {}) if records else {}
    summary = reclaim_stats.get("summary", {})
    return {
        "rounds": len(records),
        "warm_hits": sum(
            1 for record in records if record.get("session_cache", {}).get("warm_request_hit") is True
        ),
        "drops_total": sum(int(record.get("session_cache", {}).get("drops_delta") or 0) for record in records),
        "failed_unload_events_total": sum(
            1
            for record in records
            if not record.get("operation", {}).get("unload_ok")
            or record.get("settle_barrier_event", {}).get("barrier_state") == "failed_unload"
        )
        + sum(_unresolved_reclaim_events(record, "explicit_unload") for record in records),
        "failed_reclaim_events_total": sum(
            1
            for record in records
            if record.get("settle_barrier_event", {}).get("barrier_state") == "failed_reclaim"
        )
        + sum(_unresolved_reclaim_events(record, "ttl_sweep_reclaim") for record in records),
        "failure_measurement_count": int(summary.get("failure_measurement_count", 0) or 0),
        "unresolved_reclaim_barrier_events": int(summary.get("unresolved_event_count", 0) or 0),
        "duration_p50_ms": _percentile(durations, 0.50),
        "duration_p99_ms": _percentile(durations, 0.99),
        "missing_signals": sorted(set().union(*(_missing_signal_names(record) for record in records)) if records else set()),
        "all_rounds_passed": all(record.get("round_verdict") == "passed" for record in records),
    }


def _b1b_rollup(
    *,
    run_id: str,
    baseline_records: list[dict[str, Any]],
    candidate_records: list[dict[str, Any]],
    baseline_ledger: Path | None,
    candidate_ledger: Path | None,
) -> dict[str, Any]:
    baseline = _b1b_mode_summary(baseline_records)
    candidate = _b1b_mode_summary(candidate_records)
    baseline_p50 = baseline["duration_p50_ms"]
    candidate_p50 = candidate["duration_p50_ms"]
    baseline_p99 = baseline["duration_p99_ms"]
    candidate_p99 = candidate["duration_p99_ms"]
    p50_within = (
        True
        if baseline_p50 is None or candidate_p50 is None
        else candidate_p50 <= (baseline_p50 * 1.20 + 100.0)
    )
    p99_within = (
        True
        if baseline_p99 is None or candidate_p99 is None
        else candidate_p99 <= (baseline_p99 * 1.50 + 250.0)
    )
    missing_symmetric = baseline.get("missing_signals") == candidate.get("missing_signals")
    failed_reclaim = baseline["failed_reclaim_events_total"] + candidate["failed_reclaim_events_total"]
    failed_unload = baseline["failed_unload_events_total"] + candidate["failed_unload_events_total"]
    failure_measurements = baseline["failure_measurement_count"] + candidate["failure_measurement_count"]
    has_required_ledgers = bool(baseline_records and candidate_records)
    candidate_required_ok = (
        candidate["warm_hits"] >= candidate["rounds"]
        and candidate["drops_total"] == 0
        and candidate["all_rounds_passed"]
    )
    ok = (
        has_required_ledgers
        and baseline["all_rounds_passed"]
        and candidate_required_ok
        and failed_reclaim == 0
        and failed_unload == 0
        and failure_measurements == 0
        and p50_within
        and p99_within
        and missing_symmetric
    )
    verdict = "passed" if ok else ("failed" if has_required_ledgers else "blocked")
    return {
        "schema_version": "b1b.v1",
        "gate": "B-1b",
        "run_id": run_id,
        "timestamp_utc": _now_iso_utc(),
        "baseline_ledger": str(baseline_ledger) if baseline_ledger is not None else None,
        "candidate_ledger": str(candidate_ledger) if candidate_ledger is not None else None,
        "baseline_rounds": baseline["rounds"],
        "candidate_rounds": candidate["rounds"],
        "candidate_warm_hits": candidate["warm_hits"],
        "candidate_drops_total": candidate["drops_total"],
        "failed_reclaim_events_total": failed_reclaim,
        "failed_unload_events_total": failed_unload,
        "failure_measurement_count": failure_measurements,
        "duration_alignment": {
            "baseline_p50_ms": baseline_p50,
            "candidate_p50_ms": candidate_p50,
            "baseline_p99_ms": baseline_p99,
            "candidate_p99_ms": candidate_p99,
            "p50_within_threshold": p50_within,
            "p99_within_threshold": p99_within,
        },
        "missing_signals_symmetric": missing_symmetric,
        "required_ledgers_present": has_required_ledgers,
        "cache_on_no_regress": verdict,
        "conclusion": verdict,
        "graduates": {
            "cache_on_no_regress": ok,
            "unblock_B_1c_section_1": ok,
        },
    }


def _b1c1_max_drift_bytes(profile: MachineMemoryProfile) -> int:
    host_budget_bytes = int(profile.serving_budget_gb * BYTES_PER_GB * 0.005)
    return min(B1C1_DRIFT_BUDGET_BYTES, host_budget_bytes)


def _b1c1_default_session_cache_ttl_s(
    *,
    duration_s: float,
    required_duration_s: float,
    sample_interval_s: float,
) -> float:
    return max(
        float(B1C1_DURATION_S) + 3600.0,
        float(required_duration_s) + 3600.0,
        float(duration_s) + float(sample_interval_s) * len(B1C1_PROMPTS) + 3600.0,
    )


def _b1c1_round_verdict(
    *,
    load_ok: bool,
    generation: StreamGenerationResult,
    watermark: str,
    reclaim_stats: dict[str, Any],
    settle_barrier: dict[str, Any],
) -> str:
    failure_measurements = int(
        reclaim_stats.get("summary", {}).get("failure_measurement_count", 0) or 0
    )
    failed = (
        not load_ok
        or not generation.ok
        or watermark == MemoryWatermark.FATAL.name
        or failure_measurements > 0
        or settle_barrier.get("barrier_state") in {"failed_unload", "failed_reclaim"}
        or int(settle_barrier.get("unresolved_event_count") or 0) > 0
    )
    return "failed" if failed else "passed"


def _record_summary(records: list[dict[str, Any]], *, max_drift_gb: float) -> dict[str, Any]:
    settled = [
        float(record["active_memory_gb_after_unload_settled"])
        for record in records
        if record["active_memory_gb_after_unload_settled"] is not None
    ]
    total_drift_gb = round(max(settled) - min(settled), 6) if len(settled) >= 2 else 0.0
    operations_ok = all(bool(record["ok"]) for record in records)
    return {
        "ok": operations_ok and total_drift_gb <= max_drift_gb,
        "rounds": len(records),
        "total_drift_gb": total_drift_gb,
        "max_drift_gb": max_drift_gb,
        "operations_ok": operations_ok,
    }


def run_eviction_soak(
    *,
    runtime: str,
    backend: str,
    model_a: ModelSpec,
    model_b: ModelSpec,
    rounds: int,
    output_dir: Path,
    max_drift_gb: float = 0.5,
    prompt: str = DEFAULT_PROMPT,
    max_tokens: int = 1,
    settle_iterations: int = 5,
    settle_sleep_ms: float = 0.0,
    profile_memory_gb: float = 128.0,
) -> dict[str, Any]:
    if runtime != "owlmlx":
        raise ValueError("only --runtime owlmlx is implemented in this baseline round")
    if rounds < 1:
        raise ValueError("--rounds must be >= 1")

    profile = MachineMemoryProfile(
        system_memory_gb=profile_memory_gb,
        system_reserve_gb=2.0,
        serving_budget_gb=max(profile_memory_gb - 2.0, 1.0),
        warning_threshold_gb=max(profile_memory_gb - 10.0, 1.0),
    )
    kernel, sampler = _make_kernel(backend=backend, profile=profile)
    run_id = f"{_now_compact_utc()}-{runtime}-{backend}-n{rounds}"
    output_path = output_dir / f"{run_id}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    first_settled_gb: float | None = None
    models = (model_a, model_b)
    settle_sleep_s = settle_sleep_ms / 1000.0

    with output_path.open("w", encoding="utf-8") as stream:
        for round_idx in range(1, rounds + 1):
            target = models[(round_idx - 1) % 2]
            source = models[round_idx % 2]
            before_bytes = sampler.active_memory_bytes(kernel)
            load = kernel.load_model(target.model_id, memory_gb=target.memory_gb)
            after_load_bytes = sampler.active_memory_bytes(kernel)
            generation = (
                asyncio.run(kernel.generate(prompt, model_id=target.model_id, max_tokens=max_tokens))
                if load.ok
                else None
            )
            unload = kernel.unload_model(target.model_id) if load.ok else None
            settle = sampler.settle(
                kernel,
                max_iterations=settle_iterations,
                sleep_s=settle_sleep_s,
            )
            after_unload_gb = _bytes_to_gb(settle.active_memory_bytes)
            if first_settled_gb is None and after_unload_gb is not None:
                first_settled_gb = after_unload_gb
            drift_gb = (
                round(after_unload_gb - first_settled_gb, 6)
                if after_unload_gb is not None and first_settled_gb is not None
                else None
            )
            ok = bool(load.ok and (generation is not None and generation.ok) and (unload is not None and unload.ok))
            record = {
                "run_id": run_id,
                "runtime": runtime,
                "backend": backend,
                "measurement_mode": sampler.measurement_mode,
                "evidence_strength": (
                    "mlx_allocator_baseline" if backend == "native" else "smoke_only_no_allocator_claim"
                ),
                "round": round_idx,
                "switch": f"{source.model_id}\u2192{target.model_id}",
                "model_from": source.model_id,
                "model_to": target.model_id,
                "active_memory_gb_before": _bytes_to_gb(before_bytes),
                "active_memory_gb_after_load": _bytes_to_gb(after_load_bytes),
                "active_memory_gb_after_unload_settled": after_unload_gb,
                "active_memory_bytes_before": before_bytes,
                "active_memory_bytes_after_load": after_load_bytes,
                "active_memory_bytes_after_unload_settled": settle.active_memory_bytes,
                "settle_barrier_iterations": settle.iterations,
                "settle_barrier_duration_ms": settle.duration_ms,
                "watermark_before": _watermark(before_bytes, profile=profile),
                "watermark_after": _watermark(settle.active_memory_bytes, profile=profile),
                "ok": ok,
                "drift_gb": drift_gb,
                "load_result": _result_to_dict(load),
                "generate_result": _result_to_dict(generation) if generation is not None else None,
                "unload_result": _result_to_dict(unload) if unload is not None else None,
            }
            records.append(record)
            stream.write(json.dumps(record, sort_keys=True))
            stream.write("\n")

    summary = _record_summary(records, max_drift_gb=max_drift_gb)
    summary.update(
        {
            "run_id": run_id,
            "runtime": runtime,
            "backend": backend,
            "measurement_mode": sampler.measurement_mode,
            "output_path": str(output_path),
        }
    )
    return summary


def _run_b1b_mode(
    *,
    runtime: str,
    backend: str,
    model: ModelSpec,
    model_label: str,
    mode: str,
    rounds: int,
    output_path: Path,
    run_id: str,
    prompt: str,
    max_tokens: int,
    session_id_prefix: str,
    settle_iterations: int,
    settle_sleep_ms: float,
    profile_memory_gb: float,
) -> list[dict[str, Any]]:
    cache_enabled = mode == "cache_on_candidate"
    profile = MachineMemoryProfile(
        system_memory_gb=profile_memory_gb,
        system_reserve_gb=2.0,
        serving_budget_gb=max(profile_memory_gb - 2.0, 1.0),
        warning_threshold_gb=max(profile_memory_gb - 10.0, 1.0),
    )
    with _session_cache_env(cache_enabled):
        kernel, sampler = _make_kernel(backend=backend, profile=profile)
        records: list[dict[str, Any]] = []
        output_path.parent.mkdir(parents=True, exist_ok=True)
        settle_sleep_s = settle_sleep_ms / 1000.0
        with output_path.open("w", encoding="utf-8") as stream:
            for round_idx in range(1, rounds + 1):
                session_id = (
                    f"{session_id_prefix}-r{round_idx}"
                    if cache_enabled
                    else None
                )
                before_bytes = sampler.active_memory_bytes(kernel)
                cache_before = _session_cache_status(kernel)
                load = kernel.load_model(model.model_id, memory_gb=model.memory_gb)
                after_load_bytes = sampler.active_memory_bytes(kernel)
                generations: list[Any] = []
                cache_after_cold = cache_before
                cache_after_warm: dict[str, Any] | None = None
                if load.ok:
                    cold = asyncio.run(
                        _stream_generate_once(
                            kernel,
                            model_id=model.model_id,
                            prompt=prompt,
                            max_tokens=max_tokens,
                            session_id=session_id,
                        )
                    )
                    generations.append(cold)
                    cache_after_cold = _session_cache_status(kernel)
                    if cache_enabled:
                        warm = asyncio.run(
                            _stream_generate_once(
                                kernel,
                                model_id=model.model_id,
                                prompt=prompt,
                                max_tokens=max_tokens,
                                session_id=session_id,
                            )
                        )
                        generations.append(warm)
                        cache_after_warm = _session_cache_status(kernel)
                session_cache = _session_cache_observation(
                    backend=backend,
                    cache_enabled=cache_enabled,
                    before=cache_before,
                    after_cold=cache_after_cold,
                    after_warm=cache_after_warm,
                )
                unload = kernel.unload_model(model.model_id) if load.ok else None
                settle = sampler.settle(
                    kernel,
                    max_iterations=settle_iterations,
                    sleep_s=settle_sleep_s,
                )
                if cache_enabled:
                    session_cache["active_entries_after_unload"] = (
                        0 if backend == "fake" else _session_cache_status(kernel).get("active_entries")
                    )
                reclaim_stats = _reclaim_stats(kernel)
                settle_snapshot = _compact_settle_barrier(_settle_barrier_snapshot(kernel))
                generation_ok = bool(generations) and all(bool(item.ok) for item in generations)
                unload_result = unload if unload is not None else load
                record = {
                    "schema_version": "b1b.v1",
                    "gate": "B-1b",
                    "run_id": run_id,
                    "mode": mode,
                    "round": round_idx,
                    "timestamp_utc": _now_iso_utc(),
                    "model": {
                        "id": model_label,
                        "path": model.model_id,
                        "runtime_model_id": model.model_id,
                        "hf_commit_sha": None,
                        "mlx_lm_version": None,
                    },
                    "runtime": runtime,
                    "backend": backend,
                    "measurement_mode": sampler.measurement_mode,
                    "evidence_strength": (
                        "mlx_allocator_baseline" if backend == "native" else "smoke_only_no_allocator_claim"
                    ),
                    "config": {
                        "OWLMLX_SESSION_CACHE_ENABLED": "1" if cache_enabled else "0",
                        "session_id": session_id,
                        "temperature": 0.0,
                        "seed": 42,
                        "max_tokens": max_tokens,
                        "max_generation_concurrency": 1,
                    },
                    "session_cache": session_cache,
                    "operation": {
                        "load_ok": bool(load.ok),
                        "generation_ok": generation_ok,
                        "unload_ok": bool(unload.ok) if unload is not None else False,
                        "settle_barrier_iterations": settle.iterations,
                        "settle_barrier_duration_ms": settle.duration_ms,
                    },
                    "memory": {
                        "active_memory_before_bytes": before_bytes,
                        "active_memory_after_load_bytes": after_load_bytes,
                        "active_memory_after_unload_settled_bytes": settle.active_memory_bytes,
                        "watermark_before": _watermark(before_bytes, profile=profile),
                        "watermark_after": _watermark(settle.active_memory_bytes, profile=profile),
                    },
                    "settle_barrier_event": settle_snapshot,
                    "reclaim_barrier_stats_after_round": reclaim_stats,
                    "load_result": _result_to_dict(load),
                    "generate_results": [_result_to_dict(item) for item in generations],
                    "unload_result": _result_to_dict(unload) if unload is not None else None,
                }
                record["round_verdict"] = _b1b_round_verdict(
                    load=load,
                    generations=generations,
                    unload=unload_result,
                    session_cache=session_cache,
                    settle_barrier=settle_snapshot,
                    reclaim_stats=reclaim_stats,
                )
                records.append(record)
                stream.write(json.dumps(record, sort_keys=True))
                stream.write("\n")
        return records


def run_b1b_cache_on_no_regress(
    *,
    runtime: str,
    backend: str,
    model: ModelSpec,
    model_label: str = B1B_MODEL_ID,
    rounds: int,
    output_dir: Path,
    cache_mode: str = "both",
    session_id_prefix: str = B1B_SESSION_ID_PREFIX,
    prompt: str = DEFAULT_PROMPT,
    max_tokens: int = 2,
    settle_iterations: int = 5,
    settle_sleep_ms: float = 0.0,
    profile_memory_gb: float = 128.0,
) -> dict[str, Any]:
    if runtime != "owlmlx":
        raise ValueError("only --runtime owlmlx is implemented in this baseline round")
    if rounds < 1:
        raise ValueError("--rounds must be >= 1")
    if cache_mode not in {"off", "on", "both"}:
        raise ValueError("--cache-mode must be off, on, or both")

    timestamp = _now_compact_utc()
    run_id = f"{timestamp}-{runtime}-{backend}-{B1B_GATE}-n{rounds}"
    modes = []
    if cache_mode in {"off", "both"}:
        modes.append("cache_off_baseline")
    if cache_mode in {"on", "both"}:
        modes.append("cache_on_candidate")

    baseline_records: list[dict[str, Any]] = []
    candidate_records: list[dict[str, Any]] = []
    baseline_path: Path | None = None
    candidate_path: Path | None = None
    for mode in modes:
        path = output_dir / _mode_filename(timestamp, model_id=model_label, mode=mode, rounds=rounds)
        records = _run_b1b_mode(
            runtime=runtime,
            backend=backend,
            model=model,
            model_label=model_label,
            mode=mode,
            rounds=rounds,
            output_path=path,
            run_id=run_id,
            prompt=prompt,
            max_tokens=max_tokens,
            session_id_prefix=session_id_prefix,
            settle_iterations=settle_iterations,
            settle_sleep_ms=settle_sleep_ms,
            profile_memory_gb=profile_memory_gb,
        )
        if mode == "cache_off_baseline":
            baseline_records = records
            baseline_path = path
        else:
            candidate_records = records
            candidate_path = path

    rollup = _b1b_rollup(
        run_id=run_id,
        baseline_records=baseline_records,
        candidate_records=candidate_records,
        baseline_ledger=baseline_path,
        candidate_ledger=candidate_path,
    )
    rollup_path = output_dir / _rollup_filename(timestamp, model_id=model_label)
    rollup_path.parent.mkdir(parents=True, exist_ok=True)
    with rollup_path.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(rollup, sort_keys=True))
        stream.write("\n")
    return {
        **rollup,
        "ok": rollup["conclusion"] == "passed",
        "backend": backend,
        "cache_mode": cache_mode,
        "output_dir": str(output_dir),
        "rollup_path": str(rollup_path),
    }


def _b1c1_rollup(
    *,
    run_id: str,
    model: ModelSpec,
    model_label: str,
    backend: str,
    measurement_mode: str,
    output_path: Path,
    records: list[dict[str, Any]],
    started_monotonic_s: float,
    measurement_started_monotonic_s: float | None,
    measurement_finished_monotonic_s: float | None,
    required_duration_s: float,
    drift_budget_bytes: int,
    load: Any,
    cleanup_unload: Any | None,
    cleanup_settle: SettleResult | None,
    rehearsal_group_id: str | None = None,
    rehearsal_segment_id: str | None = None,
    resumes_prior_segment: bool = False,
    interruption_reason: str = "planned_stop",
) -> dict[str, Any]:
    total_duration_s = round(time.monotonic() - started_monotonic_s, 3)
    measurement_duration_s = (
        round(measurement_finished_monotonic_s - measurement_started_monotonic_s, 3)
        if measurement_started_monotonic_s is not None
        and measurement_finished_monotonic_s is not None
        else 0.0
    )
    measurement_records = [
        record for record in records if record.get("phase") == "measurement"
    ]
    warmup_records = [record for record in records if record.get("phase") == "warmup"]
    sample_indices = [int(record["sample_index"]) for record in records]
    ledger_gap_free = sample_indices == list(range(1, len(records) + 1))
    prompt_mix_counts = {
        prompt_id: sum(
            1 for record in measurement_records if record.get("prompt_id") == prompt_id
        )
        for prompt_id, _prompt in B1C1_PROMPTS
    }
    warmup_mix_counts = {
        prompt_id: sum(1 for record in warmup_records if record.get("prompt_id") == prompt_id)
        for prompt_id, _prompt in B1C1_PROMPTS
    }
    warmup_cycle_complete = all(value > 0 for value in warmup_mix_counts.values())
    mix_values = list(prompt_mix_counts.values())
    session_mix_complete = bool(mix_values) and all(value > 0 for value in mix_values)
    session_mix_balanced = bool(mix_values) and max(mix_values) - min(mix_values) <= 1
    wall_clock_continuity = _b1c1_wall_clock_continuity(records)
    drift_values = [
        int(record["memory"]["drift_from_measurement_start_bytes"])
        for record in measurement_records
        if record.get("memory", {}).get("drift_from_measurement_start_bytes") is not None
    ]
    max_drift_bytes = max(drift_values) if drift_values else None
    fatal_watermark_count = sum(
        1
        for record in records
        if record.get("memory", {}).get("watermark_after_generation") == MemoryWatermark.FATAL.name
    )
    drops_total = sum(
        int(record.get("session_cache", {}).get("counter_delta", {}).get("drops", 0) or 0)
        for record in records
    )
    expirations_total = sum(
        int(
            record.get("session_cache", {})
            .get("counter_delta", {})
            .get("expirations", 0)
            or 0
        )
        for record in records
    )
    rejects_total = sum(
        int(record.get("session_cache", {}).get("counter_delta", {}).get("rejects", 0) or 0)
        for record in records
    )
    final_reclaim_stats = (
        records[-1].get("reclaim_barrier_stats_after_sample", {}) if records else {}
    )
    final_reclaim_summary = final_reclaim_stats.get("summary", {})
    failure_measurement_count = int(
        final_reclaim_summary.get("failure_measurement_count", 0) or 0
    )
    unresolved_reclaim_barrier_events = int(
        final_reclaim_summary.get("unresolved_event_count", 0) or 0
    )
    duration_requirement_met = measurement_duration_s >= required_duration_s
    claimable_24h_duration = (
        required_duration_s >= float(B1C1_DURATION_S) and duration_requirement_met
    )
    allocator_truth_claimable = (
        backend == "native" and measurement_mode == MlxMemorySampler.measurement_mode
    )
    operations_ok = bool(load.ok) and all(
        record.get("sample_verdict") == "passed" for record in records
    )
    drift_ok = max_drift_bytes is not None and max_drift_bytes <= drift_budget_bytes
    cleanup_ok = bool(cleanup_unload.ok) if cleanup_unload is not None else not bool(load.ok)
    hard_failure = (
        bool(records)
        and (
            not operations_ok
            or (max_drift_bytes is not None and not drift_ok)
            or fatal_watermark_count > 0
            or drops_total > 0
            or expirations_total > 0
            or rejects_total > 0
            or failure_measurement_count > 0
            or unresolved_reclaim_barrier_events > 0
            or not cleanup_ok
        )
    )
    ok = (
        bool(measurement_records)
        and claimable_24h_duration
        and allocator_truth_claimable
        and warmup_cycle_complete
        and ledger_gap_free
        and bool(wall_clock_continuity["measurement_wall_clock_gap_free"])
        and session_mix_complete
        and session_mix_balanced
        and operations_ok
        and drift_ok
        and fatal_watermark_count == 0
        and drops_total == 0
        and expirations_total == 0
        and rejects_total == 0
        and failure_measurement_count == 0
        and unresolved_reclaim_barrier_events == 0
        and cleanup_ok
    )
    if ok:
        conclusion = "passed"
    elif hard_failure:
        conclusion = "failed"
    else:
        conclusion = "blocked"
    segment_id = rehearsal_segment_id or run_id
    return {
        "schema_version": "b1c1.v1",
        "gate": "B-1c section 1",
        "run_id": run_id,
        "timestamp_utc": _now_iso_utc(),
        "ledger": str(output_path),
        "model": {
            "id": model_label,
            "path": model.model_id,
            "runtime_model_id": model.model_id,
            "memory_gb": model.memory_gb,
        },
        "backend": backend,
        "measurement_mode": measurement_mode,
        "total_duration_s": total_duration_s,
        "required_duration_s": required_duration_s,
        "measurement_duration_s": measurement_duration_s,
        "duration_requirement_met": duration_requirement_met,
        "samples": len(records),
        "warmup_samples": len(warmup_records),
        "measurement_samples": len(measurement_records),
        "ledger_gap_free": ledger_gap_free,
        "warmup_mix_counts": warmup_mix_counts,
        "warmup_cycle_complete": warmup_cycle_complete,
        "wall_clock_continuity": wall_clock_continuity,
        "measurement_wall_clock_gap_free": wall_clock_continuity[
            "measurement_wall_clock_gap_free"
        ],
        "prompt_mix_counts": prompt_mix_counts,
        "session_mix_complete": session_mix_complete,
        "session_mix_balanced": session_mix_balanced,
        "claimable_24h_duration": claimable_24h_duration,
        "allocator_truth_claimable": allocator_truth_claimable,
        "hard_failure": hard_failure,
        "max_drift_bytes": max_drift_bytes,
        "drift_budget_bytes": drift_budget_bytes,
        "max_drift_within_budget": drift_ok,
        "fatal_watermark_count": fatal_watermark_count,
        "session_cache_drops_total": drops_total,
        "session_cache_expirations_total": expirations_total,
        "session_cache_rejects_total": rejects_total,
        "failure_measurement_count": failure_measurement_count,
        "unresolved_reclaim_barrier_events": unresolved_reclaim_barrier_events,
        "load_result": _result_to_dict(load),
        "cleanup_unload_result": (
            _result_to_dict(cleanup_unload) if cleanup_unload is not None else None
        ),
        "cleanup_settle": (
            {
                "active_memory_bytes": cleanup_settle.active_memory_bytes,
                "active_memory_gb": _bytes_to_gb(cleanup_settle.active_memory_bytes),
                "iterations": cleanup_settle.iterations,
                "duration_ms": cleanup_settle.duration_ms,
            }
            if cleanup_settle is not None
            else None
        ),
        "interrupted_no_swap_rehearsal": {
            "rehearsal_group_id": rehearsal_group_id,
            "rehearsal_segment_id": segment_id,
            "segment_duration_s": measurement_duration_s,
            "interruption_reason": interruption_reason,
            "resumes_prior_segment": resumes_prior_segment,
            "aggregate_measurement_duration_s": measurement_duration_s,
            "no_swap_soak_stability": "blocked" if not ok else conclusion,
        },
        "no_swap_soak_stability": conclusion,
        "conclusion": conclusion,
        "graduates": {
            "no_swap_soak_stability": ok,
            "unblock_B_1c_section_2": ok,
        },
    }


def run_b1c1_no_swap_soak(
    *,
    runtime: str,
    backend: str,
    model: ModelSpec,
    model_label: str = B1B_MODEL_ID,
    output_dir: Path,
    duration_s: float = float(B1C1_DURATION_S),
    required_duration_s: float = float(B1C1_DURATION_S),
    sample_interval_s: float = B1C1_SAMPLE_INTERVAL_S,
    max_samples: int | None = None,
    warmup_cycles: int = B1C1_WARMUP_CYCLES,
    session_id_prefix: str = B1C1_SESSION_ID_PREFIX,
    max_tokens: int = 2,
    profile_memory_gb: float = 128.0,
    rehearsal_group_id: str | None = None,
    rehearsal_segment_id: str | None = None,
    resumes_prior_segment: bool = False,
    interruption_reason: str = "planned_stop",
    session_cache_ttl_s: float | None = None,
) -> dict[str, Any]:
    if runtime != "owlmlx":
        raise ValueError("only --runtime owlmlx is implemented in this baseline round")
    if duration_s < 0:
        raise ValueError("--duration-s must be >= 0")
    if required_duration_s < 0:
        raise ValueError("--required-duration-s must be >= 0")
    if sample_interval_s < 0:
        raise ValueError("--sample-interval-s must be >= 0")
    if max_samples is not None and max_samples < 1:
        raise ValueError("--max-samples must be >= 1 when provided")
    if warmup_cycles < 0:
        raise ValueError("--warmup-cycles must be >= 0")
    if interruption_reason not in B1C1_INTERRUPTION_REASONS:
        raise ValueError(
            "--interruption-reason must be one of "
            + ", ".join(sorted(B1C1_INTERRUPTION_REASONS))
        )
    if session_cache_ttl_s is not None and session_cache_ttl_s < 0:
        raise ValueError("--session-cache-ttl-s must be >= 0")

    profile = MachineMemoryProfile(
        system_memory_gb=profile_memory_gb,
        system_reserve_gb=2.0,
        serving_budget_gb=max(profile_memory_gb - 2.0, 1.0),
        warning_threshold_gb=max(profile_memory_gb - 10.0, 1.0),
    )
    drift_budget_bytes = _b1c1_max_drift_bytes(profile)
    timestamp = _now_compact_utc()
    run_id = f"{timestamp}-{runtime}-{backend}-{B1C1_GATE}"
    output_path = output_dir / _b1c1_filename(timestamp, model_id=model_label)
    rollup_path = output_dir / _b1c1_rollup_filename(timestamp, model_id=model_label)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    settle_sleep_s = 0.0
    effective_session_cache_ttl_s = (
        float(session_cache_ttl_s)
        if session_cache_ttl_s is not None
        else _b1c1_default_session_cache_ttl_s(
            duration_s=duration_s,
            required_duration_s=required_duration_s,
            sample_interval_s=sample_interval_s,
        )
    )
    stop_requested = False
    stop_reason = interruption_reason
    installed_signal_handlers: list[tuple[signal.Signals, Any]] = []

    def _request_stop(signum: int, _frame: object | None) -> None:
        nonlocal stop_requested, stop_reason
        stop_requested = True
        if signum == signal.SIGINT:
            stop_reason = "user_interrupt"
        elif signum == signal.SIGTERM:
            stop_reason = interruption_reason

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            previous = signal.getsignal(sig)
            signal.signal(sig, _request_stop)
            installed_signal_handlers.append((sig, previous))
        except (ValueError, OSError):
            # Signal handlers can only be installed from the main thread. The
            # bench is normally run as a CLI; embedded test callers still work
            # without graceful OS-signal handling.
            continue

    def _sleep_until_next_sample(sleep_for: float) -> None:
        deadline = time.monotonic() + sleep_for
        while not stop_requested:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 1.0))

    try:
        with _session_cache_env(True, ttl_s=effective_session_cache_ttl_s):
            kernel, sampler = _make_kernel(backend=backend, profile=profile)
            records: list[dict[str, Any]] = []
            started_monotonic_s = time.monotonic()
            measurement_started_monotonic_s: float | None = None
            measurement_finished_monotonic_s: float | None = None
            warmup_sample_count = warmup_cycles * len(B1C1_PROMPTS)
            load = kernel.load_model(model.model_id, memory_gb=model.memory_gb)
            first_sample_bytes: int | None = None
            first_measurement_bytes: int | None = None
            cleanup_unload: Any | None = None
            cleanup_settle: SettleResult | None = None
            try:
                with output_path.open("w", encoding="utf-8") as stream:
                    while True:
                        if stop_requested and records:
                            break
                        if max_samples is not None and len(records) >= max_samples:
                            break
                        sample_index = len(records) + 1
                        phase = (
                            "warmup"
                            if sample_index <= warmup_sample_count
                            else "measurement"
                        )
                        if (
                            phase == "measurement"
                            and measurement_started_monotonic_s is None
                        ):
                            measurement_started_monotonic_s = time.monotonic()
                        prompt_id, prompt = B1C1_PROMPTS[
                            (sample_index - 1) % len(B1C1_PROMPTS)
                        ]
                        session_id = f"{session_id_prefix}-{prompt_id}"
                        cache_before = _session_cache_status(kernel)
                        before_bytes = sampler.active_memory_bytes(kernel)
                        try:
                            generation = (
                                asyncio.run(
                                    _stream_generate_once(
                                        kernel,
                                        model_id=model.model_id,
                                        prompt=prompt,
                                        max_tokens=max_tokens,
                                        session_id=session_id,
                                    )
                                )
                                if load.ok
                                else StreamGenerationResult(
                                    ok=False,
                                    message="model load failed",
                                    error_code=RuntimeErrorCode.model_not_loaded,
                                    model_id=model.model_id,
                                )
                            )
                        except Exception as exc:  # pragma: no cover - defensive real-run capture
                            generation = StreamGenerationResult(
                                ok=False,
                                message=str(exc),
                                error_code=RuntimeErrorCode.backend_error,
                                model_id=model.model_id,
                            )
                        after_bytes = sampler.active_memory_bytes(kernel)
                        if first_sample_bytes is None and after_bytes is not None:
                            first_sample_bytes = after_bytes
                        if (
                            phase == "measurement"
                            and first_measurement_bytes is None
                            and after_bytes is not None
                        ):
                            first_measurement_bytes = after_bytes
                        drift_bytes = (
                            abs(after_bytes - first_sample_bytes)
                            if after_bytes is not None and first_sample_bytes is not None
                            else None
                        )
                        measurement_drift_bytes = (
                            abs(after_bytes - first_measurement_bytes)
                            if after_bytes is not None and first_measurement_bytes is not None
                            else None
                        )
                        cache_after = _session_cache_status(kernel)
                        counter_delta = _counter_delta(
                            dict(cache_before.get("counters", {})),
                            dict(cache_after.get("counters", {})),
                        )
                        watermark_after = _watermark(after_bytes, profile=profile)
                        reclaim_stats = _reclaim_stats(kernel)
                        settle_snapshot = _compact_settle_barrier(
                            _settle_barrier_snapshot(kernel)
                        )
                        sample_verdict = _b1c1_round_verdict(
                            load_ok=bool(load.ok),
                            generation=generation,
                            watermark=watermark_after,
                            reclaim_stats=reclaim_stats,
                            settle_barrier=settle_snapshot,
                        )
                        record = {
                            "schema_version": "b1c1.v1",
                            "gate": "B-1c section 1",
                            "run_id": run_id,
                            "mode": "no_swap_soak",
                            "phase": phase,
                            "sample_index": sample_index,
                            "timestamp_utc": _now_iso_utc(),
                            "elapsed_s": round(time.monotonic() - started_monotonic_s, 3),
                            "runtime": runtime,
                            "backend": backend,
                            "measurement_mode": sampler.measurement_mode,
                            "evidence_strength": (
                                "mlx_allocator_soak"
                                if backend == "native"
                                else "smoke_only_no_allocator_claim"
                            ),
                            "model": {
                                "id": model_label,
                                "path": model.model_id,
                                "runtime_model_id": model.model_id,
                                "memory_gb": model.memory_gb,
                            },
                            "config": {
                                "OWLMLX_SESSION_CACHE_ENABLED": "1",
                                "OWLMLX_SESSION_CACHE_TTL_S": effective_session_cache_ttl_s,
                                "session_id": session_id,
                                "temperature": 0.0,
                                "seed": 42,
                                "max_tokens": max_tokens,
                                "duration_s": duration_s,
                                "required_duration_s": required_duration_s,
                                "sample_interval_s": sample_interval_s,
                                "warmup_cycles": warmup_cycles,
                                "max_generation_concurrency": 1,
                                "artificial_unload_or_swap_during_soak": False,
                            },
                            "prompt_id": prompt_id,
                            "session_cache": {
                                "active_entries_before": cache_before.get("active_entries"),
                                "active_entries_after": cache_after.get("active_entries"),
                                "counter_delta": counter_delta,
                                "synthetic": backend == "fake",
                                "allocator_truth": backend == "native",
                            },
                            "operation": {
                                "load_ok": bool(load.ok),
                                "generation_ok": bool(generation.ok),
                                "artificial_unload_or_swap_during_soak": False,
                            },
                            "memory": {
                                "active_memory_before_sample_bytes": before_bytes,
                                "active_memory_after_generation_bytes": after_bytes,
                                "active_memory_after_generation_gb": _bytes_to_gb(after_bytes),
                                "first_sample_active_memory_bytes": first_sample_bytes,
                                "drift_from_first_sample_bytes": drift_bytes,
                                "first_measurement_active_memory_bytes": first_measurement_bytes,
                                "drift_from_measurement_start_bytes": measurement_drift_bytes,
                                "drift_budget_bytes": drift_budget_bytes,
                                "watermark_after_generation": watermark_after,
                            },
                            "settle_barrier_event": settle_snapshot,
                            "reclaim_barrier_stats_after_sample": reclaim_stats,
                            "load_result": _result_to_dict(load),
                            "generate_result": _result_to_dict(generation),
                            "sample_verdict": sample_verdict,
                        }
                        records.append(record)
                        stream.write(json.dumps(record, sort_keys=True))
                        stream.write("\n")
                        if phase == "measurement":
                            measurement_finished_monotonic_s = time.monotonic()
                        if sample_verdict != "passed" or stop_requested:
                            break
                        if max_samples is None:
                            measurement_elapsed_s = (
                                time.monotonic() - measurement_started_monotonic_s
                                if measurement_started_monotonic_s is not None
                                else 0.0
                            )
                            if (
                                phase == "measurement"
                                and measurement_elapsed_s >= duration_s
                            ):
                                break
                            sleep_for = (
                                0.0
                                if phase == "warmup"
                                else min(
                                    sample_interval_s,
                                    max(duration_s - measurement_elapsed_s, 0.0),
                                )
                            )
                            if sleep_for > 0:
                                _sleep_until_next_sample(sleep_for)
            finally:
                if load.ok:
                    cleanup_unload = kernel.unload_model(model.model_id)
                    cleanup_settle = sampler.settle(
                        kernel,
                        max_iterations=5,
                        sleep_s=settle_sleep_s,
                    )
    finally:
        for sig, previous in reversed(installed_signal_handlers):
            signal.signal(sig, previous)

    rollup = _b1c1_rollup(
        run_id=run_id,
        model=model,
        model_label=model_label,
        backend=backend,
        measurement_mode=sampler.measurement_mode,
        output_path=output_path,
        records=records,
        started_monotonic_s=started_monotonic_s,
        measurement_started_monotonic_s=measurement_started_monotonic_s,
        measurement_finished_monotonic_s=measurement_finished_monotonic_s,
        required_duration_s=required_duration_s,
        drift_budget_bytes=drift_budget_bytes,
        load=load,
        cleanup_unload=cleanup_unload,
        cleanup_settle=cleanup_settle,
        rehearsal_group_id=rehearsal_group_id,
        rehearsal_segment_id=rehearsal_segment_id,
        resumes_prior_segment=resumes_prior_segment,
        interruption_reason=stop_reason,
    )
    rollup_path.parent.mkdir(parents=True, exist_ok=True)
    with rollup_path.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(rollup, sort_keys=True))
        stream.write("\n")
    return {
        **rollup,
        "ok": rollup["conclusion"] == "passed",
        "output_dir": str(output_dir),
        "rollup_path": str(rollup_path),
    }


def _b1c1_rehearsal_segment_ok(record: dict[str, Any]) -> bool:
    return (
        record.get("schema_version") == "b1c1.v1"
        and record.get("gate") == "B-1c section 1"
        and record.get("backend") == "native"
        and record.get("measurement_mode") == MlxMemorySampler.measurement_mode
        and record.get("no_swap_soak_stability") == "blocked"
        and record.get("hard_failure") is False
        and record.get("ledger_gap_free") is True
        and record.get("measurement_wall_clock_gap_free", True) is True
        and record.get("warmup_cycle_complete") is True
        and record.get("session_mix_complete") is True
        and record.get("session_mix_balanced") is True
        and record.get("max_drift_within_budget") is True
        and int(record.get("fatal_watermark_count", 0) or 0) == 0
        and int(record.get("session_cache_drops_total", 0) or 0) == 0
        and int(record.get("session_cache_expirations_total", 0) or 0) == 0
        and int(record.get("session_cache_rejects_total", 0) or 0) == 0
        and int(record.get("failure_measurement_count", 0) or 0) == 0
        and int(record.get("unresolved_reclaim_barrier_events", 0) or 0) == 0
        and float(record.get("measurement_duration_s", 0.0) or 0.0) > 0.0
    )


def run_b1c1_interrupted_rehearsal(
    *,
    segment_rollups: list[Path],
    output_dir: Path,
    run_id: str | None = None,
    rehearsal_group_id: str | None = None,
    required_total_duration_s: float = float(B1C1_DURATION_S),
) -> dict[str, Any]:
    if not segment_rollups:
        raise ValueError("--segment-rollup is required for interrupted rehearsal")
    if required_total_duration_s < 0:
        raise ValueError("--aggregate-required-duration-s must be >= 0")

    timestamp = _now_compact_utc()
    run_id = run_id or f"{timestamp}-owlmlx-{B1C1_REHEARSAL_GATE}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / _b1c1_rehearsal_rollup_filename(timestamp)
    segments: list[dict[str, Any]] = []
    for index, path in enumerate(segment_rollups, start=1):
        record = _read_first_jsonl_record(path)
        rehearsal = record.get("interrupted_no_swap_rehearsal", {})
        segment_ok = _b1c1_rehearsal_segment_ok(record)
        segments.append(
            {
                "segment_index": index,
                "source_rollup": str(path),
                "source_run_id": record.get("run_id"),
                "rehearsal_group_id": rehearsal.get("rehearsal_group_id"),
                "rehearsal_segment_id": rehearsal.get("rehearsal_segment_id")
                or record.get("run_id")
                or Path(path).stem,
                "segment_duration_s": float(record.get("measurement_duration_s", 0.0) or 0.0),
                "interruption_reason": rehearsal.get("interruption_reason", "unknown"),
                "resumes_prior_segment": bool(rehearsal.get("resumes_prior_segment", index > 1)),
                "segment_ok_for_rehearsal": segment_ok,
                "no_swap_soak_stability": record.get("no_swap_soak_stability"),
                "hard_failure": bool(record.get("hard_failure")),
                "backend": record.get("backend"),
                "measurement_mode": record.get("measurement_mode"),
            }
        )

    aggregate_duration_s = round(
        sum(float(segment["segment_duration_s"]) for segment in segments),
        3,
    )
    duration_requirement_met = aggregate_duration_s >= required_total_duration_s
    any_failed = any(
        segment.get("no_swap_soak_stability") == "failed"
        or bool(segment.get("hard_failure"))
        for segment in segments
    )
    all_segments_ok = all(bool(segment["segment_ok_for_rehearsal"]) for segment in segments)
    if any_failed:
        rehearsal_conclusion = "failed"
    elif all_segments_ok and duration_requirement_met:
        rehearsal_conclusion = "passed"
    else:
        rehearsal_conclusion = "blocked"

    payload = {
        "schema_version": "b1c1.rehearsal.v1",
        "gate": "B-1c section 1 interrupted rehearsal",
        "run_id": run_id,
        "timestamp_utc": _now_iso_utc(),
        "rehearsal_group_id": rehearsal_group_id,
        "segment_rollups": [str(path) for path in segment_rollups],
        "segment_count": len(segments),
        "segments": segments,
        "aggregate_measurement_duration_s": aggregate_duration_s,
        "required_total_duration_s": required_total_duration_s,
        "duration_requirement_met": duration_requirement_met,
        "all_segments_ok_for_rehearsal": all_segments_ok,
        "interrupted_no_swap_rehearsal": rehearsal_conclusion,
        "no_swap_soak_stability": "blocked",
        "conclusion": rehearsal_conclusion,
        "graduates": {
            "interrupted_no_swap_rehearsal": rehearsal_conclusion == "passed",
            "no_swap_soak_stability": False,
            "unblock_B_1c_section_2": False,
        },
        "notes": [
            "Interrupted rehearsal is operational evidence only.",
            "It must not be merged into a continuous 24h no-swap soak claim.",
        ],
    }
    with output_path.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, sort_keys=True))
        stream.write("\n")
    return {
        **payload,
        "ok": rehearsal_conclusion == "passed",
        "output_dir": str(output_dir),
        "rollup_path": str(output_path),
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate",
        choices=("baseline", B1B_GATE, B1C1_GATE, B1C1_REHEARSAL_GATE),
        default="baseline",
    )
    parser.add_argument("--runtime", choices=("owlmlx", "omlx", "vmlx"), default="owlmlx")
    parser.add_argument("--backend", choices=("fake", "native"), default="fake")
    parser.add_argument("--model-a", default="model-a")
    parser.add_argument("--model-b", default="model-b")
    parser.add_argument("--model", default=B1B_MODEL_PATH)
    parser.add_argument("--model-label", default=B1B_MODEL_ID)
    parser.add_argument("--model-gb", type=float, default=1.0)
    parser.add_argument("--model-a-gb", type=float, default=1.0)
    parser.add_argument("--model-b-gb", type=float, default=1.0)
    parser.add_argument("--rounds", type=int, default=50)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--cache-mode", choices=("off", "on", "both"), default="both")
    parser.add_argument("--session-id-prefix", default=None)
    parser.add_argument("--max-drift-gb", type=float, default=0.5)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--max-tokens", type=int, default=1)
    parser.add_argument("--settle-iterations", type=int, default=5)
    parser.add_argument("--settle-sleep-ms", type=float, default=0.0)
    parser.add_argument("--profile-memory-gb", type=float, default=128.0)
    parser.add_argument("--duration-s", type=float, default=float(B1C1_DURATION_S))
    parser.add_argument("--required-duration-s", type=float, default=float(B1C1_DURATION_S))
    parser.add_argument("--sample-interval-s", type=float, default=B1C1_SAMPLE_INTERVAL_S)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--warmup-cycles", type=int, default=B1C1_WARMUP_CYCLES)
    parser.add_argument("--session-cache-ttl-s", type=float, default=None)
    parser.add_argument("--rehearsal-group-id", default=None)
    parser.add_argument("--rehearsal-segment-id", default=None)
    parser.add_argument("--resumes-prior-segment", action="store_true")
    parser.add_argument(
        "--interruption-reason",
        choices=tuple(sorted(B1C1_INTERRUPTION_REASONS)),
        default="planned_stop",
    )
    parser.add_argument("--segment-rollup", type=Path, action="append", default=[])
    parser.add_argument(
        "--aggregate-required-duration-s",
        type=float,
        default=float(B1C1_DURATION_S),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.gate == B1B_GATE:
            summary = run_b1b_cache_on_no_regress(
                runtime=args.runtime,
                backend=args.backend,
                model=ModelSpec(args.model, args.model_gb),
                model_label=args.model_label,
                rounds=args.rounds,
                output_dir=args.output or B1B_OUTPUT_DIR,
                cache_mode=args.cache_mode,
                session_id_prefix=args.session_id_prefix or B1B_SESSION_ID_PREFIX,
                prompt=args.prompt,
                max_tokens=args.max_tokens,
                settle_iterations=args.settle_iterations,
                settle_sleep_ms=args.settle_sleep_ms,
                profile_memory_gb=args.profile_memory_gb,
            )
        elif args.gate == B1C1_GATE:
            summary = run_b1c1_no_swap_soak(
                runtime=args.runtime,
                backend=args.backend,
                model=ModelSpec(args.model, args.model_gb),
                model_label=args.model_label,
                output_dir=args.output or B1C1_OUTPUT_DIR,
                duration_s=args.duration_s,
                required_duration_s=args.required_duration_s,
                sample_interval_s=args.sample_interval_s,
                max_samples=args.max_samples,
                warmup_cycles=args.warmup_cycles,
                session_id_prefix=args.session_id_prefix or B1C1_SESSION_ID_PREFIX,
                max_tokens=args.max_tokens,
                profile_memory_gb=args.profile_memory_gb,
                rehearsal_group_id=args.rehearsal_group_id,
                rehearsal_segment_id=args.rehearsal_segment_id,
                resumes_prior_segment=args.resumes_prior_segment,
                interruption_reason=args.interruption_reason,
                session_cache_ttl_s=args.session_cache_ttl_s,
            )
        elif args.gate == B1C1_REHEARSAL_GATE:
            summary = run_b1c1_interrupted_rehearsal(
                segment_rollups=args.segment_rollup,
                output_dir=args.output or B1C1_OUTPUT_DIR,
                run_id=None,
                rehearsal_group_id=args.rehearsal_group_id,
                required_total_duration_s=args.aggregate_required_duration_s,
            )
        else:
            summary = run_eviction_soak(
                runtime=args.runtime,
                backend=args.backend,
                model_a=ModelSpec(args.model_a, args.model_a_gb),
                model_b=ModelSpec(args.model_b, args.model_b_gb),
                rounds=args.rounds,
                output_dir=args.output or DEFAULT_OUTPUT_DIR,
                max_drift_gb=args.max_drift_gb,
                prompt=args.prompt,
                max_tokens=args.max_tokens,
                settle_iterations=args.settle_iterations,
                settle_sleep_ms=args.settle_sleep_ms,
                profile_memory_gb=args.profile_memory_gb,
            )
    except Exception as exc:
        print(f"eviction_soak failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
