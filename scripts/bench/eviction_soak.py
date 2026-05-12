"""Eviction soak runner for owlmlx memory-discipline baseline evidence.

The default ``fake`` backend is a smoke/control path: it proves the bench
ledger shape and RuntimeKernel load/generate/unload cleanup without claiming
allocator truth. Use ``--backend native`` for real MLX allocator evidence.
"""

from __future__ import annotations

import argparse
import asyncio
import gc
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.memory_watermark import MemoryWatermark
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.mlx_native_backend import MlxNativeBackend


BYTES_PER_GB = 1024**3
DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "files"
    / "evidence"
    / "owlmlx"
    / "bench"
    / "eviction_soak"
)
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


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=("owlmlx", "omlx", "vmlx"), default="owlmlx")
    parser.add_argument("--backend", choices=("fake", "native"), default="fake")
    parser.add_argument("--model-a", default="model-a")
    parser.add_argument("--model-b", default="model-b")
    parser.add_argument("--model-a-gb", type=float, default=1.0)
    parser.add_argument("--model-b-gb", type=float, default=1.0)
    parser.add_argument("--rounds", type=int, default=50)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
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
        summary = run_eviction_soak(
            runtime=args.runtime,
            backend=args.backend,
            model_a=ModelSpec(args.model_a, args.model_a_gb),
            model_b=ModelSpec(args.model_b, args.model_b_gb),
            rounds=args.rounds,
            output_dir=args.output,
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
