"""Experimental Gemma4 MTP drafter contract.

This module keeps the first Gemma4 assistant/MTP path runtime-owned without
binding owlmlx to unstable mlx-vlm internals. It validates local target/drafter
metadata, builds the narrow CLI invocation, and parses the speculative summary
that current mlx-vlm emits.
"""

from __future__ import annotations

import json
import re
import resource
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


GEMMA4_MTP_DRAFTER_SURFACE = "owlmlx.gemma4_mtp_drafter"
GEMMA4_MTP_DRAFTER_VERSION = "v1"
GEMMA4_MTP_CAPABILITY_LABEL = "experimental"

REQUIRED_MLX_VLM_MTP_FLAGS = (
    "--draft-model",
    "--draft-kind",
    "--draft-block-size",
)

_SPECULATIVE_SUMMARY_RE = re.compile(
    r"Speculative decoding:\s*"
    r"(?P<accepted>[0-9]+(?:\.[0-9]+)?)\s*"
    r"accepted tokens over\s*"
    r"(?P<rounds>[0-9]+)\s*rounds",
)


@dataclass(frozen=True)
class Gemma4MtpModelDescriptor:
    path: str
    model_type: str
    architectures: tuple[str, ...]
    text_model_type: str
    text_hidden_size: int | None
    text_num_hidden_layers: int | None
    vocab_size: int | None
    is_assistant: bool | None = None
    vision_model_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "path": self.path,
            "model_type": self.model_type,
            "architectures": list(self.architectures),
            "text_model_type": self.text_model_type,
            "text_hidden_size": self.text_hidden_size,
            "text_num_hidden_layers": self.text_num_hidden_layers,
            "vocab_size": self.vocab_size,
        }
        if self.is_assistant is not None:
            payload["is_assistant"] = self.is_assistant
        if self.vision_model_type is not None:
            payload["vision_model_type"] = self.vision_model_type
        return payload


@dataclass(frozen=True)
class Gemma4MtpPairInspection:
    target: Gemma4MtpModelDescriptor | None
    draft: Gemma4MtpModelDescriptor | None
    blockers: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.blockers and self.target is not None and self.draft is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": GEMMA4_MTP_DRAFTER_SURFACE,
            "version": GEMMA4_MTP_DRAFTER_VERSION,
            "capability_label": GEMMA4_MTP_CAPABILITY_LABEL,
            "ok": self.ok,
            "status": "ready" if self.ok else "blocked",
            "target": self.target.to_dict() if self.target else None,
            "draft": self.draft.to_dict() if self.draft else None,
            "draft_model_is_standalone_target": False if self.draft else None,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class MlxVlmToolchainInspection:
    python_executable: str
    returncode: int | None
    flags_present: tuple[str, ...]
    flags_missing: tuple[str, ...]
    stderr_excerpt: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.flags_missing

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": GEMMA4_MTP_DRAFTER_SURFACE,
            "version": GEMMA4_MTP_DRAFTER_VERSION,
            "capability_label": GEMMA4_MTP_CAPABILITY_LABEL,
            "python_executable": self.python_executable,
            "ok": self.ok,
            "status": "ready" if self.ok else "blocked",
            "returncode": self.returncode,
            "flags_present": list(self.flags_present),
            "flags_missing": list(self.flags_missing),
            "stderr_excerpt": self.stderr_excerpt,
        }


