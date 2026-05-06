"""Reasoning trace policy helpers for visible model-output traces."""

from __future__ import annotations

import re
from dataclasses import dataclass


REASONING_TRACE_POLICY_SURFACE = "owlmlx.reasoning_trace_policy"
REASONING_TRACE_POLICY_VERSION = "v1"

_CHANNEL_THOUGHT_RE = re.compile(r"<\|channel\>\s*thought\b", re.IGNORECASE)
_CHANNEL_FINAL_RE = re.compile(r"<\|channel\>\s*final\b", re.IGNORECASE)
_CHANNEL_CLOSE_RE = re.compile(r"<channel\|>", re.IGNORECASE)
_THINK_OPEN_RE = re.compile(r"<think\b[^>]*>", re.IGNORECASE)
_THINK_CLOSE_RE = re.compile(r"</think>", re.IGNORECASE)


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

    think_result = _analyze_think_trace(text, finish_reason=finish_reason)
    if think_result is not None:
        return think_result

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


def _analyze_think_trace(
    text: str,
    *,
    finish_reason: str | None,
) -> ReasoningTracePolicyResult | None:
    open_match = _THINK_OPEN_RE.search(text)
    if open_match is None:
        return None

    close_match = _THINK_CLOSE_RE.search(text, open_match.end())
    if close_match is None or finish_reason == "length":
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

    return _result(
        visible_reasoning_trace=True,
        trace_marker_family="think_tag",
        trace_status="visible",
        final_text=final_text,
        final_text_source="post_think_text",
        output_sanity_label="reasoning_trace_visible",
        caveats=("visible reasoning trace was routed separately from final text",),
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
