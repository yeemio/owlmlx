from __future__ import annotations

from scripts.replacement import r4_ops_cutover_pilot as pilot


def test_module_imports_and_exposes_constants() -> None:
    assert pilot.DEFAULT_BASE_URL == "http://127.0.0.1:8066"
    assert pilot.EVIDENCE_SURFACE == "owlmlx.replacement.r4_ops_cutover_pilot"
    assert pilot.TOOL_LANE_SUBGATES == (
        "tool_call_emitted",
        "tool_call_executed",
        "tool_result_roundtrip",
        "final_answer_after_tool",
    )
