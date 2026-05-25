#!/usr/bin/env python3
"""Capture F-1 speculative_execution_status contract evidence.

This is a status-surface evidence helper, not a benchmark. It drives a fresh
RuntimeKernel through the F-1.2 / F-1.3 contract fixtures and writes the payloads
returned by GET /v1/runtime/speculative-execution-status to the evidence layout
defined in docs/architect/design/F-1-spec.md section 7.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from owlmlx.host_pressure import host_pressure_not_sampled_snapshot
from owlmlx.runtime.backends import FakeBackend
from owlmlx.runtime.kernel import RuntimeKernel
from owlmlx.runtime.server import create_app
from owlmlx.runtime.speculative_execution_status import (
    SPECULATIVE_EXECUTION_STATUS_SURFACE,
    SPECULATIVE_EXECUTION_STATUS_VERSION,
)


F1_ROUTE = "/v1/runtime/speculative-execution-status"
DEFAULT_OUTPUT_DIR = Path("files/evidence/owlmlx/runtime/f1-speculative-execution-status")

_METHOD_VALUES = {"native_mtp", "assistant_drafter", "draft_model", "eagle", "ngram"}
_TOP_LEVEL_CAPABILITY_LABELS = {
    "not_implemented",
    "scaffold_only",
    "experimental",
    "partial",
    "supported",
    "disabled",
}
_METHOD_STATUS_VALUES = _TOP_LEVEL_CAPABILITY_LABELS - {"disabled"}
_RUNNER_STATUS_VALUES = {
    "unloaded",
    "loaded",
    "deferred_cli_per_request",
    "error",
}
_REASON_CODES = {
    "spec_explicitly_disabled",
    "method_not_implemented",
    "runner_not_loaded",
    "runner_load_failed",
    "mlx_vlm_toolchain_missing",
    "runner_crash",
    "mtp_weights_absent_or_stripped",
    "target_draft_pair_blocked",
}


def _timestamp_utc() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _fresh_client() -> tuple[TestClient, RuntimeKernel]:
    backend = FakeBackend()
    kernel = RuntimeKernel(
        backend,
        host_pressure_sampler=host_pressure_not_sampled_snapshot,
    )
    return TestClient(create_app(kernel)), kernel


def _route_payload(client: TestClient) -> dict[str, Any]:
    response = client.get(F1_ROUTE)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise TypeError("F-1 route returned a non-object payload")
    return payload


def _synthetic_load_success() -> dict[str, Any]:
    return {
        "ok": True,
        "action": "load",
        "model_id": "gemma-4-31B-it",
        "pid": 99999,
        "runtime_family": "mlx-vlm-mtp",
        "capability_label": "experimental",
        "load_mode": "deferred_cli_per_request",
        "draft_model_path": "/Users/test/models/gemma-4-31B-it-assistant-bf16",
        "draft_block_size": 6,
        "pair": {"ok": True, "blockers": []},
        "toolchain": {"ok": True, "flags_missing": []},
    }


def _synthetic_generate_success() -> dict[str, Any]:
    return {
        "ok": True,
        "action": "generate",
        "runtime_family": "mlx-vlm-mtp",
        "capability_label": "experimental",
        "returncode": 0,
        "text": "hello",
        "finish_reason": "stop",
        "generation_count": 1,
        "speculative_summary": {
            "mean_accepted_tokens": 1.5,
            "rounds": 8,
        },
    }


def _synthetic_generate_crash() -> dict[str, Any]:
    return {
        "ok": False,
        "action": "generate",
        "runtime_family": "mlx-vlm-mtp",
        "capability_label": "experimental",
        "returncode": 1,
        "stderr_excerpt": "fatal: drafter crashed",
    }


def _contract_assertions(payload: dict[str, Any]) -> dict[str, bool]:
    surface_matches = (
        payload.get("surface") == SPECULATIVE_EXECUTION_STATUS_SURFACE
    )
    version_matches = (
        payload.get("version") == SPECULATIVE_EXECUTION_STATUS_VERSION
    )
    vocabulary_conformant = _vocabulary_conformant(payload)
    invariants_hold = _invariants_hold(payload)
    return {
        "surface_matches": surface_matches,
        "version_matches": version_matches,
        "vocabulary_conformant": vocabulary_conformant,
        "invariants_hold": invariants_hold,
    }


def _vocabulary_conformant(payload: dict[str, Any]) -> bool:
    method = payload.get("method")
    if method is not None and method not in _METHOD_VALUES:
        return False
    if payload.get("capability_label") not in _TOP_LEVEL_CAPABILITY_LABELS:
        return False
    if payload.get("runner_status") not in _RUNNER_STATUS_VALUES:
        return False

    missing_reason = payload.get("missing_reason")
    if missing_reason is not None and missing_reason not in _REASON_CODES:
        return False

    fallback = payload.get("fallback")
    if fallback is not None:
        if not isinstance(fallback, dict):
            return False
        from_method = fallback.get("from_method")
        to_method = fallback.get("to_method")
        if from_method not in _METHOD_VALUES:
            return False
        if to_method is not None and to_method not in _METHOD_VALUES:
            return False
        if fallback.get("reason_code") not in _REASON_CODES:
            return False

    available = payload.get("available_methods")
    if not isinstance(available, list) or not available:
        return False
    for entry in available:
        if not isinstance(entry, dict):
            return False
        if set(entry) != {"method", "status", "notes"}:
            return False
        if entry["method"] not in _METHOD_VALUES:
            return False
        if entry["status"] not in _METHOD_STATUS_VALUES:
            return False
        if entry["notes"] is not None and not isinstance(entry["notes"], str):
            return False
    return True


def _invariants_hold(payload: dict[str, Any]) -> bool:
    method = payload.get("method")
    capability_label = payload.get("capability_label")
    runner_status = payload.get("runner_status")

    if capability_label == "disabled" and method is not None:
        return False
    if capability_label != "disabled" and method is None:
        return False
    if method is None and runner_status == "loaded":
        return False
    if runner_status == "error" and payload.get("missing_reason") is None:
        return False
    if runner_status == "error" and method is None and payload.get("fallback") is None:
        return False
    if payload.get("rejected_tokens", None) is not None:
        return False

    cache_sharing = payload.get("cache_sharing")
    if cache_sharing is not None:
        if not isinstance(cache_sharing, dict):
            return False
        if cache_sharing.get("writes_session_kv_cache") is not False:
            return False
    return True


def _fixture_row(
    *,
    fixture_label: str,
    payload: dict[str, Any],
    timestamp_utc: str,
) -> dict[str, Any]:
    assertions = _contract_assertions(payload)
    return {
        "schema_version": "f1.contract_fixture.v1",
        "record_type": "speculative_execution_status_contract_fixture",
        "gate": "F-1",
        "timestamp_utc": timestamp_utc,
        "fixture_label": fixture_label,
        "payload": payload,
        "contract_assertions": assertions,
        "verdict": "passed" if all(assertions.values()) else "failed",
    }


def _fresh_round_trips_pass(fresh_round_trips: int) -> bool:
    for _index in range(fresh_round_trips):
        client, _kernel = _fresh_client()
        payload = _route_payload(client)
        assertions = _contract_assertions(payload)
        if not all(assertions.values()):
            return False
    return True


def build_contract_evidence(
    *,
    timestamp_utc: str | None = None,
    fresh_round_trips: int = 20,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build F-1 contract fixture rows and a rollup row."""
    timestamp_utc = timestamp_utc or _timestamp_utc()
    rows: list[dict[str, Any]] = []

    client, _kernel = _fresh_client()
    rows.append(
        _fixture_row(
            fixture_label="spec_disabled",
            payload=_route_payload(client),
            timestamp_utc=timestamp_utc,
        )
    )

    client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    kernel.observe_speculative_runner_generate(_synthetic_generate_success())
    rows.append(
        _fixture_row(
            fixture_label="assistant_drafter_loaded",
            payload=_route_payload(client),
            timestamp_utc=timestamp_utc,
        )
    )

    client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    kernel.observe_speculative_runner_generate(_synthetic_generate_crash())
    rows.append(
        _fixture_row(
            fixture_label="assistant_drafter_crashed",
            payload=_route_payload(client),
            timestamp_utc=timestamp_utc,
        )
    )

    client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    kernel.observe_speculative_runner_generate(_synthetic_generate_success())
    kernel.observe_speculative_runner_unload()
    rows.append(
        _fixture_row(
            fixture_label="runner_unloaded",
            payload=_route_payload(client),
            timestamp_utc=timestamp_utc,
        )
    )

    client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    kernel.observe_speculative_runner_generate(_synthetic_generate_crash())
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    rows.append(
        _fixture_row(
            fixture_label="re_loaded_after_crash",
            payload=_route_payload(client),
            timestamp_utc=timestamp_utc,
        )
    )

    all_fixtures_passed = all(row["verdict"] == "passed" for row in rows)
    fresh_passed = _fresh_round_trips_pass(fresh_round_trips)
    promotion_eligible = (
        all_fixtures_passed
        and fresh_round_trips >= 20
        and fresh_passed
    )
    rollup = {
        "schema_version": "f1.contract_rollup.v1",
        "gate": "F-1",
        "timestamp_utc": timestamp_utc,
        "slice": "F1.3",
        "fixture_count": len(rows),
        "all_fixtures_passed": all_fixtures_passed,
        "fresh_round_trips": fresh_round_trips,
        "fresh_round_trips_passed": fresh_passed,
        "endpoint_self_promotion_eligible": promotion_eligible,
        "graduates": {
            "endpoint_supported": False,
            "any_method_supported": False,
        },
    }
    return rows, rollup


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            handle.write("\n")


