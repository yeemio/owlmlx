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
import json
import os
import sys
import time
import types
from dataclasses import dataclass
from datetime import datetime, timezone
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


@dataclass(frozen=True, slots=True)
class BenchModeSummary:
    cache_enabled: bool
    p50_first_token_ms: float | None
    p95_first_token_ms: float | None
    warm_p50_first_token_ms: float | None
    warm_p95_first_token_ms: float | None
    operation_count: int
    ok: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "cache_enabled": self.cache_enabled,
            "p50_first_token_ms": self.p50_first_token_ms,
            "p95_first_token_ms": self.p95_first_token_ms,
            "warm_p50_first_token_ms": self.warm_p50_first_token_ms,
            "warm_p95_first_token_ms": self.warm_p95_first_token_ms,
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
        p50_first_token_ms=_percentile(ttft, 0.50),
        p95_first_token_ms=_percentile(ttft, 0.95),
        warm_p50_first_token_ms=_percentile(warm_ttft, 0.50),
        warm_p95_first_token_ms=_percentile(warm_ttft, 0.95),
        operation_count=len(subset),
        ok=all(bool(record.get("ok")) for record in subset),
    )


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return round(numerator / denominator, 3)


@contextlib.contextmanager
def _session_cache_env(enabled: bool) -> Iterator[None]:
    old_enabled = os.environ.get("OWLMLX_SESSION_CACHE_ENABLED")
    try:
        os.environ["OWLMLX_SESSION_CACHE_ENABLED"] = "1" if enabled else "0"
        yield
    finally:
        if old_enabled is None:
            os.environ.pop("OWLMLX_SESSION_CACHE_ENABLED", None)
        else:
            os.environ["OWLMLX_SESSION_CACHE_ENABLED"] = old_enabled


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
    seen_prompt_cache_ids: set[int] = set()
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
        cache_id = id(prompt_cache) if prompt_cache is not None else None
        if cache_id is not None and cache_id in seen_prompt_cache_ids:
            delay_ms = warm_prefill_ms
        else:
            delay_ms = cold_prefill_ms
            if cache_id is not None:
                seen_prompt_cache_ids.add(cache_id)
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
    fake._seen_prompt_cache_count = lambda: len(seen_prompt_cache_ids)  # type: ignore[attr-defined]

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
                status = kernel.status_dict()["backend"]["detail"].get(
                    "session_kv_cache", {}
                )
                records.append(
                    {
                        "runtime": runtime,
                        "backend": backend,
                        "measurement_mode": measurement_mode,
                        "evidence_strength": evidence_strength,
                        "cache_enabled": cache_enabled,
                        "round": round_idx,
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
                    }
                )
                if measurement["ok"]:
                    transcript = f"{prompt}{measurement['generated_text']}\n"
        finally:
            kernel.unload_model(model_id)
        return records


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
) -> dict[str, Any]:
    if runtime != "owlmlx":
        raise ValueError("only --runtime owlmlx is implemented in this bench")
    if backend not in {"fake", "native"}:
        raise ValueError("--backend must be fake or native")
    if rounds < 2:
        raise ValueError("--rounds must be >= 2 so warm-cache TTFT can be measured")
    if prompt_chars < 1:
        raise ValueError("--prompt-chars must be >= 1")

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

    async def run_pair() -> list[dict[str, Any]]:
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
        )
        return disabled + enabled

    if backend == "fake":
        with _fake_mlx_lm(
            cold_prefill_ms=fake_cold_prefill_ms,
            warm_prefill_ms=fake_warm_prefill_ms,
        ):
            records = asyncio.run(run_pair())
    else:
        records = asyncio.run(run_pair())

    with output_path.open("w", encoding="utf-8") as stream:
        for record in records:
            record_with_id = {"run_id": run_id, **record}
            stream.write(json.dumps(record_with_id, sort_keys=True))
            stream.write("\n")

    disabled_summary = _mode_summary(records, cache_enabled=False)
    enabled_summary = _mode_summary(records, cache_enabled=True)
    improvement_ratio = _ratio(
        disabled_summary.p50_first_token_ms,
        enabled_summary.warm_p50_first_token_ms,
    )
    summary = {
        "ok": disabled_summary.ok and enabled_summary.ok,
        "run_id": run_id,
        "runtime": runtime,
        "backend": backend,
        "measurement_mode": measurement_mode,
        "evidence_strength": evidence_strength,
        "rounds": rounds,
        "prompt_chars": prompt_chars,
        "session_id": session_id,
        "disabled": disabled_summary.to_dict(),
        "enabled": enabled_summary.to_dict(),
        "warm_cache_p50_improvement_ratio": improvement_ratio,
        "meets_5x_ttft_gate": (
            improvement_ratio is not None and improvement_ratio >= 5.0
        ),
        "output_path": str(output_path),
    }
    return summary


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=("owlmlx", "omlx", "vmlx"), default="owlmlx")
    parser.add_argument("--backend", choices=("fake", "native"), default="fake")
    parser.add_argument("--model", default=DEFAULT_MODEL_ID)
    parser.add_argument("--model-gb", type=float, default=1.0)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--prompt-chars", type=int, default=4096)
    parser.add_argument("--max-tokens", type=int, default=2)
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fake-cold-prefill-ms", type=float, default=20.0)
    parser.add_argument("--fake-warm-prefill-ms", type=float, default=2.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = run_session_kv_cache_ttft(
            runtime=args.runtime,
            backend=args.backend,
            model_id=args.model,
            model_memory_gb=args.model_gb,
            rounds=args.rounds,
            prompt_chars=args.prompt_chars,
            output_dir=args.output,
            max_tokens=args.max_tokens,
            session_id=args.session_id,
            fake_cold_prefill_ms=args.fake_cold_prefill_ms,
            fake_warm_prefill_ms=args.fake_warm_prefill_ms,
        )
    except Exception as exc:
        print(f"session_kv_cache_ttft failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
