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
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Protocol

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.memory_watermark import MemoryWatermark
from owlmlx.runtime import FakeBackend, RuntimeKernel
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
B1B_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "files"
    / "evidence"
    / "owlmlx"
    / "bench"
    / "cache-settle-no-regress"
)
B1B_MODEL_ID = "gemma-4-31B-it"
B1B_MODEL_PATH = "/Users/yeemio/AI/Agent/models/gemma-4-31B-it"
DEFAULT_PROMPT = "Reply with exactly: owlmlx eviction soak"


@dataclass(frozen=True, slots=True)
class ModelSpec:
    model_id: str
    memory_gb: float


@dataclass(frozen=True, slots=True)
class SettleResult:
    active_memory_bytes: int | None
    iterations: int
    duration_ms: float


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


def _make_kernel(*, backend: str, profile: MachineMemoryProfile) -> tuple[RuntimeKernel, MemorySampler]:
    if backend == "fake":
        return RuntimeKernel(FakeBackend(default_memory_gb=1.0), profile=profile), InventoryMemorySampler()
    if backend == "native":
        return RuntimeKernel(MlxNativeBackend(), profile=profile), MlxMemorySampler.create()
    raise ValueError(f"unsupported backend: {backend}")


@contextlib.contextmanager
def _session_cache_env(enabled: bool) -> Iterator[None]:
    previous = os.environ.get("OWLMLX_SESSION_CACHE_ENABLED")
    os.environ["OWLMLX_SESSION_CACHE_ENABLED"] = "1" if enabled else "0"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("OWLMLX_SESSION_CACHE_ENABLED", None)
        else:
            os.environ["OWLMLX_SESSION_CACHE_ENABLED"] = previous


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
    safe_model = model_id.replace("/", "-")
    return f"{timestamp}-b1b-{safe_model}-{cache_part}-n{rounds}.jsonl"


def _rollup_filename(timestamp: str, *, model_id: str) -> str:
    safe_model = model_id.replace("/", "-")
    return f"{timestamp}-b1b-{safe_model}-cache-on-no-regress-rollup.jsonl"


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
                        kernel.generate(
                            prompt,
                            model_id=model.model_id,
                            max_tokens=max_tokens,
                            session_id=session_id,
                            temperature=0.0,
                            seed=42,
                        )
                    )
                    generations.append(cold)
                    cache_after_cold = _session_cache_status(kernel)
                    if cache_enabled:
                        warm = asyncio.run(
                            kernel.generate(
                                prompt,
                                model_id=model.model_id,
                                max_tokens=max_tokens,
                                session_id=session_id,
                                temperature=0.0,
                                seed=42,
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
                        "id": B1B_MODEL_ID,
                        "path": B1B_MODEL_PATH if model.model_id == B1B_MODEL_ID else model.model_id,
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
    rounds: int,
    output_dir: Path,
    cache_mode: str = "both",
    session_id_prefix: str = "b1b-gemma4-31b",
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
        path = output_dir / _mode_filename(timestamp, model_id=model.model_id, mode=mode, rounds=rounds)
        records = _run_b1b_mode(
            runtime=runtime,
            backend=backend,
            model=model,
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
    rollup_path = output_dir / _rollup_filename(timestamp, model_id=model.model_id)
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


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", choices=("baseline", B1B_GATE), default="baseline")
    parser.add_argument("--runtime", choices=("owlmlx", "omlx", "vmlx"), default="owlmlx")
    parser.add_argument("--backend", choices=("fake", "native"), default="fake")
    parser.add_argument("--model-a", default="model-a")
    parser.add_argument("--model-b", default="model-b")
    parser.add_argument("--model", default=B1B_MODEL_ID)
    parser.add_argument("--model-gb", type=float, default=1.0)
    parser.add_argument("--model-a-gb", type=float, default=1.0)
    parser.add_argument("--model-b-gb", type=float, default=1.0)
    parser.add_argument("--rounds", type=int, default=50)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--cache-mode", choices=("off", "on", "both"), default="both")
    parser.add_argument("--session-id-prefix", default="b1b-gemma4-31b")
    parser.add_argument("--max-drift-gb", type=float, default=0.5)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--max-tokens", type=int, default=1)
    parser.add_argument("--settle-iterations", type=int, default=5)
    parser.add_argument("--settle-sleep-ms", type=float, default=0.0)
    parser.add_argument("--profile-memory-gb", type=float, default=128.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.gate == B1B_GATE:
            summary = run_b1b_cache_on_no_regress(
                runtime=args.runtime,
                backend=args.backend,
                model=ModelSpec(args.model, args.model_gb),
                rounds=args.rounds,
                output_dir=args.output or B1B_OUTPUT_DIR,
                cache_mode=args.cache_mode,
                session_id_prefix=args.session_id_prefix,
                prompt=args.prompt,
                max_tokens=args.max_tokens,
                settle_iterations=args.settle_iterations,
                settle_sleep_ms=args.settle_sleep_ms,
                profile_memory_gb=args.profile_memory_gb,
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
