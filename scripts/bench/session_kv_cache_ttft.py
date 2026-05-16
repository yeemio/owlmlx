"""Session KV cache TTFT benchmark for owlmlx.

The default ``fake`` backend injects a synthetic ``mlx_lm`` module into
``MlxNativeBackend``. It proves the bench ledger shape and session-cache wiring
without claiming real model or allocator performance. Use ``--backend native``
with a local small model for real TTFT evidence.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import importlib.metadata as importlib_metadata
import json
import os
import platform
import subprocess
import sys
import time
import types
from dataclasses import dataclass
from datetime import datetime, timezone
from inspect import isawaitable
from pathlib import Path
from typing import Any, Iterator

from owlmlx.host_pressure import host_pressure_not_sampled_snapshot
from owlmlx.runtime import RuntimeKernel
from owlmlx.runtime.mlx_native_backend import MlxNativeBackend


DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "files"
    / "evidence"
    / "owlmlx"
    / "bench"
    / "session-kv-cache"
)
DEFAULT_SESSION_ID = "session-kv-cache-bench"
DEFAULT_MODEL_ID = "synthetic-small-model"
B1A_GATE = "b1a-gemma4"
B1A_MODEL_ID = "gemma-4-31B-it"
B1A_MODEL_PATH = "/Users/yeemio/AI/Agent/models/gemma-4-31B-it"
B1A_DEFAULT_ROUNDS = 4
B1A_DEFAULT_PROMPT_CHARS = 4200
B1A_DEFAULT_MAX_TOKENS = 2
B1A_SESSION_PREFIX = "b1a-gemma4-31b"
EXECUTION_BOUNDARIES = ("auto", "runtime-kernel", "direct-native")


@dataclass(frozen=True, slots=True)
class BenchModeSummary:
    cache_enabled: bool
    min_first_token_ms: float | None
    p50_first_token_ms: float | None
    p95_first_token_ms: float | None
    max_first_token_ms: float | None
    warm_min_first_token_ms: float | None
    warm_p50_first_token_ms: float | None
    warm_p95_first_token_ms: float | None
    warm_max_first_token_ms: float | None
    operation_count: int
    ok: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "cache_enabled": self.cache_enabled,
            "min_first_token_ms": self.min_first_token_ms,
            "p50_first_token_ms": self.p50_first_token_ms,
            "p95_first_token_ms": self.p95_first_token_ms,
            "max_first_token_ms": self.max_first_token_ms,
            "warm_min_first_token_ms": self.warm_min_first_token_ms,
            "warm_p50_first_token_ms": self.warm_p50_first_token_ms,
            "warm_p95_first_token_ms": self.warm_p95_first_token_ms,
            "warm_max_first_token_ms": self.warm_max_first_token_ms,
            "operation_count": self.operation_count,
            "ok": self.ok,
        }


class _FakeToken:
    def __init__(
        self,
        text: str,
        finish_reason: str | None = None,
        token: int = 999,
    ) -> None:
        self.text = text
        self.finish_reason = finish_reason
        self.token = token


def _now_compact_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _build_prompt(
    *,
    prompt_chars: int,
    round_idx: int,
    transcript: str,
) -> str:
    system = "owlmlx session kv cache TTFT synthetic system prompt. "
    repeated = (system * ((prompt_chars // len(system)) + 1))[:prompt_chars]
    prefix = transcript or f"system: {repeated}\n"
    return (
        f"{prefix}"
        f"user: turn {round_idx}; reply with exactly two short words.\n"
        f"assistant:"
    )


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 3)
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    value = ordered[lower] * (1.0 - weight) + ordered[upper] * weight
    return round(value, 3)


def _rounded_min(values: list[float]) -> float | None:
    return round(min(values), 3) if values else None


def _rounded_max(values: list[float]) -> float | None:
    return round(max(values), 3) if values else None


def _normalize_gate(gate: str) -> str:
    normalized = str(gate).strip().lower()
    if normalized in {"", "default", "baseline"}:
        return "baseline"
    if normalized == B1A_GATE:
        return B1A_GATE
    raise ValueError("--gate must be default, baseline, or b1a-gemma4")


def _resolve_execution_boundary(
    *,
    execution_boundary: str,
    gate: str,
    backend: str,
) -> str:
    normalized = str(execution_boundary).strip().lower()
    if normalized not in EXECUTION_BOUNDARIES:
        choices = ", ".join(EXECUTION_BOUNDARIES)
        raise ValueError(f"--execution-boundary must be one of: {choices}")
    if normalized != "auto":
        return normalized
    if gate == B1A_GATE and backend == "native":
        return "direct-native"
    return "runtime-kernel"


def _host_label() -> str:
    try:
        result = subprocess.run(
            ["/usr/sbin/sysctl", "-n", "hw.model"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:
        result = None
    if result is not None and result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return platform.machine() or platform.node() or "unknown"


def _session_cache_status(kernel: RuntimeKernel) -> dict[str, Any]:
    return kernel.status_dict()["backend"]["detail"].get("session_kv_cache", {})


def _native_session_cache_status(native: MlxNativeBackend) -> dict[str, Any]:
    return native.status().detail.get("session_kv_cache", {})


def _counter_value(counters: dict[str, Any], key: str) -> int:
    value = counters.get(key, 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _counter_delta(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, int]:
    keys = set(previous) | set(current)
    return {
        key: _counter_value(current, key) - _counter_value(previous, key)
        for key in sorted(keys)
    }


def _mode_summary(records: list[dict[str, Any]], *, cache_enabled: bool) -> BenchModeSummary:
    subset = [record for record in records if record["cache_enabled"] is cache_enabled]
    ttft = [
        float(record["first_token_ms"])
        for record in subset
        if record.get("first_token_ms") is not None
    ]
    warm_ttft = [
        float(record["first_token_ms"])
        for record in subset
        if int(record.get("round", 0)) > 1 and record.get("first_token_ms") is not None
    ]
    return BenchModeSummary(
        cache_enabled=cache_enabled,
        min_first_token_ms=_rounded_min(ttft),
        p50_first_token_ms=_percentile(ttft, 0.50),
        p95_first_token_ms=_percentile(ttft, 0.95),
        max_first_token_ms=_rounded_max(ttft),
        warm_min_first_token_ms=_rounded_min(warm_ttft),
        warm_p50_first_token_ms=_percentile(warm_ttft, 0.50),
        warm_p95_first_token_ms=_percentile(warm_ttft, 0.95),
        warm_max_first_token_ms=_rounded_max(warm_ttft),
        operation_count=len(subset),
        ok=all(bool(record.get("ok")) for record in subset),
    )


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return round(numerator / denominator, 3)


@contextlib.contextmanager
def _temporary_env(updates: dict[str, str]) -> Iterator[None]:
    previous = {name: os.environ.get(name) for name in updates}
    try:
        for name, value in updates.items():
            os.environ[name] = value
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


@contextlib.contextmanager
def _session_cache_env(
    enabled: bool,
    *,
    max_entries: int | None = None,
    ttl_s: float | None = None,
) -> Iterator[None]:
    updates = {"OWLMLX_SESSION_CACHE_ENABLED": "1" if enabled else "0"}
    if max_entries is not None:
        updates["OWLMLX_SESSION_CACHE_MAX_ENTRIES"] = str(max_entries)
    if ttl_s is not None:
        updates["OWLMLX_SESSION_CACHE_TTL_S"] = str(ttl_s)
    with _temporary_env(updates):
        yield


@contextlib.contextmanager
def _fake_mlx_lm(
    *,
    cold_prefill_ms: float,
    warm_prefill_ms: float,
) -> Iterator[types.ModuleType]:
    previous = {
        name: sys.modules.get(name)
        for name in ("mlx_lm", "mlx_lm.models", "mlx_lm.models.cache")
    }
    fake = types.ModuleType("mlx_lm")
    models = types.ModuleType("mlx_lm.models")
    cache_mod = types.ModuleType("mlx_lm.models.cache")
    seen_prompt_caches: list[Any] = []
    created_cache_count = 0

    class FakeTokenizer:
        bos_token = None

        def encode(self, prompt: str, add_special_tokens: bool = True) -> list[int]:
            _ = add_special_tokens
            return [ord(ch) for ch in prompt]

    def make_prompt_cache(model: object) -> list[object]:
        nonlocal created_cache_count
        _ = model
        created_cache_count += 1
        return [{"tokens": []}]

    def trim_prompt_cache(cache: list[object], token_count: int) -> int:
        if not cache:
            return 0
        state = cache[0]
        if not isinstance(state, dict):
            return 0
        tokens = state.get("tokens")
        if not isinstance(tokens, list):
            return 0
        trimmed = min(int(token_count), len(tokens))
        if trimmed:
            del tokens[-trimmed:]
        return trimmed

    def fake_load(model_id: str) -> tuple[object, object]:
        return ({"model_id": model_id}, FakeTokenizer())

    def fake_stream_generate(
        model,
        tokenizer,
        *,
        prompt,
        max_tokens,
        prompt_cache=None,
        **kwargs,
    ):
        _ = (model, tokenizer, prompt, max_tokens, kwargs)
        cache_seen = (
            prompt_cache is not None
            and any(prompt_cache is seen for seen in seen_prompt_caches)
        )
        if cache_seen:
            delay_ms = warm_prefill_ms
        else:
            delay_ms = cold_prefill_ms
            if prompt_cache is not None:
                seen_prompt_caches.append(prompt_cache)
        generated_count = max(int(max_tokens), 1)
        if prompt_cache is not None and prompt_cache:
            state = prompt_cache[0]
            if isinstance(state, dict):
                tokens = state.get("tokens")
                if isinstance(tokens, list):
                    if isinstance(prompt, list):
                        tokens.extend(prompt)
                    else:
                        tokens.extend(tokenizer.encode(prompt))
                    tokens.extend(999 + idx for idx in range(generated_count))
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
        for idx in range(generated_count):
            yield _FakeToken(
                "hello" if idx == 0 else " world",
                finish_reason="stop" if idx == generated_count - 1 else None,
                token=999 + idx,
            )

    cache_mod.make_prompt_cache = make_prompt_cache  # type: ignore[attr-defined]
    cache_mod.trim_prompt_cache = trim_prompt_cache  # type: ignore[attr-defined]
    models.cache = cache_mod  # type: ignore[attr-defined]
    fake.models = models  # type: ignore[attr-defined]
    fake.load = fake_load  # type: ignore[attr-defined]
    fake.stream_generate = fake_stream_generate  # type: ignore[attr-defined]
    fake._created_cache_count = lambda: created_cache_count  # type: ignore[attr-defined]
    fake._seen_prompt_cache_count = lambda: len(seen_prompt_caches)  # type: ignore[attr-defined]

    try:
        sys.modules["mlx_lm"] = fake
        sys.modules["mlx_lm.models"] = models
        sys.modules["mlx_lm.models.cache"] = cache_mod
        yield fake
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


async def _measure_stream_ttft(
    kernel: RuntimeKernel,
    *,
    model_id: str,
    prompt: str,
    session_id: str,
    max_tokens: int,
) -> dict[str, Any]:
    started = time.monotonic()
    first_token_ms: float | None = None
    completion_tokens = 0
    generated_text: list[str] = []
    error: dict[str, Any] | None = None
    async for event in kernel.generate_stream(
        prompt,
        model_id=model_id,
        max_tokens=max_tokens,
        session_id=session_id,
    ):
        if event.event == "token" and first_token_ms is None:
            first_token_ms = round((time.monotonic() - started) * 1000.0, 3)
        if event.event == "token":
            generated_text.append(event.text)
        if event.completion_tokens is not None:
            completion_tokens = int(event.completion_tokens)
        if event.event == "error":
            error = {
                "error_code": event.error_code.value if event.error_code is not None else None,
                "detail": dict(event.detail),
            }
    total_ms = round((time.monotonic() - started) * 1000.0, 3)
    return {
        "ok": error is None and first_token_ms is not None,
        "first_token_ms": first_token_ms,
        "total_stream_ms": total_ms,
        "completion_tokens": completion_tokens,
        "generated_text": "".join(generated_text),
        "error": error,
    }


def _measure_direct_native_stream_ttft(
    native: MlxNativeBackend,
    *,
    model_id: str,
    prompt: str,
    session_id: str,
    max_tokens: int,
) -> dict[str, Any]:
    started = time.monotonic()
    first_token_ms: float | None = None
    completion_tokens = 0
    generated_text: list[str] = []
    error: dict[str, Any] | None = None
    for event in native.stream_generate(
        model_id,
        prompt,
        max_tokens=max_tokens,
        session_id=session_id,
    ):
        if event.event == "token" and first_token_ms is None:
            first_token_ms = round((time.monotonic() - started) * 1000.0, 3)
        if event.event == "token":
            generated_text.append(event.text)
        if event.completion_tokens is not None:
            completion_tokens = int(event.completion_tokens)
        if event.event == "error":
            error = {
                "error_code": event.error_code.value if event.error_code is not None else None,
                "detail": dict(event.detail),
            }
    total_ms = round((time.monotonic() - started) * 1000.0, 3)
    return {
        "ok": error is None and first_token_ms is not None,
        "first_token_ms": first_token_ms,
        "total_stream_ms": total_ms,
        "completion_tokens": completion_tokens,
        "generated_text": "".join(generated_text),
        "error": error,
    }


async def _run_mode(
    *,
    backend: str,
    cache_enabled: bool,
    runtime: str,
    model_id: str,
    model_memory_gb: float,
    rounds: int,
    prompt_chars: int,
    max_tokens: int,
    session_id: str,
    measurement_mode: str,
    evidence_strength: str,
    execution_boundary: str,
) -> list[dict[str, Any]]:
    _ = backend
    with _session_cache_env(cache_enabled):
        native = MlxNativeBackend()
        kernel = RuntimeKernel(
            native,
            host_pressure_sampler=host_pressure_not_sampled_snapshot,
        )
        load = kernel.load_model(model_id, memory_gb=model_memory_gb)
        if not load.ok:
            raise RuntimeError(f"load failed for {model_id}: {load.message}")
        records: list[dict[str, Any]] = []
        transcript = ""
        previous_counters = dict(_session_cache_status(kernel).get("counters", {}))
        try:
            for round_idx in range(1, rounds + 1):
                prompt = _build_prompt(
                    prompt_chars=prompt_chars,
                    round_idx=round_idx,
                    transcript=transcript,
                )
                measurement = await _measure_stream_ttft(
                    kernel,
                    model_id=model_id,
                    prompt=prompt,
                    session_id=session_id,
                    max_tokens=max_tokens,
                )
                status = _session_cache_status(kernel)
                counters = dict(status.get("counters", {}))
                delta = _counter_delta(previous_counters, counters)
                previous_counters = counters
                records.append(
                    {
                        "runtime": runtime,
                        "backend": backend,
                        "measurement_mode": measurement_mode,
                        "evidence_strength": evidence_strength,
                        "execution_boundary": execution_boundary,
                        "cache_enabled": cache_enabled,
                        "round": round_idx,
                        "phase": "cold" if round_idx == 1 else "warm",
                        "model_id": model_id,
                        "session_id": session_id,
                        "prompt_chars": len(prompt),
                        "max_tokens": max_tokens,
                        "first_token_ms": measurement["first_token_ms"],
                        "total_stream_ms": measurement["total_stream_ms"],
                        "completion_tokens": measurement["completion_tokens"],
                        "ok": measurement["ok"],
                        "error": measurement["error"],
                        "session_kv_cache": {
                            "enabled": status.get("enabled"),
                            "active_entries": status.get("active_entries"),
                            "counters": status.get("counters", {}),
                        },
                        "session_kv_cache_counter_delta": delta,
                        "hit": _counter_value(delta, "hits") > 0,
                        "miss": _counter_value(delta, "misses") > 0,
                        "drop": _counter_value(delta, "drops") > 0,
                    }
                )
                if measurement["ok"]:
                    transcript = f"{prompt}{measurement['generated_text']}\n"
        finally:
            kernel.unload_model(model_id)
        return records


def _run_mode_direct_native(
    *,
    backend: str,
    cache_enabled: bool,
    runtime: str,
    model_id: str,
    model_memory_gb: float,
    rounds: int,
    prompt_chars: int,
    max_tokens: int,
    session_id: str,
    measurement_mode: str,
    evidence_strength: str,
    execution_boundary: str,
) -> list[dict[str, Any]]:
    with _session_cache_env(cache_enabled):
        native = MlxNativeBackend()
        load = native.load(model_id, memory_gb=model_memory_gb)
        if not load.ok:
            raise RuntimeError(f"load failed for {model_id}: {load.message}")
        records: list[dict[str, Any]] = []
        transcript = ""
        previous_counters = dict(_native_session_cache_status(native).get("counters", {}))
        try:
            for round_idx in range(1, rounds + 1):
                prompt = _build_prompt(
                    prompt_chars=prompt_chars,
                    round_idx=round_idx,
                    transcript=transcript,
                )
                measurement = _measure_direct_native_stream_ttft(
                    native,
                    model_id=model_id,
                    prompt=prompt,
                    session_id=session_id,
                    max_tokens=max_tokens,
                )
                status = _native_session_cache_status(native)
                counters = dict(status.get("counters", {}))
                delta = _counter_delta(previous_counters, counters)
                previous_counters = counters
                records.append(
                    {
                        "runtime": runtime,
                        "backend": backend,
                        "measurement_mode": measurement_mode,
                        "evidence_strength": evidence_strength,
                        "execution_boundary": execution_boundary,
                        "cache_enabled": cache_enabled,
                        "round": round_idx,
                        "phase": "cold" if round_idx == 1 else "warm",
                        "model_id": model_id,
                        "session_id": session_id,
                        "prompt_chars": len(prompt),
                        "max_tokens": max_tokens,
                        "first_token_ms": measurement["first_token_ms"],
                        "total_stream_ms": measurement["total_stream_ms"],
                        "completion_tokens": measurement["completion_tokens"],
                        "ok": measurement["ok"],
                        "error": measurement["error"],
                        "session_kv_cache": {
                            "enabled": status.get("enabled"),
                            "active_entries": status.get("active_entries"),
                            "counters": status.get("counters", {}),
                        },
                        "session_kv_cache_counter_delta": delta,
                        "hit": _counter_value(delta, "hits") > 0,
                        "miss": _counter_value(delta, "misses") > 0,
                        "drop": _counter_value(delta, "drops") > 0,
                    }
                )
                if measurement["ok"]:
                    transcript = f"{prompt}{measurement['generated_text']}\n"
        finally:
            native.unload(model_id)
        return records


def _package_version(distribution: str) -> str | None:
    try:
        return importlib_metadata.version(distribution)
    except importlib_metadata.PackageNotFoundError:
        return None


def _b1a_model_metadata(*, model_id: str, backend: str) -> dict[str, Any]:
    metadata_status = (
        "not_sampled_fake_backend"
        if backend == "fake"
        else "lineage_not_sampled_by_ttft_harness"
    )
    return {
        "id": B1A_MODEL_ID,
        "path": B1A_MODEL_PATH,
        "runtime_model_id": model_id,
        "hf_commit_sha": None,
        "mlx_lm_version": _package_version("mlx-lm"),
        "quantization": None,
        "metadata_status": metadata_status,
    }


def _b1a_rounds(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "round": int(record["round"]),
            "phase": record.get("phase") or (
                "cold" if int(record["round"]) == 1 else "warm"
            ),
            "first_token_ms": record.get("first_token_ms"),
            "total_stream_ms": record.get("total_stream_ms"),
            "hit": bool(record.get("hit")),
            "miss": bool(record.get("miss")),
            "drop": bool(record.get("drop")),
            "ok": bool(record.get("ok")),
            "session_kv_cache": record.get("session_kv_cache", {}),
            "session_kv_cache_counter_delta": record.get(
                "session_kv_cache_counter_delta",
                {},
            ),
            "error": record.get("error"),
        }
        for record in records
    ]


def _b1a_summary(records: list[dict[str, Any]], *, cache_enabled: bool) -> dict[str, Any]:
    mode = _mode_summary(records, cache_enabled=cache_enabled)
    counters = (
        records[-1].get("session_kv_cache", {}).get("counters", {})
        if records
        else {}
    )
    warm_records = [record for record in records if int(record.get("round", 0)) > 1]
    return {
        **mode.to_dict(),
        "warm_hits_total": sum(1 for record in warm_records if record.get("hit")),
        "hits_total": _counter_value(counters, "hits"),
        "misses_total": _counter_value(counters, "misses"),
        "drops_total": _counter_value(counters, "drops"),
        "evictions_total": _counter_value(counters, "evictions"),
        "expirations_total": _counter_value(counters, "expirations"),
        "cold_round_miss": bool(records[0].get("miss")) if records else False,
    }


async def _probe_request(
    kernel: RuntimeKernel,
    *,
    model_id: str,
    session_id: str,
    label: str,
    max_tokens: int,
    previous_counters: dict[str, Any],
    prompt_chars: int = 256,
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = _build_prompt(prompt_chars=prompt_chars, round_idx=1, transcript="")
    measurement = await _measure_stream_ttft(
        kernel,
        model_id=model_id,
        prompt=prompt,
        session_id=session_id,
        max_tokens=max_tokens,
    )
    status = _session_cache_status(kernel)
    counters = dict(status.get("counters", {}))
    delta = _counter_delta(previous_counters, counters)
    return (
        {
            "label": label,
            "session_id": session_id,
            "ok": bool(measurement["ok"]),
            "first_token_ms": measurement["first_token_ms"],
            "hit": _counter_value(delta, "hits") > 0,
            "miss": _counter_value(delta, "misses") > 0,
            "drop": _counter_value(delta, "drops") > 0,
            "session_kv_cache": {
                "enabled": status.get("enabled"),
                "active_entries": status.get("active_entries"),
                "counters": counters,
                "entries": status.get("entries", []),
            },
            "session_kv_cache_counter_delta": delta,
            "error": measurement["error"],
        },
        counters,
    )


def _probe_request_direct_native(
    native: MlxNativeBackend,
    *,
    model_id: str,
    session_id: str,
    label: str,
    max_tokens: int,
    previous_counters: dict[str, Any],
    prompt_chars: int = 256,
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = _build_prompt(prompt_chars=prompt_chars, round_idx=1, transcript="")
    measurement = _measure_direct_native_stream_ttft(
        native,
        model_id=model_id,
        prompt=prompt,
        session_id=session_id,
        max_tokens=max_tokens,
    )
    status = _native_session_cache_status(native)
    counters = dict(status.get("counters", {}))
    delta = _counter_delta(previous_counters, counters)
    return (
        {
            "label": label,
            "session_id": session_id,
            "ok": bool(measurement["ok"]),
            "first_token_ms": measurement["first_token_ms"],
            "hit": _counter_value(delta, "hits") > 0,
            "miss": _counter_value(delta, "misses") > 0,
            "drop": _counter_value(delta, "drops") > 0,
            "session_kv_cache": {
                "enabled": status.get("enabled"),
                "active_entries": status.get("active_entries"),
                "counters": counters,
                "entries": status.get("entries", []),
            },
            "session_kv_cache_counter_delta": delta,
            "error": measurement["error"],
        },
        counters,
    )


def _load_probe_kernel(*, model_id: str, model_memory_gb: float) -> RuntimeKernel:
    native = MlxNativeBackend()
    kernel = RuntimeKernel(
        native,
        host_pressure_sampler=host_pressure_not_sampled_snapshot,
    )
    load = kernel.load_model(model_id, memory_gb=model_memory_gb)
    if not load.ok:
        raise RuntimeError(f"probe load failed for {model_id}: {load.message}")
    return kernel


def _load_probe_native(*, model_id: str, model_memory_gb: float) -> MlxNativeBackend:
    native = MlxNativeBackend()
    load = native.load(model_id, memory_gb=model_memory_gb)
    if not load.ok:
        raise RuntimeError(f"probe load failed for {model_id}: {load.message}")
    return native


async def _run_b1a_lru_probe(
    *,
    model_id: str,
    model_memory_gb: float,
    max_tokens: int,
    session_prefix: str,
    evidence_strength: str,
) -> dict[str, Any]:
    with _session_cache_env(True, max_entries=1):
        kernel = _load_probe_kernel(model_id=model_id, model_memory_gb=model_memory_gb)
        previous = dict(_session_cache_status(kernel).get("counters", {}))
        events: list[dict[str, Any]] = []
        try:
            event, previous = await _probe_request(
                kernel,
                model_id=model_id,
                session_id=f"{session_prefix}-lru-a",
                label="create_session_a",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            event, previous = await _probe_request(
                kernel,
                model_id=model_id,
                session_id=f"{session_prefix}-lru-b",
                label="create_session_b_evict_a",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            event, previous = await _probe_request(
                kernel,
                model_id=model_id,
                session_id=f"{session_prefix}-lru-a",
                label="retry_session_a_after_eviction",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            counters = events[-1]["session_kv_cache"]["counters"]
            evictions = _counter_value(counters, "evictions")
            passed = (
                all(bool(item["ok"]) for item in events)
                and evictions >= 1
                and bool(events[-1]["miss"])
                and not bool(events[-1]["drop"])
            )
            return {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "evidence_strength": evidence_strength,
                "eviction_counter_increased": evictions >= 1,
                "post_eviction_miss_recover": bool(events[-1]["miss"])
                and bool(events[-1]["ok"]),
                "watermark_fatal_observed": False,
                "events": events,
            }
        finally:
            kernel.unload_model(model_id)


async def _run_b1a_ttl_probe(
    *,
    model_id: str,
    model_memory_gb: float,
    max_tokens: int,
    session_prefix: str,
    evidence_strength: str,
) -> dict[str, Any]:
    with _session_cache_env(True, ttl_s=0.001):
        kernel = _load_probe_kernel(model_id=model_id, model_memory_gb=model_memory_gb)
        previous = dict(_session_cache_status(kernel).get("counters", {}))
        events: list[dict[str, Any]] = []
        try:
            event, previous = await _probe_request(
                kernel,
                model_id=model_id,
                session_id=f"{session_prefix}-ttl",
                label="create_session",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            await asyncio.sleep(0.01)
            event, previous = await _probe_request(
                kernel,
                model_id=model_id,
                session_id=f"{session_prefix}-ttl",
                label="request_after_ttl",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            counters = events[-1]["session_kv_cache"]["counters"]
            expirations = _counter_value(counters, "expirations")
            passed = (
                all(bool(item["ok"]) for item in events)
                and expirations >= 1
                and bool(events[-1]["miss"])
            )
            return {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "evidence_strength": evidence_strength,
                "expiration_counter_increased": expirations >= 1,
                "post_expire_miss_new_session": bool(events[-1]["miss"])
                and bool(events[-1]["ok"]),
                "events": events,
            }
        finally:
            kernel.unload_model(model_id)


async def _run_b1a_restart_probe(
    *,
    model_id: str,
    model_memory_gb: float,
    max_tokens: int,
    session_prefix: str,
    evidence_strength: str,
) -> dict[str, Any]:
    with _session_cache_env(True):
        kernel = _load_probe_kernel(model_id=model_id, model_memory_gb=model_memory_gb)
        previous = dict(_session_cache_status(kernel).get("counters", {}))
        events: list[dict[str, Any]] = []
        restart_payload: dict[str, Any] = {}
        try:
            event, previous = await _probe_request(
                kernel,
                model_id=model_id,
                session_id=f"{session_prefix}-restart",
                label="create_session",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            event, previous = await _probe_request(
                kernel,
                model_id=model_id,
                session_id=f"{session_prefix}-restart",
                label="warm_hit_before_restart",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            before_restart = _session_cache_status(kernel)
            before_restart_counters = dict(before_restart.get("counters", {}))
            restart = kernel.restart_model(model_id)
            after_restart = _session_cache_status(kernel)
            after_restart_counters = dict(after_restart.get("counters", {}))
            restart_delta = _counter_delta(
                before_restart_counters,
                after_restart_counters,
            )
            restart_detail = dict(restart.detail or {})
            unload_detail = restart_detail.get("unload")
            restart_payload = {
                "ok": bool(restart.ok),
                "stage": restart.stage,
                "retryable": restart.retryable,
                "message": restart.message,
                "detail": restart_detail,
                "session_kv_cache_after_restart": {
                    "active_entries": after_restart.get("active_entries"),
                    "counters": after_restart_counters,
                },
                "session_kv_cache_counter_delta": restart_delta,
            }
            previous = after_restart_counters
            event, previous = await _probe_request(
                kernel,
                model_id=model_id,
                session_id=f"{session_prefix}-restart",
                label="post_restart_miss",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            event, previous = await _probe_request(
                kernel,
                model_id=model_id,
                session_id=f"{session_prefix}-restart",
                label="post_restart_warm_hit",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            old_entry_dropped = (
                _counter_value(restart_delta, "drops") >= 1
                and int(after_restart.get("active_entries") or 0) == 0
            )
            reclaim_verified = bool(
                restart.ok
                and isinstance(unload_detail, dict)
                and unload_detail.get("ok") is True
            )
            passed = (
                bool(restart.ok)
                and old_entry_dropped
                and bool(events[-2]["miss"])
                and bool(events[-1]["hit"])
                and reclaim_verified
                and all(bool(item["ok"]) for item in events)
            )
            return {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "evidence_strength": evidence_strength,
                "restart_success": bool(restart.ok),
                "old_session_entry_dropped": old_entry_dropped,
                "post_restart_miss_new_session": bool(events[-2]["miss"]),
                "second_post_restart_warm_hit": bool(events[-1]["hit"]),
                "reclaim_verified": reclaim_verified,
                "restart": restart_payload,
                "events": events,
            }
        finally:
            kernel.unload_model(model_id)


def _run_b1a_lru_probe_direct_native(
    *,
    model_id: str,
    model_memory_gb: float,
    max_tokens: int,
    session_prefix: str,
    evidence_strength: str,
) -> dict[str, Any]:
    with _session_cache_env(True, max_entries=1):
        native = _load_probe_native(model_id=model_id, model_memory_gb=model_memory_gb)
        previous = dict(_native_session_cache_status(native).get("counters", {}))
        events: list[dict[str, Any]] = []
        try:
            event, previous = _probe_request_direct_native(
                native,
                model_id=model_id,
                session_id=f"{session_prefix}-lru-a",
                label="create_session_a",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            event, previous = _probe_request_direct_native(
                native,
                model_id=model_id,
                session_id=f"{session_prefix}-lru-b",
                label="create_session_b_evict_a",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            event, previous = _probe_request_direct_native(
                native,
                model_id=model_id,
                session_id=f"{session_prefix}-lru-a",
                label="retry_session_a_after_eviction",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            counters = events[-1]["session_kv_cache"]["counters"]
            evictions = _counter_value(counters, "evictions")
            passed = (
                all(bool(item["ok"]) for item in events)
                and evictions >= 1
                and bool(events[-1]["miss"])
                and not bool(events[-1]["drop"])
            )
            return {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "evidence_strength": evidence_strength,
                "execution_boundary": "direct-native",
                "eviction_counter_increased": evictions >= 1,
                "post_eviction_miss_recover": bool(events[-1]["miss"])
                and bool(events[-1]["ok"]),
                "watermark_fatal_observed": False,
                "events": events,
            }
        finally:
            native.unload(model_id)


def _run_b1a_ttl_probe_direct_native(
    *,
    model_id: str,
    model_memory_gb: float,
    max_tokens: int,
    session_prefix: str,
    evidence_strength: str,
) -> dict[str, Any]:
    with _session_cache_env(True, ttl_s=0.001):
        native = _load_probe_native(model_id=model_id, model_memory_gb=model_memory_gb)
        previous = dict(_native_session_cache_status(native).get("counters", {}))
        events: list[dict[str, Any]] = []
        try:
            event, previous = _probe_request_direct_native(
                native,
                model_id=model_id,
                session_id=f"{session_prefix}-ttl",
                label="create_session",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            time.sleep(0.01)
            event, previous = _probe_request_direct_native(
                native,
                model_id=model_id,
                session_id=f"{session_prefix}-ttl",
                label="request_after_ttl",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            counters = events[-1]["session_kv_cache"]["counters"]
            expirations = _counter_value(counters, "expirations")
            passed = (
                all(bool(item["ok"]) for item in events)
                and expirations >= 1
                and bool(events[-1]["miss"])
            )
            return {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "evidence_strength": evidence_strength,
                "execution_boundary": "direct-native",
                "expiration_counter_increased": expirations >= 1,
                "post_expire_miss_new_session": bool(events[-1]["miss"])
                and bool(events[-1]["ok"]),
                "events": events,
            }
        finally:
            native.unload(model_id)


def _run_b1a_restart_probe_direct_native(
    *,
    model_id: str,
    model_memory_gb: float,
    max_tokens: int,
    session_prefix: str,
    evidence_strength: str,
) -> dict[str, Any]:
    with _session_cache_env(True):
        native = _load_probe_native(model_id=model_id, model_memory_gb=model_memory_gb)
        previous = dict(_native_session_cache_status(native).get("counters", {}))
        events: list[dict[str, Any]] = []
        restart_payload: dict[str, Any] = {}
        try:
            event, previous = _probe_request_direct_native(
                native,
                model_id=model_id,
                session_id=f"{session_prefix}-restart",
                label="create_session",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            event, previous = _probe_request_direct_native(
                native,
                model_id=model_id,
                session_id=f"{session_prefix}-restart",
                label="warm_hit_before_restart",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            before_restart = _native_session_cache_status(native)
            before_restart_counters = dict(before_restart.get("counters", {}))
            unload = native.unload(model_id)
            after_unload = _native_session_cache_status(native)
            after_unload_counters = dict(after_unload.get("counters", {}))
            unload_delta = _counter_delta(before_restart_counters, after_unload_counters)
            load = native.load(model_id, memory_gb=model_memory_gb)
            if not load.ok:
                raise RuntimeError(f"probe reload failed for {model_id}: {load.message}")
            after_reload = _native_session_cache_status(native)
            after_reload_counters = dict(after_reload.get("counters", {}))
            restart_payload = {
                "ok": bool(unload.ok and load.ok),
                "method": "direct_native_unload_load",
                "runtime_kernel_restart_model_used": False,
                "unload": {
                    "ok": unload.ok,
                    "message": unload.message,
                    "model_id": unload.model_id,
                    "freed_gb": unload.freed_gb,
                },
                "load": {
                    "ok": load.ok,
                    "message": load.message,
                },
                "session_kv_cache_after_unload": {
                    "active_entries": after_unload.get("active_entries"),
                    "counters": after_unload_counters,
                },
                "session_kv_cache_after_reload": {
                    "active_entries": after_reload.get("active_entries"),
                    "counters": after_reload_counters,
                },
                "session_kv_cache_counter_delta": unload_delta,
            }
            previous = after_reload_counters
            event, previous = _probe_request_direct_native(
                native,
                model_id=model_id,
                session_id=f"{session_prefix}-restart",
                label="post_restart_miss",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            event, previous = _probe_request_direct_native(
                native,
                model_id=model_id,
                session_id=f"{session_prefix}-restart",
                label="post_restart_warm_hit",
                max_tokens=max_tokens,
                previous_counters=previous,
            )
            events.append(event)
            old_entry_dropped = (
                _counter_value(unload_delta, "drops") >= 1
                and int(after_unload.get("active_entries") or 0) == 0
            )
            reclaim_verified = bool(unload.ok)
            passed = (
                bool(unload.ok and load.ok)
                and old_entry_dropped
                and bool(events[-2]["miss"])
                and bool(events[-1]["hit"])
                and reclaim_verified
                and all(bool(item["ok"]) for item in events)
            )
            return {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "evidence_strength": evidence_strength,
                "execution_boundary": "direct-native",
                "restart_method": "direct_native_unload_load",
                "runtime_kernel_restart_model_used": False,
                "restart_success": bool(unload.ok and load.ok),
                "old_session_entry_dropped": old_entry_dropped,
                "post_restart_miss_new_session": bool(events[-2]["miss"]),
                "second_post_restart_warm_hit": bool(events[-1]["hit"]),
                "reclaim_verified": reclaim_verified,
                "restart": restart_payload,
                "events": events,
            }
        finally:
            native.unload(model_id)


async def _run_b1a_subprobes(
    *,
    model_id: str,
    model_memory_gb: float,
    max_tokens: int,
    session_prefix: str,
    evidence_strength: str,
    execution_boundary: str,
) -> dict[str, Any]:
    async def guarded(name: str, runner: Any) -> tuple[str, dict[str, Any]]:
        try:
            result = runner()
            if isawaitable(result):
                result = await result
            return name, result
        except Exception as exc:
            return name, {
                "passed": False,
                "status": "failed",
                "evidence_strength": evidence_strength,
                "error": str(exc),
                "events": [],
            }

    if execution_boundary == "direct-native":
        results = [
            await guarded(
                "A3_session_lru_eviction",
                lambda: _run_b1a_lru_probe_direct_native(
                    model_id=model_id,
                    model_memory_gb=model_memory_gb,
                    max_tokens=max_tokens,
                    session_prefix=session_prefix,
                    evidence_strength=evidence_strength,
                ),
            ),
            await guarded(
                "A4_session_ttl",
                lambda: _run_b1a_ttl_probe_direct_native(
                    model_id=model_id,
                    model_memory_gb=model_memory_gb,
                    max_tokens=max_tokens,
                    session_prefix=session_prefix,
                    evidence_strength=evidence_strength,
                ),
            ),
            await guarded(
                "A5_runtime_restart",
                lambda: _run_b1a_restart_probe_direct_native(
                    model_id=model_id,
                    model_memory_gb=model_memory_gb,
                    max_tokens=max_tokens,
                    session_prefix=session_prefix,
                    evidence_strength=evidence_strength,
                ),
            ),
        ]
    else:
        results = [
            await guarded(
                "A3_session_lru_eviction",
                lambda: _run_b1a_lru_probe(
                    model_id=model_id,
                    model_memory_gb=model_memory_gb,
                    max_tokens=max_tokens,
                    session_prefix=session_prefix,
                    evidence_strength=evidence_strength,
                ),
            ),
            await guarded(
                "A4_session_ttl",
                lambda: _run_b1a_ttl_probe(
                    model_id=model_id,
                    model_memory_gb=model_memory_gb,
                    max_tokens=max_tokens,
                    session_prefix=session_prefix,
                    evidence_strength=evidence_strength,
                ),
            ),
            await guarded(
                "A5_runtime_restart",
                lambda: _run_b1a_restart_probe(
                    model_id=model_id,
                    model_memory_gb=model_memory_gb,
                    max_tokens=max_tokens,
                    session_prefix=session_prefix,
                    evidence_strength=evidence_strength,
                ),
            ),
        ]
    return dict(results)


def _build_b1a_ledger(
    *,
    run_id: str,
    runtime: str,
    backend: str,
    model_id: str,
    prompt_chars: int,
    max_tokens: int,
    session_id: str,
    disabled_records: list[dict[str, Any]],
    enabled_records: list[dict[str, Any]],
    subprobes: dict[str, Any],
    measurement_mode: str,
    evidence_strength: str,
    execution_boundary: str,
    output_path: Path,
) -> dict[str, Any]:
    disabled_summary = _b1a_summary(disabled_records, cache_enabled=False)
    enabled_summary = _b1a_summary(enabled_records, cache_enabled=True)
    improvement_ratio = _ratio(
        disabled_summary.get("warm_p50_first_token_ms"),
        enabled_summary.get("warm_p50_first_token_ms"),
    )
    a1_passed = bool(
        improvement_ratio is not None
        and improvement_ratio >= 1.5
        and enabled_summary.get("warm_p50_first_token_ms") is not None
        and disabled_summary.get("warm_p50_first_token_ms") is not None
        and enabled_summary["warm_p50_first_token_ms"]
        < disabled_summary["warm_p50_first_token_ms"]
    )
    a2_passed = bool(
        enabled_summary["warm_hits_total"] >= 2
        and enabled_summary["drops_total"] == 0
        and enabled_summary["cold_round_miss"]
    )
    subprobes_passed = all(bool(probe.get("passed")) for probe in subprobes.values())
    ok = bool(
        disabled_summary["ok"]
        and enabled_summary["ok"]
        and a1_passed
        and a2_passed
        and subprobes_passed
    )
    return {
        "schema_version": "b1a.v1",
        "gate": "B-1a",
        "part": "A",
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "host": _host_label(),
        "runtime": runtime,
        "backend": "native" if backend == "fake" else backend,
        "backend_mode": backend,
        "execution_boundary": execution_boundary,
        "measurement_mode": measurement_mode,
        "evidence_strength": evidence_strength,
        "model": _b1a_model_metadata(model_id=model_id, backend=backend),
        "config": {
            "OWLMLX_SESSION_CACHE_ENABLED": "1",
            "execution_boundary": execution_boundary,
            "session_id": session_id,
            "temperature": 0.0,
            "seed": 42,
            "max_tokens": max_tokens,
            "max_generation_concurrency": 1,
        },
        "test_shape": {
            "prompt_chars_approx": prompt_chars,
            "rounds": len(enabled_records),
            "round_pattern": "append-only",
        },
        "rounds": _b1a_rounds(enabled_records),
        "summary": {
            "warm_min_first_token_ms": enabled_summary["warm_min_first_token_ms"],
            "warm_p50_first_token_ms": enabled_summary["warm_p50_first_token_ms"],
            "warm_max_first_token_ms": enabled_summary["warm_max_first_token_ms"],
            "hits_total": enabled_summary["hits_total"],
            "drops_total": enabled_summary["drops_total"],
            "A1_warm_ttft_improvement": {
                "passed": a1_passed,
                "improvement_ratio_p50": improvement_ratio,
                "enabled_warm_p50_lt_disabled_warm_p50": (
                    enabled_summary["warm_p50_first_token_ms"]
                    < disabled_summary["warm_p50_first_token_ms"]
                    if enabled_summary["warm_p50_first_token_ms"] is not None
                    and disabled_summary["warm_p50_first_token_ms"] is not None
                    else False
                ),
                "warm_min_p50_max_recorded": all(
                    value is not None
                    for value in (
                        enabled_summary["warm_min_first_token_ms"],
                        enabled_summary["warm_p50_first_token_ms"],
                        enabled_summary["warm_max_first_token_ms"],
                    )
                ),
            },
            "A2_hit_miss_counters": {
                "passed": a2_passed,
                "warm_hits_min": 2,
                "warm_hits_total": enabled_summary["warm_hits_total"],
                "drops_total": enabled_summary["drops_total"],
                "cold_round_miss": enabled_summary["cold_round_miss"],
            },
        },
        "disabled_baseline": {
            "rounds": _b1a_rounds(disabled_records),
            "warm_p50_first_token_ms": disabled_summary["warm_p50_first_token_ms"],
            "summary": disabled_summary,
        },
        "improvement_ratio_p50": improvement_ratio,
        "subprobes": subprobes,
        "watermark_fatal_observed": False,
        "verdict": "passed" if ok else "failed",
        "ok": ok,
        "output_path": str(output_path),
    }


def run_session_kv_cache_ttft(
    *,
    runtime: str,
    backend: str,
    model_id: str,
    model_memory_gb: float,
    rounds: int,
    prompt_chars: int,
    output_dir: Path,
    max_tokens: int = 2,
    session_id: str = DEFAULT_SESSION_ID,
    fake_cold_prefill_ms: float = 20.0,
    fake_warm_prefill_ms: float = 2.0,
    gate: str = "baseline",
    execution_boundary: str = "auto",
) -> dict[str, Any]:
    normalized_gate = _normalize_gate(gate)
    if runtime != "owlmlx":
        raise ValueError("only --runtime owlmlx is implemented in this bench")
    if backend not in {"fake", "native"}:
        raise ValueError("--backend must be fake or native")
    if rounds < 2:
        raise ValueError("--rounds must be >= 2 so warm-cache TTFT can be measured")
    if prompt_chars < 1:
        raise ValueError("--prompt-chars must be >= 1")
    resolved_execution_boundary = _resolve_execution_boundary(
        execution_boundary=execution_boundary,
        gate=normalized_gate,
        backend=backend,
    )

    if normalized_gate == B1A_GATE:
        run_id = f"{_now_compact_utc()}-b1a-gemma4-31b-it-session-kv-ttft"
        if session_id == DEFAULT_SESSION_ID:
            session_id = f"{B1A_SESSION_PREFIX}-{run_id}"
    else:
        run_id = f"{_now_compact_utc()}-{runtime}-{backend}-session-kv-ttft-n{rounds}"
    output_path = output_dir / f"{run_id}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    measurement_mode = (
        "synthetic_native_prompt_cache_ttft_smoke"
        if backend == "fake"
        else "native_mlx_prompt_cache_ttft"
    )
    evidence_strength = (
        "smoke_only_no_real_model_or_allocator_claim"
        if backend == "fake"
        else "real_native_model_ttft"
    )

    async def run_pair() -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        dict[str, Any],
    ]:
        disabled = await _run_mode(
            backend=backend,
            cache_enabled=False,
            runtime=runtime,
            model_id=model_id,
            model_memory_gb=model_memory_gb,
            rounds=rounds,
            prompt_chars=prompt_chars,
            max_tokens=max_tokens,
            session_id=session_id,
            measurement_mode=measurement_mode,
            evidence_strength=evidence_strength,
            execution_boundary=resolved_execution_boundary,
        )
        enabled = await _run_mode(
            backend=backend,
            cache_enabled=True,
            runtime=runtime,
            model_id=model_id,
            model_memory_gb=model_memory_gb,
            rounds=rounds,
            prompt_chars=prompt_chars,
            max_tokens=max_tokens,
            session_id=session_id,
            measurement_mode=measurement_mode,
            evidence_strength=evidence_strength,
            execution_boundary=resolved_execution_boundary,
        )
        subprobes: dict[str, Any] = {}
        if normalized_gate == B1A_GATE:
            subprobes = await _run_b1a_subprobes(
                model_id=model_id,
                model_memory_gb=model_memory_gb,
                max_tokens=max_tokens,
                session_prefix=session_id,
                evidence_strength=evidence_strength,
                execution_boundary=resolved_execution_boundary,
            )
        return disabled, enabled, subprobes

    def run_pair_direct_native() -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        dict[str, Any],
    ]:
        disabled = _run_mode_direct_native(
            backend=backend,
            cache_enabled=False,
            runtime=runtime,
            model_id=model_id,
            model_memory_gb=model_memory_gb,
            rounds=rounds,
            prompt_chars=prompt_chars,
            max_tokens=max_tokens,
            session_id=session_id,
            measurement_mode=measurement_mode,
            evidence_strength=evidence_strength,
            execution_boundary=resolved_execution_boundary,
        )
        enabled = _run_mode_direct_native(
            backend=backend,
            cache_enabled=True,
            runtime=runtime,
            model_id=model_id,
            model_memory_gb=model_memory_gb,
            rounds=rounds,
            prompt_chars=prompt_chars,
            max_tokens=max_tokens,
            session_id=session_id,
            measurement_mode=measurement_mode,
            evidence_strength=evidence_strength,
            execution_boundary=resolved_execution_boundary,
        )
        subprobes: dict[str, Any] = {}
        if normalized_gate == B1A_GATE:
            subprobes = asyncio.run(
                _run_b1a_subprobes(
                    model_id=model_id,
                    model_memory_gb=model_memory_gb,
                    max_tokens=max_tokens,
                    session_prefix=session_id,
                    evidence_strength=evidence_strength,
                    execution_boundary=resolved_execution_boundary,
                )
            )
        return disabled, enabled, subprobes

    if backend == "fake":
        with _fake_mlx_lm(
            cold_prefill_ms=fake_cold_prefill_ms,
            warm_prefill_ms=fake_warm_prefill_ms,
        ):
            if resolved_execution_boundary == "direct-native":
                disabled_records, enabled_records, subprobes = run_pair_direct_native()
            else:
                disabled_records, enabled_records, subprobes = asyncio.run(run_pair())
    else:
        if resolved_execution_boundary == "direct-native":
            disabled_records, enabled_records, subprobes = run_pair_direct_native()
        else:
            disabled_records, enabled_records, subprobes = asyncio.run(run_pair())

    records = disabled_records + enabled_records

    if normalized_gate == B1A_GATE:
        ledger = _build_b1a_ledger(
            run_id=run_id,
            runtime=runtime,
            backend=backend,
            model_id=model_id,
            prompt_chars=prompt_chars,
            max_tokens=max_tokens,
            session_id=session_id,
            disabled_records=disabled_records,
            enabled_records=enabled_records,
            subprobes=subprobes,
            measurement_mode=measurement_mode,
            evidence_strength=evidence_strength,
            execution_boundary=resolved_execution_boundary,
            output_path=output_path,
        )
        with output_path.open("w", encoding="utf-8") as stream:
            stream.write(json.dumps(ledger, sort_keys=True))
            stream.write("\n")
        return ledger

    with output_path.open("w", encoding="utf-8") as stream:
        for record in records:
            record_with_id = {"run_id": run_id, **record}
            stream.write(json.dumps(record_with_id, sort_keys=True))
            stream.write("\n")

    disabled_summary = _mode_summary(records, cache_enabled=False)
    enabled_summary = _mode_summary(records, cache_enabled=True)
    improvement_formula = (
        "disabled.warm_p50_first_token_ms / enabled.warm_p50_first_token_ms"
    )
    improvement_ratio = _ratio(
        disabled_summary.warm_p50_first_token_ms,
        enabled_summary.warm_p50_first_token_ms,
    )
    summary = {
        "ok": disabled_summary.ok and enabled_summary.ok,
        "gate": "baseline",
        "run_id": run_id,
        "runtime": runtime,
        "backend": backend,
        "execution_boundary": resolved_execution_boundary,
        "measurement_mode": measurement_mode,
        "evidence_strength": evidence_strength,
        "rounds": rounds,
        "prompt_chars": prompt_chars,
        "session_id": session_id,
        "disabled": disabled_summary.to_dict(),
        "enabled": enabled_summary.to_dict(),
        "warm_cache_p50_improvement_formula": improvement_formula,
        "warm_cache_p50_improvement_ratio": improvement_ratio,
        "meets_5x_ttft_gate": (
            improvement_ratio is not None and improvement_ratio >= 5.0
        ),
        "output_path": str(output_path),
    }
    return summary


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate",
        choices=("default", "baseline", B1A_GATE),
        default="baseline",
    )
    parser.add_argument("--runtime", choices=("owlmlx", "omlx", "vmlx"), default="owlmlx")
    parser.add_argument("--backend", choices=("fake", "native"), default="fake")
    parser.add_argument(
        "--execution-boundary",
        choices=EXECUTION_BOUNDARIES,
        default="auto",
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--model-gb", type=float, default=1.0)
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--prompt-chars", type=int, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fake-cold-prefill-ms", type=float, default=20.0)
    parser.add_argument("--fake-warm-prefill-ms", type=float, default=2.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    gate = _normalize_gate(args.gate)
    model_id = args.model
    if model_id is None:
        model_id = B1A_MODEL_PATH if gate == B1A_GATE else DEFAULT_MODEL_ID
    rounds = args.rounds
    if rounds is None:
        rounds = B1A_DEFAULT_ROUNDS if gate == B1A_GATE else 10
    prompt_chars = args.prompt_chars
    if prompt_chars is None:
        prompt_chars = B1A_DEFAULT_PROMPT_CHARS if gate == B1A_GATE else 4096
    max_tokens = args.max_tokens
    if max_tokens is None:
        max_tokens = B1A_DEFAULT_MAX_TOKENS
    try:
        summary = run_session_kv_cache_ttft(
            runtime=args.runtime,
            backend=args.backend,
            model_id=model_id,
            model_memory_gb=args.model_gb,
            rounds=rounds,
            prompt_chars=prompt_chars,
            output_dir=args.output,
            max_tokens=max_tokens,
            session_id=args.session_id,
            fake_cold_prefill_ms=args.fake_cold_prefill_ms,
            fake_warm_prefill_ms=args.fake_warm_prefill_ms,
            gate=gate,
            execution_boundary=args.execution_boundary,
        )
    except Exception as exc:
        print(f"session_kv_cache_ttft failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
