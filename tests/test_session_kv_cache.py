"""Tests for experimental session-scoped KV cache reuse."""

from __future__ import annotations

from owlmlx.session_kv_cache import (
    SessionKVCacheStore,
    classify_prefix_cache_candidate,
)


def test_session_kv_cache_disabled_does_not_call_factory() -> None:
    store = SessionKVCacheStore(enabled=False)
    calls = 0

    def make_cache() -> object:
        nonlocal calls
        calls += 1
        return object()

    decision = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=make_cache,
    )

    assert decision.decision == "disabled"
    assert decision.cache_object is None
    assert calls == 0
    assert store.status_dict()["enabled"] is False


def test_session_kv_cache_reuses_same_session_and_model() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0)
    created: list[object] = []

    def make_cache() -> object:
        cache = object()
        created.append(cache)
        return cache

    first = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=make_cache,
        now_s=1.0,
    )
    second = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=make_cache,
        now_s=2.0,
    )

    assert first.decision == "new"
    assert second.decision == "reuse"
    assert first.cache_object is second.cache_object
    assert len(created) == 1
    counters = store.status_dict()["counters"]
    assert counters["entries_created"] == 1
    assert counters["misses"] == 1
    assert counters["hits"] == 1


def test_session_kv_cache_reports_common_prefix_suffix_for_reuse() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0)
    first = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        prompt_tokens=(1, 2, 3),
    )
    remembered = store.remember_prompt(
        session_id="s1",
        model_id="m",
        prompt_tokens=(1, 2, 3),
    )
    second = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        prompt_tokens=(1, 2, 4, 5),
    )

    assert first.decision == "new"
    assert remembered is True
    assert second.decision == "reuse"
    assert second.common_prefix_token_count == 2
    assert second.previous_prompt_token_count == 3
    assert second.suffix_tokens == (4, 5)


def test_prefix_cache_candidate_accepts_same_model_token_prefix() -> None:
    decision = classify_prefix_cache_candidate(
        existing_model_id="model-a",
        requested_model_id="model-a",
        existing_prompt_tokens=(1, 2, 3),
        requested_prompt_tokens=(1, 2, 3, 4, 5),
        existing_runtime_profile_id="profile-a",
        requested_runtime_profile_id="profile-a",
        existing_isolation_scope="tenant-a",
        requested_isolation_scope="tenant-a",
    )

    assert decision.eligible is True
    assert decision.reason_code == "same_model_token_prefix"
    assert decision.common_prefix_token_count == 3
    assert decision.previous_prompt_token_count == 3
    assert decision.requested_prompt_token_count == 5
    assert decision.suffix_token_count == 2
    assert decision.needs_trim is False
    assert not hasattr(decision, "cache_object")


def test_prefix_cache_candidate_rejects_different_model() -> None:
    decision = classify_prefix_cache_candidate(
        existing_model_id="model-a",
        requested_model_id="model-b",
        existing_prompt_tokens=(1, 2, 3),
        requested_prompt_tokens=(1, 2, 3),
        existing_runtime_profile_id="profile-a",
        requested_runtime_profile_id="profile-a",
        existing_isolation_scope="tenant-a",
        requested_isolation_scope="tenant-a",
    )

    assert decision.eligible is False
    assert decision.reason_code == "different_model"


def test_prefix_cache_candidate_rejects_different_runtime_profile() -> None:
    decision = classify_prefix_cache_candidate(
        existing_model_id="model-a",
        requested_model_id="model-a",
        existing_prompt_tokens=(1, 2, 3),
        requested_prompt_tokens=(1, 2, 3),
        existing_runtime_profile_id="tokenizer-v1/template-a",
        requested_runtime_profile_id="tokenizer-v2/template-a",
        existing_isolation_scope="tenant-a",
        requested_isolation_scope="tenant-a",
    )

    assert decision.eligible is False
    assert decision.reason_code == "different_runtime_profile"