@dataclass(frozen=True)
class SpeculativeSummary:
    mean_accepted_tokens: float
    rounds: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_accepted_tokens": self.mean_accepted_tokens,
            "rounds": self.rounds,
        }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _descriptor_from_config(path: Path) -> Gemma4MtpModelDescriptor:
    config = _read_json(path / "config.json")
    generation_config_path = path / "generation_config.json"
    generation_config = (
        _read_json(generation_config_path)
        if generation_config_path.exists()
        else {}
    )
    text_config = config.get("text_config") if isinstance(config.get("text_config"), dict) else {}
    vision_config = (
        config.get("vision_config") if isinstance(config.get("vision_config"), dict) else {}
    )
    architectures = config.get("architectures")
    return Gemma4MtpModelDescriptor(
        path=str(path),
        model_type=str(config.get("model_type") or ""),
        architectures=tuple(str(item) for item in architectures)
        if isinstance(architectures, list)
        else (),
        text_model_type=str(text_config.get("model_type") or ""),
        text_hidden_size=_int_or_none(text_config.get("hidden_size")),
        text_num_hidden_layers=_int_or_none(text_config.get("num_hidden_layers")),
        vocab_size=_int_or_none(text_config.get("vocab_size")),
        is_assistant=(
            bool(generation_config["is_assistant"])
            if "is_assistant" in generation_config
            else None
        ),
        vision_model_type=(
            str(vision_config.get("model_type"))
            if vision_config.get("model_type") is not None
            else None
        ),
    )


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def inspect_gemma4_mtp_pair(
    *,
    target_path: str | Path,
    draft_path: str | Path,
) -> Gemma4MtpPairInspection:
    target_dir = Path(target_path)
    draft_dir = Path(draft_path)
    blockers: list[str] = []
    target: Gemma4MtpModelDescriptor | None = None
    draft: Gemma4MtpModelDescriptor | None = None

    if not (target_dir / "config.json").exists():
        blockers.append("target_config_missing")
    else:
        target = _descriptor_from_config(target_dir)

    if not (draft_dir / "config.json").exists():
        blockers.append("draft_config_missing")
    else:
        draft = _descriptor_from_config(draft_dir)

    if target is not None:
        if target.model_type != "gemma4":
            blockers.append("target_model_type_not_gemma4")
        if "Gemma4ForConditionalGeneration" not in target.architectures:
            blockers.append("target_architecture_not_gemma4_conditional_generation")
        if target.text_model_type != "gemma4_text":
            blockers.append("target_text_model_type_not_gemma4_text")
        if not target.vision_model_type:
            blockers.append("target_vision_config_missing")

    if draft is not None:
        if draft.model_type != "gemma4_assistant":
            blockers.append("draft_model_type_not_gemma4_assistant")
        if "Gemma4AssistantForCausalLM" not in draft.architectures:
            blockers.append("draft_architecture_not_gemma4_assistant")
        if draft.text_model_type != "gemma4_text":
            blockers.append("draft_text_model_type_not_gemma4_text")
        if draft.is_assistant is not True:
            blockers.append("draft_generation_config_not_assistant")

    if target is not None and draft is not None:
        if target.vocab_size != draft.vocab_size:
            blockers.append("target_draft_vocab_size_mismatch")
        if target.text_model_type != draft.text_model_type:
            blockers.append("target_draft_text_model_type_mismatch")

    return Gemma4MtpPairInspection(
        target=target,
        draft=draft,
        blockers=tuple(dict.fromkeys(blockers)),
    )


def classify_mlx_vlm_help_text(help_text: str) -> dict[str, tuple[str, ...]]:
    present = tuple(flag for flag in REQUIRED_MLX_VLM_MTP_FLAGS if flag in help_text)
    missing = tuple(flag for flag in REQUIRED_MLX_VLM_MTP_FLAGS if flag not in help_text)
    return {"present": present, "missing": missing}


