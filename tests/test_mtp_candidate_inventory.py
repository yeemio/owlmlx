from __future__ import annotations

import json
from pathlib import Path

from scripts.bench.mtp_candidate_inventory import (
    build_inventory_row,
    classify_cache_family,
    classify_candidate,
    mtp_signals_from_config,
)


def test_mtp_signals_detect_text_config_native_mtp() -> None:
    config = {
        "model_type": "qwen3_5",
        "text_config": {
            "layer_types": ["linear_attention", "full_attention"],
            "mtp_num_hidden_layers": 1,
            "mtp_use_dedicated_embeddings": False,
        },
    }

    assert mtp_signals_from_config(config) == (
        "text_config.mtp_num_hidden_layers=1",
    )


def test_cache_family_marks_non_full_attention_as_hybrid() -> None:
    config = {
        "model_type": "qwen3_5",
        "text_config": {
            "layer_types": ["linear_attention", "full_attention"],
        },
    }

    family, reasons = classify_cache_family(config)

    assert family == "hybrid_or_trim_sensitive"
    assert "text_config.layer_types_non_full=linear_attention" in reasons


def test_cache_family_can_identify_config_only_full_attention() -> None:
    config = {
        "model_type": "candidate",
        "text_config": {
            "layer_types": ["full_attention", "full_attention"],
        },
    }

    family, reasons = classify_cache_family(config)

    assert family == "full_attention_config_only"
    assert reasons == ("text_config.layer_types_full_attention_only",)


def test_classifies_full_attention_native_mtp_as_next_probe_candidate(tmp_path: Path) -> None:
    config = {
        "model_type": "candidate",
        "architectures": ["CandidateForCausalLM"],
        "text_config": {
            "layer_types": ["full_attention"],
            "mtp_num_hidden_layers": 1,
        },
    }

    candidate = classify_candidate(path=tmp_path / "candidate", config=config, safetensors_count=2)

    assert candidate.candidate_kind == "native_mtp_full_attention_candidate"
    assert candidate.cache_family == "full_attention_config_only"
    assert candidate.next_action == "eligible_for_lightweight_native_mtp_admissibility_probe"


def test_classifies_gemma_assistant_as_pair_only_artifact(tmp_path: Path) -> None:
    config = {
        "model_type": "gemma4_assistant",
        "architectures": ["Gemma4AssistantForCausalLM"],
    }

    candidate = classify_candidate(path=tmp_path / "assistant", config=config, safetensors_count=1)

    assert candidate.candidate_kind == "assistant_drafter_artifact"
    assert candidate.cache_family == "unknown_from_config"
    assert "Gemma4 pair already covered by F-3.1" in candidate.next_action


def test_inventory_row_summarizes_absent_full_attention_candidate(tmp_path: Path) -> None:
    qwen = tmp_path / "qwen"
    qwen.mkdir()
    (qwen / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_5",
                "architectures": ["Qwen3_5ForConditionalGeneration"],
                "text_config": {
                    "layer_types": ["linear_attention", "full_attention"],
                    "mtp_num_hidden_layers": 1,
                },
            }
        ),
        encoding="utf-8",
    )

    row = build_inventory_row(roots=[tmp_path])

    assert row["schema_version"] == "f3.mtp_candidate_inventory.v1"
    assert row["summary"]["mtp_candidate_count"] == 1
    assert row["summary"]["native_mtp_full_attention_candidate_count"] == 0
    assert row["summary"]["full_attention_resident_mtp_next_target_available"] is False
    assert row["summary"]["capability_label"] == "experimental"
    assert row["summary"]["used_for_promotion_gate"] is False
