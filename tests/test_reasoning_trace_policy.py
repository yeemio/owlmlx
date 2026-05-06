from __future__ import annotations

from owlmlx.reasoning_trace_policy import (
    REASONING_TRACE_POLICY_SURFACE,
    REASONING_TRACE_POLICY_VERSION,
    apply_reasoning_trace_policy,
)


def test_plain_text_is_safe_final_candidate() -> None:
    result = apply_reasoning_trace_policy(" OK. ")

    assert result.visible_reasoning_trace is False
    assert result.trace_status == "none"
    assert result.final_text == "OK."
    assert result.final_text_source == "plain_text"
    assert result.output_sanity_label == "valid_text"


def test_channel_thought_without_final_is_truncated_trace_not_final_text() -> None:
    result = apply_reasoning_trace_policy(
        "<|channel>thought\nPlan the answer.",
        finish_reason="length",
    )

    assert result.visible_reasoning_trace is True
    assert result.trace_marker_family == "channel"
    assert result.trace_status == "truncated"
    assert result.final_text is None
    assert result.output_sanity_label == "reasoning_trace_truncated"


def test_channel_final_can_yield_safe_final_candidate_without_hiding_trace() -> None:
    result = apply_reasoning_trace_policy(
        "<|channel>thought\nPlan.\n<|channel>final\nOne sentence.",
        finish_reason="stop",
    )

    assert result.visible_reasoning_trace is True
    assert result.trace_marker_family == "channel"
    assert result.trace_status == "visible"
    assert result.final_text == "One sentence."
    assert result.final_text_source == "channel_final"
    assert result.output_sanity_label == "reasoning_trace_visible"
    assert result.caveats


def test_gemma_closed_channel_boundary_can_yield_final_candidate() -> None:
    result = apply_reasoning_trace_policy(
        "<|channel>thought\nPlan.<channel|>\nOne sentence.<turn|>",
        finish_reason="stop",
    )

    assert result.visible_reasoning_trace is True
    assert result.trace_marker_family == "channel"
    assert result.trace_status == "visible"
    assert result.final_text == "One sentence."
    assert result.final_text_source == "post_channel_boundary"
    assert result.output_sanity_label == "reasoning_trace_visible"


def test_channel_final_marker_without_text_does_not_create_valid_text() -> None:
    result = apply_reasoning_trace_policy(
        "<|channel>thought\nPlan.\n<|channel>final\n",
        finish_reason="stop",
    )

    assert result.visible_reasoning_trace is True
    assert result.trace_status == "visible"
    assert result.final_text is None
    assert result.final_text_source is None
    assert result.output_sanity_label == "reasoning_trace_visible"


def test_closed_think_trace_can_yield_post_think_candidate() -> None:
    result = apply_reasoning_trace_policy(
        "<think>short plan</think>\nFinal answer.",
        finish_reason="stop",
    )

    assert result.visible_reasoning_trace is True
    assert result.trace_marker_family == "think_tag"
    assert result.trace_status == "visible"
    assert result.final_text == "Final answer."
    assert result.final_text_source == "post_think_text"
    assert result.output_sanity_label == "reasoning_trace_visible"


def test_closed_think_trace_with_length_keeps_final_candidate_with_caveat() -> None:
    result = apply_reasoning_trace_policy(
        "\n\n<think>\n\n</think>\n\nLocal AI runs on your own hardware,",
        finish_reason="length",
    )

    assert result.visible_reasoning_trace is True
    assert result.trace_marker_family == "think_tag"
    assert result.trace_status == "final_candidate_maybe_truncated"
    assert result.final_text == "Local AI runs on your own hardware,"
    assert result.final_text_source == "post_think_text_maybe_truncated"
    assert result.output_sanity_label == "reasoning_trace_final_length"
    assert result.caveats


def test_open_think_trace_is_truncated_not_stripped_to_valid_text() -> None:
    result = apply_reasoning_trace_policy(
        "\n\n<think>\nThinking Process:",
        finish_reason="length",
    )

    assert result.visible_reasoning_trace is True
    assert result.trace_marker_family == "think_tag"
    assert result.trace_status == "truncated"
    assert result.final_text is None
    assert result.output_sanity_label == "reasoning_trace_truncated"


def test_prose_thinking_process_without_final_marker_is_not_valid_text() -> None:
    result = apply_reasoning_trace_policy(
        "Here's a thinking process:\n\n1. Analyze the user request.",
        finish_reason="length",
    )

    assert result.visible_reasoning_trace is True
    assert result.trace_marker_family == "prose_thinking_process"
    assert result.trace_status == "truncated"
    assert result.final_text is None
    assert result.output_sanity_label == "reasoning_trace_truncated"


def test_prose_thinking_process_final_marker_yields_final_candidate() -> None:
    result = apply_reasoning_trace_policy(
        "Thinking Process:\nPlan.\n\nFinal answer: Local AI runs on your device.",
        finish_reason="stop",
    )

    assert result.visible_reasoning_trace is True
    assert result.trace_marker_family == "prose_thinking_process"
    assert result.trace_status == "visible"
    assert result.final_text == "Local AI runs on your device."
    assert result.final_text_source == "prose_final_answer"
    assert result.output_sanity_label == "reasoning_trace_visible"


def test_serialized_result_preserves_contract_surface() -> None:
    payload = apply_reasoning_trace_policy("OK.").to_dict()

    assert payload["surface"] == REASONING_TRACE_POLICY_SURFACE
    assert payload["version"] == REASONING_TRACE_POLICY_VERSION
    assert payload["visible_reasoning_trace"] is False
    assert payload["caveats"] == []
