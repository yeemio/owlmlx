from scripts.bench import prefill_chunk_compare


def _row(
    *,
    model_id: str = "qwen3.6-27b-4bit",
    target_input_tokens: int = 4096,
    chunk_size: int,
    run_idx: int,
    output_hash: str,
) -> dict[str, object]:
    return {
        "model_id": model_id,
        "target_input_tokens": target_input_tokens,
        "chunk_size": chunk_size,
        "run_idx": run_idx,
        "output_byte_hash": output_hash,
        "verdict": "pass",
    }


def test_within_chunk_determinism_passes_when_each_chunk_repeats_identically() -> None:
    rows = [
        _row(chunk_size=512, run_idx=1, output_hash="a"),
        _row(chunk_size=512, run_idx=2, output_hash="a"),
        _row(chunk_size=2048, run_idx=1, output_hash="b"),
        _row(chunk_size=2048, run_idx=2, output_hash="b"),
    ]

    summary = prefill_chunk_compare._within_chunk_determinism_summary(rows)

    assert summary == {
        "gate": "required",
        "status": "passed",
        "total_groups": 2,
        "groups_with_repeated_runs": 2,
        "repeated_groups_with_identical_output": 2,
        "repeat_match_rate": 1.0,
    }


def test_within_chunk_determinism_reports_not_measured_for_single_runs() -> None:
    rows = [
        _row(chunk_size=512, run_idx=1, output_hash="a"),
        _row(chunk_size=2048, run_idx=1, output_hash="b"),
    ]

    summary = prefill_chunk_compare._within_chunk_determinism_summary(rows)

    assert summary["status"] == "not_measured"
    assert summary["groups_with_repeated_runs"] == 0
    assert summary["repeat_match_rate"] is None


def test_cross_chunk_consistency_is_informational_only() -> None:
    rows = [
        _row(chunk_size=512, run_idx=1, output_hash="a"),
        _row(chunk_size=2048, run_idx=1, output_hash="b"),
    ]

    summary = prefill_chunk_compare._cross_chunk_consistency_summary(rows)

    assert summary["gate"] == "informational_only"
    assert summary["match_rate"] == 0.0
    assert "does not gate B" in str(summary["note"])


def test_write_rollup_marks_progress_not_measured_without_long_prompt(tmp_path) -> None:
    rollup_path = tmp_path / "rollup.jsonl"
    rows = [
        {
            **_row(chunk_size=512, run_idx=1, output_hash="a"),
            "metrics": {"prefill_progress_event_count": 1},
        },
    ]

    prefill_chunk_compare._write_rollup(
        path=rollup_path,
        run_id="test-run",
        rows=rows,
    )

    [rollup] = rollup_path.read_text(encoding="utf-8").splitlines()
    assert '"progress_events_observable": null' in rollup
