from __future__ import annotations

import json
from pathlib import Path

from scripts.bench import native_byte_equivalence


def _records(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def test_fake_native_byte_equivalence_writes_passing_b1a_record(tmp_path: Path) -> None:
    summary = native_byte_equivalence.run_native_byte_equivalence(
        output_dir=tmp_path,
        mode="fake",
    )

    assert summary["ok"] is True
    assert summary["verdict"] == "passed"
    assert summary["summary"] == {
        "total_prompts": 5,
        "utf8_equivalent_count": 5,
        "divergent_count": 0,
    }

    output_path = Path(str(summary["output_path"]))
    assert output_path.parent == tmp_path
    assert output_path.name.endswith("-b1a-gemma4-31b-it-byte-equiv-n5.jsonl")

    records = _records(output_path)
    assert len(records) == 1
    record = records[0]
    assert record["schema_version"] == "b1a.v1"
    assert record["gate"] == "B-1a"
    assert record["part"] == "B"
    assert record["verdict"] == "passed"
    assert record["divergence_diagnostic"] is None
    assert record["config"]["OWLMLX_SESSION_CACHE_ENABLED"] == "0"
    assert record["config"]["session_id_header_set"] is False
    assert record["config"]["max_tokens"] == 128
    assert record["config"]["temperature"] == 0.0
    assert record["config"]["seed"] == 42

    prompts = record["prompts"]
    assert [prompt["id"] for prompt in prompts] == ["p1", "p2", "p3", "p4", "p5"]
    assert {prompt["category"] for prompt in prompts} == {
        "short_factual_qa",
        "medium_technical_explanation",
        "long_context_qa",
        "code_completion",
        "single_prompt_multiturn_style",
    }
    for prompt in prompts:
        assert prompt["generated_text_utf8_equivalent"] is True
        assert prompt["first_byte_divergence_index"] is None
        assert prompt["token_ids_equivalent"] is None
        assert prompt["first_token_id_divergence_index"] is None
        assert prompt["native"]["token_ids"] is None
        assert prompt["subprocess"]["token_ids"] is None
        assert (
            prompt["native"]["generated_text_utf8_sha256"]
            == prompt["subprocess"]["generated_text_utf8_sha256"]
        )


def test_native_byte_equivalence_model_path_slug_uses_directory_name(
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "gemma-4-31B-it"
    model_dir.mkdir()

    summary = native_byte_equivalence.run_native_byte_equivalence(
        model_id=str(model_dir),
        output_dir=tmp_path / "evidence",
        mode="fake",
    )

    output_path = Path(str(summary["output_path"]))
    assert output_path.name.endswith("-b1a-gemma4-31b-it-byte-equiv-n5.jsonl")


def test_fake_native_byte_equivalence_records_divergence_diagnostic(
    tmp_path: Path,
) -> None:
    summary = native_byte_equivalence.run_native_byte_equivalence(
        output_dir=tmp_path,
        mode="fake",
        fake_diverge_prompt="p3",
    )

    assert summary["ok"] is False
    assert summary["verdict"] == "failed"
    assert summary["summary"] == {
        "total_prompts": 5,
        "utf8_equivalent_count": 4,
        "divergent_count": 1,
    }
    assert summary["divergence_diagnostic"]["first_failing_prompt"] == "p3"
    assert summary["divergence_diagnostic"]["suspected_root_cause"] == "sampler"

    record = _records(Path(str(summary["output_path"])))[0]
    p3 = next(prompt for prompt in record["prompts"] if prompt["id"] == "p3")
    assert p3["generated_text_utf8_equivalent"] is False
    assert isinstance(p3["first_byte_divergence_index"], int)
    assert p3["native"]["generated_text_utf8_sha256"] != (
        p3["subprocess"]["generated_text_utf8_sha256"]
    )
    diagnostic = record["divergence_diagnostic"]
    assert diagnostic["first_failing_prompt"] == "p3"
    assert diagnostic["first_byte_divergence_index"] == (
        p3["first_byte_divergence_index"]
    )
    assert diagnostic["native_byte_at_index"] != (
        diagnostic["subprocess_byte_at_index"]
    )


def test_native_byte_equivalence_cli_exit_code_follows_verdict(tmp_path: Path) -> None:
    ok_code = native_byte_equivalence.main(
        [
            "--mode",
            "fake",
            "--output",
            str(tmp_path / "pass"),
        ]
    )
    failed_code = native_byte_equivalence.main(
        [
            "--mode",
            "fake",
            "--fake-diverge-prompt",
            "p2",
            "--output",
            str(tmp_path / "fail"),
        ]
    )

    assert ok_code == 0
    assert failed_code == 1
