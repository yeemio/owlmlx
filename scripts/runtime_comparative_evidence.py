#!/usr/bin/env python3
"""Operator entry for the runtime-owned comparative-evidence record surface.

Subcommands:

- ``append-rejected-record``: append one honest ``verdict_grade=rejected``
  record. Used when reference runtimes (``oMLX`` / ``vMLX``) cannot be
  invoked on the current host. This is real v1 data, not synthetic
  ``measured`` data; it satisfies harness contract section 5.4.
- ``run-measured-short-prompt``: run two repeat attempts each against
  ``owlmlx`` and one reference runtime through caller-supplied subprocess
  argv, collect throughput / first-token latency / peak RSS / wall-clock,
  write raw artifacts, and append exactly one validated
  ``comparative_evidence_record`` whose ``verdict_grade`` is one of
  ``measured`` / ``inconclusive`` / ``rejected`` per the harness contract.
- ``import-manifest-record``: import a previously written manifest's validated
  ``appended_record`` into the selected cumulative ledger.
- ``latest``: print the latest record (or the explicit ``still_blocked``
  payload when no record exists).
- ``history``: print the full history envelope.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from owlmlx.comparative_evidence_history import (
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


def _prompt_set_hash(path: str) -> str:
    import hashlib
    data = Path(path).read_bytes()
    return "sha256:" + hashlib.sha256(data).hexdigest()


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


def _run_measured_short_prompt(
    *,
    ledger: ComparativeEvidenceLedger,
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Execute the measured short-prompt run and append exactly one record.

    Workflow:

    1. load runner config (owlmlx + reference) from JSON
    2. run ``--repeats`` attempts per runtime, writing per-attempt artifacts
    3. aggregate attempts into runtime-level measurements
    4. compute ``verdict_grade`` per the harness contract
    5. write manifest.json / commands.json / summary.md
    6. append one validated v1 record to the ledger
    7. return the appended record
    """

    from owlmlx.comparative_evidence_runner import (
        WorkloadInputs,
        aggregate_runtime,
        aggregate_to_record_runtime,
        compute_verdict,
        execute_attempt,
        load_runner_config_file,
        write_run_artifacts,
    )

    workload = WorkloadInputs(
        prompt=args.prompt,
        decode_max_tokens=int(args.decode_max_tokens),
        decode_temperature=float(args.decode_temperature),
        model_id=args.model_id,
        model_path=args.model_path,
        model_quantization=args.model_quantization,
        prompt_set_hash=args.prompt_set_hash,
        serving_budget_bytes=int(args.serving_budget_bytes),
        workload_class=args.workload_class,
    )
    repeats = max(1, int(args.repeats))

    owlmlx_cfg, reference_cfg = load_runner_config_file(args.runner_config)

    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    started_at = _now_iso_utc()

    runtime_aggregates = []
    for cfg in (owlmlx_cfg, reference_cfg):
        attempts = []
        for index in range(repeats):
            attempts.append(
                execute_attempt(
                    runtime_config=cfg,
                    workload=workload,
                    attempt_index=index + 1,
                    artifact_dir=evidence_dir,
                )
            )
        runtime_aggregates.append(aggregate_runtime(runtime_config=cfg, attempts=attempts))

    completed_at = _now_iso_utc()

    verdict_grade, verdict_text = compute_verdict(
        aggregates=runtime_aggregates,
        expected_repeats=repeats,
        workload=workload,
        host_class=args.host_class,
    )

    evidence_pointer = args.evidence_pointer or str(evidence_dir / "manifest.json")

    runtime_payload = tuple(
        aggregate_to_record_runtime(agg) for agg in runtime_aggregates
    )

    record = build_comparative_evidence_record(
        recorded_at=_now_iso_utc(),
        evidence_pointer=evidence_pointer,
        host_class=args.host_class,
        workload_class=workload.workload_class,
        workload_invariants={
            "model_id": workload.model_id,
            "model_quantization": workload.model_quantization,
            "decode_max_tokens": workload.decode_max_tokens,
            "decode_temperature": workload.decode_temperature,
            "prompt_set_hash": workload.prompt_set_hash,
            "serving_budget_bytes": workload.serving_budget_bytes,
        },
        runtimes=runtime_payload,
        verdict_text=verdict_text,
        verdict_grade=verdict_grade,
    )
    appended = ledger.append(record)

    write_run_artifacts(
        artifact_dir=evidence_dir,
        workload=workload,
        runtime_configs=(owlmlx_cfg, reference_cfg),
        aggregates=runtime_aggregates,
        repeats=repeats,
        host_class=args.host_class,
        verdict_grade=verdict_grade,
        verdict_text=verdict_text,
        ledger_path=ledger.path,
        appended_record=appended,
        started_at=started_at,
        completed_at=completed_at,
    )

    return appended


