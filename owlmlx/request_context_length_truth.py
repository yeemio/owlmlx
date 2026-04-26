"""Runtime-owned request context-length truth for admission decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from owlmlx.context_concurrency import (
    HIGH_CONTEXT_THRESHOLD_TOKENS,
    concurrency_gate_snapshot,
    gate_entry_for_context,
    is_high_context,
)


REQUEST_CONTEXT_LENGTH_TRUTH_SURFACE = "owlmlx.request_context_length_truth"
REQUEST_CONTEXT_LENGTH_TRUTH_VERSION = "v1"


@dataclass(frozen=True, slots=True)
class RequestContextLengthTruth:
    """Admission-focused context-length classification."""

    classification: str
    confidence: str
    reason_code: str
    reason_message: str
    context_tokens: int | None
    source: dict[str, Any]
    thresholds: dict[str, Any]
    policy_boundaries: dict[str, Any]
    missing_signals: tuple[dict[str, str], ...]


def _normalize_tokens(context_tokens: int | str | None) -> int | None:
    if context_tokens is None:
        return None
    if isinstance(context_tokens, bool):
        return None
    if isinstance(context_tokens, int):
        return context_tokens if context_tokens >= 0 else None
    if isinstance(context_tokens, str):
        stripped = context_tokens.strip()
        if not stripped:
            return None
        try:
            parsed = int(stripped)
        except ValueError:
            return None
        return parsed if parsed >= 0 else None
    return None


def _normalize_request_context_class(request_context_class: str | None) -> str | None:
    if request_context_class is None:
        return None
    normalized = request_context_class.strip().lower().replace("-", "_")
    if normalized in {"high", "high_context"}:
        return "high_context"
    if normalized in {"low", "short", "non_high", "non_high_context"}:
        return "non_high_context"
    if normalized == "unknown":
        return "unknown"
    return None


def build_request_context_length_truth(
    *,
    context_tokens: int | str | None = None,
    request_context_class: str | None = None,
) -> RequestContextLengthTruth:
    """Classify context length for admission without loading a tokenizer/model."""

    normalized_tokens = _normalize_tokens(context_tokens)
    normalized_class = _normalize_request_context_class(request_context_class)
    gate_snapshot = concurrency_gate_snapshot()
    thresholds = {
        "high_context_threshold_tokens": HIGH_CONTEXT_THRESHOLD_TOKENS,
        "high_context_rule": "context_tokens > high_context_threshold_tokens",
        "concurrency_gate": gate_snapshot.get("gate", {}),
    }

    if normalized_tokens is not None:
        high = is_high_context(normalized_tokens)
        classification = "high_context" if high else "non_high_context"
        return RequestContextLengthTruth(
            classification=classification,
            confidence="high",
            reason_code=(
                "explicit_context_tokens_above_high_context_threshold"
                if high
                else "explicit_context_tokens_at_or_below_high_context_threshold"
            ),
            reason_message=(
                "The request supplied an explicit runtime-visible context token count, "
                f"so admission can classify it as {classification}."
            ),
            context_tokens=normalized_tokens,
            source={
                "source_type": "explicit_context_tokens",
                "source_status": "supported",
                "request_context_class": normalized_class,
                "gate_entry": gate_entry_for_context(normalized_tokens),
                "exact_token_accounting": True,
                "tokenizer_invoked": False,
            },
            thresholds=thresholds,
            policy_boundaries={
                "policy_scope": "admission_support_only",
                "full_tokenizer_parity": False,
                "model_load_required": False,
                "character_estimation": False,
                "generation_enforcement": False,
            },
            missing_signals=(),
        )

    return RequestContextLengthTruth(
        classification="unknown",
        confidence="low",
        reason_code="context_tokens_missing",
        reason_message=(
            "No trustworthy runtime-visible context token count was supplied, so "
            "admission must keep request context length unknown."
        ),
        context_tokens=None,
        source={
            "source_type": "missing_context_tokens",
            "source_status": "insufficient_signal",
            "request_context_class": normalized_class,
            "gate_entry": None,
            "exact_token_accounting": False,
            "tokenizer_invoked": False,
        },
        thresholds=thresholds,
        policy_boundaries={
            "policy_scope": "admission_support_only",
            "full_tokenizer_parity": False,
            "model_load_required": False,
            "character_estimation": False,
            "generation_enforcement": False,
        },
        missing_signals=(
            {
                "layer": "request_context_length",
                "signal": "runtime_visible_context_tokens",
                "reason": "admission only classifies high-context requests when explicit token truth is supplied",
            },
        ),
    )


def request_context_length_truth_to_dict(
    truth: RequestContextLengthTruth,
) -> dict[str, Any]:
    """Serialize request context-length truth."""

    return {
        "contract": {
            "surface": REQUEST_CONTEXT_LENGTH_TRUTH_SURFACE,
            "version": REQUEST_CONTEXT_LENGTH_TRUTH_VERSION,
            "stable_sections": [
                "summary",
                "classification",
                "thresholds",
                "source",
                "policy_boundaries",
                "missing_signals",
            ],
        },
        "summary": {
            "classification": truth.classification,
            "confidence": truth.confidence,
            "context_tokens": truth.context_tokens,
        },
        "classification": {
            "context_classification": truth.classification,
            "confidence": truth.confidence,
            "reason_code": truth.reason_code,
            "reason_message": truth.reason_message,
        },
        "thresholds": truth.thresholds,
        "source": truth.source,
        "policy_boundaries": truth.policy_boundaries,
        "missing_signals": list(truth.missing_signals),
    }
