"""Tests for experimental session-scoped KV cache reuse."""

from __future__ import annotations

from owlmlx.session_kv_cache import SessionKVCacheStore


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
