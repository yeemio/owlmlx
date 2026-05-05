from __future__ import annotations

from owlmlx.runtime.mlx_lm_runner import _prepare_generation_params


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