def _run_measured_multi_turn(
    *,
    ledger: ComparativeEvidenceLedger,
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Execute the measured multi-turn serial run and append exactly one record.

    The driver reads the prompt-set file itself (via the runner-config argv).
    Here ``prompt`` carries the path so ``{prompt}`` substitution stays valid,
    and the hash is computed from the file for honest reproducibility.
    """
    args.prompt = args.prompt_set
    args.prompt_set_hash = _prompt_set_hash(args.prompt_set)
    if not getattr(args, "workload_class", None):
        args.workload_class = "multi_prompt_serial"
    return _run_measured_short_prompt(ledger=ledger, args=args)


def _import_manifest_record(
    *,
    ledger: ComparativeEvidenceLedger,
    manifest_path: Path,
    allow_duplicate: bool = False,
) -> dict[str, Any]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    record_payload = payload.get("appended_record")
    if not isinstance(record_payload, dict):
        raise ValueError("manifest must contain object field appended_record")

    evidence_pointer = str(record_payload.get("evidence_pointer") or "")
    if not evidence_pointer:
        raise ValueError("manifest appended_record must contain evidence_pointer")
    if not allow_duplicate:
        for existing in ledger.history():
            if existing.get("evidence_pointer") == evidence_pointer:
                raise ValueError(
                    f"comparative evidence record already imported: {evidence_pointer}"
                )

    record = build_comparative_evidence_record(
        recorded_at=str(record_payload["recorded_at"]),
        evidence_pointer=evidence_pointer,
        host_class=str(record_payload["host_class"]),
        workload_class=str(record_payload["workload_class"]),
        workload_invariants=record_payload["workload_invariants"],
        runtimes=record_payload["runtimes"],
        verdict_text=str(record_payload["verdict_text"]),
        verdict_grade=str(record_payload["verdict_grade"]),
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

    measured = sub.add_parser(
        "run-measured-short-prompt",
        help=(
            "Run two repeat short-prompt attempts each against owlmlx and one "
            "reference runtime, collect raw measurements/artifacts, and append "
            "one validated comparative_evidence_record (measured / inconclusive / rejected)"
        ),
    )
    measured.add_argument("--evidence-dir", required=True)
    measured.add_argument("--runner-config", required=True)
    measured.add_argument("--host-class", required=True)
    measured.add_argument("--workload-class", default="single_prompt_short")
    measured.add_argument("--model-id", required=True)
    measured.add_argument("--model-path", required=True)
    measured.add_argument("--model-quantization", default="full_precision_unquantized")
    measured.add_argument("--prompt", required=True)
    measured.add_argument("--prompt-set-hash", required=True)
    measured.add_argument("--decode-max-tokens", type=int, default=2)
    measured.add_argument("--decode-temperature", type=float, default=0.0)
    measured.add_argument(
        "--serving-budget-bytes", type=int, default=85899345920
    )
    measured.add_argument("--repeats", type=int, default=2)
    measured.add_argument(
        "--evidence-pointer",
        default=None,
        help="Defaults to the manifest.json path inside --evidence-dir",
    )

    multi = sub.add_parser(
        "run-measured-multi-turn",
        help="Run multi-turn serial attempts (owlmlx warm + reference) and append one record",
    )
    multi.add_argument("--evidence-dir", required=True)
    multi.add_argument("--runner-config", required=True)
    multi.add_argument("--host-class", required=True)
    multi.add_argument("--workload-class", default="multi_prompt_serial")
    multi.add_argument("--model-id", required=True)
    multi.add_argument("--model-path", required=True)
    multi.add_argument("--model-quantization", default="full_precision_unquantized")
    multi.add_argument("--prompt-set", required=True)
    multi.add_argument("--decode-max-tokens", type=int, default=128)
    multi.add_argument("--decode-temperature", type=float, default=0.0)
    multi.add_argument("--serving-budget-bytes", type=int, default=85899345920)
    multi.add_argument("--repeats", type=int, default=5)
    multi.add_argument("--evidence-pointer", default=None)

    import_manifest = sub.add_parser(
        "import-manifest-record",
        help=(
            "Import a previously written comparative manifest appended_record "
            "into the selected JSONL ledger"
        ),
    )
    import_manifest.add_argument("--manifest-path", required=True)
    import_manifest.add_argument(
        "--allow-duplicate",
        action="store_true",
        help="Append even when the evidence_pointer already exists in the ledger.",
    )

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

    if args.command == "run-measured-short-prompt":
        payload = _run_measured_short_prompt(ledger=ledger, args=args)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "run-measured-multi-turn":
        payload = _run_measured_multi_turn(ledger=ledger, args=args)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "import-manifest-record":
        payload = _import_manifest_record(
            ledger=ledger,
            manifest_path=Path(args.manifest_path),
            allow_duplicate=args.allow_duplicate,
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
