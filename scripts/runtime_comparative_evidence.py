#!/usr/bin/env python3
"""Operator entry for the runtime-owned comparative-evidence record surface.

Subcommands:

- ``append-rejected-record``: append one honest ``verdict_grade=rejected``
  record. Used when reference runtimes (``oMLX`` / ``vMLX``) cannot be
  invoked on the current host. This is real v1 data, not synthetic
  ``measured`` data; it satisfies harness contract section 5.4.
- ``latest``: print the latest record (or the explicit ``still_blocked``
  payload when no record exists).
- ``history``: print the full history envelope.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from owlmlx.comparative_evidence_ledger import (
    ComparativeEvidenceLedger,
    history_envelope,
    still_blocked_payload,
)
from owlmlx.comparative_evidence_record import (
    ComparativeEvidenceMeasurement,
    ComparativeEvidenceRuntime,
    build_comparative_evidence_record,
)


DEFAULT_LEDGER_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "comparative-evidence-ledger.jsonl"
)


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_measurement(*, failed: bool) -> ComparativeEvidenceMeasurement:
    return ComparativeEvidenceMeasurement(
        throughput_tokens_per_second=0.0,
        first_token_latency_ms=0.0,
        peak_resident_set_bytes=0,
        wall_clock_ms=0.0,
        completed_request_count=0,
        failure_count=1 if failed else 0,
        failure_causes=("reference_runtime_unavailable",) if failed else (),
    )


def _append_rejected_record(
    ledger: ComparativeEvidenceLedger,
    *,
    host_class: str,
    workload_class: str,
    model_id: str,
    model_quantization: str,
    decode_max_tokens: int,
    decode_temperature: float,
    prompt_set_hash: str,
    serving_budget_bytes: int,
    evidence_pointer: str,
    runtime_version: str,
) -> dict[str, object]:
    record = build_comparative_evidence_record(
        recorded_at=_now_iso_utc(),
        evidence_pointer=evidence_pointer,
        host_class=host_class,
        workload_class=workload_class,
        workload_invariants={
            "model_id": model_id,
            "model_quantization": model_quantization,
            "decode_max_tokens": decode_max_tokens,
            "decode_temperature": decode_temperature,
            "prompt_set_hash": prompt_set_hash,
            "serving_budget_bytes": serving_budget_bytes,
        },
        runtimes=(
            ComparativeEvidenceRuntime(
                runtime_id="owlmlx",
                runtime_version=runtime_version,
                measurement=_empty_measurement(failed=True),
            ),
            ComparativeEvidenceRuntime(
                runtime_id="omlx",
                runtime_version="unavailable",
                measurement=_empty_measurement(failed=True),
            ),
        ),
        verdict_text=(
            f"rejected: reference_runtime_unavailable on host_class={host_class}, "
            f"workload_class={workload_class}"
        ),
        verdict_grade="rejected",
    )
    return ledger.append(record)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Operator entry for the comparative-evidence record surface."
    )
    parser.add_argument(
        "--ledger-path",
        default=str(DEFAULT_LEDGER_PATH),
        help="Path to the JSONL ledger file (default: data/comparative-evidence-ledger.jsonl)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    append = sub.add_parser(
        "append-rejected-record",
        help="Append one honest verdict_grade=rejected record",
    )
    append.add_argument("--host-class", default="darwin-arm64-host")
    append.add_argument("--workload-class", default="single_prompt_short")
    append.add_argument("--model-id", default="qwen3-0.6b")
    append.add_argument("--model-quantization", default="q4")
    append.add_argument("--decode-max-tokens", type=int, default=16)
    append.add_argument("--decode-temperature", type=float, default=0.0)
    append.add_argument(
        "--prompt-set-hash",
        default="sha256:placeholder-prompt-set",
    )
    append.add_argument(
        "--serving-budget-bytes",
        type=int,
        default=6 * 1024 * 1024 * 1024,
    )
    append.add_argument(
        "--evidence-pointer",
        default="docs/source-of-truth/comparative-evidence-ledger.md#row-rejected",
    )
    append.add_argument("--runtime-version", default="0.0.0-runtime7")

    sub.add_parser("latest", help="Print the latest record or still_blocked payload")
    sub.add_parser("history", help="Print the full history envelope")

    args = parser.parse_args()
    ledger = ComparativeEvidenceLedger(args.ledger_path)

    if args.command == "append-rejected-record":
        payload = _append_rejected_record(
            ledger,
            host_class=args.host_class,
            workload_class=args.workload_class,
            model_id=args.model_id,
            model_quantization=args.model_quantization,
            decode_max_tokens=args.decode_max_tokens,
            decode_temperature=args.decode_temperature,
            prompt_set_hash=args.prompt_set_hash,
            serving_budget_bytes=args.serving_budget_bytes,
            evidence_pointer=args.evidence_pointer,
            runtime_version=args.runtime_version,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "latest":
        latest = ledger.latest()
        if latest is None:
            print(
                json.dumps(
                    still_blocked_payload(
                        missing_signal="no_comparative_evidence_record_appended",
                        ledger_path=str(ledger.path),
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        print(json.dumps(latest, indent=2, sort_keys=True))
        return 0

    if args.command == "history":
        records = ledger.history()
        envelope = history_envelope(
            records=records,
            ledger_status="available" if records else "empty",
        )
        print(json.dumps(envelope, indent=2, sort_keys=True))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
