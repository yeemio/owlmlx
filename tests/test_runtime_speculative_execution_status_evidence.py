from __future__ import annotations

import json
from pathlib import Path

from scripts.runtime_speculative_execution_status_contract import (
    build_contract_evidence,
    write_contract_evidence,
)


def test_build_contract_evidence_covers_f1_fixture_set() -> None:
    ledger_rows, rollup = build_contract_evidence(
        timestamp_utc="20260525T000000Z",
        fresh_round_trips=20,
    )

    assert [row["fixture_label"] for row in ledger_rows] == [
        "spec_disabled",
        "assistant_drafter_loaded",
        "assistant_drafter_crashed",
        "runner_unloaded",
        "re_loaded_after_crash",
    ]
    assert rollup["schema_version"] == "f1.contract_rollup.v1"
    assert rollup["slice"] == "F1.3"
    assert rollup["fixture_count"] == 5
    assert rollup["all_fixtures_passed"] is True
    assert rollup["fresh_round_trips"] == 20
    assert rollup["fresh_round_trips_passed"] is True
    assert rollup["endpoint_self_promotion_eligible"] is True
    assert rollup["graduates"] == {
        "endpoint_supported": False,
        "any_method_supported": False,
    }


def test_contract_evidence_rows_are_passed_contract_fixtures() -> None:
    ledger_rows, _rollup = build_contract_evidence(
        timestamp_utc="20260525T000000Z",
        fresh_round_trips=20,
    )

    for row in ledger_rows:
        assert row["schema_version"] == "f1.contract_fixture.v1"
        assert row["record_type"] == "speculative_execution_status_contract_fixture"
        assert row["gate"] == "F-1"
        assert row["verdict"] == "passed"
        assert row["contract_assertions"] == {
            "surface_matches": True,
            "version_matches": True,
            "vocabulary_conformant": True,
            "invariants_hold": True,
        }
        assert row["payload"]["surface"] == "owlmlx.speculative_execution_status"
        assert row["payload"]["version"] == "v1"


def test_contract_evidence_captures_crash_and_reload_payloads() -> None:
    ledger_rows, _rollup = build_contract_evidence(
        timestamp_utc="20260525T000000Z",
        fresh_round_trips=20,
    )
    rows = {row["fixture_label"]: row for row in ledger_rows}

    crashed = rows["assistant_drafter_crashed"]["payload"]
    assert crashed["method"] == "assistant_drafter"
    assert crashed["capability_label"] == "experimental"
    assert crashed["runner_status"] == "error"
    assert crashed["missing_reason"] == "runner_crash"
    assert crashed["fallback"]["reason_code"] == "runner_crash"

    reloaded = rows["re_loaded_after_crash"]["payload"]
    assert reloaded["method"] == "assistant_drafter"
    assert reloaded["runner_status"] == "deferred_cli_per_request"
    assert reloaded.get("fallback") is None


def test_write_contract_evidence_writes_ledger_and_rollup_jsonl(tmp_path: Path) -> None:
    result = write_contract_evidence(
        output_dir=tmp_path,
        timestamp_utc="20260525T000000Z",
        fresh_round_trips=20,
    )

    ledger_path = tmp_path / "20260525T000000Z-f1-contract-fixtures.jsonl"
    rollup_path = tmp_path / "20260525T000000Z-f1-contract-fixtures-rollup.jsonl"
    assert result["ledger_path"] == str(ledger_path)
    assert result["rollup_path"] == str(rollup_path)

    ledger_rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    rollup_rows = [json.loads(line) for line in rollup_path.read_text().splitlines()]

    assert len(ledger_rows) == 5
    assert len(rollup_rows) == 1
    assert rollup_rows[0]["all_fixtures_passed"] is True
    assert rollup_rows[0]["endpoint_self_promotion_eligible"] is True
