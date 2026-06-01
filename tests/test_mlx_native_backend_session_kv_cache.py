"""Native backend wiring for experimental session KV cache reuse."""

from __future__ import annotations

import importlib
import sys
import types

import pytest


def _build_fake_mlx_lm_with_observable_cache(
    *,
    trim_supported: bool = True,
    trim_partial: bool = False,
    stream_token_ids: tuple[int, ...] = (999,),
) -> types.ModuleType:
    fake = types.ModuleType("mlx_lm")
    models = types.ModuleType("mlx_lm.models")
    cache_mod = types.ModuleType("mlx_lm.models.cache")
    created_caches: list[dict[str, object]] = []
    seen_prompt_caches: list[object | None] = []
    seen_stream_prompts: list[object] = []
    trim_calls: list[int] = []

    class FakeTokenizer:
        bos_token = None

        def encode(self, prompt: str, add_special_tokens: bool = True) -> list[int]:
            _ = add_special_tokens
            return [ord(ch) for ch in prompt]

    class FakeToken:
        def __init__(
            self,
            text: str,
            finish_reason: str | None = None,
            token: int = 999,
        ) -> None:
            self.text = text
            self.finish_reason = finish_reason
            self.token = token

    class FakePromptCache(dict):
        @property
        def nbytes(self) -> int:
            tokens = self["tokens"]
            assert isinstance(tokens, list)
            return len(tokens) * 8

    def make_prompt_cache(model: object) -> FakePromptCache:
        cache = FakePromptCache({"model": model, "tokens": []})
        created_caches.append(cache)
        return cache

    def trim_prompt_cache(cache: dict[str, object], token_count: int) -> int:
        if not trim_supported:
            trim_calls.append(0)
            return 0
        tokens = cache["tokens"]
        assert isinstance(tokens, list)
        trimmed = min(int(token_count), len(tokens))
        if trim_partial and trimmed > 0:
            trimmed -= 1
        if trimmed:
            del tokens[-trimmed:]
        trim_calls.append(trimmed)
        return trimmed

    def fake_load(model_id: str) -> tuple[object, object]:
        return (object(), FakeTokenizer())

    def fake_generate(
        model,
        tokenizer,
        *,
        prompt,
        max_tokens,
        prompt_cache=None,
    ) -> str:
        seen_prompt_caches.append(prompt_cache)
        return f"generated:{prompt}:{max_tokens}"

    def fake_stream_generate(
        model,
        tokenizer,
        *,
        prompt,
        max_tokens,
        prompt_cache=None,
    ):
        _ = (model, tokenizer, max_tokens)
        seen_prompt_caches.append(prompt_cache)
        seen_stream_prompts.append(prompt)
        if prompt_cache is not None:
            tokens = prompt_cache["tokens"]
            assert isinstance(tokens, list)
            tokens.extend(prompt if isinstance(prompt, list) else tokenizer.encode(prompt))
        for index, token_id in enumerate(stream_token_ids):
            if prompt_cache is not None:
                tokens = prompt_cache["tokens"]
                assert isinstance(tokens, list)
                tokens.append(token_id)
            finish_reason = "stop" if index == len(stream_token_ids) - 1 else None
            yield FakeToken(chr(token_id), finish_reason=finish_reason, token=token_id)

    cache_mod.make_prompt_cache = make_prompt_cache  # type: ignore[attr-defined]
    cache_mod.trim_prompt_cache = trim_prompt_cache  # type: ignore[attr-defined]
    models.cache = cache_mod  # type: ignore[attr-defined]
    fake.models = models  # type: ignore[attr-defined]
    fake.load = fake_load  # type: ignore[attr-defined]
    fake.generate = fake_generate  # type: ignore[attr-defined]
    fake.stream_generate = fake_stream_generate  # type: ignore[attr-defined]
    fake._created_caches = created_caches  # type: ignore[attr-defined]
    fake._seen_prompt_caches = seen_prompt_caches  # type: ignore[attr-defined]
    fake._seen_stream_prompts = seen_stream_prompts  # type: ignore[attr-defined]
    fake._trim_calls = trim_calls  # type: ignore[attr-defined]
    return fake


