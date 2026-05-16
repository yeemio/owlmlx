#!/usr/bin/env python3
"""B-1a Part B native/subprocess UTF-8 byte equivalence bench.

The default fake mode is a deterministic smoke harness. It proves the B-1a
ledger shape and byte-divergence diagnostics without requiring MLX or model
weights. Use ``--mode real`` only on a host that can load the selected model
through both existing owlmlx backends.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DEFAULT_MODEL_ID = "gemma-4-31B-it"
DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "files"
    / "evidence"
    / "owlmlx"
    / "bench"
    / "native-byte-equivalence"
)
SCHEMA_VERSION = "b1a.v1"
GATE = "B-1a"
PART = "B"


@dataclass(frozen=True, slots=True)
class PromptCase:
    id: str
    category: str
    prompt: str


@dataclass(frozen=True, slots=True)
class BackendOutput:
    generated_text: str
    duration_ms: float
    token_ids: list[int] | None = None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _compact_timestamp(ts: datetime) -> str:
    return ts.strftime("%Y%m%dT%H%M%SZ")


def _iso_timestamp(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _model_slug(model_id: str) -> str:
    if model_id == DEFAULT_MODEL_ID:
        return "gemma4-31b-it"
    normalized = []
    for char in model_id.lower():
        if char.isalnum():
            normalized.append(char)
        elif normalized and normalized[-1] != "-":
            normalized.append("-")
    slug = "".join(normalized).strip("-")
    return slug or "model"


def _sha256_utf8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _repeat_to_chars(seed: str, target_chars: int) -> str:
    body = seed.strip()
    if not body:
        return ""
    repeated = (body + "\n") * ((target_chars // (len(body) + 1)) + 1)
    return repeated[:target_chars].rstrip()


def _prompt_cases() -> tuple[PromptCase, ...]:
    p2_seed = (
        "Explain how a runtime isolates model loading, generation, and memory "
        "accounting without mixing product UI responsibilities into the backend."
    )
    p3_seed = (
        "Background: owlmlx owns runtime identity, backend lifecycle, cache "
        "truth, and host safety. A downstream desktop product may consume its "
        "status, but it must not redefine runtime capability labels. Given this "
        "boundary, answer the operator question using only runtime-owned facts."
    )
    p5_seed = (
        "user: We need a deterministic generation path for a large local model.\n"
        "assistant: Keep sampling fixed, cache disabled, and compare the bytes.\n"
        "user: Also preserve ownership boundaries and do not claim token IDs "
        "unless the current runtime surface already exposes them.\nassistant:"
    )
    return (
        PromptCase(
            id="p1",
            category="short_factual_qa",
            prompt="What is the capital of France? Answer in one short sentence.",
        ),
        PromptCase(
            id="p2",
            category="medium_technical_explanation",
            prompt=_repeat_to_chars(p2_seed, 500),
        ),
        PromptCase(
            id="p3",
            category="long_context_qa",
            prompt=_repeat_to_chars(p3_seed, 2000),
        ),
        PromptCase(
            id="p4",
            category="code_completion",
            prompt=(
                "Complete this Python function without adding imports:\n\n"
                "def normalize_model_id(value: str) -> str:\n"
                "    \"\"\"Return a lowercase dash-separated model id.\"\"\"\n"
                "    cleaned = value.strip().lower()\n"
                "    "
            ),
        ),
        PromptCase(
            id="p5",
            category="single_prompt_multiturn_style",
            prompt=_repeat_to_chars(p5_seed, 1500),
        ),
    )


def _host_label() -> str:
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.model"],
                capture_output=True,
                check=False,
                text=True,
                timeout=1.0,
            )
        except Exception:
            result = None
        if result is not None and result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    machine = platform.machine() or "unknown-machine"
    system = platform.system() or "unknown-system"
    return f"{system}-{machine}"


def _first_byte_divergence_index(left: str, right: str) -> int | None:
    left_bytes = left.encode("utf-8")
    right_bytes = right.encode("utf-8")
    for index, (left_byte, right_byte) in enumerate(zip(left_bytes, right_bytes)):
        if left_byte != right_byte:
            return index
    if len(left_bytes) != len(right_bytes):
        return min(len(left_bytes), len(right_bytes))
    return None


def _byte_at(text: str, index: int | None) -> int | None:
    if index is None:
        return None
    payload = text.encode("utf-8")
    if index < 0 or index >= len(payload):
        return None
    return int(payload[index])


def _first_token_id_divergence_index(
    left: list[int] | None,
    right: list[int] | None,
) -> int | None:
    if left is None or right is None:
        return None
    for index, (left_token, right_token) in enumerate(zip(left, right)):
        if left_token != right_token:
            return index
    if len(left) != len(right):
        return min(len(left), len(right))
    return None


def _token_ids_equivalent(
    left: list[int] | None,
    right: list[int] | None,
) -> bool | None:
    if left is None or right is None:
        return None
    return left == right


def _suspected_root_cause(
    *,
    native_text: str,
    subprocess_text: str,
    temperature: float,
    fake_divergence: bool,
) -> str:
    if fake_divergence:
        return "sampler"
    if native_text.strip() == subprocess_text.strip():
        return "stream_framing"
    if temperature != 0.0:
        return "sampler"
    return "unknown"


def _fake_text(
    *,
    backend: str,
    prompt: PromptCase,
    max_tokens: int,
    temperature: float,
    seed: int,
    diverge_prompt: str | None,
) -> str:
    prompt_hash = _sha256_utf8(prompt.prompt)[:16]
    text = (
        f"{prompt.id}|category={prompt.category}|seed={seed}|temp={temperature}|"
        f"max_tokens={max_tokens}|prompt_hash={prompt_hash}|byte_equiv_smoke"
    )
    if backend == "subprocess" and diverge_prompt == prompt.id:
        chars = list(text)
        marker = text.find("prompt_hash=")
        index = marker + len("prompt_hash=") if marker >= 0 else len(chars) // 2
        chars[index] = "f" if chars[index] != "f" else "e"
        text = "".join(chars)
    return text


def _run_fake_backend(
    *,
    backend: str,
    prompt: PromptCase,
    max_tokens: int,
    temperature: float,
    seed: int,
    diverge_prompt: str | None,
) -> BackendOutput:
    started = time.perf_counter()
    text = _fake_text(
        backend=backend,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        seed=seed,
        diverge_prompt=diverge_prompt,
    )
    return BackendOutput(
        generated_text=text,
        duration_ms=round((time.perf_counter() - started) * 1000.0, 3),
    )


def _detail_token_ids(detail: dict[str, Any]) -> list[int] | None:
    raw = detail.get("token_ids")
    if raw is None:
        raw = detail.get("generated_token_ids")
    if not isinstance(raw, list):
        return None
    try:
        return [int(token) for token in raw]
    except (TypeError, ValueError):
        return None


def _real_backend(backend_name: str) -> Any:
    from owlmlx.runtime.mlx_lm_subprocess_backend import MlxLmSubprocessBackend
    from owlmlx.runtime.mlx_native_backend import MlxNativeBackend

    if backend_name == "native":
        return MlxNativeBackend()
    return MlxLmSubprocessBackend(
        env_overrides={"OWLMLX_SESSION_CACHE_ENABLED": "0"}
    )


def _generate_with_real_backend(
    *,
    backend: Any,
    model_id: str,
    prompt: PromptCase,
    max_tokens: int,
    temperature: float,
) -> BackendOutput:
    started = time.perf_counter()
    result = backend.generate(
        model_id,
        prompt.prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    duration_ms = round((time.perf_counter() - started) * 1000.0, 3)
    if not result.ok:
        raise RuntimeError(f"real backend generate failed: {result.message}")
    return BackendOutput(
        generated_text=result.text,
        duration_ms=duration_ms,
        token_ids=_detail_token_ids(dict(result.detail)),
    )


def _run_real_backend_suite(
    *,
    backend_name: str,
    model_id: str,
    prompts: tuple[PromptCase, ...],
    max_tokens: int,
    temperature: float,
) -> dict[str, BackendOutput]:
    backend = _real_backend(backend_name)
    load = backend.load(model_id, memory_gb=0.0)
    if not load.ok:
        raise RuntimeError(f"{backend_name} load failed: {load.message}")
    try:
        return {
            prompt.id: _generate_with_real_backend(
                backend=backend,
                model_id=model_id,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            for prompt in prompts
        }
    finally:
        backend.unload(model_id)


@contextlib.contextmanager
def _non_cache_env() -> Iterator[None]:
    old_enabled = os.environ.get("OWLMLX_SESSION_CACHE_ENABLED")
    try:
        os.environ["OWLMLX_SESSION_CACHE_ENABLED"] = "0"
        yield
    finally:
        if old_enabled is None:
            os.environ.pop("OWLMLX_SESSION_CACHE_ENABLED", None)
        else:
            os.environ["OWLMLX_SESSION_CACHE_ENABLED"] = old_enabled


def _backend_payload(output: BackendOutput) -> dict[str, Any]:
    return {
        "generated_text": output.generated_text,
        "generated_text_utf8_sha256": _sha256_utf8(output.generated_text),
        "token_ids": output.token_ids,
        "duration_ms": output.duration_ms,
    }


def _prompt_record(
    *,
    prompt: PromptCase,
    native: BackendOutput,
    subprocess_output: BackendOutput,
    temperature: float,
    fake_diverge_prompt: str | None,
) -> dict[str, Any]:
    byte_divergence = _first_byte_divergence_index(
        native.generated_text,
        subprocess_output.generated_text,
    )
    token_divergence = _first_token_id_divergence_index(
        native.token_ids,
        subprocess_output.token_ids,
    )
    token_equivalent = _token_ids_equivalent(
        native.token_ids,
        subprocess_output.token_ids,
    )
    return {
        "id": prompt.id,
        "chars": len(prompt.prompt),
        "category": prompt.category,
        "prompt_utf8_sha256": _sha256_utf8(prompt.prompt),
        "native": _backend_payload(native),
        "subprocess": _backend_payload(subprocess_output),
        "generated_text_utf8_equivalent": byte_divergence is None,
        "first_byte_divergence_index": byte_divergence,
        "token_ids_equivalent": token_equivalent,
        "first_token_id_divergence_index": token_divergence,
        "suspected_root_cause": (
            None
            if byte_divergence is None
            else _suspected_root_cause(
                native_text=native.generated_text,
                subprocess_text=subprocess_output.generated_text,
                temperature=temperature,
                fake_divergence=fake_diverge_prompt == prompt.id,
            )
        ),
    }


def _divergence_diagnostic(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    for record in records:
        if record["generated_text_utf8_equivalent"]:
            continue
        index = record["first_byte_divergence_index"]
        native_text = str(record["native"]["generated_text"])
        subprocess_text = str(record["subprocess"]["generated_text"])
        return {
            "first_failing_prompt": record["id"],
            "first_byte_divergence_index": index,
            "native_byte_at_index": _byte_at(native_text, index),
            "subprocess_byte_at_index": _byte_at(subprocess_text, index),
            "suspected_root_cause": record["suspected_root_cause"] or "unknown",
        }
    return None


def _build_record(
    *,
    run_id: str,
    timestamp_utc: str,
    host: str,
    model_id: str,
    mode: str,
    max_tokens: int,
    temperature: float,
    seed: int,
    prompts: list[dict[str, Any]],
) -> dict[str, Any]:
    equivalent_count = sum(
        1 for prompt in prompts if prompt["generated_text_utf8_equivalent"]
    )
    divergent_count = len(prompts) - equivalent_count
    verdict = "passed" if divergent_count == 0 else "failed"
    return {
        "schema_version": SCHEMA_VERSION,
        "gate": GATE,
        "part": PART,
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "host": host,
        "model": {
            "id": model_id,
            "path": model_id if Path(model_id).exists() else None,
        },
        "config": {
            "OWLMLX_SESSION_CACHE_ENABLED": "0",
            "session_id_header_set": False,
            "temperature": temperature,
            "seed": seed,
            "seed_applied_to_runtime_contract": mode in {"fake", "smoke"},
            "max_tokens": max_tokens,
            "mode": mode,
        },
        "prompts": prompts,
        "summary": {
            "total_prompts": len(prompts),
            "utf8_equivalent_count": equivalent_count,
            "divergent_count": divergent_count,
        },
        "verdict": verdict,
        "divergence_diagnostic": _divergence_diagnostic(prompts),
    }


def run_native_byte_equivalence(
    *,
    model_id: str = DEFAULT_MODEL_ID,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_tokens: int = 128,
    temperature: float = 0.0,
    seed: int = 42,
    mode: str = "fake",
    fake_diverge_prompt: str | None = None,
) -> dict[str, Any]:
    if max_tokens < 1:
        raise ValueError("--max-tokens must be >= 1")
    if mode not in {"fake", "smoke", "real"}:
        raise ValueError("--mode must be fake, smoke, or real")
    prompt_cases = _prompt_cases()
    prompt_ids = {prompt.id for prompt in prompt_cases}
    if fake_diverge_prompt is not None and fake_diverge_prompt not in prompt_ids:
        raise ValueError("--fake-diverge-prompt must be one of p1, p2, p3, p4, p5")

    timestamp = _now_utc()
    run_id = str(uuid.uuid4())
    run_stamp = _compact_timestamp(timestamp)
    output_path = (
        output_dir
        / f"{run_stamp}-b1a-{_model_slug(model_id)}-byte-equiv-n5.jsonl"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    real_mode = mode == "real"
    native_outputs: dict[str, BackendOutput] = {}
    subprocess_outputs: dict[str, BackendOutput] = {}
    records: list[dict[str, Any]] = []
    with _non_cache_env():
        if real_mode:
            native_outputs = _run_real_backend_suite(
                backend_name="native",
                model_id=model_id,
                prompts=prompt_cases,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            subprocess_outputs = _run_real_backend_suite(
                backend_name="subprocess",
                model_id=model_id,
                prompts=prompt_cases,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        for prompt in prompt_cases:
            if real_mode:
                native = native_outputs[prompt.id]
                subprocess_output = subprocess_outputs[prompt.id]
            else:
                native = _run_fake_backend(
                    backend="native",
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    seed=seed,
                    diverge_prompt=fake_diverge_prompt,
                )
                subprocess_output = _run_fake_backend(
                    backend="subprocess",
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    seed=seed,
                    diverge_prompt=fake_diverge_prompt,
                )
            records.append(
                _prompt_record(
                    prompt=prompt,
                    native=native,
                    subprocess_output=subprocess_output,
                    temperature=temperature,
                    fake_diverge_prompt=fake_diverge_prompt,
                )
            )

    record = _build_record(
        run_id=run_id,
        timestamp_utc=_iso_timestamp(timestamp),
        host=_host_label(),
        model_id=model_id,
        mode=mode,
        max_tokens=max_tokens,
        temperature=temperature,
        seed=seed,
        prompts=records,
    )
    with output_path.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True))
        stream.write("\n")

    return {
        "ok": record["verdict"] == "passed",
        "run_id": run_id,
        "output_path": str(output_path),
        "verdict": record["verdict"],
        "summary": record["summary"],
        "divergence_diagnostic": record["divergence_diagnostic"],
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL_ID)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", choices=("fake", "smoke", "real"), default="fake")
    parser.add_argument(
        "--fake-diverge-prompt",
        choices=("p1", "p2", "p3", "p4", "p5"),
        default=None,
        help="Inject a deterministic fake-mode byte divergence for tests.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = run_native_byte_equivalence(
            model_id=args.model,
            output_dir=args.output,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            seed=args.seed,
            mode=args.mode,
            fake_diverge_prompt=args.fake_diverge_prompt,
        )
    except Exception as exc:
        print(f"native_byte_equivalence failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
