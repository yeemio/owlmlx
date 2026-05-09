from __future__ import annotations

import json
from pathlib import Path

from owlmlx.gemma4_mtp_drafter import (
    GEMMA4_MTP_CAPABILITY_LABEL,
    build_mlx_vlm_generate_argv,
    build_mlx_vlm_mtp_generate_argv,
    classify_mlx_vlm_help_text,
    inspect_gemma4_mtp_pair,
    parse_mlx_vlm_generate_output,
    parse_speculative_summary,
    readiness_payload,
)


def _write_model_config(
    path: Path,
    *,
    model_type: str,
    architecture: str,
    text_model_type: str = "gemma4_text",
    vocab_size: int = 262144,
    is_assistant: bool | None = None,
    include_vision: bool = False,
) -> None:
    path.mkdir(parents=True)
    config = {
        "model_type": model_type,
        "architectures": [architecture],
        "text_config": {
            "model_type": text_model_type,
            "hidden_size": 1024 if is_assistant else 5376,
            "num_hidden_layers": 4 if is_assistant else 60,
            "vocab_size": vocab_size,
        },
    }
    if include_vision:
        config["vision_config"] = {"model_type": "gemma4_vision"}
    (path / "config.json").write_text(json.dumps(config), encoding="utf-8")
    if is_assistant is not None:
        (path / "generation_config.json").write_text(
            json.dumps({"is_assistant": is_assistant}),
            encoding="utf-8",
        )


def test_gemma4_target_and_assistant_pair_is_experimental_ready(tmp_path: Path) -> None:
    target = tmp_path / "gemma-4-31B-it"
    draft = tmp_path / "gemma-4-31B-it-assistant"
    _write_model_config(
        target,
        model_type="gemma4",
        architecture="Gemma4ForConditionalGeneration",
        include_vision=True,
    )
    _write_model_config(
        draft,
        model_type="gemma4_assistant",
        architecture="Gemma4AssistantForCausalLM",
        is_assistant=True,
    )

    inspection = inspect_gemma4_mtp_pair(target_path=target, draft_path=draft)
    payload = inspection.to_dict()

    assert inspection.ok is True
    assert payload["capability_label"] == GEMMA4_MTP_CAPABILITY_LABEL
    assert payload["status"] == "ready"
    assert payload["draft_model_is_standalone_target"] is False


def test_pair_rejects_assistant_as_target(tmp_path: Path) -> None:
    target = tmp_path / "assistant-as-target"
    draft = tmp_path / "assistant"
    _write_model_config(
        target,
        model_type="gemma4_assistant",
        architecture="Gemma4AssistantForCausalLM",
        is_assistant=True,
    )
    _write_model_config(
        draft,
        model_type="gemma4_assistant",
        architecture="Gemma4AssistantForCausalLM",
        is_assistant=True,
    )

    inspection = inspect_gemma4_mtp_pair(target_path=target, draft_path=draft)

    assert inspection.ok is False
    assert "target_model_type_not_gemma4" in inspection.blockers
    assert "target_architecture_not_gemma4_conditional_generation" in inspection.blockers


def test_pair_rejects_vocab_mismatch(tmp_path: Path) -> None:
    target = tmp_path / "target"
    draft = tmp_path / "draft"
    _write_model_config(
        target,
        model_type="gemma4",
        architecture="Gemma4ForConditionalGeneration",
        vocab_size=262144,
        include_vision=True,
    )
    _write_model_config(
        draft,
        model_type="gemma4_assistant",
        architecture="Gemma4AssistantForCausalLM",
        vocab_size=128,
        is_assistant=True,
    )

    inspection = inspect_gemma4_mtp_pair(target_path=target, draft_path=draft)

    assert inspection.ok is False
    assert "target_draft_vocab_size_mismatch" in inspection.blockers


def test_classify_mlx_vlm_help_requires_all_mtp_flags() -> None:
    classified = classify_mlx_vlm_help_text(
        "--model MODEL --draft-model DRAFT --draft-kind KIND --draft-block-size N"
    )

    assert classified["missing"] == ()
    assert classified["present"] == (
        "--draft-model",
        "--draft-kind",
        "--draft-block-size",
    )


def test_command_builder_uses_module_cli_and_mtp_flags() -> None:
    argv = build_mlx_vlm_mtp_generate_argv(
        python_executable="/venv/bin/python",
        target_path="/models/gemma",
        draft_path="/drafts/gemma-assistant",
        prompt="hello",
        max_tokens=48,
        temperature=0,
        draft_block_size=6,
    )

    assert argv[:4] == ("/venv/bin/python", "-m", "mlx_vlm", "generate")
    assert "--draft-model" in argv
    assert "--draft-kind" in argv
    assert "mtp" in argv
    assert "--draft-block-size" in argv
    assert "--verbose" in argv


def test_command_builder_can_disable_drafter_for_ab_reference() -> None:
    argv = build_mlx_vlm_generate_argv(
        python_executable="/venv/bin/python",
        target_path="/models/gemma",
        prompt="hello",
        max_tokens=48,
        temperature=0,
        draft_path=None,
    )

    assert argv[:4] == ("/venv/bin/python", "-m", "mlx_vlm", "generate")
    assert "--draft-model" not in argv
    assert "--draft-kind" not in argv
    assert "--draft-block-size" not in argv


def test_parse_speculative_summary() -> None:
    summary = parse_speculative_summary(
        "Speculative decoding: 2.86 accepted tokens over 7 rounds"
    )

    assert summary is not None
    assert summary.mean_accepted_tokens == 2.86
    assert summary.rounds == 7


def test_parse_mlx_vlm_output_removes_control_lines() -> None:
    payload = parse_mlx_vlm_generate_output(
        stdout_text=(
            "/tmp/site-packages/transformers/audio_utils.py:549: UserWarning\n"
            "Loading drafter (mtp): /draft\n"
            "Local AI refers to local models.\n"
            "Speculative decoding: 2.86 accepted tokens over 7 rounds\n"
            "       21.47 real         2.46 user        22.11 sys\n"
        )
    )

    assert payload["loaded_drafter"] is True
    assert payload["generated_text"] == "Local AI refers to local models."
    assert payload["speculative_summary"] == {
        "mean_accepted_tokens": 2.86,
        "rounds": 7,
    }


def test_readiness_payload_stays_experimental_without_toolchain(tmp_path: Path) -> None:
    target = tmp_path / "target"
    draft = tmp_path / "draft"
    _write_model_config(
        target,
        model_type="gemma4",
        architecture="Gemma4ForConditionalGeneration",
        include_vision=True,
    )
    _write_model_config(
        draft,
        model_type="gemma4_assistant",
        architecture="Gemma4AssistantForCausalLM",
        is_assistant=True,
    )

    payload = readiness_payload(target_path=target, draft_path=draft)

    assert payload["ok"] is True
    assert payload["capability_label"] == "experimental"
