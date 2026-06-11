"""owlmlx-owned model-family profile resolver.

The profile layer is deliberately configuration-only. It records the runtime
defaults and caveats that should travel with model evidence without importing
or vendoring peer-runtime implementation code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


MODEL_PROFILE_SURFACE = "owlmlx.model_profile"
MODEL_PROFILE_VERSION = "v1"


@dataclass(frozen=True)
class ModelProfile:
    profile_id: str
    profile_family: str
    model_id_patterns: tuple[str, ...]
    chat_template_kwargs: dict[str, Any]
    stop_token_strings: tuple[str, ...]
    sampler_defaults: dict[str, Any]
    reasoning_parser_family: str
    thinking_policy: dict[str, Any]
    cache_policy: dict[str, Any]
    profile_caveats: tuple[str, ...]
    source_basis: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": MODEL_PROFILE_SURFACE,
            "version": MODEL_PROFILE_VERSION,
            "profile_id": self.profile_id,
            "profile_family": self.profile_family,
            "model_id_patterns": list(self.model_id_patterns),
            "chat_template_kwargs": dict(self.chat_template_kwargs),
            "stop_token_strings": list(self.stop_token_strings),
            "sampler_defaults": dict(self.sampler_defaults),
            "reasoning_parser_family": self.reasoning_parser_family,
            "thinking_policy": dict(self.thinking_policy),
            "cache_policy": dict(self.cache_policy),
            "profile_caveats": list(self.profile_caveats),
            "source_basis": list(self.source_basis),
        }


def _profile(
    *,
    profile_id: str,
    profile_family: str,
    model_id_patterns: tuple[str, ...],
    chat_template_kwargs: dict[str, Any],
    stop_token_strings: tuple[str, ...],
    sampler_defaults: dict[str, Any],
    reasoning_parser_family: str,
    thinking_policy: dict[str, Any],
    cache_policy: dict[str, Any],
    profile_caveats: tuple[str, ...],
    source_basis: tuple[str, ...],
) -> ModelProfile:
    return ModelProfile(
        profile_id=profile_id,
        profile_family=profile_family,
        model_id_patterns=model_id_patterns,
        chat_template_kwargs=chat_template_kwargs,
        stop_token_strings=stop_token_strings,
        sampler_defaults=sampler_defaults,
        reasoning_parser_family=reasoning_parser_family,
        thinking_policy=thinking_policy,
        cache_policy=cache_policy,
        profile_caveats=profile_caveats,
        source_basis=source_basis,
    )


_PROFILES: dict[str, ModelProfile] = {
    "qwen3_6_text": _profile(
        profile_id="qwen3_6_text",
        profile_family="qwen3.6",
        model_id_patterns=(r"\bqwen3[._-]?6\b.*\b27b\b",),
        chat_template_kwargs={"enable_thinking": False},
        stop_token_strings=("<|im_end|>",),
        sampler_defaults={"temperature": 0.0, "top_p": 1.0},
        reasoning_parser_family="qwen",
        thinking_policy={
            "default_mode": "final_answer_default_disable_thinking",
            "diagnostic_mode": "set enable_thinking=True only for reasoning-workload probes",
            "budget_policy": "disabled_for_default_final_answer_profile",
            "reasoning_trace_policy": "owlmlx.reasoning_trace_policy:v1",
            "final_text_candidate_policy": "closed_think_or_final_marker_only",
        },
        cache_policy={
            "prefix_cache": "allowed_with_runtime_evidence",
            "cache_caveat": "profile does not prove cache acceleration safety",
        },
        profile_caveats=(
            "Qwen text profile carries final-answer template defaults only.",
            "Decode-speed diagnosis still needs direct same-prompt comparison evidence.",
        ),
        source_basis=(
            "docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md",
            "docs/source-of-truth/model-release-candidate-program.md",
        ),
    ),
    "qwen3_6_moe": _profile(
        profile_id="qwen3_6_moe",
        profile_family="qwen3.6_moe",
        model_id_patterns=(r"\bqwen3[._-]?6\b.*\b35b\b.*\ba3b\b",),
        chat_template_kwargs={"enable_thinking": False},
        stop_token_strings=("<|im_end|>",),
        sampler_defaults={"temperature": 0.0, "top_p": 1.0},
        reasoning_parser_family="qwen",
        thinking_policy={
            "default_mode": "final_answer_default_disable_thinking",
            "diagnostic_mode": "set enable_thinking=True only for reasoning-workload probes",
            "template_caveat": "thinking tokens may consume short generation budget",
            "budget_policy": "disabled_for_default_final_answer_profile",
            "reasoning_trace_policy": "owlmlx.reasoning_trace_policy:v1",
            "final_text_candidate_policy": "closed_think_or_final_marker_only",
        },
        cache_policy={
            "prefix_cache": "allowed_with_runtime_evidence",
            "prefill_caveat": "high TTFT must be measured separately from decode",
        },
        profile_caveats=(
            "Qwen MoE profile disables think-in-template behavior for final-answer probes.",
            "Diagnostic reasoning probes must opt in to thinking separately.",
        ),
        source_basis=(
            "docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md",
            "docs/source-of-truth/release-readiness-execution-plan.md",
        ),
    ),
    "gemma4_text": _profile(
        profile_id="gemma4_text",
        profile_family="gemma4",
        model_id_patterns=(
            r"\bgemma\b.*\b4\b.*\b12b\b.*\bit\b",
            r"\bgemma\b.*\b4\b.*\b31b\b.*\bit\b",
        ),
        chat_template_kwargs={"enable_thinking": False},
        stop_token_strings=("<eos>", "<turn|>"),
        sampler_defaults={
            "temperature": 0.0,
            "top_p": 1.0,
            "repetition_penalty_probe": "recommended",
        },
        reasoning_parser_family="gemma4",
        thinking_policy={
            "default_mode": "parser_cleanup_required",
            "channel_policy": "strip_or_route_channel_markers_before_final_text",
            "reasoning_trace_policy": "owlmlx.reasoning_trace_policy:v1",
            "final_text_candidate_policy": "only_when_derived_outside_visible_trace",
        },
        cache_policy={
            "prefix_cache": "caution_mixed_attention",
            "cache_caveat": "bypass prefix reuse until Gemma mixed-attention proof exists",
        },
        profile_caveats=(
            "Gemma profile includes stop-token and channel-cleanup caveats.",
            "Mixed-attention cache reuse can cause repetitive output without proof.",
        ),
        source_basis=(
            "docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md",
            "docs/source-of-truth/model-release-candidate-program.md",
        ),
    ),
    "deepseek_v4_experimental": _profile(
        profile_id="deepseek_v4_experimental",
        profile_family="deepseek_v4",
        model_id_patterns=(r"\bdeepseek\b.*\bv4\b.*\bflash\b",),
        chat_template_kwargs={"enable_thinking": True},
        stop_token_strings=("<｜end▁of▁sentence｜>", "<｜User｜>", "<｜Assistant｜>"),
        sampler_defaults={"temperature": 0.0, "top_p": 1.0},
        reasoning_parser_family="deepseek",
        thinking_policy={
            "default_mode": "experimental_adapter_only",
            "mainline_gate": "not_in_mainline",
        },
        cache_policy={
            "prefix_cache": "adapter_specific_only",
            "cache_caveat": "requires isolated DeepSeek adapter proof",
        },
        profile_caveats=(
            "DeepSeek V4 is a flagship experimental pressure lane only.",
            "No mainline pass/fail inference follows from this profile.",
        ),
        source_basis=(
            "docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md",
            "docs/source-of-truth/model-release-candidate-program.md",
        ),
    ),
    "unknown": _profile(
        profile_id="unknown",
        profile_family="unknown",
        model_id_patterns=(),
        chat_template_kwargs={},
        stop_token_strings=(),
        sampler_defaults={"temperature": 0.0},
        reasoning_parser_family="unknown",
        thinking_policy={
            "default_mode": "disabled_until_profiled",
            "reason": "unknown models stay conservative",
        },
        cache_policy={
            "prefix_cache": "disabled_until_profiled",
            "cache_caveat": "unknown models require explicit evidence",
        },
        profile_caveats=("Unknown model ids must not inherit mainline defaults.",),
        source_basis=("owlmlx conservative resolver fallback",),
    ),
}


def _normalize_model_id(model_id: str) -> str:
    normalized = model_id.strip().lower()
    normalized = normalized.replace("_", "-")
    normalized = re.sub(r"[^a-z0-9.+-]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized)
    return normalized.strip("-")


def model_profiles() -> dict[str, ModelProfile]:
    return dict(_PROFILES)


def get_model_profile(profile_id: str) -> ModelProfile:
    try:
        return _PROFILES[profile_id]
    except KeyError as exc:
        raise KeyError(f"unknown model profile id: {profile_id}") from exc


def resolve_model_profile(
    model_id: str,
    *,
    config: dict[str, Any] | None = None,
) -> ModelProfile:
    """Resolve a deterministic conservative profile for a model id.

    Optional config fields may provide a better local model_type hint, but the
    resolver never upgrades an unrecognized model into a mainline family unless
    either the id or model_type carries that family signal.
    """

    config = config or {}
    model_type = str(config.get("model_type") or "")
    haystack = " ".join(
        part for part in (_normalize_model_id(model_id), _normalize_model_id(model_type)) if part
    )

    if re.search(r"\bdeepseek\b.*\bv4\b|\bdeepseek-v4\b", haystack):
        return _PROFILES["deepseek_v4_experimental"]
    if re.search(r"\bgemma\b.*\b4\b|\bgemma4\b", haystack):
        return _PROFILES["gemma4_text"]
    if re.search(r"\bqwen3[.-]?6\b.*\b35b\b.*\ba3b\b", haystack):
        return _PROFILES["qwen3_6_moe"]
    if re.search(r"\bqwen3[.-]?6\b.*\b27b\b", haystack):
        return _PROFILES["qwen3_6_text"]

    for profile in _PROFILES.values():
        if profile.profile_id == "unknown":
            continue
        if any(re.search(pattern, haystack) for pattern in profile.model_id_patterns):
            return profile
    return _PROFILES["unknown"]


def model_profile_to_dict(profile: ModelProfile) -> dict[str, Any]:
    return profile.to_dict()