def write_contract_evidence(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    timestamp_utc: str | None = None,
    fresh_round_trips: int = 20,
) -> dict[str, Any]:
    timestamp_utc = timestamp_utc or _timestamp_utc()
    rows, rollup = build_contract_evidence(
        timestamp_utc=timestamp_utc,
        fresh_round_trips=fresh_round_trips,
    )
    ledger_path = output_dir / f"{timestamp_utc}-f1-contract-fixtures.jsonl"
    rollup_path = output_dir / f"{timestamp_utc}-f1-contract-fixtures-rollup.jsonl"
    _write_jsonl(ledger_path, rows)
    _write_jsonl(rollup_path, [rollup])
    return {
        "ledger_path": str(ledger_path),
        "rollup_path": str(rollup_path),
        "fixture_count": len(rows),
        "all_fixtures_passed": rollup["all_fixtures_passed"],
        "fresh_round_trips": rollup["fresh_round_trips"],
        "fresh_round_trips_passed": rollup["fresh_round_trips_passed"],
        "endpoint_self_promotion_eligible": rollup[
            "endpoint_self_promotion_eligible"
        ],
        "graduates": rollup["graduates"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write F-1 speculative_execution_status contract evidence.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Evidence output directory.",
    )
    parser.add_argument(
        "--timestamp",
        default=None,
        help="Override timestamp prefix, e.g. 20260525T000000Z.",
    )
    parser.add_argument(
        "--fresh-round-trips",
        type=int,
        default=20,
        help="Number of fresh default endpoint round trips to require.",
    )
    args = parser.parse_args(argv)

    result = write_contract_evidence(
        output_dir=args.output_dir,
        timestamp_utc=args.timestamp,
        fresh_round_trips=args.fresh_round_trips,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_fixtures_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
