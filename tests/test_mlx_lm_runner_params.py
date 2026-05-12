from __future__ import annotations

import sys
import types

from owlmlx.runtime.mlx_lm_runner import (
    _StopStringStreamFilter,
    _chat_template_kwargs_from_params,
    _prepare_generation_params,
    _prompt_from_messages,
    _stop_strings_from_params,
    _truncate_at_stop_strings,
)


def _install_fake_sampler(monkeypatch):  # type: ignore[no-untyped-def]
    mlx_lm_module = types.ModuleType("mlx_lm")
    sample_utils_module = types.ModuleType("mlx_lm.sample_utils")

    def make_sampler(**kwargs):  # type: ignore[no-untyped-def]
        def sampler(*args, **inner_kwargs):  # type: ignore[no-untyped-def]
            return {"args": args, "kwargs": inner_kwargs}

        sampler.sample_kwargs = kwargs  # type: ignore[attr-defined]
        return sampler

    sample_utils_module.make_sampler = make_sampler  # type: ignore[attr-defined]
    mlx_lm_module.sample_utils = sample_utils_module  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mlx_lm", mlx_lm_module)
    monkeypatch.setitem(sys.modules, "mlx_lm.sample_utils", sample_utils_module)


def test_prepare_generation_params_leaves_non_sampling_params_unchanged() -> None:
    prepared = _prepare_generation_params({"max_tokens": 4})

    assert prepared == {"max_tokens": 4}


def test_prepare_generation_params_converts_temperature_to_sampler(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake_sampler(monkeypatch)

    prepared = _prepare_generation_params({"max_tokens": 2, "temperature": 0.0})

    assert prepared["max_tokens"] == 2
    assert callable(prepared["sampler"])
    assert prepared["sampler"].sample_kwargs == {"temp": 0.0}
    assert "temperature" not in prepared
    assert "temp" not in prepared


def test_prepare_generation_params_converts_sampler_family_params(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake_sampler(monkeypatch)

    prepared = _prepare_generation_params(
        {
            "max_tokens": 2,
            "temperature": 0.7,
            "temp": 0.2,
            "top_p": 0.9,
            "top_k": 20,
        }
    )

    assert prepared["max_tokens"] == 2
    assert callable(prepared["sampler"])
    assert prepared["sampler"].sample_kwargs == {
        "temp": 0.2,
        "top_k": 20,
        "top_p": 0.9,
    }
    assert "temperature" not in prepared
    assert "temp" not in prepared
    assert "top_p" not in prepared
    assert "top_k" not in prepared


def test_prepare_generation_params_removes_stop_before_mlx_lm_call() -> None:
    prepared = _prepare_generation_params(
        {"max_tokens": 4, "stop": ["<turn|>", "<eos>"]}
    )

    assert prepared == {"max_tokens": 4}


def test_prepare_generation_params_removes_chat_template_kwargs() -> None:
    prepared = _prepare_generation_params(
        {"max_tokens": 4, "chat_template_kwargs": {"enable_thinking": False}}
    )

    assert prepared == {"max_tokens": 4}


def test_stop_strings_from_params_normalizes_string_and_list() -> None:
    assert _stop_strings_from_params({"stop": "<turn|>"}) == ("<turn|>",)
    assert _stop_strings_from_params({"stop": ["<turn|>", "", "<eos>", "<turn|>"]}) == (
        "<turn|>",
        "<eos>",
    )


def test_chat_template_kwargs_from_params_accepts_dict_only() -> None:
    assert _chat_template_kwargs_from_params(
        {"chat_template_kwargs": {"enable_thinking": False, "": "ignored", 1: "bad"}}
    ) == {"enable_thinking": False}
    assert _chat_template_kwargs_from_params({"chat_template_kwargs": "bad"}) == {}


def test_prompt_from_messages_forwards_chat_template_kwargs() -> None:
    class Tokenizer:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def apply_chat_template(self, messages, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append({"messages": messages, "kwargs": kwargs})
            return "rendered"

    tokenizer = Tokenizer()
    messages = [{"role": "user", "content": "hello"}]

    rendered = _prompt_from_messages(
        tokenizer,
        messages,
        chat_template_kwargs={"enable_thinking": False},
    )

    assert rendered == "rendered"
    assert tokenizer.calls == [
        {
            "messages": messages,
            "kwargs": {
                "tokenize": False,
                "add_generation_prompt": True,
                "enable_thinking": False,
            },
        }
    ]


def test_truncate_at_stop_strings_uses_earliest_marker() -> None:
    text, stopped = _truncate_at_stop_strings(
        "answer<turn|>ignored<eos>",
        ("<eos>", "<turn|>"),
    )

    assert text == "answer"
    assert stopped is True


def test_stop_string_stream_filter_holds_tail_for_split_marker() -> None:
    stop_filter = _StopStringStreamFilter(("<turn|>",))

    first, stopped = stop_filter.feed("answer<tu")
    second, stopped_second = stop_filter.feed("rn|>ignored")

    assert first == "ans"
    assert stopped is False
    assert second == "wer"
    assert stopped_second is True
    assert stop_filter.flush() == ""