def test_prefix_cache_candidate_rejects_unsafe_isolation_scope() -> None:
    decision = classify_prefix_cache_candidate(
        existing_model_id="model-a",
        requested_model_id="model-a",
        existing_prompt_tokens=(1, 2, 3),
        requested_prompt_tokens=(1, 2, 3, 4),
        existing_runtime_profile_id="profile-a",
        requested_runtime_profile_id="profile-a",
        existing_isolation_scope="tenant-a",
        requested_isolation_scope="tenant-b",
    )

    assert decision.eligible is False
    assert decision.reason_code == "unsafe_isolation_scope"


def test_prefix_cache_candidate_rejects_non_prefix_tokens() -> None:
    decision = classify_prefix_cache_candidate(
        existing_model_id="model-a",
        requested_model_id="model-a",
        existing_prompt_tokens=(1, 2, 3),
        requested_prompt_tokens=(9, 2, 3),
        existing_runtime_profile_id="profile-a",
        requested_runtime_profile_id="profile-a",
        existing_isolation_scope="tenant-a",
        requested_isolation_scope="tenant-a",
        trim_available=True,
    )

    assert decision.eligible is False
    assert decision.reason_code == "not_token_prefix"


def test_prefix_cache_candidate_rejects_edited_prefix_without_trim() -> None:
    decision = classify_prefix_cache_candidate(
        existing_model_id="model-a",
        requested_model_id="model-a",
        existing_prompt_tokens=(1, 2, 3),
        requested_prompt_tokens=(1, 2, 9),
        existing_runtime_profile_id="profile-a",
        requested_runtime_profile_id="profile-a",
        existing_isolation_scope="tenant-a",
        requested_isolation_scope="tenant-a",
        trim_available=False,
    )

    assert decision.eligible is False
    assert decision.reason_code == "trim_unavailable_for_edit"
    assert decision.common_prefix_token_count == 2
    assert decision.needs_trim is True


def test_prefix_cache_candidate_allows_edited_prefix_when_trim_available() -> None:
    decision = classify_prefix_cache_candidate(
        existing_model_id="model-a",
        requested_model_id="model-a",
        existing_prompt_tokens=(1, 2, 3),
        requested_prompt_tokens=(1, 2, 9),
        existing_runtime_profile_id="profile-a",
        requested_runtime_profile_id="profile-a",
        existing_isolation_scope="tenant-a",
        requested_isolation_scope="tenant-a",
        trim_available=True,
    )

    assert decision.eligible is True
    assert decision.reason_code == "same_model_token_prefix"
    assert decision.common_prefix_token_count == 2
    assert decision.suffix_token_count == 1
    assert decision.needs_trim is True


def test_session_kv_cache_accumulates_byte_estimate_delta() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0)
    store.acquire_for_request(session_id="s1", model_id="m", make_cache=object)

    first = store.remember_prompt(
        session_id="s1",
        model_id="m",
        prompt_tokens=(1, 2, 3),
        byte_estimate_delta=16,
    )
    second = store.remember_prompt(
        session_id="s1",
        model_id="m",
        prompt_tokens=(1, 2, 3, 4),
        byte_estimate_delta=24,
    )

    status = store.status_dict()
    assert first is True
    assert second is True
    assert status["resident_bytes_estimate"] == 40
    assert status["resident_bytes_estimate_mode"] == (
        "positive_active_memory_delta_upper_bound"
    )
    assert status["resident_bytes_estimate_used_for_promotion_gate"] is False
    assert status["entries"][0]["byte_estimate"] == 40
    assert status["entries"][0]["byte_estimate_mode"] == (
        "positive_active_memory_delta_upper_bound"
    )


def test_session_kv_cache_prefers_absolute_cache_object_byte_estimate() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0)
    store.acquire_for_request(session_id="s1", model_id="m", make_cache=object)

    remembered = store.remember_prompt(
        session_id="s1",
        model_id="m",
        prompt_tokens=(1, 2, 3),
        byte_estimate=128,
        byte_estimate_mode="cache_object_nbytes",
    )

    status = store.status_dict()
    assert remembered is True
    assert status["resident_bytes_estimate"] == 128
    assert status["resident_bytes_estimate_mode"] == "cache_object_nbytes"
    assert status["resident_bytes_estimate_modes"] == {"cache_object_nbytes": 1}
    assert status["resident_bytes_estimate_used_for_promotion_gate"] is False
    assert status["entries"][0]["byte_estimate"] == 128
    assert status["entries"][0]["byte_estimate_mode"] == "cache_object_nbytes"


