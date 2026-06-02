"""Reasoning trace policy helpers for visible model-output traces."""

from __future__ import annotations

import re
from dataclasses import dataclass


REASONING_TRACE_POLICY_SURFACE = "owlmlx.reasoning_trace_policy"
REASONING_TRACE_POLICY_VERSION = "v1"

_CHANNEL_THOUGHT_RE = re.compile(r"<\|channel\>\s*thought\b", re.IGNORECASE)
_CHANNEL_FINAL_RE = re.compile(r"<\|channel\>\s*final\b", re.IGNORECASE)
_ESCAPED_FINAL_RE = re.compile(r"(?:^|\n)\s*\\final\b\s*", re.IGNORECASE)
_CHANNEL_CLOSE_RE = re.compile(r"<channel\|>", re.IGNORECASE)
_THINK_OPEN_RE = re.compile(r"<think\b[^>]*>", re.IGNORECASE)
_THINK_CLOSE_RE = re.compile(r"</think>", re.IGNORECASE)
_PROSE_THINKING_RE = re.compile(
    r"^\s*(?:here(?:'|’)?s\s+a\s+thinking\s+process|thinking\s+process)\s*:",
    re.IGNORECASE,
)
_FINAL_ANSWER_RE = re.compile(
    r"(?:^|\n)\s*(?:final\s+answer|answer)\s*:\s*",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReasoningTracePolicyResult:
    surface: str
    version: str
    visible_reasoning_trace: bool
    trace_marker_family: str | None
    trace_status: str
    final_text: str | None
    final_text_source: str | None
    output_sanity_label: str
    caveats: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "surface": self.surface,
            "version": self.version,
            "visible_reasoning_trace": self.visible_reasoning_trace,
            "trace_marker_family": self.trace_marker_family,
            "trace_status": self.trace_status,
            "final_text": self.final_text,
            "final_text_source": self.final_text_source,
            "output_sanity_label": self.output_sanity_label,
            "caveats": list(self.caveats),
        }


def apply_reasoning_trace_policy(
    text: str,
    *,
    finish_reason: str | None = None,
) -> ReasoningTracePolicyResult:
    """Route visible reasoning traces and expose only safe final-text candidates.

    This helper never treats text made only of stripped reasoning markers as
    valid final text. A final candidate is returned only when it is plainly
    outside a recognized visible trace boundary.
    """

    if not text.strip():
        return _result(
            visible_reasoning_trace=False,
            trace_marker_family=None,
            trace_status="none",
            final_text=None,
            final_text_source=None,
            output_sanity_label="empty_text",
            caveats=("empty output has no final-text candidate",),
        )

    channel_result = _analyze_channel_trace(text, finish_reason=finish_reason)
    if channel_result is not None:
        return channel_result

    escaped_final_result = _analyze_escaped_final_trace(
        text,
        finish_reason=finish_reason,
    )
    if escaped_final_result is not None:
        return escaped_final_result

    think_result = _analyze_think_trace(text, finish_reason=finish_reason)
    if think_result is not None:
        return think_result

    prose_thinking_result = _analyze_prose_thinking_trace(
        text,
        finish_reason=finish_reason,
    )
    if prose_thinking_result is not None:
        return prose_thinking_result

    return _result(
        visible_reasoning_trace=False,
        trace_marker_family=None,
        trace_status="none",
        final_text=text.strip(),
        final_text_source="plain_text",
        output_sanity_label="valid_text",
        caveats=(),
    )


