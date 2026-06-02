#!/usr/bin/env python3
"""Lightweight local inventory for MTP/speculative candidates.

This script reads model ``config.json`` files only. It does not import MLX,
load weights, or start any runtime process. Its purpose is to turn the local
MTP candidate question into a repeatable evidence row for the F-3 line.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "f3.mtp_candidate_inventory.v1"
DEFAULT_ROOTS = (
    "/Users/yeemio/AI/Agent/models",
    "/Users/yeemio/AI/Agent/model-candidates",
)
DEFAULT_OUTPUT_DIR = "files/evidence/owlmlx/bench/f3-resident-mtp"


@dataclass(frozen=True)
class ModelCandidate:
    path: str
    model_type: str | None
    architectures: tuple[str, ...]
    safetensors_count: int
    mtp_signals: tuple[str, ...]
    cache_family: str
    cache_reasons: tuple[str, ...]
    candidate_kind: str
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "model_type": self.model_type,
            "architectures": list(self.architectures),
            "safetensors_count": self.safetensors_count,
            "mtp_signals": list(self.mtp_signals),
            "cache_family": self.cache_family,
            "cache_reasons": list(self.cache_reasons),
            "candidate_kind": self.candidate_kind,
            "next_action": self.next_action,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _flatten_values(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _flatten_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _flatten_values(child)


def _get_text_config(config: dict[str, Any]) -> dict[str, Any]:
    text_config = config.get("text_config")
    return text_config if isinstance(text_config, dict) else {}


def mtp_signals_from_config(config: dict[str, Any]) -> tuple[str, ...]:
    signals: list[str] = []
    text_config = _get_text_config(config)
    for owner, data in (("root", config), ("text_config", text_config)):
        for key in (
            "num_nextn_predict_layers",
            "mtp_num_hidden_layers",
            "num_mtp_layers",
            "mtp_num_layers",
            "use_mtp",
            "is_assistant",
        ):
            if key in data:
                signals.append(f"{owner}.{key}={data[key]}")
    model_type = str(config.get("model_type", ""))
    text_model_type = str(text_config.get("model_type", ""))
    architectures = [str(item) for item in config.get("architectures", [])]
    if "assistant" in model_type:
        signals.append(f"root.model_type={model_type}")
    if "assistant" in text_model_type:
        signals.append(f"text_config.model_type={text_model_type}")
    for architecture in architectures:
        if "Assistant" in architecture:
            signals.append(f"architecture={architecture}")
    return tuple(dict.fromkeys(signals))


def classify_cache_family(config: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    text_config = _get_text_config(config)
    model_type = str(config.get("model_type", ""))
    text_model_type = str(text_config.get("model_type", ""))

    for owner, data in (("root", config), ("text_config", text_config)):
        layer_types = data.get("layer_types")
        if isinstance(layer_types, list):
            unique = sorted({str(item) for item in layer_types})
            non_full = [item for item in unique if item != "full_attention"]
            if non_full:
                reasons.append(f"{owner}.layer_types_non_full={','.join(non_full)}")
            else:
                reasons.append(f"{owner}.layer_types_full_attention_only")
        if data.get("sliding_window") is not None:
            reasons.append(f"{owner}.sliding_window={data['sliding_window']}")
        if data.get("attention_chunk_size") is not None:
            reasons.append(f"{owner}.attention_chunk_size={data['attention_chunk_size']}")

    if model_type in {"deepseek_v4", "gemma4"}:
        reasons.append(f"known_hybrid_or_trim_sensitive_model_type={model_type}")
    if text_model_type in {"gemma4_text"}:
        reasons.append(f"known_hybrid_or_trim_sensitive_text_model_type={text_model_type}")

    if any(
        "non_full" in item
        or "sliding_window" in item
        or "attention_chunk_size" in item
        or "known_hybrid_or_trim_sensitive" in item
        for item in reasons
    ):
        return "hybrid_or_trim_sensitive", tuple(reasons)
    if any("full_attention_only" in item for item in reasons):
        return "full_attention_config_only", tuple(reasons)
    return "unknown_from_config", tuple(reasons)


def classify_candidate(
    *,
    path: Path,
    config: dict[str, Any],
    safetensors_count: int,
) -> ModelCandidate:
    model_type = config.get("model_type")
    architectures = tuple(str(item) for item in config.get("architectures", []))
    mtp_signals = mtp_signals_from_config(config)
    cache_family, cache_reasons = classify_cache_family(config)
    is_assistant = any("assistant" in item.lower() for item in mtp_signals)

    if not mtp_signals:
        candidate_kind = "no_mtp_signal"
        next_action = "ignore_for_mtp_candidate_inventory"
    elif is_assistant:
        candidate_kind = "assistant_drafter_artifact"
        next_action = "pair_with_matching_target_only; Gemma4 pair already covered by F-3.1"
    elif cache_family == "full_attention_config_only":
        candidate_kind = "native_mtp_full_attention_candidate"
        next_action = "eligible_for_lightweight_native_mtp_admissibility_probe"
    else:
        candidate_kind = "native_mtp_hybrid_or_unknown_candidate"
        next_action = "do_not_start_resident_mtp_backend; needs cache/trim-specific probe first"

    return ModelCandidate(
        path=str(path),
        model_type=str(model_type) if model_type is not None else None,
        architectures=architectures,
        safetensors_count=safetensors_count,
        mtp_signals=mtp_signals,
        cache_family=cache_family,
        cache_reasons=cache_reasons,
        candidate_kind=candidate_kind,
        next_action=next_action,
    )


def discover_candidates(roots: Iterable[Path]) -> list[ModelCandidate]:
    candidates: list[ModelCandidate] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for config_path in sorted(root.glob("**/config.json")):
            model_dir = config_path.parent
            if model_dir in seen:
                continue
            seen.add(model_dir)
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            candidates.append(
                classify_candidate(
                    path=model_dir,
                    config=config,
                    safetensors_count=sum(1 for _ in model_dir.glob("*.safetensors")),
                )
            )
    return candidates


def build_inventory_row(*, roots: Iterable[Path]) -> dict[str, Any]:
    candidates = discover_candidates(roots)
    rows = [candidate.to_dict() for candidate in candidates]
    mtp_rows = [row for row in rows if row["candidate_kind"] != "no_mtp_signal"]
    full_attention_rows = [
        row for row in rows if row["candidate_kind"] == "native_mtp_full_attention_candidate"
    ]
    assistant_rows = [
        row for row in rows if row["candidate_kind"] == "assistant_drafter_artifact"
    ]
    hybrid_rows = [
        row for row in rows if row["candidate_kind"] == "native_mtp_hybrid_or_unknown_candidate"
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "mtp_candidate_inventory",
        "generated_at": _now_iso(),
        "roots": [str(root) for root in roots],
        "summary": {
            "model_count": len(rows),
            "mtp_candidate_count": len(mtp_rows),
            "assistant_drafter_artifact_count": len(assistant_rows),
            "native_mtp_full_attention_candidate_count": len(full_attention_rows),
            "native_mtp_hybrid_or_unknown_candidate_count": len(hybrid_rows),
            "full_attention_resident_mtp_next_target_available": bool(full_attention_rows),
            "recommended_next_step": (
                "run_native_mtp_admissibility_probe_for_full_attention_candidate"
                if full_attention_rows
                else "no_local_full_attention_mtp_candidate; keep Gemma4 F-3 blocked and avoid F-3.2/F-3.3"
            ),
            "used_for_promotion_gate": False,
            "capability_label": "experimental",
        },
        "candidates": rows,
    }


def write_inventory(row: dict[str, Any], *, output_dir: Path, run_id: str | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"{run_id}-f3-mtp-candidate-inventory.jsonl"
    path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", nargs="*", default=list(DEFAULT_ROOTS))
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    roots = [Path(item) for item in args.roots]
    row = build_inventory_row(roots=roots)
    output_path = write_inventory(
        row,
        output_dir=Path(args.output_dir),
        run_id=args.run_id,
    )
    if args.print_json:
        print(json.dumps(row, indent=2, sort_keys=True))
    else:
        print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
