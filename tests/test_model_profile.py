from __future__ import annotations

from pathlib import Path

from owlmlx.model_profile import (
    MODEL_PROFILE_SURFACE,
    MODEL_PROFILE_VERSION,
    get_model_profile,
    model_profile_to_dict,
    model_profiles,
    resolve_model_profile,
)


REQUIRED_PROFILE_IDS = {
    "qwen3_6_text",
    "qwen3_6_moe",
    "gemma4_text",
    "deepseek_v4_experimental",
    "unknown",
}


def test_required_profile_ids_serialize() -> None:
    profiles = model_profiles()
    assert REQUIRED_PROFILE_IDS <= set(profiles)

    for profile_id in REQUIRED_PROFILE_IDS:
        payload = model_profile_to_dict(profiles[profile_id])
        assert payload["surface"] == MODEL_PROFILE_SURFACE
        assert payload["version"] == MODEL_PROFILE_VERSION
        assert payload["profile_id"] == profile_id
        assert isinstance(payload["model_id_patterns"], list)
        assert isinstance(payload["chat_template_kwargs"], dict)
        assert isinstance(payload["stop_token_strings"], list)
        assert isinstance(payload["sampler_defaults"], dict)
        assert isinstance(payload["profile_caveats"], list)
        assert payload["source_basis"]


def test_known_model_ids_resolve_to_expected_profiles() -> None:
    assert resolve_model_profile("Qwen3.6-27B").profile_id == "qwen3_6_text"
    assert resolve_model_profile("Qwen3.6-35B-A3B").profile_id == "qwen3_6_moe"
    assert resolve_model_profile("gemma-4-31B-it").profile_id == "gemma4_text"
    assert (
        resolve_model_profile("DeepSeek-V4-Flash-2bit-DQ").profile_id
        == "deepseek_v4_experimental"
    )


def test_resolver_is_case_and_separator_tolerant() -> None:
    assert resolve_model_profile("qwen3_6_27b").profile_id == "qwen3_6_text"
    assert resolve_model_profile("QWEN3-6-35B-A3B").profile_id == "qwen3_6_moe"
    assert resolve_model_profile("Gemma 4 31b IT").profile_id == "gemma4_text"
    assert resolve_model_profile("deepseek v4 flash").profile_id == "deepseek_v4_experimental"


def test_unknown_model_ids_stay_conservative() -> None:
    profile = resolve_model_profile("future-local-model-9b")
    assert profile.profile_id == "unknown"
    assert profile.chat_template_kwargs == {}
    assert profile.cache_policy["prefix_cache"] == "disabled_until_profiled"
    assert profile.thinking_policy["default_mode"] == "disabled_until_profiled"


def test_optional_config_fields_can_supply_family_hint() -> None:
    assert (
        resolve_model_profile("local-copy", config={"model_type": "gemma4"}).profile_id
        == "gemma4_text"
    )
    assert (
        resolve_model_profile("local-copy", config={"model_type": "deepseek_v4"}).profile_id
        == "deepseek_v4_experimental"
    )


def test_gemma_profile_includes_stop_channel_and_cache_caveats() -> None:
    profile = get_model_profile("gemma4_text")
    assert "<eos>" in profile.stop_token_strings
    assert "<turn|>" in profile.stop_token_strings
    assert profile.reasoning_parser_family == "gemma4"
    assert "channel" in profile.thinking_policy["channel_policy"]
    assert profile.thinking_policy["reasoning_trace_policy"] == (
        "owlmlx.reasoning_trace_policy:v1"
    )
    assert (
        profile.thinking_policy["final_text_candidate_policy"]
        == "only_when_derived_outside_visible_trace"
    )
    assert profile.cache_policy["prefix_cache"] == "caution_mixed_attention"
    assert any("Mixed-attention cache" in caveat for caveat in profile.profile_caveats)


def test_qwen_moe_profile_carries_thinking_and_template_caveats() -> None:
    profile = get_model_profile("qwen3_6_moe")
    assert profile.chat_template_kwargs["enable_thinking"] is True
    assert profile.reasoning_parser_family == "qwen"
    assert "thinking tokens" in profile.thinking_policy["template_caveat"]
    assert any("think-in-template" in caveat for caveat in profile.profile_caveats)


def test_deepseek_profile_is_experimental_and_not_mainline() -> None:
    profile = get_model_profile("deepseek_v4_experimental")
    assert profile.thinking_policy["default_mode"] == "experimental_adapter_only"
    assert profile.thinking_policy["mainline_gate"] == "not_in_mainline"
    assert profile.cache_policy["prefix_cache"] == "adapter_specific_only"
    assert any("experimental pressure lane only" in caveat for caveat in profile.profile_caveats)


def test_no_banned_current_claim_wording_in_profile_module() -> None:
    text = Path("owlmlx/model_profile.py").read_text(encoding="utf-8").lower()
    for banned in (
        "release-ready",
        "production-grade",
        "equivalent",
        "beats",
        "wins",
        "matches",
    ):
        assert banned not in text
