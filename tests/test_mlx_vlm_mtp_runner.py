from __future__ import annotations

import json
from pathlib import Path

from owlmlx.gemma4_mtp_drafter import MlxVlmToolchainInspection
from owlmlx.runtime.mlx_vlm_mtp_runner import MlxVlmMtpChildRunner


def _write_model_config(
    path: Path,
    *,
    model_type: str,
    architecture: str,
    is_assistant: bool | None = None,
    include_vision: bool = False,
) -> None:
    path.mkdir(parents=True)
    config = {
        "model_type": model_type,
        "architectures": [architecture],
        "text_config": {
            "model_type": "gemma4_text",
            "hidden_size": 1024 if is_assistant else 5376,
            "num_hidden_layers": 4 if is_assistant else 60,
            "vocab_size": 262144,
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


def _ready_toolchain(**_: object) -> MlxVlmToolchainInspection:
    return MlxVlmToolchainInspection(
        python_executable="/fake/python",
        returncode=0,
        flags_present=("--draft-model", "--draft-kind", "--draft-block-size"),
        flags_missing=(),
        stderr_excerpt="",
    )


def _fake_generate(**_: object) -> dict[str, object]:
    return {
        "ok": True,
        "returncode": 0,
        "elapsed_ms": 12.5,
        "stderr": "",
        "parsed": {
            "generated_text": "Local AI runs on your own machine.",
            "loaded_drafter": True,
            "speculative_summary": {
                "mean_accepted_tokens": 2.5,
                "rounds": 4,
            },
        },
    }


def test_runner_load_requires_draft_env(tmp_path: Path) -> None:
    target = tmp_path / "target"
    _write_model_config(
        target,
        model_type="gemma4",
        architecture="Gemma4ForConditionalGeneration",
        include_vision=True,
    )
    runner = MlxVlmMtpChildRunner(
        env={},
        python_executable="/fake/python",
        toolchain_inspector=_ready_toolchain,
    )

    result = runner.handle({"action": "load", "model_id": str(target)})[0]

    assert result["ok"] is False
    assert "OWLMLX_GEMMA4_MTP_DRAFT_MODEL" in result["error"]
    assert result["capability_label"] == "experimental"


def test_runner_load_validates_pair_and_records_experimental_metadata(tmp_path: Path) -> None:
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
    runner = MlxVlmMtpChildRunner(
        env={"OWLMLX_GEMMA4_MTP_DRAFT_MODEL": str(draft)},
        python_executable="/fake/python",
        toolchain_inspector=_ready_toolchain,
    )

    result = runner.handle({"action": "load", "model_id": str(target)})[0]

    assert result["ok"] is True
    assert result["runtime_family"] == "mlx-vlm-mtp"
    assert result["capability_label"] == "experimental"
    assert result["load_mode"] == "deferred_cli_per_request"
    assert runner.current_model_id == str(target)


def test_stream_generate_messages_emits_token_terminal_and_speculative_metadata(
    tmp_path: Path,
) -> None:
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
    runner = MlxVlmMtpChildRunner(
        env={"OWLMLX_GEMMA4_MTP_DRAFT_MODEL": str(draft)},
        python_executable="/fake/python",
        generate_func=_fake_generate,
        toolchain_inspector=_ready_toolchain,
    )
    assert runner.handle({"action": "load", "model_id": str(target)})[0]["ok"] is True

    events = runner.handle(
        {
            "action": "stream_generate_messages",
            "model_id": str(target),
            "messages": [{"role": "user", "content": "define local AI"}],
            "params": {"max_tokens": 16, "temperature": 0},
        }
    )

    assert events[0]["action"] == "stream_message_event"
    assert events[0]["event"] == "token"
    assert events[0]["text"] == "Local AI runs on your own machine."
    assert events[0]["speculative_summary"]["rounds"] == 4
    assert events[-1]["action"] == "stream_message_done"
    assert events[-1]["timing"]["surface"] == "owlmlx.child_stream_timing"
    assert events[-1]["capability_label"] == "experimental"
