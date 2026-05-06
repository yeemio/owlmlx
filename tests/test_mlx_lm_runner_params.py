from __future__ import annotations

from owlmlx.runtime.mlx_lm_runner import (
    _StopStringStreamFilter,
    _prepare_generation_params,
    _stop_strings_from_params,
    _truncate_at_stop_strings,
)


def test_prepare_generation_params_leaves_non_sampling_params_unchanged() -> None:
    prepared = _prepare_generation_params({"max_tokens": 4})

    assert prepared == {"max_tokens": 4}


def test_prepare_generation_params_converts_temperature_to_sampler() -> None:
    prepared = _prepare_generation_params({"max_tokens": 2, "temperature": 0.0})

    assert prepared["max_tokens"] == 2
    assert callable(prepared["sampler"])
    assert "temperature" not in prepared
    assert "temp" not in prepared


def test_prepare_generation_params_converts_sampler_family_params() -> None:
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
    assert "temperature" not in prepared
    assert "temp" not in prepared
    assert "top_p" not in prepared
    assert "top_k" not in prepared


def test_prepare_generation_params_removes_stop_before_mlx_lm_call() -> None:
    prepared = _prepare_generation_params(
        {"max_tokens": 4, "stop": ["<turn|>", "<eos>"]}
    )

    assert prepared == {"max_tokens": 4}


def test_stop_strings_from_params_normalizes_string_and_list() -> None:
    assert _stop_strings_from_params({"stop": "<turn|>"}) == ("<turn|>",)
    assert _stop_strings_from_params({"stop": ["<turn|>", "", "<eos>", "<turn|>"]}) == (
        "<turn|>",
        "<eos>",
    )


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