def _reload_native_backend_with_fake_mlx_lm(
    monkeypatch: pytest.MonkeyPatch,
    *,
    trim_supported: bool = True,
    trim_partial: bool = False,
    stream_token_ids: tuple[int, ...] = (999,),
):
    fake = _build_fake_mlx_lm_with_observable_cache(
        trim_supported=trim_supported,
        trim_partial=trim_partial,
        stream_token_ids=stream_token_ids,
    )
    monkeypatch.setitem(sys.modules, "mlx_lm", fake)
    monkeypatch.setitem(sys.modules, "mlx_lm.models", fake.models)
    monkeypatch.setitem(sys.modules, "mlx_lm.models.cache", fake.models.cache)
    import owlmlx.runtime.mlx_native_backend as mod
    importlib.reload(mod)
    return mod, fake


def test_native_session_kv_cache_stream_reuses_prompt_cache_with_suffix_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        assert backend.load("fake-model").ok is True

        first = list(backend.stream_generate("fake-model", "prefix A", session_id="s1"))
        second = list(backend.stream_generate("fake-model", "prefix B", session_id="s1"))

        assert first[-1].event == "done"
        assert second[-1].event == "done"
        assert len(fake._created_caches) == 1
        assert fake._seen_prompt_caches[0] is fake._seen_prompt_caches[1]
        assert fake._seen_stream_prompts[0] == [ord(ch) for ch in "prefix A"]
        assert fake._seen_stream_prompts[1] == [ord("B")]
        assert fake._trim_calls == [1, 1, 1]
        assert second[-1].detail["session_kv_cache"]["cache_decision"] == "reuse"
        assert second[-1].detail["session_kv_cache"]["cache_reason_code"] == (
            "session_cache_hit"
        )
        assert second[-1].detail["session_kv_cache"]["cached_prompt_tokens"] == len(
            "prefix "
        )
        assert second[-1].detail["session_kv_cache"]["suffix_token_count"] == 1
        assert backend._cache_manager.counters().entries == 0
        status = backend.status().detail["session_kv_cache"]
        assert status["enabled"] is True
        assert status["active_entries"] == 1
        assert status["counters"]["entries_created"] == 1
        assert status["counters"]["hits"] == 1
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_auto_prefix_reuses_without_private_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED", "1")
    mod, fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        assert backend.load("fake-model").ok is True

        first = list(backend.stream_generate("fake-model", "prefix A"))
        second = list(backend.stream_generate("fake-model", "prefix B"))

        assert first[-1].event == "done"
        assert second[-1].event == "done"
        assert len(fake._created_caches) == 1
        assert fake._seen_prompt_caches[0] is fake._seen_prompt_caches[1]
        assert fake._seen_stream_prompts[1] == [ord("B")]
        detail = second[-1].detail["session_kv_cache"]
        assert detail["cache_decision"] == "reuse"
        assert detail["cache_reason_code"] == "session_cache_hit"
        assert detail["cached_prompt_tokens"] == len("prefix ")
        status = backend.status().detail["session_kv_cache"]
        assert status["automatic_prefix_enabled"] is True
        assert status["active_entries"] == 1
        assert status["counters"]["hits"] == 1
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_auto_prefix_disabled_keeps_fresh_no_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    monkeypatch.delenv("OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED", raising=False)
    mod, fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        assert backend.load("fake-model").ok is True

        first = list(backend.stream_generate("fake-model", "prefix A"))
        second = list(backend.stream_generate("fake-model", "prefix B"))

        assert first[-1].event == "done"
        assert second[-1].event == "done"
        assert len(fake._created_caches) == 2
        assert fake._seen_prompt_caches[0] is not fake._seen_prompt_caches[1]
        assert "session_kv_cache" not in second[-1].detail
        status = backend.status().detail["session_kv_cache"]
        assert status["automatic_prefix_enabled"] is False
        assert status["active_entries"] == 0
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_auto_prefix_rejects_non_prefix_reuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED", "1")
    mod, fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        assert backend.load("fake-model").ok is True

        first = list(backend.stream_generate("fake-model", "abc"))
        second = list(backend.stream_generate("fake-model", "XYZ"))

        assert first[-1].event == "done"
        assert second[-1].event == "done"
        assert len(fake._created_caches) == 2
        assert fake._seen_prompt_caches[0] is not fake._seen_prompt_caches[1]
        detail = second[-1].detail["session_kv_cache"]
        assert detail["cache_decision"] == "new"
        assert detail["cache_reason_code"] == "auto_prefix_ineligible_not_token_prefix"
        assert detail["cached_prompt_tokens"] == 0
        status = backend.status().detail["session_kv_cache"]
        assert status["active_entries"] == 1
        assert status["counters"]["hits"] == 0
        assert status["counters"]["misses"] == 2
        assert status["counters"]["trim_bypasses"] == 1
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_exact_prompt_hit_streams_empty_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        assert backend.load("fake-model").ok is True

        first = list(backend.stream_generate("fake-model", "prefix A", session_id="s1"))
        second = list(backend.stream_generate("fake-model", "prefix A", session_id="s1"))

        assert first[-1].event == "done"
        assert second[-1].event == "done"
        assert len(fake._created_caches) == 1
        assert fake._seen_prompt_caches[0] is fake._seen_prompt_caches[1]
        assert fake._seen_stream_prompts[0] == [ord(ch) for ch in "prefix A"]
        assert fake._seen_stream_prompts[1] == []
        assert fake._trim_calls == [1, 1]
        status = backend.status().detail["session_kv_cache"]
        assert status["active_entries"] == 1
        assert status["counters"]["hits"] == 1
        assert status["counters"]["drops"] == 0
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_records_completion_trim_drop_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, _fake = _reload_native_backend_with_fake_mlx_lm(
        monkeypatch,
        trim_partial=True,
        stream_token_ids=(999, 1000),
    )
    try:
        backend = mod.MlxNativeBackend()
        assert backend.load("fake-model").ok is True

        events = list(backend.stream_generate("fake-model", "prefix A", session_id="s1"))

        assert events[-1].event == "done"
        status = backend.status().detail["session_kv_cache"]
        assert status["active_entries"] == 0
        assert status["counters"]["drops"] == 1
        assert status["last_drop_event"]["reason_code"] == "completion_trim_mismatch"
        assert status["last_drop_event"]["detail"]["requested_trim_tokens"] == 2
        assert status["last_drop_event"]["detail"]["trimmed_tokens"] == 1
        assert status["last_drop_event"]["detail"]["generated_token_count"] == 2
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_accounts_positive_active_memory_growth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, _fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)

    class FakeMxCore:
        def __init__(self) -> None:
            self._readings = iter([100, 116, 116, 140])

        def get_active_memory(self) -> int:
            return next(self._readings)

        def get_cache_memory(self) -> int:
            return 0

    try:
        backend = mod.MlxNativeBackend()
        fake_mx = FakeMxCore()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: fake_mx)
        assert backend.load("fake-model").ok is True

        first = list(backend.stream_generate("fake-model", "prefix A", session_id="s1"))
        second = list(backend.stream_generate("fake-model", "prefix B", session_id="s1"))

        assert first[-1].event == "done"
        assert second[-1].event == "done"
        status = backend.status().detail["session_kv_cache"]
        assert status["resident_bytes_estimate"] == 72
        assert status["resident_bytes_estimate_mode"] == "cache_object_nbytes"
        assert status["resident_bytes_estimate_used_for_promotion_gate"] is False
        assert status["resident_bytes_estimate_modes"] == {"cache_object_nbytes": 1}
        assert status["entries"][0]["byte_estimate"] == 72
        assert status["entries"][0]["byte_estimate_mode"] == "cache_object_nbytes"
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_prompt_window_bypasses_persistent_reuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_MAX_PROMPT_TOKENS", "3")
    mod, fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        assert backend.load("fake-model").ok is True

        first = list(backend.stream_generate("fake-model", "abcd", session_id="s1"))
        second = list(backend.stream_generate("fake-model", "abcde", session_id="s1"))

        assert first[-1].event == "done"
        assert second[-1].event == "done"
        assert len(fake._created_caches) == 2
        assert fake._seen_prompt_caches[0] is not fake._seen_prompt_caches[1]
        assert backend._cache_manager.status_dict()["handles_count_by_model"] == {}
        status = backend.status().detail["session_kv_cache"]
        assert status["active_entries"] == 0
        assert status["max_prompt_tokens"] == 3
        assert status["prompt_window_policy"] == "bypass_and_evict_over_limit"
        assert status["counters"]["window_bypasses"] == 2
        assert status["counters"]["window_evictions"] == 0
        assert status["counters"]["drops"] == 0
        assert status["counters"]["rejects"] == 0
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_non_trimmable_cache_reuses_append_only_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, fake = _reload_native_backend_with_fake_mlx_lm(
        monkeypatch,
        trim_supported=False,
    )
    try:
        backend = mod.MlxNativeBackend()
        assert backend.load("fake-model").ok is True

        first = list(backend.stream_generate("fake-model", "prefix A", session_id="s1"))
        second_prompt = "prefix A" + chr(999) + " suffix"
        second = list(backend.stream_generate("fake-model", second_prompt, session_id="s1"))

        assert first[-1].event == "done"
        assert second[-1].event == "done"
        assert len(fake._created_caches) == 1
        assert fake._seen_prompt_caches[0] is fake._seen_prompt_caches[1]
        assert fake._seen_stream_prompts[1] == [ord(ch) for ch in " suffix"]
        status = backend.status().detail["session_kv_cache"]
        assert status["active_entries"] == 1
        assert status["counters"]["hits"] == 1
        assert status["counters"]["drops"] == 0
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_unavailable_reuse_trim_bypasses_without_drop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, fake = _reload_native_backend_with_fake_mlx_lm(
        monkeypatch,
        trim_supported=False,
    )
    try:
        backend = mod.MlxNativeBackend()
        assert backend.load("fake-model").ok is True

        first = list(backend.stream_generate("fake-model", "prefix A", session_id="s1"))
        second = list(backend.stream_generate("fake-model", "prefix B", session_id="s1"))

        assert first[-1].event == "done"
        assert second[-1].event == "done"
        assert len(fake._created_caches) == 2
        status = backend.status().detail["session_kv_cache"]
        assert status["counters"]["drops"] == 0
        assert status["counters"]["trim_bypasses"] == 1
        assert status["counters"]["trim_evictions"] == 1
        assert status["last_bypass_event"]["reason_code"] == (
            "reuse_trim_unavailable_fresh_cache"
        )
        assert status["last_bypass_event"]["detail"]["requested_trim_tokens"] > 0
        assert status["last_bypass_event"]["detail"]["trimmed_tokens"] == 0
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_drops_model_entries_before_unload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, _fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        monkeypatch.setattr(backend, "_try_import_mlx_core", lambda: None)
        backend.load("fake-model")
        list(backend.stream_generate("fake-model", "hello", session_id="s1"))
        assert backend.status().detail["session_kv_cache"]["active_entries"] == 1

        unload = backend.unload("fake-model")

        assert unload.ok is True
        session_cache = backend.status().detail["session_kv_cache"]
        assert session_cache["active_entries"] == 0
        assert session_cache["counters"]["drops"] == 1
    finally:
        importlib.reload(mod)


def test_native_session_kv_cache_pressure_falls_back_to_single_request_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OWLMLX_SESSION_CACHE_ENABLED", "1")
    mod, fake = _reload_native_backend_with_fake_mlx_lm(monkeypatch)
    try:
        backend = mod.MlxNativeBackend()
        backend.load("fake-model")
        list(backend.stream_generate("fake-model", "hello", session_id="s1"))

        pressured = list(
            backend.stream_generate(
                "fake-model",
                "hello under pressure",
                session_id="s1",
                session_kv_cache_watermark="yellow",
            )
        )

        assert pressured[-1].event == "done"
        assert len(fake._created_caches) == 2
        assert fake._seen_prompt_caches[0] is not fake._seen_prompt_caches[1]
        assert backend._cache_manager.counters().entries == 1
        session_cache = backend.status().detail["session_kv_cache"]
        assert session_cache["active_entries"] == 0
        assert session_cache["counters"]["rejects"] == 1
        assert session_cache["counters"]["evictions"] == 1
    finally:
        importlib.reload(mod)
