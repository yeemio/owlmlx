from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "runtime_gemma4_mtp_resident_probe.py"


def _load_probe_module():
    spec = importlib.util.spec_from_file_location("runtime_gemma4_mtp_resident_probe", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _config(tmp_path: Path):
    probe = _load_probe_module()
    return probe.ProbeConfig(
        python_executable="/fake/python",
        target_path="/models/gemma-4-31B-it",
        draft_path="/models/gemma-4-31B-it-assistant",
        output_dir=tmp_path,
        max_tokens=8,
        request_count=3,
        draft_block_size=6,
        timeout_s=1.0,
    )


def test_inspection_without_resident_surface_blocks_local_runtime() -> None:
    probe = _load_probe_module()

    verdict, reasons = probe.classify_verdict(
        api_inspection={"ok": False, "errors": ["ImportError"]},
        probe_payload=None,
        request_count=3,
    )

    assert verdict == "blocked_on_local_runtime"
    assert reasons == ["resident_api_surface_unavailable"]


def test_successful_resident_probe_without_trim_is_append_only(tmp_path: Path) -> None:
    probe = _load_probe_module()
    row = probe.build_verdict_row(
        config=_config(tmp_path),
        api_inspection={"ok": True, "versions": {"mlx-vlm": "0.5.0"}},
        probe_payload={
            "ok": True,
            "versions": {"mlx-vlm": "0.5.0"},
            "target_load_count": 1,
            "draft_load_count": 1,
            "trim_calls": [],
            "requests": [
                {"ok": True, "speculative_summary": {"mean_accepted_tokens": 0, "rounds": 0}},
                {"ok": True, "speculative_summary": {"mean_accepted_tokens": 2.5, "rounds": 4}},
                {"ok": True, "speculative_summary": {"mean_accepted_tokens": 3.0, "rounds": 4}},
            ],
        },
    )

    assert row["verdict"] == "resident_viable_append_only"
    assert row["cache_regime"] == "append_only"
    assert row["used_for_promotion_gate"] is False
    assert row["capability_label"] == "experimental"
    assert row["mean_accepted_tokens"] == 2.75


def test_successful_resident_probe_with_trim_is_separate_verdict(tmp_path: Path) -> None:
    probe = _load_probe_module()
    row = probe.build_verdict_row(
        config=_config(tmp_path),
        api_inspection={"ok": True},
        probe_payload={
            "ok": True,
            "target_load_count": 1,
            "draft_load_count": 1,
            "trim_calls": [{"class": "RotatingKVCache", "n": 2}],
            "requests": [
                {"ok": True, "speculative_summary": {"mean_accepted_tokens": 1.0, "rounds": 1}},
                {"ok": True, "speculative_summary": {"mean_accepted_tokens": 2.0, "rounds": 2}},
                {"ok": True, "speculative_summary": {"mean_accepted_tokens": 2.0, "rounds": 2}},
            ],
        },
    )

    assert row["verdict"] == "resident_viable_with_trim"
    assert row["cache_regime"] == "trim"
    assert row["trim_attempted"] is True


def test_probe_failure_mentions_trim_maps_to_980_blocker() -> None:
    probe = _load_probe_module()

    verdict, reasons = probe.classify_verdict(
        api_inspection={"ok": True},
        probe_payload={
            "ok": False,
            "error": "RotatingKVCache is not trimmable",
            "requests": [],
        },
        request_count=3,
    )

    assert verdict == "blocked_on_980"
    assert reasons == ["hybrid_cache_or_trim_failure"]