def _analyze_channel_trace(
    text: str,
    *,
    finish_reason: str | None,
) -> ReasoningTracePolicyResult | None:
    thought_match = _CHANNEL_THOUGHT_RE.search(text)
    if thought_match is None:
        return None

    final_match = _CHANNEL_FINAL_RE.search(text, thought_match.end())
    if final_match is None:
        close_match = _CHANNEL_CLOSE_RE.search(text, thought_match.end())
        if close_match is not None and finish_reason != "length":
            final_text = _clean_candidate(text[close_match.end() :])
            if final_text is not None:
                return _result(
                    visible_reasoning_trace=True,
                    trace_marker_family="channel",
                    trace_status="visible",
                    final_text=final_text,
                    final_text_source="post_channel_boundary",
                    output_sanity_label="reasoning_trace_visible",
                    caveats=(
                        "Gemma-style channel thought was closed before final text",
                    ),
                )
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="channel",
            trace_status="truncated",
            final_text=None,
            final_text_source=None,
            output_sanity_label="reasoning_trace_truncated",
            caveats=("visible channel thought trace has no safe final channel",),
        )

    if finish_reason == "length":
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="channel",
            trace_status="truncated",
            final_text=None,
            final_text_source=None,
            output_sanity_label="reasoning_trace_truncated",
            caveats=("visible channel thought trace has no safe final channel",),
        )

    final_text = _clean_candidate(text[final_match.end() :])
    if final_text is None:
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="channel",
            trace_status="visible",
            final_text=None,
            final_text_source=None,
            output_sanity_label="reasoning_trace_visible",
            caveats=("final channel marker was present but final text was empty",),
        )

    return _result(
        visible_reasoning_trace=True,
        trace_marker_family="channel",
        trace_status="visible",
        final_text=final_text,
        final_text_source="channel_final",
        output_sanity_label="reasoning_trace_visible",
        caveats=("visible reasoning trace was routed separately from final text",),
    )


def _analyze_escaped_final_trace(
    text: str,
    *,
    finish_reason: str | None,
) -> ReasoningTracePolicyResult | None:
    matches = list(_ESCAPED_FINAL_RE.finditer(text))
    if not matches:
        return None

    final_match = matches[-1]
    if finish_reason == "length":
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="escaped_final_channel",
            trace_status="truncated",
            final_text=None,
            final_text_source=None,
            output_sanity_label="reasoning_trace_truncated",
            caveats=("escaped final channel marker may have truncated final text",),
        )

    final_text = _clean_candidate(text[final_match.end() :])
    if final_text is None:
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="escaped_final_channel",
            trace_status="visible",
            final_text=None,
            final_text_source=None,
            output_sanity_label="reasoning_trace_visible",
            caveats=("escaped final channel marker was present but final text was empty",),
        )

    return _result(
        visible_reasoning_trace=True,
        trace_marker_family="escaped_final_channel",
        trace_status="visible",
        final_text=final_text,
        final_text_source="escaped_final_channel",
        output_sanity_label="reasoning_trace_visible",
        caveats=("visible escaped final channel marker was routed to final text",),
    )


def _analyze_think_trace(
    text: str,
    *,
    finish_reason: str | None,
) -> ReasoningTracePolicyResult | None:
    open_match = _THINK_OPEN_RE.search(text)
    if open_match is None:
        hanging_close_match = _THINK_CLOSE_RE.search(text)
        if hanging_close_match is None:
            return None
        final_text = _clean_candidate(text[hanging_close_match.end() :])
        if final_text is None:
            return _result(
                visible_reasoning_trace=True,
                trace_marker_family="think_tag",
                trace_status="visible",
                final_text=None,
                final_text_source=None,
                output_sanity_label="reasoning_trace_visible",
                caveats=(
                    "hanging think close marker was present but final text was empty",
                ),
            )
        if finish_reason == "length":
            return _result(
                visible_reasoning_trace=True,
                trace_marker_family="think_tag",
                trace_status="final_candidate_maybe_truncated",
                final_text=final_text,
                final_text_source="post_hanging_think_close_text_maybe_truncated",
                output_sanity_label="reasoning_trace_final_length",
                caveats=(
                    "hanging think close marker left final text but finish_reason=length may be incomplete",
                ),
            )
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="think_tag",
            trace_status="visible",
            final_text=final_text,
            final_text_source="post_hanging_think_close_text",
            output_sanity_label="reasoning_trace_visible",
            caveats=(
                "hanging think close marker was treated as a prompt-opened reasoning trace boundary",
            ),
        )

    close_match = _THINK_CLOSE_RE.search(text, open_match.end())
    if close_match is None:
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="think_tag",
            trace_status="truncated",
            final_text=None,
            final_text_source=None,
            output_sanity_label="reasoning_trace_truncated",
            caveats=("visible think trace has no safe closing boundary",),
        )

    final_text = _clean_candidate(text[close_match.end() :])
    if final_text is None:
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="think_tag",
            trace_status="visible",
            final_text=None,
            final_text_source=None,
            output_sanity_label="reasoning_trace_visible",
            caveats=("closed think trace did not leave final text",),
        )

    if finish_reason == "length":
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="think_tag",
            trace_status="final_candidate_maybe_truncated",
            final_text=final_text,
            final_text_source="post_think_text_maybe_truncated",
            output_sanity_label="reasoning_trace_final_length",
            caveats=(
                "closed think trace left final text but finish_reason=length may be incomplete",
            ),
        )

    return _result(
        visible_reasoning_trace=True,
        trace_marker_family="think_tag",
        trace_status="visible",
        final_text=final_text,
        final_text_source="post_think_text",
        output_sanity_label="reasoning_trace_visible",
        caveats=("visible reasoning trace was routed separately from final text",),
    )