def test_session_kv_cache_evicts_lru_over_resident_budget() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0, max_resident_bytes=150)
    first = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        byte_estimate=100,
        byte_estimate_mode="cache_object_nbytes",
        now_s=1.0,
    )
    second = store.acquire_for_request(
        session_id="s2",
        model_id="m",
        make_cache=object,
        byte_estimate=100,
        byte_estimate_mode="cache_object_nbytes",
        now_s=2.0,
    )

    status = store.status_dict()
    assert first.evicted_count == 0
    assert second.evicted_count == 1
    assert status["active_entries"] == 1
    assert status["active_sessions"] == 1
    assert status["resident_bytes_estimate"] == 100
    assert status["max_resident_bytes"] == 150
    assert status["resident_pressure_policy"] == "lru_evict_over_limit"
    assert status["counters"]["evictions"] == 1
    assert status["entries"][0]["session_id"] == "s2"


def test_session_kv_cache_remember_prompt_enforces_resident_budget() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0, max_resident_bytes=150)
    store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        byte_estimate=60,
        byte_estimate_mode="cache_object_nbytes",
        now_s=1.0,
    )
    store.acquire_for_request(
        session_id="s2",
        model_id="m",
        make_cache=object,
        byte_estimate=60,
        byte_estimate_mode="cache_object_nbytes",
        now_s=2.0,
    )

    remembered = store.remember_prompt(
        session_id="s2",
        model_id="m",
        prompt_tokens=(1, 2, 3),
        byte_estimate=180,
        byte_estimate_mode="cache_object_nbytes",
    )

    status = store.status_dict()
    assert remembered is True
    assert status["active_entries"] == 0
    assert status["resident_bytes_estimate"] == 0
    assert status["counters"]["evictions"] == 2


def test_session_kv_cache_bypasses_and_evicts_over_prompt_window() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0, max_prompt_tokens=3)
    first = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        prompt_tokens=(1, 2, 3),
    )
    remembered = store.remember_prompt(
        session_id="s1",
        model_id="m",
        prompt_tokens=(1, 2, 3),
    )
    second = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        prompt_tokens=(1, 2, 3, 4),
    )

    status = store.status_dict()
    assert first.decision == "new"
    assert remembered is True
    assert second.decision == "bypassed"
    assert second.reason_code == "prompt_token_window_exceeded"
    assert second.cache_object is None
    assert second.evicted_count == 1
    assert status["active_entries"] == 0
    assert status["max_prompt_tokens"] == 3
    assert status["prompt_window_policy"] == "bypass_and_evict_over_limit"
    assert status["counters"]["window_bypasses"] == 1
    assert status["counters"]["window_evictions"] == 1
    assert status["counters"]["drops"] == 0
    assert status["counters"]["rejects"] == 0


def test_session_kv_cache_remember_over_prompt_window_evicts_without_drop() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0, max_prompt_tokens=3)
    store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        prompt_tokens=(1, 2, 3),
    )

    remembered = store.remember_prompt(
        session_id="s1",
        model_id="m",
        prompt_tokens=(1, 2, 3, 4),
    )

    status = store.status_dict()
    assert remembered is True
    assert status["active_entries"] == 0
    assert status["counters"]["window_bypasses"] == 1
    assert status["counters"]["window_evictions"] == 1
    assert status["counters"]["drops"] == 0