def inspect_mlx_vlm_toolchain(
    *,
    python_executable: str,
    timeout_s: float = 20.0,
) -> MlxVlmToolchainInspection:
    try:
        completed = subprocess.run(
            [python_executable, "-m", "mlx_vlm", "generate", "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return MlxVlmToolchainInspection(
            python_executable=python_executable,
            returncode=None,
            flags_present=(),
            flags_missing=REQUIRED_MLX_VLM_MTP_FLAGS,
            stderr_excerpt=str(exc)[-2000:],
        )
    classified = classify_mlx_vlm_help_text(completed.stdout)
    return MlxVlmToolchainInspection(
        python_executable=python_executable,
        returncode=int(completed.returncode),
        flags_present=classified["present"],
        flags_missing=classified["missing"],
        stderr_excerpt=completed.stderr[-2000:],
    )


def build_mlx_vlm_generate_argv(
    *,
    python_executable: str,
    target_path: str | Path,
    prompt: str,
    max_tokens: int,
    temperature: float = 0.0,
    draft_path: str | Path | None = None,
    draft_block_size: int = 6,
    verbose: bool = True,
    skip_special_tokens: bool = False,
) -> tuple[str, ...]:
    argv = [
        python_executable,
        "-m",
        "mlx_vlm",
        "generate",
        "--model",
        str(target_path),
        "--prompt",
        str(prompt),
        "--max-tokens",
        str(int(max_tokens)),
        "--temperature",
        str(float(temperature)),
    ]
    if draft_path is not None:
        argv.extend(
            [
                "--draft-model",
                str(draft_path),
                "--draft-kind",
                "mtp",
                "--draft-block-size",
                str(int(draft_block_size)),
            ]
        )
    if skip_special_tokens:
        argv.append("--skip-special-tokens")
    if verbose:
        argv.append("--verbose")
    return tuple(argv)


def build_mlx_vlm_mtp_generate_argv(
    *,
    python_executable: str,
    target_path: str | Path,
    draft_path: str | Path,
    prompt: str,
    max_tokens: int,
    temperature: float = 0.0,
    draft_block_size: int = 6,
    verbose: bool = True,
    skip_special_tokens: bool = False,
) -> tuple[str, ...]:
    return build_mlx_vlm_generate_argv(
        python_executable=python_executable,
        target_path=target_path,
        draft_path=draft_path,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        draft_block_size=draft_block_size,
        verbose=verbose,
        skip_special_tokens=skip_special_tokens,
    )


def parse_speculative_summary(text: str) -> SpeculativeSummary | None:
    match = _SPECULATIVE_SUMMARY_RE.search(text)
    if not match:
        return None
    return SpeculativeSummary(
        mean_accepted_tokens=float(match.group("accepted")),
        rounds=int(match.group("rounds")),
    )


def extract_mlx_vlm_generated_text(stdout_text: str) -> str:
    generated_lines: list[str] = []
    saw_drafter_load = False
    for raw_line in stdout_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Loading drafter "):
            saw_drafter_load = True
            continue
        if line.startswith("Speculative decoding:"):
            if saw_drafter_load:
                break
            continue
        if "Loading drafter (mtp):" in stdout_text and not saw_drafter_load:
            continue
        generated_lines.append(raw_line.rstrip())
    return "\n".join(generated_lines).strip()


def parse_mlx_vlm_generate_output(
    *,
    stdout_text: str,
    stderr_text: str = "",
) -> dict[str, Any]:
    combined = "\n".join(part for part in (stdout_text, stderr_text) if part)
    summary = parse_speculative_summary(combined)
    return {
        "surface": GEMMA4_MTP_DRAFTER_SURFACE,
        "version": GEMMA4_MTP_DRAFTER_VERSION,
        "capability_label": GEMMA4_MTP_CAPABILITY_LABEL,
        "generated_text": extract_mlx_vlm_generated_text(stdout_text),
        "loaded_drafter": "Loading drafter (mtp):" in combined,
        "speculative_summary": summary.to_dict() if summary else None,
    }


def run_mlx_vlm_generate(
    *,
    python_executable: str,
    target_path: str | Path,
    prompt: str,
    max_tokens: int,
    temperature: float = 0.0,
    draft_path: str | Path | None = None,
    draft_block_size: int = 6,
    timeout_s: float = 900.0,
) -> dict[str, Any]:
    argv = build_mlx_vlm_generate_argv(
        python_executable=python_executable,
        target_path=target_path,
        draft_path=draft_path,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        draft_block_size=draft_block_size,
    )
    started = time.monotonic()
    completed = subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    elapsed_ms = round((time.monotonic() - started) * 1000, 3)
    parsed = parse_mlx_vlm_generate_output(
        stdout_text=completed.stdout,
        stderr_text=completed.stderr,
    )
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "surface": GEMMA4_MTP_DRAFTER_SURFACE,
        "version": GEMMA4_MTP_DRAFTER_VERSION,
        "capability_label": GEMMA4_MTP_CAPABILITY_LABEL,
        "ok": completed.returncode == 0,
        "adapter_family": "mlx-vlm",
        "drafter_enabled": draft_path is not None,
        "returncode": int(completed.returncode),
        "elapsed_ms": elapsed_ms,
        "child_max_resident_set_size": int(child_usage.ru_maxrss),
        "argv": list(argv),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "parsed": parsed,
    }


def run_mlx_vlm_mtp_generate(
    *,
    python_executable: str,
    target_path: str | Path,
    draft_path: str | Path,
    prompt: str,
    max_tokens: int,
    temperature: float = 0.0,
    draft_block_size: int = 6,
    timeout_s: float = 900.0,
) -> dict[str, Any]:
    return run_mlx_vlm_generate(
        python_executable=python_executable,
        target_path=target_path,
        draft_path=draft_path,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        draft_block_size=draft_block_size,
        timeout_s=timeout_s,
    )


def readiness_payload(
    *,
    target_path: str | Path,
    draft_path: str | Path,
    python_executable: str | None = None,
) -> dict[str, Any]:
    pair = inspect_gemma4_mtp_pair(target_path=target_path, draft_path=draft_path)
    payload: dict[str, Any] = {
        "surface": GEMMA4_MTP_DRAFTER_SURFACE,
        "version": GEMMA4_MTP_DRAFTER_VERSION,
        "capability_label": GEMMA4_MTP_CAPABILITY_LABEL,
        "pair": pair.to_dict(),
    }
    if python_executable:
        toolchain = inspect_mlx_vlm_toolchain(python_executable=python_executable)
        payload["toolchain"] = toolchain.to_dict()
        payload["ok"] = pair.ok and toolchain.ok
    else:
        payload["toolchain"] = None
        payload["ok"] = pair.ok
    payload["status"] = "ready" if payload["ok"] else "blocked"
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect Gemma4 MTP drafter readiness.")
    parser.add_argument("--target-path", required=True)
    parser.add_argument("--draft-path", required=True)
    parser.add_argument("--python-executable")
    args = parser.parse_args(argv)
    print(
        json.dumps(
            readiness_payload(
                target_path=args.target_path,
                draft_path=args.draft_path,
                python_executable=args.python_executable,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