def _analyze_prose_thinking_trace(
    text: str,
    *,
    finish_reason: str | None,
) -> ReasoningTracePolicyResult | None:
    thinking_match = _PROSE_THINKING_RE.search(text)
    if thinking_match is None:
        return None

    final_match = _FINAL_ANSWER_RE.search(text, thinking_match.end())
    if final_match is None:
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="prose_thinking_process",
            trace_status="truncated" if finish_reason == "length" else "visible",
            final_text=None,
            final_text_source=None,
            output_sanity_label=(
                "reasoning_trace_truncated"
                if finish_reason == "length"
                else "reasoning_trace_visible"
            ),
            caveats=("visible prose thinking process has no safe final-answer marker",),
        )

    final_text = _clean_candidate(text[final_match.end() :])
    if final_text is None:
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="prose_thinking_process",
            trace_status="visible",
            final_text=None,
            final_text_source=None,
            output_sanity_label="reasoning_trace_visible",
            caveats=("final-answer marker was present but final text was empty",),
        )

    if finish_reason == "length":
        return _result(
            visible_reasoning_trace=True,
            trace_marker_family="prose_thinking_process",
            trace_status="final_candidate_maybe_truncated",
            final_text=final_text,
            final_text_source="prose_final_answer_maybe_truncated",
            output_sanity_label="reasoning_trace_final_length",
            caveats=(
                "prose thinking trace left final text but finish_reason=length may be incomplete",
            ),
        )

    return _result(
        visible_reasoning_trace=True,
        trace_marker_family="prose_thinking_process",
        trace_status="visible",
        final_text=final_text,
        final_text_source="prose_final_answer",
        output_sanity_label="reasoning_trace_visible",
        caveats=("visible prose reasoning trace was routed separately from final text",),
    )


def _clean_candidate(candidate: str) -> str | None:
    cleaned = candidate.strip()
    cleaned = re.sub(r"(?:<turn\|>|<eos>)\s*$", "", cleaned, flags=re.IGNORECASE).strip()
    if not cleaned:
        return None
    if _CHANNEL_THOUGHT_RE.search(cleaned) or _THINK_OPEN_RE.search(cleaned):
        return None
    return cleaned


def _result(
    *,
    visible_reasoning_trace: bool,
    trace_marker_family: str | None,
    trace_status: str,
    final_text: str | None,
    final_text_source: str | None,
    output_sanity_label: str,
    caveats: tuple[str, ...],
) -> ReasoningTracePolicyResult:
    return ReasoningTracePolicyResult(
        surface=REASONING_TRACE_POLICY_SURFACE,
        version=REASONING_TRACE_POLICY_VERSION,
        visible_reasoning_trace=visible_reasoning_trace,
        trace_marker_family=trace_marker_family,
        trace_status=trace_status,
        final_text=final_text,
        final_text_source=final_text_source,
        output_sanity_label=output_sanity_label,
        caveats=caveats,
    )