def test_session_kv_cache_records_last_drop_reason() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0)
    store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        prompt_tokens=(1, 2, 3),
        token_count=3,
    )

    dropped = store.drop_for_session_model(
        session_id="s1",
        model_id="m",
        reason_code="reuse_trim_mismatch",
        detail={"requested_trim_tokens": 2, "trimmed_tokens": 1},
    )

    status = store.status_dict()
    assert dropped is True
    assert status["active_entries"] == 0
    assert status["counters"]["drops"] == 1
    assert status["last_drop_event"]["reason_code"] == "reuse_trim_mismatch"
    assert status["last_drop_event"]["entry_token_count"] == 3
    assert status["last_drop_event"]["detail"] == {
        "requested_trim_tokens": 2,
        "trimmed_tokens": 1,
    }


def test_session_kv_cache_records_trim_bypass_without_drop() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0)
    store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        prompt_tokens=(1, 2, 3),
        token_count=3,
    )

    bypassed = store.bypass_for_session_model(
        session_id="s1",
        model_id="m",
        reason_code="reuse_trim_unavailable_fresh_cache",
        detail={"requested_trim_tokens": 2, "trimmed_tokens": 0},
    )

    status = store.status_dict()
    assert bypassed is True
    assert status["active_entries"] == 0
    assert status["counters"]["drops"] == 0
    assert status["counters"]["trim_bypasses"] == 1
    assert status["counters"]["trim_evictions"] == 1
    assert status["last_bypass_event"]["reason_code"] == (
        "reuse_trim_unavailable_fresh_cache"
    )


def test_session_kv_cache_misses_on_model_switch() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=60.0)
    created: list[object] = []

    def make_cache() -> object:
        cache = object()
        created.append(cache)
        return cache

    first = store.acquire_for_request(
        session_id="s1",
        model_id="m-a",
        make_cache=make_cache,
    )
    second = store.acquire_for_request(
        session_id="s1",
        model_id="m-b",
        make_cache=make_cache,
    )

    assert first.cache_object is not second.cache_object
    assert len(created) == 2
    assert store.status_dict()["active_entries"] == 2


def test_session_kv_cache_drop_for_model_removes_only_that_model() -> None:
    store = SessionKVCacheStore(enabled=True)

    store.acquire_for_request(session_id="s1", model_id="m-a", make_cache=object)
    store.acquire_for_request(session_id="s2", model_id="m-a", make_cache=object)
    store.acquire_for_request(session_id="s1", model_id="m-b", make_cache=object)

    dropped = store.drop_for_model("m-a")
    status = store.status_dict()

    assert dropped == 2
    assert status["active_entries"] == 1
    assert status["entries"][0]["model_id"] == "m-b"
    assert status["counters"]["drops"] == 2


def test_session_kv_cache_drop_for_session_model_removes_one_entry() -> None:
    store = SessionKVCacheStore(enabled=True)
    store.acquire_for_request(session_id="s1", model_id="m-a", make_cache=object)
    store.acquire_for_request(session_id="s2", model_id="m-a", make_cache=object)

    dropped = store.drop_for_session_model(session_id="s1", model_id="m-a")
    status = store.status_dict()

    assert dropped is True
    assert status["active_entries"] == 1
    assert status["entries"][0]["session_id"] == "s2"
    assert status["counters"]["drops"] == 1


def test_session_kv_cache_ttl_expiry_forces_new_entry() -> None:
    store = SessionKVCacheStore(enabled=True, ttl_s=1.0)
    first = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        now_s=1.0,
    )
    second = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        now_s=3.0,
    )

    assert first.cache_object is not second.cache_object
    status = store.status_dict()
    assert status["active_entries"] == 1
    assert status["counters"]["expirations"] == 1


def test_session_kv_cache_watermark_pressure_evicts_and_rejects_reuse() -> None:
    store = SessionKVCacheStore(enabled=True)
    store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        byte_estimate=123,
    )

    decision = store.acquire_for_request(
        session_id="s1",
        model_id="m",
        make_cache=object,
        watermark="yellow",
    )
    status = store.status_dict()

    assert decision.decision == "rejected"
    assert decision.reason_code == "watermark_yellow"
    assert decision.evicted_count == 1
    assert status["active_entries"] == 0
    assert status["counters"]["rejects"] == 1
    assert status["counters"]["evictions"] == 1
